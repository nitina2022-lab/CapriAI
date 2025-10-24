"""
change_detector.py
Simple change detector comparing hashes of raw HTML snapshots.
Usage:
  python3 change_detector.py
It writes/updates changelog.json and a small state file .state_hashes.json
"""

import os
import hashlib
import json
from glob import glob
from datetime import datetime

RAW_DIR = "raw_data"
STATE_FILE = ".state_hashes.json"
CHANGELOG = "changelog.json"

def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            data = f.read(8192)
            if not data:
                break
            h.update(data)
    return h.hexdigest()

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def append_changelog(entry):
    logs = []
    if os.path.exists(CHANGELOG):
        with open(CHANGELOG, "r", encoding="utf-8") as f:
            logs = json.load(f)
    logs.append(entry)
    with open(CHANGELOG, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2)

def run():
    os.makedirs(RAW_DIR, exist_ok=True)
    state = load_state()
    files = glob(os.path.join(RAW_DIR, "*.html"))
    if not files:
        print("No snapshots found in raw_data/. Run fetcher.py first.")
        return
    changed = False
    for path in files:
        h = file_hash(path)
        name = os.path.basename(path)
        old = state.get(name)
        if old != h:
            print("Change detected:", name)
            entry = {
                "file": name,
                "old_hash": old,
                "new_hash": h,
                "detected_at": datetime.utcnow().isoformat() + "Z"
            }
            append_changelog(entry)
            state[name] = h
            changed = True
    if changed:
        save_state(state)
        print("Changelog updated:", CHANGELOG)
    else:
        print("No changes detected.")

if __name__ == "__main__":
    run()
