import re
from pathlib import Path


def fix_file(filepath):
    path = Path(filepath)
    if not path.exists():
        return
    content = path.read_text()
    new_content = re.sub(
        "^([ \\t]*)def ([a-zA-Z0-9_]+)\\(([^)]*)\\):", "\\1def \\2(\\3) -> None:", content, flags=re.MULTILINE
    )
    new_content = re.sub("# type: ignore$", "", new_content, flags=re.MULTILINE)
    new_content = re.sub("(: set) =", ": set[str] =", new_content)
    new_content = re.sub("(: dict[str, typing.Any]) =", ": dict[str, str] =", new_content)
    if new_content != content:
        path.write_text(new_content)
        print(f"Fixed {filepath}")


files = [
    "scripts/c5_opera_attestation.py",
    "scripts/autodetect_invariants.py",
    "scripts/audit_md_files.py",
    "scripts/fix_sqlite.py",
    "scripts/c5_autopoietic_exergy_daemon.py",
    "scripts/kinetic_purge_ultrathink.py",
    "scripts/map_skills_bridges.py",
    "proof_kernel/crdt.py",
    "babylon60/crypto/keyring.py",
    "proof_kernel/ast_rule.py",
    "scripts/audit_conversations_swarm.py",
    "scripts/swarm_audit.py",
    "scripts/bft_swarm_100.py",
    "scripts/audit_conversations_100.py",
    "babylon60/utils/void_vec.py",
    "tests/test_proof_kernel_invariants.py",
    "tests/test_net_mamba_ledger_engine.py",
    "tests/test_c5_invariants.py",
    "scripts/omega_arena_stress.py",
]
for f in files:
    fix_file(f)
