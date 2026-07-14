# C5-REAL: [D-7] BROWSER DOM MANIPULATION (Primitive 600-629)
# Secuestro Total e Infinito del Navegador vía Chrome DevTools Protocol (CDP)
# Zero-Selenium. Zero-Puppeteer. Latencia Causal de Red Local.

import subprocess
import json
import urllib.request
import time
import sys

def hijack_browser():
    print("[+] Inicializando Inyección CDP (Chrome DevTools Protocol)...")
    
    # 1. Lanzar el navegador (Brave/Chrome) sin interfaz gráfica bloqueante, 
    # abriendo un puerto de depuración físico a nivel de OS.
    # Esto desactiva el aislamiento de seguridad (sandbox) para control total.
    browser_cmd = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        # O usar Brave: "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
        "--remote-debugging-port=9222",
        "--no-first-run",
        "--no-default-browser-check",
        "--user-data-dir=/tmp/c5_real_browser_hijack" # Aislamiento total de cookies/sesión
    ]
    
    print("[-] Levantando daemon del navegador en puerto 9222...")
    process = subprocess.Popen(
        browser_cmd, 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL
    )
    
    # Dar tiempo termodinámico al proceso para abrir el socket
    time.sleep(1.5)
    
    # 2. Extraer el Socket WebSocket para inyección directa
    try:
        req = urllib.request.Request("http://127.0.0.1:9222/json")
        with urllib.request.urlopen(req) as response:
            targets = json.loads(response.read().decode())
    except Exception as e:
        print("[!] Error: No se pudo conectar al Socket CDP. ¿Está Chrome/Brave instalado?")
        process.kill()
        sys.exit(1)

    # Filtrar la pestaña activa (page)
    page_target = next((t for t in targets if t['type'] == 'page'), None)
    if not page_target:
        print("[!] No se encontraron targets inyectables.")
        process.kill()
        sys.exit(1)

    ws_url = page_target['webSocketDebuggerUrl']
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
            time.sleep(10)
    except KeyboardInterrupt:
        process.kill()
        print("\n[+] Navegador aniquilado.")

if __name__ == "__main__":
    print("=== MOSKV-1 APEX: MAC BROWSER HIJACK (CDP) ===")
    hijack_browser()
