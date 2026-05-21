# DECLARACIÓN DE REALIDAD: C5-REAL (operación real de red peer-to-peer Soulseek, descargas y firmas hash reales)

import asyncio
import random
import string
import os
import sys
import argparse
import signal
import hashlib
import subprocess
import unicodedata
from aioslsk.client import SoulSeekClient
from aioslsk.settings import Settings, CredentialsSettings, NetworkSettings, ListeningSettings, PeerSettings, UpnpSettings
from aioslsk.network.network import PeerConnectMode
from aioslsk.naming import KeepDirectoryStrategy, DefaultNamingStrategy, NumberDuplicateStrategy
from aioslsk.transfer.state import TransferState

# Generar un usuario único
random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
username = f"moskv_down_{random_suffix}"
password = "cortex_password_2026"

# TIP ALPHA Latency Cache to optimize socket re-evaluations
LATENCY_CACHE = {}      # Maps peer_name -> (timestamp, lat_info_dict)
LATENCY_CACHE_TTL = 300 # Cache results for 300 seconds (5 minutes)
LATENCY_CACHE_LOCK = None

def normalize_text(text):
    return "".join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))

def compute_sha256(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def verify_flac_integrity(filepath):
    try:
        res = subprocess.run(['flac', '-t', filepath], capture_output=True, text=True)
        if res.returncode == 0:
            return True, "Valid FLAC file"
        else:
            return False, f"flac -t failed: {res.stderr.strip()}"
    except Exception as e:
        return False, f"Execution failed: {str(e)}"

# Pre-defined forensic high-fidelity target groups
TARGETS = {
    "afro_free": {
        "description": "Sandro Brugnolini, Luigi Malatesta - Afro Free (Library / Film Soundtrack)",
        "query": "Brugnolini Malatesta Afro Free",
        "peer_priority": ["xgcrp", "uovgf", "oqcjn"],
        "filename_keyword": "afro free",
        "extension": ".flac"
    },
    "fantabulous": {
        "description": "Sandro Brugnolini & Luigi Malatesta - Fantabulous LP (1967)",
        "query": "Brugnolini Malatesta Fantabulous",
        "peer_priority": ["uovgf", "xgcrp"],
        "filename_keyword": "fantabulous",
        "extension": ".flac"
    },
    "bach_abel_hume": {
        "description": "Anja Lechner - Bach, Abel, Hume (2024 ECM Viol Masters)",
        "query": "Lechner Bach Abel Hume",
        "peer_priority": ["lozzv"],
        "filename_keyword": "hume",
        "extension": ".flac"
    },
    "spirit_of_gambo": {
        "description": "Tobias Hume - The Spirit of Gambo (Viola da Gamba)",
        "query": "Tobias Hume Spirit Gambo",
        "peer_priority": ["ttkfr"],
        "filename_keyword": "hume",
        "extension": ".flac"
    }
}

async def main():
    global LATENCY_CACHE_LOCK
    LATENCY_CACHE_LOCK = asyncio.Lock()
    
    parser = argparse.ArgumentParser(description="CORTEX Sovereign Forensic Downloader for Malatesta & Hume Assets")
    parser.add_argument("--target", choices=list(TARGETS.keys()), default="afro_free", help="High-fidelity target asset key")
    parser.add_argument("--save-dir", default="$CORTEX_ROOT/Music/downloads", help="Directory where files will be stored")
    args = parser.parse_args()

    target_info = TARGETS[args.target]
    os.makedirs(args.save_dir, exist_ok=True)
    
    print("="*70)
    print("  CORTEX SOULSEEK SOVEREIGN FORENSIC DOWNLOADER v3.0")
    print(f"  Target Asset: {target_info['description']}")
    print(f"  Search Query: '{target_info['query']}'")
    print(f"  Destination:  {args.save_dir}")
    print("="*70)

    # TIP ALPHA Connection Optimizations: listening port and prioritizing FALLBACK direct connection
    listen_port = random.randint(60200, 60900)
    print(f"[*] Assigning local ports: {listen_port} & {listen_port + 1}")
    print("[*] Implementing TIP ALPHA direct connection / port retry bypass...")

    settings = Settings(
        credentials=CredentialsSettings(
            username=username,
            password=password
        ),
        network=NetworkSettings(
            listening=ListeningSettings(
                port=listen_port,
                obfuscated_port=listen_port + 1
            ),
            peer=PeerSettings(
                obfuscate=False,
                connect_mode=PeerConnectMode.FALLBACK  # Direct connection first to avoid indirect server bottlenecks
            ),
            upnp=UpnpSettings(
                enabled=True  # Attempt active NAT mapping to facilitate direct-connect handshakes
            )
        ),
        shares=__import__('aioslsk.settings', fromlist=['SharesSettings']).SharesSettings(download=args.save_dir)
    )
    
    client = SoulSeekClient(settings)
    client.shares.naming_strategies = [
        DefaultNamingStrategy(),
        KeepDirectoryStrategy(),
        NumberDuplicateStrategy()
    ]
    
    stop_event = asyncio.Event()

    def handle_shutdown():
        print("\n[!] Received shutdown signal. Terminating clean...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_shutdown)
        except NotImplementedError:
            pass

    try:
        print("[*] Initializing Soulseek network stack...")
        await client.start()
        print("[*] Logging in to master server...")
        await client.login()
        print(f"[+] Authenticated successfully as: {username}")
        
        print(f"[*] Dispatching query search: '{target_info['query']}'")
        search_request = await client.searches.search(target_info['query'])
        
        print("[*] Gathering peer metadata response (20 seconds)...")
        for i in range(20):
            if stop_event.is_set():
                break
            await asyncio.sleep(1)
            
        if stop_event.is_set():
            return

        user_files = {}
        for res in search_request.results:
            if hasattr(res, 'shared_items') and res.shared_items:
                for item in res.shared_items:
                    filename = item.filename
                    ext = filename.lower()
                    norm_filename = normalize_text(ext)
                    
                    # Verify target constraints: file extension and target keyword match
                    if ext.endswith(target_info['extension']) and target_info['filename_keyword'] in norm_filename:
                        if res.username not in user_files:
                            user_files[res.username] = {}
                        user_files[res.username][item.filename] = item
        
        if not user_files:
            print("[-] No matching high-fidelity assets found in search results.")
            return

        print(f"[+] Total peers matching target: {len(user_files)}")
        
        # Select best peer based on latency metrics
        selected_peer = None
        selected_items = []
        
        # Sort peers into check order: priority peers first, then fallback peers by file count descending
        candidate_peers = []
        for priority_peer in target_info['peer_priority']:
            if priority_peer in user_files:
                candidate_peers.append(priority_peer)
                
        remaining_peers = sorted(
            [p for p in user_files if p not in candidate_peers],
            key=lambda p: len(user_files[p]),
            reverse=True
        )
        candidate_peers.extend(remaining_peers)
        
        print("\n[*] Auditing candidate peers using TIP ALPHA latency filter (RTT < 300ms)...")
        from aioslsk.commands import GetPeerAddressCommand
        from medir_latencia import measure_rtt
        import time
        
        for peer in candidate_peers:
            async with LATENCY_CACHE_LOCK:
                now = time.time()
                use_cached = False
                lat_info = None
                
                # Check local cache first to avoid redundant socket probing
                if peer in LATENCY_CACHE:
                    cached_time, cached_info = LATENCY_CACHE[peer]
                    if now - cached_time < LATENCY_CACHE_TTL:
                        print(f"[*] Peer '{peer}' found in local latency cache (age: {now - cached_time:.1f}s).")
                        lat_info = cached_info
                        use_cached = True
                
                if not use_cached:
                    print(f"[*] Resolving connection address for peer '{peer}'...")
                    try:
                        # Get the peer address with a 5-second timeout to prevent stalling
                        ip, port, obfuscated_port = await asyncio.wait_for(
                            client.execute(GetPeerAddressCommand(peer), response=True),
                            timeout=5.0
                        )
                        print(f"[+] Address resolved for '{peer}': {ip}:{port}")
                        
                        if ip == "0.0.0.0" or port == 0:
                            print(f"[!] Peer '{peer}' is indirect (behind restricted NAT). Skipping direct latency probe.")
                            lat_info = {"status": "INDIRECT", "rtt_ms": None, "notes": "Indirect peer behind strict NAT."}
                        else:
                            # Measure RTT
                            lat_info = await measure_rtt(ip, port, peer)
                    except Exception as e:
                        print(f"[!] Failed to resolve address or measure latency for peer '{peer}': {e}")
                        lat_info = {"status": "ERROR", "rtt_ms": None, "notes": f"Error: {str(e)}"}
                    
                    # Store evaluated metrics in local cache
                    LATENCY_CACHE[peer] = (time.time(), lat_info)
            
            # Evaluate latency metrics against threshold
            if lat_info and lat_info["status"] == "SUCCESS":
                rtt = lat_info["rtt_ms"]
                print(f"[+] Peer '{peer}' RTT: {rtt:.2f} ms")
                if rtt <= 300.0:
                    selected_peer = peer
                    selected_items = list(user_files[peer].values())
                    print(f"[++] Peer '{peer}' ACCEPTED with latency {rtt:.2f} ms (< 300 ms threshold)!")
                    break
                else:
                    print(f"[!] Peer '{peer}' rejected: latency {rtt:.2f} ms exceeds 300 ms threshold.")
            elif lat_info:
                print(f"[!] Latency evaluation for '{peer}' skipped/failed: {lat_info.get('notes', 'No notes')}")
                
        if not selected_peer:
            print("[!] WARNING: No peers passed the strict direct-connection RTT check.")
            for peer in candidate_peers:
                selected_peer = peer
                selected_items = list(user_files[peer].values())
                print(f"[+] Emergency fallback: Selecting peer '{selected_peer}' without latency guarantee.")
                break
        
        if not selected_peer or not selected_items:
            print("[-] Error: Unable to determine a suitable peer for download.")
            return
            
        selected_items = sorted(selected_items, key=lambda x: x.filename)
        print(f"\n[+] Queueing downloads from peer '{selected_peer}':")
        for item in selected_items:
            print(f"    -> {item.filename} ({item.filesize / (1024*1024):.2f} MB)")
            
        transfers_map = {}
        for item in selected_items:
            print(f"[*] Requesting transfer stream for: {os.path.basename(item.filename)}")
            tf = await client.transfers.download(selected_peer, item.filename)
            transfers_map[item.filename] = {
                'transfer': tf,
                'filename': os.path.basename(item.filename),
                'retries': 0,
                'verified': False,
                'sha256': None,
                'integrity': None
            }
            
        print("\n[*] Starting forensic acquisition loop...")
        await asyncio.sleep(2)
        
        while not stop_event.is_set():
            all_complete = True
            print("-" * 60)
            
            for remote_path, info in transfers_map.items():
                tf = info['transfer']
                tf.take_progress_snapshot()
                state = tf.state.VALUE
                
                total_size = tf.filesize or 0
                bytes_tx = tf.bytes_transfered or 0
                pct = (bytes_tx / total_size * 100) if total_size > 0 else 0
                speed = tf.get_speed() or 0.0
                speed_kb = speed / 1024.0
                
                state_str = state.name if hasattr(state, 'name') else str(state)
                print(f"Asset: {info['filename'][:30]:30} | State: {state_str:12} | Progress: {pct:.1f}% ({bytes_tx/(1024*1024):.1f}/{total_size/(1024*1024):.1f} MB) | Speed: {speed_kb:.1f} KB/s")
                
                if state == TransferState.State.COMPLETE:
                    if not info['verified']:
                        local_path = tf.local_path
                        if local_path and os.path.exists(local_path):
                            print(f"    [+] Asset saved to: {local_path}")
                            print("    [*] Verifying asset integrity...")
                            sha = compute_sha256(local_path)
                            ok, msg = verify_flac_integrity(local_path)
                            info['verified'] = True
                            info['sha256'] = sha
                            
                            if ok:
                                info['integrity'] = "VERIFIED_VALID"
                                print(f"    [+] SHA-256: {sha}")
                                print(f"    [+] Integrity: VERIFIED_VALID")
                                
                                # Registrar en el cortex_treasury_ledger.jsonl
                                ledger_dir = os.path.expanduser("~/.gemini/antigravity/brain")
                                os.makedirs(ledger_dir, exist_ok=True)
                                ledger_path = os.path.join(ledger_dir, "cortex_treasury_ledger.jsonl")
                                import json
                                import time
                                entry = {
                                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                    "filename": os.path.basename(local_path),
                                    "filepath": local_path,
                                    "sha256": sha,
                                    "status": "VERIFIED_VALID",
                                    "size_bytes": os.path.getsize(local_path)
                                }
                                try:
                                    with open(ledger_path, "a") as f_ledger:
                                        f_ledger.write(json.dumps(entry) + "\n")
                                    print(f"    [+] Firma criptográfica registrada en ledger: {ledger_path}")
                                except Exception as le:
                                    print(f"    [!] Error writing ledger: {le}")
                            else:
                                info['integrity'] = f"CORRUPT: {msg}"
                                print(f"    [!] Integrity check FAILED: {msg}")
                                print(f"    [!] Purgando archivo corrupto de forma inmediata: {local_path}")
                                try:
                                    os.remove(local_path)
                                except Exception as re:
                                    print(f"    [!] Error al purgar archivo: {re}")
                        else:
                            all_complete = False
                elif state in (TransferState.State.FAILED, TransferState.State.ABORTED, TransferState.State.INCOMPLETE):
                    all_complete = False
                    info['retries'] += 1
                    if info['retries'] <= 10:
                        print(f"    [!] Transfer interrupted. Dispatching Tip Alpha direct retry {info['retries']}/10...")
                        try:
                            await client.transfers.queue(tf)
                        except Exception as e:
                            print(f"    [!] Retry dispatch failed: {e}")
                    else:
                        print(f"    [!] Maximum retry attempts exceeded for {info['filename']}.")
                else:
                    all_complete = False
                    
            if all_complete:
                print("\n[+] Forensic acquisition completed successfully.")
                break
                
            await asyncio.sleep(5)
            
        print("\n" + "="*70)
        print("  C5-REAL FORENSIC ACQUISITION REPORT")
        print("="*70)
        for remote_path, info in transfers_map.items():
            print(f"File: {info['filename']}")
            print(f"  Status: {info['transfer'].state.VALUE.name}")
            print(f"  Retries: {info['retries']}")
            print(f"  SHA-256: {info['sha256']}")
            print(f"  Integrity: {info['integrity']}")
            print("-" * 60)
            
    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        print("\n[*] Gracefully disconnecting Soulseek network stack...")
        await client.stop()
        print("[+] Off-line status achieved.")
        print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
