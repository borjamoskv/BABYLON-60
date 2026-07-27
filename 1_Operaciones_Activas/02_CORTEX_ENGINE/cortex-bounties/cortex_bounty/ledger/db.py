"""
LEDGER — SQLite Portfolio Database

Schema + CRUD for tracking hunts, submissions, and payouts.
"""
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Optional

from cortex_bounty.config import DB_PATH


def _ensure_db_dir():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class BountyDB:
    """SQLite-backed bounty portfolio tracker."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(DB_PATH)
        _ensure_db_dir()
        self.conn = sqlite3.connect(self.db_path, timeout=5.0)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS hunts (
                id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                target TEXT NOT NULL,
                category TEXT DEFAULT '',
                started_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                status TEXT DEFAULT 'scouting',
                hours_spent REAL DEFAULT 0,
                notes TEXT DEFAULT '',
                max_payout REAL DEFAULT 0,
                repo_url TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS submissions (
                id TEXT PRIMARY KEY,
                hunt_id TEXT REFERENCES hunts(id),
                platform TEXT NOT NULL,
                title TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                submitted_at TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                payout_usd REAL DEFAULT 0,
                report_hash TEXT DEFAULT '',
                report_path TEXT DEFAULT '',
                notes TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS payouts (
                id TEXT PRIMARY KEY,
                submission_id TEXT REFERENCES submissions(id),
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'USDC',
                tx_hash TEXT DEFAULT '',
                received_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS findings (
                id TEXT PRIMARY KEY,
                hunt_id TEXT REFERENCES hunts(id),
                pattern_id TEXT DEFAULT '',
                severity TEXT DEFAULT 'medium',
                file TEXT DEFAULT '',
                line INTEGER DEFAULT 0,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'open',
                created_at TEXT NOT NULL
            );
        """)
        self.conn.commit()

    # ─── Hunts ──────────────────────────────────────────────
    def create_hunt(self, platform: str, target: str, **kwargs) -> str:
        hunt_id = f"HUNT-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT INTO hunts (id, platform, target, started_at, updated_at, category, max_payout, repo_url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (hunt_id, platform, target, now, now,
             kwargs.get("category", ""), kwargs.get("max_payout", 0),
             kwargs.get("repo_url", "")),
        )
        self.conn.commit()
        return hunt_id

    def update_hunt(self, hunt_id: str, **kwargs):
        sets = []
        vals = []
        for k, v in kwargs.items():
            if k in ("status", "hours_spent", "notes"):
                sets.append(f"{k} = ?")
                vals.append(v)
        if sets:
            sets.append("updated_at = ?")
            vals.append(datetime.now(timezone.utc).isoformat())
            vals.append(hunt_id)
            self.conn.execute(
                f"UPDATE hunts SET {', '.join(sets)} WHERE id = ?", vals
            )
            self.conn.commit()

    def get_hunts(self, status: Optional[str] = None) -> list[dict]:
        if status:
            rows = self.conn.execute(
                "SELECT * FROM hunts WHERE status = ? ORDER BY updated_at DESC", (status,)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM hunts ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    # ─── Submissions ────────────────────────────────────────
    def create_submission(self, hunt_id: str, platform: str, title: str,
                          severity: str = "medium", report_hash: str = "",
                          report_path: str = "") -> str:
        sub_id = f"SUB-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT INTO submissions (id, hunt_id, platform, title, severity, "
            "submitted_at, report_hash, report_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (sub_id, hunt_id, platform, title, severity, now, report_hash, report_path),
        )
        self.conn.commit()
        return sub_id

    def update_submission(self, sub_id: str, **kwargs):
        sets = []
        vals = []
        for k, v in kwargs.items():
            if k in ("status", "payout_usd", "notes"):
                sets.append(f"{k} = ?")
                vals.append(v)
        if sets:
            vals.append(sub_id)
            self.conn.execute(
                f"UPDATE submissions SET {', '.join(sets)} WHERE id = ?", vals
            )
            self.conn.commit()

    def get_submissions(self, hunt_id: Optional[str] = None) -> list[dict]:
        if hunt_id:
            rows = self.conn.execute(
                "SELECT * FROM submissions WHERE hunt_id = ? ORDER BY submitted_at DESC",
                (hunt_id,)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM submissions ORDER BY submitted_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    # ─── Payouts ────────────────────────────────────────────
    def record_payout(self, submission_id: str, amount: float,
                      currency: str = "USDC", tx_hash: str = "") -> str:
        payout_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT INTO payouts (id, submission_id, amount, currency, tx_hash, received_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (payout_id, submission_id, amount, currency, tx_hash, now),
        )
        # Update submission
        self.conn.execute(
            "UPDATE submissions SET status = 'paid', payout_usd = ? WHERE id = ?",
            (amount, submission_id)
        )
        self.conn.commit()
        return payout_id

    # ─── Analytics ──────────────────────────────────────────
    def get_stats(self) -> dict:
        hunts = self.conn.execute("SELECT COUNT(*) as c FROM hunts").fetchone()["c"]
        subs = self.conn.execute("SELECT COUNT(*) as c FROM submissions").fetchone()["c"]
        accepted = self.conn.execute(
            "SELECT COUNT(*) as c FROM submissions WHERE status IN ('accepted', 'paid')"
        ).fetchone()["c"]
        total_payout = self.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM payouts"
        ).fetchone()["total"]
        total_hours = self.conn.execute(
            "SELECT COALESCE(SUM(hours_spent), 0) as total FROM hunts"
        ).fetchone()["total"]

        hit_rate = (accepted / subs * 100) if subs > 0 else 0
        hourly_rate = (total_payout / total_hours) if total_hours > 0 else 0

        return {
            "total_hunts": hunts,
            "total_submissions": subs,
            "accepted": accepted,
            "hit_rate": hit_rate,
            "total_payout_usd": total_payout,
            "total_hours": total_hours,
            "hourly_rate_usd": hourly_rate,
        }

    def get_pipeline(self) -> dict:
        """Funnel: scouting → analyzing → writing → submitted → accepted → paid"""
        pipeline = {}
        for status in ("scouting", "analyzing", "writing", "submitted", "accepted", "paid", "rejected"):
            count = self.conn.execute(
                "SELECT COUNT(*) as c FROM hunts WHERE status = ?", (status,)
            ).fetchone()["c"]
            pipeline[status] = count
        return pipeline

    def close(self):
        self.conn.close()
