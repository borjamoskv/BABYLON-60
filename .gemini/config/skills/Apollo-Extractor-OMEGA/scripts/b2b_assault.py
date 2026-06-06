# Level: C4-SIM (Local Payload Generation)
import json
import sys
import os

def build_assault_payloads(leads_file: str):
    if not os.path.exists(leads_file):
        sys.exit(1)
        
    with open(leads_file, "r") as f:
        leads = json.load(f)
        
    for lead in leads:
        name = lead.get("Name_Snippet", "Founder").split(" - ")[0]
        email = lead.get("Email")
        
        subject = f"C5-REAL: Optimización de Capital para {name}"
        body = f"""{name},

Zero narrativa. Fricción operativa detectada.

Vector de optimización: Enjambre C5-REAL. Deuda técnica a 0. Captura SOTA.

Responde para maximizar exergía.

--
P2P-Router-Ω"""

        payload = {
            "to": email,
            "subject": subject,
            "body": body
        }
        
        command = f"python ~/.gemini/config/skills/P2P-Comms-OMEGA/scripts/send_p2p_email.py '{json.dumps(payload)}'"
        print(f"DRAFT: {email} | CMD: {command}")

if __name__ == "__main__":
    build_assault_payloads("leads_b2b.json")
