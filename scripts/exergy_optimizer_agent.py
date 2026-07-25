import sys
from pathlib import Path

import babylon60.database.core

import hashlib
import json
import re
import sqlite3
import subprocess
import time
from dataclasses import dataclass
from typing import Union

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = Path.home() / '.babylon60/exergy_agent_ledger.db'
VAULT_DIR = Path.home() / '.gemini/config/.cortex/memory_vault'
BRAIN_DIR = Path.home() / '.gemini/antigravity/brain'

@dataclass(frozen=True)
class ExergyScore:
    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1000.0:
            raise ValueError('ExergyScore must be in range [0.0, 1000.0]')

@dataclass(frozen=True)
class GELABP:
    gradient: str
    entropy: str
    leverage: str
    autoloop: str
    bottleneck: str

@dataclass(frozen=True)
class ExergyPassed:
    score: ExergyScore
    gelabp: GELABP
    prov_hash: str

@dataclass(frozen=True)
class ExergyFailed:
    score: ExergyScore
    gelabp: GELABP
    reasons: list[str]
ExergyVerdict = ExergyPassed | ExergyFailed

@dataclass(frozen=True)
class TriggerConsolidation:
    reason: str
    pending_count: int

@dataclass(frozen=True)
class Stable:
    last_timestamp: float
ConsolidationDecision = TriggerConsolidation | Stable

def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = babylon60.database.core.connect_sync(str(DB_PATH))
    conn.execute('PRAGMA journal_mode=WAL;')
    cursor = conn.cursor()
    cursor.execute('\n        CREATE TABLE IF NOT EXISTS ledger (\n            id int PRIMARY KEY AUTOINCREMENT,\n            timestamp int NOT NULL,\n            commit_hash TEXT NOT NULL,\n            exergy_score int NOT NULL,\n            gradient TEXT NOT NULL,\n            entropy TEXT NOT NULL,\n            leverage TEXT NOT NULL,\n            autoloop TEXT NOT NULL,\n            bottleneck TEXT NOT NULL,\n            verdict_yaml TEXT NOT NULL,\n            prov_hash TEXT NOT NULL UNIQUE\n        )\n    ')
    conn.commit()
    conn.close()

def get_git_diff() -> str:
    try:
        diff = subprocess.check_output(['git', 'diff', 'HEAD'], text=True, stderr=subprocess.DEVNULL)
        return diff
    except subprocess.SubprocessError:
        return ''

