# DECLARACIÓN DE REALIDAD: C5-REAL (medición real de latencia TCP RTT contra hosts y servidores Soulseek activos)

import asyncio
import time
import socket
import argparse
import sys

# Default target list for connection testing
DEFAULT_TARGETS = [
    {"name": "Soulseek Main Server (Standard)", "host": "server.slsknet.org", "port": 2416},
    {"name": "Soulseek Main Server (Alternate)", "host": "server.slsknet.org", "port": 2242},
    {"name": "Local Loopback (Control)", "host": "127.0.0.1", "port": 60200}  # Optional local port
]

# TIP ALPHA Active Socket Pool Limiter to mitigate FD exhaustion
ACTIVE_SOCKET_SEMAPHORE = None

async def measure_rtt(host, port, name="Unknown Peer"):
    global ACTIVE_SOCKET_SEMAPHORE
    if ACTIVE_SOCKET_SEMAPHORE is None:
        ACTIVE_SOCKET_SEMAPHORE = asyncio.Semaphore(10)
        
    async with ACTIVE_SOCKET_SEMAPHORE:
        print(f"[*] Dispatching test probe to: {name} ({host}:{port})")
        
        t_start = time.perf_counter_ns()
        try:
            # Establish connection with short 3-second timeout
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), 
                timeout=3.0
            )
            t_connected = time.perf_counter_ns()
            
            # Connection RTT (TCP Handshake completion)
            connect_rtt_ms = (t_connected - t_start) / 1_000_000.0
            
            # Send a 4-byte empty payload (mock heartbeat/handshake)
            payload = b"\x00\x00\x00\x00"
            writer.write(payload)
            await writer.drain()
            
            t_payload_sent = time.perf_counter_ns()
            
            # Close connection gracefully
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
                
            return {
                "status": "SUCCESS",
                "rtt_ms": connect_rtt_ms,
                "notes": "TCP Handshake established & payload transmitted."
            }
            
        except asyncio.TimeoutError:
            return {
                "status": "TIMEOUT",
                "rtt_ms": None,
                "notes": "Connection attempt exceeded 3.0s timeout."
            }
        except ConnectionRefusedError:
            return {
                "status": "REFUSED",
                "rtt_ms": None,
                "notes": "Target port explicitly closed or peer off-line."
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "rtt_ms": None,
                "notes": f"Socket error: {str(e)}"
            }

async def main():
    parser = argparse.ArgumentParser(description="CORTEX Sovereign TCP RTT & Latency Forensic Meter")
    parser.add_argument("--host", help="Custom target host/IP")
    parser.add_argument("--port", type=int, help="Custom target port")
    parser.add_argument("--name", default="Custom Peer", help="Friendly name for custom target")
    args = parser.parse_args()

    targets = []
    if args.host and args.port:
        targets.append({"name": args.name, "host": args.host, "port": args.port})
    else:
        targets = DEFAULT_TARGETS

    print("="*80)
    print("  CORTEX HIGH-PRECISION TCP LATENCY FORENSIC METER v1.0")
    print("  Protocol: Raw TCP Socket Connect + 4-byte Mock Handshake")
    print("="*80)

    results = []
    for target in targets:
        res = await measure_rtt(target["host"], target["port"], target["name"])
        results.append({**target, **res})
        await asyncio.sleep(0.5)  # Cooldown between probes

    # Print gorgeous table report
    print("\n" + "="*80)
    print(f"{'TARGET NAME':35} | {'HOST:PORT':22} | {'STATUS':8} | {'RTT (ms)':9}")
    print("="*80)
    
    for r in results:
        rtt_str = f"{r['rtt_ms']:.2f} ms" if r["rtt_ms"] is not None else "N/A"
        print(f"{r['name'][:35]:35} | {f'{r['host']}:{r['port']}'[:22]:22} | {r['status']:8} | {rtt_str:9}")
        if r["notes"]:
            print(f"  └─ Notes: {r['notes']}")
            
    print("="*80)
    print("[*] Diagnostic complete. Alignment recommended for RTT < 150 ms.")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
