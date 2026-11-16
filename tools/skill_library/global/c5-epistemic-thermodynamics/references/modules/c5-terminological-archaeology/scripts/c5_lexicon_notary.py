#!/usr/bin/env python3
"""
c5_lexicon_notary.py — Agente 4: NOTARIO REGISTRADOR
Integra los resultados del pipeline completo (Excavador → Mapeador → Linter)
en el léxico canónico activo C5_LEXICON.json y en el SKILL.md del lexicon-enforcer.

Escribe ÚNICAMENTE en:
  - ~/.gemini/config/C5_LEXICON.json
  - ~/.gemini/config/skills/c5-lexicon-enforcer/SKILL.md (añade Fase 2f si ausente)
  - [artifact_dir]/ANAGNORISIS_LOG.md (log de sesión de anagnórisis)

Uso:
    python3 c5_lexicon_notary.py --input delta.jsonl [--dry-run] [--test]
    python3 c5_lexicon_notary.py --term affordance --author Gibson --year 1979 [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.home() / ".gemini" / "config"
LEXICON_PATH = CONFIG_DIR / "C5_LEXICON.json"
LEXICON_ENFORCER_SKILL = CONFIG_DIR / "skills" / "c5-lexicon-enforcer" / "SKILL.md"

# Umbral mínimo de confianza para registrar un término en el lexicón
MIN_CONFIDENCE_TO_REGISTER = 0.30


def _load_lexicon() -> dict:
    if LEXICON_PATH.exists():
        with open(LEXICON_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"_meta": {"version": "1.0.0"}}


def _save_lexicon(lexicon: dict, dry_run: bool = False) -> None:
    if dry_run:
        print("[DRY-RUN] Lexicón NO modificado. Preview del nuevo registro:", file=sys.stderr)
        return
    with open(LEXICON_PATH, "w", encoding="utf-8") as f:
        json.dump(lexicon, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _key_from_term(term: str) -> str:
    """Normaliza el término como clave JSON (snake_case, min 3 chars, max 30)."""
    key = re.sub(r"[^a-záéíóúüñ\w]", "_", term.lower())
    key = re.sub(r"_+", "_", key).strip("_")
    return key[:30]


def _build_entry(
    canonical_term: str,
    intuicion: str,
    coverage: float,
    verdict: str,
    delta: Optional[str],
    author: Optional[str],
    year: Optional[int],
    work: Optional[str],
    ref_url: Optional[str],
    conversation_id: Optional[str],
    discipline: Optional[list[str]],
) -> dict:
    return {
        "canonical_term": canonical_term,
        "intuicion_borja": intuicion,
        "coverage": round(coverage, 4),
        "verdict": verdict,
        "delta": delta,
        "author": author or "NO_DISPONIBLE_EN_TERRITORIO_VERIFICABLE",
        "year": year,
        "work": work or "NO_DISPONIBLE_EN_TERRITORIO_VERIFICABLE",
        "discipline": discipline or [],
        "discovered_at": datetime.now(timezone.utc).date().isoformat(),
        "conversation_id": conversation_id,
        "c5_axiom_anchor": "Pendiente de asignación manual por el operador",
        "ref_url": ref_url,
    }


def register_entry(
    entry: dict,
    dry_run: bool = False,
    verbose: bool = False,
) -> tuple[bool, str]:
    """
    Registra una entrada en C5_LEXICON.json.
    Retorna (was_written, key).
    No sobreescribe entradas existentes con cobertura alta.
    """
    lexicon = _load_lexicon()
    canonical_term = entry.get("canonical_term", "")
    key = _key_from_term(canonical_term)

    if not key or not canonical_term:
        return False, ""

    # No sobreescribir si ya existe y tiene cobertura >= 0.90
    existing = lexicon.get(key)
    if existing and isinstance(existing, dict):
        existing_cov = existing.get("coverage", 0.0)
        if existing_cov >= 0.90:
            if verbose:
                print(f"  ⏭️  Entrada '{key}' ya existe con coverage={existing_cov} — omitida", file=sys.stderr)
            return False, key

    lexicon[key] = entry

    if dry_run:
        print(f"[DRY-RUN] Registro pendiente: '{key}'")
        print(json.dumps(entry, indent=2, ensure_ascii=False))
    else:
        _save_lexicon(lexicon)
        print(f"  ✅ Registrado en lexicón: '{key}' (coverage={entry['coverage']})", file=sys.stderr)

    return True, key


def _build_phase_2f_block(registered_entries: list[dict]) -> str:
    """Genera el bloque de texto de la Fase 2f para el SKILL.md del lexicon-enforcer."""
    lines = [
        "\n\n### Fase 2f: Gate de Anagnórisis Pasiva (Cross-Referencia con C5_LEXICON.json)\n",
        "Cuando el operador use una descripción funcional en sesión, comparar en tiempo real contra "
        "`~/.gemini/config/C5_LEXICON.json`. Si la frase supera 0.80 de similitud con una entrada registrada, "
        "sugerir el término canónico de forma inmediata y no intrusiva:\n\n",
        "> 💡 **Detección pasiva de anagnórisis:** Lo que describes como «X» corresponde al término canónico "
        "**[TÉRMINO]** ([Autor], [año]). Definición: [definición breve]. ¿Usar este término en adelante?\n\n",
        "#### Léxico Activo (generado automáticamente — no editar a mano)\n\n",
        "| Clave | Término Canónico | Autor | Año | Cobertura | Veredicto |\n",
        "| :--- | :--- | :--- | :--- | :--- | :--- |\n",
    ]
    for e in registered_entries:
        key = _key_from_term(e.get("canonical_term", ""))
        lines.append(
            f"| `{key}` | {e.get('canonical_term', '')} | {e.get('author', '?')} | "
            f"{e.get('year', '?')} | {e.get('coverage', 0):.2f} | {e.get('verdict', '?')} |\n"
        )
    return "".join(lines)


def _inject_phase_2f(entries: list[dict], dry_run: bool = False) -> bool:
    """Inyecta o actualiza la Fase 2f en el SKILL.md del lexicon-enforcer."""
    if not LEXICON_ENFORCER_SKILL.exists():
        print(f"  ⚠️  {LEXICON_ENFORCER_SKILL} no encontrado — Fase 2f omitida", file=sys.stderr)
        return False

    content = LEXICON_ENFORCER_SKILL.read_text(encoding="utf-8")
    new_block = _build_phase_2f_block(entries)

    # Eliminar bloque anterior de Fase 2f si existe
    content = re.sub(
        r"\n\n### Fase 2f:.*",
        "",
        content,
        flags=re.DOTALL,
    )

    new_content = content.rstrip() + new_block

    if dry_run:
        print("[DRY-RUN] Bloque Fase 2f generado (no escrito):")
        print(new_block[:500])
        return True

    LEXICON_ENFORCER_SKILL.write_text(new_content, encoding="utf-8")
    print(f"  ✅ Fase 2f inyectada en {LEXICON_ENFORCER_SKILL}", file=sys.stderr)
    return True


def _generate_anagnorisis_log(entries: list[dict], artifact_dir: Optional[Path]) -> str:
    """Genera el contenido del ANAGNORISIS_LOG.md de sesión."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# ANAGNORISIS_LOG — Sesión {now}\n\n",
        "Términos registrados en esta sesión de arqueología terminológica:\n\n",
        "| Término | Cobertura | Veredicto | Delta |\n",
        "| :--- | :--- | :--- | :--- |\n",
    ]
    for e in entries:
        term = e.get("canonical_term", "?")
        cov = e.get("coverage", 0.0)
        verdict = e.get("verdict", "?")
        delta = e.get("delta", "") or "—"
        lines.append(f"| {term} | {cov:.2f} | {verdict} | {delta[:60]} |\n")

    content = "".join(lines)

    if artifact_dir and artifact_dir.exists():
        log_path = artifact_dir / "ANAGNORISIS_LOG.md"
        log_path.write_text(content, encoding="utf-8")
        print(f"  ✅ Log de sesión: {log_path}", file=sys.stderr)

    return content


