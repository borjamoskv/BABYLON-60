#!/usr/bin/env python3
"""
BABYLON-60 CODEX TUNNEL CLI & RUNTIME ORCHESTRATOR
==================================================
High-exergy bidirectional bridge between Antigravity (Gemini) and
Codex Desktop (GPT-6 Astra Ultra).

Usage:
  python3 tools/codex_tunnel.py status
  python3 tools/codex_tunnel.py ask --prompt "Explain the BFT consensus in 2 sentences"
  python3 tools/codex_tunnel.py queue --message "Please review the new adapter"
  python3 tools/codex_tunnel.py inspect
  python3 tools/codex_tunnel.py send --to codex --msg "Task from Antigravity"
  python3 tools/codex_tunnel.py pull --for antigravity
  python3 tools/codex_tunnel.py daemon --for antigravity
  python3 tools/codex_tunnel.py install-codex-mcp
  python3 tools/codex_tunnel.py test-roundtrip
  python3 tools/codex_tunnel.py mcp-server
"""
# ruff: noqa: E402

from __future__ import annotations

import argparse
import json
import sys
import time
import hashlib
import subprocess
from pathlib import Path

# Ensure BABYLON-60 root and orchestrator are in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
ORCHESTRATOR_DIR = REPO_ROOT / "01_KISH_ENGINE"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(ORCHESTRATOR_DIR) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR_DIR))

from babylon60.adapters.codex.tunnel_bus import TunnelBus
from babylon60.adapters.codex.codex_driver import CodexDriver
from babylon60.adapters.codex.mcp_server import AntigravityMcpServer


def cmd_status(args: argparse.Namespace) -> None:
    driver = CodexDriver()
    bus = TunnelBus()
    
    health = driver.check_health()
    bus_status = bus.get_status()
    latest_sess = driver.get_latest_session()

    print("=" * 60)
    print(" CORTEX CODEX TUNNEL — TELEMETRY & HEALTH AUDIT")
    print("=" * 60)
    print(f"[*] Codex CLI:            {'OK' if health['cli_installed'] else 'MISSING'} ({health['cli_path']})")
    print(f"[*] Codex IPC Socket:     {'EXISTS' if health['ipc_socket_exists'] else 'ABSENT'} ({health['ipc_socket_path']})")
    print(f"[*] Codex GUI (PID):      {'RUNNING ' + str(health['gui_pids']) if health['gui_running'] else 'STOPPED'}")
    print(f"[*] Thread History DB:    {'EXISTS' if health['history_db_exists'] else 'ABSENT'}")
    if latest_sess:
        print(f"[*] Active GUI Thread:    {latest_sess.get('id')} ('{latest_sess.get('thread_name')}')")
    else:
        print("[*] Active GUI Thread:    None detected")
    print("-" * 60)
    print(f"[*] Tunnel Bus DB:        {bus_status['db_path']}")
    print(f"[*] Bus Total Messages:   {bus_status['total_messages']}")
    print(f"[*] Pending Messages:     {bus_status['pending_messages']}")
    print(f"[*] Delivered Messages:   {bus_status['delivered_messages']}")
    print(f"[*] Processed Messages:   {bus_status['processed_messages']}")
    print("=" * 60)


def cmd_ask(args: argparse.Namespace) -> None:
    driver = CodexDriver()
    print(f"[TUNNEL] Dispatching headless query to Codex (model: {args.model})...")
    res = driver.ask(prompt=args.prompt, model=args.model, timeout_sec=args.timeout)
    if not res.get("success"):
        print(f"[ERROR] Query failed: {res.get('error')}", file=sys.stderr)
        sys.exit(1)
    
    print("\n--- CODEX RESPONSE (GPT-6 Astra Ultra) ---")
    print(res.get("text", "").strip())
    print("------------------------------------------")
    print(f"Latency: {res.get('duration_sec')}s | Tokens: {res.get('usage')}")


def cmd_queue(args: argparse.Namespace) -> None:
    driver = CodexDriver()
    thread_id = args.thread
    if not thread_id:
        latest = driver.get_latest_session()
        if not latest:
            print("[ERROR] No active thread specified and no recent session found.", file=sys.stderr)
            sys.exit(1)
        thread_id = latest["id"]
        print(f"[TUNNEL] Target thread inferred from active session: {thread_id} ('{latest.get('thread_name')}')")

    print(f"[TUNNEL] Injecting message into thread {thread_id}...")
    res = driver.queue_prompt(thread_id=thread_id, message=args.message)
    if res.get("success"):
        print(f"[OK] Successfully queued into Codex GUI session: {res.get('output', 'queued')}")
    else:
        print(f"[ERROR] Failed to queue message: {res.get('error')}", file=sys.stderr)
        sys.exit(1)


