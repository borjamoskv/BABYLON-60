#!/usr/bin/env python3
"""
[C5-REAL] CORTEX Ouroboros — DVDFi Z3 Verification Orchestrator
================================================================
Runs all DVDFi Z3 verification scripts, collects results, and
generates a consolidated Immunefi evidence bundle with:
  - SHA-256 taint hashes per challenge
  - Aggregate severity assessment
  - CWE taxonomy mapping
  - Attack pattern classification for Immunefi templates

Usage:
  python3 run_all_verifications.py           # Run all
  python3 run_all_verifications.py --json    # Output JSON bundle only
  python3 run_all_verifications.py --target naive_receiver  # Single target
================================================================
"""
import subprocess
import sys
import json
import hashlib
import time
from pathlib import Path

VERIFICATION_DIR = Path(__file__).parent
CHALLENGES = [
    {
        "name": "Unstoppable",
        "script": "unstoppable_verify.py",
        "cwe": ["CWE-682"],
        "pattern": "Invariant Break — Accounting Mismatch",
        "severity": "HIGH",
    },
    {
        "name": "Naive Receiver",
        "script": "naive_receiver_verify.py",
        "cwe": ["CWE-284", "CWE-290"],
        "pattern": "Fee Exhaustion + Meta-TX Identity Forgery",
        "severity": "CRITICAL",
    },
    {
        "name": "Side Entrance",
        "script": "side_entrance_verify.py",
        "cwe": ["CWE-682", "CWE-841"],
        "pattern": "Dual-Accounting Confusion — Deposit as Repayment",
        "severity": "CRITICAL",
    },
    {
        "name": "Truster",
        "script": "truster_verify.py",
        "cwe": ["CWE-20", "CWE-863"],
        "pattern": "Arbitrary External Call — Approval Injection",
        "severity": "CRITICAL",
    },
    {
        "name": "Selfie",
        "script": "selfie_verify.py",
        "cwe": ["CWE-284", "CWE-362"],
        "pattern": "Flash Loan Governance Takeover — TOCTOU",
        "severity": "CRITICAL",
    },
    {
        "name": "The Rewarder",
        "script": "the_rewarder_verify.py",
        "cwe": ["CWE-682", "CWE-841"],
        "pattern": "Multi-Claim Bitmap Race — Transfer Before State Update",
        "severity": "CRITICAL",
    },
]


def run_verification(challenge: dict, verbose: bool = True) -> dict:
    """Execute a single Z3 verification script and capture output."""
    script_path = VERIFICATION_DIR / challenge["script"]

    if not script_path.exists():
        return {
            "name": challenge["name"],
            "status": "MISSING",
            "output": f"Script not found: {script_path}",
            "elapsed": 0,
        }

    t0 = time.time()
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(VERIFICATION_DIR),
        )
        elapsed = time.time() - t0

        output = result.stdout
        status = "PASS" if result.returncode == 0 else "FAIL"

        # Check for SAT confirmations in output
        sat_count = output.count("[!] SAT")
        confirmed = sat_count > 0

        if verbose:
            print(output)
            if result.stderr:
                print(f"  [STDERR] {result.stderr[:200]}", file=sys.stderr)

        return {
            "name": challenge["name"],
            "status": status,
            "confirmed": confirmed,
            "sat_count": sat_count,
            "elapsed": round(elapsed, 3),
            "cwe": challenge["cwe"],
            "pattern": challenge["pattern"],
            "severity": challenge["severity"],
            "output_hash": hashlib.sha256(output.encode()).hexdigest()[:16],
        }

    except subprocess.TimeoutExpired:
        return {
            "name": challenge["name"],
            "status": "TIMEOUT",
            "elapsed": 60,
        }
    except Exception as e:
        return {
            "name": challenge["name"],
            "status": "ERROR",
            "error": str(e),
            "elapsed": time.time() - t0,
        }


