#!/usr/bin/env python3
"""
c5_orphan_phrase_detector.py — Agente 1: EXCAVADOR
Detecta perífrasis huérfanas en transcripts y sesiones de Antigravity IDE.
Una "perífrasis huérfana" es una descripción funcional de ≥7 palabras que captura
un mecanismo sistémico, dinámico o físico SIN usar el término técnico canónico.

Uso:
    python3 c5_orphan_phrase_detector.py [--input <texto>] [--transcript <path>] [--session-dir <brain_dir>] [--since YYYY-MM-DD]
    python3 c5_orphan_phrase_detector.py --test

Salida: candidatos.jsonl en el directorio de trabajo.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

# ─── Términos canónicos ya conocidos ────────────────────────────────────────────
# Si uno de estos aparece en la frase → ya está bautizado, NO es candidato.
KNOWN_CANONICAL_TERMS: list[str] = [
    "exergía", "anergía", "affordance", "afordancia", "manta de markov",
    "markov blanket", "chentsov", "fisher-rao", "landauer", "stigmergia",
    "stigmergy", "kudurru", "bisimulación", "bisimulation", "ergodicidad",
    "ergodicity", "autopoiesis", "umwelt", "goodhart", "campbell",
    "cambio 2", "second-order change", "señalización costosa", "costly signaling",
    "handicap principle", "zahavi", "watzlawick", "ashby", "requisite variety",
    "ley de variedad requerida", "shannon", "kolmogorov", "kullback-leibler",
    "bateson", "friston", "free energy principle", "homeostasis", "alostasis",
    "pareto", "zipf", "power law", "histéresis", "histeresis",
]
KNOWN_RE = re.compile("|".join(re.escape(t) for t in KNOWN_CANONICAL_TERMS), re.IGNORECASE)

# ─── Patrones de perífrasis sistémica huérfana ──────────────────────────────────
# Cada patrón captura una descripción funcional sin término técnico de raíz.
# Grupos nombrados: 'phrase' = texto capturado como candidato.
ORPHAN_PATTERNS: list[tuple[str, str]] = [
    # Mecanismos relacionales agente-entorno (→ affordance)
    (r"(?P<phrase>(?:una? )?\w[\w\s]{6,60}(?:invita|sugiere|obliga|empuja|permite)\w*\s+\w[\w\s]{3,40}sin[\w\s]{3,40}(?:manual|instruccione?s|leer|conocer))",
     "relacion_agente_entorno"),
    # Dinámicas de escalada / bucle de retroalimentación (→ cambio 2 / watzlawick)
    (r"(?P<phrase>(?:cuanto|mientras)\s+(?:m[aá]s|menos)[\w\s,;\.]{4,80}(?:peor|mejor|m[aá]s|mayor|menos)[\w\s,;\.]{3,60})",
     "escalada_retroalimentacion"),
    # Coordinación sin canal directo (→ stigmergy)
    (r"(?P<phrase>\w[\w\s]{5,50}(?:coordinan|organizan|sincronizan)\w*\s+sin\s+\w[\w\s]{3,40}(?:hablar(?:se)?|comunicar(?:se)?|reunirse?|mensaje))",
     "coordinacion_sin_canal"),
    # Coste termodinámico del pensamiento (→ landauer)
    (r"(?P<phrase>(?:borrar|cambiar de contexto|pensar|depurar)\w*\s+\w[\w\s]{3,50}(?:disipa|genera|consume|cuesta)\w*\s+\w[\w\s]{2,30}(?:calor|energía|energía|recursos físicos))",
     "coste_termico_cognitivo"),
    # Diferencia entre promedio grupal y trayectoria individual (→ ergodicity)
    (r"(?P<phrase>(?:el promedio|la media|lo que pasa a muchos|estadística del grupo)\w*\s+(?:no|nunca|jamás)\s+\w[\w\s]{4,60}(?:un solo|un individuo|a ti|tu trayectoria))",
     "no_ergodicidad"),
    # Señal barata vs señal costosa (→ costly signaling)
    (r"(?P<phrase>(?:palabras?|promesas?|declaraciones?|intenciones?)\w*\s+(?:no valen|valen menos|no significan|son baratas?|son cheap)\w*\s+(?:sin|que)\s+\w[\w\s]{4,50}(?:coste|costo|riesgo|sacrificio|prueba|evidencia))",
     "senal_barata_vs_costosa"),
    # Fracción útil vs fracción inútil de energía o esfuerzo (→ exergia/anergia)
    (r"(?P<phrase>(?:parte|fracción|porción|trozo)\s+(?:del|de la|del)\s+\w[\w\s]{3,50}(?:que (?:sirve|produce|genera|avanza|construye)|útil|productiva?)\s+(?:vs?\.?|versus|frente a|contra)\s+\w[\w\s]{3,50}(?:que no|inútil|muerta?|desperdiciada?|burocrática?))",
     "fraccion_util_vs_inutil"),
    # Cada agente vive en una burbuja perceptual diferente (→ umwelt)
    (r"(?P<phrase>(?:no (?:ven|perciben|experimentan|procesan)|viven en)\w*\s+\w[\w\s]{4,60}(?:realidad|mundo|entorno|contexto)\w*\s+(?:diferente|distinto|otro|propio|su propio))",
     "burbuja_perceptual"),
    # Métrica que deja de medir lo que importaba al volverse objetivo (→ goodhart)
    (r"(?P<phrase>cuando\s+\w[\w\s]{3,50}(?:métrica|indicador|kpi|objetivo)\w*\s+(?:se convierte|se vuelve|pasa a ser)\w*\s+\w[\w\s]{3,40}(?:dejas? de|ya no|pierde)\w*\s+\w[\w\s]{3,30}(?:medir|reflejar|capturar))",
     "metrica_que_se_destruye"),
    # Descripciones genéricas de términos técnicos ausentes (comodín)
    (r"(?P<phrase>(?:eso que pasa cuando|lo que ocurre es que|la tendencia (?:de los sistemas?|del sistema) a|cuando un sistema|el hecho de que)\s+.{15,120})",
     "descripcion_generica_comodin"),
]
ORPHAN_RES: list[tuple[re.Pattern, str]] = [
    (re.compile(p, re.IGNORECASE | re.DOTALL), label)
    for p, label in ORPHAN_PATTERNS
]

# ─── Ventana mínima de palabras para considerar candidato ───────────────────────
MIN_WORDS = 7


def _is_known(text: str) -> bool:
    """True si el texto ya contiene un término canónico conocido."""
    return bool(KNOWN_RE.search(text))


def _is_long_enough(text: str) -> bool:
    return len(text.split()) >= MIN_WORDS


def scan_text(text: str, source_id: str = "inline") -> list[dict]:
    """Escanea texto libre y devuelve candidatos con metadatos."""
    candidates = []
    for compiled, label in ORPHAN_RES:
        for m in compiled.finditer(text):
            phrase = m.group("phrase").strip()
            if not _is_long_enough(phrase):
                continue
            if _is_known(phrase):
                continue
            # Contexto: ±100 chars alrededor del match
            start = max(0, m.start() - 100)
            end = min(len(text), m.end() + 100)
            context = text[start:end].replace("\n", " ")
            candidates.append({
                "phrase": phrase,
                "signal_type": label,
                "context": context,
                "source_id": source_id,
                "scanned_at": datetime.now(timezone.utc).isoformat(),
            })
    return candidates


def scan_transcript(path: Path) -> Iterator[dict]:
    """Escanea un transcript.jsonl del brain de Antigravity."""
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                step = json.loads(line)
            except json.JSONDecodeError:
                continue
            # Solo procesar inputs explícitos del operador (USER_INPUT, USER_EXPLICIT)
            if step.get("source") not in ("USER_INPUT", "USER_EXPLICIT"):
                continue
            content = step.get("content", "")
            if not content:
                continue
            created_at = step.get("created_at", "")
            step_idx = step.get("step_index", 0)
            source_id = f"{path.parent.parent.name}:step_{step_idx}@{created_at}"
            for cand in scan_text(content, source_id=source_id):
                cand["created_at"] = created_at
                cand["step_index"] = step_idx
                cand["conversation_id"] = path.parent.parent.name
                yield cand


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="C5 Orphan Phrase Detector — Agente 1: EXCAVADOR")
    p.add_argument("--input", help="Texto libre a escanear directamente")
    p.add_argument("--transcript", help="Ruta a un transcript.jsonl específico")
    p.add_argument("--session-dir", default=str(Path.home() / ".gemini/antigravity/brain"),
                   help="Directorio raíz del brain de Antigravity")
    p.add_argument("--since", default="2025-12-01", help="Fecha desde (YYYY-MM-DD)")
    p.add_argument("--output", default="candidatos.jsonl", help="Fichero de salida JSONL")
    p.add_argument("--test", action="store_true", help="Ejecutar tests de verificación internos")
    return p.parse_args()


def run_tests() -> None:
    """Tests de verificación internos para CI."""
    print("─── TESTS DE VERIFICACIÓN ───")
    cases = [
        {
            "text": "Una puerta que invita a tirar sin necesitar un manual de instrucciones",
            "expect_hit": True,
            "label": "Test affordance (relacion_agente_entorno)",
        },
        {
            "text": "Cuanto más intentamos solucionar el problema, peor se pone la situación",
            "expect_hit": True,
            "label": "Test cambio 2 (escalada_retroalimentacion)",
        },
        {
            "text": "Las afordancias de Gibson describen exactamente esto",
            "expect_hit": False,
            "label": "Test ya-conocido (debe filtrar affordance)",
        },
        {
            "text": "Eso que pasa cuando un sistema comienza a autorregularse sin ningún controlador central definido",
            "expect_hit": True,
            "label": "Test comodín genérico",
        },
    ]
    passed = 0
    for c in cases:
        results = scan_text(c["text"])
        hit = len(results) > 0
        ok = hit == c["expect_hit"]
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status}: {c['label']}")
        if ok:
            passed += 1
        else:
            print(f"       texto: {c['text'][:80]}")
            print(f"       esperado hit={c['expect_hit']}, obtenido hit={hit}")
    print(f"\n  Resultado: {passed}/{len(cases)} tests OK")
    sys.exit(0 if passed == len(cases) else 1)


def main() -> None:
    args = _parse_args()

    if args.test:
        run_tests()

    candidates: list[dict] = []

    # Modo 1: Texto libre inline
    if args.input:
        candidates.extend(scan_text(args.input, source_id="cli_input"))

    # Modo 2: Transcript individual
    elif args.transcript:
        for cand in scan_transcript(Path(args.transcript)):
            candidates.append(cand)

    # Modo 3: Escaneo del brain completo desde --since
    else:
        since_dt = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)
        brain_dir = Path(args.session_dir)
        transcripts = sorted(glob.glob(str(brain_dir / "*/.system_generated/logs/transcript.jsonl")))
        print(f"🔍 Escaneando {len(transcripts)} transcripts desde {args.since}…", file=sys.stderr)
        n_conv = 0
        for t_path in transcripts:
            for cand in scan_transcript(Path(t_path)):
                ts = cand.get("created_at", "")
                if ts:
                    try:
                        if datetime.fromisoformat(ts.replace("Z", "+00:00")) < since_dt:
                            continue
                    except ValueError:
                        pass
                candidates.append(cand)
            n_conv += 1
        print(f"   Conversaciones procesadas: {n_conv}", file=sys.stderr)

    # Deduplicación por frase normalizada
    seen: set[str] = set()
    unique: list[dict] = []
    for c in candidates:
        key = re.sub(r"\s+", " ", c["phrase"].lower().strip())
        if key not in seen:
            seen.add(key)
            unique.append(c)

    # Escritura de salida
    out_path = Path(args.output)
    with open(out_path, "w", encoding="utf-8") as f:
        for c in unique:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"✅ {len(unique)} candidatos detectados → {out_path}", file=sys.stderr)
    for c in unique[:5]:
        print(f"   [{c['signal_type']}] {c['phrase'][:80]}…", file=sys.stderr)
    if len(unique) > 5:
        print(f"   … y {len(unique) - 5} más.", file=sys.stderr)


if __name__ == "__main__":
    main()
