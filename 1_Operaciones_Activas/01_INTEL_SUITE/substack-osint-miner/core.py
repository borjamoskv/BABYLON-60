# C5-REAL EXERGY CERTIFIED
import re
import datetime
import urllib.parse
import json
from bs4 import BeautifulSoup
import networkx as nx

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

class SubstackMiner:
    def __init__(self):
        self.G = nx.DiGraph()

    def extract_entities(self, html):
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ")
        emails = set(EMAIL_RE.findall(text))

        authors = set()
        links = set()

        for a in soup.find_all("a"):
            href = a.get("href", "")
            if href:
                links.add(href)

        for tag in soup.find_all(["meta", "h1", "h2"]):
            content = tag.get("content") or tag.text
            if content:
                authors.add(content.strip())

        return {
            "emails": list(emails),
            "authors": list(authors),
            "links": list(links),
            "text": text[:50000]
        }

    def get_published_date(self, html):
        """Helper to parse ISO publish date from HTML metadata"""
        soup = BeautifulSoup(html, "html.parser")
        # Try JSON-LD datePublished
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and "datePublished" in data:
                    return data["datePublished"]
            except Exception:
                pass

        # Try article:published_time
        meta = soup.find("meta", {"property": "article:published_time"})
        if meta and meta.get("content"):
            return meta.get("content")

        # Try other common tags
        meta_pub = soup.find("meta", {"name": "pubdate"})
        if meta_pub and meta_pub.get("content"):
            return meta_pub.get("content")

        return None

    def analyze_speculative_ratio(self, text):
        """Sentence-level ratio of speculative statements lacking empirical anchors"""
        spec_patterns = [
            r'\b(?:debería|podría|habría|sería|tendría|estaría|surjan|irá|irán|hará|harán|cambiará|morirá|morirán)\b',
            r'\b(?:quizás|tal vez|probablemente|posiblemente|especula|asume|creo|pienso)\b',
            r'\b(?:should|would|could|will|might|probably|maybe|speculate|think|believe)\b'
        ]
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        if not sentences:
            return 0.0

        speculative_count = 0
        for s in sentences:
            has_spec = any(re.search(pat, s, re.I) for pat in spec_patterns)
            has_evidence = any(c.isdigit() for c in s) or "http" in s
            if has_spec and not has_evidence:
                speculative_count += 1
        return speculative_count / len(sentences)

    def analyze_unverifiable_ratio(self, text):
        """Ratio of claim statements lacking quotes, data, or link anchors"""
        claim_patterns = [
            r'\b(?:afirma|señala|dice|asegura|concluye|demuestra|estudio|algoritmo|modelo)\b',
            r'\b(?:claims|says|states|concludes|shows|study|algorithm|model)\b'
        ]
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        if not sentences:
            return 0.0

        unverifiable_count = 0
        for s in sentences:
            has_claim = any(re.search(pat, s, re.I) for pat in claim_patterns)
            has_anchor = "http" in s or any(c.isdigit() for c in s) or '"' in s or '“' in s
            if has_claim and not has_anchor:
                unverifiable_count += 1
        return unverifiable_count / len(sentences)

    def classify_node(self, recycled_ratio, humo_index):
        if recycled_ratio >= 0.40 and humo_index < 0.30:
            return "Epistemic CDN"
        elif recycled_ratio >= 0.40 and humo_index >= 0.30:
            return "Hype Arbitrage"
        elif recycled_ratio < 0.40 and humo_index < 0.30:
            return "Original Research"
        else:
            return "Hype Generator"

    def add_post_node(self, post_id, properties):
        self.G.add_node(post_id, type="post", **properties)

    def add_arbitrage_edge(self, target_post, source_post, properties):
        self.G.add_node(source_post, type="post")
        self.G.add_edge(target_post, source_post, type="ARBITRAGES", **properties)

    def add_post(self, post_id, author, emails, links, properties=None):
        props = properties or {"type": "post"}
        self.G.add_node(post_id, **props)
        self.G.add_node(author, type="author")
        self.G.add_edge(author, post_id, type="writes")

        for e in emails:
            self.G.add_node(e, type="email")
            self.G.add_edge(post_id, e, type="contains_email")

        for link in links:
            self.G.add_node(link, type="link")
            self.G.add_edge(post_id, link, type="references")

    def export_graph(self):
        return nx.node_link_data(self.G)

