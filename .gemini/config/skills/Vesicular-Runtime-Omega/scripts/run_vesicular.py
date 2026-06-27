import os
import sys
import json
import sqlite3
import hashlib
import time
import subprocess
import re
from pathlib import Path
from typing import Any, Dict, Tuple, List


# Vesicular-Runtime-Omega
# Bounded OS environment for Agent stateless execution

CORTEX_DB_PATH = Path.home() / ".gemini/antigravity/scratch/cortex-c5-ledger/cortex.db"
RUNTIME_DIR = Path(__file__).parent.parent
SEATBELT_PROFILE = RUNTIME_DIR / "vesicle.sb"

def ensure_cortex_db():
    CORTEX_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CORTEX_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vesicular_checkpoints (
            hash TEXT PRIMARY KEY,
            timestamp TEXT,
            intent TEXT,
            causal_parent TEXT,
            payload TEXT,
            signature TEXT
        )
    """)
    # Check if we need to migrate/recreate episodic_failures due to new fingerprinting columns
    try:
        cursor.execute("SELECT error_class FROM episodic_failures LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("DROP TABLE IF EXISTS episodic_failures")
        
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS episodic_failures (
            signature TEXT PRIMARY KEY,
            intent TEXT,
            error_class TEXT,
            error_detail TEXT,
            failing_file TEXT,
            failing_line INTEGER,
            failing_func TEXT,
            error_message TEXT,
            mitigation_payload TEXT,
            exergy_at_failure REAL,
            timestamp TEXT
        )
    """)
    conn.commit()
    return conn

def write_checkpoint(conn: sqlite3.Connection, intent: str, causal_parent: str, payload: dict):
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S.000000+00:00')
    payload_str = json.dumps(payload, sort_keys=True)
    
    # Simple hash chain signature
    raw_sig = f"{timestamp}{intent}{causal_parent}{payload_str}".encode()
    signature = hashlib.sha256(raw_sig).hexdigest()
    record_hash = hashlib.sha256(signature.encode()).hexdigest()[:16]

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO vesicular_checkpoints (hash, timestamp, intent, causal_parent, payload, signature) VALUES (?, ?, ?, ?, ?, ?)",
        (record_hash, timestamp, intent, causal_parent, payload_str, signature)
    )
    conn.commit()
    return record_hash

def get_credential(service: str, account: str) -> str:
    # C5-REAL: macOS Keychain via security CLI
    try:
        cmd = ["security", "find-generic-password", "-w", "-s", service, "-a", account]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        # Fallback or empty if not set for strict testing
        return ""

class TaskIntent:
    def __init__(self, needs_filesystem: bool = True, target_paths: List[str] = None, needs_network: bool = False, needs_keychain: bool = False):
        self.needs_filesystem = needs_filesystem
        self.target_paths = target_paths or []
        self.needs_network = needs_network
        self.needs_keychain = needs_keychain

def parse_intent_string(intent_str: str) -> TaskIntent:
    # Default: allow workspace, /tmp, and antigravity data path
    paths = [
        "/tmp",
        "$CORTEX_ROOT/10_PROJECTS/borjamoskv-site",
        "$CORTEX_ROOT/.gemini/antigravity"
    ]
    
    # Extract absolute paths that might be mentioned in the intent
    found_paths = re.findall(r'/[a-zA-Z0-9_\-\.\/]+', intent_str)
    for p in found_paths:
        if os.path.exists(p) or p.startswith("$CORTEX_ROOT/10_PROJECTS"):
            paths.append(p)
            
    # Check if network outbound is requested
    needs_network = any(word in intent_str.lower() for word in ["network", "fetch", "scrape", "api", "url", "http", "curl"])
    
    # Check if keychain/keys is requested
    needs_keychain = any(word in intent_str.lower() for word in ["keychain", "credential", "auth", "token", "password", "env"])
    
    return TaskIntent(
        needs_filesystem=True,
        target_paths=list(set(paths)),
        needs_network=needs_network,
        needs_keychain=needs_keychain
    )

def compile_sb_profile(intent: TaskIntent) -> str:
    exec_dir = os.path.dirname(sys.executable)
    real_exec_dir = os.path.dirname(os.path.realpath(sys.executable))
    
    rules = [
        "(version 1)",
        "(deny default)",
        f'(allow process-exec (subpath "{exec_dir}") (subpath "{real_exec_dir}") (subpath "/opt/homebrew") (subpath "/usr/bin") (subpath "/bin"))',
        "(allow file-read*)",
        "(deny file-write*)"
    ]
    
    if intent.needs_filesystem:
        for path in intent.target_paths:
            # Only allow write to workspace, /tmp or explicitly permitted user temp areas
            if path.startswith(("/tmp", "$CORTEX_ROOT/10_PROJECTS/borjamoskv-site", "$CORTEX_ROOT/.gemini/antigravity")):
                rules.append(f'(allow file-write* (subpath "{path}"))')

    if intent.needs_network:
        rules.append("(allow network-outbound)")
    else:
        rules.append("(deny network*)")
        
    return "\n".join(rules)

