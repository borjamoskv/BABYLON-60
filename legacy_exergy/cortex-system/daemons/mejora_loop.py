#!/usr/bin/env python3
"""
🔄 MEJORAlo Perpetual Loop — The Heartbeat of Improvement
==========================================================
A CORTEX daemon that continuously monitors project health,
detects decay, and triggers /mejoralo waves autonomously.

Usage:
    python mejora_loop.py                  # Interactive mode
    python mejora_loop.py --dry-run        # Preview without executing
    python mejora_loop.py --pulse          # Single pulse (one cycle)
    python mejora_loop.py --status         # Show loop health
    python mejora_loop.py --history        # Show improvement history
"""

import json
import os
import sqlite3
import subprocess
import sys
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Configuration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CORTEX_DIR = Path.home() / ".cortex"
CORTEX_DB = CORTEX_DIR / "cortex.db"
LOOP_STATE_FILE = CORTEX_DIR / "mejora_loop_state.json"
LOOP_LOG_FILE = CORTEX_DIR / "logs" / "mejora_loop.log"
WORKFLOW_PATH = CORTEX_DIR / "workflows" / "mejoralo.md"

# Tunables
DEFAULT_CONFIG = {
    "pulse_interval_hours": 6,       # How often to check for decay
    "decay_threshold_hours": 72,     # Files untouched for this long = decaying
    "error_growth_threshold": 3,     # New errors since last pulse = trigger
    "ghost_age_trigger_days": 7,     # Ghosts older than this = urgent
    "max_concurrent_waves": 1,       # Safety: only 1 wave at a time
    "self_improve_every_n": 5,       # Self-reflect on mejoralo.md every N pulses
    "dry_run": False,                # Preview mode
    "red_button": False,             # Emergency stop
    "cooldown_minutes": 30,          # Min time between waves on same project
    "max_daily_pulses": 12,          # Safety cap
}


