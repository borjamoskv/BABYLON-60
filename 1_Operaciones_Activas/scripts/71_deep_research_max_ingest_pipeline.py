#!/usr/bin/env python3
"""
C5-REAL EXERGY CERTIFIED
AUTODIDACT-Ω V6.0 MAXIMUM ENTROPY INGESTION → ANERGY PURGE → EXERGY RANKING PIPELINE
Axioms: Ω2 (Zero-Hallucination), Ω15 (Exergy Max), Ω16 (Landauer), Ω35 (Zero-Residual Purge)

Pipeline:
  Phase 1: INGEST MAXIMUM — fetch every possible source from arXiv API
  Phase 2: DEDUPLICATE — collapse identical arXiv IDs
  Phase 3: SCORE — compute exergy relevance score per paper
  Phase 4: RANK — sort by descending exergy
  Phase 5: CUTOFF — identify the thermodynamic frontier (first paper that is anergy)
  Phase 6: EMIT — write ranked JSON + human-readable report
"""
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import os
import sys
import time
import re
import hashlib
from typing import List, Dict, Any, Tuple
from collections import Counter

# =============================================================================
# PHASE 1: MAXIMUM ENTROPY INGESTION
# =============================================================================

# Exhaustive query matrix: every meaningful reformulation per pillar
QUERY_MATRIX = {
    "Pillar_I_Arithmetization": [
        'all:"zk-SNARK"',
        'all:"zk-STARK"',
        'all:"zkVM"',
        'all:"zkLLM"',
        'all:"zero knowledge" AND all:"machine learning"',
        'all:"verifiable inference"',
        'all:"verifiable computation" AND all:"neural network"',
        'all:"arithmetization" AND all:"circuit"',
        'all:"PLONK"',
        'all:"Groth16"',
        'all:"R1CS"',
        'all:"lookup argument"',
        'all:"polynomial commitment"',
        'all:"verifiable transformer"',
        'all:"zkML"',
        'all:"zero knowledge proof" AND all:"deep learning"',
        'all:"succinct argument"',
        'all:"interactive proof" AND all:"computation"',
        'all:"folding scheme"',
        'all:"Nova" AND all:"recursive proof"',
    ],
    "Pillar_II_Provenance_ZDR": [
        'all:"zero knowledge" AND all:"provenance"',
        'all:"data provenance" AND all:"blockchain"',
        'all:"verifiable" AND all:"data lineage"',
        'all:"zero data retention"',
        'all:"privacy preserving" AND all:"machine learning"',
        'all:"differential privacy" AND all:"language model"',
        'all:"oblivious RAM"',
        'all:"verifiable SQL"',
        'all:"authenticated data structure"',
        'all:"watermark" AND all:"zero knowledge"',
        'all:"federated learning" AND all:"zero knowledge"',
        'all:"TLSNotary"',
        'all:"verifiable credential"',
        'all:"dataset provenance"',
        'all:"embedding" AND all:"privacy"',
    ],
    "Pillar_III_Sovereign_Auth_BFT": [
        'all:"Byzantine fault tolerance" AND all:"agent"',
        'all:"Byzantine fault tolerance" AND all:"machine learning"',
        'all:"trusted execution environment" AND all:"machine learning"',
        'all:"TEE" AND all:"inference"',
        'all:"zkWASM"',
        'all:"RISC Zero"',
        'all:"multi-agent" AND all:"consensus"',
        'all:"agentic AI" AND all:"trust"',
        'all:"agentic AI" AND all:"authentication"',
        'all:"BFT" AND all:"neural"',
        'all:"zero trust" AND all:"AI"',
        'all:"biometric" AND all:"blockchain"',
        'all:"decentralized identity" AND all:"agent"',
        'all:"PBFT" AND all:"scalable"',
        'all:"asynchronous BFT"',
    ],
    "Pillar_IV_Thermodynamics": [
        'all:"Landauer" AND all:"computation"',
        'all:"Bekenstein bound"',
        'all:"Szilard engine"',
        'all:"thermodynamics of computation"',
        'all:"reversible computing"',
        'all:"information erasure" AND all:"energy"',
        'all:"Maxwell demon" AND all:"information"',
        'all:"adiabatic computing"',
        'all:"entropy" AND all:"computation" AND all:"physical"',
        'all:"Landauer limit"',
        'all:"holographic entropy bound"',
        'all:"information thermodynamics"',
        'all:"reversible logic"',
        'all:"minimum energy" AND all:"bit erasure"',
        'all:"computational thermodynamics"',
    ],
}

