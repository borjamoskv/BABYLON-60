#!/usr/bin/env python3
"""
Apple Mail Osascript Blaster — Transductor C5-REAL para envío inmediato de 10 requerimientos RGPD Art. 17/22
---------------------------------------------------------------------------------------------------------
Se comunica directamente con Mail.app en macOS vía AppleScript (`osascript`) para crear, dirigir,
y disparar fehacientemente los 10 requerimientos legales de supresión de huella digital.
Inyecta la confirmación oficial en `takedown_ledger.db` (SQLite WAL).
"""

import os
import sys
import subprocess
import sqlite3
from datetime import datetime

DB_PATH = "takedown_manifest/takedown_ledger.db"

TARGET_BROKERS = [
    {
        "id": "google",
        "name": "Google Search DPO / Legal",
        "email": "data-protection-office@google.com"
    },
    {
        "id": "bing",
        "name": "Microsoft Bing Privacy Officer",
        "email": "EU-DPO@microsoft.com"
    },
    {
        "id": "archive",
        "name": "Internet Archive (Wayback Machine) DMCA/GDPR",
        "email": "info@archive.org"
    },
    {
        "id": "informa",
        "name": "e-Informa (Informasa DPO)",
        "email": "dpo@informa.es"
    },
    {
        "id": "experian",
        "name": "Axesor / Experian España DPO",
        "email": "dpo.spain@experian.com"
    },
    {
        "id": "beedigital",
        "name": "Teledir / Páginas Amarillas (BeeDigital)",
        "email": "dpo@beedigital.es"
    },
    {
        "id": "equifax",
        "name": "Equifax Ibérica DPO",
        "email": "dpo.spain@equifax.com"
    },
    {
        "id": "acxiom",
        "name": "Acxiom EU Data Protection Officer",
        "email": "consuel@acxiom.com"
    },
    {
        "id": "atradius",
        "name": "Crédito y Caución (Atradius DPO)",
        "email": "dpo.es@atradius.com"
    },
    {
        "id": "lexisnexis",
        "name": "LexisNexis Risk Solutions DPO",
        "email": "privacy.es@lexisnexisrisk.com"
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

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=5000)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS takedown_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            broker_id TEXT NOT NULL,
            broker_email TEXT NOT NULL,
            execution_type TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL
        );
    """)
    conn.commit()
    return conn

def record_takedown(broker_id, broker_email, exec_type, status="SENT"):
    conn = init_db()
    conn.execute(
        "INSERT INTO takedown_events (broker_id, broker_email, execution_type, status) VALUES (?, ?, ?, ?)",
        (broker_id, broker_email, exec_type, status)
    )
    conn.commit()
    conn.close()

def send_via_apple_mail(legal_name, aliases, sender_email="borjamoskv@gmail.com"):
    print(f"\n[⚡ C5-REAL] Conectando con Apple Mail (`Mail.app`) usando remitente '{sender_email}'...")
    date_str = datetime.now().strftime("%Y-%m-%d")
    sent_count = 0

    for broker in TARGET_BROKERS:
        subject = f"REQUERIMIENTO VINCULANTE RGPD ART. 17 - SUPRESION DE DATOS ({legal_name})"
        payload = ULTRATHINK_PAYLOAD_TEMPLATE.format(
            broker_name=broker["name"],
            date=date_str,
            legal_name=legal_name,
            aliases=aliases
        )

        # Escape strings for AppleScript
        safe_subject = subject.replace('"', '\\"')
        safe_payload = payload.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\r')
        safe_email = broker["email"].replace('"', '\\"')
        safe_sender = sender_email.replace('"', '\\"')

        applescript = f"""
        tell application "Mail"
            set newMessage to make new outgoing message with properties {{subject:"{safe_subject}", content:"{safe_payload}", visible:false, sender:"{safe_sender}"}}
            tell newMessage
                make new to recipient at end of to recipients with properties {{address:"{safe_email}"}}
            end tell
            send newMessage
        end tell
        """

        print(f"  [>] Disparando sobre: {broker['name']} ({broker['email']})...")
        try:
            res = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True, check=True)
            record_takedown(broker["id"], broker["email"], "APPLE_MAIL_OSASCRIPT", "SENT")
            sent_count += 1
            print(f"      ✔ Entregado a servidor saliente Mail.app")
        except subprocess.CalledProcessError as e:
            print(f"      ❌ Fallo osascript en {broker['id']}: {e.stderr.strip()}")

    print(f"\n[⚡ C5-REAL] Operación concluida. {sent_count}/10 requerimientos transmitidos a Apple Mail y sellados en '{DB_PATH}'.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        name = "Borja Fernández Angulo"
        alias = "borjamoskv"
    else:
        name = sys.argv[1]
        alias = sys.argv[2] if len(sys.argv) > 2 else "borjamoskv"

    send_via_apple_mail(name, alias, sender_email="borjamoskv@gmail.com")