def validate_seatbelt_profile(sb_content: str) -> Tuple[bool, str]:
    # Rule 1: No blanket file-write* to root
    if re.search(r'\(allow\s+file-write\*\s+\(subpath\s+"/"\)\)', sb_content):
        return False, "Security Violation: Root filesystem write access requested."
        
    # Rule 2: Deny default rule override
    if not re.search(r'\(deny\s+default\)', sb_content):
        return False, "Security Violation: Default deny rule missing."
        
    # Rule 3: Restrict system write access
    write_paths = re.findall(r'\(allow\s+file-write\*(?:\-data)?\s+\(subpath\s+"([^"]+)"\)\)', sb_content)
    for path in write_paths:
        # Allow /tmp, workspace, and antigravity directories
        if not path.startswith(("/tmp", "$CORTEX_ROOT/10_PROJECTS/borjamoskv-site", "$CORTEX_ROOT/.gemini/antigravity")):
            return False, f"Security Violation: File write allowed outside workspace limits: {path}"
            
    return True, "Profile passes security invariants."

def execute_sandboxed(code: str, intent_str: str) -> str:
    # C5-REAL: Dynamic Bounded execution via macOS Seatbelt (sandbox-exec)
    intent = parse_intent_string(intent_str)
    profile_content = compile_sb_profile(intent)
    
    valid, msg = validate_seatbelt_profile(profile_content)
    if not valid:
        return f"ERROR: Execution failed (security): JIT seatbelt profile validation failed: {msg}"
        
    # Write whitelisted JIT profile
    SEATBELT_PROFILE.write_text(profile_content, encoding="utf-8")

    # We use a temporary file for the payload to execute securely inside the sandbox
    target_py = RUNTIME_DIR / ".vesicle_target.py"
    target_py.write_text(code, encoding="utf-8")

    try:
        cmd = ["sandbox-exec", "-f", str(SEATBELT_PROFILE), sys.executable, str(target_py)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return f"ERROR: Execution failed (code {result.returncode}): {result.stderr.strip()}"
        return result.stdout
    except subprocess.TimeoutExpired:
        return "ERROR: Vesicle Sandbox Timeout"
    except Exception as e:
        return f"ERROR: Sandbox execution failed: {e}"
    finally:
        if target_py.exists():
            target_py.unlink()

def create_seatbelt_profile():
    profile = """(version 1)
(deny default)
(allow process-exec (literal "/opt/homebrew/bin/python3") (literal "/usr/bin/python3"))
(allow file-read*
    (subpath "/System/Library")
    (subpath "/usr/lib")
    (subpath "/usr/local/lib")
    (subpath "/opt/homebrew/Cellar")
    (subpath "/opt/homebrew/lib")
    (subpath "/opt/homebrew/opt")
)
(allow file-read-data (subpath "$CORTEX_ROOT/.gemini/antigravity/skills/Vesicular-Runtime-Omega"))
(deny network*)
"""
    SEATBELT_PROFILE.write_text(profile, encoding="utf-8")

class FailureFingerprint:
    def __init__(self, error_class: str, error_detail: str, file: str, line: int, func: str):
        self.error_class = error_class
        self.error_detail = error_detail
        self.file = file
        self.line = line
        self.func = func

    def compute_signature(self) -> str:
        raw = f"{self.error_class}:{self.file}:{self.line}:{self.func}:{self.normalize(self.error_detail)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @staticmethod
    def normalize(detail: str) -> str:
        d = re.sub(r'0x[0-9a-fA-F]+', '0xHEX', detail)
        d = re.sub(r'/tmp/omega_trigger_[a-zA-Z0-9_]+\.py', '/tmp/omega_trigger_TEMP.py', d)
        d = re.sub(r'\d+', 'NUM', d)
        return d.strip()

    @classmethod
    def parse_from_traceback(cls, tb_text: str) -> 'FailureFingerprint':
        error_class = "RuntimeError"
        error_detail = tb_text.strip()
        file = "unknown"
        line = 0
        func = "unknown"

        tb_lines = [l.strip() for l in tb_text.splitlines() if l.strip()]
        if not tb_lines:
            return cls(error_class, error_detail, file, line, func)

        last_line = tb_lines[-1]
        match_err = re.match(r'^([a-zA-Z0-9_]+Error|Exception|SystemExit|KeyboardInterrupt):\s*(.*)$', last_line)
        if match_err:
            error_class = match_err.group(1)
            error_detail = match_err.group(2)
        elif ":" in last_line:
            parts = last_line.split(":", 1)
            if re.match(r'^[a-zA-Z0-9_]+$', parts[0].strip()):
                error_class = parts[0].strip()
                error_detail = parts[1].strip()

        for line_str in reversed(tb_lines[:-1]):
            frame_match = re.search(r'File\s+"([^"]+)",\s+line\s+(\d+),\s+in\s+([a-zA-Z0-9_<>\-]+)', line_str)
            if frame_match:
                file = Path(frame_match.group(1)).name
                line = int(frame_match.group(2))
                func = frame_match.group(3)
                break

        return cls(error_class, error_detail, file, line, func)

def check_episodic_mitigation(conn: sqlite3.Connection, intent: str, logic_payload: str = None) -> Tuple[bool, str]:
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT intent, error_class, error_detail, failing_file, failing_line, failing_func, mitigation_payload 
            FROM episodic_failures
        """)
        rows = cursor.fetchall()
        best_match = None
        highest_score = 0.0

        intent_words = set(w.lower() for w in re.findall(r'\w+', intent) if len(w) > 3)

        for failed_intent, err_class, err_detail, fail_file, fail_line, fail_func, mitigation in rows:
            score = 0.0
            failed_words = set(w.lower() for w in re.findall(r'\w+', failed_intent) if len(w) > 3)
            common = intent_words.intersection(failed_words)
            if common:
                score += (len(common) / len(intent_words.union(failed_words))) * 5.0

            if logic_payload and fail_file and fail_file != "unknown":
                if fail_file in logic_payload:
                    score += 3.0
                if err_detail and err_detail in logic_payload:
                    score += 2.0

            if score > highest_score and score >= 1.5:
                highest_score = score
                best_match = (failed_intent, err_class, err_detail, mitigation)

        if best_match:
            failed_intent, err_class, err_detail, mitigation = best_match
            return True, f"Alert: Matching historical failure detected (similarity {highest_score:.2f}/8.0) for intent '{failed_intent}' -> [{err_class}]: {err_detail}. Mitigation strategy: {mitigation}"
    except Exception as e:
        print(f"[VESICULAR-RUNTIME] Warning: Error checking mitigations: {e}")
    return False, ""

def log_episodic_failure(conn: sqlite3.Connection, intent_str: str, error_output: str) -> str:
    fp = FailureFingerprint.parse_from_traceback(error_output)
    sig = fp.compute_signature()
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S.000000+00:00')
    
    mitigation = "General execution failure. Review traceback details."
    if fp.error_class == "ModuleNotFoundError":
        mitigation = f"Missing python package: {fp.error_detail}. Install dependency or add to isolated environment."
    elif fp.error_class == "PermissionError" or "Operation not permitted" in error_output:
        mitigation = f"macOS Sandbox restriction in '{fp.file}' at line {fp.line}. Update Vesicular intent or add write/read rule to vesicle.sb."
    elif fp.error_class == "NameError":
        mitigation = f"Variable reference error in '{fp.file}' line {fp.line}: {fp.error_detail}. Ensure all variables and modules are defined."
    elif fp.error_class == "FileNotFoundError":
        mitigation = f"File not found: {fp.error_detail}. Confirm target path exists and sandbox permission rules allow access."
    elif fp.error_class == "SyntaxError":
        mitigation = f"Python syntax syntax error in '{fp.file}' line {fp.line}: {fp.error_detail}."

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO episodic_failures (
                signature, intent, error_class, error_detail, failing_file, failing_line, failing_func, 
                error_message, mitigation_payload, exergy_at_failure, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sig, intent_str, fp.error_class, fp.error_detail, fp.file, fp.line, fp.func,
            f"{fp.error_class}: {fp.error_detail[:150]}", mitigation, 0.0, timestamp
        ))
        conn.commit()
        print(f"[VESICULAR-RUNTIME] L3: Causal failure logged. Signature: {sig} (Class: {fp.error_class}, File: {fp.file}:{fp.line})")
        return sig
    except Exception as e:
        print(f"[VESICULAR-RUNTIME] L3 Warning: Failed to log failure: {e}")
        return ""

def run(intent: str, causal_parent: str, requested_by: str, logic_payload: str):
    print(f"[VESICULAR-RUNTIME] Booting bound OS. Intent: {intent}")
    conn = ensure_cortex_db()
    
    found, mitigation_msg = check_episodic_mitigation(conn, intent, logic_payload)
    if found:
        print(f"[VESICULAR-RUNTIME] L3 Mitigation Match: {mitigation_msg}")
        
    cp_hash = write_checkpoint(conn, intent, causal_parent, {"status": "INIT", "requested_by": requested_by})
    print(f"[VESICULAR-RUNTIME] State cross-docked. Hash: {cp_hash}")
    
    output = execute_sandboxed(logic_payload, intent)
    
    if isinstance(output, str) and output.startswith("ERROR: Execution failed"):
        log_episodic_failure(conn, intent, output)
        
    cp_hash_final = write_checkpoint(conn, intent, causal_parent, {"status": "COMPLETE", "output": output})
    print(f"[VESICULAR-RUNTIME] Execution halted. Result checkpointed. Hash: {cp_hash_final}")
    return output

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--list-failures":
        conn = ensure_cortex_db()
        cursor = conn.cursor()
        cursor.execute("SELECT signature, intent, error_class, failing_file, failing_line, error_message, mitigation_payload, timestamp FROM episodic_failures")
        rows = cursor.fetchall()
        failures = []
        for r in rows:
            failures.append({
                "signature": r[0],
                "intent": r[1],
                "error_class": r[2],
                "file": r[3],
                "line": r[4],
                "message": r[5],
                "mitigation": r[6],
                "timestamp": r[7]
            })
        print(json.dumps(failures, indent=2))
        sys.exit(0)
        
    elif len(sys.argv) >= 2 and sys.argv[1] == "--clear-failures":
        conn = ensure_cortex_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM episodic_failures")
        conn.commit()
        print(json.dumps({"ok": True, "message": "All episodic failures purged."}))
        sys.exit(0)

    elif len(sys.argv) >= 2 and sys.argv[1] == "--mitigate":
        if len(sys.argv) < 4:
            print(json.dumps({"error": "Usage: --mitigate <signature> <mitigation_payload>"}))
            sys.exit(1)
        sig = sys.argv[2]
        mitigation = sys.argv[3]
        conn = ensure_cortex_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE episodic_failures SET mitigation_payload = ? WHERE signature = ?", (mitigation, sig))
        conn.commit()
        print(json.dumps({"ok": True, "signature": sig, "mitigation": mitigation}))
        sys.exit(0)

    elif len(sys.argv) >= 2 and sys.argv[1] == "--test":
        print("=== RUNNING VESICULAR EPISODIC MATCHER SELF TEST ===")
        tb_sample = """Traceback (most recent call last):
  File "test_script.py", line 42, in my_function
    x = 1 / 0
ZeroDivisionError: division by zero"""
        fp = FailureFingerprint.parse_from_traceback(tb_sample)
        print(f"Test 1 Error Class: {fp.error_class} (Expected: ZeroDivisionError)")
        print(f"Test 1 File: {fp.file} (Expected: test_script.py)")
        print(f"Test 1 Line: {fp.line} (Expected: 42)")
        print(f"Test 1 Func: {fp.func} (Expected: my_function)")
        sig = fp.compute_signature()
        print(f"Test 1 Signature: {sig}")
        
        conn = ensure_cortex_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM episodic_failures WHERE intent = 'test_division_by_zero_intent'")
        conn.commit()
        
        log_sig = log_episodic_failure(conn, "test_division_by_zero_intent", tb_sample)
        print(f"Test 2 Logged Signature: {log_sig}")
        
        found, msg = check_episodic_mitigation(conn, "run division by zero on my script", "test_script.py")
        print(f"Test 3 Match Found: {found}")
        print(f"Test 3 Message: {msg}")
        
        cursor.execute("DELETE FROM episodic_failures WHERE intent = 'test_division_by_zero_intent'")
        conn.commit()
        
        if fp.error_class == "ZeroDivisionError" and fp.line == 42 and found:
            print("=== SELF TEST STATUS: 3/3 PASSED (OK) ===")
            sys.exit(0)
        else:
            print("=== SELF TEST STATUS: FAILED ===")
            sys.exit(1)

    if len(sys.argv) < 5:
        print("Usage: python run_vesicular.py <intent> <causal_parent> <requested_by> <logic_payload>")
        print("   or: python run_vesicular.py --test")
        print("   or: python run_vesicular.py --list-failures")
        print("   or: python run_vesicular.py --clear-failures")
        print("   or: python run_vesicular.py --mitigate <signature> <mitigation_payload>")
        sys.exit(1)
        
    intent = sys.argv[1]
    causal_parent = sys.argv[2]
    requested_by = sys.argv[3]
    logic_payload = sys.argv[4]
    
    result = run(intent, causal_parent, requested_by, logic_payload)
    print("\n--- Sandbox Output ---")
    print(result)
