# CapriAI - Local RAG Pipeline

This folder contains simple scripts to build a local retrieval-augmented system for CapriAI.
Run the scripts in order to fetch web pages, extract text, chunk, create embeddings, and (optionally) upsert to Pinecone.

## Quick workflow (local)
1. Prepare your environment variables in `.env` (OPENAI_API_KEY, PINECONE_API_KEY).  
2. Install Python packages:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
3. Fetch pages:
   ```bash
   python3 fetcher.py
   ```
4. Extract cleaned text:
   ```bash
   python3 extractor.py
   ```
5. Chunk the text:
   ```bash
   python3 chunker.py
   ```
6. Generate embeddings (saved to `embeddings/embeddings.jsonl`):
   ```bash
   python3 ingest.py
   ```
7. Upsert to Pinecone (optional):
   ```bash
   python3 upsert_pinecone.py
   ```

## Notes
- `ingest.py` generates embeddings using OpenAI and stores them locally. This lets you inspect or re-run uploads later.
- `upsert_pinecone.py` uses the new Pinecone Python API. You can tweak cloud/region in the script.
- `change_detector.py` is a simple snapshot-based change detector for `raw_data/` files.
- `retriever_api.py` exposes a minimal Flask API to query Pinecone and return top-k results.

## Support
If you run into issues with compiling packages on macOS, refer to the main chat instructions about installing Xcode Command Line Tools and Rust.
