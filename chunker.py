"""
chunker.py
CapriAI - Splits cleaned text files from 'extracted' into overlapping chunks ready for embeddings.
Usage:
  1. Ensure 'extracted' folder contains .txt files (created by extractor.py).
  2. Run: python3 chunker.py
  3. Chunk JSON files will be written to the 'chunks' folder.
"""

import os
import glob
import json
from datetime import datetime

EXTRACTED_DIR = "extracted"
CHUNKS_DIR = "chunks"
# Approximate character size per chunk (not tokens). Adjust if needed.
CHUNK_SIZE = 3000
OVERLAP = 600

os.makedirs(CHUNKS_DIR, exist_ok=True)

def chunk_text(text, size=CHUNK_SIZE, overlap=OVERLAP):
    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = start + size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        if start < 0:
            start = 0
    return chunks

def process_file(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    base = os.path.basename(path).rsplit(".", 1)[0]
    chunks = chunk_text(text)
    outputs = []
    for i, c in enumerate(chunks):
        meta = {
            "chunk_id": f"{base}__chunk{i}",
            "source": base,
            "chunk_index": i,
            "fetch_date": None,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "text": c
        }
        out_path = os.path.join(CHUNKS_DIR, f"{meta['chunk_id']}.json")
        with open(out_path, "w", encoding="utf-8") as fo:
            json.dump(meta, fo, ensure_ascii=False)
        outputs.append(out_path)
    return outputs

def run_all():
    files = glob.glob(os.path.join(EXTRACTED_DIR, "*.txt"))
    if not files:
        print(f"No extracted .txt files found in '{EXTRACTED_DIR}'. Run extractor.py first.")
        return
    total = 0
    for path in files:
        outs = process_file(path)
        print(f"[+] Created {len(outs)} chunks from {os.path.basename(path)}")
        total += len(outs)
    print(f"--- Chunking complete: {total} chunks created ---")

if __name__ == "__main__":
    run_all()
