# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
CORTEX-SCRAPER v1.0 — Sovereign Bounty Reconnaissance Engine
─────────────────────────────────────────────────────────────
Replaces Firecrawl for the 5 critical bounty platforms.
Zero API keys. Zero cost. 100% local. 100% sovereign.

Usage:
    python3 cortex_scraper.py <url>                    # Scrape any URL → Markdown
    python3 cortex_scraper.py --platform c4 <slug>     # Code4rena bounty
    python3 cortex_scraper.py --platform immunefi <id> # Immunefi program
    python3 cortex_scraper.py --platform etherscan <addr> --chain base  # Contract ABI
    python3 cortex_scraper.py <url> -o output.md       # Save to file

Governing Laws:
    Ω₅ (Signal): Zero thermal noise — only actionable content.
    Ω₉ (Truth): C5-REAL output only. No simulated data.
    Ω₂ (Exergy): Minimal resource burn. Headless by default.
"""

import argparse
import asyncio
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
import markdownify
from readability import Document


# ─── Configuration ────────────────────────────────────────────────────────────

PLATFORMS = {
    "c4": "https://code4rena.com/bounties/{slug}",
    "c4-audit": "https://code4rena.com/audits/{slug}",
    "immunefi": "https://immunefi.com/bug-bounty/{slug}/information/",
    "etherscan": "https://api.etherscan.io/api?module=contract&action=getabi&address={slug}",
    "basescan": "https://api.basescan.org/api?module=contract&action=getabi&address={slug}",
    "github": "https://github.com/{slug}",
}

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

# Elements to strip from the DOM before extraction
NOISE_SELECTORS = [
    "nav", "footer", "header",
    "[class*='cookie']", "[class*='Cookie']",
    "[class*='banner']", "[class*='popup']", "[class*='modal']",
    "[class*='sidebar']", "[class*='Sidebar']",
    "[class*='newsletter']", "[class*='Newsletter']",
    "[class*='toast']", "[class*='Toast']",
    "[id*='cookie']", "[id*='banner']",
    "script", "style", "noscript", "iframe",
    "[aria-hidden='true']",
]


# ─── Core Extraction Engine ──────────────────────────────────────────────────

async def scrape_with_playwright(url: str, wait_ms: int = 3000) -> str:
    """
    Render a JavaScript-heavy page using Playwright and return clean HTML.
    This is the heavy path — only used when static fetch fails or for SPAs.
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-gpu"])
        context = await browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1440, "height": 900},
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(wait_ms)

            # Strip noise from the DOM before extraction
            for selector in NOISE_SELECTORS:
                await page.evaluate(
                    f"""() => {{
                        document.querySelectorAll('{selector}')
                            .forEach(el => el.remove());
                    }}"""
                )

            html = await page.content()
        except Exception as e:
            print(f"⚠ Playwright error: {e}", file=sys.stderr)
            html = ""
        finally:
            await browser.close()

    return html


async def scrape_static(url: str) -> str:
    """
    Fast, lightweight HTTP fetch. Used for static pages and APIs.
    Falls back to Playwright if the response looks like an empty SPA shell.
    """
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=20.0,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


def html_to_markdown(html: str, url: str = "") -> str:
    """
    Convert raw HTML to clean Markdown using readability + markdownify.
    This is the semantic compression step (Ω₅).
    """
    if not html or len(html) < 100:
        return ""

    # Phase 1: Readability extracts the "main content" from the page
    doc = Document(html, url=url)
    clean_html = doc.summary()
    title = doc.title()

    # Phase 2: Convert the clean HTML to Markdown
    md = markdownify.markdownify(
        clean_html,
        heading_style="ATX",
        strip=["img"],  # Strip images — we want text only
        convert=["table", "tr", "td", "th", "a", "p", "h1", "h2", "h3", "h4", "h5", "h6",
                 "ul", "ol", "li", "pre", "code", "blockquote", "strong", "em"],
    )

    # Phase 3: Clean up excessive whitespace
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = md.strip()

    # Prepend title if available
    if title and not md.startswith(f"# {title}"):
        md = f"# {title}\n\n{md}"

    return md


def is_spa_shell(html: str) -> bool:
    """
    Detect if the HTML is just an empty SPA shell (React/Next.js/Vue)
    that needs JavaScript rendering.
    """
    # If the body has very little text content, it's likely an SPA shell
    body_match = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL)
    if not body_match:
        return True

    body = body_match.group(1)
    # Remove all tags and count remaining text
    text_only = re.sub(r"<[^>]+>", "", body).strip()
    # If body text is tiny but HTML is large, it's an SPA
    return len(text_only) < 200 and len(html) > 5000


# ─── Platform-Specific Parsers ───────────────────────────────────────────────

