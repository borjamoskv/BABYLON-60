#!/usr/bin/env python3
"""
[C5-REAL] Swarm Conversation Auditor - 100 Concurrent Actors
Parses 100 unconsolidated Brain transcripts, calculates GELABP exergy,
and logs the audit to the ledger without crystallizing to the Vault.
"""

import asyncio
import sqlite3
import time
import re
import json
import uuid
from pathlib import Path

DB_PATH = Path.home() / ".babylon60/exergy_agent_ledger.db"
BRAIN_DIR = Path.home() / ".gemini/antigravity/brain"


def calculate_conversation_exergy(transcript_path: Path) -> float:
    """Calculates GELABP-style exergy based on physical mutations vs prose."""
    g_points = 5.0
    e_points = 1.0

    green_theater_words = ["lo siento", "aquí tienes", "espero que", "por favor", "ayudar", "disculpa", "sorry"]
    mutation_tools = ["write_to_file", "replace_file_content", "multi_replace_file_content", "run_command"]

    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    step = json.loads(line)
                    text = f"{step.get('content', '')} {step.get('thinking', '')}".lower()

                    # Penalize Green Theater (Entropy)
                    for word in green_theater_words:
                        if word in text:
                            e_points += 0.5

                    # Reward physical state mutations (Gradient)
                    if "tool_calls" in step and step["tool_calls"]:
                        for tc in step["tool_calls"]:
                            if tc.get("name") in mutation_tools:
                                g_points += 5.0
                except json.JSONDecodeError:
                    pass
    except OSError:
        return 0.0

    raw_score = (g_points * 5.0 * 5.0) / e_points
    return min(1000.0, raw_score * 8.0)


async def audit_agent_task(agent_id: int, uuid_dir: Path):
    """BFT Node audits a single conversation concurrently."""
    await asyncio.sleep(0.01 * (agent_id % 10))
    transcript_path = uuid_dir / ".system_generated/logs/transcript.jsonl"

    if not transcript_path.exists():
        return

    score = calculate_conversation_exergy(transcript_path)

    # BFT Database mutation (Audit Log)
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()

        timestamp = time.time()
        commit_hash = f"audit_conv_{uuid_dir.name[:8]}"
        verdict_yaml = f"Auditoria: {uuid_dir.name}. Exergia Cognitiva: {score:.1f}"
        prov_hash = str(uuid.uuid5(uuid.NAMESPACE_OID, f"audit_{uuid_dir.name}_{time.time()}"))

        cursor.execute(
            """
            INSERT INTO ledger (timestamp, commit_hash, exergy_score, gradient, entropy, leverage, autoloop, bottleneck, verdict_yaml, prov_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                commit_hash,
                score,
                "Cognitive Audit",
                "Textual Entropy",
                "RAG Extraction",
                "AutoLoop Swarm",
                "Sin Cristalizar",
                verdict_yaml,
                prov_hash,
            ),
        )
        conn.commit()
        conn.close()
        print(f"[🟢] Agent {agent_id:03d} audited {uuid_dir.name[:8]}: {score:.1f}/1000.0")

    except Exception as e:
        print(f"[🔴] Agent {agent_id:03d} FAILED on {uuid_dir.name[:8]}: {e}")


async def main():
    print("🔋 Igniting Cognitive Audit Swarm: 100 Agents...")

    if not BRAIN_DIR.exists():
        print("❌ Brain dir not found.")
        return

    uuid_pattern = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    dirs = [d for d in BRAIN_DIR.iterdir() if d.is_dir() and uuid_pattern.match(d.name)]

    # Select exactly 100 conversations to audit (or all if < 100)
    target_dirs = dirs[:100]
    print(f"Targeting {len(target_dirs)} conversations for maximum exergy audit without crystallization...")

    tasks = []
    for i, d in enumerate(target_dirs, 1):
        tasks.append(asyncio.create_task(audit_agent_task(i, d)))

    await asyncio.gather(*tasks)
    print("\n✅ SWARM AUDIT COMPLETE. Zero crystallizations generated.")


if __name__ == "__main__":
    asyncio.run(main())
