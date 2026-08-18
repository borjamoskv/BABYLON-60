#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
[Causal-Determinist] Exergy Optimizer Agent.
Parses changes, evaluates them using the GELABP thermodynamic framework,
implements strict algebraic typing, and determines when memory consolidation is required.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path to resolve local packages
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dataclasses import dataclass  # noqa: E402
from typing import Union, List, Set, Optional, Tuple  # noqa: E402
import sqlite3  # noqa: E402
import hashlib  # noqa: E402
import time  # noqa: E402

from babylon60.database.core import connect_sync
import subprocess  # noqa: E402
import ast  # noqa: E402


class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.current_depth = 0
        self.max_depth = 0

    def visit(self, node: ast.AST) -> None:
        is_control = isinstance(
            node, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        )
        if is_control:
            self.current_depth += 1
            if self.current_depth > self.max_depth:
                self.max_depth = self.current_depth

        super().generic_visit(node)

        if is_control:
            self.current_depth -= 1


# Invariants
babylon_home = os.environ.get("BABYLON_HOME")
if not babylon_home:
    raise RuntimeError("INV_C5_ENV: BABYLON_HOME must be set. Path.home() is prohibited.")
DB_PATH = Path(babylon_home) / ".babylon60/exergy_agent_ledger.db"
gemini_home = os.environ.get("GEMINI_HOME")
if not gemini_home:
    raise RuntimeError("INV_C5_ENV: GEMINI_HOME must be set. Path.home() is prohibited.")
VAULT_DIR = Path(gemini_home) / "config/.cortex/memory_vault"
BRAIN_DIR = Path(gemini_home) / "antigravity-ide/brain"


@dataclass(frozen=True)
class ExergyScore:
    value: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.value <= 1000.0):
            raise ValueError("ExergyScore must be in range [0.0, 1000.0]")


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
    reasons: List[str]


# Algebraic Sum Type for Verdict
ExergyVerdict = Union[ExergyPassed, ExergyFailed]


@dataclass(frozen=True)
class TriggerConsolidation:
    reason: str
    pending_count: int


@dataclass(frozen=True)
class Stable:
    last_timestamp: float


