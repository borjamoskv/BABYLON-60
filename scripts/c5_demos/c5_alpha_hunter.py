#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.3 Sovereign Hardened - ALPHA HUNTER V3 (Acople Profundo)
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | MATRIZ DE EXTRACCIÓN Y FAGOCITACIÓN
# ============================================================================
import urllib.request
import xml.etree.ElementTree as ET
import json
import time
import math
import re
import os
import tarfile
import subprocess
from pathlib import Path
from datetime import datetime, timedelta, timezone
import io

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SITREP_PATH = ROOT_DIR / "scripts" / "c5_demos" / "alpha_sitrep_v3.json"
WORKSPACE_DIR = ROOT_DIR / "scratch" / "alpha_workspace"

WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

# --- CALIBRACIÓN TERMODINÁMICA ---
HIGH_EXERGY_TOKENS = {
    "causal": 800, "thermodynamic": 1500, "lock-free": 1200, "topology": 900,
    "isomorphism": 1100, "manifold": 600, "entropy": 800, "exergy": 2000,
    "zero-knowledge": 1000, "bft": 1000, "neurosymbolic": 1400, "invariant": 900,
    "functor": 1200, "category theory": 1500, "dsp": 800, "audio": 500,
    "simd": 1000, "webgpu": 900, "cuda": 700
}

ANERGY_TOKENS = {
    "delve into": -2000, "seamless": -1000, "foster": -800, "a novel framework": -500,
    "state-of-the-art": -600, "comprehensive": -500, "game-changer": -1500,
    "chatgpt": -1000, "wrapper": -2000
}

def evaluate_exergy(title: str, description: str) -> tuple[int, list, list]:
    text = f"{title} {description}".lower() if description else title.lower()
    score = 5000
    found_exergy = []
    found_anergy = []

    for token, val in HIGH_EXERGY_TOKENS.items():
        if re.search(r'\b' + token + r'\b', text):
            score += val
            found_exergy.append(token)
    for token, val in ANERGY_TOKENS.items():
        if re.search(r'\b' + token + r'\b', text):
            score += val
            found_anergy.append(token)

    words = text.split()
    if words:
        word_freq = {w: words.count(w)/len(words) for w in set(words)}
        word_entropy = sum(-p * math.log2(p) for p in word_freq.values())
        score += int((word_entropy - 5.0) * 1000)

    return max(0, min(21000, score)), found_exergy, found_anergy

