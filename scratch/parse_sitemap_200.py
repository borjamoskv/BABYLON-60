# C5-REAL EXERGY CERTIFIED
"""
Parse ALL 200 post URLs from borjamoskv.substack.com/sitemap.xml
"""

import urllib.request
import re
import json
import os

url = "https://borjamoskv.substack.com/sitemap.xml"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

with urllib.request.urlopen(req) as resp:
    xml_data = resp.read().decode("utf-8")

urls = sorted(list(set(re.findall(r'https://borjamoskv\.substack\.com/p/[^<" \n\r]+', xml_data))))

catalog_200 = []
for u in urls:
    slug = u.split("/")[-1].strip()
    title_readable = slug.replace("-", " ").title()
    catalog_200.append({"slug": slug, "canonical_url": u, "title": title_readable})

out_file = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/scratch/substack_complete_200_catalog.json"
os.makedirs(os.path.dirname(out_file), exist_ok=True)
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(catalog_200, f, indent=2, ensure_ascii=False)

print(f"PARSED SITEMAP: Extracted EXACTLY {len(catalog_200)} post URLs from sitemap.xml!")
