#!/bin/bash
# run_pipeline.sh - simple pipeline to fetch, extract, chunk, embed and upsert for CapriAI
# Run this from the CapriAI project folder with your .venv activated.

set -euo pipefail

echo "1) Ensure virtualenv is active (should show '(.venv)' in prompt)."
echo

echo "2) Fetching raw pages (fetcher.py)"
python3 fetcher.py
echo

echo "3) Extracting text from raw files (extractor.py)"
python3 extractor.py
echo

echo "4) Chunking text into chunks/ (chunker.py)"
python3 chunker.py
echo

echo "5) List resulting chunk files (first 20)"
ls -la chunks | head -n 20
echo

echo "If chunks exist, next step is to create embeddings:"
echo "6) Create embeddings (ingest.py)"
echo "   (this will call OpenAI and consume credit from your account)"
python3 ingest.py
echo

echo "7) Upload embeddings to Pinecone (upsert_pinecone.py)"
python3 upsert_pinecone.py
echo

echo "Pipeline completed. Check logs above for any errors and paste them back here if something failed."
