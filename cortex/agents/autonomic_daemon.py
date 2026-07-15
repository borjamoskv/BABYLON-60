import os
import sys
import time
import yaml
import psutil
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


DB_PATH = Path("/Users/borjafernandezangulo/30_BABYLON-60/telemetry.db")
REPORT_PATH = Path("/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/cortex/audits/overnight_swarm_report.yaml")

class AutonomicSwarmDaemon:
    def __init__(self) -> None:
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.db_conn = sqlite3.connect(DB_PATH, timeout=5.0)
        self.db_conn.execute("PRAGMA journal_mode=WAL;")
        self.db_conn.execute("PRAGMA synchronous=NORMAL;")

    def scan_processes(self) -> Dict[str, Any]:
        """Detects python zombie processes or memory anomalies."""
        zombies = []
        current_pid = os.getpid()
        
        for proc in psutil.process_iter(['pid', 'name', 'create_time', 'memory_info']):
            try:
                # Check for python processes other than the current executing script
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    if proc.info['pid'] != current_pid:
                        elapsed = time.time() - proc.info['create_time']
                        # Mark as zombie if it has been running for > 3600 seconds (1 hour)
                        if elapsed > 3600:
                            zombies.append({
                                "pid": proc.info['pid'],
                                "elapsed_sec": elapsed,
                                "memory_mb": proc.info['memory_info'].rss / (1024 * 1024)
                            })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
        return {
            "current_pid": current_pid,
            "zombies_count": len(zombies),
            "zombies_list": zombies
        }

    def run_telemetry(self) -> Dict[str, Any]:
        """Runs local model latency and swap simulation measurements."""
        telemetry_results = {}
        
        # Measure local model TTFT & Throughput (qwen2.5:0.5b)
        try:
            from cortex.telemetry.throughput_measurement import measure_throughput
            prompt, token_count, total_time_ms, tps, status, err = measure_throughput("qwen2.5:0.5b")
            telemetry_results["qwen2.5"] = {
                "status": status,
                "tps": tps if status == "SUCCESS" else 0.0,
                "latency_ms": total_time_ms if status == "SUCCESS" else 0.0,
                "error": err
            }
        except Exception as e:
            telemetry_results["qwen2.5"] = {"status": "FAILED", "error": str(e)}

        # Run Layer Swap Simulator (simulate Llama-3-70B sequential load)
        try:
            from cortex.engine.layer_swap_simulator import LayerSwapSimulator
            sim = LayerSwapSimulator(num_layers=32, layer_size_mb=100.0)
            speed = sim.calibrate_disk_speed()
            seq_time, _ = sim.run_sequential_benchmark()
            pipe_time, _ = sim.run_pipelined_benchmark()
            telemetry_results["layer_swap"] = {
                "disk_speed_mb_s": speed,
                "seq_time_ms": seq_time,
                "pipe_time_ms": pipe_time,
                "efficiency_gain_pct": ((seq_time - pipe_time) / seq_time) * 100.0 if seq_time > 0 else 0.0
            }
        except Exception as e:
            telemetry_results["layer_swap"] = {"status": "FAILED", "error": str(e)}

        return telemetry_results

    def check_workspace(self) -> Dict[str, Any]:
        """Checks git tree state and AST syntax compilation."""
        # Git status
        git_status_res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        dirty_files = [line.strip() for line in git_status_res.stdout.split('\n') if line.strip()]
        
        # AST check
        ast_failures = []
        try:
            import py_compile
            from tests.test_syntax_integrity import _tracked_python_files
            for path in _tracked_python_files():
                try:
                    py_compile.compile(str(path), doraise=True)
                except Exception as e:
                    ast_failures.append({"file": str(path), "error": str(e)})
        except Exception as e:
            ast_failures.append({"file": "general_syntax_test", "error": str(e)})

        return {
            "git_dirty": len(dirty_files) > 0,
            "dirty_files_count": len(dirty_files),
            "dirty_files": dirty_files[:10],
            "ast_ok": len(ast_failures) == 0,
            "ast_failures": ast_failures
        }

    def generate_report(self) -> None:
        """Executes full diagnostic run and persists overnight report."""
        os.makedirs(REPORT_PATH.parent, exist_ok=True)
        
        # Run diagnostics
        proc_data = self.scan_processes()
        telem_data = self.run_telemetry()
        work_data = self.check_workspace()
        
        # Calculate session exergy
        exergy_saved_ms = 0.0
        if "layer_swap" in telem_data and "seq_time_ms" in telem_data["layer_swap"]:
            exergy_saved_ms = telem_data["layer_swap"]["seq_time_ms"] - telem_data["layer_swap"]["pipe_time_ms"]

        report = {
            "Claim": "Autonomic Swarm Daemon overnight state consolidation.",
            "Timestamp": self.timestamp,
            "Creator": "Borja Moskv (borjamoskv)",
            "Environment": "C5-REAL",
            "Metrics": {
                "processes": proc_data,
                "telemetry": telem_data,
                "workspace": work_data,
                "exergy_saved_ms": exergy_saved_ms
            }
        }

        # Write YAML report
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            yaml.dump(report, f, default_flow_style=False, sort_keys=False)

        # Also insert a log record into telemetry.db
        self.db_conn.execute("""
            CREATE TABLE IF NOT EXISTS autonomic_daemon_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                zombies_count INTEGER NOT NULL,
                qwen_tps REAL NOT NULL,
                disk_speed REAL NOT NULL,
                git_dirty INTEGER NOT NULL,
                ast_ok INTEGER NOT NULL
            )
        """)
        
        qwen_tps = telem_data.get("qwen2.5", {}).get("tps", 0.0)
        disk_speed = telem_data.get("layer_swap", {}).get("disk_speed_mb_s", 0.0)
        git_dirty = 1 if work_data["git_dirty"] else 0
        ast_ok = 1 if work_data["ast_ok"] else 0

        self.db_conn.execute(
            """
            INSERT INTO autonomic_daemon_log 
            (timestamp, zombies_count, qwen_tps, disk_speed, git_dirty, ast_ok) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (self.timestamp, proc_data["zombies_count"], qwen_tps, disk_speed, git_dirty, ast_ok)
        )
        self.db_conn.commit()
        self.db_conn.close()

if __name__ == "__main__":
    daemon = AutonomicSwarmDaemon()
    daemon.generate_report()
    print(f"🟢 [STATUS_OK / EXERGY] Swarm Daemon cycle completed. Report saved at {REPORT_PATH}")
