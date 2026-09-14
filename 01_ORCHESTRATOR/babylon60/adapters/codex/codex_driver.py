"""
CORTEX CODEX RUNTIME DRIVER
===========================
Driver for programmatic interaction with OpenAI Codex Desktop & CLI.
Manages headless high-reasoning query dispatch (GPT-6 Astra Ultra),
interactive GUI session queuing, and live turn introspection from SQLite.

Invariants:
- INV_C5_17: Sovereign local control without third-party web dependencies.
- INV_BFT_02: Read-only query concurrency on Codex SQLite with WAL.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import subprocess
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("codex_tunnel.driver")


def _process_event_item(ev: dict[str, Any], agent_messages: list[str]) -> None:
    if ev.get("type") != "item.completed":
        return
    item = ev.get("item", {})
    if item.get("type") == "agent_message" and item.get("text"):
        agent_messages.append(item["text"])


def _parse_codex_events(lines: list[str]) -> tuple[Optional[str], list[str], dict[str, Any], list[dict[str, Any]]]:
    thread_id = None
    agent_messages: list[str] = []
    usage: dict[str, Any] = {}
    raw_events: list[dict[str, Any]] = []

    for line in lines:
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except Exception:
            continue

        raw_events.append(ev)
        ev_type = ev.get("type")
        if ev_type == "thread.started":
            thread_id = ev.get("thread_id")
        if ev_type == "turn.completed":
            usage = ev.get("usage", {})
        _process_event_item(ev, agent_messages)

    return thread_id, agent_messages, usage, raw_events


CODEX_CLI_PATH = Path("/Applications/ChatGPT.app/Contents/Resources/codex")
CODEX_HOME = Path.home() / ".codex"
THREAD_HISTORY_DB = CODEX_HOME / "thread_history_1.sqlite"
SESSION_INDEX = CODEX_HOME / "session_index.jsonl"
IPC_SOCK = CODEX_HOME / "ipc" / "ipc.sock"


class CodexDriver:
    """Interface to local OpenAI Codex CLI and Desktop application."""

    def __init__(self, cli_path: Optional[Path] = None, codex_home: Optional[Path] = None):
        self.cli_path = cli_path or CODEX_CLI_PATH
        self.codex_home = codex_home or CODEX_HOME
        self.history_db = self.codex_home / "thread_history_1.sqlite"
        self.session_index = self.codex_home / "session_index.jsonl"
        self.ipc_sock = self.codex_home / "ipc" / "ipc.sock"

    def check_health(self) -> dict[str, Any]:
        """Verify Codex local presence and runtime state."""
        cli_ok = self.cli_path.is_file() and os.access(self.cli_path, os.X_OK)
        sock_ok = self.ipc_sock.exists()
        history_ok = self.history_db.is_file()

        # Check if ChatGPT process is running
        ps_out = subprocess.run(
            ["pgrep", "-f", "ChatGPT.app/Contents/MacOS/ChatGPT"],
            capture_output=True,
            text=True,
        )
        pids = [int(p) for p in ps_out.stdout.strip().split() if p.isdigit()]
        gui_running = len(pids) > 0

        return {
            "cli_installed": cli_ok,
            "cli_path": str(self.cli_path),
            "ipc_socket_exists": sock_ok,
            "ipc_socket_path": str(self.ipc_sock),
            "history_db_exists": history_ok,
            "gui_running": gui_running,
            "gui_pids": pids,
            "status": "ready" if cli_ok else "missing_cli",
        }

    def ask(
        self,
        prompt: str,
        model: str = "gpt-6-astra",
        timeout_sec: int = 120,
        cwd: Optional[str] = None,
    ) -> dict[str, Any]:
        """Execute a headless query against Codex via JSON-L event stream."""
        if not self.cli_path.is_file():
            return {
                "success": False,
                "error": f"Codex CLI binary not found at {self.cli_path}",
            }

        cmd = [
            str(self.cli_path),
            "exec",
            "--ephemeral",
            "--skip-git-repo-check",
            "--dangerously-bypass-approvals-and-sandbox",
            "--json",
            "-m",
            model,
            prompt,
        ]

        work_dir = cwd or "/tmp"
        start_time = time.time()

        try:
            # We pipe empty stdin to close the prompt stdin reader cleanly
            proc = subprocess.run(
                cmd,
                input="",
                capture_output=True,
                text=True,
                cwd=work_dir,
                timeout=timeout_sec,
            )
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Codex execution timed out after {timeout_sec}s",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Codex execution failed: {e}",
            }

        duration_sec = time.time() - start_time
        lines = proc.stdout.strip().split("\n")
        thread_id, agent_messages, usage, raw_events = _parse_codex_events(lines)
        full_text = "\n".join(agent_messages)

        if proc.returncode != 0 and not full_text:
            return {
                "success": False,
                "returncode": proc.returncode,
                "error": proc.stderr or proc.stdout,
                "duration_sec": duration_sec,
            }

        return {
            "success": True,
            "text": full_text,
            "thread_id": thread_id,
            "usage": usage,
            "duration_sec": round(duration_sec, 2),
            "events_count": len(raw_events),
        }

    def queue_prompt(self, thread_id: str, message: str) -> dict[str, Any]:
        """Inject a prompt into an active Codex GUI thread via app-server."""
        if not self.cli_path.is_file():
            return {"success": False, "error": f"Codex CLI not found at {self.cli_path}"}

        cmd = [
            str(self.cli_path),
            "queue",
            "--thread",
            thread_id,
            "--message",
            message,
        ]

        try:
            proc = subprocess.run(
                cmd,
                input="",
                capture_output=True,
                text=True,
                timeout=15,
            )
            if proc.returncode == 0:
                return {"success": True, "output": proc.stdout.strip()}
            return {
                "success": False,
                "returncode": proc.returncode,
                "error": proc.stderr or proc.stdout,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_latest_session(self) -> Optional[dict[str, Any]]:
        """Retrieve the newest recorded session metadata from session_index.jsonl."""
        if not self.session_index.is_file():
            return None

        try:
            with open(self.session_index, "r", encoding="utf-8") as f:
                last_line = ""
                for line in f:
                    if line.strip():
                        last_line = line.strip()
                if last_line:
                    data = json.loads(last_line)
                    if isinstance(data, dict):
                        return data
        except Exception as e:
            logger.error("Failed to read session index: %s", e)
        return None

    def inspect_session(
        self,
        thread_id: Optional[str] = None,
        limit_items: int = 15,
    ) -> dict[str, Any]:
        """Read turns, reasoning, command executions, and messages from SQLite."""
        if not self.history_db.is_file():
            return {"error": "thread_history_1.sqlite not found"}

        if not thread_id:
            latest = self.get_latest_session()
            if not latest:
                return {"error": "No sessions found in session index"}
            thread_id = latest["id"]
            thread_name = latest.get("thread_name", "Untitled")
        else:
            thread_name = "Specified thread"

        try:
            conn = sqlite3.connect(f"file:{self.history_db}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row

            # Fetch turns
            cur = conn.execute(
                """
                SELECT turn_id, rollout_ordinal, status, started_at, completed_at, duration_ms
                FROM thread_turns
                WHERE thread_id = ?
                ORDER BY rollout_ordinal DESC
                LIMIT 5
                """,
                (thread_id,),
            )
            turns = [dict(r) for r in cur.fetchall()]

            # Fetch items
            cur_items = conn.execute(
                """
                SELECT rollout_ordinal, item_type, item_json
                FROM thread_items
                WHERE thread_id = ?
                ORDER BY rollout_ordinal DESC
                LIMIT ?
                """,
                (thread_id, limit_items),
            )
            raw_items = cur_items.fetchall()
            items = []
            for r in reversed(raw_items):
                try:
                    p = json.loads(r["item_json"])
                except Exception:
                    p = {"raw": r["item_json"]}
                items.append(
                    {
                        "rollout_ordinal": r["rollout_ordinal"],
                        "item_type": r["item_type"],
                        "data": p,
                    }
                )

            conn.close()

            return {
                "thread_id": thread_id,
                "thread_name": thread_name,
                "turns_count": len(turns),
                "latest_turn": turns[0] if turns else None,
                "turns": turns,
                "items": items,
            }
        except Exception as e:
            return {"error": f"Failed to query thread history: {e}"}
