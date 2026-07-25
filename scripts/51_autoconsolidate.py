# C5-REAL EXERGY CERTIFIED
"""C5-REAL Autoconsolidator script for conversation logs."""

import os
import json
import glob
import datetime

BRAIN_DIR: str = os.environ.get("CORTEX_BRAIN_DIR", "")
if not BRAIN_DIR:
    raise RuntimeError("CORTEX_BRAIN_DIR env var is required (Ω23).")

ARTIFACT_DIR = os.path.join(os.getcwd(), "artifacts")


def consolidate_conversations() -> None:
    """Scans conversation transcripts in BRAIN_DIR and generates a consolidated markdown ledger."""
    print("[C5-REAL] Iniciando Autoconsolidación de Conversaciones-Ω...")
    os.makedirs(ARTIFACT_DIR, exist_ok=True)

    transcripts = glob.glob(
        os.path.join(BRAIN_DIR, "**", "transcript.jsonl"), recursive=True
    )
    total_steps = 0
    anergy_purged = 0
    extracted_axioms = []

    # Scaneamos los logs de la sesión
    for t_path in transcripts:
        try:
            with open(t_path, "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    total_steps += 1
                    content = data.get("content", "")
                    if (
                        "[ARTIFACT:" in content
                        or "Claim:" in content
                        or "C5-REAL" in content
                    ):
                        extracted_axioms.append(
                            f"- [ {data.get('created_at')} ] {content[:150]}..."
                        )
                    if "Error" in content or "failed" in content:
                        anergy_purged += 1
        except (json.JSONDecodeError, OSError):
            continue

    ledger_path = os.path.join(
        ARTIFACT_DIR,
        f"c5_consolidation_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.md",
    )

    with open(ledger_path, "w", encoding="utf-8") as out:
        out.write("# 🏛️ C5-REAL MASTER CONSOLIDATION LEDGER\n")
        out.write(f"**Timestamp:** {datetime.datetime.now().isoformat()}Z\n")
        out.write(f"**Total Steps Analizados:** {total_steps}\n")
        out.write(f"**Anergía Purgada (Errores asimilados):** {anergy_purged}\n\n")
        out.write("## 🧬 Axiomas Extraídos (Invariantes C5-REAL)\n")
        for ax in extracted_axioms[-50:]:  # Last 50 meaningful steps
            out.write(f"{ax}\n")

    print(f"[SUCCESS] Consolidación cristalizada en: {ledger_path}")


if __name__ == "__main__":
    consolidate_conversations()
