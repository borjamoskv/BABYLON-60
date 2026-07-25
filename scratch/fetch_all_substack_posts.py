# C5-REAL EXERGY CERTIFIED
"""
Fetch and catalog all posts from borjamoskv.substack.com archive.
"""

import urllib.request
import json
import os

url = "https://borjamoskv.substack.com/api/v1/archive?sort=new&search=&offset=0&limit=50"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))

posts = []
for p in data:
    post_info = {
        "id": p.get("id"),
        "title": p.get("title"),
        "subtitle": p.get("subtitle", ""),
        "slug": p.get("slug"),
        "canonical_url": f"https://borjamoskv.substack.com/p/{p.get('slug')}",
        "post_date": p.get("post_date")
    }
    posts.append(post_info)

out_file = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/scratch/substack_archive_catalog.json"
os.makedirs(os.path.dirname(out_file), exist_ok=True)
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(posts, f, indent=2, ensure_ascii=False)

print(f"Fetched {len(posts)} posts from borjamoskv.substack.com archive!")
