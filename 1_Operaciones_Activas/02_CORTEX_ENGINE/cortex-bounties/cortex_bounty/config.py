"""
CORTEX-BOUNTY Config — Centralized API keys, paths, and settings.
All secrets read from environment. Zero hardcoded credentials.
"""
import os
from pathlib import Path

# ─── Paths ──────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
SUBMISSIONS_DIR = PROJECT_ROOT / "submissions"
TARGETS_DIR = PROJECT_ROOT / "targets"
INTEL_DIR = PROJECT_ROOT / "intel"
HUNT_DIR = PROJECT_ROOT / "hunt"
DB_PATH = PROJECT_ROOT / "cortex_bounty" / "ledger" / "bounty_ledger.db"

# ─── API Keys (env) ────────────────────────────────────────────
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")  # Free tier works

# ─── API Endpoints (C5-REAL) ───────────────────────────────────
DEFILLAMA_BASE = "https://api.llama.fi"
ETHERSCAN_V2_BASE = "https://api.etherscan.io/v2/api"
GITHUB_API_BASE = "https://api.github.com"
COINGECKO_BASE = "https://api.coingecko.com/api/v3"

IMMUNEFI_GRAPHQL = "https://immunefi.com/api/bounties"
IMMUNEFI_EXPLORE = "https://immunefi.com/explore/"
SHERLOCK_API = "https://app.sherlock.xyz/audits"
CODE4RENA_API = "https://code4rena.com"
HATS_VAULTS_V2 = "0x571f39d351513146248AcafA9D0509319A327C4D"

# ─── RPC ────────────────────────────────────────────────────────
ETH_RPC_URL = os.getenv("ETH_RPC_URL", "https://ethereum-rpc.publicnode.com")

# ─── Scoring Weights ───────────────────────────────────────────
SCORING = {
    "tvl_weight": 0.25,
    "payout_weight": 0.35,
    "freshness_weight": 0.20,
    "competition_weight": 0.20,
    "min_payout_default": 10_000,
}

# ─── User Agent ─────────────────────────────────────────────────
USER_AGENT = "CORTEX-BountyEngine/2.0"
