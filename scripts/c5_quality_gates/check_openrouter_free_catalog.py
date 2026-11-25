#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ OPENROUTER FREE CATALOG WATCHDOG | DOMAIN: c5_quality_gates | STATE: C5-REAL
# ============================================================================
"""
ROYAL-RUMBLE v2 Live Catalog Watchdog for OpenRouter `:free` endpoints.
Audits presence, context windows, and parameter support of the canonical free fleet:
  - thinkingmachines/inkling:free
  - thinkingmachines/inkling-small:free
  - poolside/laguna-s-2.1:free (sunset 2026-10-31)
  - cohere/north-mini-code:free
  - nvidia/nemotron-3-super-120b-a12b:free
  - nvidia/nemotron-3.5-super-vl:free
"""

import argparse
from datetime import date
import json
from pathlib import Path
import sys
import urllib.request
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).absolute().parents[2]
for _sub in ("02_EDIN_SWARMS", "01_KISH_ENGINE"):
    _p = str(REPO_ROOT / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from agents_archi.clients.openrouter import (  # noqa: E402
    POOLSIDE_FREE_SUNSET_DATE,
    _assert_ssrf_safe,
)

MODELS_URL = "https://openrouter.ai/api/v1/models"
EMBEDDINGS_URL = "https://openrouter.ai/api/v1/embeddings/models"

CANONICAL_CHAT_MODELS: List[str] = [
    "thinkingmachines/inkling:free",
    "thinkingmachines/inkling-small:free",
    "cohere/north-mini-code:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3.5-super-vl:free",
    "openrouter/free",
]

CANONICAL_EMBED_MODELS: List[str] = [
    "nvidia/nemotron-3-embed-1b:free",
    "nvidia/llama-nemotron-embed-vl-1b-v2:free",
]


def fetch_catalog(url: str, timeout: float = 10.0) -> Dict[str, Dict[str, Any]]:
    _assert_ssrf_safe(url)
    req = urllib.request.Request(url, headers={"User-Agent": "BABYLON-60-MOSKV-1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    data = payload.get("data", [])
    return {str(item["id"]): item for item in data if isinstance(item, dict) and "id" in item}


def audit_catalog(reference_date: date | None = None) -> Dict[str, Any]:
    today = reference_date or date.today()
    chat_by_id = fetch_catalog(MODELS_URL)
    embed_by_id = fetch_catalog(EMBEDDINGS_URL)

    expected_chat = list(CANONICAL_CHAT_MODELS)
    if today <= POOLSIDE_FREE_SUNSET_DATE:
        expected_chat.insert(2, "poolside/laguna-s-2.1:free")

    missing_chat: List[str] = []
    verified_chat: List[Dict[str, Any]] = []

    for mid in expected_chat:
        if mid not in chat_by_id:
            missing_chat.append(mid)
            continue
        meta = chat_by_id[mid]
        pricing = meta.get("pricing") or {}
        prompt_price = str(pricing.get("prompt", "0"))
        verified_chat.append(
            {
                "id": mid,
                "context_length": meta.get("context_length"),
                "max_completion_tokens": (meta.get("top_provider") or {}).get("max_completion_tokens"),
                "prompt_price": prompt_price,
                "supported_parameters": meta.get("supported_parameters", []),
            }
        )

    missing_embed = [mid for mid in CANONICAL_EMBED_MODELS if mid not in embed_by_id]

    return {
        "date": today.isoformat(),
        "poolside_sunset_active": today > POOLSIDE_FREE_SUNSET_DATE,
        "total_free_chat_models": sum(1 for k in chat_by_id if k.endswith(":free") or k == "openrouter/free"),
        "verified_chat": verified_chat,
        "missing_chat": missing_chat,
        "missing_embed": missing_embed,
        "healthy": len(missing_chat) == 0 and len(missing_embed) == 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit OpenRouter ROYAL-RUMBLE v2 :free catalog.")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    args = parser.parse_args()

    report = audit_catalog()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        status = "PASS" if report["healthy"] else "WARN"
        print(f"[{status}] OpenRouter ROYAL-RUMBLE v2 Catalog ({report['date']}) — Free Chat Models: {report['total_free_chat_models']}")
        for m in report["verified_chat"]:
            print(f"  + {m['id']:44s} ctx={m['context_length']} max_out={m['max_completion_tokens']} price={m['prompt_price']}")
        if report["missing_chat"]:
            print(f"  ! Missing chat models: {report['missing_chat']}")
        if report["missing_embed"]:
            print(f"  ! Missing embed models: {report['missing_embed']}")

    return 0 if report["healthy"] else 1


if __name__ == "__main__":
    sys.exit(main())
