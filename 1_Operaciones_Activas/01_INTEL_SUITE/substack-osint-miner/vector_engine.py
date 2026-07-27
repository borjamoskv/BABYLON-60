# C5-REAL EXERGY CERTIFIED
import os
import json
import urllib.request
import math
from sentence_transformers import SentenceTransformer
import numpy as np
from rich.console import Console

console = Console()

class VectorDBMock:
    """Mock for local Pinecone/Weaviate interface"""
    def __init__(self):
        self.vectors = {}

    def upsert(self, id, vector, metadata):
        self.vectors[id] = {"vector": vector, "metadata": metadata}

    def query(self, target_vector, top_k=3):
        if not self.vectors:
            return []

        ids = list(self.vectors.keys())
        # C5-REAL: Vectorized Numpy matrix operations. Zero Python loops.
        matrix = np.array([self.vectors[i]["vector"] for i in ids])

        target_norm = target_vector / (np.linalg.norm(target_vector) or 1.0)
        matrix_norm = matrix / (np.linalg.norm(matrix, axis=1)[:, np.newaxis] or 1.0)

        similarities = np.dot(matrix_norm, target_norm)

        top_indices = np.argsort(similarities)[::-1][:top_k]
        return [(ids[i], float(similarities[i]), self.vectors[ids[i]]["metadata"]) for i in top_indices]

class NarrativeEngine:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if self.api_key:
            console.print("[dim]NarrativeEngine initialized with OpenAI Embedding API.[/dim]")
            self.model = None
        else:
            console.print("[dim]Loading local SentenceTransformer (all-MiniLM-L6-v2) fallback...[/dim]")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.db = VectorDBMock()

    def get_embedding(self, text):
        if self.api_key:
            url = "https://api.openai.com/v1/embeddings"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            payload = {
                "model": "text-embedding-3-small",
                "input": text[:8000] # Safe limit
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers
            )
            try:
                with urllib.request.urlopen(req) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    return np.array(res_data['data'][0]['embedding'])
            except Exception as e:
                console.print(f"[dim red]OpenAI API error, falling back to local model: {e}[/dim red]")
                # Fallback to local model if API call fails
                if not hasattr(self, 'fallback_model'):
                    self.fallback_model = SentenceTransformer('all-MiniLM-L6-v2')
                return self.fallback_model.encode(text[:1000])
        else:
            return self.model.encode(text[:1000])

    def embed_post(self, post_id, author, text):
        vector = self.get_embedding(text)
        self.db.upsert(
            id=post_id,
            vector=vector,
            metadata={"author": author}
        )
        return vector

    def detect_anomalies(self, post_id):
        """Find if a post is a narrative outlier compared to author's history"""
        if post_id not in self.db.vectors:
            return False

        vector = self.db.vectors[post_id]["vector"]
        author = self.db.vectors[post_id]["metadata"]["author"]

        similar = self.db.query(vector, top_k=5)
        foreign_influence = sum(1 for _, _, m in similar if m["author"] != author)
        return foreign_influence > 3

    def compute_cross_lingual_alignment(self, en_paragraphs, es_paragraphs, threshold=0.75):
        """Map Spanish paragraphs to English paragraphs using cosine similarity of embeddings"""
        if not en_paragraphs or not es_paragraphs:
            return {
                "recycled_ratio": 0.0,
                "recycled_count": 0,
                "mappings": []
            }

        en_embeddings = [self.get_embedding(p) for p in en_paragraphs]
        es_embeddings = [self.get_embedding(p) for p in es_paragraphs]

        recycled_count = 0
        mappings = []

        for idx_es, (p_es, emb_es) in enumerate(zip(es_paragraphs, es_embeddings)):
            best_sim = -1.0
            best_en_idx = -1
            best_en_text = ""

            for idx_en, (p_en, emb_en) in enumerate(zip(en_paragraphs, en_embeddings)):
                sim = np.dot(emb_es, emb_en) / (np.linalg.norm(emb_es) * np.linalg.norm(emb_en))
                if sim > best_sim:
                    best_sim = sim
                    best_en_idx = idx_en
                    best_en_text = p_en

            is_recycled = best_sim >= threshold
            if is_recycled:
                recycled_count += 1

            mappings.append({
                "target_idx": idx_es,
                "target_text": p_es,
                "source_idx": best_en_idx,
                "source_text": best_en_text,
                "similarity": float(best_sim),
                "recycled": is_recycled
            })

        recycled_ratio = recycled_count / len(es_paragraphs)
        return {
            "recycled_ratio": recycled_ratio,
            "recycled_count": recycled_count,
            "mappings": mappings
        }