class MejoraLoopState:
    """Persistent state for the improvement loop."""

    def __init__(self):
        self.state = self._load()

    def _load(self) -> dict:
        if LOOP_STATE_FILE.exists():
            with open(LOOP_STATE_FILE) as f:
                return json.load(f)
        return {
            "total_pulses": 0,
            "total_waves_triggered": 0,
            "last_pulse": None,
            "last_self_improve": None,
            "project_cooldowns": {},
            "improvement_history": [],
            "version_hash": None,
            "daily_pulse_count": 0,
            "daily_pulse_date": None,
        }

    def save(self):
        LOOP_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOOP_STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=2, default=str)

    def record_pulse(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if self.state.get("daily_pulse_date") != today:
            self.state["daily_pulse_count"] = 0
            self.state["daily_pulse_date"] = today
        self.state["total_pulses"] += 1
        self.state["daily_pulse_count"] += 1
        self.state["last_pulse"] = datetime.now().isoformat()
        self.save()

    def record_wave(self, project: str, score_before: int, score_after: int):
        self.state["total_waves_triggered"] += 1
        self.state["project_cooldowns"][project] = datetime.now().isoformat()
        self.state["improvement_history"].append({
            "project": project,
            "timestamp": datetime.now().isoformat(),
            "score_before": score_before,
            "score_after": score_after,
            "delta": score_after - score_before,
        })
        # Keep last 100 entries
        self.state["improvement_history"] = self.state["improvement_history"][-100:]
        self.save()

    def is_project_cooling(self, project: str, cooldown_min: int) -> bool:
        last = self.state.get("project_cooldowns", {}).get(project)
        if not last:
            return False
        last_dt = datetime.fromisoformat(last)
        return datetime.now() - last_dt < timedelta(minutes=cooldown_min)

    def daily_limit_reached(self, max_daily: int) -> bool:
        today = datetime.now().strftime("%Y-%m-%d")
        if self.state.get("daily_pulse_date") != today:
            return False
        return self.state.get("daily_pulse_count", 0) >= max_daily

    def should_self_improve(self, every_n: int) -> bool:
        return self.state["total_pulses"] % every_n == 0 and self.state["total_pulses"] > 0


class CortexScanner:
    """Scans CORTEX DB for decay signals."""

    def __init__(self):
        self.db_path = CORTEX_DB
        if not self.db_path.exists():
            raise FileNotFoundError(f"CORTEX DB not found: {self.db_path}")

    def _query(self, sql: str, params: tuple = ()) -> list:
        from babylon60.database.core import connect_sync

        with connect_sync(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(sql, params).fetchall()

    def get_active_projects(self) -> list[str]:
        """Get projects with recent activity."""
        rows = self._query(
            "SELECT DISTINCT project FROM facts WHERE (valid_until IS NULL OR valid_until > datetime('now'))"
        )
        return [r["project"] for r in rows if not r["project"].startswith("__")]

    def get_error_count(self, project: str) -> int:
        """Count active errors for a project."""
        rows = self._query(
            "SELECT COUNT(*) as cnt FROM facts WHERE project = ? AND fact_type = 'error' AND (valid_until IS NULL OR valid_until > datetime('now'))",
            (project,)
        )
        return rows[0]["cnt"] if rows else 0

    def get_ghost_count(self, project: str) -> int:
        """Count ghosts (stalled tasks) for a project."""
        rows = self._query(
            "SELECT COUNT(*) as cnt FROM facts WHERE project = ? AND fact_type = 'ghost' AND (valid_until IS NULL OR valid_until > datetime('now'))",
            (project,)
        )
        return rows[0]["cnt"] if rows else 0

    def get_last_decision_age(self, project: str) -> Optional[int]:
        """Hours since last decision was recorded for a project."""
        rows = self._query(
            "SELECT MAX(created_at) as latest FROM facts WHERE project = ? AND fact_type = 'decision'",
            (project,)
        )
        if rows and rows[0]["latest"]:
            try:
                last = datetime.fromisoformat(rows[0]["latest"].replace("Z", "+00:00"))
                delta = datetime.now(last.tzinfo) - last
                return int(delta.total_seconds() / 3600)
            except (ValueError, TypeError):
                pass
        return None

    def compute_decay_score(self, project: str, config: dict) -> dict:
        """
        Compute a 'Decay Score' for a project.
        Higher = more urgently needs improvement.
        
        Factors:
          - Error density (weight: 30)
          - Ghost presence (weight: 25)
          - Inactivity/staleness (weight: 25)
          - Time since last MEJORAlo wave (weight: 20)
        """
        errors = self.get_error_count(project)
        ghosts = self.get_ghost_count(project)
        last_decision_hours = self.get_last_decision_age(project)
        
        # Error score: 0-30
        error_score = min(errors * 10, 30)
        
        # Ghost score: 0-25
        ghost_score = min(ghosts * 12, 25)
        
        # Staleness score: 0-25
        staleness = 0
        if last_decision_hours is not None:
            if last_decision_hours > config["decay_threshold_hours"]:
                staleness = min(25, int((last_decision_hours - config["decay_threshold_hours"]) / 24) * 5)
        
        # Recency score (inverse of last wave): 0-20
        recency = 20  # Max if never improved
        
        total = error_score + ghost_score + staleness + recency
        
        return {
            "project": project,
            "decay_score": min(total, 100),
            "errors": errors,
            "ghosts": ghosts,
            "staleness_hours": last_decision_hours,
            "breakdown": {
                "error_score": error_score,
                "ghost_score": ghost_score,
                "staleness_score": staleness,
                "recency_score": recency,
            }
        }


class SelfReflector:
    """
    The Ouroboros: MEJORAlo improves itself.
    Analyzes the mejoralo.md workflow for potential improvements
    based on historical success/failure patterns.
    """

    def __init__(self, state: MejoraLoopState):
        self.state = state
        self.workflow_path = WORKFLOW_PATH

    def compute_workflow_hash(self) -> str:
        """Hash the current workflow for change detection."""
        if not self.workflow_path.exists():
            return "MISSING"
        content = self.workflow_path.read_text()
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def analyze_effectiveness(self) -> dict:
        """Analyze improvement history for patterns."""
        history = self.state.state.get("improvement_history", [])
        if len(history) < 3:
            return {"status": "INSUFFICIENT_DATA", "entries": len(history)}

        deltas = [h["delta"] for h in history]
        avg_delta = sum(deltas) / len(deltas)
        positive = sum(1 for d in deltas if d > 0)
        negative = sum(1 for d in deltas if d < 0)
        zero = sum(1 for d in deltas if d == 0)

        # Detect stagnation: last 3 waves had zero or negative improvement
        recent = deltas[-3:]
        stagnating = all(d <= 0 for d in recent)

        # Detect regression: any negative delta
        regressing = negative > 0

        return {
            "status": "STAGNATING" if stagnating else "REGRESSING" if regressing else "HEALTHY",
            "total_waves": len(history),
            "avg_improvement": round(avg_delta, 1),
            "positive_waves": positive,
            "negative_waves": negative,
            "zero_waves": zero,
            "stagnating": stagnating,
            "recommendations": self._generate_recommendations(stagnating, regressing, avg_delta),
        }

    def _generate_recommendations(self, stagnating: bool, regressing: bool, avg_delta: float) -> list[str]:
        recs = []
        if stagnating:
            recs.append("STAGNATION DETECTED: Consider adding new dimensions to X-Ray scan")
            recs.append("Try --deep mode to unlock Psi dimension analysis")
            recs.append("Review /sacrifice log — abandoned approaches may now be viable")
        if regressing:
            recs.append("REGRESSION DETECTED: Enable stricter verification in Fase 5")
            recs.append("Add regression tests before each wave")
        if avg_delta < 2:
            recs.append("LOW IMPACT: Consider raising the bar — target 'Trascendencia' wave more aggressively")
        if avg_delta > 10:
            recs.append("HIGH IMPACT: Current approach is very effective — document patterns as Skills")
        return recs

    def generate_self_improvement_report(self) -> str:
        """Generate a report for the Ouroboros phase."""
        effectiveness = self.analyze_effectiveness()
        current_hash = self.compute_workflow_hash()
        previous_hash = self.state.state.get("version_hash", "UNKNOWN")

        report = []
        report.append("━" * 50)
        report.append("🐍 OUROBOROS — Self-Reflection Report")
        report.append("━" * 50)
        report.append(f"  Workflow Hash: {current_hash}")
        report.append(f"  Changed Since Last Check: {'YES' if current_hash != previous_hash else 'NO'}")
        report.append(f"  Status: {effectiveness['status']}")
        
        if effectiveness.get("total_waves"):
            report.append(f"  Total Waves: {effectiveness['total_waves']}")
            report.append(f"  Avg Δ Score: {effectiveness['avg_improvement']:+.1f}")
            report.append(f"  Win Rate: {effectiveness.get('positive_waves', 0)}/{effectiveness['total_waves']}")
        
        if effectiveness.get("recommendations"):
            report.append("")
            report.append("  📋 Recommendations:")
            for rec in effectiveness["recommendations"]:
                report.append(f"    → {rec}")

        report.append("━" * 50)

        # Update hash
        self.state.state["version_hash"] = current_hash
        self.state.state["last_self_improve"] = datetime.now().isoformat()
        self.state.save()

        return "\n".join(report)


class MejoraLoop:
    """
    🔄 The Perpetual Improvement Loop.
    
    Architecture:
        PULSE → SCAN → TRIAGE → TRIGGER → REFLECT → PERSIST → SLEEP → PULSE
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.state = MejoraLoopState()
        self.scanner = CortexScanner()
        self.reflector = SelfReflector(self.state)
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        LOOP_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    def _log(self, msg: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line)
        with open(LOOP_LOG_FILE, "a") as f:
            f.write(line + "\n")

    def pulse(self) -> dict:
        """
        Execute one pulse of the improvement loop.
        Returns a summary of what was found and done.
        """
        # Safety checks
        if self.config["red_button"]:
            self._log("🔴 RED BUTTON ACTIVE — Loop is paused")
            return {"status": "PAUSED", "reason": "red_button"}

        if self.state.daily_limit_reached(self.config["max_daily_pulses"]):
            self._log("⚠️ Daily pulse limit reached — sleeping")
            return {"status": "RATE_LIMITED", "reason": "daily_cap"}

        self._log("💓 PULSE — Scanning for decay...")
        self.state.record_pulse()

        # 1. SCAN all active projects
        projects = self.scanner.get_active_projects()
        self._log(f"  📡 Found {len(projects)} active projects")

        # 2. TRIAGE: compute decay scores
        decay_reports = []
        for proj in projects:
            try:
                report = self.scanner.compute_decay_score(proj, self.config)
                decay_reports.append(report)
            except Exception as e:
                self._log(f"  ⚠️ Error scanning {proj}: {e}")

        # Sort by decay score (most urgent first)
        decay_reports.sort(key=lambda r: r["decay_score"], reverse=True)

        # 3. TRIGGER: fire /mejoralo on projects exceeding threshold
        triggered = []
        for report in decay_reports:
            if report["decay_score"] >= 40:  # Threshold for action
                proj = report["project"]
                
                if self.state.is_project_cooling(proj, self.config["cooldown_minutes"]):
                    self._log(f"  ❄️ {proj} is cooling down — skipping")
                    continue
                
                self._log(f"  🔥 TRIGGER: {proj} (decay={report['decay_score']})")
                
                if not self.config["dry_run"]:
                    self._trigger_mejoralo(proj, report)
                else:
                    self._log(f"  🏜️ DRY RUN — would trigger /mejoralo on {proj}")
                
                triggered.append(report)
                
                if len(triggered) >= self.config["max_concurrent_waves"]:
                    break

        # 4. REFLECT: Self-improve every N pulses
        self_reflection = None
        if self.state.should_self_improve(self.config["self_improve_every_n"]):
            self._log("🐍 OUROBOROS — Self-reflecting on mejoralo.md...")
            self_reflection = self.reflector.generate_self_improvement_report()
            self._log(self_reflection)

        # 5. Summary
        summary = {
            "status": "COMPLETE",
            "pulse_number": self.state.state["total_pulses"],
            "projects_scanned": len(projects),
            "decay_reports": decay_reports[:5],  # Top 5
            "waves_triggered": len(triggered),
            "self_reflection": self_reflection is not None,
            "timestamp": datetime.now().isoformat(),
        }

        self._log(f"  ✅ Pulse complete: {len(triggered)} waves triggered, {len(projects)} scanned")
        return summary

    def _trigger_mejoralo(self, project: str, report: dict):
        """Trigger a /mejoralo wave on a project."""
        self._log(f"  🌊 Triggering wave on {project}...")
        
        # Record wave (with placeholder scores — real scores come from the wave)
        self.state.record_wave(project, 100 - report["decay_score"], 0)
        
        # The actual trigger would interface with your IDE/agent
        # For now, we log the intent and create a CORTEX fact
        try:
            subprocess.run(
                ["python3", "-m", "cortex.cli", "add",
                 "--project", project,
                 "--type", "task",
                 "--content", f"MEJORAlo Perpetual Loop triggered (decay={report['decay_score']}). Errors={report['errors']}, Ghosts={report['ghosts']}."],
                capture_output=True, text=True, timeout=10
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self._log(f"  ⚠️ Could not write to CORTEX: {e}")

    def status(self) -> str:
        """Show the current status of the loop."""
        s = self.state.state
        lines = [
            "━" * 50,
            "🔄 MEJORAlo Perpetual Loop — Status",
            "━" * 50,
            f"  Total Pulses:     {s.get('total_pulses', 0)}",
            f"  Total Waves:      {s.get('total_waves_triggered', 0)}",
            f"  Last Pulse:       {s.get('last_pulse', 'Never')}",
            f"  Last Self-Improve: {s.get('last_self_improve', 'Never')}",
            f"  Daily Pulses:     {s.get('daily_pulse_count', 0)}/{self.config['max_daily_pulses']}",
            f"  Red Button:       {'🔴 ACTIVE' if self.config['red_button'] else '🟢 OFF'}",
            f"  Workflow Hash:    {s.get('version_hash', 'Unknown')}",
            "",
            "  📊 Improvement History (last 5):",
        ]
        
        history = s.get("improvement_history", [])[-5:]
        if not history:
            lines.append("    (no history yet)")
        for h in history:
            lines.append(f"    {h.get('project', '?')} | Δ{h.get('delta', 0):+d} | {h.get('timestamp', '?')[:16]}")
        
        lines.append("━" * 50)
        return "\n".join(lines)

    def run_forever(self):
        """Run the loop perpetually."""
        self._log("🌌 MEJORAlo Perpetual Loop ACTIVATED")
        self._log(f"  Pulse interval: {self.config['pulse_interval_hours']}h")
        self._log(f"  Decay threshold: {self.config['decay_threshold_hours']}h")
        self._log(f"  Max daily pulses: {self.config['max_daily_pulses']}")
        
        while True:
            try:
                self.pulse()
                sleep_seconds = self.config["pulse_interval_hours"] * 3600
                self._log(f"  😴 Sleeping for {self.config['pulse_interval_hours']}h...")
                time.sleep(sleep_seconds)
            except KeyboardInterrupt:
                self._log("🛑 Loop interrupted by user")
                break
            except Exception as e:
                self._log(f"❌ Loop error: {e}")
                time.sleep(60)  # Brief cooldown on error


def main():
    args = sys.argv[1:]
    
    if "--help" in args:
        print(__doc__)
        return
    
    loop = MejoraLoop({"dry_run": "--dry-run" in args})
    
    if "--status" in args:
        print(loop.status())
    elif "--history" in args:
        history = loop.state.state.get("improvement_history", [])
        if not history:
            print("No improvement history yet.")
        for h in history:
            print(f"  {h['timestamp'][:16]} | {h['project']} | Δ{h['delta']:+d}")
    elif "--pulse" in args:
        result = loop.pulse()
        print(json.dumps(result, indent=2, default=str))
    elif "--reflect" in args:
        report = loop.reflector.generate_self_improvement_report()
        print(report)
    else:
        loop.run_forever()


if __name__ == "__main__":
    main()
