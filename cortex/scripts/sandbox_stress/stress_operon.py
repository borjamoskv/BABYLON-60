import asyncio
import subprocess
import time
import os
import signal

REQUESTS = 20000
CONCURRENCY = 200

async def raw_http_get(sem, host, port):
    async with sem:
        t_start = time.perf_counter()
        try:
            reader, writer = await asyncio.open_connection(host, port)
            req = b"GET / HTTP/1.1\r\nHost: localhost:8000\r\nConnection: close\r\n\r\n"
            writer.write(req)
            await writer.drain()
            await reader.read(1024)
            writer.close()
            await writer.wait_closed()
            t_end = time.perf_counter()
            return True, (t_end - t_start) * 1000.0
        except Exception:
            return False, 0.0

async def check_port_ready(host, port, timeout=5.0):
    """Wait dynamically for the port to start accepting connections."""
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            await asyncio.sleep(0.05)
    return False

def clean_orphan_processes(port):
    """Locate and terminate orphan processes running on target port to prevent EADDRINUSE."""
    try:
        output = subprocess.check_output(["lsof", "-t", f"-i:{port}"]).decode().strip()
        if output:
            for pid_str in output.split("\n"):
                pid = int(pid_str)
                print(f"[*] Releasing port {port} (Terminating orphan PID {pid})...")
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.2)
    except Exception:
        pass

async def stress_test():
    import statistics
    print(f"[*] [C5-REAL] Iniciando asedio termodinámico RAW TCP: {REQUESTS} iteraciones (N={CONCURRENCY}).")
    sem = asyncio.Semaphore(CONCURRENCY)
    tasks = []
    for _ in range(REQUESTS):
        tasks.append(raw_http_get(sem, '127.0.0.1', 8000))
    
    start_time = time.monotonic()
    results = await asyncio.gather(*tasks)
    end_time = time.monotonic()
    
    successes = [r[1] for r in results if r[0]]
    failed = len(results) - len(successes)
    total_time = end_time - start_time
    
    print(f"[*] Asedio completado em {total_time:.2f}s")
    print(f"[*] Éxitos: {len(successes)}, Fallos: {failed}")
    
    if successes:
        avg_lat = statistics.mean(successes)
        p50 = statistics.median(successes)
        sorted_latencies = sorted(successes)
        p90 = sorted_latencies[int(len(successes) * 0.90)]
        p95 = sorted_latencies[int(len(successes) * 0.95)]
        p99 = sorted_latencies[int(len(successes) * 0.99)]
        min_lat = min(successes)
        max_lat = max(successes)
        rps = len(results) / total_time
        
        print("\n=== LATENCY COMPARATIVE METRICS ===")
        print(f"Throughput:       {rps:.2f} req/s")
        print(f"Min Latency:      {min_lat:.2f} ms")
        print(f"Avg Latency:      {avg_lat:.2f} ms")
        print(f"p50 (Median):     {p50:.2f} ms")
        print(f"p90 Latency:      {p90:.2f} ms")
        print(f"p95 Latency:      {p95:.2f} ms")
        print(f"p99 Latency:      {p99:.2f} ms")
        print(f"Max Latency:      {max_lat:.2f} ms")
        print("===================================\n")
    else:
        print("[!] Warning: Zero successful requests recorded.")

def main():
    import resource
    resource.setrlimit(resource.RLIMIT_CORE, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
    
    # Pre-clean the target port to avoid bind collisions
    clean_orphan_processes(8000)
    
    print("[*] Levantando demonio Operon en Sandbox...")
    env = os.environ.copy()
    env["NODE_OPTIONS"] = "--heapsnapshot-signal=SIGUSR2 --trace-gc"
    env["BUN_GARBAGE_COLLECTOR"] = "1"
    
    daemon = subprocess.Popen(
        ["./operon_core", "serve", "--here"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Dynamic ignition check instead of static sleep
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        ready = loop.run_until_complete(check_port_ready('127.0.0.1', 8000, timeout=5.0))
    finally:
        loop.close()
        
    if not ready:
        print("[!] Error: Daemon operon_core did not bind port 8000 in time. Aborting.")
        daemon.kill()
        return
        
    try:
        asyncio.run(stress_test())
    except KeyboardInterrupt:
        pass
    
    print(f"[*] Forzando volcado de memoria (SIGABRT) en PID {daemon.pid}...")
    daemon.send_signal(signal.SIGABRT)
    time.sleep(2)
    
    print("[*] Terminando...")
    daemon.kill()

if __name__ == "__main__":
    main()
