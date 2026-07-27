"""
CORTEX Auto-Crystallization Hook — Ouroboros Post-Submission Engine
================================================================
Dispara automáticamente la cristalización de KIs al detectar status SUBMITTED
en el ouroboros_strike_ledger.jsonl.

Uso:
  from cortex_crystallizer import auto_crystallize_submission
  auto_crystallize_submission(ledger_entry)

O en modo CLI para procesar el ledger completo:
  python3 cortex_crystallizer.py --scan-ledger

Ley Ω₉: C5-REAL. Todo submission SUBMITTED debe tener KI antes de cerrar sesión.
"""

import json
import os
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Paths ───────────────────────────────────────────────────────────────
KNOWLEDGE_BASE = Path(os.path.expanduser("~/.gemini/antigravity/knowledge"))
LEDGER_PATH = Path(__file__).parent / "ouroboros_strike_ledger.jsonl"
REPORTS_DIR = Path(__file__).parent / "reports"
SUBMISSIONS_DIR = Path(__file__).parent / "submissions"


def _ki_slug(target: str, platform: str) -> str:
    """Genera slug determinístico para el KI desde target + platform."""
    raw = f"{target}_{platform}".lower()
    slug = re.sub(r"[^a-z0-9_]", "_", raw)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return f"bounty_{slug}_ki"


def _extract_summary_from_report(report_path: Path, max_chars: int = 400) -> str:
    """Extrae el resumen ejecutivo del reporte markdown."""
    if not report_path.exists():
        return "Report file not found at time of crystallization."
    text = report_path.read_text(encoding="utf-8", errors="ignore")
    # Buscar primer bloque de contenido significativo
    lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("#")]
    summary = " ".join(lines)[:max_chars]
    return summary if summary else text[:max_chars]


def _ki_exists(slug: str) -> bool:
    """Verifica si el KI ya existe en el knowledge base."""
    return (KNOWLEDGE_BASE / slug / "metadata.json").exists()


def auto_crystallize_submission(entry: dict) -> Optional[Path]:
    """
    Cristaliza automáticamente un ledger entry con status SUBMITTED o DRAFT_CREATED.
    
    Args:
        entry: Dict del ledger JSONL con keys: target_name, platform, severity,
               title, report_path, status, timestamp, etc.
    
    Returns:
        Path al KI creado, o None si ya existía o se omitió.
    """
    status = entry.get("status", "")
    if status not in ("SUBMITTED", "DRAFT_CREATED", "PREPARED"):
        return None

    target = entry.get("target") or entry.get("target_name") or "unknown"
    platform = entry.get("platform", "immunefi")
    severity = entry.get("severity", "?")
    title = entry.get("title", target)
    timestamp = entry.get("timestamp", datetime.now(timezone.utc).isoformat())
    report_path_str = entry.get("report_path", "")
    report_path = Path(report_path_str) if report_path_str else None
    
    intent_id = entry.get("intent_id", "")
    chain_id = entry.get("chain_id", "unknown")
    strike_id = entry.get("id", "")

    slug = _ki_slug(target, platform)

    # Skip si ya existe
    if _ki_exists(slug):
        print(f"[CRYSTALLIZER] ⏩ KI already exists: {slug}")
        return None

    # Crear estructura KI
    ki_dir = KNOWLEDGE_BASE / slug
    artifacts_dir = ki_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Extraer summary del reporte
    summary = _extract_summary_from_report(report_path) if report_path else title

    # Policy Decision Record (PDR) Generation
    pdr = {
        "pdr_version": "1.0",
        "strike_id": strike_id,
        "intent_id": intent_id,
        "chain_id": chain_id,
        "decision": "STRIKE",
        "rationale": f"Verified vulnerability in {target} via Ouroboros Pipeline.",
        "verifier": "CORTEX-Inference-Ω",
        "verification_method": entry.get("confidence", "C4-Simulated"),
        "timestamp": timestamp,
        "proof_hashes": [hashlib.sha256(summary.encode()).hexdigest()]
    }
    pdr_path = artifacts_dir / "pdr.json"
    pdr_path.write_text(json.dumps(pdr, indent=2))

    # metadata.json
    metadata = {
        "title": f"{target} — Bounty Strike ({severity.upper()})",
        "created_at": timestamp,
        "summary": summary,
        "intent_id": intent_id,
        "chain_id": chain_id,
        "references": [
            str(report_path) if report_path else "",
            str(SUBMISSIONS_DIR / f"SUBMIT_{entry.get('target', '').upper().replace(' ', '_')}_*.md"),
        ],
        "tags": [
            target.lower().replace(" ", "_"),
            platform,
            severity.lower(),
            "bounty",
            "c5-real",
            status.lower(),
        ],
        "confidence": entry.get("confidence", "C5-REAL"),
        "capital_vector": "V1-BugBounty",
        "platform": platform,
        "status": status,
        "auto_crystallized": True,
        "ledger_taint": entry.get("id", ""),
        "pdr_hash": hashlib.sha256(json.dumps(pdr).encode()).hexdigest()
    }

    metadata_path = ki_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))

    # artifacts/overview.md — auto-generado desde reporte
    if report_path and report_path.exists():
        report_content = report_path.read_text(encoding="utf-8", errors="ignore")
        overview_content = f"""# {title}
> **Auto-crystallized:** {timestamp} · **Status:** {status} · **Severity:** {severity}
> **Platform:** {platform} · **Confidence:** C5-REAL

## Source Report
```
{report_path}
```

---

{report_content[:3000]}

---
*Auto-crystallized by CORTEX Ouroboros Post-Submission Hook v1.0*
*Ω₉: Todo submission SUBMITTED debe tener KI. Esta es la verdad.*
"""
    else:
        overview_content = f"""# {title}
> **Auto-crystallized:** {timestamp} · **Status:** {status}
> Report path not found: `{report_path_str}`

## Ledger Entry
```json
{json.dumps(entry, indent=2, ensure_ascii=False)}
```
"""

    (artifacts_dir / "overview.md").write_text(overview_content, encoding="utf-8")

    print(f"[CRYSTALLIZER] ✅ KI cristalizado: {slug}")
    print(f"               📁 {ki_dir}")
    return ki_dir


