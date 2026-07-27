"""
HYDRA — Sherlock Audit Contest Scraper (C5-REAL)

Fetches live audit contest data from Sherlock's public API/page.
"""
import asyncio
import json
import re
from dataclasses import dataclass
from typing import Optional

import httpx

from cortex_bounty.config import USER_AGENT


@dataclass
class SherlockContest:
    """Single Sherlock audit contest."""
    id: str = ""
    title: str = ""
    protocol: str = ""
    prize_pool: float = 0.0
    start_date: str = ""
    end_date: str = ""
    status: str = ""  # upcoming, active, judging, finished
    repo_url: str = ""
    nsloc: int = 0  # lines of code
    lead_auditor: str = ""
    contest_url: str = ""


class SherlockScraper:
    """
    Fetches audit contest data from Sherlock (app.sherlock.xyz).

    Sherlock exposes contest data through their web app which we
    parse from the rendered page or API endpoints.
    """

    BASE_URL = "https://app.sherlock.xyz"
    AUDITS_URL = "https://app.sherlock.xyz/audits"
    API_URL = "https://mainnet-contest.sherlock.xyz"

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

    async def fetch_contests(self) -> list[SherlockContest]:
        """Fetch all contests from Sherlock."""
        contests = []

        # Try the contest API first
        api_endpoints = [
            f"{self.API_URL}/contests",
            f"{self.BASE_URL}/api/contests",
        ]

        for endpoint in api_endpoints:
            try:
                resp = await self.client.get(endpoint)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list):
                        for item in data:
                            c = self._parse_contest(item)
                            if c:
                                contests.append(c)
                    elif isinstance(data, dict):
                        items = data.get("contests", data.get("data", []))
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
            resp = await self.client.get(self.AUDITS_URL)
            if resp.status_code == 200:
                text = resp.text

                # Extract Next.js data
                next_data = re.search(
                    r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                    text,
                    re.DOTALL
                )
                if next_data:
                    data = json.loads(next_data.group(1))
                    props = data.get("props", {}).get("pageProps", {})
                    for key in ("contests", "audits", "data"):
                        items = props.get(key, [])
                        if isinstance(items, list):
                            for item in items:
                                c = self._parse_contest(item)
                                if c:
                                    contests.append(c)
                            if contests:
                                break
        except (httpx.HTTPError, json.JSONDecodeError):
            pass

        return sorted(contests, key=lambda x: x.prize_pool, reverse=True)

    def _parse_contest(self, raw: dict) -> Optional[SherlockContest]:
        """Parse raw contest JSON into SherlockContest."""
        if not raw or not isinstance(raw, dict):
            return None

        title = raw.get("title", raw.get("name", ""))
        if not title:
            return None

        # Extract prize pool
        prize = 0.0
        for key in ("prizePool", "prize_pool", "totalPrize", "total_prize", "rewards"):
            val = raw.get(key, 0)
            if isinstance(val, str):
                val = float(re.sub(r'[^\d.]', '', val) or 0)
            if isinstance(val, (int, float)) and val > prize:
                prize = float(val)

        # Status
        status = raw.get("status", raw.get("state", "unknown")).lower()

        # Repo
        repo = raw.get("repo", raw.get("repoUrl", raw.get("repo_url", "")))
        if not repo:
            # Try to find GitHub link in description
            desc = raw.get("description", "")
            gh_match = re.search(r'https?://github\.com/[^\s"\'<>]+', desc)
            if gh_match:
                repo = gh_match.group(0)

        contest_id = str(raw.get("id", raw.get("contestId", title.lower().replace(" ", "-"))))

        return SherlockContest(
            id=contest_id,
            title=title,
            protocol=raw.get("protocol", raw.get("project", title)),
            prize_pool=prize,
            start_date=raw.get("startDate", raw.get("start_date", raw.get("starts", ""))),
            end_date=raw.get("endDate", raw.get("end_date", raw.get("ends", ""))),
            status=status,
            repo_url=repo,
            nsloc=int(raw.get("nsloc", raw.get("linesOfCode", 0)) or 0),
            lead_auditor=raw.get("leadAuditor", raw.get("lead_auditor", "")),
            contest_url=f"{self.AUDITS_URL}/contests/{contest_id}",
        )

    async def search(self, status: str = "", min_prize: float = 0) -> list[SherlockContest]:
        """Search contests with filters."""
        all_contests = await self.fetch_contests()
        results = []
        for c in all_contests:
            if status and status.lower() != c.status:
                continue
            if min_prize and c.prize_pool < min_prize:
                continue
            results.append(c)
        return results


async def _test():
    """Quick test against live Sherlock."""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    async with SherlockScraper() as scraper:
        console.print("[bold]HYDRA · Sherlock Scan[/bold]", style="blue")
        contests = await scraper.fetch_contests()
        console.print(f"  Found {len(contests)} contests")

        if contests:
            table = Table(title="Sherlock Contests")
            table.add_column("Title", style="cyan")
            table.add_column("Prize Pool", justify="right", style="green")
            table.add_column("Status")
            table.add_column("NSLOC", justify="right")
            table.add_column("Repo")

            for c in contests[:10]:
                table.add_row(
                    c.title[:40],
                    f"${c.prize_pool:,.0f}" if c.prize_pool else "N/A",
                    c.status,
                    str(c.nsloc) if c.nsloc else "?",
                    c.repo_url[:50] if c.repo_url else "—",
                )
            console.print(table)


if __name__ == "__main__":
    asyncio.run(_test())
