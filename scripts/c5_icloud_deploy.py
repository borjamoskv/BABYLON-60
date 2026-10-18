import os
import sys
import json
import urllib.request
import urllib.error

def request_cf(method, url, token, data=None):
    req = urllib.request.Request(f"https://api.cloudflare.com/client/v4{url}", method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    
    if data:
        data_bytes = json.dumps(data).encode("utf-8")
        req.add_header("Content-Length", len(data_bytes))
    else:
        data_bytes = None
        
    try:
        with urllib.request.urlopen(req, data=data_bytes) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"[!] Error HTTP {e.code}: {e.read().decode()}")
        sys.exit(1)

def main():
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    apple_code = os.environ.get("APPLE_DOMAIN_CODE")
    domain = "babylon60.com"

    if not token or not apple_code:
        print("╔═════════════════════════════════════════════════════════════════════╗")
        print("║ 🛑 [ ALERTA RING-0 ] · FALTAN INVARIANTES DE ENTORNO                ║")
        print("╚═════════════════════════════════════════════════════════════════════╝")
        print("Uso obligatorio:")
        print("CLOUDFLARE_API_TOKEN='...' APPLE_DOMAIN_CODE='apple-domain=...' python3 c5_icloud_deploy.py\n")
        sys.exit(1)

    print(f"[*] Obteniendo Topología (Zone ID) para {domain}...")
    zones = request_cf("GET", f"/zones?name={domain}", token)
    if not zones.get("result"):
        print("[-] Dominio no encontrado en Cloudflare. Revisa el Token.")
        sys.exit(1)
    
    zone_id = zones["result"][0]["id"]
    print(f"[+] Zone ID: {zone_id}")

    print("[*] Mapeando registros DNS actuales...")
    records = request_cf("GET", f"/zones/{zone_id}/dns_records", token)["result"]

    # 1. Purgar MX y SPF viejos
    print("[*] Iniciando Fase 1: Purga de Anergía (Eliminando Email Routing)...")
    for r in records:
        if r["type"] == "MX":
            print(f"[-] Purgando MX: {r['content']}")
            request_cf("DELETE", f"/zones/{zone_id}/dns_records/{r['id']}", token)
        elif r["type"] == "TXT" and "v=spf1" in r["content"]:
            print(f"[-] Purgando SPF antiguo: {r['content']}")
            request_cf("DELETE", f"/zones/{zone_id}/dns_records/{r['id']}", token)

    # 2. Inyectar registros de iCloud
    print("[*] Iniciando Fase 2: Inyección de Registros Nativos de Apple...")
    apple_records = [
        {"type": "MX", "name": domain, "content": "mx01.mail.icloud.com", "priority": 10, "proxied": False},
        {"type": "MX", "name": domain, "content": "mx02.mail.icloud.com", "priority": 10, "proxied": False},
        {"type": "TXT", "name": domain, "content": "v=spf1 include:icloud.com ~all", "proxied": False},
        {"type": "TXT", "name": domain, "content": apple_code, "proxied": False},
        {"type": "CNAME", "name": f"sig1._domainkey.{domain}", "content": f"sig1.dkim.{domain}.applecustomdomain.com", "proxied": False}
    ]

    for rec in apple_records:
        content_val = rec.get('content', '')
        print(f"[+] Inyectando {rec['type']} -> {content_val} ...")
        request_cf("POST", f"/zones/{zone_id}/dns_records", token, data=rec)

    print("\n╔═════════════════════════════════════════════════════════════════════╗")
    print("║ [✓] DESPLIEGUE C5-REAL COMPLETADO. Manta de Markov cerrada.         ║")
    print("╚═════════════════════════════════════════════════════════════════════╝")
    print("➔ Vuelve a Ajustes de macOS (iCloud) y pulsa 'Verificar Dominio'.\n")

if __name__ == "__main__":
    main()
