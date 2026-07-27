"""
JIL v2 — Just-In-Time Intelligence Layer (Refactored)

Migrated from jil_engine.py. Same C5-REAL API calls,
now integrated into the cortex_bounty package.
"""
import time
from dataclasses import dataclass, field
from typing import Optional

import aiohttp

from cortex_bounty.config import (
    DEFILLAMA_BASE, ETHERSCAN_V2_BASE, GITHUB_API_BASE,
    ETHERSCAN_API_KEY, GITHUB_TOKEN, USER_AGENT,
)


@dataclass
class ProtocolIntel:
    name: str = ""
    slug: str = ""
    category: str = ""
    chains: list = field(default_factory=list)
    tvl_current: float = 0.0
    tvl_peak: float = 0.0
    tvl_trend: str = ""
    github_org: str = ""
    token_symbol: str = ""
    audit_links: list = field(default_factory=list)
    contracts: dict = field(default_factory=dict)
    source_code: dict = field(default_factory=dict)
    risk_score: float = 0.0


class JILEngine:
    """C5-REAL API Bridge — DefiLlama + Etherscan V2 + GitHub."""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": USER_AGENT}
        )
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def defillama_protocol(self, slug: str) -> dict:
        url = f"{DEFILLAMA_BASE}/protocol/{slug}"
        async with self.session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {
                    "name": data.get("name", ""),
                    "category": data.get("category", ""),
                    "chains": data.get("chains", []),
                    "tvl": data.get("currentChainTvls", {}),
                    "github": data.get("github", []),
                    "audit_links": data.get("audit_links", []),
                    "symbol": data.get("symbol", ""),
                }
            return {"error": f"HTTP {resp.status}"}

    async def defillama_tvl_history(self, slug: str, days: int = 90) -> list:
        url = f"{DEFILLAMA_BASE}/protocol/{slug}"
        async with self.session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                tvl_data = data.get("tvl", [])
                cutoff = time.time() - (days * 86400)
                return [
                    {"date": p["date"], "tvl": p["totalLiquidityUSD"]}
                    for p in tvl_data
                    if p["date"] >= cutoff and p["totalLiquidityUSD"] > 0
                ]
            return []

    async def defillama_search(self, query: str) -> list:
        url = f"{DEFILLAMA_BASE}/protocols"
        async with self.session.get(url) as resp:
            if resp.status == 200:
                protocols = await resp.json()
                q = query.lower()
                matches = [
                    {"name": p["name"], "slug": p["slug"],
                     "tvl": p.get("tvl", 0), "category": p.get("category", ""),
                     "chains": p.get("chains", [])}
                    for p in protocols
                    if q in p.get("name", "").lower() or q in p.get("slug", "").lower()
                ]
                return sorted(matches, key=lambda x: x["tvl"], reverse=True)
            return []

    async def etherscan_source(self, address: str, chain_id: int = 1) -> dict:
        if not ETHERSCAN_API_KEY:
            return {"error": "ETHERSCAN_API_KEY not set"}
        params = {
            "chainid": chain_id, "module": "contract",
            "action": "getsourcecode", "address": address,
            "apikey": ETHERSCAN_API_KEY,
        }
        async with self.session.get(ETHERSCAN_V2_BASE, params=params) as resp:
            data = await resp.json()
            if data.get("status") == "1" and data.get("result"):
                r = data["result"][0]
                return {
                    "contract_name": r.get("ContractName", ""),
                    "compiler": r.get("CompilerVersion", ""),
                    "proxy": r.get("Proxy", "0"),
                    "implementation": r.get("Implementation", ""),
                }
            return {"error": data.get("result", "Unknown")}

    async def github_list_repos(self, org: str) -> list:
        headers = {"Accept": "application/vnd.github.v3+json"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
        async with self.session.get(
            f"{GITHUB_API_BASE}/orgs/{org}/repos",
            params={"per_page": 100, "sort": "updated"},
            headers=headers
        ) as resp:
            if resp.status == 200:
                repos = await resp.json()
                return [
                    {"name": r["name"], "language": r.get("language", ""),
                     "stars": r.get("stargazers_count", 0), "url": r["html_url"]}
                    for r in repos
                ]
            return []

    async def full_recon(self, target: str, address: str = None) -> ProtocolIntel:
        """Full JIL reconnaissance."""
        intel = ProtocolIntel(name=target, slug=target.lower())

        # DefiLlama
        dl = await self.defillama_protocol(target.lower())
        if "error" not in dl:
            intel.name = dl.get("name", target)
            intel.category = dl.get("category", "")
            intel.chains = dl.get("chains", [])
            intel.token_symbol = dl.get("symbol", "")
            intel.audit_links = dl.get("audit_links", [])
            intel.github_org = (dl.get("github", [None]) or [None])[0] or ""
            tvl = dl.get("tvl", {})
            intel.tvl_current = sum(
                v for k, v in tvl.items()
                if isinstance(v, (int, float)) and "staking" not in k.lower()
            )

        # TVL trend
        history = await self.defillama_tvl_history(target.lower(), 90)
        if len(history) >= 2:
            first, last = history[0]["tvl"], history[-1]["tvl"]
            if first > 0:
                change = (last - first) / first * 100
                intel.tvl_trend = "declining" if change < -10 else ("growing" if change > 10 else "stable")
                intel.tvl_peak = max(p["tvl"] for p in history)

        # Etherscan
        if address and ETHERSCAN_API_KEY:
            src = await self.etherscan_source(address)
            if "error" not in src:
                intel.source_code[address] = src

        # Risk score
        risk = 0
        if intel.tvl_current < 100_000: risk += 30
        if intel.tvl_trend == "declining": risk += 20
        if not intel.audit_links: risk += 25
        if len(intel.chains) > 3: risk += 15
        intel.risk_score = min(risk, 100)

        return intel
