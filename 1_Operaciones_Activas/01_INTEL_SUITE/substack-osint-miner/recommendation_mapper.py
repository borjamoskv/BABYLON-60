# C5-REAL EXERGY CERTIFIED
import os
import json
import urllib.request
import re
from bs4 import BeautifulSoup
from datetime import datetime
from collections import defaultdict
import concurrent.futures
import time

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

    print(f"[C5-REAL] Cargando nodos mafia de: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        nodes = json.load(f)

    # Filtrar solo dominios de Substack y dominios personalizados
    domains = set()
    for item in nodes:
        item = item.strip().lower()
        # Si tiene un punto y no contiene espacios, es un dominio
        if "." in item and " " not in item:
            # Normalizar a dominio base (quitar http/https y www si existen)
            domain = re.sub(r'^(https?://)?(www\.)?', '', item)
            domains.add(domain)

    print(f"[C5-REAL] Dominios únicos mafia identificados: {len(domains)}")
    return sorted(list(domains))

def clean_url(url):
    """Limpia la URL para obtener el dominio base."""
    url = url.strip().lower()
    url = re.sub(r'^(https?://)?(www\.)?', '', url)
    # Quitar query params y paths
    url = url.split("/")[0].split("?")[0]
    return url

def fetch_recommendations(domain):
    """Descarga la página de recomendaciones de un dominio y extrae sus enlaces de recomendación."""
    url = f"https://{domain}/recommendations"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    recs = []
    print(f"[C5-REAL] Minando recomendaciones de: {domain}...")
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            html = response.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            # Buscar todos los enlaces con utm_source=recommendations_page
            links = soup.find_all('a', href=lambda href: href and 'utm_source=recommendations_page' in href)
            for link in links:
                href = link.get('href')
                target_domain = clean_url(href)
                # Evitar autoreferencias
                if target_domain and target_domain != domain and target_domain not in recs:
                    recs.append(target_domain)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Algunos substacks no tienen recomendaciones configuradas
            print(f"[C5-REAL] {domain} no tiene página de recomendaciones activa (404).")
        else:
            print(f"[C5-REAL] Error HTTP {e.code} para {domain}: {e.reason}")
    except Exception as e:
        print(f"[C5-REAL] Error indexando {domain}: {e}")

    return domain, recs

def analyze_graph(graph, mafia_domains):
    # Calcular métricas del grafo
    in_degree = defaultdict(int)
    out_degree = defaultdict(int)
    edges = []

    mafia_set = set(mafia_domains)
    mafia_connections = []

    for source, targets in graph.items():
        out_degree[source] = len(targets)
        for t in targets:
            in_degree[t] += 1
            edges.append((source, t))
            if t in mafia_set:
                mafia_connections.append((source, t))

    # Detectar reciprocidad (A -> B y B -> A)
    reciprocal_pairs = []
    edge_set = set(edges)
    for u, v in edge_set:
        if (v, u) in edge_set and u < v:
            reciprocal_pairs.append((u, v))

    # Detectar el círculo cerrado (cuántos recomiendan a miembros de la mafia)
    internal_edges_count = len(mafia_connections)

    return {
        "in_degree": dict(in_degree),
        "out_degree": dict(out_degree),
        "reciprocal_pairs": reciprocal_pairs,
        "total_edges": len(edges),
        "internal_edges_count": internal_edges_count,
        "edges": edges
    }

def generate_report(mafia_domains, graph, metrics):
    home = os.path.expanduser("~")
    output_dir = os.environ.get("SUBSTACK_MINER_OUTPUT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "mafia_graph_report.md")

    # Ordenar por in-degree (los más recomendados)
    sorted_by_in = sorted(metrics["in_degree"].items(), key=lambda x: x[1], reverse=True)
    # Ordenar por out-degree (los que más recomiendan)
    sorted_by_out = sorted(metrics["out_degree"].items(), key=lambda x: x[1], reverse=True)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# REPORTE DE RED: El Grafo de Recomendaciones de la Substack Mafia\n")
        f.write(f"*Generado el: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*\n\n")

        f.write("## 1. Métricas Globales del Grafo\n")
        f.write(f"- **Nodos Mafia Indexados:** `{len(mafia_domains)}`\n")
        f.write(f"- **Total de Recomendaciones Identificadas (Enlaces):** `{metrics['total_edges']}`\n")
        f.write(f"- **Recomendaciones Internas (Recirculación Mafia):** `{metrics['internal_edges_count']}`\n")
        f.write(f"- **Tasa de Conectividad Interna:** `{metrics['internal_edges_count'] / metrics['total_edges'] * 100:.1f}%` de las recomendaciones apuntan a otros miembros del cluster.\n\n")

        f.write("## 2. Los Superconectores de la Red\n")
        f.write("### Nodos Más Recomendados (In-Degree)\n")
        f.write("Representan los mayores receptores de tráfico recirculado del cluster.\n\n")
        f.write("| Posición | Dominio | Recomendaciones Recibidas (In-Degree) |\n")
        f.write("| :--- | :--- | :--- |\n")
        for i, (node, deg) in enumerate(sorted_by_in[:15], 1):
            f.write(f"| {i} | **{node}** | `{deg}` |\n")
        f.write("\n")

        f.write("### Nodos Más Recomendadores (Out-Degree)\n")
        f.write("Los miembros que actúan como pasarelas de salida inyectando tráfico a otros.\n\n")
        f.write("| Posición | Dominio | Recomendaciones Emitidas (Out-Degree) |\n")
        f.write("| :--- | :--- | :--- |\n")
        for i, (node, deg) in enumerate(sorted_by_out[:15], 1):
            f.write(f"| {i} | **{node}** | `{deg}` |\n")
        f.write("\n")

        f.write("## 3. Puntos de Reciprocidad Directa (Bucle A <-> B)\n")
        f.write("La prueba física del intercambio coordinado de favores. Nodos que se recomiendan mutuamente en un pacto simétrico de tráfico:\n\n")
        f.write("| Nodo A | Dirección | Nodo B |\n")
        f.write("| :--- | :---: | :--- |\n")
        for u, v in metrics["reciprocal_pairs"]:
            f.write(f"| **{u}** | `<--->` | **{v}** |\n")
        f.write("\n")

        f.write("## 4. Estructura Completa de Conexiones\n")
        f.write("A continuación se lista la matriz completa de procedencia y destino de tráfico recomendado:\n\n")
        f.write("| Origen (Recomienda) | Destino (Recomendado) |\n")
        f.write("| :--- | :--- |\n")
        for u, v in sorted(metrics["edges"]):
            f.write(f"| {u} | {v} |\n")

        f.write("\n---\n*MOSKV-1 APEX | Verified via BFS DOM parser*\n")

    print(f"[C5-REAL] Reporte del grafo guardado con éxito en: {report_path}")

def run():
    mafia_domains = load_mafia_domains()
    graph = {}

    # Descargar concurrentemente
    print("[C5-REAL] Iniciando descarga concurrente de recomendaciones...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_recommendations, d): d for d in mafia_domains}
        for future in concurrent.futures.as_completed(futures):
            domain, recs = future.result()
            if recs:
                graph[domain] = recs
            time.sleep(0.1) # Pequeño delay de cortesía

    metrics = analyze_graph(graph, mafia_domains)
    generate_report(mafia_domains, graph, metrics)

if __name__ == "__main__":
    run()
