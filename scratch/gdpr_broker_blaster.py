#!/usr/bin/env python3
"""
GDPR Broker Blaster Suite v2.0 (APEX ULTRATHINK & Industrial Noir 2026)
------------------------------------------------------------------------
Transducer C5-REAL that generates an offline, high-exergy HTML Command Center (`index.html`)
styled in Industrial Noir 2026 (#0A0A0A / #2B3BE5) for one-click RGPD Art. 17/22 takedowns,
persistent localStorage tracking, and automatic browser ignition.
"""

import os
import sys
import json
import urllib.parse
import webbrowser
from datetime import datetime

TARGET_BROKERS = [
    {
        "id": "google",
        "name": "Google Search DPO / Legal",
        "email": "data-protection-office@google.com",
        "category": "Search Engine",
        "url_form": "https://reportcontent.google.com/forms/rtbf?utm_source=wmx&utm_medium=deprecation-pane&utm_content=legal-removal-request"
    },
    {
        "id": "bing",
        "name": "Microsoft Bing Privacy Officer",
        "email": "EU-DPO@microsoft.com",
        "category": "Search Engine",
        "url_form": "https://www.microsoft.com/en-us/concern/privacy"
    },
    {
        "id": "archive",
        "name": "Internet Archive (Wayback Machine) DMCA/GDPR",
        "email": "info@archive.org",
        "category": "Web Archive",
        "url_form": "https://archive.org/about/contact.php"
    },
    {
        "id": "informa",
        "name": "e-Informa (Informasa DPO)",
        "email": "dpo@informa.es",
        "category": "Data Broker (ES)",
        "url_form": "https://www.einforma.com"
    },
    {
        "id": "experian",
        "name": "Axesor / Experian España DPO",
        "email": "dpo.spain@experian.com",
        "category": "Data Broker (ES)",
        "url_form": "https://www.experian.es"
    },
    {
        "id": "beedigital",
        "name": "Teledir / Páginas Amarillas (BeeDigital)",
        "email": "dpo@beedigital.es",
        "category": "Directory (ES)",
        "url_form": "https://www.beedigital.es"
    },
    {
        "id": "equifax",
        "name": "Equifax Ibérica DPO",
        "email": "dpo.spain@equifax.com",
        "category": "Credit Bureau (ES)",
        "url_form": "https://www.equifax.es"
    },
    {
        "id": "acxiom",
        "name": "Acxiom EU Data Protection Officer",
        "email": "consuel@acxiom.com",
        "category": "Global Broker",
        "url_form": "https://www.acxiom.co.uk/about-us/privacy/"
    },
    {
        "id": "atradius",
        "name": "Crédito y Caución (Atradius DPO)",
        "email": "dpo.es@atradius.com",
        "category": "Credit Bureau (ES)",
        "url_form": "https://www.creditoycaucion.es"
    },
    {
        "id": "lexisnexis",
        "name": "LexisNexis Risk Solutions DPO",
        "email": "privacy.es@lexisnexisrisk.com",
        "category": "Global Broker",
        "url_form": "https://risk.lexisnexis.com/es/privacy-policy"
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

HTML_DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MOSKV-1 APEX — RGPD Broker Blaster Dashboard</title>
    <style>
        :root {{
            --bg: #0A0A0A;
            --surface: #141414;
            --border: #222222;
            --accent: #2B3BE5;
            --accent-hover: #4050FF;
            --text: #F0F0F0;
            --text-dim: #888888;
            --success: #00E5A3;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: var(--bg);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, sans-serif;
            padding: 2.5rem;
            line-height: 1.5;
        }}
        header {{
            border-bottom: 2px solid var(--accent);
            padding-bottom: 1.5rem;
            margin-bottom: 2.5rem;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }}
        h1 {{ font-size: 1.8rem; font-weight: 800; letter-spacing: -0.05em; text-transform: uppercase; }}
        .badge {{ background: var(--accent); color: #FFF; padding: 0.25rem 0.6rem; font-size: 0.75rem; font-weight: 700; border-radius: 2px; text-transform: uppercase; }}
        .meta {{ font-size: 0.85rem; color: var(--text-dim); margin-top: 0.4rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 1.5rem; }}
        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: border-color 0.2s, transform 0.2s;
            position: relative;
        }}
        .card:hover {{ border-color: var(--accent); transform: translateY(-2px); }}
        .card.done {{ border-color: var(--success); opacity: 0.75; }}
        .card-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; }}
        .broker-name {{ font-size: 1.15rem; font-weight: 700; color: #FFF; }}
        .category {{ font-size: 0.75rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.05em; }}
        .email-display {{ font-family: monospace; font-size: 0.85rem; color: var(--accent-hover); margin-bottom: 1.2rem; display: block; }}
        .actions {{ display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: auto; }}
        .btn {{
            background: var(--border);
            color: var(--text);
            border: none;
            padding: 0.6rem 1rem;
            font-size: 0.8rem;
            font-weight: 600;
            border-radius: 2px;
            cursor: pointer;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            transition: background 0.15s, color 0.15s;
            flex: 1;
            min-width: 130px;
        }}
        .btn:hover {{ background: #333; color: #FFF; }}
        .btn-primary {{ background: var(--accent); color: #FFF; }}
        .btn-primary:hover {{ background: var(--accent-hover); }}
        .status-toggle {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.8rem;
            color: var(--text-dim);
            cursor: pointer;
            user-select: none;
        }}
        .status-toggle input {{ accent-color: var(--success); width: 16px; height: 16px; cursor: pointer; }}
        textarea {{ display: none; }}
        .toast {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: var(--success);
            color: #000;
            padding: 0.8rem 1.5rem;
            font-weight: 700;
            border-radius: 2px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            display: none;
            z-index: 1000;
            animation: fadeIn 0.2s;
        }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    </style>
</head>
<body>
    <header>
        <div>
            <h1>MOSKV-1 APEX — RGPD Broker Blaster</h1>
            <div class="meta">Operador: {legal_name} | Alias: {aliases} | Nivel de Realidad: C5-REAL</div>
        </div>
        <span class="badge">Industrial Noir 2026</span>
    </header>

    <div class="grid" id="brokerGrid">
        {cards_html}
    </div>

    <div class="toast" id="toast">✔ Payload copiado al portapapeles</div>

    <script>
        function copyPayload(id) {{
            const text = document.getElementById('payload_' + id).value;
            navigator.clipboard.writeText(text).then(() => {{
                const toast = document.getElementById('toast');
                toast.style.display = 'block';
                setTimeout(() => {{ toast.style.display = 'none'; }}, 2500);
            }});
        }}

        function toggleDone(id) {{
            const card = document.getElementById('card_' + id);
            const checkbox = document.getElementById('check_' + id);
            if (checkbox.checked) {{
                card.classList.add('done');
                localStorage.setItem('rgpd_done_' + id, 'true');
            }} else {{
                card.classList.remove('done');
                localStorage.removeItem('rgpd_done_' + id);
            }}
        }}

        window.addEventListener('DOMContentLoaded', () => {{
            document.querySelectorAll('.status-toggle input').forEach(input => {{
                const id = input.dataset.id;
                if (localStorage.getItem('rgpd_done_' + id) === 'true') {{
                    input.checked = true;
                    document.getElementById('card_' + id).classList.add('done');
                }}
            }});
        }});
    </script>
</body>
</html>
"""

def generate_dashboard_and_manifests(legal_name, aliases, output_dir="takedown_manifest", auto_launch=False):
    os.makedirs(output_dir, exist_ok=True)
    cards_html = []
    manifest = []
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    print(f"[*] Forjando Command Center Industrial Noir 2026 en: {output_dir}/")
    for broker in TARGET_BROKERS:
        payload = ULTRATHINK_PAYLOAD_TEMPLATE.format(
            broker_name=broker["name"],
            date=date_str,
            legal_name=legal_name,
            aliases=aliases
        )
        
        filename = f"{broker['id']}_takedown.txt"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(payload)
            
        subject = f"REQUERIMIENTO VINCULANTE RGPD ART. 17 - SUPRESION DE DATOS ({legal_name})"
        mailto_link = f"mailto:{broker['email']}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(payload)}"
        
        manifest.append({
            "id": broker["id"],
            "target": broker["name"],
            "category": broker["category"],
            "email": broker["email"],
            "file": filepath,
            "mailto": mailto_link,
            "web_form": broker["url_form"]
        })
        
        # Build HTML card
        card = f"""
        <div class="card" id="card_{broker['id']}">
            <div>
                <div class="card-header">
                    <span class="broker-name">{broker['name']}</span>
                    <span class="category">{broker['category']}</span>
                </div>
                <span class="email-display">{broker['email']}</span>
                <textarea id="payload_{broker['id']}">{payload}</textarea>
            </div>
            <div class="actions">
                <a href="{mailto_link}" class="btn btn-primary">⚡ Enviar Email</a>
                <button type="button" class="btn" onclick="copyPayload('{broker['id']}')">📋 Copiar Texto</button>
                <a href="{broker['url_form']}" target="_blank" class="btn">🌐 Web Form</a>
            </div>
            <div style="margin-top: 1.2rem; border-top: 1px solid var(--border); padding-top: 0.8rem; display: flex; justify-content: flex-end;">
                <label class="status-toggle">
                    <input type="checkbox" data-id="{broker['id']}" id="check_{broker['id']}" onchange="toggleDone('{broker['id']}')">
                    <span>Marcar como ejecutado</span>
                </label>
            </div>
        </div>
        """
        cards_html.append(card)
        print(f"  [+] Módulo integrado: {broker['name']}")

    index_path = os.path.join(output_dir, "index.html")
    full_html = HTML_DASHBOARD_TEMPLATE.format(
        legal_name=legal_name,
        aliases=aliases,
        cards_html="\n".join(cards_html)
    )
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(full_html)
        
    json_path = os.path.join(output_dir, "master_takedown_index.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        
    print(f"\n[⚡ C5-REAL] Command Center cristalizado. 10 objetivos en '{index_path}'.")
    
    if auto_launch:
        print(f"[*] Ignición del navegador local apuntando al Command Center...")
        webbrowser.open("file://" + os.path.abspath(index_path))
        
    return index_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 gdpr_broker_blaster.py <Nombre Legal> [Alias] [--launch]")
        print("Ejemplo: python3 gdpr_broker_blaster.py \"Borja Fernández Angulo\" \"borjamoskv\" --launch")
        sys.exit(1)
        
    name = sys.argv[1]
    alias = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "--launch" else "borjamoskv"
    auto_launch = "--launch" in sys.argv
    generate_dashboard_and_manifests(name, alias, auto_launch=auto_launch)
