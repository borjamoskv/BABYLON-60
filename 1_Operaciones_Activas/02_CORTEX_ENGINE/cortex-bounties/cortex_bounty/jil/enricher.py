"""
JIL v2 — Enricher

Cross-references JIL protocol intel with HYDRA bounty targets
to identify high-value audit opportunities.
"""
from cortex_bounty.jil.engine import ProtocolIntel


class Enricher:
    """Cross-references JIL intel with HYDRA targets."""

    def enrich_target(self, intel: ProtocolIntel, target: dict) -> dict:
        """
        Merge JIL protocol data with a HYDRA target.

        Returns enriched target dict with:
        - TVL data from DefiLlama
        - Risk score
        - Audit history
        - GitHub repos
        """
        return {
            **target,
            "tvl_current": intel.tvl_current,
            "tvl_peak": intel.tvl_peak,
            "tvl_trend": intel.tvl_trend,
            "risk_score": intel.risk_score,
            "audit_count": len(intel.audit_links),
            "chains": intel.chains,
            "category": intel.category or target.get("category", ""),
            "github_org": intel.github_org,
        }

    def calculate_opportunity_score(self, intel: ProtocolIntel, max_payout: float) -> float:
        """
        Score = (payout × risk_factor × tvl_factor) / audit_coverage

        Higher score = better opportunity.
        """
        risk_factor = intel.risk_score / 100 if intel.risk_score > 0 else 0.5
        tvl_factor = min(intel.tvl_current / 1_000_000, 10) if intel.tvl_current > 0 else 1.0
        audit_penalty = max(1, len(intel.audit_links))

        return (max_payout * risk_factor * tvl_factor) / audit_penalty