# Algebraic Sum Type for Consolidation
ConsolidationDecision = Union[TriggerConsolidation, Stable]


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = connect_sync(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            commit_hash TEXT NOT NULL,
            exergy_score REAL NOT NULL,
            gradient TEXT NOT NULL,
            entropy TEXT NOT NULL,
            leverage TEXT NOT NULL,
            autoloop TEXT NOT NULL,
            bottleneck TEXT NOT NULL,
            verdict_yaml TEXT NOT NULL,
            prov_hash TEXT NOT NULL UNIQUE
        )
    """)
    conn.commit()
    conn.close()


def get_git_diff() -> str:
    try:
        diff = subprocess.check_output(["git", "diff", "HEAD"], text=True, stderr=subprocess.DEVNULL)
        return diff
    except subprocess.SubprocessError:
        return ""


def _analyze_added_lines(added_lines: List[str], header: str) -> Tuple[float, int, List[str], List[str]]:
    e_pts = 0.0
    l_pts = 0
    reasons_e = []
    reasons_l = []
    for line in added_lines:
        if re.search(r"except\s+Exception\b|except\s*:", line):
            e_pts += 4.0
            reasons_e.append("Broad exception caught (INV_C5_07 violation).")
        if re.search(r'(SECRET|PRIVATE_KEY|MASTER_LEDGER_KEY)\s*[:=]\s*["\']\w', line, re.IGNORECASE):
            e_pts += 8.0
            reasons_e.append("Hardcoded key pattern found (INV_C5_02 violation).")
        if re.search(r"hashlib\.(md5|sha1)\b", line):
            e_pts += 5.0
            reasons_e.append("Weak hashing primitives (MD5/SHA1) (INV_C5_03 violation).")
        if re.search(r"bytes\((sk|sk\.public_key)\)", line):
            l_pts += 3
            reasons_l.append("PyNaCl bytes serialization aligned with INV_C5_10.")
        if "readlink" in line or "is_symlink" in line:
            l_pts += 2
            reasons_l.append("Nexus package symlink validation (INV_C5_12).")
    return e_pts, l_pts, reasons_e, reasons_l


def _check_ast_complexity(header: str) -> Tuple[float, List[str]]:
    m = re.search(r"b/([^\s]+)", header)
    if not m:
        return 0.0, []
    filepath = m.group(1)
    if not filepath.endswith(".py"):
        return 0.0, []
    try:
        with open(filepath, "r") as f:
            tree = ast.parse(f.read())
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        if visitor.max_depth > 4:
            msg = f"CRITICAL: Algebraic Limit Exceeded (Nesting Depth = {visitor.max_depth} > 4) in {filepath}."
            return 500.0, [msg]
    except (SyntaxError, FileNotFoundError):
        pass
    return 0.0, []


def evaluate_gelabp(diff_text: str) -> ExergyVerdict:
    """
    Thermodynamic analysis of the diff.
    Returns either ExergyPassed or ExergyFailed based on algebraic rules.
    """
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

    files_diffs = diff_text.split("diff --git ")
    for file_diff in files_diffs:
        if not file_diff.strip():
            continue
        lines = file_diff.splitlines()
        header = lines[0] if lines else ""

        is_excluded = (
            any(x in header for x in ["demo_exergy_poc.py", "exergy_optimizer_agent.py", "autodetect_invariants.py"])
            or "test_" in header
            or "tests/" in header
        )

        added_lines = [line for line in lines if line.startswith("+") and not line.startswith("+++")]
        removed_lines = [line for line in lines if line.startswith("-") and not line.startswith("---")]

        added += len(added_lines)
        removed += len(removed_lines)

        if not is_excluded:
            e_add, l_add, r_e, r_l = _analyze_added_lines(added_lines, header)
            e_points += e_add
            l_points += l_add
            reasons_e.extend(r_e)
            reasons_l.extend(r_l)
            reasons_failed.extend(r_e)

            e_ast, r_ast = _check_ast_complexity(header)
            e_points += e_ast
            reasons_e.extend(r_ast)
            reasons_failed.extend(r_ast)
        elif any("test" in ln or "invariant" in ln for ln in added_lines):
            a_points += 4
            reasons_a.append("Autopoietic alignment of invariants (INV_C5_13).")

    if added > 100 and removed < 5:
        e_points += 1.5
        reasons_e.append("Large code volume increase with minimal deletion (Anergia Bloat risk).")

    if added > 0 and removed > added * 0.5:
        g_points += 2
        reasons_g.append("Active code pruning: high removal-to-addition ratio (Clean AST).")

    raw_score = (g_points * l_points * a_points) / e_points
    exergy_value = min(1000.0, raw_score * 8.0)
    score = ExergyScore(exergy_value)

    g_desc = "; ".join(reasons_g) if reasons_g else "Standard code mutation."
    e_desc = "; ".join(reasons_e) if reasons_e else "No anomalies detected."
    l_desc = "; ".join(reasons_l) if reasons_l else "Standard support abstraction."
    a_desc = "; ".join(reasons_a) if reasons_a else "Execution feedback loops intact."
    b_desc = "Disk I/O and interpreter speed limits execution."

    gelabp = GELABP(gradient=g_desc, entropy=e_desc, leverage=l_desc, autoloop=a_desc, bottleneck=b_desc)

    if exergy_value < 700.0 or reasons_failed:
        return ExergyFailed(score=score, gelabp=gelabp, reasons=reasons_failed)

    return ExergyPassed(score=score, gelabp=gelabp, prov_hash="")


def _extract_conv_id_from_file(filepath: Path) -> Optional[str]:
    try:
        content = filepath.read_text(encoding="utf-8")
        if not content.startswith("---"):
            return None
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None
        m = re.search(r'conversation_id:\s*["\']?([0-9a-f\-]+)["\']?', parts[1])
        return m.group(1).strip() if m else None
    except OSError:
        return None


def _get_consolidated_ids() -> Set[str]:
    consolidated_ids: Set[str] = set()
    if not VAULT_DIR.exists():
        return consolidated_ids
    for f in VAULT_DIR.glob("*.md"):
        cid = _extract_conv_id_from_file(f)
        if cid:
            consolidated_ids.add(cid)
    return consolidated_ids


def check_consolidation_need() -> ConsolidationDecision:
    """
    Checks brain folders and memory vault files to determine if consolidation is required.
    """
    if not BRAIN_DIR.exists():
        return Stable(last_timestamp=time.time())

    consolidated_ids = _get_consolidated_ids()
    unconsolidated_count = 0
    uuid_pattern = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

    try:
        for entry in BRAIN_DIR.iterdir():
            if entry.is_dir() and uuid_pattern.match(entry.name):
                conv_id = entry.name
                if conv_id not in consolidated_ids and (entry / ".system_generated/logs/transcript.jsonl").exists():
                    unconsolidated_count += 1
    except OSError:
        pass

    if unconsolidated_count >= 3:
        return TriggerConsolidation(
            reason=f"High accumulated KV Cache/Session Entropy: {unconsolidated_count} unconsolidated sessions detected.",
            pending_count=unconsolidated_count,
        )
    return Stable(last_timestamp=time.time())


def main() -> None:
    print("🔋 Igniting Causal-Determinist Exergy Optimizer Agent...")
    init_db()

    diff = get_git_diff()
    if not diff:
        try:
            diff = subprocess.check_output(["git", "diff", "HEAD~1", "HEAD"], text=True, stderr=subprocess.DEVNULL)
            print("ℹ️ No active changes. Analyzing last commit delta.")
        except subprocess.SubprocessError:
            print("❌ Target error: Cannot load active or historical diff.")
            sys.exit(1)

    verdict = evaluate_gelabp(diff)

    try:
        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except subprocess.SubprocessError:
        commit_hash = "unknown"

    timestamp = time.time()
    prov_payload = f"{timestamp}:{commit_hash}:{verdict.score.value}".encode("utf-8")
    digest = hashlib.sha3_256(prov_payload).digest()

    from babylon60.primitives.base60 import bytes_to_base60

    prov_hash = bytes_to_base60(digest)

    # Update prov_hash on verdict if it's passed
    if isinstance(verdict, ExergyPassed):
        verdict = ExergyPassed(score=verdict.score, gelabp=verdict.gelabp, prov_hash=prov_hash)

    # Check consolidation decision
    consolidation = check_consolidation_need()

    verdict_yaml = f"""# GELABP MATRIX O-COLLAPSE
