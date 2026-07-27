# C5-REAL EXERGY CERTIFIED
import feedparser
import requests
import time
from bs4 import BeautifulSoup
import re
import datetime
import urllib.parse
from rich.console import Console
from vector_engine import NarrativeEngine

console = Console()

class SubstackLiveIngestor:
    def __init__(self, miner_instance):
        self.miner = miner_instance
        self.vector_engine = NarrativeEngine()

    def fetch_rss(self, publication_url):
        rss_url = f"{publication_url.rstrip('/')}/feed"
        console.print(f"[dim]Fetching RSS feed from: {rss_url}[/dim]")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml'
        }
        try:
            response = requests.get(rss_url, headers=headers, timeout=10)
            feed = feedparser.parse(response.content)
        except Exception as e:
            console.print(f"[bold red]⚠ Connection error: {str(e)}[/bold red]")
            return []

        if not feed.entries:
            console.print("[bold red]⚠ No entries found or invalid feed.[/bold red]")
            return []

        console.print(f"[green]✔ Found {len(feed.entries)} posts in feed.[/green]")
        return feed.entries

    def fetch_full_post(self, url):
        """Fetch full HTML and extract paragraphs, text, and date"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')

            # Extract paragraphs
            body = soup.find('div', class_='available-content') or soup.find('div', class_='post-content') or soup.body
            paragraphs = []
            if body:
                for p in body.find_all('p'):
                    p_text = p.get_text(strip=True)
                    if len(p_text) > 30:
                        paragraphs.append(p_text)

            text_content = body.get_text(" ", strip=True) if body else ""
            pub_date = self.miner.get_published_date(res.text)

            return {
                "text": text_content,
                "paragraphs": paragraphs,
                "pub_date": pub_date
            }
        except Exception as e:
            console.print(f"[dim red]Error fetching post {url}: {e}[/dim red]")
            return None

    def find_potential_sources(self, links, target_domain):
        """Find links that point to other Substack posts (potential sources)"""
        sources = []
        for l in links:
            if '/p/' in l and target_domain not in l and 'substack.com' in l:
                sources.append(l)
        return list(set(sources))

    def parse_iso_date(self, date_str):
        if not date_str:
            return None
        # Remove offset timezone colon if present
        date_str = re.sub(r'(\d\d):(\d\d)$', r'\1\2', date_str)
        # Handle Zulu
        if date_str.endswith('Z'):
            date_str = date_str[:-1] + '+0000'

        formats = [
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d"
        ]
        for fmt in formats:
            try:
                return datetime.datetime.strptime(date_str, fmt)
            except Exception:
                pass
        return None


