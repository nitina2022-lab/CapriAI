"""
fetcher.py
CapriAI - Fetches live data from sources listed in capriAI_sources_updated.csv
"""

import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

# Folder to store raw HTML snapshots
os.makedirs("raw_data", exist_ok=True)

def fetch_page(url):
    """Fetch the HTML content of a webpage."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"[!] Failed to fetch {url}: {e}")
        return None

def save_snapshot(url, content):
    """Save the raw HTML snapshot."""
    filename = url.replace("https://", "").replace("http://", "").replace("/", "_")
    filepath = os.path.join("raw_data", f"{filename}.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[+] Saved: {filepath}")

def main():
    with open("capriAI_sources_updated.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            url = row["url"]
            print(f"Fetching: {url}")
            content = fetch_page(url)
            if content:
                save_snapshot(url, content)

if __name__ == "__main__":
    print(f"--- CapriAI Fetcher started at {datetime.now()} ---")
    main()
    print(f"--- Fetch complete at {datetime.now()} ---")