# Relevance keywords per pillar (for scoring)
RELEVANCE_KEYWORDS = {
    "Pillar_I_Arithmetization": [
        "zk-snark", "zk-stark", "zkvm", "zkllm", "arithmetiz", "plonk", "groth16",
        "r1cs", "circom", "lookup", "snark", "stark", "verifiable", "proof",
        "zero-knowledge", "zero knowledge", "polynomial commit", "kzg", "fri",
        "bulletproof", "folding", "nova", "recursive", "succinct", "constraint",
        "witness", "prover", "verifier", "circuit", "gate", "qap", "zkml",
        "transformer", "neural", "inference", "machine learning",
    ],
    "Pillar_II_Provenance_ZDR": [
        "provenance", "lineage", "data origin", "merkle", "privacy", "oblivious",
        "watermark", "federated", "differential privacy", "retention", "erasure",
        "credential", "split learning", "embedding", "dataset", "tlsnotary",
        "authenticated", "verifiable sql", "vsql", "commitment", "zk-rag",
    ],
    "Pillar_III_Sovereign_Auth_BFT": [
        "byzantine", "bft", "pbft", "tendermint", "tee", "trusted execution",
        "wasm", "consensus", "agent", "swarm", "biometric", "risc-v", "risc zero",
        "sp1", "multi-agent", "agentic", "identity", "authentication", "zero trust",
        "decentralized", "quorum", "fault tolerance", "resilien",
    ],
    "Pillar_IV_Thermodynamics": [
        "landauer", "bekenstein", "szilard", "entropy", "reversible", "thermodynamic",
        "adiabatic", "holographic", "maxwell", "information bound", "erasure",
        "dissipation", "free energy", "computation energy", "bit erase",
        "physical limit", "boltzmann", "information theory",
    ],
}

# Hard noise patterns: papers that are NEVER relevant regardless of query match
NOISE_PATTERNS = [
    r"chondrocyte", r"cartilage", r"fibroblast", r"collagen", r"osteo",
    r"gene expression", r"protein binding", r"signalling pathway",
    r"natural convection", r"fluid dynamics", r"heat transfer",
    r"stellar", r"globular cluster", r"AGB star", r"supernova\b",
    r"drone routing", r"vehicle routing", r"zinc.finger",
    r"magnetic dimensionality", r"charge order",
    r"clinical trial", r"patient", r"diagnosis",
    r"galaxy", r"cosmolog", r"dark matter", r"dark energy",
    r"quantum chromodynamics", r"hadron", r"quark",
    r"plant", r"crop", r"soil", r"agricultural",
    r"protein fold", r"amino acid", r"DNA sequence",
    r"social network analysis", r"sentiment analysis",
    r"image classification(?!.*zero.knowledge)", r"object detection(?!.*verif)",
]

NOISE_RE = re.compile("|".join(NOISE_PATTERNS), re.IGNORECASE)


