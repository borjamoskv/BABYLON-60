# C5_IGNORE_NESTING
# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
Inspect Web Target - Automated Stage 1-5 Forensics for Web Application Reverse Engineering
"""

import sys
import os
import re
import json
import urllib.request
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

KNOWN_LIBRARIES = [
    "gsap", "three", "stimulus", "hotwire", "turbo", "alpine", "react", "vue", "svelte",
    "next", "nuxt", "swiper", "lenis", "locomotive-scroll", "lottie", "choices",
    "amplitude", "mixpanel", "framer-motion", "tailwindcss", "bootstrap", "recaptcha"
]

def inspect_url(url: str, output_dir: str = "scratch"):
    os.makedirs(output_dir, exist_ok=True)
    print(f"[*] Probing Target: {url}")

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req) as resp:
            headers = dict(resp.info())
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[!] Error fetching URL: {e}")
        return

    # Save HTML
    domain = re.sub(r'https?://', '', url).strip('/').replace('/', '_')
    html_path = os.path.join(output_dir, f"{domain}_target.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[+] Saved HTML to {html_path} ({len(html)} bytes)")

    soup = BeautifulSoup(html, "html.parser")

    # Stage 1: Headers
    print("\n--- STAGE 1: HEADERS & INFRASTRUCTURE ---")
    for k in ["Server", "Cache-Control", "Vary", "Content-Type", "Strict-Transport-Security", "X-Powered-By"]:
        if k in headers:
            print(f"  {k}: {headers[k]}")

    # Stage 2: Inlined CSS & Clamps
    styles = soup.find_all("style")
    print(f"\n--- STAGE 2: CSS & FLUID MATH ---")
    print(f"  Inline <style> blocks count: {len(styles)}")
    total_css = "\n".join([s.string or "" for s in styles])
    css_vars = set(re.findall(r'--[a-zA-Z0-9_\-]+', total_css))
    print(f"  CSS Variables found ({len(css_vars)}): {sorted(list(css_vars))[:15]}")
    clamps = set(re.findall(r'clamp\([^)]+\)', total_css))
    print(f"  Fluid clamp() functions ({len(clamps)}): {sorted(list(clamps))[:10]}")

    # Stage 3: Scripts & Bundles
    print(f"\n--- STAGE 3: SCRIPTS & JS LIBRARIES ---")
    script_srcs = []
    for s in soup.find_all("script"):
        src = s.get("src")
        if src:
            script_srcs.append(src)
    print(f"  Script tags count: {len(script_srcs)}")
    for src in script_srcs[:15]:
        print(f"   -> {src}")

    # Stage 4: DOM Controllers & Actions
    print(f"\n--- STAGE 4: DOM MICRO-CONTROLLERS ---")
    controllers = set()
    actions = set()
    for el in soup.find_all(True):
        for k, v in el.attrs.items():
            if k == "data-controller":
                controllers.add(v)
            elif k == "data-action":
                actions.add(v)
    print(f"  data-controller attributes: {sorted(list(controllers))}")
    print(f"  data-action attributes (sample): {sorted(list(actions))[:15]}")

    # Stage 5: Endpoints & Framework Signals
    print(f"\n--- STAGE 5: ENDPOINTS & BACKEND SIGNALS ---")
    urls = set(re.findall(r'/[a-zA-Z0-9_\-\?&=%/\.]+', html))
    filtered_endpoints = [u for u in urls if any(kw in u for kw in ["api", "search", "fragment", "vote", "user", "admin", "graphql", "json"])]
    print(f"  Endpoints discovered in HTML ({len(filtered_endpoints)}): {sorted(filtered_endpoints)[:20]}")

    print("\n[*] Inspection Complete. Use these findings to execute Stages 6 & 7.")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "https://www.awwwards.com"
    inspect_url(target)
