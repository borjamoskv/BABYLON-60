# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
Prueba de Concepto (PoC) Autónoma: Extracción Causal de Google Labs FX.
Esta es una implementación estricta (Demonio Ciego) que interactúa con la FSM de MusicFX
bypasseando cualquier interfaz web.

INSTRUCCIONES DE FALSACIÓN:
1. Abre tu navegador autenticado en labs.google/fx
2. Abre la consola de desarrollo (Network tab).
3. Copia el Header 'Authorization: Bearer ya29...'
4. Copia tu Header 'Cookie: SAPISID=...; __Secure-1PSID=...'
5. Ejecuta este script e inyecta las variables cuando se te solicite.
"""

import sys
import json
import time
import urllib.request
import urllib.parse
from urllib.error import HTTPError


def log(msg):
    print(f"[Moskv-PoC] {msg}")


def _submit_task(base_url, headers, prompt):
    project_id = "00000000-0000-0000-0000-000000000000"
    log(f"Initiating Transición SUBMITTING con prompt: '{prompt}'")
    payload = {
        "0": {
            "json": {
                "projectId": project_id,
                "tool": "MUSIC_FX",
                "prompt": prompt,
                "parameters": {"duration": 30, "loop": False},
            }
        }
    }
    req = urllib.request.Request(
        f"{base_url}/generation.createMediaTask?batch=1",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data[0]["result"]["data"]["json"]["taskId"]
    except HTTPError as e:
        log(f"Colapso Termodinámico (Submitting). HTTP {e.code}: {e.read().decode('utf-8')}")
        sys.exit(1)
    except KeyError:
        log("Colisión Bizantina: El formato del JSON devuelto no coincide con el axioma esperado.")
        sys.exit(1)


def _poll_single(base_url, headers, task_id):
    query_input = urllib.parse.quote(json.dumps({"0": {"json": {"taskId": task_id}}}))
    poll_req = urllib.request.Request(
        f"{base_url}/generation.getTaskStatus?batch=1&input={query_input}", headers=headers, method="GET"
    )
    try:
        with urllib.request.urlopen(poll_req) as poll_res:
            poll_data = json.loads(poll_res.read().decode("utf-8"))
            return poll_data[0]["result"]["data"]["json"]
    except HTTPError as e:
        log(f"Error de red temporal: {e.code}. Reintentando...")
        return None


def run_fsm(bearer_token, cookie_str, prompt):
    base_url = "https://labs.google/fx/api/trpc"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Authorization": bearer_token,
        "Cookie": cookie_str,
    }
    task_id = _submit_task(base_url, headers, prompt)
    log(f"Transición EXITOSA -> QUEUED. TaskID: {task_id}")
    log("Initiating Transición POLLING (Bucle acotado a 90s)")
    start_time = time.time()

    while time.time() - start_time < 90:
        status_json = _poll_single(base_url, headers, task_id)
        if status_json:
            status = status_json.get("status")
            if status == "SUCCESS":
                log(f"Punto Fijo Alcanzado (CRYSTALLIZED)! URL: {status_json.get('signedUrl')}")
                return
            if status == "FAILED":
                log("Veto Absoluto: El servidor reportó fallo en la inferencia.")
                sys.exit(1)
            log(f"Estado actual: {status} - Esperando exergía de GPU...")
        time.sleep(2.5)

    log("Error: Límite de entropía de Chaitin superado (Timeout).")
    sys.exit(1)


if __name__ == "__main__":
    print("=" * 60)
    print("  MOSKV-FX-SCAVENGER - PRUEBA DE CONCEPTO STANDALONE")
    print("=" * 60)

    try:
        bearer = input("Introduce Header Authorization (ej. 'Bearer ya29...'): ").strip()
        cookies = input("Introduce Header Cookie (ej. 'SAPISID=...; __Secure-1PSID=...'): ").strip()
        prompt = input("Introduce tu prompt musical: ").strip()

        if not bearer or not cookies or not prompt:
            log("Faltan parámetros axiomáticos. Abortando.")
            sys.exit(1)

        run_fsm(bearer, cookies, prompt)
    except KeyboardInterrupt:
        log("Ejecución colapsada por el Operador.")
        sys.exit(0)
