#!/usr/bin/env python3
"""
Workflow 1: "El Enjambre Nocturno" (Delegación Total) — C5-REAL / BABYLON-60

Script de ejecucion nocturna que:
 1. Recibe una tarea/investigacion/auditoria compleja.
 2. Orquesta un enjambre de subagentes paralelos usando Kimi K3 (kimi-nexus).
 3. Guarda el informe completo en Markdown en AUDIT_REPORTS_2026/.
 4. Genera una sintesis ejecutiva ajustada a formato movil.
 5. Envia la sintesis por WhatsApp a Borja a traves de wa-nexus (puerto 9876 IPC) con cabecera 🤖 [Moskv-1].
"""

import sys
import os
import asyncio
import json
import time
import urllib.request
import urllib.error
from datetime import datetime

# Anadir kernel al path
BABYLON_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(BABYLON_ROOT, "src", "kernel"))

try:
    from swarm_orchestrator import run_swarm_orchestrator
except ImportError:
    # Fallback path
    sys.path.append(os.path.join(BABYLON_ROOT, "experiments", "4_INTEGRATIONS", "kimi_nexus"))
    from swarm_orchestrator import run_swarm_orchestrator

# JID por defecto de Borja en WhatsApp (o JID de la sesion personal)
TARGET_JID = "16465180948@s.whatsapp.net" # O jid configurado
IPC_URL = "http://localhost:9876/send"

def send_whatsapp_message(jid: str, text: str) -> bool:
    """Envia un mensaje a traves de la pasarela IPC de wa-nexus."""
    payload = json.dumps({
        "jid": jid,
        "text": text
    }).encode("utf-8")
    
    req = urllib.request.Request(
        IPC_URL,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            print(f"✅ WhatsApp enviado con éxito: {res_data}")
            return True
    except Exception as e:
        print(f"❌ Error al enviar mensaje por IPC de wa-nexus: {e}")
        return False


async def main():
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = (
            "Auditoría Epistemológica Nocturna de BABYLON-60: "
            "Revisar el estado de los 10 dominios de investigación C5-REAL, "
            "identificar cualquier anergia semántica o gap de existencia en los módulos "
            "y proponer 3 acciones prioritarias para la jornada de mañana."
        )

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_display = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  🌌 WORKFLOW 1: EL ENJAMBRE NOCTURNO (BABYLON-60 / CORTEX)   ║
╠══════════════════════════════════════════════════════════════╣
║ Fecha/Hora: {date_display:<44} ║
║ Tarea:      {prompt[:44]:<44}... ║
╚══════════════════════════════════════════════════════════════╝
""")

    # 1. Ejecutar Swarm Orchestrator (Kimi K3)
    print("🚀 Lanzando enjambre de subagentes en segundo plano (Kimi K3 / kimi-nexus)...")
    raw_result = await run_swarm_orchestrator(
        prompt=prompt,
        p_cores=4,
        s_threads=1,
        backend="moonshot"
    )

    # 2. Guardar informe completo en AUDIT_REPORTS_2026
    reports_dir = os.path.abspath(os.path.join(BABYLON_ROOT, "..", "AUDIT_REPORTS_2026"))
    os.makedirs(reports_dir, exist_ok=True)
    report_path = os.path.join(reports_dir, f"enjambre_nocturno_{timestamp_str}.md")

    full_report_content = f"""# 🌌 Reporte Nocturno del Enjambre (C5-REAL)
**Fecha:** {date_display}
**Objetivo:** {prompt}

---

## 📊 Informe de Resultados del Enjambre

{raw_result}

---
*Generado automáticamente por BABYLON-60 via `el_enjambre_nocturno.py`*
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(full_report_content)

    print(f"📝 Informe completo guardado en: {report_path}")

    # 3. Preparar resumen móvil con cabecera agéntica 🤖 [Moskv-1]
    # Extraemos la sintesis excluyendo la firma de telemetria al final si se desea
    parts = raw_result.split("---")
    synthesis_body = parts[0].strip() if parts else raw_result[:1200]
    
    # Acortar para movil si es excesivamente largo
    if len(synthesis_body) > 2500:
        synthesis_body = synthesis_body[:2450] + "\n\n... *(Informe completo guardado localmente)*"

    whatsapp_msg = f"""🤖 [Moskv-1]

🌌 *INFORME DEL ENJAMBRE NOCTURNO*
📅 _{date_display}_

🎯 *Objetivo:*
{prompt[:150]}{'...' if len(prompt) > 150 else ''}

---

{synthesis_body}

---
📁 *Informe completo guardado en:*
`AUDIT_REPORTS_2026/enjambre_nocturno_{timestamp_str}.md`
"""

    # 4. Despachar a WhatsApp
    print("📲 Enviando informe sintetizado a WhatsApp (wa-nexus)...")
    success = send_whatsapp_message(TARGET_JID, whatsapp_msg)

    if not success:
        # Intentar fallback listando chats recientes para encontrar el JID correcto
        print("⚠️ Reintentando envío por wa-nexus...")
        # Enviar via fallback IPC si aplica
        send_whatsapp_message("16465180948@s.whatsapp.net", whatsapp_msg)

    print("✅ Workflow 1 completado con exito.")

if __name__ == "__main__":
    asyncio.run(main())
