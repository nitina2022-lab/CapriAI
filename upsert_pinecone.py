from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
import os
import json

# Load .env variables
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# Set index name
INDEX_NAME = "capri-index"

# Check if index exists, create if not
existing_indexes = [index["name"] for index in pc.list_indexes()]
if INDEX_NAME not in existing_indexes:
    print(f"Creating index {INDEX_NAME}")
    pc.create_index(
        name=INDEX_NAME,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
else:
    print(f"Index '{INDEX_NAME}' already exists")

# Load embeddings from JSONL
embeddings_file = "embeddings/embeddings.jsonl"
if not os.path.exists(embeddings_file):
    raise FileNotFoundError(f"❌ {embeddings_file} not found. Run ingest.py first.")

print("Uploading embeddings to Pinecone...")

with open(embeddings_file, "r", encoding="utf-8") as f:
    vectors = [json.loads(line) for line in f]

index = pc.Index(INDEX_NAME)

# Upload in batches
batch_size = 100
for i in range(0, len(vectors), batch_size):
    batch = vectors[i:i + batch_size]
    ids = [str(v["id"]) for v in batch]
    embeds = [v["embedding"] for v in batch]
    metas = [{"text": v["text"]} for v in batch]
    index.upsert(vectors=zip(ids, embeds, metas))
    print(f"Upserted batch {i // batch_size + 1}")

print("✅ Pinecone index updated successfully.")
