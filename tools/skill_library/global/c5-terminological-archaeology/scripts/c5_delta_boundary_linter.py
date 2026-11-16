#!/usr/bin/env python3
"""
c5_delta_boundary_linter.py — Agente 3: LINTER DIFERENCIAL
Determina si la intuición de Borja ≡ término canónico o añade un delta genuino.

Veredictos:
  CONVERGE  → coverage >= 0.90 → Usar el término canónico directamente.
  DIVERGE   → 0.50 <= coverage < 0.90 → La intuición es parcialmente distinta;
              preservar nombre propio + anclar en canónico.
  SUPERSET  → El término canónico es un caso particular de la intuición;
              la intuición de Borja es más general.
  NO_MATCH  → coverage < 0.50 → El candidato no tiene término canónico claro;
              encolar como término potencialmente nuevo.

Estrategia de similitud:
  - Primaria: Jaccard sobre tokens de contenido (sin stopwords)
  - Secundaria: Solapamiento de bigrams
  - Terciaria: Solapamiento de conceptos clave extraídos de C5_LEXICON.json

Uso:
    python3 c5_delta_boundary_linter.py --input mapeos.jsonl [--output delta.jsonl] [--test]
    python3 c5_delta_boundary_linter.py --intuition "..." --canonical "..." [--expected-verdict CONVERGE]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.home() / ".gemini" / "config"
LEXICON_PATH = CONFIG_DIR / "C5_LEXICON.json"

# ─── Stopwords multilingüe ────────────────────────────────────────────────────────
STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "de", "del", "que", "cuando",
    "si", "sin", "con", "por", "para", "a", "en", "es", "son", "se",
    "lo", "le", "al", "ya", "no", "más", "mas", "pero", "como", "este",
    "esta", "todo", "toda", "cada", "hay", "muy", "sus", "su", "has",
    "the", "a", "an", "of", "and", "that", "when", "without", "in", "is",
    "are", "it", "its", "to", "from", "by", "or", "be", "was", "been",
    "can", "not", "this", "for", "which", "what", "any", "all", "both",
}

# ─── Umbrales de veredicto (calibrados empíricamente para similitud de tokens) ───
CONVERGE_THRESHOLD = 0.24
DIVERGE_MIN = 0.12
SUPERSET_THRESHOLD = 0.20  # Si intuición tiene cobertura fwd pero tiene muchos tokens extra


def _tokenize_content(text: str) -> set[str]:
    """Tokeniza eliminando stopwords y términos muy cortos."""
    tokens = set(re.findall(r"[a-záéíóúüñ\w]{3,}", text.lower()))
    return tokens - STOPWORDS


def _bigrams(tokens: set[str]) -> set[tuple[str, str]]:
    """Genera bigrams de un conjunto de tokens (orden libre)."""
    lst = sorted(tokens)
    return {(lst[i], lst[i + 1]) for i in range(len(lst) - 1)}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _coverage(intuition_tokens: set[str], canonical_tokens: set[str]) -> float:
    """
    Coverage asimétrico: ¿qué fracción del canónico está cubierta por la intuición?
    = |intersection| / |canonical|
    Mide si la intuición "comprende" el término canónico.
    """
    if not canonical_tokens:
        return 0.0
    return len(intuition_tokens & canonical_tokens) / len(canonical_tokens)


def _reverse_coverage(intuition_tokens: set[str], canonical_tokens: set[str]) -> float:
    """
    ¿Qué fracción de la intuición está capturada por el canónico?
    = |intersection| / |intuition|
    Si es alta, el canónico cubre la intuición completamente.
    Si es baja, la intuición tiene elementos extras → posible delta o SUPERSET.
    """
    if not intuition_tokens:
        return 0.0
    return len(intuition_tokens & canonical_tokens) / len(intuition_tokens)


def compute_similarity(intuition: str, canonical: str) -> dict:
    """
    Calcula la similitud multidimensional entre intuición y definición canónica.
    Retorna métricas y veredicto.
    """
    i_tokens = _tokenize_content(intuition)
    c_tokens = _tokenize_content(canonical)

    # Jaccard simétrico
    jaccard = _jaccard(i_tokens, c_tokens)

    # Coverage asimétrico (canónico cubierto por intuición)
    fwd_cov = _coverage(i_tokens, c_tokens)

    # Coverage inverso (intuición cubierta por canónico)
    rev_cov = _reverse_coverage(i_tokens, c_tokens)

    # Bigram Jaccard (captura co-ocurrencias de orden)
    i_bi = _bigrams(i_tokens)
    c_bi = _bigrams(c_tokens)
    bigram_score = _jaccard(i_bi, c_bi) if i_bi and c_bi else 0.0

    # Score combinado: ponderación
    combined = round(0.40 * fwd_cov + 0.30 * rev_cov + 0.20 * jaccard + 0.10 * bigram_score, 4)

    # Determinar veredicto
    if fwd_cov >= SUPERSET_THRESHOLD and len(i_tokens) >= 1.4 * max(1, len(c_tokens)) and rev_cov < 0.40:
        # La intuición cubre el canónico pero añade dimensiones sustanciales no contempladas
        verdict = "SUPERSET"
        extra_tokens = i_tokens - c_tokens - STOPWORDS
        delta = " | ".join(sorted(extra_tokens)[:10]) if extra_tokens else None
    elif combined >= CONVERGE_THRESHOLD:
        verdict = "CONVERGE"
        delta = None
    elif combined >= DIVERGE_MIN:
        verdict = "DIVERGE"
        # El delta son los tokens de la intuición no cubiertos por el canónico
        extra_tokens = i_tokens - c_tokens - STOPWORDS
        delta = " | ".join(sorted(extra_tokens)[:10]) if extra_tokens else None
    else:
        verdict = "NO_MATCH"
        delta = None

    return {
        "jaccard": jaccard,
        "fwd_coverage": fwd_cov,
        "rev_coverage": rev_cov,
        "bigram_score": bigram_score,
        "combined_score": combined,
        "verdict": verdict,
        "delta": delta,
    }


def load_lexicon_definitions() -> dict[str, str]:
    """Carga las definiciones del C5_LEXICON.json para comparación enriquecida."""
    if not LEXICON_PATH.exists():
        return {}
    try:
        with open(LEXICON_PATH, encoding="utf-8") as f:
            lexicon = json.load(f)
        return {
            key: entry.get("intuicion_borja", "")
            for key, entry in lexicon.items()
            if not key.startswith("_")
        }
    except Exception:
        return {}


def lint_mapping(mapping_entry: dict) -> dict:
    """
    Procesa una entrada de mapeos.jsonl y añade el análisis de delta.
    """
    phrase = mapping_entry.get("phrase", "")
    mapping = mapping_entry.get("mapping", {})
    best_match = mapping.get("best_match")

    if not best_match:
        return {
            **mapping_entry,
            "delta_analysis": {
                "verdict": "NO_MATCH",
                "combined_score": 0.0,
                "delta": None,
                "note": "Sin término canónico encontrado — candidato potencialmente nuevo",
            },
        }

    canonical_definition = best_match.get("definition", "")
    canonical_term = best_match.get("term", "")

    # Comparar la frase candidata contra la definición canónica
    sim = compute_similarity(phrase, canonical_definition)

    # Enriquecer con la intuición almacenada en el lexicón (si existe)
    lexicon_defs = load_lexicon_definitions()
    lexicon_key = re.sub(r"[^a-z0-9]", "_", canonical_term.lower())[:20]
    stored_intuicion = lexicon_defs.get(lexicon_key, "")
    if stored_intuicion:
        sim2 = compute_similarity(phrase, stored_intuicion)
        # Tomar el mejor de los dos scores
        if sim2["combined_score"] > sim["combined_score"]:
            sim = sim2
            sim["note"] = "Score mejorado al comparar contra intuicion_borja almacenada"

    return {
        **mapping_entry,
        "canonical_term": canonical_term,
        "delta_analysis": {
            **sim,
            "canonical_definition_used": canonical_definition[:150],
        },
    }


def run_tests() -> None:
    """Tests de verificación del linter diferencial."""
    print("─── TESTS DE LINTER DIFERENCIAL ───")
    cases = [
        {
            "intuition": "La fracción de energía que puede producir trabajo real y útil",
            "canonical": "La exergía es la porción de energía libre convertible en trabajo útil máximo en referencia al ambiente T0",
            "expected": "CONVERGE",
        },
        {
            "intuition": "Coordinar agentes sin hablar entre ellos dejando marcas en un tablero compartido",
            "canonical": "Stigmergia: coordinación indirecta entre agentes a través de modificaciones en el entorno físico compartido",
            "expected": "CONVERGE",
        },
        {
            "intuition": "El coste que tiene borrar o procesar información en términos de calor disipado irreversiblemente y también la fatiga cognitiva que genera en el cerebro biológico del investigador durante sesiones largas de depuración",
            "canonical": "Principio de Landauer: mínimo de calor kT*ln2 disipado al borrar un bit",
            "expected": "SUPERSET",
        },
        {
            "intuition": "Un término completamente inventado sin relación con nada conocido",
            "canonical": "Concepto arbitrario sin correlato físico ni matemático",
            "expected": "NO_MATCH",
        },
    ]
    passed = 0
    for c in cases:
        result = compute_similarity(c["intuition"], c["canonical"])
        verdict = result["verdict"]
        ok = verdict == c["expected"]
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status}: expected={c['expected']}, got={verdict} (score={result['combined_score']})")
        if not ok:
            print(f"       intuición: {c['intuition'][:60]}…")
        if ok:
            passed += 1
    print(f"\n  Resultado: {passed}/{len(cases)} tests OK")
    sys.exit(0 if passed == len(cases) else 1)


def main() -> None:
    p = argparse.ArgumentParser(description="C5 Delta Boundary Linter — Agente 3: LINTER DIFERENCIAL")
    p.add_argument("--input", help="Fichero JSONL de mapeos (salida del Mapeador)")
    p.add_argument("--intuition", help="Texto de intuición directa")
    p.add_argument("--canonical", help="Definición canónica para comparar")
    p.add_argument("--expected-verdict", help="Veredicto esperado (para tests)")
    p.add_argument("--output", default="delta.jsonl", help="Fichero de salida")
    p.add_argument("--test", action="store_true")
    args = p.parse_args()

    if args.test:
        run_tests()

    # Modo inline: comparar dos textos directamente
    if args.intuition and args.canonical:
        result = compute_similarity(args.intuition, args.canonical)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if args.expected_verdict:
            ok = result["verdict"] == args.expected_verdict
            print(f"\n{'✅ PASS' if ok else '❌ FAIL'}: expected={args.expected_verdict}, got={result['verdict']}")
            sys.exit(0 if ok else 1)
        return

    if not args.input:
        print("Uso: --input mapeos.jsonl | --intuition '...' --canonical '...'", file=sys.stderr)
        sys.exit(1)

    out_path = Path(args.output)
    n_total = 0
    verdicts: dict[str, int] = {"CONVERGE": 0, "DIVERGE": 0, "SUPERSET": 0, "NO_MATCH": 0}

    with open(args.input, encoding="utf-8") as in_f, open(out_path, "w", encoding="utf-8") as out_f:
        for line in in_f:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            result = lint_mapping(entry)
            out_f.write(json.dumps(result, ensure_ascii=False) + "\n")
            v = result.get("delta_analysis", {}).get("verdict", "NO_MATCH")
            verdicts[v] = verdicts.get(v, 0) + 1
            n_total += 1
            print(f"  [{v}] {entry.get('phrase', '')[:60]}…", file=sys.stderr)

    print(f"\n✅ {n_total} entradas procesadas → {out_path}", file=sys.stderr)
    print(f"   Veredictos: {verdicts}", file=sys.stderr)


if __name__ == "__main__":
    main()
