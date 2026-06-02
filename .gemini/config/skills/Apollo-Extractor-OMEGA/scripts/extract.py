import os
import time
import requests
import json
import sys

def extract_web3_ai_leads(target_leads: int, output_file: str):
    api_key = os.environ.get("APOLLO_API_KEY")
    if not api_key:
        print("[P0] Singularity: APOLLO_API_KEY no detectada. Operación abortada.")
        sys.exit(1)

    print(f"[*] Iniciando extracción C5-REAL: Objetivo {target_leads} leads.")
    
    url = "https://api.apollo.io/v1/people/search"
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": api_key
    }

    # Apollo Free Plan constraints:
    # "mixed_people" is blocked. Using "people/search" with allowed basic parameters.
    data = {
        "page": 1,
        "per_page": min(100, target_leads),
        "person_titles": ["founder", "ceo", "cto"],
        "organization_keywords": ["web3", "ai"]
    }

    extracted_leads = []
    
    while len(extracted_leads) < target_leads:
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            # La API de people/search devuelve la clave 'people'
            contacts = response.json().get("people", [])
            
            if not contacts:
                break

            for contact in contacts:
                if len(extracted_leads) >= target_leads:
                    break
                extracted_leads.append({
                    "Name": contact.get("name"),
                    "Title": contact.get("title"),
                    "Company": contact.get("organization_name"),
                    "Email": contact.get("email"),
                    "LinkedIn": contact.get("linkedin_url")
                })
            
            data["page"] += 1
            time.sleep(1) # Rate limit respect
            
        except Exception as e:
            print(f"[!] Error: {e}")
            break

    with open(output_file, "w") as f:
        json.dump(extracted_leads, f, indent=2)
        
    print(f"[+] Persistencia finalizada. {len(extracted_leads)} leads en {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract.py <target_leads> <output_file>")
        sys.exit(1)
    
    extract_web3_ai_leads(int(sys.argv[1]), sys.argv[2])