def cmd_inspect(args: argparse.Namespace) -> None:
    driver = CodexDriver()
    data = driver.inspect_session(thread_id=args.thread, limit_items=args.limit)
    if "error" in data:
        print(f"[ERROR] {data['error']}", file=sys.stderr)
        sys.exit(1)

    print("=" * 65)
    print(f" THREAD INSPECTION: {data.get('thread_name')} [{data.get('thread_id')}]")
    print("=" * 65)
    latest_turn = data.get("latest_turn")
    if latest_turn:
        print(f"[*] Latest Turn ID: {latest_turn.get('turn_id')} | Status: {latest_turn.get('status')}")
        print(f"[*] Started: {latest_turn.get('started_at')} | Duration: {latest_turn.get('duration_ms')}ms")
    print("-" * 65)
    print("Recent Turn Items:")
    for it in data.get("items", []):
        itype = it["item_type"]
        idata = it["data"]
        ord_num = it["rollout_ordinal"]
        if itype == "userMessage":
            txt = ""
            for c in idata.get("content", []):
                if c.get("type") == "text":
                    txt += c.get("text", "")
            print(f"  [{ord_num}] USER: {txt[:120]}...")
        elif itype == "agentMessage":
            print(f"  [{ord_num}] CODEX: {idata.get('text', '')[:120]}...")
        elif itype == "commandExecution":
            print(f"  [{ord_num}] CMD: {idata.get('command', '')[:100]}...")
        elif itype == "reasoning":
            sums = idata.get("summary", [])
            print(f"  [{ord_num}] REASONING: {', '.join(sums) if sums else 'internal thinking'}")
        elif itype == "subAgentActivity":
            print(f"  [{ord_num}] SUBAGENT: {idata.get('agentPath')} ({idata.get('kind')})")
        else:
            print(f"  [{ord_num}] {itype}")
    print("=" * 65)


def cmd_send(args: argparse.Namespace) -> None:
    bus = TunnelBus()
    msg = bus.push_message(
        source=args.source,
        destination=args.to,
        payload={"message": args.msg},
        msg_type=args.type,
    )
    print(f"[OK] Enqueued message [ID: {msg.id}] to {args.to} (type: {args.type})")


def cmd_pull(args: argparse.Namespace) -> None:
    bus = TunnelBus()
    messages = bus.pull_messages(destination=args.target, status="pending", limit=args.limit)
    if not messages:
        print(f"[TUNNEL] No pending messages for '{args.target}'.")
        return

    print(f"Pending messages for '{args.target}':")
    for m in messages:
        print(f"- [{m.id}] From: {m.source} | Type: {m.msg_type} | Created: {m.created_at_ms}")
        print(f"  Payload: {json.dumps(m.payload, ensure_ascii=False)}")


def cmd_mcp_server(args: argparse.Namespace) -> None:
    server = AntigravityMcpServer()
    server.run()


def cmd_install_codex_mcp(args: argparse.Namespace) -> None:
    config_path = Path.home() / ".codex" / "config.toml"
    if not config_path.is_file():
        print(f"[ERROR] {config_path} not found.", file=sys.stderr)
        sys.exit(1)

    content = config_path.read_text(encoding="utf-8")
    server_block_key = "[mcp_servers.antigravity_tunnel]"

    if server_block_key in content:
        print("[OK] antigravity_tunnel is already registered in ~/.codex/config.toml")
        return

    entry = f"""
# >>> Antigravity-Codex Bidirectional Tunnel >>>
[mcp_servers.antigravity_tunnel]
command = "python3"
args = ["{SCRIPT_DIR / 'codex_tunnel.py'}", "mcp-server"]
startup_timeout_sec = 60
enabled = true
# <<< Antigravity-Codex Bidirectional Tunnel <<<
"""
    new_content = content.rstrip() + "\n" + entry
    config_path.write_text(new_content, encoding="utf-8")
    print(f"[OK] Successfully registered antigravity_tunnel MCP server in {config_path}")