def fetch_arxiv(query: str, max_results: int = 50, start: int = 0) -> List[Dict]:
    """Fetch papers from arXiv API. Returns list of paper dicts."""
    url = (
        f"http://export.arxiv.org/api/query?"
        f"search_query={urllib.parse.quote(query)}"
        f"&start={start}&max_results={max_results}"
        f"&sortBy=relevance&sortOrder=descending"
    )
    papers = []
    try:
        req = urllib.request.urlopen(url, timeout=30)
        xml_data = req.read().decode("utf-8")
        root = ET.fromstring(xml_data)

        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            title_el = entry.find("{http://www.w3.org/2005/Atom}title")
            if title_el is None or title_el.text is None:
                continue
            title = title_el.text.strip().replace("\n", " ").replace("  ", " ")

            authors = [
                a.find("{http://www.w3.org/2005/Atom}name").text
                for a in entry.findall("{http://www.w3.org/2005/Atom}author")
                if a.find("{http://www.w3.org/2005/Atom}name") is not None
            ]
            published = entry.find("{http://www.w3.org/2005/Atom}published")
            year = published.text[:4] if published is not None and published.text else "0000"

            link = entry.find("{http://www.w3.org/2005/Atom}id")
            url_str = link.text if link is not None and link.text else ""

            summary_el = entry.find("{http://www.w3.org/2005/Atom}summary")
            abstract = summary_el.text.strip().replace("\n", " ") if summary_el is not None and summary_el.text else ""

            # Extract arXiv categories
            categories = []
            for cat in entry.findall("{http://www.w3.org/2005/Atom}category"):
                term = cat.get("term", "")
                if term:
                    categories.append(term)

            arxiv_id = url_str.split("/")[-1] if url_str else ""

            papers.append({
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": authors[0] + (" et al." if len(authors) > 1 else "") if authors else "Unknown",
                "authors_full": authors,
                "year": year,
                "url": url_str,
                "abstract": abstract[:500],
                "categories": categories,
            })
    except Exception as e:
        print(f"  ⚠ Fetch error for query '{query[:50]}...': {e}", file=sys.stderr)

    return papers


def phase1_ingest(max_per_query: int = 50) -> List[Dict]:
    """PHASE 1: Maximum entropy ingestion across all query variations."""
    print("=" * 80)
    print("  PHASE 1: MAXIMUM ENTROPY INGESTION (arXiv API)")
    print("=" * 80)

    all_papers = []
    total_queries = sum(len(qs) for qs in QUERY_MATRIX.values())
    query_idx = 0

    for pillar, queries in QUERY_MATRIX.items():
        print(f"\n■ {pillar} ({len(queries)} queries)")
        for q in queries:
            query_idx += 1
            papers = fetch_arxiv(q, max_results=max_per_query)
            # Tag with source pillar
            for p in papers:
                p["source_pillar"] = pillar
                p["source_query"] = q
            all_papers.extend(papers)
            print(f"  [{query_idx}/{total_queries}] +{len(papers):3d} papers | query: {q[:60]}")
            # Rate limit courtesy
            time.sleep(0.5)

    print(f"\n■ TOTAL RAW INGESTED: {len(all_papers)} papers")
    return all_papers


# =============================================================================
# PHASE 2: DEDUPLICATION
# =============================================================================

def phase2_deduplicate(papers: List[Dict]) -> List[Dict]:
    """PHASE 2: Collapse duplicates by arXiv ID."""
    print("\n" + "=" * 80)
    print("  PHASE 2: DEDUPLICATION (arXiv ID collapse)")
    print("=" * 80)

    seen_ids = {}
    for p in papers:
        aid = p["arxiv_id"]
        if aid not in seen_ids:
            seen_ids[aid] = p
        else:
            # Merge source pillars
            existing = seen_ids[aid]
            if p["source_pillar"] != existing["source_pillar"]:
                if "cross_pillars" not in existing:
                    existing["cross_pillars"] = {existing["source_pillar"]}
                existing["cross_pillars"].add(p["source_pillar"])

    unique = list(seen_ids.values())
    print(f"■ Before: {len(papers)} | After: {len(unique)} | Duplicates removed: {len(papers) - len(unique)}")
    return unique


# =============================================================================
# PHASE 3: SCORING (Exergy Relevance)
# =============================================================================

