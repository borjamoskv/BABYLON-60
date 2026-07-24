#!/usr/bin/env python3
"""
MOSKV-1 APEX: 100-AGENT SWARM CONVERSATION AUDITOR (MAX EXERGY)
Scans all conversation sessions in ~/.gemini/antigravity/brain/
Performs multi-threaded analysis on transcript logs without git crystallization.
[CORTEX-TAINT:borjamoskv:swarm_conversation_audit:2026-07-24]
"""

import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any

BRAIN_DIR = Path.home() / ".gemini" / "antigravity" / "brain"

def audit_single_session(session_dir: Path) -> Dict[str, Any]:
    session_id = session_dir.name
    transcript_path = session_dir / ".system_generated" / "logs" / "transcript.jsonl"
    
    if not transcript_path.exists():
        # Check root of session_dir
        alt_path = session_dir / "transcript.jsonl"
        if alt_path.exists():
            transcript_path = alt_path
        else:
            return {"session_id": session_id, "status": "NO_TRANSCRIPT"}

    user_messages = []
    model_turns = 0
    tool_calls_count = 0
    invariants_found = set()
    c5_assertions = 0
    code_edits = 0
    errors_encountered = 0
    unfulfilled_goals = []
    first_prompt = "N/A"
    
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue
                
                step_type = data.get("type")
                content = str(data.get("content", ""))
                
                # Check user input
                if step_type == "USER_INPUT" or data.get("source") == "USER_EXPLICIT":
                    prompt_text = content.strip()
                    if prompt_text:
                        user_messages.append(prompt_text)
                        if first_prompt == "N/A":
                            first_prompt = prompt_text[:120].replace("\n", " ")
                            
                # Check model turns & tool calls
                if step_type == "PLANNER_RESPONSE" or data.get("source") == "MODEL":
                    model_turns += 1
                    t_calls = data.get("tool_calls", [])
                    tool_calls_count += len(t_calls)
                    
                    for tc in t_calls:
                        t_name = tc.get("name", "") if isinstance(tc, dict) else str(tc)
                        if t_name in ("replace_file_content", "multi_replace_file_content", "write_to_file"):
                            code_edits += 1

                # Scan for C5 assertions and invariants
                if "C5-REAL" in content:
                    c5_assertions += 1
                
                # Detect invariants like INV_C5_*, INV_BFT_*, Ω*
                inv_matches = re.findall(r'(INV_[A-Z0-9_]+|Ω\d+)', content)
                for inv in inv_matches:
                    invariants_found.add(inv)
                
                if "ERROR" in content or "failed with exit code" in content:
                    errors_encountered += 1

                if "/goal" in content:
                    unfulfilled_goals.append("/goal directive present")

    except Exception as e:
        return {"session_id": session_id, "status": f"ERROR: {str(e)}"}

    # Exergy calculation (Density of actionable tool calls + C5 invariants per turn)
    exergy_score = min(1000.0, round((code_edits * 15.0 + tool_calls_count * 5.0 + c5_assertions * 10.0 + len(invariants_found) * 20.0) / max(1, model_turns) * 10, 2))
    if exergy_score == 0 and len(user_messages) > 0:
        exergy_score = 420.0  # Base line reading session

    return {
        "session_id": session_id,
        "status": "OK",
        "first_prompt": first_prompt,
        "user_prompts_count": len(user_messages),
        "model_turns": model_turns,
        "tool_calls": tool_calls_count,
        "code_edits": code_edits,
        "c5_assertions": c5_assertions,
        "invariants_count": len(invariants_found),
        "invariants": list(invariants_found)[:10],
        "errors_count": errors_encountered,
        "exergy_score": exergy_score,
        "has_goal": len(unfulfilled_goals) > 0
    }

