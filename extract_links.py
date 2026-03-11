#!/usr/bin/env python3
"""
Reusable HTML link extractor using BeautifulSoup.
Extracts links with their descriptions and saves to JSON/CSV.

Usage:
    # Provide HTML directly via stdin
    echo '<html>...</html>' | uv run extract_links.py
    
    # Or paste HTML interactively
    uv run extract_links.py
    
    # From file
    uv run extract_links.py --html input.html
    
    # Specify format
    uv run extract_links.py --format csv
"""
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "beautifulsoup4",
# ]
# ///

import argparse
import json
import csv
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup


def extract_links(html_content: str) -> list[dict]:
    """Extract links with descriptions from HTML content."""
    soup = BeautifulSoup(html_content, "html.parser")
    links = []
    
    for anchor in soup.find_all("a", href=True):
        url = anchor["href"]
        label = anchor.get_text(strip=True)
        aria_label = anchor.get("aria-label", "")
        
        # Try to find description from parent container
        description = ""
        parent = anchor.find_parent("section") or anchor.find_parent("div")
        if parent:
            desc_div = parent.find("div", class_="blocks-button__description")
            if desc_div:
                description = desc_div.get_text(strip=True)
        
        links.append({
            "url": url,
            "label": label,
            "aria_label": aria_label,
            "description": description
        })
    
    return links


def generate_filename(html_content: str, fmt: str) -> str:
    """Generate unique filename based on content hash and timestamp."""
    content_hash = hashlib.md5(html_content.encode()).hexdigest()[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"links_{timestamp}_{content_hash}.{fmt}"


def save_to_json(links: list[dict], output_path: Path) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(links, f, indent=2, ensure_ascii=False)


def save_to_csv(links: list[dict], output_path: Path) -> None:
    if not links:
        return
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=links[0].keys())
        writer.writeheader()
        writer.writerows(links)


def main():
    parser = argparse.ArgumentParser(description="Extract links from HTML content")
    parser.add_argument("--html", type=Path, help="Path to HTML file (optional, reads from stdin if not provided)")
    parser.add_argument("--output", type=Path, help="Output file path (auto-generated if not provided)")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")
    args = parser.parse_args()
    
    # Get HTML content
    if args.html and args.html.exists():
        html_content = args.html.read_text(encoding="utf-8")
    elif not sys.stdin.isatty():
        # Read from stdin (piped input)
        html_content = sys.stdin.read()
    else:
        # Interactive input
        print("Paste HTML content (press Ctrl+D or Ctrl+Z when done):")
        html_content = sys.stdin.read()
    
    if not html_content.strip():
        print("Error: No HTML content provided")
        sys.exit(1)
    
    # Generate output filename if not provided
    output_path = args.output or Path(generate_filename(html_content, args.format))
    
    links = extract_links(html_content)
    
    if args.format == "csv":
        save_to_csv(links, output_path)
    else:
        save_to_json(links, output_path)
    
    print(f"Extracted {len(links)} links to {output_path}")
    return links


if __name__ == "__main__":
    main()
