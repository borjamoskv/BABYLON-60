#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.3 Sovereign Hardened - ORÁCULO DE FRICCIÓN LEGAL
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | MATRIZ DE PREVENCIÓN BUROCRÁTICA
# ============================================================================
import urllib.request
import xml.etree.ElementTree as ET
import json
import time
import math
import re
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SITREP_PATH = ROOT_DIR / "scripts" / "c5_demos" / "legal_friction_sitrep.json"

# --- CALIBRACIÓN DE AMENAZA Y EVASIÓN ---
# 1. Indicadores de Extracción Burocrática (Anergía de Estado)
THREAT_TOKENS = {
    "eu ai act": 2000, "compliance": 800, "mandatory": 1000, "liability": 900,
    "audit requirement": 1200, "kyc": 1500, "regulation": 500, "watermarking": 1000,
    "enforcement": 800, "surveillance": 1200, "eidas": 1500, "digital identity": 1000
}

# 2. Indicadores de Evasión Epistémica (Escudos Matemáticos/Criptográficos)
SHIELD_TOKENS = {
    "zero-knowledge": 1500, "zk-snark": 1800, "homomorphic": 1200, "scitt": 2000,
    "decentralized identifier": 1000, "did": 800, "attestation": 1100, 
    "privacy-preserving": 900, "plausible deniability": 1500, "air-gapped": 1200,
    "obfuscation": 800
}

def evaluate_friction(title: str, abstract: str) -> tuple[int, int, list, list]:
    text = f"{title} {abstract}".lower()
    
    threat_score = 0
    shield_score = 0
    found_threats = []
    found_shields = []

    for token, val in THREAT_TOKENS.items():
        if re.search(r'\b' + token + r'\b', text):
            threat_score += val
            found_threats.append(token)

    for token, val in SHIELD_TOKENS.items():
        if re.search(r'\b' + token + r'\b', text):
            shield_score += val
            found_shields.append(token)

    return threat_score, shield_score, found_threats, found_shields

def fetch_arxiv_legal_oracle():
    print("[*] Oráculo Legal: Escaneando arXiv (cs.CY, cs.CR) en busca de vectores coercitivos...")
    url = "http://export.arxiv.org/api/query?search_query=cat:cs.CY+OR+cat:cs.CR&sortBy=submittedDate&sortOrder=descending&max_results=100"
    req = urllib.request.Request(url, headers={'User-Agent': 'BABYLON-60-Sovereign-Agent'})
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read()
    except Exception as e:
        print(f"[!] Fricción de red: {e}")
        return [], []

    root = ET.fromstring(xml_data)
    namespace = {'atom': 'http://www.w3.org/2005/Atom'}
    
    high_threats = []
    high_shields = []
    
    for entry in root.findall('atom:entry', namespace):
        title = entry.find('atom:title', namespace).text.replace('\n', ' ').strip()
        abstract = entry.find('atom:summary', namespace).text.replace('\n', ' ').strip()
        link = entry.find('atom:id', namespace).text
        
        t_score, s_score, t_triggers, s_triggers = evaluate_friction(title, abstract)
        
        node = {
            "id": link,
            "title": title,
            "threat_score": t_score,
            "shield_score": s_score,
            "threat_triggers": t_triggers,
            "shield_triggers": s_triggers
        }
        
        if t_score >= 1000:
            high_threats.append(node)
        if s_score >= 1000:
            high_shields.append(node)
            
    # Ordenar por máxima fricción y máximo blindaje
    high_threats.sort(key=lambda x: x["threat_score"], reverse=True)
    high_shields.sort(key=lambda x: x["shield_score"], reverse=True)
    
    return high_threats[:3], high_shields[:3]

def main():
    start_time = time.perf_counter()
    print("========================================================================")
    print(" █ AUTOCOGNITION-Ω | ORÁCULO DE FRICCIÓN LEGAL | VECTOR 2")
    print("========================================================================")
    
    threats, shields = fetch_arxiv_legal_oracle()
    
    sitrep = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scan_time_ms": int((time.perf_counter() - start_time) * 1000),
        "top_threats": threats,
        "top_shields": shields
    }
    
    with open(SITREP_PATH, 'w', encoding='utf-8') as f:
        json.dump(sitrep, f, indent=4)
        
    print(f"\n[+] Oráculo finalizado en {sitrep['scan_time_ms']} ms.")
    
    print("\n--- 🚨 TOP VECTORES DE COERCIÓN (AMENAZAS BUROCRÁTICAS) ---")
    if not threats: print("    Cero amenazas inminentes detectadas en el radar de corto alcance.")
    for i, target in enumerate(threats, 1):
        print(f"[{i}] FRICCIÓN: {target['threat_score']} | {target['title']}")
        print(f"    Vectores: {', '.join(target['threat_triggers'])}")
        print(f"    URI: {target['id']}\n")

    print("--- 🛡️ TOP VECTORES DE EVASIÓN (ESCUDOS CRIPTOGRÁFICOS) ---")
    if not shields: print("    Cero arquitecturas defensivas recientes detectadas.")
    for i, target in enumerate(shields, 1):
        print(f"[{i}] BLINDAJE: {target['shield_score']} | {target['title']}")
        print(f"    Matemática Evasiva: {', '.join(target['shield_triggers'])}")
        print(f"    URI: {target['id']}\n")

    print("========================================================================")
    print("DICTAMEN: Radar legal operativo. A la espera de directiva del Operador Raíz.")

if __name__ == "__main__":
    main()