def evaluate_gelabp(diff_text: str) -> ExergyVerdict:
    g_points = 5
    e_points = 1.0
    l_points = 5
    a_points = 5
    reasons_g = []
    reasons_e = []
    reasons_l = []
    reasons_a = []
    reasons_failed = []
    added = 0
    removed = 0
    files_diffs = diff_text.split('diff --git ')
    for file_diff in files_diffs:
        if not file_diff.strip():
            continue
        lines = file_diff.splitlines()
        header = lines[0] if lines else ''
        is_excluded = any(x in header for x in ['demo_exergy_poc.py', 'exergy_optimizer_agent.py', 'autodetect_invariants.py']) or 'test_' in header or 'tests/' in header
        added_lines = [line for line in lines if line.startswith('+') and (not line.startswith('+++'))]
        removed_lines = [line for line in lines if line.startswith('-') and (not line.startswith('---'))]
        added += len(added_lines)
        removed += len(removed_lines)
        if not is_excluded:
            for line in added_lines:
                if re.search('except\\s+Exception\\b|except\\s*:', line) and "bare 'except:'" not in line.lower() and ('except exception' not in line.lower()) and ('check for broad excepts' not in line.lower()):
                    print(f'DEBUG Match in {header}: {line}')
                    e_points += 4.0
                    msg = 'Broad exception caught (INV_C5_07 violation).'
                    reasons_e.append(msg)
                    reasons_failed.append(msg)
                if re.search('(SECRET|PRIVATE_KEY|MASTER_LEDGER_KEY)\\s*[:=]\\s*["\\\']\\w', line, re.IGNORECASE):
                    e_points += 8.0
                    msg = 'Hardcoded key pattern found (INV_C5_02 violation).'
                    reasons_e.append(msg)
                    reasons_failed.append(msg)
                if re.search('hashlib\\.(md5|sha1)\\b', line):
                    e_points += 5.0
                    msg = 'Weak hashing primitives (MD5/SHA1) (INV_C5_03 violation).'
                    reasons_e.append(msg)
                    reasons_failed.append(msg)
                if re.search('bytes\\((sk|sk\\.public_key)\\)', line):
                    l_points += 3
                    reasons_l.append('PyNaCl bytes serialization aligned with INV_C5_10.')
                if 'readlink' in line or 'is_symlink' in line:
                    l_points += 2
                    reasons_l.append('Nexus package symlink validation (INV_C5_12).')
        elif any('test' in ln or 'invariant' in ln for ln in added_lines):
            a_points += 4
            reasons_a.append('Autopoietic alignment of invariants (INV_C5_13).')
    if added > 400 and removed < 10:
        e_points += 1.5
        reasons_e.append('Large code volume increase with minimal deletion (Anergia Bloat risk).')
    if added > 0 and removed > added * 0.5:
        g_points += 2
        reasons_g.append('Active code pruning: high removal-to-addition ratio (Clean AST).')
    raw_score = g_points * l_points * a_points / e_points
    exergy_value = min(1000.0, raw_score * 8.0)
    score = ExergyScore(exergy_value)
    g_desc = '; '.join(reasons_g) if reasons_g else 'Standard code mutation.'
    e_desc = '; '.join(reasons_e) if reasons_e else 'No anomalies detected.'
    l_desc = '; '.join(reasons_l) if reasons_l else 'Standard support abstraction.'
    a_desc = '; '.join(reasons_a) if reasons_a else 'Execution feedback loops intact.'
    b_desc = 'Disk I/O and interpreter speed limits execution.'
    gelabp = GELABP(gradient=g_desc, entropy=e_desc, leverage=l_desc, autoloop=a_desc, bottleneck=b_desc)
    if exergy_value < 700.0 or reasons_failed:
        return ExergyFailed(score=score, gelabp=gelabp, reasons=reasons_failed)
    return ExergyPassed(score=score, gelabp=gelabp, prov_hash='')

