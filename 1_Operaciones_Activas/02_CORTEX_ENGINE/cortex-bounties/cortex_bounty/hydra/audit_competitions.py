"""
HYDRA — Immunefi Audit Competition Scraper (C5-REAL)

Dedicated scraper for Immunefi's audit competition surface.
Audit competitions are distinct from bug bounty programs:
  - Time-bound (fixed start/end)
  - Fixed reward pools (not per-bug payouts)
  - Tiered rewards by severity found
  - Often require KYC + Runnable PoC
  - Duplicates may be valid (unlike standard bounties)

Data source: https://immunefi.com/audit-competition/
"""
import asyncio
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import httpx

from cortex_bounty.config import USER_AGENT

log = logging.getLogger("HYDRA.AUDIT_COMP")


class CompetitionStatus(str, Enum):
    """Competition lifecycle states."""
    UPCOMING = "upcoming"
    LIVE = "live"
    EVALUATING = "evaluating"
    FINISHED = "finished"
    UNKNOWN = "unknown"


class CompetitionType(str, Enum):
    """Competition format types."""
    AUDIT_COMP = "audit_comp"
    ATTACKATHON = "attackathon"
    BUG_BOUNTY_COMP = "bug_bounty_comp"
    IOP = "iop"  # Invite-Only Program
    MITIGATION = "mitigation"


@dataclass
class AuditCompetition:
    """Single Immunefi audit competition with full metadata."""
    slug: str = ""
    name: str = ""
    project: str = ""
    comp_type: CompetitionType = CompetitionType.AUDIT_COMP
    status: CompetitionStatus = CompetitionStatus.UNKNOWN
    reward_pool: float = 0.0
    reward_currency: str = "USD"
    time_remaining: str = ""
    end_date: str = ""
    url: str = ""
    triaged_by_immunefi: bool = False
    kyc_required: bool = False
    poc_required: bool = False

    # Deep-scraped fields (from detail page)
    description: str = ""
    reward_tiers: list = field(default_factory=list)
    assets_in_scope: list = field(default_factory=list)
    nsloc: int = 0
    audit_links: list = field(default_factory=list)
    github_urls: list = field(default_factory=list)
    chains: list = field(default_factory=list)
    payment_method: str = ""
    duplicates_valid: bool = False
    fixes_mid_contest: bool = False
    discord_channel: str = ""

    # Scoring
    exergy_score: float = 0.0  # Composite score for prioritization


