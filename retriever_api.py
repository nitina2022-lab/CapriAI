#!/usr/bin/env python3
"""
retriever_api.py
Simple Flask service that queries Pinecone index given a text query.
Requires OPENAI_API_KEY to embed the query and PINECONE_API_KEY for Pinecone.
"""

import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from openai import OpenAI
from pinecone import Pinecone

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
if not OPENAI_API_KEY or not PINECONE_API_KEY:
    raise SystemExit("Please set OPENAI_API_KEY and PINECONE_API_KEY in .env")

client = OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)
INDEX_NAME = "capri-index"
index = pc.Index(INDEX_NAME)

app = Flask(__name__)

def embed_query(q):
    resp = client.embeddings.create(model="text-embedding-3-small", input=q)
    return resp.data[0].embedding

@app.route("/retrieve", methods=["POST"])
def retrieve():
    body = request.get_json() or {}
    q = body.get("q", "")
    k = int(body.get("k", 5))
    if not q:
        return jsonify({"error": "missing 'q' parameter"}), 400
    vec = embed_query(q)
    resp = index.query(vector=vec, top_k=k, include_metadata=True)
    results = []
    matches = getattr(resp, "matches", None) or resp.get("matches", [])
    for item in matches:
        item_id = getattr(item, "id", None) or item.get("id")
        score = getattr(item, "score", None) or item.get("score")
        metadata = getattr(item, "metadata", None) or item.get("metadata")
        results.append({"id": item_id, "score": score, "metadata": metadata})
    return jsonify({"query": q, "results": results})

if __name__ == "__main__":
    app.run(port=8080, debug=True)
