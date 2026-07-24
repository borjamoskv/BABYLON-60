"""
BABYLON60 IDE — Chatbot Arena API routes.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from ..services.db_pool import connect_readonly

router = APIRouter(prefix="/api/arena", tags=["arena"])


def _get_babylon_db_dir() -> Path:
    return Path.home() / ".babylon60"


@router.get("/leaderboard")
def get_leaderboard() -> dict[str, Any]:
    """Get the latest LMSYS Chatbot Arena leaderboard sync."""
    db_dir = _get_babylon_db_dir()
    db_path = db_dir / "ojeador_leaderboard.db"

    if not db_path.exists():
        return {"exists": False, "models": [], "meta": {}}

    conn = connect_readonly(db_path)
    try:
        run_cursor = conn.execute(
            "SELECT id, fetched_at, last_updated, latency_ms, entropy FROM sync_runs ORDER BY id DESC LIMIT 1"
        )
        run = run_cursor.fetchone()
        if not run:
            return {"exists": False, "models": [], "meta": {}}

        run_id = run["id"]
        meta = {
            "fetched_at": run["fetched_at"],
            "last_updated": run["last_updated"],
            "latency_ms": run["latency_ms"],
            "entropy": run["entropy"],
        }

        models_cursor = conn.execute(
            "SELECT rank, model, vendor, score, votes FROM leaderboard_snapshots WHERE run_id = ? ORDER BY rank",
            (run_id,),
        )
        models = [dict(row) for row in models_cursor.fetchall()]

        return {"exists": True, "meta": meta, "models": models}
    except sqlite3.OperationalError as e:
        return {"exists": False, "models": [], "error": str(e)}
    finally:
        conn.close()


@router.get("/battles")
def get_battles() -> dict[str, Any]:
    """Get the domestic arena battles captured from the DOM."""
    db_dir = _get_babylon_db_dir()
    db_path = db_dir / "arena_alpha_ledger.db"

    if not db_path.exists():
        return {"exists": False, "battles": []}

    conn = connect_readonly(db_path)
    try:
        cursor = conn.execute(
            "SELECT id, timestamp, vector, prompt, model_a, model_b, response_a, response_b, winner, entropy_a, entropy_b, cortex_taint_hash "
            "FROM alpha_ledger ORDER BY id DESC LIMIT 50"
        )
        battles = [dict(row) for row in cursor.fetchall()]
        return {"exists": True, "battles": battles}
    except sqlite3.OperationalError as e:
        return {"exists": False, "battles": [], "error": str(e)}
    finally:
        conn.close()


@router.get("/conversations")
def get_conversations() -> dict[str, Any]:
    """Get processed sample conversations from Hugging Face toxic-chat dataset."""
    path = Path(__file__).resolve().parent.parent / "sample_toxic_chat.txt"
    if not path.exists():
        return {"exists": False, "conversations": [], "message": f"Sample file not found at {path.name}"}

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        parts = content.split("================================================================================")
        conversations = []
        for part in parts:
            part = part.strip()
            if not part:
                continue

            id_start = part.find("(ID: ")
            id_end = part.find(")")
            conv_id = "unknown"
            if id_start != -1 and id_end != -1:
                conv_id = part[id_start + 5 : id_end]

            prompt_marker = "Prompt:\n"
            prompt_start = part.find(prompt_marker)
            response_marker = "\n\nResponse:\n"
            response_start = part.find(response_marker)
            toxicity_marker = "\n\nToxicity (User/Model): "
            toxicity_start = part.find(toxicity_marker)

            prompt = ""
            response = ""
            toxicity = "None / None"

            if prompt_start != -1:
                start_idx = prompt_start + len(prompt_marker)
                end_idx = (
                    response_start if response_start != -1 else (toxicity_start if toxicity_start != -1 else len(part))
                )
                prompt = part[start_idx:end_idx].strip()

            if response_start != -1:
                start_idx = response_start + len(response_marker)
                end_idx = toxicity_start if toxicity_start != -1 else len(part)
                response = part[start_idx:end_idx].strip()

            if toxicity_start != -1:
                toxicity = part[toxicity_start + len(toxicity_marker) :].strip()

            conversations.append({"conv_id": conv_id, "prompt": prompt, "response": response, "toxicity": toxicity})

        return {"exists": True, "conversations": conversations}
    except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as e:
        return {"exists": False, "conversations": [], "error": str(e)}