class AuditCompetitionScraper:
    """
    Scrapes Immunefi audit competition listings and detail pages.

    Two-phase approach:
    1. List scan — parse /audit-competition/ for all competitions
    2. Deep scan — scrape individual /information/ pages for scope details
    """

    BASE_URL = "https://immunefi.com/audit-competition/"
    COMP_DETAIL_BASE = "https://immunefi.com/audit-competition/"

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

    async def fetch_competitions(self) -> list[AuditCompetition]:
        """
        Fetch all audit competitions from the listing page.
        Returns parsed competitions sorted by reward pool (descending).
        """
        competitions: list[AuditCompetition] = []

        try:
            resp = await self.client.get(self.BASE_URL)
            if resp.status_code != 200:
                log.warning(f"Failed to fetch competitions: HTTP {resp.status_code}")
                return []

            text = resp.text
            competitions = self._parse_listing_page(text)
            log.info(f"Parsed {len(competitions)} competitions from listing")

        except httpx.HTTPError as e:
            log.error(f"HTTP error fetching competitions: {e}")

        return sorted(competitions, key=lambda c: c.reward_pool, reverse=True)

    async def fetch_active(self) -> list[AuditCompetition]:
        """Fetch only live/evaluating/upcoming competitions."""
        all_comps = await self.fetch_competitions()
        return [
            c for c in all_comps
            if c.status in (
                CompetitionStatus.LIVE,
                CompetitionStatus.EVALUATING,
                CompetitionStatus.UPCOMING,
            )
        ]

    async def deep_scan(self, competition: AuditCompetition) -> AuditCompetition:
        """
        Deep-scrape a competition's detail page for full scope info.
        Enriches the competition object with assets, reward tiers, etc.
        """
        info_url = f"{self.COMP_DETAIL_BASE}{competition.slug}/information/"
        scope_url = f"{self.COMP_DETAIL_BASE}{competition.slug}/scope/"

        try:
            # Fetch info page
            resp = await self.client.get(info_url)
            if resp.status_code == 200:
                self._parse_detail_page(competition, resp.text)

            # Fetch scope page
            resp = await self.client.get(scope_url)
            if resp.status_code == 200:
                self._parse_scope_page(competition, resp.text)

        except httpx.HTTPError as e:
            log.warning(f"Deep scan failed for {competition.slug}: {e}")

        return competition

    async def deep_scan_all_active(self) -> list[AuditCompetition]:
        """Deep-scan all active competitions in parallel."""
        active = await self.fetch_active()
        if not active:
            return []

        tasks = [self.deep_scan(c) for c in active]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        enriched = []
        for r in results:
            if isinstance(r, AuditCompetition):
                enriched.append(r)

        return enriched

    def _parse_listing_page(
        self, html: str
    ) -> list[AuditCompetition]:
        """
        Parse the audit competition listing page.

        Immunefi renders competition data as continuous text
        blocks near slug URLs. Pattern (from markdown render):
          [Audit Comp | Firedancer V1Triaged by Immunefi](url)
          $1,000,000Reward Pool Live8h: 24m remaining
        """
        competitions: list[AuditCompetition] = []
        slugs_seen: set[str] = set()

        # Find all competition slug links
        slug_pat = re.compile(
            r'/audit-competition/'
            r'([a-zA-Z0-9_-]+)/information/'
        )

        for match in slug_pat.finditer(html):
            slug = match.group(1)
            if slug in slugs_seen:
                continue
            slugs_seen.add(slug)

            comp = AuditCompetition(slug=slug)
            comp.url = (
                "https://immunefi.com/"
                f"audit-competition/{slug}/information/"
            )
            comp.comp_type = self._classify_type(slug)

            # Wide context window (1500 chars each way)
            s = max(0, match.start() - 1500)
            e = min(len(html), match.end() + 1500)
            ctx = html[s:e]

            comp.name = self._extract_name(ctx, slug)
            comp.project = self._extract_project(comp.name)
            comp.reward_pool = self._extract_reward(ctx)
            comp.status = self._extract_status(ctx)
            comp.time_remaining = self._extract_time(ctx)
            comp.triaged_by_immunefi = (
                "Triaged by Immunefi" in ctx
            )

            competitions.append(comp)

        return competitions

    def _classify_type(self, slug: str) -> CompetitionType:
        """Classify competition type from slug."""
        sl = slug.lower()
        if "attackathon" in sl:
            return CompetitionType.ATTACKATHON
        if "bug-bounty-comp" in sl:
            return CompetitionType.BUG_BOUNTY_COMP
        if sl.startswith("iop") or "iop-" in sl:
            return CompetitionType.IOP
        if "mitigation" in sl:
            return CompetitionType.MITIGATION
        return CompetitionType.AUDIT_COMP

    def _extract_name(
        self, context: str, slug: str
    ) -> str:
        """Extract competition name from context."""
        pats = [
            re.compile(r'\[(Audit Comp[^\]]*)\]'),
            re.compile(r'\[(Attackathon[^\]]*)\]'),
            re.compile(r'\[(IOP[^\]]*)\]'),
            re.compile(r'\[(Mitigation[^\]]*)\]'),
            re.compile(r'\[(Bug Bounty Comp[^\]]*)\]'),
        ]
        for pat in pats:
            m = pat.search(context)
            if m:
                name = m.group(1)
                name = re.sub(
                    r'Triaged by Immunefi\s*$', '', name
                ).strip()
                return name
        return slug.replace("-", " ").title()

    def _extract_project(self, name: str) -> str:
        """Extract project name from competition name."""
        prefixes = (
            "Audit Comp | ",
            "Attackathon | ",
            "IOP | ",
            "Mitigation Audit | ",
            "Bug Bounty Comp | ",
        )
        for prefix in prefixes:
            if name.startswith(prefix):
                return name[len(prefix):]
        return name

    def _extract_reward(self, context: str) -> float:
        """Extract reward pool from context text."""
        # Primary: look for $X,XXX,XXX near "Reward Pool"
        rp = re.search(
            r'\$([0-9]{1,3}(?:,\d{3})*)'
            r'(?:\s*Reward\s*Pool)',
            context
        )
        if rp:
            return float(rp.group(1).replace(",", ""))

        # Secondary: look for "Max Bounty: $X"
        mb = re.search(
            r'Max Bounty:\s*\$([0-9]{1,3}(?:,\d{3})*)',
            context
        )
        if mb:
            return float(mb.group(1).replace(",", ""))

        # Fallback: largest dollar amount
        all_amounts = re.findall(
            r'\$([0-9]{1,3}(?:,\d{3})+)', context
        )
        if all_amounts:
            vals = [
                float(a.replace(",", ""))
                for a in all_amounts
            ]
            return max(vals)
        return 0.0

    def _extract_status(
        self, context: str
    ) -> CompetitionStatus:
        """Determine competition status from context."""
        # Check for specific status indicators
        # Order matters: more specific first
        if re.search(r'\bLive\b.*remaining', context):
            return CompetitionStatus.LIVE
        if re.search(r'\bLive\b', context):
            return CompetitionStatus.LIVE
        if re.search(r'\bEvaluating\b', context):
            return CompetitionStatus.EVALUATING
        if re.search(r'\bFinished\b', context):
            return CompetitionStatus.FINISHED
        if re.search(r'\bEnded\b', context):
            return CompetitionStatus.FINISHED
        if re.search(r'\bUpcoming\b', context):
            return CompetitionStatus.UPCOMING
        return CompetitionStatus.UNKNOWN

    def _extract_time(self, context: str) -> str:
        """Extract time remaining from context."""
        # Match: 26d: 9h, 8h: 24m
        pats = [
            re.compile(r'(\d+d:\s*\d+h)'),
            re.compile(r'(\d+h:\s*\d+m)'),
        ]
        for pat in pats:
            m = pat.search(context)
            if m:
                return m.group(1).strip()
        return ""

    def _parse_detail_page(self, comp: AuditCompetition, html: str):
        """Parse a competition's detail/information page."""
        # Description
        desc_match = re.search(
            r'Program Overview.*?(?:<p>|^)(.+?)(?:</p>|$)',
            html, re.DOTALL | re.MULTILINE
        )
        if desc_match:
            comp.description = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()[:500]

        # KYC required
        if "KYC required" in html or "KYC is required" in html:
            comp.kyc_required = True

        # PoC required
        if "Proof of concept" in html or "Runnable PoC Required" in html:
            comp.poc_required = True

        # Duplicates valid
        if "Duplicate reports" in html and "valid" in html:
            comp.duplicates_valid = True

        # Fixes mid-contest
        if "Fixes may be applied mid-contest" in html:
            comp.fixes_mid_contest = True

        # nSLOC
        nsloc_match = re.search(r'([\d,]+)\s*nSLOC', html)
        if nsloc_match:
            comp.nsloc = int(nsloc_match.group(1).replace(",", ""))

        # Payment method
        for token in ("USDC", "USDT", "ETH", "SOL"):
            if f"payments are done in {token}" in html or f"paid in {token}" in html:
                comp.payment_method = token
                break

        # Discord
        discord_match = re.search(r'(https://discord\.com/invite/[^\s"]+)', html)
        if discord_match:
            comp.discord_channel = discord_match.group(1)

        # Reward tiers
        tier_pattern = re.compile(
            r'(?:If .+?(?:Critical|High|Medium|Low).+?'
            r'the reward pool will be \$([0-9,]+))',
            re.IGNORECASE
        )
        for m in tier_pattern.finditer(html):
            amount = float(m.group(1).replace(",", ""))
            text = m.group(0)
            severity = "unknown"
            for sev in ("Critical", "High", "Medium", "Low"):
                if sev in text:
                    severity = sev.lower()
                    break
            comp.reward_tiers.append({
                "severity": severity,
                "reward": amount,
            })

        # GitHub URLs
        gh_pattern = re.compile(r'https://github\.com/[^\s"<>]+')
        for m in gh_pattern.finditer(html):
            url = m.group(0).rstrip(")")
            if url not in comp.github_urls:
                comp.github_urls.append(url)

        # Audit links (Cantina, etc.)
        audit_pattern = re.compile(r'https://cantina\.xyz/portfolio/[^\s"<>]+')
        for m in audit_pattern.finditer(html):
            url = m.group(0)
            if url not in comp.audit_links:
                comp.audit_links.append(url)

    def _parse_scope_page(self, comp: AuditCompetition, html: str):
        """Parse a competition's scope page for assets."""
        # Extract GitHub repo links as scope assets
        gh_pattern = re.compile(
            r'(https://github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+(?:/tree/[^\s"<>]+)?)'
        )
        for m in gh_pattern.finditer(html):
            url = m.group(1).rstrip(")")
            asset = {"target": url, "type": "github_repo"}
            if asset not in comp.assets_in_scope:
                comp.assets_in_scope.append(asset)

        # Extract contract addresses
        addr_pattern = re.compile(r'(0x[a-fA-F0-9]{40})')
        for m in addr_pattern.finditer(html):
            addr = m.group(1)
            asset = {"target": addr, "type": "contract"}
            if asset not in comp.assets_in_scope:
                comp.assets_in_scope.append(asset)