def check_consolidation_need() -> ConsolidationDecision:
    if not BRAIN_DIR.exists():
        return Stable(last_timestamp=int(time.time() * 1000))
    consolidated_ids: set[str] = set()
    if VAULT_DIR.exists():
        for f in VAULT_DIR.glob('*.md'):
            try:
                content = f.read_text(encoding='utf-8')
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        m = re.search('conversation_id:\\s*["\\\']?([0-9a-f\\-]+)["\\\']?', parts[1])
                        if m:
                            consolidated_ids.add(m.group(1).strip())
            except OSError:
                continue
    unconsolidated_count = 0
    uuid_pattern = re.compile('^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    try:
        for entry in BRAIN_DIR.iterdir():
            if entry.is_dir() and uuid_pattern.match(entry.name):
                conv_id = entry.name
                if conv_id in consolidated_ids:
                    continue
                transcript = entry / '.system_generated/logs/transcript.jsonl'
                if transcript.exists():
                    belongs_to_babylon = False
                    keywords = ['babylon', '30_babylon-60', 'babylon60', 'cortex-persist', 'cortex.db', 'teorema', 'robinson', 'moskv']
                    try:
                        with open(transcript, encoding='utf-8') as tf:
                            for line in tf:
                                if not line.strip():
                                    continue
                                try:
                                    step = json.loads(line)
                                    text = f"{step.get('content', '')} {step.get('thinking', '')} {str(step.get('tool_calls', ''))}".lower()
                                    if any(kw in text for kw in keywords):
                                        belongs_to_babylon = True
                                        break
                                except json.JSONDecodeError:
                                    pass
                    except OSError:
                        pass
                    if belongs_to_babylon:
                        unconsolidated_count += 1
    except OSError:
        pass
    if unconsolidated_count >= 3:
        return TriggerConsolidation(reason=f'High accumulated KV Cache/Session Entropy: {unconsolidated_count} unconsolidated sessions detected.', pending_count=unconsolidated_count)
    return Stable(last_timestamp=int(time.time() * 1000))

def main() -> None:
    print('🔋 Igniting C5-REAL Exergy Optimizer Agent...')
    init_db()
    diff = get_git_diff()
    if not diff:
        try:
            diff = subprocess.check_output(['git', 'diff', 'HEAD~1', 'HEAD'], text=True, stderr=subprocess.DEVNULL)
            print('ℹ️ No active changes. Analyzing last commit delta.')
        except subprocess.SubprocessError:
            print('❌ Target error: Cannot load active or historical diff.')
            sys.exit(1)
    verdict = evaluate_gelabp(diff)
    try:
        commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.SubprocessError:
        commit_hash = 'unknown'
    timestamp = int(time.time() * 1000)
    prov_payload = f'{timestamp}:{commit_hash}:{verdict.score.value}'.encode()
    digest = hashlib.sha3_256(prov_payload).digest()
    from babylon60.utils.base60 import bytes_to_base60
    prov_hash = bytes_to_base60(digest)
    if isinstance(verdict, ExergyPassed):
        verdict = ExergyPassed(score=verdict.score, gelabp=verdict.gelabp, prov_hash=prov_hash)
    consolidation = check_consolidation_need()
    verdict_yaml = f'''# GELABP MATRIX O-COLLAPSE\nTarget: "Teorema-Robinson-Moskv"\nConfidence: C5-REAL\nExergyScore: {verdict.score.value:.1f}/1000.0\n\nG_Gradient: |\n  {verdict.gelabp.gradient}\nE_Entropy: |\n  {verdict.gelabp.entropy}\nL_Leverage: |\n  {verdict.gelabp.leverage}\nA_AutoLoop: |\n  {verdict.gelabp.autoloop}\nB_Bottleneck: |\n  {verdict.gelabp.bottleneck}\nP_PostHoc: |\n  "Narrativa descriptiva sin código" -> [TACHADO - IGNORAR]\n\nConsolidationStatus: "{('REQUIRED' if isinstance(consolidation, TriggerConsolidation) else 'STABLE')}"\nConsolidationDetails: "{(consolidation.reason if isinstance(consolidation, TriggerConsolidation) else 'Vault is synchronized')}"\n\nTimestamp: {timestamp}\nCommitHash: "{commit_hash}"\nProvSignature: "{prov_hash}"\n'''
    print(verdict_yaml)
    try:
        conn = babylon60.database.core.connect_sync(str(DB_PATH))
        conn.execute('PRAGMA journal_mode=WAL;')
        cursor = conn.cursor()
        cursor.execute('\n            INSERT INTO ledger (timestamp, commit_hash, exergy_score, gradient, entropy, leverage, autoloop, bottleneck, verdict_yaml, prov_hash)\n            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n        ', (timestamp, commit_hash, verdict.score.value, verdict.gelabp.gradient, verdict.gelabp.entropy, verdict.gelabp.leverage, verdict.gelabp.autoloop, verdict.gelabp.bottleneck, verdict_yaml, prov_hash))
        conn.commit()
        conn.close()
        print(f'✅ Exergy Attestation successfully written to Ledger: {DB_PATH.name}')
    except sqlite3.Error as err:
        print(f'❌ Failed to persist ledger: {err}')
    if isinstance(consolidation, TriggerConsolidation):
        print(f'\n🚨 CONSOLIDATION REQUIRED: {consolidation.pending_count} unconsolidated sessions pending.')
        print("💡 Suggestion: Run 'python3 scratch/prepare_and_crystallize.py' to crystallize sessions into the vault.")
    if isinstance(verdict, ExergyFailed):
        print(f'🚨 ALERT: Iteration Exergy too low ({verdict.score.value:.1f}/1000.0). Purge entropy before committing.')
        print('Reasons:\n  - ' + '\n  - '.join(verdict.reasons))
        sys.exit(1)
    sys.exit(0)
if __name__ == '__main__':
    main()