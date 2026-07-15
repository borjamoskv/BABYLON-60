import os
import time
import threading
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Tuple

DB_PATH = Path("/Users/borjafernandezangulo/30_BABYLON-60/telemetry.db")
TEMP_SWAP_FILE = Path("scratch/swap_buffer.bin")

class LayerSwapSimulator:
    def __init__(self, num_layers: int = 80, layer_size_mb: float = 500.0) -> None:
        self.num_layers = num_layers
        self.layer_size_mb = layer_size_mb
        self.calibrated_speed_mb_per_sec = 1000.0  # Fallback: 1 GB/s
        self.lock = threading.Lock()
        self.prefetch_thread: threading.Thread | None = None
        self.prefetch_buffer: bytes | None = None
        self.prefetch_layer_id: int | None = None

    def calibrate_disk_speed(self) -> float:
        """Calibrates local disk read speed using a temporary 20MB payload."""
        os.makedirs(TEMP_SWAP_FILE.parent, exist_ok=True)
        size_bytes = 20 * 1024 * 1024  # 20 MB
        payload = b"0" * size_bytes

        # Write
        with open(TEMP_SWAP_FILE, "wb") as f:
            f.write(payload)

        # Measure read
        start = time.perf_counter()
        with open(TEMP_SWAP_FILE, "rb") as f:
            _ = f.read()
        end = time.perf_counter()

        # Clean up
        if TEMP_SWAP_FILE.exists():
            os.remove(TEMP_SWAP_FILE)

        duration = end - start
        if duration > 0:
            self.calibrated_speed_mb_per_sec = 20.0 / duration
        else:
            self.calibrated_speed_mb_per_sec = 1000.0

        return self.calibrated_speed_mb_per_sec

    def _simulate_load(self, layer_id: int) -> float:
        """Simulates loading a single layer's weights. Returns latency in ms."""
        # Calculate simulated transfer time
        transfer_time = (self.layer_size_mb / self.calibrated_speed_mb_per_sec)
        time.sleep(transfer_time)
        return transfer_time * 1000.0

    def _simulate_compute(self) -> float:
        """Simulates GPU attention/MLP layer computation time. Returns latency in ms."""
        compute_time = 0.005  # 5 ms standard ALU delay
        time.sleep(compute_time)
        return compute_time * 1000.0

    def run_sequential_benchmark(self) -> Tuple[float, Dict[int, float]]:
        """Simulates sequential layer execution without prefetching (blocking loading)."""
        latencies = {}
        total_time = 0.0

        for layer in range(self.num_layers):
            # Load layer weights
            load_lat = self._simulate_load(layer)
            # Compute layer
            comp_lat = self._simulate_compute()
            
            layer_lat = load_lat + comp_lat
            latencies[layer] = layer_lat
            total_time += layer_lat

        return total_time, latencies

    def _async_prefetch_worker(self, layer_id: int) -> None:
        """Background thread worker to prefetch weights for the next layer."""
        self._simulate_load(layer_id)
        with self.lock:
            self.prefetch_buffer = b"loaded"
            self.prefetch_layer_id = layer_id

    def start_prefetch(self, next_layer_id: int) -> None:
        """Starts asynchronous load of the next layer weights."""
        with self.lock:
            self.prefetch_buffer = None
            self.prefetch_layer_id = None
        self.prefetch_thread = threading.Thread(
            target=self._async_prefetch_worker, 
            args=(next_layer_id,), 
            daemon=True
        )
        self.prefetch_thread.start()

    def run_pipelined_benchmark(self) -> Tuple[float, Dict[int, float]]:
        """Simulates pipelined layer execution leveraging asynchronous prefetching."""
        latencies = {}
        total_time = 0.0

        # Prime the pipeline: load layer 0
        load_lat_0 = self._simulate_load(0)
        
        for layer in range(self.num_layers):
            # Compute current layer
            start_compute = time.perf_counter()
            
            # Start prefetching the next layer asynchronously
            next_layer = layer + 1
            if next_layer < self.num_layers:
                self.start_prefetch(next_layer)
                
            self._simulate_compute()
            end_compute = time.perf_counter()
            compute_elapsed_ms = (end_compute - start_compute) * 1000.0

            # Wait for next layer load to finish (if not already completed)
            load_elapsed_ms = 0.0
            if next_layer < self.num_layers:
                start_wait = time.perf_counter()
                if self.prefetch_thread:
                    self.prefetch_thread.join()
                end_wait = time.perf_counter()
                load_elapsed_ms = (end_wait - start_wait) * 1000.0
                
            # If it was layer 0, we add the initial load latency
            if layer == 0:
                layer_lat = load_lat_0 + compute_elapsed_ms
            else:
                layer_lat = compute_elapsed_ms + load_elapsed_ms
                
            latencies[layer] = layer_lat
            total_time += layer_lat

        return total_time, latencies

def record_telemetry(seq_time: float, pipe_time: float, num_layers: int, layer_size_mb: float, speed: float) -> None:
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS layer_swap_telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            num_layers INTEGER NOT NULL,
            layer_size_mb REAL NOT NULL,
            disk_speed_mb_s REAL NOT NULL,
            seq_time_ms REAL NOT NULL,
            pipe_time_ms REAL NOT NULL,
            exergy_saved_ms REAL NOT NULL,
            efficiency_gain REAL NOT NULL
        )
    """)
    
    saved = seq_time - pipe_time
    gain = (saved / seq_time) * 100.0 if seq_time > 0 else 0.0
    
    conn.execute(
        """
        INSERT INTO layer_swap_telemetry 
        (timestamp, num_layers, layer_size_mb, disk_speed_mb_s, seq_time_ms, pipe_time_ms, exergy_saved_ms, efficiency_gain) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (datetime.now(timezone.utc).isoformat(), num_layers, layer_size_mb, speed, seq_time, pipe_time, saved, gain)
    )
    conn.commit()
    conn.close()

def main() -> None:
    print("🔍 [DEBUG / TRACE / PARSING] Initializing Layer Swap Simulator (AirLLM model)...")
    sim = LayerSwapSimulator(num_layers=32, layer_size_mb=100.0) # Downscaled for safe test latency
    
    print("🔍 [DEBUG / TRACE / PARSING] Calibrating disk speed...")
    speed = sim.calibrate_disk_speed()
    print(f"🟢 [STATUS_OK / EXERGY] Calibrated Disk Speed: {speed:.2f} MB/s")

    print("🔍 [DEBUG / TRACE / PARSING] Running sequential execution simulation...")
    seq_time, _ = sim.run_sequential_benchmark()
    print(f"🟢 [STATUS_OK / EXERGY] Sequential execution completed in {seq_time:.2f}ms")

    print("🔍 [DEBUG / TRACE / PARSING] Running pipelined execution (prefetching) simulation...")
    pipe_time, _ = sim.run_pipelined_benchmark()
    print(f"🟢 [STATUS_OK / EXERGY] Pipelined execution completed in {pipe_time:.2f}ms")

    saved = seq_time - pipe_time
    gain = (saved / seq_time) * 100.0 if seq_time > 0 else 0.0
    print(f"🟢 [STATUS_OK / EXERGY] Pipelining saved {saved:.2f}ms ({gain:.2f}% efficiency gain)")

    record_telemetry(seq_time, pipe_time, sim.num_layers, sim.layer_size_mb, speed)
    print("🟢 [STATUS_OK / EXERGY] Simulation data recorded in telemetry.db")

if __name__ == "__main__":
    main()