async def parse_etherscan(address: str, chain: str = "ethereum") -> str:
    """Extract contract ABI from Etherscan-family block explorers."""
    base_urls = {
        "ethereum": "https://api.etherscan.io",
        "base": "https://api.basescan.org",
        "optimism": "https://api-optimistic.etherscan.io",
        "arbitrum": "https://api.arbiscan.io",
        "polygon": "https://api.polygonscan.com",
    }

    base = base_urls.get(chain, base_urls["ethereum"])
    url = f"{base}/api?module=contract&action=getabi&address={address}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url)
        data = resp.json()

    if data.get("status") != "1":
        return f"# Error: Contract not verified\n\nAddress: `{address}`\nChain: `{chain}`\nMessage: {data.get('message', 'Unknown')}"

    abi = json.loads(data["result"])

    # Extract function signatures
    lines = [f"# Contract ABI: `{address}`", f"**Chain:** {chain}\n"]

    functions = [f for f in abi if f.get("type") == "function"]
    events = [f for f in abi if f.get("type") == "event"]

    if functions:
        lines.append("## Functions\n")
        lines.append("| Name | Inputs | Outputs | Mutability |")
        lines.append("|------|--------|---------|------------|")
        for fn in sorted(functions, key=lambda x: x.get("name", "")):
            name = fn.get("name", "?")
            inputs = ", ".join(f"{i.get('type')} {i.get('name','')}" for i in fn.get("inputs", []))
            outputs = ", ".join(f"{o.get('type')}" for o in fn.get("outputs", []))
            mutability = fn.get("stateMutability", "?")
            lines.append(f"| `{name}` | `{inputs}` | `{outputs}` | {mutability} |")

    if events:
        lines.append("\n## Events\n")
        for ev in sorted(events, key=lambda x: x.get("name", "")):
            name = ev.get("name", "?")
            params = ", ".join(
                f"{'indexed ' if p.get('indexed') else ''}{p.get('type')} {p.get('name','')}"
                for p in ev.get("inputs", [])
            )
            lines.append(f"- `{name}({params})`")

    return "\n".join(lines)


async def parse_github_repo(slug: str) -> str:
    """Extract README and file tree from a GitHub repo."""
    owner, repo = slug.split("/", 1) if "/" in slug else (slug, "")

    # Try to get the README via API (no rendering needed)
    async with httpx.AsyncClient(timeout=15.0, headers={"User-Agent": USER_AGENT}) as client:
        # File tree
        tree_url = f"https://api.github.com/repos/{slug}/git/trees/main?recursive=1"
        tree_resp = await client.get(tree_url)

        # README
        readme_url = f"https://api.github.com/repos/{slug}/readme"
        readme_resp = await client.get(readme_url, headers={"Accept": "application/vnd.github.raw"})

    lines = [f"# GitHub: {slug}\n"]

    # File tree
    if tree_resp.status_code == 200:
        tree = tree_resp.json()
        sol_files = [t["path"] for t in tree.get("tree", [])
                     if t["path"].endswith((".sol", ".rs", ".vy", ".cairo"))
                     and "test" not in t["path"].lower()
                     and "mock" not in t["path"].lower()
                     and "node_modules" not in t["path"]]

        if sol_files:
            lines.append("## Contracts in Scope\n")
            for f in sorted(sol_files):
                lines.append(f"- `{f}`")
            lines.append("")

    # README
    if readme_resp.status_code == 200:
        lines.append("## README\n")
        lines.append(readme_resp.text[:5000])  # Cap at 5k chars

    return "\n".join(lines)


# ─── Main Orchestrator ───────────────────────────────────────────────────────

async def scrape(
    url: str,
    platform: Optional[str] = None,
    chain: str = "ethereum",
    force_js: bool = False,
) -> str:
    """
    Main scraping entrypoint.
    Returns clean Markdown from any URL or platform shortcut.
    """
    # Handle platform shortcuts
    if platform == "etherscan" or platform == "basescan":
        return await parse_etherscan(url, chain=chain if platform == "etherscan" else "base")

    if platform == "github":
        return await parse_github_repo(url)

    if platform in PLATFORMS:
        url = PLATFORMS[platform].format(slug=url)

    # Phase 1: Try static fetch first (fast, cheap)
    if not force_js:
        try:
            html = await scrape_static(url)
            if not is_spa_shell(html):
                md = html_to_markdown(html, url)
                if len(md) > 100:
                    return _add_metadata(md, url, method="static")
        except Exception:
            pass

    # Phase 2: Fall back to Playwright (JS rendering)
    html = await scrape_with_playwright(url)
    if not html:
        return f"# Error\n\nFailed to scrape: `{url}`"

    md = html_to_markdown(html, url)
    return _add_metadata(md, url, method="playwright")


def _add_metadata(md: str, url: str, method: str) -> str:
    """Append extraction metadata footer."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    footer = f"\n\n---\n*Extracted by CORTEX-SCRAPER v1.0 | {method} | {ts} | Source: {url}*"
    return md + footer


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="CORTEX-SCRAPER — Sovereign Bounty Reconnaissance Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://code4rena.com/bounties/intuition
  %(prog)s --platform c4 intuition
  %(prog)s --platform immunefi exactly-protocol
  %(prog)s --platform etherscan 0x1234... --chain base
  %(prog)s --platform github code-423n4/intuition-bug-bounty
  %(prog)s https://docs.some-protocol.com -o scope.md
        """,
    )
    parser.add_argument("target", help="URL or platform-specific identifier")
    parser.add_argument(
        "--platform", "-p",
        choices=["c4", "c4-audit", "immunefi", "etherscan", "basescan", "github"],
        help="Use a platform shortcut instead of a full URL",
    )
    parser.add_argument("--chain", default="ethereum", help="Blockchain for explorer APIs (default: ethereum)")
    parser.add_argument("--output", "-o", help="Save output to file instead of stdout")
    parser.add_argument("--js", action="store_true", help="Force JavaScript rendering via Playwright")

    args = parser.parse_args()

    md = asyncio.run(scrape(
        url=args.target,
        platform=args.platform,
        chain=args.chain,
        force_js=args.js,
    ))

    if args.output:
        Path(args.output).write_text(md, encoding="utf-8")
        print(f"✅ Saved to {args.output} ({len(md)} chars)", file=sys.stderr)
    else:
        print(md)


if __name__ == "__main__":
    main()
