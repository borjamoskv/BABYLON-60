import asyncio
import subprocess
import time
import os
import signal

REQUESTS = 20000
CONCURRENCY = 200

async def raw_http_get(sem, host, port):
    async with sem:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            req = b"GET / HTTP/1.1\r\nHost: localhost:8000\r\nConnection: close\r\n\r\n"
            writer.write(req)
            await writer.drain()
            await reader.read(1024)
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

async def stress_test():
    print(f"[*] [C5-REAL] Iniciando asedio termodinámico RAW TCP: {REQUESTS} iteraciones (N={CONCURRENCY}).")
    sem = asyncio.Semaphore(CONCURRENCY)
    tasks = []
    for _ in range(REQUESTS):
        tasks.append(raw_http_get(sem, '127.0.0.1', 8000))
    
    start_time = time.time()
    responses = await asyncio.gather(*tasks)
    end_time = time.time()
    
    success = sum(1 for r in responses if r)
    failed = len(responses) - success
    print(f"[*] Asedio completado en {end_time - start_time:.2f}s")
    print(f"[*] Éxitos: {success}, Fallos: {failed}")

def main():
    import resource
    resource.setrlimit(resource.RLIMIT_CORE, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
    
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
    
    time.sleep(3) # Wait for ignition
    
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