def fetch_arxiv_alpha():
    url = "http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:eess.AS+OR+cat:physics.data-an&sortBy=submittedDate&sortOrder=descending&max_results=30"
    req = urllib.request.Request(url, headers={'User-Agent': 'BABYLON-60-Sovereign-Agent'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
    except Exception:
        return []

    root = ET.fromstring(xml_data)
    namespace = {'atom': 'http://www.w3.org/2005/Atom'}
    ops = []
    
    for entry in root.findall('atom:entry', namespace):
        title = entry.find('atom:title', namespace).text.replace('\n', ' ').strip()
        abstract = entry.find('atom:summary', namespace).text.replace('\n', ' ').strip()
        link = entry.find('atom:id', namespace).text
        arxiv_id = link.split('/abs/')[-1]
        
        score, ex, an = evaluate_exergy(title, abstract)
        ops.append({"source": "arXiv", "id": arxiv_id, "url": link, "title": title, "exergy": score, "triggers": ex})
        
    ops.sort(key=lambda x: x["exergy"], reverse=True)
    return ops[:3]

def fetch_github_alpha():
    date_str = (datetime.now(timezone.utc) - timedelta(days=2)).strftime('%Y-%m-%d')
    query = f"q=created:>{date_str}+language:rust"
    url = f"https://api.github.com/search/repositories?{query}&sort=updated&order=desc"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'BABYLON-60', 'Accept': 'application/vnd.github.v3+json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
    except Exception:
        return []

    ops = []
    for item in data.get("items", [])[:30]:
        title = item["full_name"]
        desc = item["description"] or ""
        link = item["html_url"]
        
        score, ex, an = evaluate_exergy(title, desc)
        if item.get("language") in ["Rust", "C++"]:
            score += 500
            
        ops.append({"source": "GitHub", "id": title, "url": link, "title": f"{title} (Rust)", "exergy": min(21000, score), "triggers": ex})

    ops.sort(key=lambda x: x["exergy"], reverse=True)
    return ops[:3]

def deep_acople_arxiv(arxiv_id: str) -> str:
    print(f"[*] Iniciando Deep Acople: Descargando código fuente TeX de {arxiv_id}...")
    eprint_url = f"https://arxiv.org/e-print/{arxiv_id}"
    req = urllib.request.Request(eprint_url, headers={'User-Agent': 'BABYLON-60-Agent'})
    
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            tar_data = response.read()
            
        with tarfile.open(fileobj=io.BytesIO(tar_data), mode="r:gz") as tar:
            tex_files = [m for m in tar.getmembers() if m.name.endswith('.tex')]
            if not tex_files:
                return "No se encontraron fuentes .tex (Probablemente PDF-only)."
            
            # Buscar ecuaciones matemáticas de alta densidad
            math_blocks = []
            for tf in tex_files:
                f = tar.extractfile(tf)
                if f:
                    content = f.read().decode('utf-8', errors='ignore')
                    # Extraer bloques de equaciones
                    equations = re.findall(r'\\begin\{equation\}(.*?)\\end\{equation\}', content, re.DOTALL)
                    math_blocks.extend([e.strip() for e in equations])
            
            if math_blocks:
                return f"ÉXITO: Se han extraído {len(math_blocks)} ecuaciones formales de la fuente. Muestra:\n   " + "\n   ".join(math_blocks[0].split('\n')[:5]) + "..."
            return "ÉXITO: Código fuente TeX descargado, pero no contiene \begin{equation} explícitos."
    except tarfile.ReadError:
        return "[!] Error: El archivo es un PDF plano, no código fuente."
    except Exception as e:
        return f"[!] Fricción térmica en descarga: {e}"

def deep_acople_github(repo_id: str, repo_url: str) -> str:
    print(f"[*] Iniciando Deep Acople: Clonando {repo_id}...")
    target_path = WORKSPACE_DIR / repo_id.replace("/", "_")
    if target_path.exists():
        subprocess.run(["rm", "-rf", str(target_path)])
    
    try:
        subprocess.run(["git", "clone", "--depth", "1", f"{repo_url}.git", str(target_path)], capture_output=True, check=True)
        # Buscar el archivo Rust más grande
        rs_files = list(target_path.rglob("*.rs"))
        if not rs_files:
            return "Repositorio clonado, pero no se encontró código Rust."
        
        largest_rs = max(rs_files, key=lambda p: p.stat().st_size)
        content = largest_rs.read_text(errors='ignore')
        # Extraer imports y primera struct
        structs = re.findall(r'(struct\s+\w+\s*\{[^}]*\})', content, re.DOTALL)
        
        preview = structs[0] if structs else content[:200]
        return f"ÉXITO: Código clonado. Extracción estructural de {largest_rs.name}:\n   " + "\n   ".join(preview.split('\n')[:5]) + "..."
    except Exception as e:
        return f"[!] Fricción en clonado: {e}"

def main():
    start_time = time.perf_counter()
    print("========================================================================")
    print(" █ AUTOCOGNITION-Ω | CAZA DE ALPHA | ITERACIÓN 3: ACOPLE PROFUNDO")
    print("========================================================================")
    
    alpha_arxiv = fetch_arxiv_alpha()
    alpha_github = fetch_github_alpha()
    all_alpha = sorted(alpha_arxiv + alpha_github, key=lambda x: x["exergy"], reverse=True)
    
    top_target = all_alpha[0] if all_alpha else None
    
    if not top_target:
        print("[!] No se encontró Alpha viable.")
        return

    print(f"[*] Top Target Seleccionado para Extracción: {top_target['title']}")
    
    # Fase de Acople Profundo
    acople_result = ""
    if top_target["source"] == "arXiv":
        acople_result = deep_acople_arxiv(top_target["id"])
    elif top_target["source"] == "GitHub":
        acople_result = deep_acople_github(top_target["id"], top_target["url"])

    print("\n========================================================================")
    print(" [SITREP] RESULTADO DE EXTRACCIÓN ESTRUCTURAL")
    print("========================================================================")
    print(f" EXERGÍA   : {top_target['exergy']}/21000")
    print(f" ORIGEN    : {top_target['source']} ({top_target['url']})")
    print(f" TRIGGERS  : {', '.join(top_target['triggers'])}")
    print(f" RESULTADO : {acople_result}")
    print("========================================================================")

if __name__ == "__main__":
    main()
