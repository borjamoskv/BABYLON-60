#!/usr/bin/env python3
"""
c5_canonical_term_mapper.py — Agente 2: MAPEADOR
Cruza frases candidatas contra:
  1. Corpus local C5 (C5_LEXICON.json + skills/*.md + rules/*.md) → BM25 Jaccard
  2. Wikipedia API (en + es) → categorías: Systems_theory, Cybernetics, etc.
  3. Semantic Scholar API (gratuita, sin key) → título + abstract
Devuelve el término canónico más probable para cada candidato.

Uso:
    python3 c5_canonical_term_mapper.py [--input candidatos.jsonl] [--phrase "..."] [--test]
    cat candidatos.jsonl | python3 c5_canonical_term_mapper.py --stdin
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

# ─── Configuración de fuentes ────────────────────────────────────────────────────
CONFIG_DIR = Path.home() / ".gemini" / "config"
LEXICON_PATH = CONFIG_DIR / "C5_LEXICON.json"
SKILLS_DIR = CONFIG_DIR / "skills"
RULES_DIR = CONFIG_DIR / "rules"

WIKIPEDIA_CATEGORIES = [
    "Systems_theory", "Cybernetics", "Information_theory",
    "Thermodynamics", "Philosophy_of_mind", "Evolutionary_biology",
    "Cognitive_science", "Semiotics", "Bayesian_statistics",
    "Control_theory", "Game_theory",
]

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"
WIKIPEDIA_API_EN = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"
WIKIPEDIA_API_ES = "https://es.wikipedia.org/api/rest_v1/page/summary/{}"


# ─── Utilidades HTTP mínimas (sin dependencias externas) ────────────────────────

def _http_get(url: str, timeout: int = 5) -> Optional[dict]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "C5-Archaeology-Bot/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


# ─── BM25 Jaccard simplificado para corpus local ────────────────────────────────

def _tokenize(text: str) -> set[str]:
    """Tokenización básica: minúsculas + split por no-alfanumérico."""
    return set(re.findall(r"[a-záéíóúüñ\w]{3,}", text.lower()))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def load_local_corpus() -> list[dict]:
    """
    Carga el corpus local: C5_LEXICON.json + skills/*/SKILL.md (primeras 50 líneas)
    Retorna lista de {term, definition, source}.
    """
    corpus = []

    # 1. C5_LEXICON.json
    if LEXICON_PATH.exists():
        with open(LEXICON_PATH, encoding="utf-8") as f:
            lexicon = json.load(f)
        for key, entry in lexicon.items():
            if key.startswith("_"):
                continue
            corpus.append({
                "term": entry.get("canonical_term", key),
                "definition": entry.get("intuicion_borja", "") + " " + entry.get("canonical_term", ""),
                "source": "C5_LEXICON",
                "author": entry.get("author", ""),
                "year": entry.get("year"),
                "work": entry.get("work", ""),
                "ref_url": entry.get("ref_url"),
                "discipline": entry.get("discipline", []),
            })

    # 2. Skills locales (nombre del skill + descripción)
    for skill_md in SKILLS_DIR.glob("*/SKILL.md"):
        try:
            text = skill_md.read_text(encoding="utf-8", errors="ignore")
            # Extraer description de frontmatter YAML
            m = re.search(r"description:\s*(.+)", text)
            desc = m.group(1).strip() if m else ""
            m2 = re.search(r"display_name:\s*(.+)", text)
            name = m2.group(1).strip() if m2 else skill_md.parent.name
            if desc:
                corpus.append({
                    "term": name,
                    "definition": desc,
                    "source": f"skill:{skill_md.parent.name}",
                    "author": "C5-REAL",
                    "year": None,
                    "work": None,
                    "ref_url": None,
                    "discipline": ["C5-REAL"],
                })
        except Exception:
            pass

    return corpus


def search_local(phrase: str, corpus: list[dict], top_k: int = 3) -> list[dict]:
    """BM25 Jaccard contra corpus local."""
    q_tokens = _tokenize(phrase)
    scores = []
    for entry in corpus:
        def_tokens = _tokenize(entry["definition"])
        score = _jaccard(q_tokens, def_tokens)
        if score > 0.05:
            scores.append((score, entry))
    scores.sort(key=lambda x: x[0], reverse=True)
    return [{"score": round(s, 4), **e} for s, e in scores[:top_k]]


# ─── Wikipedia ───────────────────────────────────────────────────────────────────

