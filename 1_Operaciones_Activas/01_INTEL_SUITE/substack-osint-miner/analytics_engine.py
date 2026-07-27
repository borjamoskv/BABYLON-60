# C5-REAL EXERGY CERTIFIED
import re
import numpy as np
from sklearn.cluster import DBSCAN
from collections import Counter

class AnalyticsEngine:
    """C5-REAL decouple of ML and NLP analytics from the CLI layer."""
    def __init__(self):
        self.stopwords = set(["el", "la", "de", "que", "en", "un", "una", "y", "o", "a", "del", "se", "con", "para", "como", "al", "los", "las", "por", "su", "sus", "es", "este", "esta", "esto", "the", "and", "of", "to", "a", "is", "in", "that", "it", "on", "for", "with", "as", "was", "at"])

    def extract_keywords(self, texts):
        all_words = []
        for text in texts:
            words = re.findall(r'\b[a-zA-Záéíóúüñ]{3,}\b', text.lower())
            all_words.extend([w for w in words if w not in self.stopwords])
        common_words = [w[0] for w in Counter(all_words).most_common(5)]
        return ", ".join(common_words) if common_words else "None"

    def process_graph_clusters(self, G, eps, min_samples):
        post_nodes = [node for node, attr in G.nodes(data=True) if attr.get("type") == "post" and "embedding" in attr]
        if len(post_nodes) < 2:
            return None, []

        embeddings = np.array([G.nodes[node]["embedding"] for node in post_nodes])
        db = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine")
        labels = db.fit_predict(embeddings)

        clusters = {}
        for node, label in zip(post_nodes, labels):
            label_key = int(label)
            if label_key not in clusters: clusters[label_key] = []
            clusters[label_key].append(node)

        sync_relations = []
        cluster_summaries = []

        for c_id, nodes in clusters.items():
            c_name = f"Cluster_{c_id}" if c_id != -1 else "Outliers (Noise)"

            roles = [G.nodes[n].get("classification", "Unknown") for n in nodes]
            dominant_role = Counter(roles).most_common(1)[0][0] if roles else "Unknown"

            authors = list(set([G.nodes[n].get("author", "Unknown") for n in nodes]))

            texts = [G.nodes[n].get("text", "") for n in nodes]
            keywords_str = self.extract_keywords(texts)

            cluster_summaries.append({
                "c_id": str(c_id) if c_id != -1 else "Outliers",
                "keywords": keywords_str,
                "dominant_role": dominant_role,
                "node_count": str(len(nodes)),
                "authors_str": ", ".join(authors)
            })

            for n in nodes:
                G.nodes[n]["cluster_id"] = c_id
                sync_relations.append((n, c_name, {"keywords": keywords_str, "dominant_role": dominant_role}))

        return cluster_summaries, sync_relations