def main():
    print("🚀 [SWARM 100-AGENT] Bootstrapping Parallel Audit across all Brain Conversations...")
    session_dirs = [d for d in BRAIN_DIR.iterdir() if d.is_dir() and d.name != "tempmediaStorage"]
    print(f"[*] Total target conversation sessions: {len(session_dirs)}")

    results = []
    # Execute with 100 workers (ThreadPool/ProcessPool Turbo Swarm)
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = {executor.submit(audit_single_session, sdir): sdir for sdir in session_dirs}
        for future in futures:
            try:
                res = future.result()
                results.append(res)
            except Exception as exc:
                results.append({"session_id": futures[future].name, "status": f"FAILED: {exc}"})

    valid_results = [r for r in results if r.get("status") == "OK"]
    valid_results.sort(key=lambda x: x.get("exergy_score", 0), reverse=True)

    total_prompts = sum(r.get("user_prompts_count", 0) for r in valid_results)
    total_turns = sum(r.get("model_turns", 0) for r in valid_results)
    total_tool_calls = sum(r.get("tool_calls", 0) for r in valid_results)
    total_code_edits = sum(r.get("code_edits", 0) for r in valid_results)
    avg_exergy = round(sum(r.get("exergy_score", 0) for r in valid_results) / max(1, len(valid_results)), 2)

    all_invariants = set()
    for r in valid_results:
        all_invariants.update(r.get("invariants", []))

    print("\n" + "="*80)
    print("📊 EXECUTIVE BRIEFING: 100-AGENT CONVERSATION SWARM AUDIT SUMMARY")
    print("="*80)
    print(f"▸ Total Sessions Audited:  {len(valid_results)} / {len(session_dirs)}")
    print(f"▸ Total User Prompts:       {total_prompts}")
    print(f"▸ Total Model Turns:       {total_turns}")
    print(f"▸ Total Tool Calls Executed:{total_tool_calls}")
    print(f"▸ Total Code Edits (Disk): {total_code_edits}")
    print(f"▸ Average Swarm Exergy:    {avg_exergy} / 1000.0")
    print(f"▸ Unique Invariants Active: {len(all_invariants)}")
    print("="*80)

    print("\n🏆 TOP 10 HIGH-EXERGY SESSIONS:")
    for idx, r in enumerate(valid_results[:10], 1):
        print(f"{idx:02d}. [{r['session_id'][:8]}] Exergy: {r['exergy_score']:6.1f} | Turns: {r['model_turns']:3d} | Tools: {r['tool_calls']:3d} | Prompt: {r['first_prompt'][:60]}")

    # Generate Markdown Summary Report in memory / file (without git commit)
    report_path = Path("docs/SWARM_CONVERSATIONS_AUDIT_REPORT.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# ⚡ C5-REAL: 100-AGENT CONVERSATION AUDIT REPORT (MAX EXERGY)\n")
        f.write("> **Status:** Executed via Parallel Swarm | **Git Sentinel:** UNCRYSTALLIZED (sin cristalizar)\n\n")
        f.write("## 1. METRICS & THERMODYNAMIC EXERGY MATRIX\n")
        f.write(f"- **Total Sessions Audited:** {len(valid_results)}\n")
        f.write(f"- **Total User Prompts:** {total_prompts}\n")
        f.write(f"- **Total Model Turns:** {total_turns}\n")
        f.write(f"- **Total Tool Executions:** {total_tool_calls}\n")
        f.write(f"- **Total Physical Code Edits:** {total_code_edits}\n")
        f.write(f"- **Mean Swarm Exergy Score:** `{avg_exergy}/1000.0`\n")
        f.write(f"- **Total Invariants Discovered:** {len(all_invariants)}\n\n")
        
        f.write("## 2. DISCOVERED INVARIANTS IN CONVERSATION CORPUS\n")
        for inv in sorted(list(all_invariants))[:30]:
            f.write(f"- `{inv}`\n")
        f.write("\n")
        
        f.write("## 3. TOP HIGH-EXERGY SESSION TRAJECTORIES\n")
        f.write("| Rank | Session ID | Exergy Score | Turns | Tools | Edits | Initial Prompt |\n")
        f.write("|:---:|:---|:---:|:---:|:---:|:---:|:---|\n")
        for idx, r in enumerate(valid_results[:25], 1):
            f.write(f"| {idx} | `{r['session_id']}` | **{r['exergy_score']}** | {r['model_turns']} | {r['tool_calls']} | {r['code_edits']} | {r['first_prompt'][:50]}... |\n")
            
    print(f"\n[+] Audit Report generated at {report_path} (NO GIT COMMIT EXECUTED).")

if __name__ == "__main__":
    main()
