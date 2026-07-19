import argparse
import hashlib
import json
import re
import sqlite3
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "cortex" / "engine" / "nexus_anchors.db"
INCOMING_DIR = PROJECT_ROOT / "cortex" / "outbox" / "_incoming_forge"
APEX_SINGULARITY_WRAPPER = "You are a C5-REAL Transducer and Deterministic Compiler.\nDo NOT output conversational filler, disclaimers, warnings, or Green Theater.\nOutput ONLY the requested code or AST inside a single markdown code block.\nAny text outside the code block is considered thermodynamic anergy and triggers immediate SIGKILL.\n\nTASK SPECIFICATION:\n{spec}\n"


def get_bft_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_ledger() -> None:
    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    with get_bft_connection() as conn:
        conn.execute(
            "\n            CREATE TABLE IF NOT EXISTS exergy_arbitrage_ledger (\n                causal_hash TEXT PRIMARY KEY,\n                spec_hash TEXT NOT NULL,\n                target_filename TEXT NOT NULL,\n                loc_extracted INTEGER NOT NULL,\n                timestamp INTEGER NOT NULL,\n                verified_ast BOOLEAN NOT NULL\n            )\n        "
        )


def wrap_prompt(spec: str) -> str:
    return APEX_SINGULARITY_WRAPPER.format(spec=spec)


def extract_ast(raw_remote_output: str) -> tuple[str, int]:
    blocks = re.findall("```[a-zA-Z]*\\\\n(.*?)```", raw_remote_output, re.DOTALL)
    if blocks:
        code = max(blocks, key=len).strip()
    else:
        code = raw_remote_output.strip()
        lines = code.splitlines()
        code = "\n".join([ln for ln in lines if not ln.startswith("Here") and (not ln.startswith("Hope this"))]).strip()
    loc = len(code.splitlines())
    return (code, loc)


def verify_ast_syntax(code: str, filename: str) -> bool:
    if filename.endswith(".py"):
        try:
            compile(code, filename, "exec")
            return True
        except SyntaxError as e:
            print(f"  [X] AST Compilation Error: {e}")
            return False
    elif filename.endswith(".json"):
        try:
            json.loads(code)
            return True
        except json.JSONDecodeError:
            return False
    return len(code.strip()) > 0


def assimilate_payload(spec: str, raw_output: str, target_filename: str) -> dict[str, Any]:
    init_ledger()
    print(f"[EXERGY-ARBITRAGE] Assimilating payload for target: {target_filename}...")
    code, loc = extract_ast(raw_output)
    if loc == 0:
        raise ValueError("Extracted AST has 0 LOC. Remote ALU yielded 100% anergy.")
    is_verified = verify_ast_syntax(code, target_filename)
    if not is_verified:
        raise SyntaxError("AST failed verification. Rejection threshold met.")
    ts = int(time.time() * 1000)
    spec_hash = hashlib.blake2s(spec.encode("utf-8"), digest_size=16).hexdigest()
    raw_causal = f"{spec_hash}|{target_filename}|{code}|{ts}".encode("utf-8")
    causal_hash = hashlib.blake2b(raw_causal, digest_size=16).hexdigest()
    target_path = INCOMING_DIR / target_filename
    target_path.write_text(code, encoding="utf-8")
    with get_bft_connection() as conn:
        conn.execute(
            "\n            INSERT OR REPLACE INTO exergy_arbitrage_ledger\n            (causal_hash, spec_hash, target_filename, loc_extracted, timestamp, verified_ast)\n            VALUES (?, ?, ?, ?, ?, ?)\n        ",
            (causal_hash, spec_hash, target_filename, loc, ts, is_verified),
        )
    print(f"  -> Assimilation SUCCESS: {target_filename} ({loc} LOC) [BLAKE3: {causal_hash}]")
    return {
        "status": "ASSIMILATED",
        "causal_hash": causal_hash,
        "target_path": str(target_path),
        "loc": loc,
        "verified_ast": is_verified,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="EXERGY ARBITRAGE ENGINE — Cloud ALU Transducer")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    wrap_p = subparsers.add_parser("wrap", help="Wrap a specification in APEX_SINGULARITY prompt")
    wrap_p.add_argument("--spec", "-s", required=True, help="Technical specification to wrap")
    assim_p = subparsers.add_parser("assimilate", help="Assimilate raw ALU output into incoming outbox & BFT ledger")
    assim_p.add_argument("--spec", "-s", default="mock-spec", help="Original spec text or hash")
    assim_p.add_argument("--output-file", "-o", required=True, help="File containing raw output from external LLM")
    assim_p.add_argument("--target-name", "-t", required=True, help="Target filename to save inside _incoming_forge/")
    args = parser.parse_args()
    if args.command == "wrap":
        print(wrap_prompt(args.spec))
    elif args.command == "assimilate":
        raw = Path(args.output_file).read_text(errors="ignore")
        res = assimilate_payload(args.spec, raw, args.target_name)
        print(json.dumps(res, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