def compute_relevance_score(paper: Dict) -> float:
    """Compute exergy relevance score for a paper."""
    title_lower = paper["title"].lower()
    abstract_lower = paper.get("abstract", "").lower()
    text = title_lower + " " + abstract_lower

    # 1. Keyword density (0-1)
    max_hits = 0
    best_pillar = None
    for pillar, keywords in RELEVANCE_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text)
        density = hits / len(keywords)
        if density > max_hits:
            max_hits = density
            best_pillar = pillar

    # 2. Recency bonus (papers from 2024-2026 get boost)
    year = int(paper.get("year", "2000"))
    if year >= 2026:
        recency = 1.0
    elif year >= 2025:
        recency = 0.95
    elif year >= 2024:
        recency = 0.85
    elif year >= 2022:
        recency = 0.70
    elif year >= 2020:
        recency = 0.55
    elif year >= 2015:
        recency = 0.40
    else:
        recency = 0.25

    # 3. Cross-pillar bonus (papers appearing in multiple pillar queries)
    cross = len(paper.get("cross_pillars", set()))
    cross_bonus = min(cross * 0.1, 0.3)

    # 4. Category relevance (cs.CR, cs.AI, cs.LG, quant-ph get bonus)
    relevant_cats = {"cs.CR", "cs.AI", "cs.LG", "cs.DC", "cs.CC", "quant-ph", "cs.IT"}
    cat_bonus = 0.1 if any(c in relevant_cats for c in paper.get("categories", [])) else 0.0

    # Combined score
    score = (0.50 * max_hits) + (0.25 * recency) + (0.15 * cross_bonus / 0.3) + (0.10 * cat_bonus / 0.1)

    paper["exergy_score"] = round(score, 4)
    paper["best_pillar"] = best_pillar
    paper["keyword_density"] = round(max_hits, 4)
    paper["recency_score"] = recency

    return score


def phase3_score(papers: List[Dict]) -> List[Dict]:
    """PHASE 3: Score all papers by exergy relevance."""
    print("\n" + "=" * 80)
    print("  PHASE 3: EXERGY SCORING")
    print("=" * 80)

    # First: noise filter
    clean = []
    noise = []
    for p in papers:
        combined = p["title"] + " " + p.get("abstract", "")
        if NOISE_RE.search(combined):
            noise.append(p)
        else:
            clean.append(p)

    print(f"■ Noise papers purged: {len(noise)}")
    if noise:
        print("  Purged examples:")
        for n in noise[:5]:
            print(f"    ❌ {n['title'][:70]}")

    # Score remaining
    for p in clean:
        compute_relevance_score(p)

    print(f"■ Scored papers: {len(clean)}")
    return clean


# =============================================================================
# PHASE 4: RANK
# =============================================================================

def phase4_rank(papers: List[Dict]) -> List[Dict]:
    """PHASE 4: Sort by descending exergy score."""
    print("\n" + "=" * 80)
    print("  PHASE 4: EXERGY RANKING (descending)")
    print("=" * 80)

    ranked = sorted(papers, key=lambda p: p["exergy_score"], reverse=True)

    # Print top 20
    print("\n  TOP 20 EXERGY PAPERS:")
    for i, p in enumerate(ranked[:20], 1):
        print(f"  [{i:3d}] Score={p['exergy_score']:.4f} | {p['year']} | {p['title'][:65]}")

    return ranked


# =============================================================================
# PHASE 5: CUTOFF — find the thermodynamic frontier
# =============================================================================

