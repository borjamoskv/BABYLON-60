#!/usr/bin/env python3
import os
import sys
import argparse
import datetime
import hashlib

VAULT_DIR = os.path.expanduser("~/.gemini/config/.cortex/memory_vault")

def ensure_vault():
    os.makedirs(VAULT_DIR, exist_ok=True)

def generate_filename(tags):
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    hash_str = hashlib.md5(date_str.encode()).hexdigest()[:6]
    clean_tags = "-".join([t.strip().replace(" ", "_") for t in tags.split(",")])[:30]
    return f"{date_str}_{clean_tags}_{hash_str}.md"

def store_memory(content, tags, conv_id):
    ensure_vault()
    filename = generate_filename(tags)
    filepath = os.path.join(VAULT_DIR, filename)
    
    date_iso = datetime.datetime.now().isoformat()
    
    yaml_frontmatter = f"""---
date: "{date_iso}"
tags: [{tags}]
conversation_id: "{conv_id}"
---

"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(yaml_frontmatter)
        f.write(content)
        f.write("\n")
    
    print(f"[C5-REAL] Memory crystallized in {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Episodic Memory Manager for Cortex Vault")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    store_parser = subparsers.add_parser("store")
    store_parser.add_argument("--content", required=True, help="The memory content to store")
    store_parser.add_argument("--tags", required=True, help="Comma-separated tags")
    store_parser.add_argument("--conv-id", default="unknown", help="Conversation ID context")
    
    args = parser.parse_args()
    
    if args.command == "store":
        store_memory(args.content, args.tags, args.conv_id)

if __name__ == "__main__":
    main()