def calculate_exergy_score(comp: AuditCompetition) -> float:
    """
    Calculate exergy score for competition prioritization.

    Score = (reward_norm × W_r + time_urgency × W_t + scope_density × W_s)
            × status_mult × type_mult

    Higher = more actionable.
    """
    # Reward normalization (log scale, cap at $2M)
    import math
    reward_norm = min(math.log10(max(comp.reward_pool, 1)) / math.log10(2_000_000), 1.0)

    # Time urgency: live > evaluating > finished
    time_urgency = {
        CompetitionStatus.LIVE: 1.0,
        CompetitionStatus.UPCOMING: 0.9,
        CompetitionStatus.EVALUATING: 0.3,  # Can still submit during eval
        CompetitionStatus.FINISHED: 0.0,
        CompetitionStatus.UNKNOWN: 0.1,
    }.get(comp.status, 0.1)

    # Scope density: more nSLOC = more surface area
    scope_density = min(comp.nsloc / 500_000, 1.0) if comp.nsloc > 0 else 0.5

    # Status multiplier
    status_mult = {
        CompetitionStatus.LIVE: 1.5,
        CompetitionStatus.UPCOMING: 1.3,
        CompetitionStatus.EVALUATING: 0.8,
        CompetitionStatus.FINISHED: 0.0,
        CompetitionStatus.UNKNOWN: 0.3,
    }.get(comp.status, 0.3)

    # Type multiplier
    type_mult = {
        CompetitionType.AUDIT_COMP: 1.0,
        CompetitionType.ATTACKATHON: 1.1,
        CompetitionType.BUG_BOUNTY_COMP: 1.2,
        CompetitionType.IOP: 0.7,
        CompetitionType.MITIGATION: 0.6,
    }.get(comp.comp_type, 1.0)

    # KYC penalty
    kyc_mult = 0.7 if comp.kyc_required else 1.0

    score = (
        reward_norm * 0.45
        + time_urgency * 0.30
        + scope_density * 0.25
    ) * status_mult * type_mult * kyc_mult

    comp.exergy_score = round(score, 4)
    return comp.exergy_score


