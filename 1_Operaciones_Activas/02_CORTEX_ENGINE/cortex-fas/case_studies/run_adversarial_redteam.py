#!/usr/bin/env python3
"""
FAS v24 — Adversarial Red-Team Engine
Reality level: C5-REAL
Aesthetics: Industrial Noir 2026

Simulates technical legal appeals ("Recursos de Reposición")
against the generated Actas de Inspección, using a logical-fiscal
framework to train the forensic agent in counter-arguments.
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

def generate_objection(record):
    target = record.get("target", {})
    fin = record.get("financials", {})
    forensics = record.get("forensics", {})
    
    vector = target.get("risk_vector", "").lower()
    blockchain = target.get("blockchain", "")
    jef = forensics.get("jef_score", 0.0)
    
    objections = []
    
    # Logic 1: DeFi & Staking (Classification of income)
    if "defi" in vector or "staking" in vector:
        objections.append({
            "type": "Calificación Jurídica",
            "argument": "Las recompensas no constituyen rendimientos del capital mobiliario, sino ganancias patrimoniales no realizadas hasta su conversión a fiat, según consultas vinculantes recientes."
        })
    
    # Logic 2: Penalty Disproportion (Culpabilidad)
    if jef >= 0.7:
        objections.append({
            "type": "Principio de Culpabilidad",
            "argument": "Ausencia de dolo. La complejidad estructural (JEF > 0.7) se debe a la arquitectura inherente del protocolo (ej. Mixers integrados por defecto) y no a una intención de ocultación deliberada."
        })
        
    # Logic 3: Model 721 / Off-shore
    if "721" in vector or "off-shore" in vector:
        objections.append({
            "type": "Infracción de Derecho Europeo",
            "argument": "La sanción propuesta por omisión del Modelo 721 es desproporcionada y contraria a la libre circulación de capitales de la UE (Sentencia del TJUE Asunto C-788/19)."
        })
        
    # Logic 4: Generic Prescription for Bitcoin holders
    if blockchain == "Bitcoin" and not objections:
        objections.append({
            "type": "Prescripción",
            "argument": "Los activos fueron adquiridos en ejercicios fiscales prescritos (> 4 años) sin que se haya producido un hecho imponible reciente."
        })
        
    # Fallback
    if not objections:
        objections.append({
            "type": "Error de Cálculo Pericial",
            "argument": "Discrepancia en la valoración del activo digital en el momento del devengo."
        })
        
    return objections

def generate_recurso_md(record, objections, output_dir):
    taxpayer = record.get("target", {}).get("taxpayer", "Unknown")
    total_due = record.get("financials", {}).get("total_due_eur", 0)
    
    md = f"""# RECURSO DE REPOSICIÓN - DEFENSA FISCAL (RED-TEAM)
**Sujeto Pasivo:** {taxpayer}
**Fecha de Presentación:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
**Cuota y Sanción Impugnada:** €{total_due:,.2f}

---

## ALA DE DEFENSA FISCAL - ALEGACIONES TÉCNICAS

El contribuyente impugna el Acta de Inspección bajo los siguientes fundamentos de derecho:

"""
    for obj in objections:
        md += f"### {obj['type']}\n> {obj['argument']}\n\n"
        
    md += f"""---
**Estrategia Red-Team:** El Agente Forense de Bizkaia deberá emitir un informe vinculante contrarrestando estas alegaciones técnicas para sostener la liquidación.
"""

    filename = f"bizkaia_recurso_{taxpayer.replace(' ', '_')}.md"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w') as f:
        f.write(md)
    print(f"[+] Recurso generado: {filepath}")

def main():
    base_dir = os.path.dirname(__file__)
    # We load the training ledger to simulate appeals against existing actas
    ledger_path = os.path.join(base_dir, "bizkaia_training_ledger.jsonl")
    
    ledger = load_ledger(ledger_path)
    if not ledger:
        print("[-] No ledger data found.")
        return
        
    out_dir = os.path.join(base_dir, "recursos_legales")
    os.makedirs(out_dir, exist_ok=True)
    
    print("[*] Iniciando Motor Adversarial (Red-Team)...")
    count = 0
    for record in ledger:
        # Only appeal high-value or specific cases
        total_due = record.get("financials", {}).get("total_due_eur", 0)
        if total_due > 10_000:
            objections = generate_objection(record)
            generate_recurso_md(record, objections, out_dir)
            count += 1
            
    print(f"[*] Proceso completado. {count} recursos legales generados en {out_dir}")

if __name__ == "__main__":
    main()
