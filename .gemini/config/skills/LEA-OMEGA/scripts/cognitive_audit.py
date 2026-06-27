#!/usr/bin/env python3
import sys
import os
import json
import re
import sqlite3

def compute_metrics(transcript_path):
    if not os.path.exists(transcript_path):
        return {
            "error": f"Transcript not found at path: {transcript_path}"
        }

    steps = []
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    steps.append(json.loads(line))
    except Exception as e:
        return {"error": f"Failed to parse transcript: {str(e)}"}

    total_steps = len(steps)
    user_steps = [s for s in steps if s.get("source") == "USER_EXPLICIT"]
    model_steps = [s for s in steps if s.get("source") == "MODEL"]
    
    total_model_chars = 0
    signal_chars = 0
    tool_calls_count = 0
    commands_executed = []
    
    # Analyze model steps for signal vs narrative density
    for s in model_steps:
        content = s.get("content", "") or ""
        
        total_model_chars += len(content)
        
        # Extract markdown code blocks (fenced blocks with ``` )
        # Using a regex to find all matches of blocks
        code_blocks = re.findall(r'```(?:[a-zA-Z0-9_+-]+)?\n(.*?)\n```', content, re.DOTALL)
        for block in code_blocks:
            signal_chars += len(block)
            
        # Extract inline code backticks as minor signal
        inline_code = re.findall(r'`[^`\n]+`', content)
        for inline in inline_code:
            signal_chars += len(inline)

        # Count tool calls
        if "tool_calls" in s and s["tool_calls"]:
            tool_calls_count += len(s["tool_calls"])
            for tc in s["tool_calls"]:
                if tc.get("name") == "run_command":
                    args = tc.get("args", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except:
                            pass
                    cmd = args.get("CommandLine") if isinstance(args, dict) else None
                    if cmd:
                        commands_executed.append(cmd)

    # Detect loops in commands (identical command run sequentially or repeatedly)
    repeated_commands = {}
    last_cmd = None
    sequential_loops = 0
    for cmd in commands_executed:
        repeated_commands[cmd] = repeated_commands.get(cmd, 0) + 1
        if last_cmd == cmd:
            sequential_loops += 1
        last_cmd = cmd

    loop_density = sum(count for cmd, count in repeated_commands.items() if count > 1)
    
    exergy_ratio = 0.0
    if total_model_chars > 0:
        exergy_ratio = round(signal_chars / total_model_chars, 4)

    # CORTEX Ledger integration
    ledger_metrics = {
        "ledger_path": None,
        "total_checkpoints": 0,
        "total_episodic_failures": 0,
        "failures_in_current_conv": 0
    }
    
    # Standard path for CORTEX ledger
    cortex_db_path = os.path.expanduser("~/.gemini/antigravity/scratch/cortex-c5-ledger/cortex.db")
    if os.path.exists(cortex_db_path):
        ledger_metrics["ledger_path"] = cortex_db_path
        try:
            # C5-REAL Ouroboros Rule 10 Enforcement: Hardened Sovereign Connection
            with sqlite3.connect(cortex_db_path, timeout=5.0) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA busy_timeout=5000")
                cursor = conn.cursor()
                
                # Count total checkpoints
                cursor.execute("SELECT COUNT(*) FROM vesicular_checkpoints")
                row = cursor.fetchone()
                if row:
                    ledger_metrics["total_checkpoints"] = row[0]
                    
                # Count total episodic failures
                cursor.execute("SELECT COUNT(*) FROM episodic_failures")
                row = cursor.fetchone()
                if row:
                    ledger_metrics["total_episodic_failures"] = row[0]
                    
                # Check for failures matching current conversation (if any mapping exists)
                # Usually intent might store some reference to commands or conversation
                conv_id = os.path.basename(os.path.dirname(os.path.dirname(transcript_path)))
                cursor.execute("SELECT COUNT(*) FROM episodic_failures WHERE intent LIKE ?", (f"%{conv_id}%",))
                row = cursor.fetchone()
                if row:
                    ledger_metrics["failures_in_current_conv"] = row[0]
                    
        except Exception as e:
            ledger_metrics["error"] = f"Failed to read CORTEX ledger: {str(e)}"
    else:
        ledger_metrics["error"] = "CORTEX ledger not found at expected path."

    return {
        "metadata": {
            "conversation_id": os.path.basename(os.path.dirname(os.path.dirname(transcript_path))),
            "total_steps": total_steps,
            "user_inputs": len(user_steps),
            "model_responses": len(model_steps)
        },
        "exergy_metrics": {
            "total_response_chars": total_model_chars,
            "structured_signal_chars": signal_chars,
            "exergy_ratio": exergy_ratio,
            "anergy_ratio": round(1.0 - exergy_ratio, 4) if total_model_chars > 0 else 1.0
        },
        "tool_metrics": {
            "total_tool_calls": tool_calls_count,
            "distinct_commands_run": len(set(commands_executed)),
            "total_commands_run": len(commands_executed)
        },
        "loop_detection": {
            "sequential_repeats": sequential_loops,
            "duplicate_command_count": loop_density,
            "potential_loops_detected": [cmd for cmd, count in repeated_commands.items() if count > 2]
        },
        "cortex_ledger": ledger_metrics
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 cognitive_audit.py <path_to_transcript_or_conv_dir>")
        sys.exit(1)

    target_path = sys.argv[1]
    if os.path.isdir(target_path):
        # Resolve to transcript.jsonl if a directory was passed
        transcript_path = os.path.join(target_path, ".system_generated", "logs", "transcript.jsonl")
    else:
        transcript_path = target_path

    metrics = compute_metrics(transcript_path)
    
    # Output metrics as formatted JSON
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()
