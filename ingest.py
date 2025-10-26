"""
Ingest script (safe to upload to GitHub)
- reads chunk JSON files from ./chunks (each file is expected to contain an object with 'id' and 'text' or similar)
- creates embeddings using OpenAI's `text-embedding-3-small` via the modern `openai` package (OpenAI client)
- writes results to embeddings/embeddings.jsonl (jsonlines)

Requirements (install in your virtualenv):
    pip install openai python-dotenv tqdm

IMPORTANT:
- Do NOT store your API key in this file. Put it into a .env file or export OPENAI_API_KEY in your shell.
  Example .env contents (DO NOT commit with real key):
      OPENAI_API_KEY=sk-...

- The script loads .env automatically from the current working directory if present.

Usage:
    python3 ingest.py

This file purposely contains no secrets. Keep your .env in the project root and DO NOT push it to GitHub.
"""

import os
import json
import time
import glob
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from tqdm import tqdm

# Modern OpenAI SDK
from openai import OpenAI
from openai import OpenAIError

# --- Configuration ---
CHUNKS_DIR = Path("chunks")
OUT_DIR = Path("embeddings")
OUT_DIR.mkdir(exist_ok=True)
OUT_FILE = OUT_DIR / "embeddings.jsonl"
EMBED_MODEL = "text-embedding-3-small"  # change if you prefer another model
BATCH_SIZE = 16
MAX_RETRIES = 6
INITIAL_BACKOFF = 1.0

# --- Helpers ---

def load_env():
    # Load .env if present (safe) and return whether an OPENAI_API_KEY is available
    dotenv_path = Path(os.getcwd()) / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path)

    return bool(os.getenv("OPENAI_API_KEY"))


def find_chunk_files(directory: Path) -> List[Path]:
    # find json files in chunks directory
    if not directory.exists():
        return []
    return sorted(directory.glob("*.json"))


def read_chunk_file(p: Path):
    """Return a list of dicts with keys: id, text (best-effort)."""
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        # try line-delimited
        try:
            lines = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
            raw = lines
        except Exception:
            print(f"WARNING: cannot parse {p} - skipping ({e})")
            return []

    items = []
    if isinstance(raw, dict):
        # If file is a single object that contains text or chunks
        # Try several common keys
        if "chunks" in raw and isinstance(raw["chunks"], list):
            for c in raw["chunks"]:
                text = c.get("text") or c.get("content") or c.get("body") or c.get("page_text")
                if text:
                    items.append({"id": c.get("id") or c.get("url") or p.stem, "text": text})
        else:
            # try to interpret top-level as a single chunk
            text = raw.get("text") or raw.get("content") or raw.get("body") or raw.get("page_text")
            if text:
                items.append({"id": raw.get("id") or raw.get("url") or p.stem, "text": text})
    elif isinstance(raw, list):
        for obj in raw:
            if not isinstance(obj, dict):
                continue
            text = obj.get("text") or obj.get("content") or obj.get("body") or obj.get("page_text")
            if text:
                items.append({"id": obj.get("id") or obj.get("url") or (p.stem + f"_{len(items)}"), "text": text})

    return items


def batches(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def create_client():
    # create OpenAI client using OPENAI_API_KEY from env
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment. Put it into .env or export in shell.")
    return OpenAI(api_key=api_key)


def embed_texts(client: OpenAI, texts: List[str]):
    """Call OpenAI embeddings API with retry/backoff and return list of embedding vectors.
    Uses the modern OpenAI SDK client.embeddings.create(...)
    """
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
            # resp.data is a list of embedding objects - each has .embedding
            embeddings = [d.embedding for d in resp.data]
            return embeddings
        except OpenAIError as e:
            # Some errors we may retry (rate limit, transient). For others, raise.
            msg = str(e)
            is_rate = "rate limit" in msg.lower() or getattr(e, "http_status", None) == 429
            is_quota = "quota" in msg.lower() or getattr(e, "http_status", None) == 402
            backoff = INITIAL_BACKOFF * (2 ** attempt)
            if attempt + 1 < MAX_RETRIES and (is_rate or getattr(e, "retryable", False)):
                print(f"Embedding API error: {e} — retrying in {backoff:.1f}s...")
                time.sleep(backoff)
                continue
            else:
                # Bubble up for non-retryable error or out of retries
                raise
    raise RuntimeError("Failed to get embeddings after retries")


def main():
    ok = load_env()
    if not ok and not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not found in environment or .env — please set it and re-run.")
        return

    client = create_client()

    chunk_files = find_chunk_files(CHUNKS_DIR)
    if not chunk_files:
        print(f"No chunk files found in {CHUNKS_DIR}. Create chunks first and re-run.")
        return

    # read chunks
    all_chunks = []
    for cf in chunk_files:
        items = read_chunk_file(cf)
        all_chunks.extend(items)

    if not all_chunks:
        print("No text chunks could be read from chunk files.")
        return

    print(f"Creating embeddings for {len(all_chunks)} chunks (batch_size={BATCH_SIZE})")

    out_lines = []
    # process in batches
    for batch in tqdm(list(batches(all_chunks, BATCH_SIZE)), desc="embedding batches"):
        texts = [c["text"] for c in batch]
        ids = [c.get("id") or f"chunk_{i}" for i, c in enumerate(batch)]
        try:
            vectors = embed_texts(client, texts)
        except Exception as e:
            print("ERROR while creating embeddings:", e)
            print("Aborting. Fix the problem (e.g. quota, key) and re-run.")
            return

        for item, emb in zip(batch, vectors):
            out_obj = {
                "id": str(item.get("id") or item.get("url") or ""),
                "text": item.get("text"),
                "embedding": emb,
            }
            out_lines.append(out_obj)

    # write to jsonl
    with OUT_FILE.open("w", encoding="utf-8") as fh:
        for o in out_lines:
            fh.write(json.dumps(o, ensure_ascii=False) + "\n")

    print(f"✅ Completed embeddings for {len(out_lines)} chunks")
    print(f"✅ Saved to {OUT_FILE}")


if __name__ == "__main__":
    main()
