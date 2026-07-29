# C5-REAL EXERGY CERTIFIED
"""
Substack Reverse Engineering OSINT Miner & Notes Extractor
Author: borjamoskv
Classification: C5-REAL

Full extraction suite for Substack Profiles, Notes, Newsletters, TTS Audio, and Recommendation Topology.
"""

import sys
import os
import json
import re
import time
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional

class SubstackIntelMiner:
    def __init__(self, handle: str, subdomain: Optional[str] = None):
        self.handle = handle.replace("@", "").strip()
        self.subdomain = subdomain or self.handle
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*'
        }
        self.profile_data: Dict[str, Any] = {}
        self.notes: List[Dict[str, Any]] = []
        self.posts: List[Dict[str, Any]] = []
        self.recommendations: List[str] = []

    def _http_get_json(self, url: str) -> Optional[Any]:
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            print(f"[C5-REAL WARN] Error fetching JSON from {url}: {e}")
            return None

    def _http_get_html(self, url: str) -> Optional[str]:
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.read().decode('utf-8')
        except Exception as e:
            print(f"[C5-REAL WARN] Error fetching HTML from {url}: {e}")
            return None

    def fetch_profile(self) -> Dict[str, Any]:
        """Fetch public profile metadata for the given handle."""
        print(f"[C5-REAL] Extraendo perfil público de @{self.handle}...")
        url = f"https://substack.com/api/v1/user/{self.handle}/public_profile"
        data = self._http_get_json(url)
        if data:
            self.profile_data = data
            print(f"[C5-REAL] Perfil encontrado: ID {data.get('id')} | Nombre: {data.get('name')}")
        else:
            print(f"[C5-REAL FAIL] No se pudo obtener el perfil para @{self.handle}")
        return self.profile_data

    def fetch_notes_and_activity(self, max_items: int = 50) -> List[Dict[str, Any]]:
        """Fetch short-form Notes and social activity feed using pagination cursor."""
        user_id = self.profile_data.get('id')
        if not user_id:
            print("[C5-REAL WARN] user_id no disponible. Intentando resolver perfil primero...")
            self.fetch_profile()
            user_id = self.profile_data.get('id')

        if not user_id:
            print("[C5-REAL ERROR] Imposible obtener feed sin user_id.")
            return []

        print(f"[C5-REAL] Minando Substack Notes del usuario ID {user_id}...")
        cursor = None
        collected = 0

        while collected < max_items:
            url = f"https://substack.com/api/v1/reader/feed/profile/{user_id}?limit=20"
            if cursor:
                url += f"&nextCursor={urllib.parse.quote(cursor)}"

            feed_res = self._http_get_json(url)
            if not feed_res or 'items' not in feed_res:
                break

            items = feed_res.get('items', [])
            if not items:
                break

            for item in items:
                item_type = item.get('type')
                comment = item.get('comment')
                post = item.get('post')

                note_entry = {
                    "type": item_type,
                    "id": item.get('id'),
                    "timestamp": item.get('timestamp') or (comment.get('created_at') if comment else None),
                }

                if comment:
                    note_entry.update({
                        "note_id": f"c-{comment.get('id')}",
                        "raw_id": comment.get('id'),
                        "body": comment.get('body'),
                        "body_html": comment.get('body_html'),
                        "reactions": comment.get('reactions_count', 0),
                        "restacks": comment.get('restacks_count', 0),
                        "replies": comment.get('children_count', 0),
                        "url": f"https://substack.com/@{self.handle}/note/c-{comment.get('id')}"
                    })
                elif post:
                    note_entry.update({
                        "post_id": post.get('id'),
                        "title": post.get('title'),
                        "slug": post.get('slug'),
                        "canonical_url": post.get('canonical_url'),
                        "subtitle": post.get('subtitle')
                    })

                self.notes.append(note_entry)
                collected += 1
                if collected >= max_items:
                    break

            cursor = feed_res.get('nextCursor')
            if not cursor:
                break
            time.sleep(0.5)

        print(f"[C5-REAL] Se extrajeron {len(self.notes)} ítems de actividad/Notes.")
        return self.notes

    def fetch_archive_posts(self, limit: int = 24) -> List[Dict[str, Any]]:
        """Fetch long-form articles from the publication archive."""
        # Check publications linked in profile
        subdomains_to_check = [self.subdomain]
        for pub in self.profile_data.get('publications', []):
            sd = pub.get('subdomain')
            if sd and sd not in subdomains_to_check:
                subdomains_to_check.append(sd)

        for sd in subdomains_to_check:
            print(f"[C5-REAL] Extraendo archivo de artículos de: {sd}.substack.com...")
            url = f"https://{sd}.substack.com/api/v1/archive?sort=new&limit={limit}"
            archive_data = self._http_get_json(url)

            if isinstance(archive_data, list):
                for post in archive_data:
                    audio_items = post.get('audio_items', [])
                    tts_url = audio_items[0].get('audio_url') if audio_items else None

                    bylines = post.get('publishedBylines') or [{}]
                    bestseller_tier = bylines[0].get('bestseller_tier') if (bylines and isinstance(bylines, list) and len(bylines) > 0) else None

                    post_obj = {
                        "id": post.get('id'),
                        "publication": sd,
                        "title": post.get('title'),
                        "slug": post.get('slug'),
                        "post_date": post.get('post_date'),
                        "audience": post.get('audience'),
                        "canonical_url": post.get('canonical_url'),
                        "subtitle": post.get('subtitle'),
                        "cover_image": post.get('cover_image'),
                        "wordcount": post.get('wordcount'),
                        "reactions": post.get('reactions'),
                        "reaction_count": post.get('reaction_count', 0),
                        "comment_count": post.get('comment_count', 0),
                        "restacks": post.get('restacks', 0),
                        "tags": [t.get('name') for t in post.get('postTags', [])],
                        "tts_audio_url": tts_url,
                        "bestseller_tier": bestseller_tier
                    }
                    self.posts.append(post_obj)

        print(f"[C5-REAL] Total de publicaciones extraídas: {len(self.posts)}")
        return self.posts

    def fetch_recommendations(self) -> List[str]:
        """Fetch public recommendation network graph for the publication."""
        print(f"[C5-REAL] Minando recomendaciones de: {self.subdomain}.substack.com...")
        url = f"https://{self.subdomain}.substack.com/recommendations"
        html = self._http_get_html(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a', href=lambda href: href and 'utm_source=recommendations_page' in href)

        recs = []
        for link in links:
            href = link.get('href', '')
            clean = re.sub(r'^(https?://)?(www\.)?', '', href).split('/')[0].split('?')[0]
            if clean and clean != f"{self.subdomain}.substack.com" and clean not in recs:
                recs.append(clean)

        self.recommendations = recs
        print(f"[C5-REAL] {len(recs)} recomendaciones descubiertas: {recs}")
        return recs

    def generate_report(self, output_dir: str = "output"):
        os.makedirs(output_dir, exist_ok=True)

        dataset = {
            "_meta": {
                "handle": self.handle,
                "subdomain": self.subdomain,
                "extracted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "classification": "C5-REAL EXERGY CERTIFIED"
            },
            "profile": self.profile_data,
            "notes": self.notes,
            "posts": self.posts,
            "recommendations": self.recommendations
        }

        # 1. Save raw JSON
        json_path = os.path.join(output_dir, f"intel_{self.handle}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        print(f"[C5-REAL] Dataset guardado en: {json_path}")

        # 2. Save Markdown Report
        md_path = os.path.join(output_dir, f"intel_{self.handle}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# INFORME DE INTELIGENCIA OSINT: @{self.handle}\n")
            f.write(f"**Generado:** {time.strftime('%Y-%m-%d %H:%M:%S')} | **Clasificación:** C5-REAL\n\n")

            prof = self.profile_data
            f.write("## 1. Perfil del Creador\n")
            f.write(f"- **Nombre:** {prof.get('name')}\n")
            f.write(f"- **Handle:** @{prof.get('handle')}\n")
            f.write(f"- **User ID:** {prof.get('id')}\n")
            f.write(f"- **Bio:** {prof.get('bio')}\n")
            f.write(f"- **Twitter:** @{prof.get('twitter_screen_name')}\n\n")

            f.write("## 2. Substack Notes Extraídas (Últimas Actividades)\n")
            for note in self.notes:
                if note.get('body'):
                    f.write(f"### Note [{note.get('note_id')}]({note.get('url')})\n")
                    f.write(f"> {note.get('body')}\n\n")
                    f.write(f"*Reacciones:* ❤ {note.get('reactions', 0)} | *Restacks:* 🔄 {note.get('restacks', 0)} | *Respuestas:* 💬 {note.get('replies', 0)}\n\n---\n\n")

            f.write("## 3. Publicaciones Principales\n")
            for post in self.posts[:10]:
                f.write(f"- [{post.get('title')}]({post.get('canonical_url')}) ({post.get('wordcount')} palabras, ❤ {post.get('reaction_count')})\n")
                if post.get('tts_audio_url'):
                    f.write(f"  - 🎧 *Audio TTS:* {post.get('tts_audio_url')}\n")

            f.write("\n## 4. Red de Recomendaciones Públicas\n")
            for rec in self.recommendations:
                f.write(f"- `{rec}`\n")

        print(f"[C5-REAL] Informe Markdown guardado en: {md_path}")
        return dataset

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "victormillan"
    miner = SubstackIntelMiner(handle=target, subdomain="escribepro")
    miner.fetch_profile()
    miner.fetch_notes_and_activity(max_items=30)
    miner.fetch_archive_posts(limit=15)
    miner.fetch_recommendations()
    miner.generate_report()
