import json
import faiss
import numpy as np
from typing import List, Dict
from rag.embedding import EmbeddingModel

class FaissIndex:
    def __init__(self, embedding_model: EmbeddingModel, index_path: str = "storage/faiss_index.index", metadata_path: str = "storage/metadata.json"):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.embedding_model = embedding_model
        self.embedding_path = "storage/embeddings.npy"
        self.index = None
        self.metadata = None
    
    def build_index(self): 
        embeddings = np.load(self.embedding_path)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)
        faiss.write_index(self.index, self.index_path)

    def load_index(self):
        if self.index is not None and self.metadata is not None:
            return
        self.index = faiss.read_index(self.index_path)
        with open(self.metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
    
    def search(self, query_text: str, top_k: int = 5) -> List[Dict]:
        if self.index is None or self.metadata is None:
            self.load_index()
        query_embedding = self.embedding_model.encode([query_text])
        D, I = self.index.search(query_embedding, top_k)
        results = []
        for j, idx in enumerate(I[0]):
            if idx < len(self.metadata["ids"]) and idx >= 0:  # 防止索引超出范围
                results.append({
                    "id": self.metadata["ids"][idx],
                    "text": self.metadata["texts"][idx],
                    "distance": float(D[0][j])  # 将距离转换为float类型
                })
        return results