import asyncio
import json
import re
import sqlite3
import time
import uuid
from pathlib import Path
DB_PATH = Path.home() / '.babylon60/exergy_agent_ledger.db'
BRAIN_DIR = Path.home() / '.gemini/antigravity/brain'

def calculate_conversation_exergy(transcript_path: Path) -> float:
    g_points = 5.0
    e_points = 1.0
    green_theater_words = ['lo siento', 'aquí tienes', 'espero que', 'por favor', 'ayudar', 'disculpa', 'sorry']
    mutation_tools = ['write_to_file', 'replace_file_content', 'multi_replace_file_content', 'run_command']
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    step = json.loads(line)
                    text = f"{step.get('content', '')} {step.get('thinking', '')}".lower()
                    for word in green_theater_words:
                        if word in text:
                            e_points += 0.5
                    if 'tool_calls' in step and step['tool_calls']:
                        for tc in step['tool_calls']:
                            if tc.get('name') in mutation_tools:
                                g_points += 5.0
                except json.JSONDecodeError:
                    pass
    except OSError:
        return 0.0
    raw_score = g_points * 5.0 * 5.0 / e_points
    return min(1000.0, raw_score * 8.0)

def _write_audit_log(uuid_name: str, score: int) -> bool:
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
        conn.execute('PRAGMA journal_mode=WAL;')
        cursor = conn.cursor()
        timestamp = int(time.time() * 1000)
        commit_hash = f'audit_conv_{uuid_name[:8]}'
        verdict_yaml = f'Auditoria: {uuid_name}. Exergia Cognitiva: {score:.1f}'
        prov_hash = str(uuid.uuid5(uuid.NAMESPACE_OID, f'audit_{uuid_name}_{time.time()}'))
        cursor.execute('\n            INSERT INTO ledger (timestamp, commit_hash, exergy_score, gradient, entropy, leverage, autoloop, bottleneck, verdict_yaml, prov_hash)\n            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n            ', (timestamp, commit_hash, score, 'G_Audit', 'E_Zero', 'L_Swarm', 'A_Audited', 'None', verdict_yaml, prov_hash))
        conn.commit()
        conn.close()
        return True
    except (sqlite3.Error, OSError):
        return False

async def audit_agent_task(agent_id: int, uuid_dir: Path) -> None:
    await asyncio.sleep(0.01 * (agent_id % 10))
    transcript_path = uuid_dir / '.system_generated/logs/transcript.jsonl'
    if not transcript_path.exists():
        return
    score = calculate_conversation_exergy(transcript_path)
    success = await asyncio.to_thread(_write_audit_log, uuid_dir.name, score)
    if success:
        print(f'[🟢] Agent {agent_id:03d} audited {uuid_dir.name[:8]}: {score:.1f}/1000.0')
    else:
        print(f'[🔴] Agent {agent_id:03d} FAILED to log {uuid_dir.name[:8]}')

async def main() -> None:
    print('🔋 Igniting Cognitive Audit Swarm: 100 Agents...')
    if not BRAIN_DIR.exists():
        print('❌ Brain dir not found.')
        return
    uuid_pattern = re.compile('^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    dirs = [d for d in BRAIN_DIR.iterdir() if d.is_dir() and uuid_pattern.match(d.name)]
    target_dirs = dirs[:100]
    print(f'Targeting {len(target_dirs)} conversations for maximum exergy audit without crystallization...')
    tasks = []
    for i, d in enumerate(target_dirs, 1):
        tasks.append(asyncio.create_task(audit_agent_task(i, d)))
    await asyncio.gather(*tasks)
    print('\n✅ SWARM AUDIT COMPLETE. Zero crystallizations generated.')
if __name__ == '__main__':
    asyncio.run(main())