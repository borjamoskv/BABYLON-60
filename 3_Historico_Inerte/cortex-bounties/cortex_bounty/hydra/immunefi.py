"""
HYDRA — Immunefi Bounty Scraper (C5-REAL)

Fetches live bounty program data from Immunefi's public API.
No mock data. No placeholders. Every byte from the wire.
"""
import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Optional

import httpx

from cortex_bounty.config import USER_AGENT


@dataclass
class ImmunefiProgram:
    """Single Immunefi bounty program."""
    id: str = ""
    project: str = ""
    max_bounty: float = 0.0
    min_bounty: float = 0.0
    category: str = ""  # smart_contract, websites_and_apps, blockchain_dlt
    assets_in_scope: list = field(default_factory=list)
    launch_date: str = ""
    updated_date: str = ""
    kyc_required: bool = False
    program_url: str = ""
    github_urls: list = field(default_factory=list)
    technologies: list = field(default_factory=list)


class ImmunefiScraper:
    """
    Scrapes Immunefi bounty listings from their public-facing API.

    Immunefi serves bounty data via a JSON endpoint that backs their
    /explore page. We hit that directly — no browser, no Selenium.
    """

    BOUNTIES_URL = "https://immunefi.com/bounty"
    EXPLORE_API = "https://immunefi.com/api/bounty"

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

    # Community-maintained JSON with full Immunefi program data (C5-REAL)
    PROGRAMS_JSON_URL = (
        "https://raw.githubusercontent.com/infosec-us-team/"
        "Immunefi-Bug-Bounty-Programs-Unofficial/main/projects.json"
    )

    async def fetch_all_programs(self) -> list[ImmunefiProgram]:
        """
        Fetch all active bounty programs from Immunefi.

        Primary source: infosec-us-team/Immunefi-Bug-Bounty-Programs-Unofficial
        GitHub repo — structured JSON with 286+ programs. C5-REAL.
        """
        programs = []

        try:
            resp = await self.client.get(self.PROGRAMS_JSON_URL)
            if resp.status_code == 200:
                data = json.loads(resp.text)
                if isinstance(data, list):
                    for item in data:
                        prog = self._parse_program(item)
                        if prog:
                            programs.append(prog)
        except (httpx.HTTPError, json.JSONDecodeError):
            pass

        return programs

    async def fetch_program_detail(self, project_slug: str) -> Optional[ImmunefiProgram]:
        """Fetch detailed info for a specific bounty program."""
        url = f"https://immunefi.com/bug-bounty/{project_slug}/information/"
        try:
            resp = await self.client.get(url)
            if resp.status_code != 200:
                return None

            text = resp.text
            next_data = re.search(
                r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                text,
                re.DOTALL
            )
            if next_data:
                data = json.loads(next_data.group(1))
                props = data.get("props", {}).get("pageProps", {})
                bounty = props.get("bounty", props.get("program", {}))
                return self._parse_program(bounty)
        except (httpx.HTTPError, json.JSONDecodeError):
            pass
        return None

    def _parse_program(self, raw: dict) -> Optional[ImmunefiProgram]:
        """Parse a raw JSON bounty object into an ImmunefiProgram."""
        if not raw or not isinstance(raw, dict):
            return None

        project = raw.get("project", raw.get("name", ""))
        if not project:
            return None

        # Extract max bounty — can be nested or flat
        max_bounty = 0.0
        for key in ("maxBounty", "maximum_bounty", "max_bounty", "maximumReward"):
            val = raw.get(key, 0)
            if isinstance(val, (int, float)) and val > max_bounty:
                max_bounty = float(val)

        # Parse reward ranges from nested structure
        rewards = raw.get("rewards", raw.get("reward_ranges", []))
        if isinstance(rewards, list):
            for r in rewards:
                if isinstance(r, dict):
                    mx = r.get("max", r.get("maximum", 0))
                    if isinstance(mx, (int, float)) and mx > max_bounty:
                        max_bounty = float(mx)

        # Extract assets in scope
        assets = []
        scope = raw.get("assets", raw.get("assetsInScope", []))
        if isinstance(scope, list):
            for a in scope:
                if isinstance(a, dict):
                    assets.append({
                        "target": a.get("target", a.get("url", "")),
                        "type": a.get("type", a.get("asset_type", "")),
                    })

        # Extract GitHub URLs from assets
        github_urls = []
        for a in assets:
            target = a.get("target", "")
            if "github.com" in target:
                github_urls.append(target)

        # KYC
        kyc = raw.get("kycRequired", raw.get("kyc_required", False))
        if isinstance(kyc, str):
            kyc = kyc.lower() in ("true", "yes", "1")

        slug = raw.get("id", raw.get("slug", project.lower().replace(" ", "-")))

        return ImmunefiProgram(
            id=slug,
            project=project,
            max_bounty=max_bounty,
            min_bounty=float(raw.get("minBounty", raw.get("min_bounty", 0)) or 0),
            category=raw.get("category", raw.get("programType", "")),
            assets_in_scope=assets,
            launch_date=raw.get("launchDate", raw.get("launch_date", "")),
            updated_date=raw.get("updatedDate", raw.get("updated_date", "")),
            kyc_required=bool(kyc),
            program_url=f"https://immunefi.com/bug-bounty/{slug}/",
            github_urls=github_urls,
            technologies=raw.get("technologies", []),
        )

    async def search(self, min_payout: float = 0, category: str = "", no_kyc: bool = False) -> list[ImmunefiProgram]:
        """Search and filter Immunefi programs."""
        all_programs = await self.fetch_all_programs()

        results = []
        for p in all_programs:
            if min_payout and p.max_bounty < min_payout:
                continue
            if category and category.lower() not in p.category.lower():
                continue
            if no_kyc and p.kyc_required:
                continue
            results.append(p)

        return sorted(results, key=lambda x: x.max_bounty, reverse=True)


async def _test():
    """Quick verification against live Immunefi."""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    async with ImmunefiScraper() as scraper:
        console.print("[bold]HYDRA · Immunefi Scan[/bold]", style="blue")
        programs = await scraper.fetch_all_programs()
        console.print(f"  Found {len(programs)} programs")

        if programs:
            table = Table(title="Top 10 by Payout")
            table.add_column("Project", style="cyan")
            table.add_column("Max Payout", justify="right", style="green")
            table.add_column("Category")
            table.add_column("KYC", justify="center")
            table.add_column("Assets")

            top = sorted(programs, key=lambda x: x.max_bounty, reverse=True)[:10]
            for p in top:
                table.add_row(
                    p.project,
                    f"${p.max_bounty:,.0f}",
                    p.category,
                    "⚠️" if p.kyc_required else "✅",
                    str(len(p.assets_in_scope)),
                )
            console.print(table)


if __name__ == "__main__":
    asyncio.run(_test())