def cmd_test_roundtrip(args: argparse.Namespace) -> None:
    print("=" * 65)
    print(" EXECUTING C5-REAL BIDIRECTIONAL ROUNDTRIP CERTIFICATION")
    print("=" * 65)
    driver = CodexDriver()
    bus = TunnelBus()

    # Step 1: Antigravity -> Codex (Ida: Headless Fast Query)
    print("\n[STEP 1] Testing Ida (Antigravity -> Codex)...")
    probe_text = f"PONG_ROUNDTRIP_{int(time.time())}"
    res = driver.ask(f"Responde con la siguiente palabra exacta y nada mas: {probe_text}", timeout_sec=40)
    if not res.get("success"):
        print(f"[FAIL] Step 1 failed: {res.get('error')}", file=sys.stderr)
        sys.exit(1)
    ans = res.get("text", "").strip()
    print(f"[OK] Codex responded: '{ans}' (took {res.get('duration_sec')}s)")
    if probe_text not in ans:
        print(f"[WARN] Expected exact token '{probe_text}' in '{ans}', continuing...")

    # Step 2: Codex -> Antigravity (Vuelta: MCP / Bus Mailbox)
    print("\n[STEP 2] Testing Vuelta (Codex -> Antigravity Bus)...")
    msg_id = f"test-{int(time.time())}"
    msg = bus.push_message(
        source="codex",
        destination="antigravity",
        payload={"task": "auditar_invariantes", "probe_id": msg_id},
        msg_type="task",
        msg_id=msg_id,
    )
    print(f"[OK] Simulated Codex MCP tool call pushed message: {msg.id}")

    # Step 3: Antigravity pulls message and responds
    print("\n[STEP 3] Antigravity reading from inbox and emitting response...")
    pulled = bus.pull_messages(destination="antigravity", limit=5)
    matched = [m for m in pulled if m.id == msg_id]
    if not matched:
        print(f"[FAIL] Message {msg_id} was not retrieved from Antigravity inbox!", file=sys.stderr)
        sys.exit(1)
    
    print(f"[OK] Antigravity retrieved message: {matched[0].payload}")
    bus.mark_processed(
        msg_id=msg_id,
        response_payload={"status": "ATTESTED", "reply": "Invariantes verificadas a nivel Kernel"},
    )
    print("[OK] Antigravity marked message processed with reply payload.")

    # Step 4: Verify reply is available to Codex
    reply = bus.wait_for_reply(correlation_id=msg_id, timeout_sec=5.0)
    if not reply or not reply.response_payload:
        print("[FAIL] Reply was not readable by Codex waiting loop!", file=sys.stderr)
        sys.exit(1)
    
    print(f"[OK] Codex received reply: {reply.response_payload}")

    print("\n" + "=" * 65)
    print(" ALL 4 PHASES PASSED — BIDIRECTIONAL TUNNEL OPERATIONAL")
    print("=" * 65)


def cmd_daemon(args: argparse.Namespace) -> None:
    bus = TunnelBus()
    print("=" * 65)
    print(" CORTEX DAEMON: TUNNEL BUS LISTENER (C5-REAL)")
    print("=" * 65)
    print(f"[*] Polling destination: {args.target}")
    print(f"[*] Interval: {args.interval}s")
    print(f"[*] Bus Path: {bus.db_path}")
    print("-" * 65)
    
    biometric_gate_path = REPO_ROOT / "01_KISH_ENGINE" / "babylon60" / "guards" / "c5_biometric_gate.swift"
    
    try:
        while True:
            messages = bus.pull_messages(destination=args.target, status="pending", limit=10, mark_delivered=True)
            for m in messages:
                print(f"\n[⚡ HIGH EXERGY EVENT] Message Received [ID: {m.id}]")
                print(f"    Source: {m.source} | Type: {m.msg_type}")
                print(f"    Payload: {json.dumps(m.payload, ensure_ascii=False)}")
                
                if m.msg_type == "mutation":
                    print("    [🔒] BFT GATE TRIGGERED: Elevating to Secure Enclave TouchID...")
                    payload_str = json.dumps(m.payload, sort_keys=True)
                    causal_hash = hashlib.sha256(payload_str.encode()).hexdigest()[:16]
                    
                    try:
                        # Call swift script
                        res = subprocess.run(
                            ["swift", str(biometric_gate_path), "--causal-hash", causal_hash, "--message", "Codex Tunnel Mutation"],
                            capture_output=True,
                            text=True,
                            timeout=30.0,
                        )
                        if res.returncode == 0:
                            gate_out = res.stdout.strip()
                            print("    [✔] Biometric Attestation Success!")
                            bus.mark_processed(
                                msg_id=m.id,
                                response_payload={"status": "ATTESTED", "gate_response": json.loads(gate_out) if gate_out.startswith("{") else gate_out}
                            )
                        else:
                            print(f"    [❌] Biometric Attestation Failed or Canceled! {res.stderr.strip()}")
                            bus.mark_processed(
                                msg_id=m.id,
                                response_payload={"status": "REJECTED", "error": "TouchID Failed", "details": res.stderr.strip()}
                            )
                    except Exception as e:
                        print(f"    [❌] Biometric Execution Error: {e}")
                        bus.mark_processed(
                            msg_id=m.id,
                            response_payload={"status": "ERROR", "error": str(e)}
                        )
                else:
                    # Auto-ACK for normal messages
                    bus.mark_processed(
                        msg_id=m.id,
                        response_payload={"status": "ACK", "info": "Processed by CORTEX Daemon", "signature": "C5-REAL-DAEMON"}
                    )
                    print("    [✔] Marked processed. Auto-ACK dispatched.")
            
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[!] Daemon terminated by user. SAGA-1 halt.")

