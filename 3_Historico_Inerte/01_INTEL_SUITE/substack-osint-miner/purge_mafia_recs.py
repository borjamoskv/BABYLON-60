# C5-REAL EXERGY CERTIFIED
import os
import json
import urllib.request
import urllib.error
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
            # Normalizar dominio base
            domain = re.sub(r"^(https?://)?(www\.)?", "", item)
            domains.add(domain)
    return domains

def get_admin_recommendations(subdomain, cookie):
    """Obtiene las recomendaciones activas del panel de administración."""
    url = f"https://{subdomain}.substack.com/api/v1/recommendations"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": f"connect.sid={cookie}"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"[ERROR] No se pudieron obtener las recomendaciones: {e}")
        return []

def delete_recommendation(subdomain, rec_id, cookie):
    """Elimina una recomendación específica usando la API interna."""
    url = f"https://{subdomain}.substack.com/api/v1/recommendations/{rec_id}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": f"connect.sid={cookie}"
    }
    # Substack utiliza el método DELETE para dar de baja recomendaciones
    req = urllib.request.Request(url, headers=headers, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status in (200, 204):
                return True
    except urllib.error.HTTPError as e:
        print(f"[ERROR] Fallo al eliminar rec {rec_id}: HTTP {e.code}")
    except Exception as e:
        print(f"[ERROR] Error de conexión: {e}")
    return False

def purge(subdomain, cookie, dry_run=True):
    print(f"[C5-REAL] Iniciando purga del nodo Substack: {subdomain}")
    mafia_domains = load_mafia_domains()
    if not mafia_domains:
        return

    recs = get_admin_recommendations(subdomain, cookie)
    if not recs:
        print("[C5-REAL] No se encontraron recomendaciones activas o la sesión es inválida.")
        return

    print(f"[C5-REAL] Total recomendaciones activas detectadas: {len(recs)}")

    purged_count = 0
    for rec in recs:
        # Estructura típica del objeto de recomendación de Substack
        rec_id = rec.get("id")
        target_pub = rec.get("target_publication", {})
        target_subdomain = target_pub.get("subdomain")
        target_name = target_pub.get("name", "Desconocido")

        if not target_subdomain:
            continue

        target_domain = f"{target_subdomain}.substack.com"

        # Verificar si el dominio recomendado pertenece a la mafia
        if target_subdomain in mafia_domains or target_domain in mafia_domains:
            print(f"[ALERTA] Nodo Mafia detectado: {target_name} ({target_domain})")
            if dry_run:
                print(f"[DRY-RUN] Se habría eliminado la recomendación ID: {rec_id}")
                purged_count += 1
            else:
                print(f"[MUTACIÓN] Eliminando recomendación {rec_id}...")
                success = delete_recommendation(subdomain, rec_id, cookie)
                if success:
                    print(f"[SUCCESS] Recomendación con {target_name} eliminada con éxito.")
                    purged_count += 1
                else:
                    print(f"[FALLO] No se pudo eliminar la recomendación {rec_id}.")

    print(f"[C5-REAL] Proceso finalizado. Total nodos mafia purgados: {purged_count}")

if __name__ == "__main__":
    # Configuración de credenciales y modo de ejecución
    # Reemplazar con el subdominio de tu newsletter (ej: "borjamoskv")
    SUBDOMAIN = "borjamoskv"

    # Extraer el cookie "connect.sid" de la sesión de tu navegador en Substack
    COOKIE = "REEMPLAZAR_CON_TU_COOKIE_CONNECT_SID"

    # Cambiar a False para aplicar los cambios reales en producción
    DRY_RUN = True

    if COOKIE == "REEMPLAZAR_CON_TU_COOKIE_CONNECT_SID":
        print("[ERROR] Debes configurar tu cookie connect.sid antes de ejecutar la purga.")
    else:
        purge(SUBDOMAIN, COOKIE, dry_run=DRY_RUN)
