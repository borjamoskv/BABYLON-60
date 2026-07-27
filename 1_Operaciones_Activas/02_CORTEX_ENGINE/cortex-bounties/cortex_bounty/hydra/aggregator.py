"""
HYDRA — Unified Target Aggregator & Ranker

Merges data from Immunefi, Sherlock, Code4rena, and Hats on-chain
into a single ranked target list.

Score = (TVL_weight × Payout × Freshness) / Competition_density
"""
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from cortex_bounty.config import SCORING


@dataclass
class UnifiedTarget:
    """A bounty target normalized across all platforms."""
    id: str = ""
    platform: str = ""  # immunefi, sherlock, code4rena, hats
    project: str = ""
    max_payout: float = 0.0
    tvl_usd: float = 0.0
    category: str = ""
    status: str = ""
    deadline: str = ""
    repo_url: str = ""
    kyc_required: bool = False
    score: float = 0.0
    url: str = ""
    assets_count: int = 0
    nsloc: int = 0


class Aggregator:
    """
    Unified ranking engine. Collects targets from all HYDRA scrapers,
    normalizes them, and produces a ranked priority list.
    """

    def __init__(self):
        self.targets: list[UnifiedTarget] = []

    async def collect_all(self, min_payout: float = 0) -> list[UnifiedTarget]:
        """
        Collect targets from all platforms in parallel.
        Returns ranked list by composite score.
        """
        self.targets = []

        # Run all scrapers in parallel
        immunefi_task = self._collect_immunefi()
        sherlock_task = self._collect_sherlock()
        code4rena_task = self._collect_code4rena()

        results = await asyncio.gather(
            immunefi_task,
            sherlock_task,
            code4rena_task,
            return_exceptions=True
        )

        for result in results:
            if isinstance(result, list):
                self.targets.extend(result)
            elif isinstance(result, Exception):
                pass  # Platform unavailable — continue with others

        # Apply minimum payout filter
        if min_payout > 0:
            self.targets = [t for t in self.targets if t.max_payout >= min_payout]

        # Score and rank
        self._calculate_scores()

        return sorted(self.targets, key=lambda x: x.score, reverse=True)

    async def _collect_immunefi(self) -> list[UnifiedTarget]:
        """Collect from Immunefi."""
        targets = []
        try:
            from cortex_bounty.hydra.immunefi import ImmunefiScraper

            async with ImmunefiScraper() as scraper:
                programs = await scraper.fetch_all_programs()
                for p in programs:
                    targets.append(UnifiedTarget(
                        id=f"immunefi-{p.id}",
                        platform="immunefi",
                        project=p.project,
                        max_payout=p.max_bounty,
                        category=p.category,
                        status="active",
                        repo_url=p.github_urls[0] if p.github_urls else "",
                        kyc_required=p.kyc_required,
                        url=p.program_url,
                        assets_count=len(p.assets_in_scope),
                    ))
        except Exception:
            pass
        return targets

    async def _collect_sherlock(self) -> list[UnifiedTarget]:
        """Collect from Sherlock."""
        targets = []
        try:
            from cortex_bounty.hydra.sherlock import SherlockScraper

            async with SherlockScraper() as scraper:
                contests = await scraper.fetch_contests()
                for c in contests:
                    targets.append(UnifiedTarget(
                        id=f"sherlock-{c.id}",
                        platform="sherlock",
                        project=c.protocol,
                        max_payout=c.prize_pool,
                        status=c.status,
                        deadline=c.end_date,
                        repo_url=c.repo_url,
                        kyc_required=False,
                        url=c.contest_url,
                        nsloc=c.nsloc,
                    ))
        except Exception:
            pass
        return targets

    async def _collect_code4rena(self) -> list[UnifiedTarget]:
        """Collect from Code4rena."""
        targets = []
        try:
            from cortex_bounty.hydra.code4rena import Code4renaScraper

            async with Code4renaScraper() as scraper:
                contests = await scraper.fetch_contests()
                for c in contests:
                    targets.append(UnifiedTarget(
                        id=f"c4-{c.id}",
                        platform="code4rena",
                        project=c.protocol,
                        max_payout=c.prize_pool,
                        status=c.status,
                        deadline=c.end_date,
                        repo_url=c.repo_url,
                        kyc_required=c.kyc_required,
                        url=c.contest_url,
                        nsloc=c.nsloc,
                    ))
        except Exception:
            pass
        return targets

    def _calculate_scores(self):
        """
        Calculate composite score for each target.

        Score = (payout_norm * Wp + freshness_norm * Wf) * kyc_multiplier

        Higher score = higher priority target.
        """
        if not self.targets:
            return

        max_payout = max(t.max_payout for t in self.targets) or 1
        wp = SCORING["payout_weight"]
        wf = SCORING["freshness_weight"]

        now = datetime.now(timezone.utc)

        for t in self.targets:
            # Payout normalization (0-1)
            payout_norm = t.max_payout / max_payout if max_payout > 0 else 0

            # Freshness: contests with deadlines get urgency boost
            freshness_norm = 0.5
            if t.deadline:
                try:
                    deadline = datetime.fromisoformat(t.deadline.replace("Z", "+00:00"))
                    days_remaining = (deadline - now).days
                    if 0 < days_remaining <= 7:
                        freshness_norm = 1.0  # Urgent
                    elif 7 < days_remaining <= 14:
                        freshness_norm = 0.8
                    elif 14 < days_remaining <= 30:
                        freshness_norm = 0.6
                except (ValueError, TypeError):
                    pass

            # KYC penalty
            kyc_mult = 0.5 if t.kyc_required else 1.0

            # Platform bonus
            platform_mult = {
                "sherlock": 1.1,    # Direct USDC, pseudonymous
                "hats": 1.2,       # Full on-chain, no KYC
                "code4rena": 1.0,
                "immunefi": 0.8,   # KYC friction, slow triage
            }.get(t.platform, 1.0)

            t.score = (payout_norm * wp + freshness_norm * wf) * kyc_mult * platform_mult

    def add_hats_vaults(self, vaults: list) -> None:
        """Add Hats on-chain vaults to the target list."""
        for v in vaults:
            self.targets.append(UnifiedTarget(
                id=f"hats-pool-{v.pool_id}",
                platform="hats",
                project=f"{v.token_name} ({v.token_symbol})",
                max_payout=v.balance_usd if v.balance_usd > 0 else v.balance_human,
                tvl_usd=v.balance_usd,
                status=v.status,
                kyc_required=False,
            ))


async def _test():
    """Full aggregation test."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    agg = Aggregator()

    console.print("[bold]HYDRA · Full Platform Aggregation[/bold]", style="blue")
    targets = await agg.collect_all()
    console.print(f"  Total targets: {len(targets)}")

    if targets:
        table = Table(title=f"Top 20 Targets (of {len(targets)})")
        table.add_column("#", justify="right", style="dim")
        table.add_column("Platform", style="magenta")
        table.add_column("Project", style="cyan")
        table.add_column("Max Payout", justify="right", style="green")
        table.add_column("Score", justify="right", style="yellow")
        table.add_column("KYC", justify="center")
        table.add_column("Status")

        for i, t in enumerate(targets[:20], 1):
            table.add_row(
                str(i),
                t.platform.upper(),
                t.project[:35],
                f"${t.max_payout:,.0f}" if t.max_payout else "N/A",
                f"{t.score:.3f}",
                "⚠️" if t.kyc_required else "✅",
                t.status,
            )
        console.print(table)


if __name__ == "__main__":
    asyncio.run(_test())