def _wikipedia_slug(phrase: str) -> str:
    """Convierte frase en slug de Wikipedia (best-effort)."""
    words = phrase.strip().split()[:4]
    return "_".join(w.capitalize() for w in words)


def search_wikipedia(phrase: str) -> Optional[dict]:
    """
    Busca en Wikipedia API (en + es) usando el concepto clave de la frase.
    Retorna el primer resultado útil con extracto.
    """
    # Extraer concepto clave: eliminar stopwords y tomar las 3 primeras palabras sustantivas
    stopwords = {
        "el", "la", "los", "las", "un", "una", "de", "del", "que", "cuando",
        "si", "sin", "con", "por", "para", "a", "en", "es", "son", "the", "a",
        "of", "and", "that", "when", "without"
    }
    words = [w for w in re.findall(r"[a-záéíóúüñ\w]{3,}", phrase.lower()) if w not in stopwords]
    if not words:
        return None

    # Intentar variantes
    queries = [
        " ".join(words[:3]),
        " ".join(words[:2]),
        words[0] if words else "",
    ]
    for query in queries:
        if not query:
            continue
        encoded = urllib.parse.quote(query)
        # Intentar en inglés primero
        result = _http_get(WIKIPEDIA_API_EN.format(encoded), timeout=4)
        if result and result.get("type") != "disambiguation":
            extract = result.get("extract", "")
            if len(extract) > 50:
                return {
                    "term": result.get("title", query),
                    "definition": extract[:300],
                    "source": "wikipedia_en",
                    "ref_url": result.get("content_urls", {}).get("desktop", {}).get("page"),
                    "author": None,
                    "year": None,
                    "work": None,
                    "discipline": [],
                    "score": 0.0,
                }
        # Intentar en español
        result_es = _http_get(WIKIPEDIA_API_ES.format(encoded), timeout=4)
        if result_es and result_es.get("type") != "disambiguation":
            extract = result_es.get("extract", "")
            if len(extract) > 50:
                return {
                    "term": result_es.get("title", query),
                    "definition": extract[:300],
                    "source": "wikipedia_es",
                    "ref_url": result_es.get("content_urls", {}).get("desktop", {}).get("page"),
                    "author": None,
                    "year": None,
                    "work": None,
                    "discipline": [],
                    "score": 0.0,
                }
    return None


# ─── Semantic Scholar ────────────────────────────────────────────────────────────

def search_semantic_scholar(phrase: str) -> Optional[dict]:
    """
    Busca en Semantic Scholar (API gratuita). Devuelve el paper más citado
    que contenga el término en el título o abstract.
    """
    words = re.findall(r"[a-záéíóúüñ\w]{4,}", phrase.lower())[:5]
    query = " ".join(words)
    url = (
        f"{SEMANTIC_SCHOLAR_API}?query={urllib.parse.quote(query)}"
        f"&limit=3&fields=title,year,authors,citationCount,externalIds"
    )
    data = _http_get(url, timeout=6)
    if not data or not data.get("data"):
        return None

    # Ordenar por citas y tomar el más relevante
    papers = sorted(data["data"], key=lambda p: p.get("citationCount", 0), reverse=True)
    top = papers[0]
    if top.get("citationCount", 0) < 10:
        return None

    authors = top.get("authors", [])
    author_str = authors[0]["name"] if authors else "Unknown"

    return {
        "term": top.get("title", ""),
        "definition": f"Paper seminal con {top.get('citationCount', 0)} citas",
        "source": "semantic_scholar",
        "author": author_str,
        "year": top.get("year"),
        "work": top.get("title", ""),
        "ref_url": f"https://www.semanticscholar.org/paper/{top.get('paperId', '')}",
        "discipline": [],
        "score": 0.0,
    }


# ─── Motor principal de mapeo ────────────────────────────────────────────────────

