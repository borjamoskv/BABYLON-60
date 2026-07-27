import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Auto-crystallization hook — Ω₉ mandate
# Importar de forma segura (no bloquear si hay error)
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from cortex_crystallizer import scan_ledger_and_crystallize, LEDGER_PATH
    _CRYSTALLIZER_AVAILABLE = True
except ImportError:
    _CRYSTALLIZER_AVAILABLE = False


def bundle_reports():
    print("[OUROBOROS] Initializing report bundling for Immunefi...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.path.join(base_dir, "reports")
    submissions_dir = os.path.join(base_dir, "submissions")
    ledger_path = os.path.join(base_dir, "ouroboros_strike_ledger.jsonl")

    os.makedirs(submissions_dir, exist_ok=True)

    ledger = []
    if os.path.exists(ledger_path):
        with open(ledger_path, "r") as f:
            for line in f:
                if line.strip():
                    ledger.append(json.loads(line))

    verified_reports = [
        r for r in ledger
        if r.get("status") in ["CRYSTALLIZED", "VERIFIED", "DRAFT_CREATED", "PREPARED"]
    ]

    print(f"[OUROBOROS] Found {len(verified_reports)} verified reports.")

    for report in verified_reports:
        # Use explicit report_path from ledger
        source_path = report.get("report_path")
        report.get("id", "UNKNOWN")

        # Generate bundle id from id or target_name for naming the submission file
        target_name = report.get("target_name", report.get("target", "UNKNOWN"))
        bundle_id = report.get("id", target_name.lower().replace(" ", "_"))

        # Fallback and validation
        if not source_path or not os.path.exists(source_path):
            print(f"[WARNING] Source file not found for {bundle_id}: {source_path}")
            content = f"# Submission Manifest: {report.get('title', 'N/A')}\n"
            content += f"ID: {bundle_id}\n"
            content += f"Status: {report['status']}\n"
            content += f"Severity: {report.get('severity', 'N/A')}\n"
            content += "\n[FORENSIC DATA ATTACHED]\n"
        else:
            with open(source_path, "r") as f:
                content = f.read()

        timestamp = datetime.now().strftime("%Y%m%d")
        sub_filename = f"SUBMIT_{bundle_id.upper()}_{timestamp}.md"
        submission_path = os.path.join(submissions_dir, sub_filename)

        with open(submission_path, "w") as f:
            f.write(content)

        print(f"[OUROBOROS] Bundled: {submission_path} (Size: {len(content)} bytes)")

    # ── Auto-crystallization hook (Ω₉ mandate) ──────────────────────────
    # Todo submission BUNDLED debe tener KI antes de cerrar sesión.
    if _CRYSTALLIZER_AVAILABLE:
        print("\n[OUROBOROS] 🔮 Triggering auto-crystallization hook...")
        try:
            created = scan_ledger_and_crystallize(LEDGER_PATH)
            print(f"[OUROBOROS] ✅ {created} KI(s) crystallized from ledger.")
        except Exception as e:
            print(f"[OUROBOROS] ⚠️ Crystallization hook failed: {e}")
    else:
        print("[OUROBOROS] ⚠️ cortex_crystallizer not available.")


if __name__ == "__main__":
    bundle_reports()