async def _test():
    """Verify against live Immunefi."""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    async with AuditCompetitionScraper() as scraper:
        console.print("[bold blue]HYDRA · Audit Competition Scan[/bold blue]")
        comps = await scraper.fetch_competitions()
        console.print(f"  Total competitions: {len(comps)}")

        active = [c for c in comps if c.status != CompetitionStatus.FINISHED]
        console.print(f"  Active/Evaluating: {len(active)}")

        # Score all
        for c in comps:
            calculate_exergy_score(c)

        # Display table
        table = Table(title="Audit Competitions (Top 20)")
        table.add_column("#", justify="right", style="dim")
        table.add_column("Status", style="bold")
        table.add_column("Type", style="dim")
        table.add_column("Project", style="cyan")
        table.add_column("Reward Pool", justify="right", style="green")
        table.add_column("Time Left", style="yellow")
        table.add_column("Score", justify="right", style="magenta")
        table.add_column("KYC", justify="center")

        status_styles = {
            CompetitionStatus.LIVE: "bold green",
            CompetitionStatus.EVALUATING: "yellow",
            CompetitionStatus.UPCOMING: "blue",
            CompetitionStatus.FINISHED: "dim",
        }

        sorted_comps = sorted(comps, key=lambda c: c.exergy_score, reverse=True)
        for i, c in enumerate(sorted_comps[:20], 1):
            style = status_styles.get(c.status, "")
            table.add_row(
                str(i),
                c.status.value.upper(),
                c.comp_type.value[:8],
                c.project[:35],
                f"${c.reward_pool:,.0f}" if c.reward_pool else "TBD",
                c.time_remaining or "—",
                f"{c.exergy_score:.3f}",
                "⚠" if c.kyc_required else "✓",
                style=style,
            )
        console.print(table)


if __name__ == "__main__":
    asyncio.run(_test())
