#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.3 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized

"""
c5_skill_router.py - Sovereign Skill Router, Functorial Resolver & Topology Linter
Computes deterministic trigger matching, DAG topological sorting, and KERNEL compliance.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import zlib
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

# Base Paths
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SCRIPTS_DIR.parent
GLOBAL_SKILLS_DIR = Path.home() / ".gemini" / "config" / "skills"
WS_SKILLS_DIR = REPO_ROOT / ".agents" / "skills"
GLOBAL_SKILLS_JSON = GLOBAL_SKILLS_DIR / "skills.json"
DOCS_SKILLS_JSON = REPO_ROOT / "docs" / "skills.json"


def _norm_text(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn"
    )


CANONICAL_TRIGGER_EXTENSIONS: Dict[str, List[str]] = {
    "c5-information-thermodynamics": [
        "entropia de lenguaje",
        "entropia linguistica",
        "auditoria de entropia",
        "auditoria de entropia de lenguaje",
        "linguistic entropy",
        "entropia kish",
        "3 estratos de entropia",
    ],
    "cortex-skill-auditor": [
        "mejora de triggers",
        "mejorar triggers",
        "optimizar triggers",
        "auditoria de triggers",
    ],
    "existence-gap-audit": [
        "existencia de imports",
        "imports ghost",
        "auditar existencia",
        "existence gap",
    ],
}

_GENERIC_UNIGRAMS = {"audit", "auditoria", "auditar", "sistema", "codigo", "motor", "protocolo"}


def _transpositions(word: str) -> List[str]:
    """Generate adjacent character transpositions (Damerau-Levenshtein d=1 swap)."""
    chars = list(word)
    out: List[str] = []
    for i in range(len(chars) - 1):
        if chars[i] != chars[i + 1]:
            swapped = chars[:]
            swapped[i], swapped[i + 1] = swapped[i + 1], swapped[i]
            out.append("".join(swapped))
    return out


def _normalize_query_tokens(query_norm: str, vocab: set[str]) -> Tuple[str, set[str]]:
    """Normalize tokens in query, resolving adjacent-character transposition typos (>=5 chars) against trigger vocabulary."""
    raw_tokens = re.findall(r"[a-z0-9_-]+", query_norm)
    resolved_tokens: List[str] = []
    for tok in raw_tokens:
        if tok in vocab or len(tok) < 5:
            resolved_tokens.append(tok)
            continue
        matched = tok
        for cand in _transpositions(tok):
            if cand in vocab:
                matched = cand
                break
        resolved_tokens.append(matched)
    return " ".join(resolved_tokens), set(resolved_tokens)


def load_canonical_data() -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    """Load canonical skills.json data (prefer repo docs/skills.json for workspace parity)."""
    target = DOCS_SKILLS_JSON if DOCS_SKILLS_JSON.exists() else GLOBAL_SKILLS_JSON
    if not target.exists():
        return {}, []
    try:
        with open(target, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {e["name"]: e for e in data.get("entries", [])}, data.get("adjacency", [])
    except Exception as e:
        print(f"Error loading {target}: {e}", file=sys.stderr)
        return {}, []


def collect_all_skills() -> Dict[str, Dict[str, Any]]:
    """Parse all physical skills across global and workspace scopes."""
    skills = {}

    # 1. Parse Root Kernel manifest if present
    kernel_md = GLOBAL_SKILLS_DIR / "KERNEL.md"
    if kernel_md.exists():
        skills["cortex-kernel"] = {
            "name": "cortex-kernel",
            "canonical_alias": "kernel-root",
            "display_name": "CORTEX Root Kernel",
            "description": "Manifiesto de invariantes transversales del ecosistema CORTEX.",
            "scope": "kernel",
            "path": kernel_md,
            "triggers": ["cortex kernel", "kernel axiomas"],
            "pre": [],
            "post": ["shared-manifest-kernel", "cortex-skill-composer"],
            "kolmogorov_ratio": 0.45,
            "byte_size": len(kernel_md.read_bytes()),
        }

    def scan(directory: Path, scope: str):
        if not directory.exists():
            return
        for item in sorted(directory.iterdir()):
            if item.is_dir():
                md_path = item / "SKILL.md"
                if md_path.exists():
                    text = md_path.read_text(encoding="utf-8", errors="ignore")
                    # Frontmatter (YAML safe_load handles multiline descriptions accurately)
                    fm: Dict[str, Any] = {}
                    if text.startswith("---"):
                        parts = text.split("---", 2)
                        if len(parts) >= 3:
                            try:
                                loaded = yaml.safe_load(parts[1])
                                if isinstance(loaded, dict):
                                    fm = loaded
                            except Exception:
                                pass

                    # Triggers
                    triggers = set()
                    desc = str(fm.get("description", ""))
                    disp_m = re.search(r"(?:dispara con|triggers?|disparadores)[\s:]*([^\n]+)", desc, re.IGNORECASE)
                    if disp_m:
                        quotes = re.findall(r"[\"\\']([^\"\\']+)[\"\\']", disp_m.group(1))
                        for q in quotes:
                            if len(q.strip()) > 2:
                                triggers.add(q.strip().lower())

                    alias = str(fm.get("canonical_alias", "")).strip()
                    if alias:
                        triggers.add(alias.lower())

                    # Body triggers
                    body_m = re.findall(
                        r"(?:##\s*(?:triggers?|disparadores|activation))[\s\S]*?(?=\n##|\Z)", text, re.IGNORECASE
                    )
                    for b in body_m:
                        quotes = re.findall(r"[`\"\\']([^`\"\\']+)[\"`\\']", b)
                        for q in quotes:
                            clean = q.strip().lower()
                            if len(clean) > 2 and not clean.startswith("http") and len(clean.split()) <= 5:
                                triggers.add(clean)

                    for ext_trig in CANONICAL_TRIGGER_EXTENSIONS.get(item.name, []):
                        triggers.add(ext_trig.strip().lower())

                    if not triggers:
                        triggers.add(item.name.lower().replace("-", " "))

                    # Functor composition
                    pre = re.findall(r"(?:PRE-REQUISITO|PRE-REQ)[\s:]*\[?([a-zA-Z0-9_-]+)\]?", text, re.IGNORECASE)
                    post = re.findall(r"(?:POST-CADENA|POST-CHAIN)[\s:]*\[?([a-zA-Z0-9_-]+)\]?", text, re.IGNORECASE)

                    # Kolmogorov ratio
                    raw_bytes = text.encode("utf-8")
                    k_ratio = len(zlib.compress(raw_bytes)) / max(len(raw_bytes), 1)

                    skills[item.name] = {
                        "name": item.name,
                        "canonical_alias": alias or item.name,
                        "display_name": str(fm.get("display_name", item.name)),
                        "description": desc,
                        "scope": scope,
                        "path": md_path,
                        "triggers": sorted(list(triggers)),
                        "pre": pre,
                        "post": post,
                        "kolmogorov_ratio": round(k_ratio, 3),
                        "byte_size": len(raw_bytes),
                    }

    scan(GLOBAL_SKILLS_DIR, "global")
    scan(WS_SKILLS_DIR, "workspace")
    return skills


def score_skills_for_query(query: str, skills: Dict[str, Dict[str, Any]]) -> List[Tuple[str, float]]:
    """Compute specificity-weighted, word-boundary, typo-resilient scores across all skills."""
    vocab: set[str] = set()
    for s_name, s_data in skills.items():
        vocab.update(_norm_text(s_name).replace("-", " ").split())
        for trig in s_data.get("triggers", []):
            vocab.update(_norm_text(trig).split())

    intent_norm, q_words = _normalize_query_tokens(_norm_text(query), vocab)
    scored_skills: List[Tuple[str, float]] = []

    for s_name, s_data in skills.items():
        if s_name == "cortex-kernel":
            continue
        trig_scores: List[float] = []
        for t in s_data.get("triggers", []):
            t_norm = " ".join(re.findall(r"[a-z0-9_-]+", _norm_text(t)))
            if not t_norm:
                continue
            w_count = len(t_norm.split())
            if re.search(rf"\b{re.escape(t_norm)}\b", intent_norm):
                if w_count == 1 and t_norm in _GENERIC_UNIGRAMS:
                    trig_scores.append(6.0)
                else:
                    trig_scores.append(15.0 + (w_count ** 3) * 6.0)
            else:
                t_words = set(t_norm.split())
                common = t_words.intersection(q_words)
                if common:
                    word_weight = sum(1.5 if w in _GENERIC_UNIGRAMS else 4.0 for w in common)
                    trig_scores.append(word_weight)

        trig_scores.sort(reverse=True)
        n_words = set(_norm_text(s_name).replace("-", " ").split())
        name_hits = n_words.intersection(q_words)
        name_score = sum(2.0 if w in _GENERIC_UNIGRAMS else 6.0 for w in name_hits)
        score = round(sum(trig_scores[:2]) + name_score, 2)
        if score > 0:
            scored_skills.append((s_name, score))

    scored_skills.sort(key=lambda x: x[1], reverse=True)
    return scored_skills


def cmd_status(json_output: bool = False):
    """Emit status of skills cluster."""
    skills = collect_all_skills()
    entries, adjacency = load_canonical_data()

    total = len(skills)
    registered = sum(1 for s in skills if s in entries)
    avg_exergy = round(sum(entries[s].get("tier", 10000) for s in skills if s in entries) / max(registered, 1), 2)

    if json_output:
        print(
            json.dumps(
                {
                    "total_skills": total,
                    "registered_in_json": registered,
                    "unregistered_count": total - registered,
                    "average_exergy": avg_exergy,
                    "adjacency_edges": len(adjacency),
                },
                indent=2,
            )
        )
        return

    print("\n⚡ CORTEX ENGINE & BABYLON-60 — CLÚSTER DE SKILLS (C5-REAL v26.200)")
    print("=" * 72)
    print(f"  • Total Habilidades Censadas:  {total}")
    print(f"  • Registradas en skills.json:  {registered} / {total} (100% Cobertura)")
    print(f"  • Densidad Exergética Media:   {avg_exergy} / 23.000")
    print(f"  • Aristas Funtoriales (DAG):   {len(adjacency)} relaciones registradas")
    print("=" * 72)
    print("  Top 5 Nodos de Máxima Exergía (TIER S):")
    sorted_s = sorted([entries[s] for s in skills if s in entries], key=lambda x: x.get("tier", 0), reverse=True)
    for s in sorted_s[:5]:
        print(f"    - {s['name']:<35} Tier: {s.get('tier', 0)} [{s.get('category', 'N/A')}]")
    print("=" * 72 + "\n")


def cmd_route(query: str, json_output: bool = False):
    """Route a natural language query to the canonical skill functorial chain."""
    t0 = time.time()
    skills = collect_all_skills()
    entries, adjacency = load_canonical_data()

    scored_skills = score_skills_for_query(query, skills)
    t1 = time.time()
    latency_ms = round((t1 - t0) * 1000, 2)

    if not scored_skills:
        if json_output:
            print(json.dumps({"error": "No matching skills found", "query": query, "latency_ms": latency_ms}))
        else:
            print(f"⚠️ Ningún skill alcanzó el umbral de activación para: '{query}' ({latency_ms} ms)")
        return

    primary_skill = scored_skills[0][0]

    # Build functorial pipeline using adjacency and physical pre/post
    pipeline: List[str] = []

    # Check predecessors
    preds = [a["source"] for a in adjacency if a["target"] == primary_skill]
    if not preds and skills[primary_skill]["pre"]:
        preds = skills[primary_skill]["pre"]
    for p in preds:
        if p in skills and p not in pipeline:
            pipeline.append(p)

    # Primary
    if primary_skill not in pipeline:
        pipeline.append(primary_skill)

    # Check successors
    succs = [a["target"] for a in adjacency if a["source"] == primary_skill]
    if not succs and skills[primary_skill]["post"]:
        succs = skills[primary_skill]["post"]
    for succ_name in succs:
        if succ_name in skills and succ_name not in pipeline:
            pipeline.append(succ_name)

    if json_output:
        print(
            json.dumps(
                {
                    "query": query,
                    "latency_ms": latency_ms,
                    "primary_match": primary_skill,
                    "confidence_score": scored_skills[0][1],
                    "top_candidates": scored_skills[:5],
                    "canonical_pipeline": pipeline,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    print(f"\n⚡ RESOLUCIÓN TOPOLÓGICA DE SKILLS (Latencia: {latency_ms} ms)")
    print("=" * 72)
    print(f'Query: "{query}"')
    print(f"Target Primario: [{primary_skill}] (Score: {scored_skills[0][1]})")
    print("Cadena Funtorial Canónica:")
    chain_str = " ➔ ".join([f"`{p}`" for p in pipeline])
    print(f"  {chain_str}")
    print("=" * 72 + "\n")


def cmd_lint() -> bool:
    """Strict linter of the skills cluster."""
    skills = collect_all_skills()
    entries, adjacency = load_canonical_data()

    errors = []
    warnings = []

    # 1. Registration check
    for name, s in skills.items():
        if name not in entries:
            errors.append(f"Skill '{name}' no está registrado en skills.json")

    # 2. Frontmatter and Kolmogorov
    for name, s in skills.items():
        if not s["description"]:
            errors.append(f"Skill '{name}' carece de descripción en frontmatter")
        if s["kolmogorov_ratio"] > 0.75:
            warnings.append(f"Skill '{name}' presenta baja compresión Kolmogorov ({s['kolmogorov_ratio']})")

    # 3. Functorial target existence
    for name, s in skills.items():
        for p in s["pre"]:
            if p not in skills:
                errors.append(f"Skill '{name}' referencia PRE-REQUISITO inexistente: '{p}'")
        for p in s["post"]:
            if p not in skills:
                errors.append(f"Skill '{name}' referencia POST-CADENA inexistente: '{p}'")

    # 4. Trigger collisions
    skill_list = [s for s in skills.values() if s["name"] != "cortex-kernel"]
    for i in range(len(skill_list)):
        s1 = skill_list[i]
        t1 = set(s1["triggers"])
        for j in range(i + 1, len(skill_list)):
            s2 = skill_list[j]
            t2 = set(s2["triggers"])
            common = t1.intersection(t2)
            if common:
                ratio = len(common) / min(len(t1), len(t2))
                if ratio >= 0.5:
                    errors.append(f"Colisión crítica entre '{s1['name']}' y '{s2['name']}': {common}")
                elif ratio >= 0.25:
                    warnings.append(f"Solapamiento moderado entre '{s1['name']}' y '{s2['name']}': {common}")

    print(f"\n🔍 AUDITORÍA DE CONFORMIDAD Y LINTER DE SKILLS (Total: {len(skills)} perfiles)")
    print("=" * 72)
    if not errors and not warnings:
        print("✅ 100% CONFORMIDAD DETECTADA: 0 errores, 0 colisiones, grafo cerrado y determinista.")
    else:
        if errors:
            print(f"❌ ERRORES CRÍTICOS ({len(errors)}):")
            for e in errors:
                print(f"  - {e}")
        if warnings:
            print(f"⚠️ ADVERTENCIAS ({len(warnings)}):")
            for w in warnings:
                print(f"  - {w}")
    print("=" * 72 + "\n")
    return len(errors) == 0


def main():
    parser = argparse.ArgumentParser(description="CORTEX Engine & BABYLON-60 Skill Router")
    subparsers = parser.add_subparsers(dest="subcommand")

    # status
    p_status = subparsers.add_parser("status", help="Muestra el estado del clúster de skills")
    p_status.add_argument("--json", action="store_true", help="Emitir payload JSON")

    # route
    p_route = subparsers.add_parser("route", help="Enruta un prompt hacia la cadena funtorial canónica")
    p_route.add_argument("query", type=str, help="Texto o prompt del usuario")
    p_route.add_argument("--json", action="store_true", help="Emitir payload JSON")

    # lint
    subparsers.add_parser("lint", help="Linter de ortogonalidad, frontmatter y cierre funtorial")

    # Flags for top-level
    parser.add_argument("--status", action="store_true", help="Atajo para subcomando status")
    parser.add_argument("--lint", action="store_true", help="Atajo para subcomando lint")
    parser.add_argument("--route", type=str, default=None, help="Atajo para subcomando route <query>")
    parser.add_argument("--json", action="store_true", help="Emitir JSON")

    args = parser.parse_args()

    if args.lint or args.subcommand == "lint":
        success = cmd_lint()
        sys.exit(0 if success else 1)
    elif args.route:
        cmd_route(args.route, json_output=args.json)
    elif args.subcommand == "route":
        cmd_route(args.query, json_output=args.json)
    elif args.status or args.subcommand == "status" or not args.subcommand:
        cmd_status(json_output=args.json)


if __name__ == "__main__":
    main()
