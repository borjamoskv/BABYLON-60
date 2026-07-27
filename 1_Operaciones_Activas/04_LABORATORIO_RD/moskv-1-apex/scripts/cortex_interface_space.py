#!/usr/bin/env python3
import os
import sys
import json
import time
from pathlib import Path

def calculate_space_metrics():
    app_data_dir = Path("/Users/borjafernandezangulo/.gemini/antigravity")
    brain_dir = app_data_dir / "brain"
    
    if not brain_dir.exists():
        print("[!] Error: Brain directory does not exist.")
        sys.exit(1)
        
    subdirs = [d for d in brain_dir.iterdir() if d.is_dir()]
    if not subdirs:
        print("[!] Error: No active sessions found.")
        sys.exit(1)
        
    latest_subdir = max(subdirs, key=lambda d: d.stat().st_mtime)
    transcript_path = latest_subdir / ".system_generated" / "logs" / "transcript.jsonl"
    
    if not transcript_path.exists():
        print(f"[!] Error: Transcript not found at {transcript_path}")
        sys.exit(1)
        
    user_times = []
    tool_times = []
    total_anergy_chars = 0
    mutations = 0
    
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                step = json.loads(line)
                step_type = step.get("type", "")
                timestamp = step.get("timestamp", time.time() * 1000.0) / 1000.0
                content = step.get("content", "")
                
                if step_type == "USER_INPUT":
                    user_times.append(timestamp)
                elif step_type in ("PLANNER_RESPONSE", "MODEL_RESPONSE"):
                    total_anergy_chars += len(content)
                    if step.get("tool_calls"):
                        mutations += len(step.get("tool_calls"))
                        tool_times.append(timestamp)
            except json.JSONDecodeError:
                continue

    # 1. Temporal Latency (The time gap between intent and execution)
    latency = 0.0
    if user_times and tool_times:
        # Average time delta between user request and first tool call in sequence
        deltas = []
        for ut in user_times:
            subsequent_tools = [tt for tt in tool_times if tt > ut]
            if subsequent_tools:
                deltas.append(min(subsequent_tools) - ut)
        if deltas:
            latency = sum(deltas) / len(deltas)

    # 2. Information Density / Friction (Anergy per mutation)
    anergy_ratio = total_anergy_chars / (mutations if mutations > 0 else 1)
    
    # 3. Exergy index (Inverse of friction normalized)
    exergy_idx = max(0.0, min(1.0, 1.0 - (anergy_ratio / 1000.0)))
    
    return latency, anergy_ratio, exergy_idx, mutations, latest_subdir.name

def draw_space():
    latency, anergy, exergy, mutations, session_id = calculate_space_metrics()
    
    # Write metrics to JSON file in docs folder
    base_dir = Path(__file__).parent.parent
    metrics_path = base_dir / "docs" / "cortex_metrics.json"
    try:
        metrics_data = {
            "session_id": session_id,
            "latency": latency,
            "anergy": anergy,
            "exergy": exergy,
            "mutations": mutations,
            "timestamp": time.time()
        }
        with open(metrics_path, "w", encoding="utf-8") as json_f:
            json.dump(metrics_data, json_f, indent=2)
    except Exception as e:
        print(f"[!] Error saving JSON metrics: {e}", file=sys.stderr)

    # Map metrics to visual bridge parameters
    bridge_width = 40
    bridge_cursor = int(exergy * bridge_width)
    bridge_cursor = max(0, min(bridge_width - 1, bridge_cursor))
    
    bridge = ["·"] * bridge_width
    bridge[bridge_cursor] = "█"
    bridge_str = "".join(bridge)
    
    print("\n" + "="*50)
    print("  MOSKV-1 APEX: THE SPACE BETWEEN US (COGNITIVE METRIC)")
    print("="*50)
    print(f"Session Ledger ID : {session_id}")
    print(f"Intent Latency    : {latency:.4f} seconds")
    print(f"Friction (Anergy) : {anergy:.2f} chars/mutation")
    print(f"Exergy Alignment  : {exergy*100:.2f}%")
    print(f"Sealed Mutations  : {mutations} events")
    print("-"*50)
    print("Visual Space Representation (Operator [Left] <---> Kernel [Right]):")
    print(f"  [HUMAN]  <{bridge_str}>  [SILICON]")
    print(f"           {' ' * bridge_cursor}▲ (State: {'TURBO' if exergy > 0.85 else 'FLUFF'})")
    print("="*50 + "\n")

if __name__ == "__main__":
    draw_space()