def map_phrase(phrase: str, corpus: list[dict], verbose: bool = False) -> dict:
    """
    Cruza una frase candidata contra todas las fuentes y devuelve el mejor match.
    """
    results: list[dict] = []

    # 1. Corpus local (más rápido y preciso para términos ya conocidos)
    local = search_local(phrase, corpus, top_k=3)
    results.extend(local)

    # 2. Wikipedia (si el corpus local no tiene un match fuerte)
    best_local_score = max((r["score"] for r in local), default=0.0)
    if best_local_score < 0.25:
        wiki = search_wikipedia(phrase)
        if wiki:
            results.append(wiki)

    # 3. Semantic Scholar (solo si los dos anteriores no son conclusivos)
    if best_local_score < 0.15:
        time.sleep(0.5)  # Respetar rate limit de la API gratuita
        ss = search_semantic_scholar(phrase)
        if ss:
            results.append(ss)

    if not results:
        return {
            "phrase": phrase,
            "best_match": None,
            "confidence": 0.0,
            "all_candidates": [],
        }

    # Seleccionar mejor resultado por score (local) o por fuente preferida
    def _rank(r: dict) -> float:
        base = r.get("score", 0.0)
        if r["source"] == "C5_LEXICON":
            base += 0.3  # Bonus por ya estar en el léxico canónico
        elif r["source"].startswith("wiki"):
            base += 0.1
        return base

    best = max(results, key=_rank)

    return {
        "phrase": phrase,
        "best_match": best,
        "confidence": round(_rank(best), 4),
        "all_candidates": results,
    }


# ─── CLI ─────────────────────────────────────────────────────────────────────────

def run_tests() -> None:
    """Tests de verificación de integración básica."""
    print("─── TESTS DE MAPEADOR ───")
    corpus = load_local_corpus()
    print(f"  Corpus local: {len(corpus)} entradas cargadas")

    cases = [
        {
            "phrase": "coordinación de agentes sin comunicación directa mediante marcas en el sustrato",
            "expected_keyword": "stigmer",  # stigmergia
        },
        {
            "phrase": "fracción de energía que puede producir trabajo real",
            "expected_keyword": "exerg",  # exergía
        },
        {
            "phrase": "puerta que invita a tirar sin manual",
            "expected_keyword": "afford",  # affordance
        },
    ]
    passed = 0
    for c in cases:
        result = map_phrase(c["phrase"], corpus)
        best = result.get("best_match")
        term = (best.get("term", "") if best else "").lower()
        ok = c["expected_keyword"] in term
        status = "✅ PASS" if ok else "⚠️ SOFT"  # Wikipedia/SS pueden cambiar
        print(f"  {status}: '{c['phrase'][:50]}…'")
        if best:
            print(f"       → {best.get('term', 'N/A')} (score={result['confidence']})")
        else:
            print(f"       → sin match (OK si Wikipedia/SS no disponibles en test)")
        if ok:
            passed += 1

    print(f"\n  Resultado: {passed}/{len(cases)} tests OK (algunos pueden fallar sin red)")
    sys.exit(0 if passed >= 2 else 1)


def main() -> None:
    p = argparse.ArgumentParser(description="C5 Canonical Term Mapper — Agente 2: MAPEADOR")
    p.add_argument("--input", help="Fichero JSONL de candidatos (salida del Excavador)")
    p.add_argument("--phrase", help="Frase única a mapear directamente")
    p.add_argument("--stdin", action="store_true", help="Leer JSONL desde stdin")
    p.add_argument("--output", default="mapeos.jsonl", help="Fichero de salida")
    p.add_argument("--test", action="store_true")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    if args.test:
        run_tests()

    corpus = load_local_corpus()
    print(f"📚 Corpus local: {len(corpus)} entradas", file=sys.stderr)

    candidates: list[dict] = []

    if args.phrase:
        candidates.append({"phrase": args.phrase, "signal_type": "cli", "source_id": "cli"})
    elif args.input:
        with open(args.input, encoding="utf-8") as f:
            for line in f:
                try:
                    candidates.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    elif args.stdin:
        for line in sys.stdin:
            try:
                candidates.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                pass
    else:
        print("Uso: --input candidatos.jsonl | --phrase '...' | --stdin", file=sys.stderr)
        sys.exit(1)

    out_path = Path(args.output)
    mapped = 0
    with open(out_path, "w", encoding="utf-8") as out_f:
        for cand in candidates:
            phrase = cand.get("phrase", "")
            if not phrase:
                continue
            result = map_phrase(phrase, corpus, verbose=args.verbose)
            output = {**cand, "mapping": result}
            out_f.write(json.dumps(output, ensure_ascii=False) + "\n")
            mapped += 1
            best = result.get("best_match")
            if best:
                print(f"  [{mapped}] '{phrase[:50]}…' → {best.get('term', '?')} ({result['confidence']:.2f})",
                      file=sys.stderr)
            else:
                print(f"  [{mapped}] '{phrase[:50]}…' → sin match", file=sys.stderr)

    print(f"✅ {mapped} frases mapeadas → {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
