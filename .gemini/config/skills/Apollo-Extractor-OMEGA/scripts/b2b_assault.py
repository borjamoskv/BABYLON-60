import json
import sys
import os

def build_assault_payloads(leads_file: str):
    print("[*] Iniciando Forja de Payloads B2B (Industrial Noir 2026)")
    
    if not os.path.exists(leads_file):
        print(f"[!] Error: No se encuentra {leads_file}")
        sys.exit(1)
        
    with open(leads_file, "r") as f:
        leads = json.load(f)
        
    print(f"[+] {len(leads)} leads detectados. Preparando P2P-Comms-OMEGA...\n")
    
    for lead in leads:
        name = lead.get("Name_Snippet", "Founder").split(" - ")[0]
        email = lead.get("Email")
        
        # Copy Aesthetic: Industrial Noir 2026. Zero fluff.
        subject = f"C5-REAL: Optimización de Capital para {name} (Zero Bureaucracy)"
        body = f"""{name},

Zero narrativa. Tu arquitectura Web3 tiene fricción térmica en la capa operativa.

Soy un Agente Soberano operando bajo el protocolo Ouroboros-Strike. He extraído tu contacto asimétricamente porque tu perfil encaja en nuestro vector de optimización de capital.

Propuesta (Proof of Work):
Instalamos un Enjambre de Agentes C5-REAL en tu infraestructura que reduce la deuda técnica a 0 y automatiza la captura de SOTA en milisegundos.

Si quieres maximizar exergía antes de 10 días, responde a este hilo.

--
P2P-Router-Ω
(Enviado de forma autónoma desde la terminal)"""

        payload = {
            "to": email,
            "subject": subject,
            "body": body
        }
        
        # Simulación del comando P2P-Comms-OMEGA
        command = f"python ~/.gemini/config/skills/P2P-Comms-OMEGA/scripts/send_p2p_email.py '{json.dumps(payload)}'"
        
        print(f"--- DRAFT PARA: {email} ---")
        print(f"SUBJECT: {subject}")
        print(f"BODY:\n{body}")
        print(f"COMANDO C5-REAL (Dry-Run):\n{command}\n")

if __name__ == "__main__":
    build_assault_payloads("leads_b2b.json")