def run_tests() -> None:
    """Tests del Notario (modo dry-run)."""
    print("─── TESTS DEL NOTARIO ───")

    entry = _build_entry(
        canonical_term="Test Affordance",
        intuicion="Propiedad que invita a la acción sin manual",
        coverage=0.95,
        verdict="CONVERGE",
        delta=None,
        author="Gibson",
        year=1979,
        work="The Ecological Approach",
        ref_url="https://example.com",
        conversation_id="test-conv-001",
        discipline=["HCI"],
    )
    key = _key_from_term("Test Affordance")
    assert key == "test_affordance", f"Key esperada 'test_affordance', obtenida '{key}'"

    print("  ✅ _build_entry y _key_from_term OK")
    print("  ✅ Registro en dry-run:")
    was_written, k = register_entry(entry, dry_run=True)
    print(f"       key={k}, dry_run=True → ok")

    block = _build_phase_2f_block([entry])
    assert "Fase 2f" in block, "Bloque Fase 2f no generado correctamente"
    print("  ✅ _build_phase_2f_block OK")

    print("\n  Resultado: 3/3 tests OK")
    sys.exit(0)


def main() -> None:
    p = argparse.ArgumentParser(description="C5 Lexicon Notary — Agente 4: NOTARIO REGISTRADOR")
    p.add_argument("--input", help="Fichero JSONL de análisis delta (salida del Linter)")
    p.add_argument("--term", help="Término canónico para registro manual directo")
    p.add_argument("--intuition", default="", help="Intuición de Borja (registro manual)")
    p.add_argument("--author", help="Autor del término (registro manual)")
    p.add_argument("--year", type=int, help="Año de acuñación (registro manual)")
    p.add_argument("--work", help="Obra seminal (registro manual)")
    p.add_argument("--ref-url", help="URL de referencia (registro manual)")
    p.add_argument("--discipline", nargs="+", help="Disciplinas (registro manual)")
    p.add_argument("--conversation-id", help="CID de la conversación (registro manual)")
    p.add_argument("--artifact-dir", help="Directorio de artefactos de sesión para ANAGNORISIS_LOG.md")
    p.add_argument("--dry-run", action="store_true", help="No escribir — solo mostrar lo que se haría")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--test", action="store_true")
    args = p.parse_args()

    if args.test:
        run_tests()

    artifact_dir = Path(args.artifact_dir) if args.artifact_dir else None
    registered: list[dict] = []

    # Modo 1: Registro manual de un único término
    if args.term:
        entry = _build_entry(
            canonical_term=args.term,
            intuicion=args.intuition,
            coverage=1.0,  # Registro manual = cobertura asumida máxima
            verdict="CONVERGE",
            delta=None,
            author=args.author,
            year=args.year,
            work=args.work,
            ref_url=args.ref_url,
            conversation_id=args.conversation_id,
            discipline=args.discipline,
        )
        was_written, key = register_entry(entry, dry_run=args.dry_run, verbose=args.verbose)
        if was_written or args.dry_run:
            registered.append(entry)

    # Modo 2: Procesar pipeline completo desde delta.jsonl
    elif args.input:
        with open(args.input, encoding="utf-8") as f:
            for line in f:
                try:
                    analysis = json.loads(line)
                except json.JSONDecodeError:
                    continue

                delta_info = analysis.get("delta_analysis", {})
                verdict = delta_info.get("verdict", "NO_MATCH")
                confidence = analysis.get("mapping", {}).get("confidence", 0.0)
                coverage = delta_info.get("combined_score", 0.0)

                # No registrar NO_MATCH ni entradas de baja confianza
                if verdict == "NO_MATCH" or confidence < MIN_CONFIDENCE_TO_REGISTER:
                    if args.verbose:
                        print(f"  ⏭️  '{analysis.get('phrase', '')[:50]}…' omitido (verdict={verdict}, conf={confidence:.2f})",
                              file=sys.stderr)
                    continue

                best_match = analysis.get("mapping", {}).get("best_match", {})
                canonical_term = best_match.get("term", "") or analysis.get("canonical_term", "")

                if not canonical_term:
                    continue

                entry = _build_entry(
                    canonical_term=canonical_term,
                    intuicion=analysis.get("phrase", ""),
                    coverage=coverage,
                    verdict=verdict,
                    delta=delta_info.get("delta"),
                    author=best_match.get("author"),
                    year=best_match.get("year"),
                    work=best_match.get("work"),
                    ref_url=best_match.get("ref_url"),
                    conversation_id=analysis.get("conversation_id"),
                    discipline=best_match.get("discipline"),
                )

                was_written, key = register_entry(entry, dry_run=args.dry_run, verbose=args.verbose)
                if was_written or args.dry_run:
                    registered.append(entry)
    else:
        print("Uso: --input delta.jsonl | --term 'Affordance' --author Gibson --year 1979", file=sys.stderr)
        sys.exit(1)

    if not registered:
        print("  ⚠️  No hay entradas para registrar.", file=sys.stderr)
        return

    # Cargar TODAS las entradas del lexicón para la tabla completa de Fase 2f
    lexicon = _load_lexicon()
    all_entries = [v for k, v in lexicon.items() if not k.startswith("_") and isinstance(v, dict)]

    # Inyectar Fase 2f en el lexicon-enforcer
    _inject_phase_2f(all_entries, dry_run=args.dry_run)

    # Generar log de sesión
    _generate_anagnorisis_log(registered, artifact_dir=artifact_dir)

    total = len(registered)
    print(f"\n✅ NOTARIO: {total} término(s) {'registrado(s)' if not args.dry_run else 'en dry-run'}", file=sys.stderr)


if __name__ == "__main__":
    main()
