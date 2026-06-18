import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from typing import List, Tuple
from rag.embedding import EmbeddingModel
import numpy as np
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "storage", "npc_memory.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "storage")

def get_all_turns(db_path: str = DB_PATH) -> List[dict]:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""SELECT id, text 
                   FROM conversation_turns 
                   WHERE text IS NOT NULL AND text != ''
                    """)
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "text": row[1]} for row in rows]

if __name__ == "__main__":
    model = EmbeddingModel()
    turns = get_all_turns(DB_PATH)
    if not turns:
        print("No turns found in database.")
        exit(0)
    texts = [t["text"] for t in turns]
    ids = [t["id"] for t in turns]
    embeddings = model.encode(texts)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    np.save(os.path.join(OUTPUT_DIR, "embeddings.npy"), embeddings)
    with open(os.path.join(OUTPUT_DIR, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump({"ids": ids, "texts": texts}, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(ids)} embeddings to {OUTPUT_DIR}")