def scan_ledger_and_crystallize(ledger_path: Path = LEDGER_PATH) -> int:
    """
    Escanea el ledger completo y cristaliza todos los entries sin KI.
    
    Returns:
        Número de KIs creados.
    """
    if not ledger_path.exists():
        print(f"[CRYSTALLIZER] ❌ Ledger no encontrado: {ledger_path}")
        return 0

    created = 0
    seen_slugs = set()

    with open(ledger_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            target = entry.get("target") or entry.get("target_name") or ""
            platform = entry.get("platform", "immunefi")
            slug = _ki_slug(target, platform)

            # Deduplicar (mismo target puede aparecer varias veces en ledger)
            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)

            result = auto_crystallize_submission(entry)
            if result is not None:
                created += 1

    print(f"\n[CRYSTALLIZER] 🔮 Cristalización completada: {created} KIs nuevos creados.")
    return created


def update_ledger_entry_status(
    ledger_path: Path,
    taint: str,
    new_status: str,
) -> bool:
    """Actualiza status en ledger JSONL por taint hash o id."""
    if not ledger_path.exists():
        return False

    lines = ledger_path.read_text().splitlines()
    updated = False
    new_lines = []

    for line in lines:
        try:
            entry = json.loads(line)
            if entry.get("taint") == taint or entry.get("id") == taint:
                entry["status"] = new_status
                entry["crystallized_at"] = datetime.now(timezone.utc).isoformat()
                new_lines.append(json.dumps(entry))
                updated = True
            else:
                new_lines.append(line)
        except json.JSONDecodeError:
            new_lines.append(line)

    if updated:
        ledger_path.write_text("\n".join(new_lines) + "\n")

    return updated


if __name__ == "__main__":
    import sys

    if "--scan-ledger" in sys.argv:
        print("=== CORTEX Auto-Crystallizer ===")
        print(f"Ledger: {LEDGER_PATH}")
        print(f"Knowledge Base: {KNOWLEDGE_BASE}")
        print()
        n = scan_ledger_and_crystallize()
        sys.exit(0 if n >= 0 else 1)

    elif "--entry" in sys.argv:
        # Modo: echo '{"target_name": "...", ...}' | python3 cortex_crystallizer.py --entry
        raw = sys.stdin.read().strip()
        entry = json.loads(raw)
        result = auto_crystallize_submission(entry)
        print(f"Result: {result}")

    else:
        print(__doc__)
        print("\nUso:")
        print("  python3 cortex_crystallizer.py --scan-ledger    # Procesa ledger completo")
        print("  echo '{...}' | python3 cortex_crystallizer.py --entry  # Procesa 1 entry")