def phase5_cutoff(ranked: List[Dict], threshold: float = 0.15) -> Tuple[List[Dict], List[Dict], int]:
    """PHASE 5: Identify the cutoff point where exergy drops below threshold."""
    print("\n" + "=" * 80)
    print(f"  PHASE 5: THERMODYNAMIC CUTOFF (threshold={threshold})")
    print("=" * 80)

    exergy = []
    anergy = []
    cutoff_idx = len(ranked)

    for i, p in enumerate(ranked):
        if p["exergy_score"] >= threshold:
            exergy.append(p)
        else:
            if not anergy:  # First anergy paper
                cutoff_idx = i
                print(f"\n  🎯 CUTOFF AT RANK #{i + 1}:")
                print(f"     Title: {p['title'][:70]}")
                print(f"     Score: {p['exergy_score']:.4f} < {threshold}")
                print(f"     Year:  {p['year']}")
                print(f"     This is the FIRST paper we should NOT give importance to.")
            anergy.append(p)

    print(f"\n■ EXERGY (keep):  {len(exergy)} papers")
    print(f"■ ANERGY (purge): {len(anergy)} papers")
    print(f"■ Cutoff rank:    #{cutoff_idx + 1}")

    # Distribution by pillar
    print("\n  Exergy distribution by pillar:")
    pillar_counts = Counter(p.get("best_pillar", "Unknown") for p in exergy)
    for pil, count in pillar_counts.most_common():
        bar = "█" * (count // 2)
        print(f"    {pil:40s} {count:3d} {bar}")

    return exergy, anergy, cutoff_idx


# =============================================================================
# PHASE 6: EMIT
# =============================================================================

def phase6_emit(exergy: List[Dict], anergy: List[Dict], cutoff_idx: int, output_dir: str):
    """PHASE 6: Write ranked results to disk."""
    print("\n" + "=" * 80)
    print("  PHASE 6: EMIT RESULTS")
    print("=" * 80)

    # Full ranked JSON
    result = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "engine": "AUTODIDACT-Ω V6.0 ULTRA-EXERGY",
        "total_ingested": len(exergy) + len(anergy),
        "total_exergy": len(exergy),
        "total_anergy": len(anergy),
        "cutoff_rank": cutoff_idx + 1,
        "first_anergy_paper": anergy[0]["title"] if anergy else "N/A",
        "exergy_papers": [{
            "rank": i + 1,
            "arxiv_id": p["arxiv_id"],
            "title": p["title"],
            "authors": p["authors"],
            "year": p["year"],
            "url": p["url"],
            "exergy_score": p["exergy_score"],
            "best_pillar": p["best_pillar"],
            "keyword_density": p["keyword_density"],
            "recency_score": p["recency_score"],
        } for i, p in enumerate(exergy)],
        "anergy_papers_sample": [{
            "rank": cutoff_idx + 1 + i,
            "arxiv_id": p["arxiv_id"],
            "title": p["title"],
            "exergy_score": p["exergy_score"],
        } for i, p in enumerate(anergy[:20])],
    }

    json_path = os.path.join(output_dir, "deep_research_ranked.json")
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"■ JSON: {json_path}")

    # Stats
    if exergy:
        scores = [p["exergy_score"] for p in exergy]
        print(f"■ Exergy score range: [{min(scores):.4f}, {max(scores):.4f}]")
        print(f"■ Mean exergy score:  {sum(scores)/len(scores):.4f}")

    print(f"\n🎯 PIPELINE COMPLETE — {len(exergy)} EXERGY PAPERS RANKED, {len(anergy)} ANERGY PURGED")
    return json_path


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("  AUTODIDACT-Ω V6.0 ULTRA-EXERGY MAXIMUM INGESTION PIPELINE")
    print("  Axioms: Ω2, Ω15, Ω16, Ω22, Ω35")
    print("=" * 80)

    output_dir = "/tmp"

    # Check for cached results to avoid re-fetching
    cache_path = os.path.join(output_dir, "deep_research_raw_cache.json")
    if os.path.exists(cache_path):
        print(f"\n■ Loading cached raw corpus from {cache_path}")
        with open(cache_path, "r") as f:
            raw_papers = json.load(f)
        print(f"■ Cached papers: {len(raw_papers)}")
    else:
        raw_papers = phase1_ingest(max_per_query=50)
        with open(cache_path, "w") as f:
            json.dump(raw_papers, f, indent=2, default=str)
        print(f"■ Cached to {cache_path}")

    unique = phase2_deduplicate(raw_papers)
    scored = phase3_score(unique)
    ranked = phase4_rank(scored)
    exergy, anergy, cutoff = phase5_cutoff(ranked, threshold=0.15)
    json_path = phase6_emit(exergy, anergy, cutoff, output_dir)
