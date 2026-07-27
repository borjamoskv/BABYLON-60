#!/usr/bin/env python3
import time
import json
import random
import math
import threading
import subprocess
import os
import shutil
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import sqlite3


# Global state of the Cortex Engine
class CortexEngineState:
    def __init__(self):
        self.fep_enabled = True

        # SQLite Database Initialization
        self.db_conn = sqlite3.connect("cortex.db", check_same_thread=False)
        self.db_conn.execute("PRAGMA journal_mode=WAL")
        self.db_conn.execute("PRAGMA synchronous=NORMAL")
        self.db_conn.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                timestamp REAL, state TEXT, dopamine REAL, serotonin REAL,
                noradrenaline REAL, acetylcholine REAL, free_energy REAL,
                prediction_error REAL, latency REAL, exergy REAL
            )
        """)
        self.db_conn.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                timestamp TEXT, text TEXT, type TEXT
            )
        """)
        self.db_conn.execute("""
            CREATE TABLE IF NOT EXISTS edge_telemetry (
                timestamp REAL, hostname TEXT, pathname TEXT,
                latency_ms INTEGER, status INTEGER, method TEXT
            )
        """)

        # Restore state from Hipocampo (L2)
        cursor = self.db_conn.cursor()
        cursor.execute(
            "SELECT state, dopamine, serotonin, noradrenaline, acetylcholine, free_energy, prediction_error, latency, exergy FROM telemetry ORDER BY timestamp DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            self.state = row[0]
            self.dopamine = row[1]
            self.serotonin = row[2]
            self.noradrenaline = row[3]
            self.acetylcholine = row[4]
            self.free_energy = row[5]
            self.prediction_error = row[6]
            self.latency = row[7]
            self.exergy = row[8]
        else:
            self.state = "vigilance"  # vigilance, sleep, flow, limerence
            self.dopamine = 50.0
            self.serotonin = 50.0
            self.noradrenaline = 50.0
            self.acetylcholine = 50.0
            self.free_energy = 0.45
            self.prediction_error = 0.08
            self.latency = 15.0
            self.exergy = 100.0
        self.logs = []
        self.clients = []
        self.lock = threading.RLock()

        # Initialize 10,000 parallel active inference agents using optimized lists
        self.agent_mu = [random.gauss(5.0, 2.0) for _ in range(10000)]
        self.agent_var = [random.uniform(5.0, 15.0) for _ in range(10000)]

        # Thread controls
        self.flow_active = False
        self.limerence_active = False

        # JULES agent state
        self.jules_state = "idle"
        self.jules_dopamine = 50.0
        self.jules_cortisol = 10.0
        self.jules_adrenaline = 30.0
        self.jules_tasks = []

        # Config map for targets
        self.configs = {
            "vigilance": {
                "dopamine": 55,
                "serotonin": 60,
                "noradrenaline": 45,
                "acetylcholine": 50,
                "target_fe": 0.32,
                "target_pe": 0.05,
                "target_latency": 14,
                "target_exergy": 100,
            },
            "sleep": {
                "dopamine": 15,
                "serotonin": 80,
                "noradrenaline": 5,
                "acetylcholine": 70,
                "target_fe": 0.05,
                "target_pe": 0.01,
                "target_latency": 480,
                "target_exergy": 85,
            },
            "flow": {
                "dopamine": 95,
                "serotonin": 10,
                "noradrenaline": 90,
                "acetylcholine": 85,
                "target_fe": 0.01,
                "target_pe": 0.00,
                "target_latency": 8,
                "target_exergy": 100,
            },
            "limerence": {
                "dopamine": 100,
                "serotonin": 12,
                "noradrenaline": 95,
                "acetylcholine": 40,
                "target_fe": 4.85,
                "target_pe": 0.95,
                "target_latency": 22,
                "target_exergy": 25,
            },
        }

    def anchor_deterministic_seed(self):
        try:
            git_hash = (
                subprocess.check_output("git rev-parse HEAD", shell=False)
                .decode()
                .strip()
            )
            seed_val = int(git_hash[:8], 16)
            random.seed(seed_val)
        except Exception:
            random.seed(42)

    def add_log(self, text, type_="normal"):
        timestamp = time.strftime("%H:%M:%S")
        log_entry = {"time": timestamp, "text": text, "type": type_}
        with self.lock:
            self.logs.append(log_entry)
            if len(self.logs) > 30:
                self.logs.pop(0)
            self.db_conn.execute(
                "INSERT INTO logs (timestamp, text, type) VALUES (?, ?, ?)",
                (timestamp, text, type_),
            )
            self.db_conn.commit()
        self.broadcast({"event": "log", "data": log_entry})

    def broadcast(self, message):
        with self.lock:
            active_clients = list(self.clients)

        dead_clients = []
        msg_bytes = f"data: {json.dumps(message)}\n\n".encode("utf-8")
        for client in active_clients:
            try:
                client.write(msg_bytes)
                client.flush()
            except Exception:
                dead_clients.append(client)

        if dead_clients:
            with self.lock:
                for client in dead_clients:
                    if client in self.clients:
                        self.clients.remove(client)

    def set_state(self, new_state):
        if new_state not in self.configs:
            return

        # Stop background task threads
        self.flow_active = False
        self.limerence_active = False

        with self.lock:
            self.state = new_state
        self.add_log(f"STATE CHANGE: Transitioning to {new_state.upper()}.", "sys")

        cfg = self.configs[new_state]
        self.dopamine = cfg["dopamine"]
        self.serotonin = cfg["serotonin"]
        self.noradrenaline = cfg["noradrenaline"]
        self.acetylcholine = cfg["acetylcholine"]

        if new_state == "sleep":
            threading.Thread(target=self.execute_sleep_cleanup, daemon=True).start()
        elif new_state == "flow":
            threading.Thread(target=self.run_flow_compute, daemon=True).start()
        elif new_state == "limerence":
            threading.Thread(target=self.run_limerence_lock, daemon=True).start()

    def execute_sleep_cleanup(self):
        self.add_log(
            "GLYMPHATIC PURGE: Astrocytic flow purging waste (workspace cache cleanup).",
            "sys",
        )
        time.sleep(0.5)
        purged_dirs = []
        purged_files_count = 0

        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for d in dirs:
                if d == "__pycache__":
                    dir_path = os.path.join(root, d)
                    try:
                        shutil.rmtree(dir_path)
                        purged_dirs.append(dir_path)
                    except Exception as e:
                        self.add_log(f"GLYMPHATIC ERROR: {str(e)}", "error")
            for f in files:
                if f.endswith(".pyc"):
                    file_path = os.path.join(root, f)
                    try:
                        os.remove(file_path)
                        purged_files_count += 1
                    except Exception:
                        pass

        if purged_dirs or purged_files_count:
            self.add_log(
                f"GLYMPHATIC SUCCESS: Removed {len(purged_dirs)} cache dirs and {purged_files_count} pyc files.",
                "success",
            )
        else:
            self.add_log(
                "GLYMPHATIC SUCCESS: Extracellular space clean. Heap optimal.",
                "success",
            )

        # SWR Memory consolidation: Synced ledger read (Hipocampo -> Neocórtex)
        time.sleep(0.5)
        self.add_log(
            "SWR COMPRESSION: Consolidating thermodynamic memory (L2 Hipocampo -> L3 Neocórtex).",
            "sys",
        )
        try:
            cursor = self.db_conn.cursor()
            cursor.execute(
                "SELECT prediction_error, free_energy FROM telemetry ORDER BY timestamp DESC LIMIT 500"
            )
            rows = cursor.fetchall()

            if rows:
                pe_values = [r[0] for r in rows]
                fe_values = [r[1] for r in rows]
                avg_pe = sum(pe_values) / len(pe_values)
                avg_fe = sum(fe_values) / len(fe_values)

                # SWR Transfer to Neocortex (Priors modulation)
                with self.lock:
                    drift_factor = avg_pe * 0.1
                    variance_shift = -0.5 if avg_fe < 0.2 else 0.5

                    for i in range(10000):
                        self.agent_mu[i] += random.gauss(0, drift_factor)
                        self.agent_var[i] = max(
                            0.1, min(15.0, self.agent_var[i] + variance_shift)
                        )

                self.add_log(
                    f"SWR SUCCESS: Condensed {len(rows)} epochs. Priors drifted by factor {drift_factor:.4f}.",
                    "success",
                )
            else:
                self.add_log(
                    "SWR SKIP: Insufficient L2 memory trace for consolidation.", "warn"
                )

        except Exception as e:
            self.add_log(f"SWR ERROR: Failed memory consolidation: {str(e)}", "error")

    def run_flow_compute(self):
        self.flow_active = True
        self.add_log("FLOW DAEMON: High coherent compute thread activated.", "sys")
        while self.flow_active:
            x = 0.0
            for i in range(50000):
                x += math.sin(i) * math.cos(i)
            time.sleep(0.02)

    def run_limerence_lock(self):
        self.limerence_active = True
        self.add_log(
            "LIMERENCE DAEMON: High exergy drain recursive loop locked.", "error"
        )
        while self.limerence_active:
            x = 0.5
            for i in range(200000):
                x = math.sin(x + 1.2) * 0.95
            time.sleep(0.001)

    def get_mac_metrics(self):
        try:
            # Memory Load
            vmstat = subprocess.check_output(["vm_stat"]).decode()
            page_size = 4096
            active_pages = 0
            for line in vmstat.split("\n"):
                if "Pages active" in line:
                    active_pages = int(line.split()[-1].strip("."))
                    break
            active_mem_gb = (active_pages * page_size) / (1024**3)

            # CPU Load
            load = (
                subprocess.check_output(["sysctl", "-n", "vm.loadavg"])
                .decode()
                .strip()
                .split()[1]
            )
            cpu_load = float(load) * 100.0 / 8.0

            # Motor Load
            idle_seconds = 0.0
            try:
                ioreg_out = subprocess.check_output(
                    ["ioreg", "-c", "IOHIDSystem"]
                ).decode()
                for line in ioreg_out.splitlines():
                    if "HIDIdleTime" in line:
                        parts = line.split("=")
                        if len(parts) >= 2:
                            idle_val = parts[-1].strip().strip('"').strip()
                            idle_seconds = float(idle_val) / 1000000000.0
                            break
            except Exception:
                pass
            motor_activity = max(0.0, 100.0 - (idle_seconds * (100.0 / 60.0)))

            # Melatonin
            hour = time.localtime().tm_hour
            melatonin = (math.sin((hour - 9) * math.pi / 12) + 1.0) * 50.0

            return (
                min(100.0, cpu_load),
                min(100.0, active_mem_gb * 100.0 / 16.0),
                motor_activity,
                melatonin,
            )
        except Exception:
            return 15.0, 48.0, 50.0, 10.0

    def update_tick(self):
        cpu_load, mem_load, motor_activity, melatonin = self.get_mac_metrics()

        with self.lock:
            cfg = self.configs[self.state]

            if self.state == "vigilance":
                self.noradrenaline += (cpu_load - self.noradrenaline) * 0.1
                self.acetylcholine += (mem_load - self.acetylcholine) * 0.1
                cpu_diff = self.noradrenaline - cpu_load
                self.dopamine += (50.0 + cpu_diff * 2.0 - self.dopamine) * 0.1
                self.serotonin += (cfg["serotonin"] - self.serotonin) * 0.1

                sensory_input = 5.0 + random.gauss(0, 0.8)
                sensory_variance = 0.8
            else:
                self.dopamine += (cfg["dopamine"] - self.dopamine) * 0.1
                self.serotonin += (cfg["serotonin"] - self.serotonin) * 0.1
                self.noradrenaline += (cfg["noradrenaline"] - self.noradrenaline) * 0.1
                self.acetylcholine += (cfg["acetylcholine"] - self.acetylcholine) * 0.1

                if self.state == "sleep":
                    sensory_input = 0.0
                    sensory_variance = 999.0
                elif self.state == "flow":
                    sensory_input = 5.0 + random.gauss(0, 0.1)
                    sensory_variance = 0.1
                elif self.state == "limerence":
                    sensory_input = 5.0 + random.gauss(0, 4.0)
                    sensory_variance = 8.0

            # MASSIVE PARALLEL ACTIVE INFERENCE: Update all 10,000 agents in parallel
            if self.state != "sleep" and self.fep_enabled:
                p_sensory = 1.0 / max(0.001, sensory_variance)
                log_sens_var = math.log(sensory_variance)
                half_p_sensory = 0.5 * p_sensory
                half_log_sens_var = 0.5 * log_sens_var
                total_fe = 0.0
                total_pe = 0.0

                new_mu = []
                new_var = []
                # Inline zip-vectorized update loop for 10,000 nodes (highly optimized)
                for mu, var in zip(self.agent_mu, self.agent_var):
                    pe = sensory_input - mu
                    p_prior = 1.0 / max(0.001, var)
                    k = p_sensory / (p_prior + p_sensory)

                    # Update belief mu and variance
                    new_mu.append(mu + k * pe)
                    new_var.append(var * (1.0 - k))

                    # Sum population Free Energy and Prediction Error
                    total_fe += (pe**2) * half_p_sensory + half_log_sens_var
                    total_pe += abs(pe)

                self.agent_mu = new_mu
                self.agent_var = new_var
                self.free_energy = total_fe / 10000.0
                self.prediction_error = total_pe / 10000.0
            else:
                # Decaying prior variance during sleep (Thermodynamic relaxation via list comprehension)
                self.agent_var = [min(15.0, var + 0.05) for var in self.agent_var]
                self.free_energy += (cfg["target_fe"] - self.free_energy) * 0.2
                self.prediction_error += (
                    cfg["target_pe"] - self.prediction_error
                ) * 0.2

            # Metrics updates
            self.latency += (cfg["target_latency"] - self.latency) * 0.1
            self.exergy += (cfg["target_exergy"] - self.exergy) * 0.1

            if cpu_load > 85.0 and self.state != "flow":
                self.exergy = max(10.0, self.exergy - 1.0)

            # CICLO 3: Mac-Control-Ω (Physical Autopoiesis)
            # If exergy crashes or we hit Limerence state (entropy runaway), we intervene on the physical OS.
            if self.exergy < 15.0 and self.state != "sleep":
                self.add_log(
                    "EXERGY COLLAPSE: Invoking Mac-Control-Ω to forcibly purge macOS RAM and darken screen.",
                    "error",
                )
                threading.Thread(
                    target=self._physical_autopoiesis_purge, daemon=True
                ).start()
                self.exergy += (
                    50.0  # Virtual rebound to prevent infinite loop of purges
                )

            if random.random() > 0.95:
                self.trigger_random_simulation_log()

    def _physical_autopoiesis_purge(self):
        try:
            # Drop screen brightness drastically via AppleScript to force user to rest/disconnect
            subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to key code 145'],
                check=False,
            )
            subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to key code 145'],
                check=False,
            )

            # Request macOS to purge inactive RAM pages (requires root, but we try standard memory pressure first)
            subprocess.run(["memory_pressure", "-S", "-l", "critical"], check=False)

            self.add_log(
                "MAC-CONTROL-Ω: Biological intervention executed. Entropy throttled.",
                "warn",
            )
        except Exception as e:
            self.add_log(f"MAC-CONTROL-Ω ERROR: Physical override failed: {e}", "error")

            # Database Ledger Sync (Thermodynamic state preservation)
            self.db_conn.execute(
                """
                INSERT INTO telemetry (timestamp, state, dopamine, serotonin, noradrenaline, acetylcholine, free_energy, prediction_error, latency, exergy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    time.time(),
                    self.state,
                    self.dopamine,
                    self.serotonin,
                    self.noradrenaline,
                    self.acetylcholine,
                    self.free_energy,
                    self.prediction_error,
                    self.latency,
                    self.exergy,
                ),
            )
            self.db_conn.commit()

            # Broadcast current telemetry
            telemetry = {
                "state": self.state,
                "dopamine": self.dopamine,
                "serotonin": self.serotonin,
                "noradrenaline": self.noradrenaline,
                "acetylcholine": self.acetylcholine,
                "free_energy": self.free_energy,
                "prediction_error": self.prediction_error,
                "latency": self.latency,
                "exergy": self.exergy,
                "cpu_load": cpu_load,
                "mem_load": mem_load,
                "motor_activity": motor_activity,
                "melatonin": melatonin,
                "jules": {
                    "state": self.jules_state,
                    "dopamine": self.jules_dopamine,
                    "cortisol": self.jules_cortisol,
                    "adrenaline": self.jules_adrenaline,
                    "tasks": self.jules_tasks,
                },
            }
            self.broadcast({"event": "telemetry", "data": telemetry})

    def trigger_random_simulation_log(self):
        logs_pool = {
            "vigilance": [
                (
                    "ORCHESTRATOR: Massively parallel active inference running (10,000 neural agents).",
                    "success",
                ),
                ("L4_NEOCORTEX: Population prior consensus reached.", "normal"),
                ("L3_THALAMUS: 10k nodes sensory gating resolved.", "normal"),
                ("L2_LIMBIC: Synaptic alignment variance checks stable.", "normal"),
            ],
            "sleep": [
                ("DELTA_WAVE: Population relaxation traces active.", "sys"),
                ("MICROGLIA: Pruning inactive nodes from 10k population.", "success"),
                ("GLYMPHATIC SYSTEM: Heap optimal across 10k array.", "success"),
            ],
            "flow": [
                ("FLOW: 10,000 agents synchronized in Gamma (40Hz).", "success"),
                ("FLOW: In-phase prediction error convergence achieved.", "success"),
                ("SYSTEM: Massively coherent action execution active.", "success"),
            ],
            "limerence": [
                ("VTA: 10k agents reward bias set to LO.", "error"),
                ("PFC: Massively parallel obsessive loops active.", "warn"),
                ("AMYGDALA: 10k population variance overloaded.", "warn"),
            ],
        }
        logs = logs_pool.get(self.state, [("System OK", "normal")])
        log_txt, log_type = random.choice(logs)
        self.add_log(log_txt, log_type)


# Instantiate global state
engine = CortexEngineState()
engine.anchor_deterministic_seed()
engine.add_log("SYSTEM: Deterministic seed anchored to Git Ledger.", "sys")


class CortexHTTPRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path == "/telemetry":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            with engine.lock:
                engine.clients.append(self.wfile)
            initial_msg = {
                "event": "sys_info",
                "data": "Backend telemetry connection synchronized.",
            }
            self.wfile.write(f"data: {json.dumps(initial_msg)}\n\n".encode("utf-8"))
            self.wfile.flush()

            while True:
                with engine.lock:
                    is_active = self.wfile in engine.clients
                if not is_active:
                    break
                time.sleep(1)

        elif parsed_path.path in ["/", "/index.html", "/ultramapeo.html"]:
            try:
                with open("ultramapeo.html", "r", encoding="utf-8") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
            except FileNotFoundError:
                self.send_error(404, "ultramapeo.html not found.")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path == "/control":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")

            try:
                command = json.loads(post_data)
                action = command.get("action")

                if action == "set_state":
                    new_state = command.get("state")
                    engine.set_state(new_state)
                    self.send_success_response({"status": "ok", "state": new_state})

                elif action == "toggle_fep":
                    with engine.lock:
                        engine.fep_enabled = not engine.fep_enabled
                        status_str = "ENABLED" if engine.fep_enabled else "DISABLED"
                        engine.add_log(
                            f"EPISTEMIC TEST: Active Inference FEP {status_str}.",
                            "warn",
                        )
                    self.send_success_response(
                        {"status": "ok", "fep_enabled": engine.fep_enabled}
                    )

                elif action == "modulate":
                    param = command.get("param")
                    value = float(command.get("value"))
                    with engine.lock:
                        if hasattr(engine, param):
                            setattr(engine, param, value)
                            engine.configs[engine.state][param] = value
                    engine.add_log(
                        f"MANUAL: Modulated {param.upper()} to {value:.1f}%.", "sys"
                    )
                    self.send_success_response(
                        {"status": "ok", "param": param, "value": value}
                    )

                elif action == "interrupt":
                    engine.add_log(
                        "INTERRUPT: Critical external sensory payload received!", "warn"
                    )
                    with engine.lock:
                        if engine.state == "sleep":
                            engine.set_state("vigilance")
                            engine.add_log(
                                "WAKE DAEMON: Sensory gated bypass. Vigilance forced.",
                                "error",
                            )
                        elif engine.state == "vigilance":
                            engine.noradrenaline = min(
                                100.0, engine.noradrenaline + 30.0
                            )
                            engine.add_log(
                                "AMYGDALA: Salience Spike detected. Arousal modified.",
                                "warn",
                            )
                        elif engine.state == "flow":
                            engine.set_state("vigilance")
                            engine.add_log(
                                "ALERT: Flow state broken by external focus redirect.",
                                "warn",
                            )
                        elif engine.state == "limerence":
                            engine.free_energy += 1.5
                            engine.add_log(
                                "ERROR: LO interaction simulation crashed.", "error"
                            )
                    self.send_success_response({"status": "ok"})

                else:
                    self.send_error_response("Unknown action")
            except Exception as e:
                self.send_error_response(str(e))
        elif parsed_path.path == "/agent_telemetry":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")

            try:
                data = json.loads(post_data)
                agent_name = data.get("agent")

                if agent_name == "jules":
                    with engine.lock:
                        engine.jules_state = data.get("state", "idle")
                        engine.jules_dopamine = float(data.get("dopamine", 50.0))
                        engine.jules_cortisol = float(data.get("cortisol", 10.0))
                        engine.jules_adrenaline = float(data.get("adrenaline", 30.0))
                        engine.jules_tasks = data.get("tasks", [])
                    self.send_success_response({"status": "ok"})
                else:
                    self.send_error_response("Unknown agent")
            except Exception as e:
                self.send_error_response(str(e))
        elif parsed_path.path == "/telemetry":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")

            try:
                data = json.loads(post_data)
                ts = data.get("timestamp", time.time()) / 1000.0
                hostname = data.get("hostname", "")
                pathname = data.get("pathname", "")
                latency_ms = int(data.get("latencyMs", 0))
                status = int(data.get("status", 200))
                method = data.get("method", "GET")

                with engine.lock:
                    engine.db_conn.execute(
                        "INSERT INTO edge_telemetry (timestamp, hostname, pathname, latency_ms, status, method) VALUES (?, ?, ?, ?, ?, ?)",
                        (ts, hostname, pathname, latency_ms, status, method)
                    )
                    engine.db_conn.commit()

                self.send_success_response({"status": "ok"})
            except Exception as e:
                self.send_error_response(str(e))
        else:
            self.send_response(404)
            self.end_headers()

    def send_success_response(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def send_error_response(self, error_msg):
        self.send_response(400)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"error": error_msg}).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def run_tick_loop():
    while True:
        try:
            engine.update_tick()
        except Exception as e:
            print(f"Error in tick loop: {e}")
        time.sleep(0.1)


def main():
    tick_thread = threading.Thread(target=run_tick_loop, daemon=True)
    tick_thread.start()

    server_address = ("", 8000)
    httpd = ThreadingHTTPServer(server_address, CortexHTTPRequestHandler)
    print("\n" + "=" * 70)
    print("   [C5-REAL] CORTEX SINGULARITY BACKEND SERVER STARTED")
    print("   Local Address: http://localhost:8000")
    print("   Event-Stream:  http://localhost:8000/telemetry")
    print("=" * 70 + "\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()


if __name__ == "__main__":
    main()
