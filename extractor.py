"""
extractor.py
CapriAI - Cleans HTML snapshots saved by fetcher.py and writes plain text files.
Usage:
  1. Place HTML files into the 'raw_data' folder (fetcher.py does this).
  2. Run: python3 extractor.py
  3. Cleaned text files will be written to the 'extracted' folder.
"""

import os
import glob
from bs4 import BeautifulSoup
from datetime import datetime

RAW_DIR = "raw_data"
OUT_DIR = "extracted"

os.makedirs(OUT_DIR, exist_ok=True)

def clean_html(html):
    """Return cleaned, readable text from raw HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove common noisy tags
    for selector in ["script", "style", "nav", "footer", "aside", "header", "form", "noscript"]:
        for tag in soup.select(selector):
            tag.decompose()

    # Remove common site banners and cookie notices by id/class heuristics
    for attr in ["cookie", "consent", "banner", "modal", "subscribe", "newsletter", "promo", "advert"]:
        for tag in soup.select(f"[id*='{attr}']"):
            tag.decompose()
        for tag in soup.select(f"[class*='{attr}']"):
            tag.decompose()

    # Prefer main/article sections if present
    main = soup.find("main") or soup.find("article")
    if main:
        text_source = main
    else:
        text_source = soup

    # Collect headings and paragraphs
    lines = []
    for elem in text_source.find_all(["h1","h2","h3","h4","p","li"]):
        line = elem.get_text(separator=' ', strip=True)
        if line:
            lines.append(line)

    # Fallback: if no lines found, get all text
    if not lines:
        text = text_source.get_text(separator='\n', strip=True)
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # Join and normalize whitespace
    cleaned = "\n\n".join(lines)
    return cleaned

def process_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
    except Exception as e:
        print(f"[!] Failed to read {path}: {e}")
        return

    text = clean_html(html)
    if not text or len(text) < 50:
        print(f"[!] Warning: extracted text seems very short for {os.path.basename(path)}")

    base = os.path.basename(path).rsplit(".",1)[0]
    out_path = os.path.join(OUT_DIR, base + ".txt")
    try:
        with open(out_path, "w", encoding="utf-8") as fo:
            fo.write(f"<!-- source: {base}  extracted: {datetime.utcnow().isoformat()} UTC -->\n\n")
            fo.write(text)
        print(f"[+] Extracted: {out_path}")
    except Exception as e:
        print(f"[!] Failed to write {out_path}: {e}")

def run_all():
    files = glob.glob(os.path.join(RAW_DIR, "*.html"))
    if not files:
        print(f"No HTML files found in '{RAW_DIR}'. Run fetcher.py first.")
        return
    for path in files:
        process_file(path)

if __name__ == "__main__":
    run_all()
