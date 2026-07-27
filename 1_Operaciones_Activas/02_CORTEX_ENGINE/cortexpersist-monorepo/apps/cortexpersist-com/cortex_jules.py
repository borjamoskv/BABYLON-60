#!/usr/bin/env python3
import os
import re
import json
import time
import urllib.request
import urllib.error
import subprocess

# Blocklist for directories
IGNORE_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    ".astro",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    ".next",
    "build",
    "out",
    ".vercel",
}

# Regex to match TODO or FIXME comments
TODO_PATTERN = re.compile(r"(?:#|//|<!--)\s*(TODO|FIXME)\s*:\s*(.*)", re.IGNORECASE)


class JulesDaemon:
    def __init__(self, workspace_path="."):
        self.workspace = os.path.abspath(workspace_path)
        self.server_url = "http://localhost:8000/agent_telemetry"
        self.dopamine = 50.0
        self.cortisol = 10.0
        self.adrenaline = 30.0
        self.state = "idle"

    def get_git_diff_stats(self):
        try:
            # Run git diff --shortstat
            out = (
                subprocess.check_output(
                    ["git", "diff", "--shortstat"],
                    cwd=self.workspace,
                    stderr=subprocess.DEVNULL,
                )
                .decode("utf-8")
                .strip()
            )

            if not out:
                return 0

            # Extract number of insertions/deletions
            # e.g., "1 file changed, 14 insertions(+), 10 deletions(-)"
            match = re.search(r"(\d+)\s+insertion", out)
            insertions = int(match.group(1)) if match else 0

            match = re.search(r"(\d+)\s+deletion", out)
            deletions = int(match.group(1)) if match else 0

            return insertions + deletions
        except Exception:
            return 0

    def scan_todos(self):
        todos = []
        for root, dirs, files in os.walk(self.workspace):
            # Prune ignored directories in-place
            dirs[:] = [
                d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")
            ]

            for file in files:
                ext = os.path.splitext(file)[1]
                if ext not in {
                    ".py",
                    ".ts",
                    ".tsx",
                    ".html",
                    ".js",
                    ".mjs",
                    ".astro",
                    ".css",
                }:
                    continue

                file_path = os.path.join(root, file)

                # Ignore files larger than 250KB to keep exergy high
                try:
                    if os.path.getsize(file_path) > 250000:
                        continue
                except OSError:
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_num, line in enumerate(f, 1):
                            match = TODO_PATTERN.search(line)
                            if match:
                                type_ = match.group(1).upper()
                                content = match.group(2).strip()
                                # Clean trailing HTML comment tags if present
                                content = re.sub(r"\s*-->.*", "", content)

                                priority = (
                                    "high"
                                    if (
                                        type_ == "FIXME"
                                        or "P0" in content.upper()
                                        or "CRITICAL" in content.upper()
                                    )
                                    else "normal"
                                )

                                # Limit content length
                                if len(content) > 100:
                                    content = content[:97] + "..."

                                todos.append(
                                    {
                                        "file": os.path.relpath(
                                            file_path, self.workspace
                                        ),
                                        "line": line_num,
                                        "text": content,
                                        "priority": priority,
                                    }
                                )
                except Exception:
                    pass
        return todos

    def update_endocrine(self, pending_todos_count, diff_changes):
        # Dopamine goes down as TODOs accumulate (cognitive debt), goes up when clean
        self.dopamine = max(10.0, 100.0 - pending_todos_count * 4.0)

        # Cortisol reflects overall load of pending work
        self.cortisol = min(100.0, pending_todos_count * 8.0)

        # Adrenaline spike when we are actively making changes (diffs > 0)
        if diff_changes > 0:
            self.adrenaline = min(100.0, 40.0 + diff_changes * 1.5)
            self.state = "executing"
        else:
            self.adrenaline = max(15.0, self.adrenaline - 5.0)  # decay adrenaline
            self.state = "scanning" if pending_todos_count > 0 else "idle"

    def report_telemetry(self, todos):
        payload = {
            "agent": "jules",
            "state": self.state,
            "dopamine": self.dopamine,
            "cortisol": self.cortisol,
            "adrenaline": self.adrenaline,
            "tasks": todos[:15],  # Send at most 15 tasks to keep packet small
        }

        # Write to local file for fallback/caching
        try:
            with open("cortex_jules_tasks.json", "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception:
            pass

        # POST payload to cortex server
        req = urllib.request.Request(
            self.server_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=1):
                pass
        except urllib.error.URLError:
            # Server might be offline, fallback gracefully
            pass

    def run_loop(self):
        while True:
            try:
                todos = self.scan_todos()
                diff_changes = self.get_git_diff_stats()
                self.update_endocrine(len(todos), diff_changes)
                self.report_telemetry(todos)
            except Exception as e:
                print(f"JULES Error in loop: {e}")
            time.sleep(3.0)  # Tick rate


if __name__ == "__main__":
    print("=" * 60)
    print("   [C5-REAL] JULES SECRETARIO DAEMON STARTED")
    print("   Scanning workspace for TODOs/FIXMEs and active git context...")
    print("=" * 60)
    daemon = JulesDaemon()
    try:
        daemon.run_loop()
    except KeyboardInterrupt:
        print("\nJULES Secretary daemon stopped.")
