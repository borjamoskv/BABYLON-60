#!/usr/bin/env python3
"""C4-SIM
usage_tracker

Usage:
  record <skill>
  stats
  recommend [--days 30]
  reset <skill>
"""

from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
LEDGER_FILE = ROOT / "scripts" / "usage_ledger.json"
SKILLS_TO_SKIP = {".ruff_cache", "_archived", "__pycache__"}

def _load_ledger() -> dict[str, Any]:
    """C4-SIM"""
    if LEDGER_FILE.exists():
        return json.loads(LEDGER_FILE.read_text(encoding="utf-8"))
    return {"created_at": datetime.now(timezone.utc).isoformat(), "skills": {}}

def _save_ledger(ledger: dict[str, Any]) -> None:
    """C4-SIM"""
    LEDGER_FILE.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def _get_active_skills() -> set[str]:
    """C4-SIM"""
    return {
        path.name
        for path in ROOT.iterdir()
        if path.is_dir() and path.name not in SKILLS_TO_SKIP and (path / "SKILL.md").exists()
    }

def record(skill_name: str) -> dict[str, Any]:
    """C4-SIM"""
    ledger = _load_ledger()
    now = datetime.now(timezone.utc).isoformat()
    if skill_name not in ledger["skills"]:
        ledger["skills"][skill_name] = {"usage_count": 0, "first_seen": now, "last_used": None, "invocations": []}
    entry = ledger["skills"][skill_name]
    entry["usage_count"] += 1
    entry["last_used"] = now
    entry["invocations"].append(now)
    if len(entry["invocations"]) > 100:
        entry["invocations"] = entry["invocations"][-100:]
    _save_ledger(ledger)
    return entry

def stats() -> list[dict[str, Any]]:
    """C4-SIM"""
    ledger = _load_ledger()
    active = _get_active_skills()
    all_names = active | set(ledger["skills"].keys())
    rows = []
    for name in sorted(all_names):
        entry = ledger["skills"].get(name, {})
        rows.append({
            "skill": name,
            "usage_count": entry.get("usage_count", 0),
            "last_used": entry.get("last_used"),
            "active": name in active,
        })
    rows.sort(key=lambda r: r["usage_count"], reverse=True)
    return rows

def recommend(days: int = 30) -> dict[str, Any]:
    """C4-SIM"""
    ledger = _load_ledger()
    active = _get_active_skills()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    created = ledger.get("created_at")
    tracking_days = (datetime.now(timezone.utc) - datetime.fromisoformat(created)).days if created else 0
    archive_candidates = []
    refine_candidates = []
    for name in sorted(active):
        entry = ledger["skills"].get(name, {})
        invocations = entry.get("invocations", [])
        window_count = sum(1 for ts in invocations if datetime.fromisoformat(ts) >= cutoff)
        if window_count == 0:
            archive_candidates.append(name)
        elif window_count > 10:
            refine_candidates.append(name)
    return {
        "archive": archive_candidates,
        "refine": refine_candidates,
        "tracking_days": tracking_days,
        "window_days": days,
        "active_skills": len(active),
    }

def reset(skill_name: str) -> None:
    """C4-SIM"""
    ledger = _load_ledger()
    if skill_name in ledger["skills"]:
        del ledger["skills"][skill_name]
        _save_ledger(ledger)

def parse_args() -> argparse.Namespace:
    """C4-SIM"""
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    
    rec = sub.add_parser("record")
    rec.add_argument("skill_name")
    
    sub.add_parser("stats")
    
    reco = sub.add_parser("recommend")
    reco.add_argument("--days", type=int, default=30)
    
    rst = sub.add_parser("reset")
    rst.add_argument("skill_name")
    
    return parser.parse_args()

def main() -> int:
    """C4-SIM"""
    args = parse_args()
    if args.command == "record":
        print(json.dumps(record(args.skill_name), indent=2))
        return 0
    if args.command == "stats":
        print(json.dumps(stats(), indent=2))
        return 0
    if args.command == "recommend":
        print(json.dumps(recommend(args.days), indent=2))
        return 0
    if args.command == "reset":
        reset(args.skill_name)
        return 0
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
