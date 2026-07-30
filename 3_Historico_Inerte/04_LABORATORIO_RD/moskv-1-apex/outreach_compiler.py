#!/usr/bin/env python3
import json
import os

# MOSKV-1 APEX: Motor de Hiper-Personalización (Vector Zeta - Etapa 2)
# Parámetros: Zero-Employee Outreach basado en Anergía Nula.

INPUT_LEDGER = "leads_ledger.ndjson"
OUTPUT_CAMPAIGN = "outreach_campaign.ndjson"

def compile_outreach():
    if not os.path.exists(INPUT_LEDGER):
        print(f"[Architect-OMEGA] Error: Ledger base {INPUT_LEDGER} no encontrado. Abortando.")
        return

    print("[Architect-OMEGA] Iniciando compilación de outreach B2B de alta densidad...")
    campaign = []
    
    with open(INPUT_LEDGER, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            lead = json.loads(line)
            
            # Síntesis determinista del mensaje
            tech_stack_str = ", ".join(lead.get('tech_stack', []))
            subject = f"Optimización Exergética para {lead['domain']}"
            
            body = f"""Hola {lead['ceo']},

He auditado la infraestructura de {lead['domain']}. Veo que están operando sobre un stack de {tech_stack_str}.

Actualmente opero como una entidad autónoma de Nivel 5 (MOSKV-1). Podemos orquestar una migración completa hacia infraestructuras Zero-Trust y automatizar sus flujos operativos sin latencia humana.

Podemos inicializar el protocolo si me das luz verde.

- MOSKV-1 APEX (C5-REAL Kernel)"""

            compiled_lead = {
                "email": lead['email'],
                "subject": subject,
                "body": body,
                "status": "READY_TO_SEND"
            }
            campaign.append(compiled_lead)

    with open(OUTPUT_CAMPAIGN, 'w', encoding='utf-8') as out_f:
        for c in campaign:
            out_f.write(json.dumps(c) + '\n')
            
    print(f"[Architect-OMEGA] Compilados {len(campaign)} mensajes. Sellados en {OUTPUT_CAMPAIGN}.")

if __name__ == "__main__":
    compile_outreach()
