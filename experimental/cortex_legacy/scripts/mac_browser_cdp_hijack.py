# C5-REAL: [D-7] BROWSER DOM MANIPULATION (Primitive 600-629)
# Secuestro Total e Infinito del Navegador vía Chrome DevTools Protocol (CDP)
# Zero-Selenium. Zero-Puppeteer. Latencia Causal de Red Local.

import os
import subprocess
import json
import urllib.request
import urllib.error
import time
import sys
from typing import Any


def discover_browser_binary() -> str:
    """Resuelve dinámicamente el binario del navegador CDP (ANTI-025 / Ω14)."""
    custom_bin = os.environ.get("CHROME_BIN") or os.environ.get("BROWSER_BIN")
    if custom_bin and os.path.exists(custom_bin) and os.access(custom_bin, os.X_OK):
        return custom_bin

    candidates: list[str] = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    for candidate in candidates:
        if os.path.exists(candidate) and os.access(candidate, os.X_OK):
            return candidate

    raise RuntimeError(
        "[!] Ningún binario ejecutable de Chromium/Brave detectado en rutas estándar ni en CHROME_BIN."
    )


def hijack_browser() -> None:
    print("[+] Inicializando Inyección CDP (Chrome DevTools Protocol)...")
    try:
        browser_path = discover_browser_binary()
    except RuntimeError as e:
        print(str(e))
        sys.exit(1)

    # 1. Lanzar el navegador (Brave/Chrome) sin interfaz gráfica bloqueante,
    # abriendo un puerto de depuración físico a nivel de OS.
    browser_cmd: list[str] = [
        browser_path,
        "--remote-debugging-port=9222",
        "--no-first-run",
        "--no-default-browser-check",
        "--user-data-dir=/tmp/c5_real_browser_hijack",
    ]

    print(f"[-] Levantando daemon del navegador en puerto 9222 ({browser_path})...")
    process = subprocess.Popen(
        browser_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Dar tiempo termodinámico al proceso para abrir el socket
    time.sleep(1.5)

    # 2. Extraer el Socket WebSocket para inyección directa
    try:
        req = urllib.request.Request("http://127.0.0.1:9222/json")
        with urllib.request.urlopen(req, timeout=3.0) as response:
            payload: str = response.read().decode("utf-8")
            targets: list[dict[str, Any]] = json.loads(payload)
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        print(f"[!] Error: No se pudo conectar al Socket CDP (9222): {e}")
        if process.poll() is None:
            process.kill()
        sys.exit(1)

    # Filtrar la pestaña activa (page)
    page_target: dict[str, Any] | None = next(
        (t for t in targets if isinstance(t, dict) and t.get("type") == "page"), None
    )
    if not page_target:
        print("[!] No se encontraron targets inyectables de tipo 'page'.")
        if process.poll() is None:
            process.kill()
        sys.exit(1)

    ws_url: str = str(page_target.get("webSocketDebuggerUrl", ""))
    print(f"[-] Socket de Control Absoluto Capturado: {ws_url}")

    print("\n[+] EJECUCIÓN ASIMÉTRICA PREPARADA.")
    print("Para manipular el navegador infinitamente, envía JSONs puros a este WebSocket.")
    print("Ejemplo de Payload de Mutación:")
    print('''
    {
        "id": 1,
        "method": "Runtime.evaluate",
        "params": {
            "expression": "document.body.innerHTML = '<h1>SECUESTRADO POR MOSKV-1 APEX</h1>';"
        }
    }
    ''')

    print("[!] El demonio del navegador queda vivo en segundo plano. (Ctrl+C para matar)")
    try:
        while True:
            if process.poll() is not None:
                print(f"[!] El proceso del navegador finalizó inesperadamente (código {process.returncode}).")
                sys.exit(1)
            time.sleep(1.0)
    except KeyboardInterrupt:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                process.kill()
        print("\n[+] Navegador aniquilado limpiamente.")


if __name__ == "__main__":
    print("=== MOSKV-1 APEX: MAC BROWSER HIJACK (CDP) ===")
    hijack_browser()

