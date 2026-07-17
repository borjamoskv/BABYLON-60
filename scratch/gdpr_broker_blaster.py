#!/usr/bin/env python3
"""
GDPR Broker Blaster Suite (C5-REAL)
-----------------------------------
Automates the generation and staging of binding RGPD Article 17 (Right to be Forgotten) 
and Article 22 (Anti-Automated Processing) legal takedown requests against major EU/Spanish 
data brokers, search engines, and web archives.
"""

import os
import sys
import json
import urllib.parse
from datetime import datetime

TARGET_BROKERS = [
    {
        "name": "Google Search DPO / Legal",
        "email": "data-protection-office@google.com",
        "category": "Search Engine",
        "url_form": "https://reportcontent.google.com/forms/rtbf"
    },
    {
        "name": "Microsoft Bing Privacy Officer",
        "email": "EU-DPO@microsoft.com",
        "category": "Search Engine",
        "url_form": "https://www.microsoft.com/en-us/concern/privacy"
    },
    {
        "name": "Internet Archive (Wayback Machine) DMCA/GDPR",
        "email": "info@archive.org",
        "category": "Web Archive",
        "url_form": "mailto:info@archive.org"
    },
    {
        "name": "e-Informa (Informasa DPO)",
        "email": "dpo@informa.es",
        "category": "Data Broker (ES)",
        "url_form": "mailto:dpo@informa.es"
    },
    {
        "name": "Axesor / Experian España DPO",
        "email": "dpo.spain@experian.com",
        "category": "Data Broker (ES)",
        "url_form": "mailto:dpo.spain@experian.com"
    },
    {
        "name": "Teledir / Páginas Amarillas (BeeDigital)",
        "email": "dpo@beedigital.es",
        "category": "Directory (ES)",
        "url_form": "mailto:dpo@beedigital.es"
    }
]

ULTRATHINK_PAYLOAD_TEMPLATE = """A LA ATENCIÓN DEL DELEGADO DE PROTECCIÓN DE DATOS (DPO) / SERVICIOS JURÍDICOS: {broker_name}

REQUERIMIENTO VINCULANTE DE SUPRESIÓN DE DATOS (ART. 17 Y ART. 22 RGPD)
Fecha de emisión: {date}

Por medio de la presente, yo, con nombre legal {legal_name} (y seudónimos asociados: {aliases}), ejerzo formalmente mi derecho de supresión ("derecho al olvido") de conformidad con el Artículo 17 del Reglamento (UE) 2016/679 (RGPD) y la jurisprudencia del TJUE (Asunto C-131/12, Costeja González).

1. EXIGENCIA DE SUPRESIÓN E IRRELEVANCIA PÚBLICA:
Exijo la eliminación inmediata y el cese del tratamiento de cualquier registro, URL, perfil en caché, o indexación algorítmica vinculada a mis datos identificativos. La información tratada por sus sistemas pertenece estrictamente a mi esfera privada, es anacrónica y carece de toda base legitimadora, interés público o relevancia informativa (Art. 17.3 no aplicable).

2. REVOCACIÓN ABSOLUTA DE CONSENTIMIENTO:
Retiro de forma expresa e irrevocable cualquier consentimiento (explícito o implícito) que pudiera haber amparado la captura o indexación inicial de mis datos por parte de sus arañas web (crawlers) o bases de datos de terceros.

3. PRECLUSIÓN DE RESIGNACIÓN AUTOMATIZADA (ART. 22 RGPD):
Me opongo categóricamente a que la presente solicitud sea tramitada mediante respuestas tipo predeterminadas o algoritmos de desestimación automática. Exijo la intervención de un revisor humano cualificado. 

De no verificarse la supresión completa en el plazo perentorio improrrogable de 30 días naturales establecido por el Art. 12.3 RGPD, se interpondrá denuncia formal ante la Agencia Española de Protección de Datos (AEPD) exigiendo la apertura de expediente sancionador por obstrucción al ejercicio de derechos fundamentales.

ATENTAMENTE,
{legal_name}
"""

def generate_takedown_manifest(legal_name, aliases, output_dir="takedown_manifest"):
    os.makedirs(output_dir, exist_ok=True)
    manifest = []
    
    print(f"[*] Generando arsenal de supresión RGPD en: {output_dir}/")
    for broker in TARGET_BROKERS:
        payload = ULTRATHINK_PAYLOAD_TEMPLATE.format(
            broker_name=broker["name"],
            date=datetime.now().strftime("%Y-%m-%d"),
            legal_name=legal_name,
            aliases=aliases
        )
        
        filename = f"{broker['category'].replace(' ', '_').lower()}_{broker['name'].split()[0].lower()}.txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(payload)
            
        # Create mailto link for direct execution
        subject = f"REQUERIMIENTO VINCULANTE RGPD ART. 17 - SUPRESION DE DATOS ({legal_name})"
        mailto_link = f"mailto:{broker['email']}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(payload)}"
        
        manifest.append({
            "target": broker["name"],
            "category": broker["category"],
            "email": broker["email"],
            "file": filepath,
            "mailto_action": mailto_link
        })
        print(f"  [+] Generado requerimiento para: {broker['name']}")

    # Save master execution JSON
    json_path = os.path.join(output_dir, "master_takedown_index.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        
    print(f"\n[⚡ C5-REAL] Arsenal completado. {len(TARGET_BROKERS)} requerimientos legales cristalizados en '{output_dir}/'.")
    return output_dir

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 gdpr_broker_blaster.py <Nombre Legal> [Alias1,Alias2...]")
        print("Ejemplo: python3 gdpr_broker_blaster.py \"Borja Fernández Angulo\" \"borjamoskv\"")
        sys.exit(1)
        
    name = sys.argv[1]
    alias = sys.argv[2] if len(sys.argv) > 2 else "borjamoskv"
    generate_takedown_manifest(name, alias)