def generate_consolidated_bundle(results: list) -> dict:
    """Generate a consolidated Immunefi evidence bundle."""

    # Aggregate CWEs
    all_cwes = set()
    for r in results:
        if "cwe" in r:
            all_cwes.update(r["cwe"])

    # Count confirmations
    confirmed = sum(1 for r in results if r.get("confirmed", False))
    total_sats = sum(r.get("sat_count", 0) for r in results)

    bundle = {
        "meta": {
            "framework": "CORTEX-PERSIST/Ouroboros Z3 Verification Suite",
            "source": "Damn Vulnerable DeFi v4",
            "verification_engine": "Z3 SMT Solver",
            "confidence": "C5-REAL (Symbolic Proof)",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_challenges": len(results),
            "confirmed_vulnerable": confirmed,
            "total_sat_queries": total_sats,
        },
        "cwe_taxonomy": sorted(list(all_cwes)),
        "attack_patterns": {
            "accounting_mismatch": [
                "Unstoppable (direct transfer breaks internal counter)",
                "Side Entrance (deposit-as-repayment creates phantom credits)",
            ],
            "access_control": [
                "Naive Receiver (permissionless flashLoan on behalf of victim)",
                "Truster (arbitrary external call as pool)",
                "Selfie (transient voting power via flash loan)",
            ],
            "state_manipulation": [
                "Naive Receiver (_msgSender forgery via calldata injection)",
                "The Rewarder (transfer before bitmap update)",
            ],
            "temporal": [
                "Selfie (TOCTOU: votes at queue-time, not execute-time)",
            ],
        },
        "immunefi_template_mapping": {
            "CWE-284": "Improper Access Control → Direct theft of funds",
            "CWE-290": "Authentication Bypass by Spoofing → Unauthorized withdrawal",
            "CWE-682": "Incorrect Calculation → Protocol insolvency",
            "CWE-841": "Improper Behavioral Workflow → State corruption",
            "CWE-20":  "Improper Input Validation → Arbitrary code execution context",
            "CWE-863": "Incorrect Authorization → Privilege escalation",
            "CWE-362": "Race Condition (TOCTOU) → Governance takeover",
        },
        "results": results,
    }

    # Compute bundle hash
    bundle_json = json.dumps(bundle, sort_keys=True, default=str)
    bundle["meta"]["bundle_hash"] = hashlib.sha256(bundle_json.encode()).hexdigest()

    return bundle


def print_summary_table(results: list):
    """Print a compact summary table."""
    print(f"\n{'=' * 80}")
    print("  CORTEX Z3 VERIFICATION SUITE — CONSOLIDATED RESULTS")
    print(f"{'=' * 80}")
    print(f"  {'Challenge':<18} | {'Status':<8} | {'SATs':<5} | {'Time':<8} | {'Severity':<10} | Pattern")
    print(f"  {'-'*18} | {'-'*8} | {'-'*5} | {'-'*8} | {'-'*10} | {'-'*30}")

    for r in results:
        status_icon = "✅" if r.get("confirmed") else ("❌" if r["status"] == "FAIL" else "⚠️")
        print(
            f"  {r['name']:<18} | {status_icon} {r['status']:<5} | "
            f"{r.get('sat_count', '-'):<5} | "
            f"{r.get('elapsed', 0):<7.3f}s | "
            f"{r.get('severity', 'N/A'):<10} | "
            f"{r.get('pattern', 'N/A')[:30]}"
        )

    total_time = sum(r.get("elapsed", 0) for r in results)
    confirmed = sum(1 for r in results if r.get("confirmed", False))
    print(f"  {'-'*80}")
    print(f"  Total: {len(results)} challenges | {confirmed} confirmed | {total_time:.3f}s")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    json_only = "--json" in sys.argv
    target = None
    for arg in sys.argv[1:]:
        if arg.startswith("--target="):
            target = arg.split("=")[1]
        elif arg == "--target" and sys.argv.index(arg) + 1 < len(sys.argv):
            target = sys.argv[sys.argv.index(arg) + 1]

    # Filter challenges if target specified
    challenges = CHALLENGES
    if target:
        challenges = [c for c in CHALLENGES if target.lower().replace("_", " ") in c["name"].lower()
                      or target.lower().replace(" ", "_") in c["script"].lower()]
        if not challenges:
            print(f"[!] No challenge matching '{target}'. Available:")
            for c in CHALLENGES:
                print(f"    - {c['name']} ({c['script']})")
            sys.exit(1)

    if not json_only:
        print("=" * 80)
        print("  CORTEX OUROBOROS — Z3 FORMAL VERIFICATION SUITE")
        print(f"  Challenges: {len(challenges)} | Engine: Z3 SMT | Confidence: C5-REAL")
        print("=" * 80)

    # Execute all verifications
    results = []
    for challenge in challenges:
        if not json_only:
            print(f"\n{'─' * 80}")
            print(f"  ▶ Running: {challenge['name']} ({challenge['script']})")
            print(f"{'─' * 80}")

        result = run_verification(challenge, verbose=not json_only)
        results.append(result)

    # Generate consolidated bundle
    bundle = generate_consolidated_bundle(results)

    if json_only:
        print(json.dumps(bundle, indent=2, default=str))
    else:
        print_summary_table(results)

        # Write bundle to file
        bundle_path = VERIFICATION_DIR / "immunefi_evidence_bundle.json"
        with open(bundle_path, "w") as f:
            json.dump(bundle, f, indent=2, default=str)
        print(f"\n  📦 Evidence bundle written to: {bundle_path}")
        print(f"  🔑 Bundle hash: {bundle['meta']['bundle_hash'][:24]}...")
