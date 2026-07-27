"""
HYDRA — Code4rena Contest Scraper (C5-REAL)

Fetches live audit contest data from Code4rena's public pages.
"""
import asyncio
import json
import re
from dataclasses import dataclass
from typing import Optional

import httpx

from cortex_bounty.config import USER_AGENT


@dataclass
class C4Contest:
    """Single Code4rena audit contest."""
    id: str = ""
    title: str = ""
    protocol: str = ""
    prize_pool: float = 0.0
    start_date: str = ""
    end_date: str = ""
    status: str = ""  # upcoming, active, judging, completed
    repo_url: str = ""
    nsloc: int = 0
    sponsor: str = ""
    kyc_required: bool = False
    contest_url: str = ""


class Code4renaScraper:
    """
    Fetches contest data from Code4rena (code4rena.com).
    """

    BASE_URL = "https://code4rena.com"
    CONTESTS_URL = "https://code4rena.com/audits"

    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()

    async def fetch_contests(self) -> list[C4Contest]:
        """Fetch all contests from Code4rena."""
        contests = []

        # Try API endpoints
        api_urls = [
            f"{self.BASE_URL}/api/contests",
            f"{self.BASE_URL}/api/v1/contests",
        ]

        for url in api_urls:
            try:
                resp = await self.client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data if isinstance(data, list) else data.get("contests", data.get("data", []))
                    for item in items:
                        c = self._parse_contest(item)
                        if c:
                            contests.append(c)
                    if contests:
                        return sorted(contests, key=lambda x: x.prize_pool, reverse=True)
            except (httpx.HTTPError, json.JSONDecodeError):
                continue

        # Fallback: scrape the audits page
        try:
            resp = await self.client.get(self.CONTESTS_URL)
            if resp.status_code == 200:
                text = resp.text

                # Extract Next.js or embedded JSON data
                next_data = re.search(
                    r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                    text,
                    re.DOTALL
                )
                if next_data:
                    data = json.loads(next_data.group(1))
                    props = data.get("props", {}).get("pageProps", {})
                    for key in ("contests", "audits"):
                        items = props.get(key, [])
                        if isinstance(items, list):
                            for item in items:
                                c = self._parse_contest(item)
                                if c:
                                    contests.append(c)

                # Also try to find contest data in script tags
                script_data = re.findall(
                    r'<script[^>]*>(.*?)</script>',
                    text,
                    re.DOTALL
                )
                for script in script_data:
                    if "contest" in script.lower() and "prize" in script.lower():
                        json_match = re.search(r'\[.*?\]', script, re.DOTALL)
                        if json_match:
                            try:
                                items = json.loads(json_match.group(0))
                                for item in items:
                                    if isinstance(item, dict):
                                        c = self._parse_contest(item)
                                        if c:
                                            contests.append(c)
                            except json.JSONDecodeError:
                                pass

        except (httpx.HTTPError, json.JSONDecodeError):
            pass

        return sorted(contests, key=lambda x: x.prize_pool, reverse=True)

    def _parse_contest(self, raw: dict) -> Optional[C4Contest]:
        """Parse raw contest JSON into C4Contest."""
        if not raw or not isinstance(raw, dict):
            return None

        title = raw.get("title", raw.get("name", raw.get("contestName", "")))
        if not title:
            return None

        # Prize pool
        prize = 0.0
        for key in ("amount", "prize", "prizePool", "prize_pool", "totalPrize", "pot"):
            val = raw.get(key, 0)
            if isinstance(val, str):
                val = float(re.sub(r'[^\d.]', '', val) or 0)
            if isinstance(val, (int, float)) and val > prize:
                prize = float(val)

        status = raw.get("status", raw.get("state", "unknown")).lower()

        # Repo URL
        repo = raw.get("repo", raw.get("repoUrl", raw.get("repo_url", "")))
        if not repo:
            for key in ("description", "details"):
                desc = raw.get(key, "")
                if desc:
                    gh = re.search(r'https?://github\.com/[^\s"\'<>]+', desc)
                    if gh:
                        repo = gh.group(0)
                        break

        contest_id = str(raw.get("id", raw.get("contestId", raw.get("slug", ""))))
        if not contest_id:
            contest_id = re.sub(r'[^a-z0-9-]', '-', title.lower())

        return C4Contest(
            id=contest_id,
            title=title,
            protocol=raw.get("sponsor", raw.get("protocol", title)),
            prize_pool=prize,
            start_date=raw.get("startDate", raw.get("start_date", raw.get("start", ""))),
            end_date=raw.get("endDate", raw.get("end_date", raw.get("end", ""))),
            status=status,
            repo_url=repo,
            nsloc=int(raw.get("nsloc", raw.get("linesOfCode", 0)) or 0),
            sponsor=raw.get("sponsor", raw.get("sponsorName", "")),
            kyc_required=bool(raw.get("kycRequired", raw.get("kyc_required", False))),
            contest_url=f"{self.BASE_URL}/audits/{contest_id}",
        )

    async def search(self, status: str = "", min_prize: float = 0, no_kyc: bool = False) -> list[C4Contest]:
        """Filter contests."""
        all_contests = await self.fetch_contests()
        results = []
        for c in all_contests:
            if status and status.lower() != c.status:
                continue
            if min_prize and c.prize_pool < min_prize:
                continue
            if no_kyc and c.kyc_required:
                continue
            results.append(c)
        return results


async def _test():
    from rich.console import Console
    from rich.table import Table

    console = Console()

    async with Code4renaScraper() as scraper:
        console.print("[bold]HYDRA · Code4rena Scan[/bold]", style="blue")
        contests = await scraper.fetch_contests()
        console.print(f"  Found {len(contests)} contests")

        if contests:
            table = Table(title="Code4rena Contests")
            table.add_column("Title", style="cyan")
            table.add_column("Prize", justify="right", style="green")
            table.add_column("Status")
            table.add_column("KYC", justify="center")

            for c in contests[:10]:
                table.add_row(
                    c.title[:40],
                    f"${c.prize_pool:,.0f}" if c.prize_pool else "N/A",
                    c.status,
                    "⚠️" if c.kyc_required else "✅",
                )
            console.print(table)


if __name__ == "__main__":
    asyncio.run(_test())
