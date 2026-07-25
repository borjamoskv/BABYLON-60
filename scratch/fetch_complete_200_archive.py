# C5-REAL EXERGY CERTIFIED
"""
Fetch ALL ~200 posts from borjamoskv.substack.com archive by paginating offset.
"""

import urllib.request
import json
import os

all_posts = []
offset = 0
limit = 50

while True:
    url = f"https://borjamoskv.substack.com/api/v1/archive?sort=new&search=&offset={offset}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if not data:
                break
            for p in data:
                all_posts.append(
                    {
                        "id": p.get("id"),
                        "title": p.get("title", ""),
                        "subtitle": p.get("subtitle", ""),
                        "slug": p.get("slug"),
                        "canonical_url": f"https://borjamoskv.substack.com/p/{p.get('slug')}",
                        "post_date": p.get("post_date"),
                    }
                )
            print(f"Offset {offset}: fetched {len(data)} posts. Total so far: {len(all_posts)}")
            if len(data) < limit:
                break
            offset += limit
    except (OSError, ValueError) as e:
        print(f"Error at offset {offset}: {e}")
        break

out_file = (
    "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/scratch/substack_complete_archive_catalog.json"
)
os.makedirs(os.path.dirname(out_file), exist_ok=True)
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(all_posts, f, indent=2, ensure_ascii=False)

print(f"COMPLETED FULL PAGINATION: Fetched {len(all_posts)} posts total from borjamoskv.substack.com archive!")
