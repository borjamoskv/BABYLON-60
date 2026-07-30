# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""translate_substack.py – Fetch Substack posts, translate into all Substack supported languages, and save bilingual markdown.

Features added:
- Uses a TranslatorManager (deep-translator) to translate the plain text of each post into the 18 languages Substack supports.
- Performs back‑translation verification (default similarity ≥70%).
- Saves a separate markdown file per post containing the original Spanish and each language section.
- Retains concurrent processing with 200 worker threads.
"""

import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import feedparser
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# Local modules
from scripts.translator_manager import TranslatorManager

# ---------- Configuration ----------
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "translated_posts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MAX_WORKERS = 200  # number of concurrent agents
SRC_LANG = "es"
SIMILARITY_THRESHOLD = 70

# ---------- Helper functions ----------

def fetch_post_links() -> List[str]:
    """Fetch post URLs from Substack RSS feed."""
    feed_url = "https://borjamoskv.substack.com/feed"
    feed = feedparser.parse(feed_url)
    links: List[str] = []
    for entry in feed.entries:
        url = getattr(entry, "link", None)
        if url:
            links.append(url)
    # Deduplicate while preserving order
    return list(dict.fromkeys(links))


def fetch_post_content(url: str) -> Dict:
    """Download a post, extract title and plain‑text body."""
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            break
        except Exception:
            if attempt < 2:
                time.sleep(2)
            else:
                raise
    soup = BeautifulSoup(resp.text, "html.parser")
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "Untitled"
    body_tag = soup.find("article") or soup.find("div", class_="post-content")
    body_html = str(body_tag) if body_tag else ""
    plain_text = BeautifulSoup(body_html, "html.parser").get_text(separator="\n")
    return {"url": url, "title": title, "plain_text": plain_text}


def save_multilingual(post: Dict, translations: Dict[str, tuple]):
    """Write a markdown file containing the original Spanish text and all language sections.
    ``translations`` maps ISO code -> (translated_text, verification_passed).
    """
    slug = post["title"].lower().replace(" ", "-")
    safe_slug = "".join(c for c in slug if c.isalnum() or c == "-")
    filename = OUTPUT_DIR / f"{safe_slug}.md"
    with open(filename, "w", encoding="utf-8") as fp:
        fp.write(f"# {post['title']}\n\n")
        fp.write("## Original (Spanish)\n\n")
        fp.write(post["plain_text"] + "\n\n")
        for code, (text, ok) in translations.items():
            # Map ISO code back to readable language name for headings
            lang_name = next((k for k, v in TranslatorManager.LANGUAGE_CODES.items() if v == code), code)
            fp.write(f"## Translation ({lang_name})\n\n")
            fp.write(text + "\n\n")
            fp.write(f"*Verification passed: {ok}*\n\n")
    return filename


def process_post(url: str) -> Path:
    post = fetch_post_content(url)
    manager = TranslatorManager(src_lang=SRC_LANG, verify=True, similarity_thresh=SIMILARITY_THRESHOLD)
    translations = manager.translate_all(post["plain_text"])
    return save_multilingual(post, translations)


def main(dry_run: bool = False):
    links = fetch_post_links()
    print(f"Found {len(links)} posts to translate.")
    if dry_run:
        print("Dry run enabled – exiting without processing.")
        return
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_post, url): url for url in links}
        for fut in tqdm(as_completed(futures), total=len(futures), unit="post"):
            try:
                _ = fut.result()
            except Exception as e:
                sys.stderr.write(f"Error processing {futures[fut]}: {e}\n")

if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    main(dry_run=dry)
