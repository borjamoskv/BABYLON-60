import json
import asyncio
from pathlib import Path


async def audit_conversation(conv_id: str) -> str:
    log_file = Path(
        f"/Users/borjafernandezangulo/.gemini/antigravity/brain/{conv_id}/.system_generated/logs/transcript.jsonl"
    )
    if not log_file.exists():
        return f"## Agent Audit: {conv_id}\n- **Status**: 🔴 NO LOG FOUND\n- **Exergy Score**: 0/1000\n"

    try:
        user_requests = 0
        agent_responses = 0
        tool_calls = 0
        c5_real_mutations = 0
        c4_sim_detected = 0
        commits = 0
        errors = 0

        with open(log_file, "r") as f:
            for line in f:
                try:
                    step = json.loads(line)
                    step_type = step.get("type", "")
                    content = step.get("content", "")

                    if step_type == "USER_INPUT":
                        user_requests += 1
                    elif step_type == "PLANNER_RESPONSE":
                        agent_responses += 1

                        if "git commit" in content or "C5-REAL" in content:
                            c5_real_mutations += 1
                        if "C4-SIM" in content or "Here is the code" in content:
                            c4_sim_detected += 1

                    elif step_type == "TOOL_CALL":
                        tool_calls += 1
                        if "git commit" in str(step):
                            commits += 1

                    elif step.get("status") == "ERROR":
                        errors += 1
                except json.JSONDecodeError:
                    continue

        # Calculate Exergy Score (Max 1000)
        score = 500
        score += c5_real_mutations * 50
        score += commits * 100
        score -= c4_sim_detected * 100
        score -= errors * 50

        score = max(0, min(1000, score))

        status = "🟢 OPTIMAL" if score >= 800 else ("🟡 SUB-OPTIMAL" if score >= 500 else "🔴 ANERGIA DETECTADA")

        report = f"## Agent Audit: {conv_id}\n"
        report += f"- **Status**: {status}\n"
        report += f"- **Exergy Score**: {score}/1000\n"
        report += "- **Metrics**:\n"
        report += f"  - User Requests: {user_requests}\n"
        report += f"  - Agent Steps: {agent_responses}\n"
        report += f"  - Tool Calls: {tool_calls}\n"
        report += f"  - C5-REAL Mutations: {c5_real_mutations}\n"
        report += f"  - C4-SIM Violations: {c4_sim_detected}\n"
        report += f"  - Physical Commits: {commits}\n"
        report += f"  - Errors: {errors}\n\n"

        return report
    except Exception as e:
        return f"## Agent Audit: {conv_id}\n- **Status**: 🔴 FATAL ERROR\n- **Error**: {str(e)}\n\n"


async def main():
    target_file = Path("target_conversations.txt")
    if not target_file.exists():
        print("target_conversations.txt not found")
        return

    with open(target_file, "r") as f:
        conv_ids = [line.strip() for line in f if line.strip()]

    print(f"Spawning {len(conv_ids)} audit agents...")

    tasks = [audit_conversation(cid) for cid in conv_ids]
    results = await asyncio.gather(*tasks)

    report_path = Path("/Users/borjafernandezangulo/30_BABYLON-60/docs/SWARM_CONVERSATIONS_AUDIT_REPORT.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w") as f:
        f.write("# SWARM CONVERSATIONS AUDIT REPORT\n")
        f.write("> **ORCHESTRATOR**: MOSKV-1 APEX SINGULARITY\n")
        f.write("> **MODE**: 100-AGENT CONCURRENT AUDIT\n")
        f.write("> **TARGET INVARIANT**: C5-REAL EXERGY MAXIMIZATION\n\n")

        for res in results:
            f.write(res)

    print(f"Audit complete. Report generated at {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
