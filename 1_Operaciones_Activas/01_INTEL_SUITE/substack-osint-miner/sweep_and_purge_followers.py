# C5-REAL EXERGY CERTIFIED
import os
import json
import urllib.request
import urllib.parse
import re

def resolve_mafia_nodes_path() -> str:
    """Resolve mafia_nodes.json path dynamically using env vars and dynamic search paths."""
    env_path = os.environ.get("MAFIA_NODES_JSON")
    if env_path and os.path.exists(env_path):
        return env_path
    local_path = os.path.abspath("mafia_nodes.json")
    if os.path.exists(local_path):
        return local_path
    sibling_path = os.path.abspath("../30_BABYLON-60/babylon60/routes/mafia_nodes.json")
    if os.path.exists(sibling_path):
        return sibling_path
    home = os.path.expanduser("~")
    return os.path.join(home, "30_BABYLON-60/babylon60/routes/mafia_nodes.json")

def load_mafia_domains():
    json_path = resolve_mafia_nodes_path()
    if not os.path.exists(json_path):
        print(f"[ERROR] No se encontró el archivo de nodos en: {json_path}")
        return set()

    with open(json_path, "r", encoding="utf-8") as f:
        nodes = json.load(f)

    domains = set()
    for item in nodes:
        item = item.strip().lower()
        if "." in item and " " not in item:
            domain = re.sub(r"^(https?://)?(www\.)?", "", item)
            domains.add(domain)
            # Extraer también el subdominio base
            domains.add(domain.split(".")[0])
    return domains

def fetch_subscribers(subdomain, cookie):
    """Descarga la lista de suscriptores vía API en formato JSON."""
    url = f"https://{subdomain}.substack.com/api/v1/subscribers?limit=200&offset=0"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": f"connect.sid={cookie}"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"[ERROR] Falló la descarga de suscriptores: {e}")
        return None

def block_subscriber(subdomain, email, cookie):
    """Bloquea y elimina un suscriptor por email usando la API de administración."""
    url = f"https://{subdomain}.substack.com/api/v1/subscribers/block"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": f"connect.sid={cookie}",
        "Content-Type": "application/json"
    }
    # Payload para la API interna de Substack
    data = json.dumps({{"email": email}}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status in (200, 204):
                return True
    except Exception as e:
        print(f"[ERROR] No se pudo bloquear a {email}: {e}")
    return False

def sweep_and_purge(subdomain, cookie, dry_run=True):
    print(f"[C5-REAL] Iniciando barrido y purga de suscriptores para: {subdomain}")
    mafia_domains = load_mafia_domains()

    data = fetch_subscribers(subdomain, cookie)
    if not data or "subscribers" not in data:
        print("[ERROR] No se obtuvieron datos o la respuesta no contiene la lista de suscriptores.")
        return

    subscribers = data.get("subscribers", [])
    print(f"[C5-REAL] Total suscriptores listados: {len(subscribers)}")

    purged_count = 0
    for sub in subscribers:
        email = sub.get("email", "").lower()
        sub_id = sub.get("id")

        if not email:
            continue

        # Extraer dominio del email
        email_domain = email.split("@")[-1]
        email_prefix = email.split("@")[0]

        is_mafia = False
        reason = ""

        # 1. Comprobar si el dominio del email coincide con la lista negra de la mafia
        if email_domain in mafia_domains or email_domain.split(".")[0] in mafia_domains:
            is_mafia = True
            reason = f"Dominio Mafia detectado: {email_domain}"

        # 2. Comprobar si es un correo sospechoso de gurú (humo > señal)
        # Nombres de newsletters o correos que usan ganchos exagerados de marketing o keywords del cluster
        elif any(kw in email for kw in ("guru", "marketing", "funnel", "ventas", "seo", "stripe", "afiliado", "mastery")):
            is_mafia = True
            reason = f"Patrón de marketing/humo detectado en el prefijo o dominio: {email}"

        if is_mafia:
            print(f"[ALERTA] Suscriptor sospechoso: {email} | Razón: {reason}")
            if dry_run:
                print(f"[DRY-RUN] Se habría bloqueado y eliminado al suscriptor: {email}")
                purged_count += 1
            else:
                print(f"[MUTACIÓN] Bloqueando a {email}...")
                success = block_subscriber(subdomain, email, cookie)
                if success:
                    print(f"[SUCCESS] Suscriptor {email} bloqueado y purgado de la lista.")
                    purged_count += 1
                else:
                    print(f"[FALLO] Error al purgar al suscriptor {email}.")

    print(f"[C5-REAL] Barrido completado. Total cuentas de la mafia/humo purgadas: {purged_count}")

if __name__ == "__main__":
    # Configuración de credenciales de tu Substack
    SUBDOMAIN = "borjamoskv"

    # Pegar tu cookie "connect.sid" extraída de tu sesión activa
    COOKIE = "REEMPLAZAR_CON_TU_COOKIE_CONNECT_SID"

    # Cambiar a False para aplicar los bloqueos reales en la base de datos
    DRY_RUN = True

    if COOKIE == "REEMPLAZAR_CON_TU_COOKIE_CONNECT_SID":
        print("[ERROR] Debes configurar tu cookie connect.sid para iniciar el barrido.")
    else:
        sweep_and_purge(SUBDOMAIN, COOKIE, dry_run=DRY_RUN)
