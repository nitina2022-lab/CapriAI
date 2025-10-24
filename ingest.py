from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from tqdm import tqdm

# Load .env variables
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_KEY:
    raise SystemExit("OPENAI_API_KEY not found in environment/.env. Please add it and retry.")

# Initialize client
client = OpenAI(api_key=OPENAI_KEY)
EMBED_MODEL = "text-embedding-3-small"

# Input/output paths
CHUNKS_DIR = "chunks"
OUTPUT_FILE = "embeddings/embeddings.jsonl"

def embed_texts(texts):
    """Create embeddings for a list of text chunks."""
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=texts
    )
    return [d.embedding for d in response.data]

def extract_text_from_file(filepath):
    if filepath.endswith(".txt"):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read().strip()
    elif filepath.endswith(".json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Try to extract from known fields
                if isinstance(data, dict) and "text" in data:
                    return data["text"]
                elif isinstance(data, list) and len(data) > 0 and "text" in data[0]:
                    return " ".join([x.get("text", "") for x in data])
                else:
                    return json.dumps(data)
        except Exception as e:
            print(f"⚠️ Could not parse {filepath}: {e}")
            return ""
    return ""

def run():
    all_texts = []
    if not os.path.isdir(CHUNKS_DIR):
        raise SystemExit(f"Chunks directory '{CHUNKS_DIR}' not found. Run extractor/fetcher first.")
    for fname in sorted(os.listdir(CHUNKS_DIR)):
        if fname.endswith((".txt", ".json")):
            path = os.path.join(CHUNKS_DIR, fname)
            txt = extract_text_from_file(path)
            if txt:
                all_texts.append(txt)

    if not all_texts:
        raise SystemExit("No text chunks found in the 'chunks' folder.")

    print(f"Creating embeddings for {len(all_texts)} chunks...")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        for i in tqdm(range(0, len(all_texts), 16), desc="embedding batches"):
            batch = all_texts[i:i + 16]
            try:
                embeddings = embed_texts(batch)
            except Exception as e:
                print("Embedding API error:", e)
                raise
            for j, emb in enumerate(embeddings):
                json.dump({
                    "id": i + j,
                    "text": batch[j],
                    "embedding": emb
                }, out)
                out.write("\n")

    print(f"✅ Completed embeddings for {len(all_texts)} chunks")
    print(f"✅ Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    run()
