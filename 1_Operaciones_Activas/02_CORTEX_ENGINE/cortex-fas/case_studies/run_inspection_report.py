#!/usr/bin/env python3
"""
FAS v24 — Inspection Report Generator (Fase 5)
Reality level: C5-REAL
Aesthetics: Industrial Noir 2026

Fuses financial ledger data with OSINT intelligence to generate
official Hacienda de Bizkaia markdown inspection reports.
"""

import json
import os
from datetime import datetime, timezone

def load_ledger(filepath):
    data = []
    if not os.path.exists(filepath): return data
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def load_osint(filepath):
    if not os.path.exists(filepath): return {}
    with open(filepath, 'r') as f:
        doc = json.load(f)
        return {item['taxpayer']: item for item in doc.get("results", [])}

def determine_penalty_rate(jef_score):
    if jef_score < 0.3:
        return 0.50, "Infracción Leve (Ofuscación baja)"
    elif jef_score < 0.7:
        return 1.00, "Infracción Grave (Ofuscación estructural)"
    else:
        return 1.50, "Infracción Muy Grave (Ingeniería de ocultación compleja)"

def generate_acta(financial_record, osint_record, output_dir):
    target = financial_record.get("target", {})
    taxpayer = target.get("taxpayer", "Unknown")
    address = target.get("wallet_address", "Unknown")
    
    fin = financial_record.get("financials", {})
    tax_base = fin.get("tax_base_liability_eur", 0)
    
    forensics = financial_record.get("forensics", {})
    jef = forensics.get("jef_score", 0.0)
    
    penalty_rate, penalty_desc = determine_penalty_rate(jef)
    calc_penalty = tax_base * penalty_rate
    interest = fin.get("interest_demora_eur", 0)
    total_debt = tax_base + calc_penalty + interest
    
    # OSINT
    ens = osint_record.get("ens", "No detectado")
    github = osint_record.get("github_profile") or {}
    cex_exp = osint_record.get("cex_exposure", [])
    
    flight_risk = "ALTO" if (ens and github) else "MODERADO"
    if any(c.get("type") == "simulated_cex_hit" or c.get("type") == "withdrawal_to_cex" for c in cex_exp):
        flight_risk = "MUY ALTO (Canal de Off-Ramping detectado)"

    md = f"""# ACTA DE INSPECCIÓN FISCAL - DIPUTACIÓN FORAL DE BIZKAIA
**Expediente:** FAS-2026-{taxpayer.replace(' ', '').upper()}
**Fecha Emisión:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}
**Nivel de Realidad:** C5-REAL (Forensic Digital Twin)

---

## 1. IDENTIFICACIÓN DEL SUJETO PASIVO Y RIESGO DE FUGA
- **Contribuyente:** {taxpayer}
- **Dirección Principal (Blockchain):** `{address}`
- **Alias ENS (OSINT):** {ens}
- **Identidad GitHub Correlacionada:** {github.get('name', 'N/A')} ({github.get('location', 'N/A')})
- **Evaluación de Riesgo de Fuga:** **{flight_risk}**

## 2. EXPOSICIÓN CEX (MODELO 721)
"""
    if cex_exp:
        for exp in cex_exp:
            md += f"- **Tipo:** {exp.get('type')} | **Entidad:** {exp.get('cex', 'N/A')} | **Estado:** {exp.get('status', 'Confirmado')}\n"
    else:
        md += "- Sin interacción directa con CEX detectada.\n"

    md += f"""
## 3. TRAZABILIDAD FINANCIERA Y OFUSCACIÓN
- **Vector de Riesgo Detonante:** {target.get('risk_vector', 'N/A')}
- **Nivel de Ofuscación Detectado (JEF Score):** {jef:.4f}
- **Volumen Sintético (EUR):** €{fin.get('synthetic_volume_eur', 0):,.2f}
- **Base Imponible No Declarada:** €{tax_base:,.2f}

## 4. RÉGIMEN SANCIONADOR Y LIQUIDACIÓN
Basado en el JEF Score de `{jef:.4f}`, se aplica el régimen: **{penalty_desc}** (Coeficiente: {penalty_rate*100:.0f}%).

| Concepto | Importe (EUR) |
|----------|---------------|
| Cuota Íntegra Omitida | €{tax_base:,.2f} |
| Intereses de Demora (4.0625%) | €{interest:,.2f} |
| **Sanción Tributaria** | **€{calc_penalty:,.2f}** |
| **TOTAL A INGRESAR** | **€{total_debt:,.2f}** |

---
**Firma Digital del Agente Forense:** `0xOuroborosFAS_Signed_{datetime.now().timestamp()}`
"""
    
    filename = f"bizkaia_acta_{taxpayer.replace(' ', '_')}.md"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w') as f:
        f.write(md)
    print(f"[+] Generada: {filepath}")

def main():
    base_dir = os.path.dirname(__file__)
    ledger_path = os.path.join(base_dir, "bizkaia_training_ledger.jsonl")
    osint_path = os.path.join(base_dir, "cortex_osint_ens_report.json")
    
    ledger = load_ledger(ledger_path)
    osint = load_osint(osint_path)
    
    if not ledger:
        print("[-] No ledger data found.")
        return
        
    out_dir = os.path.join(base_dir, "actas_inspeccion")
    os.makedirs(out_dir, exist_ok=True)
    
    print("[*] Iniciando motor de Generación de Actas (Fase 5)...")
    for record in ledger:
        taxpayer = record.get("target", {}).get("taxpayer")
        if taxpayer in osint:
            # We have intelligence fusion
            generate_acta(record, osint[taxpayer], out_dir)
            
    print(f"[*] Proceso completado. Actas exportadas a {out_dir}")

if __name__ == "__main__":
    main()