Target: "Teorema-Robinson-Moskv"
Confidence: Causal-Determinist
ExergyScore: {verdict.score.value:.1f}/1000.0

# INVARIANTES ESTRUCTURALES
G_Gradient: |
  {verdict.gelabp.gradient}
E_Entropy: |
  {verdict.gelabp.entropy}
L_Leverage: |
  {verdict.gelabp.leverage}
A_AutoLoop: |
  {verdict.gelabp.autoloop}
B_Bottleneck: |
  {verdict.gelabp.bottleneck}
P_PostHoc: |
  "Narrativa descriptiva sin código" -> [TACHADO - IGNORAR]

# CONSOLIDATION METRICS
ConsolidationStatus: "{"REQUIRED" if isinstance(consolidation, TriggerConsolidation) else "STABLE"}"
ConsolidationDetails: "{consolidation.reason if isinstance(consolidation, TriggerConsolidation) else "Vault is synchronized"}"

# ATTESTATION PROVENANCE
Timestamp: {timestamp}
CommitHash: "{commit_hash}"
ProvSignature: "{prov_hash}"
"""
    print(verdict_yaml)

    # Write to database
    try:
        conn = connect_sync(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ledger (timestamp, commit_hash, exergy_score, gradient, entropy, leverage, autoloop, bottleneck, verdict_yaml, prov_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                timestamp,
                commit_hash,
                verdict.score.value,
                verdict.gelabp.gradient,
                verdict.gelabp.entropy,
                verdict.gelabp.leverage,
                verdict.gelabp.autoloop,
                verdict.gelabp.bottleneck,
                verdict_yaml,
                prov_hash,
            ),
        )
        conn.commit()
        conn.close()
        print(f"✅ Exergy Attestation successfully written to Ledger: {DB_PATH.name}")
    except sqlite3.Error as err:
        print(f"❌ Failed to persist ledger: {err}")

    # Act on consolidation decision
    if isinstance(consolidation, TriggerConsolidation):
        print(f"\n🚨 CONSOLIDATION REQUIRED: {consolidation.pending_count} unconsolidated sessions pending.")
        print("💡 Suggestion: Run 'python3 scratch/prepare_and_crystallize.py' to crystallize sessions into the vault.")

    # Fail-Fast if exergy score is below threshold (700)
    if isinstance(verdict, ExergyFailed):
        print(
            f"🚨 ALERT: Iteration Exergy too low ({verdict.score.value:.1f}/1000.0). Purge entropy before committing."
        )
        print("Reasons:\n  - " + "\n  - ".join(verdict.reasons))
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
