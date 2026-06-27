#!/usr/bin/env python3
"""
SOTA-Vector-Engine-Omega (V3)
Physical Vectorization Stage. Ingests Frontier_Node YAML data into a local ChromaDB instance.
Execution Mode: C5-REAL (Deterministic Local Storage)
"""

import os
import sys
import yaml
import json
import hashlib
import time

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    print("CRITICAL: chromadb not installed. Run 'pip install chromadb' to enable V3.")
    sys.exit(1)

CORTEX_DB_PATH = os.path.expanduser("~/.gemini/config/.cortex/vector_db")

def ensure_db_path():
    if not os.path.exists(CORTEX_DB_PATH):
        os.makedirs(CORTEX_DB_PATH)

def hash_content(content):
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def ingest_node(yaml_file_path):
    print(f"Ingesting {yaml_file_path} into SOTA Vector Engine...")
    
    with open(yaml_file_path, 'r') as f:
        try:
            data = yaml.safe_load(f)
        except Exception as e:
            print(f"Error parsing YAML: {e}")
            sys.exit(1)
            
    if "Frontier_Node" not in data:
        print("Error: Input does not contain a valid Frontier_Node.")
        sys.exit(1)
        
    node = data["Frontier_Node"]
    core_insight = node.get("Core_Insight", "")
    domain = node.get("Domain", "Unknown")
    confidence = node.get("confidence_score", 0.0)
    
    if confidence < 0.5:
        print(f"Warning: Low confidence score ({confidence}). Node ingested but flagged.")
        
    # Build a dense document string for embedding
    document = f"Domain: {domain}. Insight: {core_insight}. Mechanism: {node.get('Mechanism', '')}. Capability Delta: {node.get('Capability_Delta', {}).get('Description', '')}."
    
    node_id = hash_content(document)[:16]
    
    # Initialize ChromaDB
    ensure_db_path()
    client = chromadb.PersistentClient(path=CORTEX_DB_PATH)
    
    # Using local embedding function if OpenAI is not set
    # all-MiniLM-L6-v2 is default for ChromaDB
    emb_fn = embedding_functions.DefaultEmbeddingFunction()
    
    collection = client.get_or_create_collection(
        name="sota_frontier_nodes",
        embedding_function=emb_fn
    )
    
    # Check if exists
    res = collection.get(ids=[node_id])
    if res and res.get('ids') and len(res['ids']) > 0:
        print(f"Node {node_id} already exists in Cortex. Skipping.")
        sys.exit(0)
        
    metadata = {
        "domain": domain,
        "confidence": confidence,
        "timestamp": int(time.time()),
        "source": node.get("Evidence", [{}])[0].get("URI", "Unknown")
    }
    
    collection.add(
        documents=[document],
        metadatas=[metadata],
        ids=[node_id]
    )
    
    print(f"[C5-REAL] Frontier_Node {node_id} successfully embedded and crystallized in Cortex (Domain: {domain}).")

def main():
    if len(sys.argv) < 2:
        print("Usage: python sota_ingest.py <path_to_frontier_node.yaml>")
        sys.exit(1)
        
    target_file = sys.argv[1]
    if not os.path.exists(target_file):
        print(f"File not found: {target_file}")
        sys.exit(1)
        
    ingest_node(target_file)

if __name__ == "__main__":
    main()