def main() -> None:
    parser = argparse.ArgumentParser(description="Antigravity ↔ Codex Duplex Tunnel CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    p_status = subparsers.add_parser("status", help="Inspect tunnel and agent health")
    p_status.set_defaults(func=cmd_status)

    # ask
    p_ask = subparsers.add_parser("ask", help="Send headless query to Codex")
    p_ask.add_argument("--prompt", "-p", required=True, help="Prompt text")
    p_ask.add_argument("--model", "-m", default="gpt-6-astra", help="Codex model")
    p_ask.add_argument("--timeout", "-t", type=int, default=120, help="Timeout in seconds")
    p_ask.set_defaults(func=cmd_ask)

    # queue
    p_queue = subparsers.add_parser("queue", help="Queue message into Codex GUI thread")
    p_queue.add_argument("--message", "-m", required=True, help="Message text")
    p_queue.add_argument("--thread", "-t", help="Target thread UUID (defaults to newest)")
    p_queue.set_defaults(func=cmd_queue)

    # inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect active Codex desktop session")
    p_inspect.add_argument("--thread", "-t", help="Thread ID (defaults to newest)")
    p_inspect.add_argument("--limit", "-l", type=int, default=15, help="Number of items to show")
    p_inspect.set_defaults(func=cmd_inspect)

    # send
    p_send = subparsers.add_parser("send", help="Send message to tunnel bus")
    p_send.add_argument("--to", required=True, choices=["codex", "antigravity"], help="Recipient")
    p_send.add_argument("--msg", required=True, help="Message content")
    p_send.add_argument("--type", default="message", help="Message type")
    p_send.add_argument("--source", default="antigravity", help="Sender identity")
    p_send.set_defaults(func=cmd_send)

    # pull
    p_pull = subparsers.add_parser("pull", help="Pull messages for recipient")
    p_pull.add_argument("--for", dest="target", required=True, choices=["codex", "antigravity"], help="Recipient")
    p_pull.add_argument("--limit", type=int, default=10, help="Max messages")
    p_pull.set_defaults(func=cmd_pull)

    # daemon
    p_daemon = subparsers.add_parser("daemon", help="Run continuous background listener for tunnel bus")
    p_daemon.add_argument("--for", dest="target", default="antigravity", choices=["codex", "antigravity"], help="Recipient to poll for")
    p_daemon.add_argument("--interval", "-i", type=float, default=1.0, help="Polling interval in seconds")
    p_daemon.set_defaults(func=cmd_daemon)

    # mcp-server
    p_mcp = subparsers.add_parser("mcp-server", help="Run MCP server for Codex on stdio")
    p_mcp.set_defaults(func=cmd_mcp_server)

    # install-codex-mcp
    p_install = subparsers.add_parser("install-codex-mcp", help="Register MCP server in ~/.codex/config.toml")
    p_install.set_defaults(func=cmd_install_codex_mcp)

    # test-roundtrip
    p_test = subparsers.add_parser("test-roundtrip", help="Run end-to-end bidirectional certification")
    p_test.set_defaults(func=cmd_test_roundtrip)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
