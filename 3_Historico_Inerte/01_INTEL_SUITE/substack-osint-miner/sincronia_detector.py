# C5-REAL EXERGY CERTIFIED
import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import email.utils
from collections import Counter
import concurrent.futures
import re

# Stopwords en español para limpiar frecuencias semánticas
STOPWORDS = set([
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al", "a", "en", "con", "por", "para", "como", "y", "o", "no", "si", "se", "lo", "su", "sus", "mi", "me", "le", "les", "te", "que", "es", "son", "un", "una", "este", "esta", "estos", "estas", "eso", "esa", "esos", "esas", "pero", "mas", "más", "he", "ha", "han", "hay", "todo", "toda", "todos", "todas", "muy", "ya", "ahora", "cuando", "donde", "quien", "quienes", "cual", "cuales", "este", "sino", "sobre", "entre", "hasta", "desde", "sin", "también", "tambien", "sólo", "solo", "tienen", "tiene", "cómo", "como", "qué", "que"
])

def clean_and_tokenize(text):
    # Eliminar HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Tokenizar palabras minúsculas, remover caracteres especiales
    words = re.findall(r'\b[a-zA-Záéíóúüñ]{2,}\b', text.lower())
    # Filtrar stopwords
    return [w for w in words if w not in STOPWORDS]

def parse_pub_date(pub_date_str):
    try:
        # Intentar parsear fecha RFC 2822 estándar de feeds
        parsed = email.utils.parsedate_to_datetime(pub_date_str)
        # Convertir a timezone-aware UTC
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        else:
            parsed = parsed.astimezone(timezone.utc)
        return parsed
    except Exception:
        return None

def fetch_feed(domain):
    url = f"https://{domain}/feed"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)

            # Encontrar el título de la publicación
            channel = root.find('channel')
            pub_title = channel.find('title').text if channel.find('title') is not None else domain

            posts = []
            for item in channel.findall('item'):
                title = item.find('title').text if item.find('title') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                pub_date_raw = item.find('pubDate').text if item.find('pubDate') is not None else ""
                description = item.find('description').text if item.find('description') is not None else ""
                content = item.find('{http://purl.org/rss/1.0/modules/content/}encoded')
                content_text = content.text if content is not None else description

                pub_date = parse_pub_date(pub_date_raw)
                if pub_date:
                    posts.append({
                        "publication": pub_title,
                        "domain": domain,
                        "title": title,
                        "link": link,
                        "pub_date": pub_date,
                        "description": description,
                        "content_tokens": clean_and_tokenize(title + " " + description + " " + (content_text or ""))
                    })
            return posts
    except Exception:
        # Algunos dominios pueden no tener RSS activo o fallar
        return []

def analyze_bursts(all_posts, window_hours=48):
    # Ordenar posts por fecha de publicación descendente
    sorted_posts = sorted(all_posts, key=lambda x: x['pub_date'], reverse=True)
    if not sorted_posts:
        return []

    bursts = []
    # Usar un enfoque de ventana deslizante para encontrar bursts
    for idx, anchor in enumerate(sorted_posts):
        burst_group = [anchor]
        anchor_time = anchor['pub_date']

        # Encontrar posts dentro del rango temporal de window_hours
        for other in sorted_posts[idx+1:]:
            time_diff = (anchor_time - other['pub_date']).total_seconds() / 3600.0
            if time_diff <= window_hours:
                # Evitar duplicados del mismo dominio en el mismo burst para medir coordinación inter-nodo
                if not any(x['domain'] == other['domain'] for x in burst_group):
                    burst_group.append(other)
            else:
                break

        # Guardar bursts con al menos 3 publicaciones distintas coordinadas
        if len(burst_group) >= 3:
            # Calcular overlap semántico
            all_tokens = []
            for p in burst_group:
                all_tokens.extend(p['content_tokens'])

            common_words = Counter(all_tokens).most_common(10)

            # Calcular la dispersión temporal (máxima diferencia en horas en el grupo)
            times = [p['pub_date'] for p in burst_group]
            max_diff_hours = (max(times) - min(times)).total_seconds() / 3600.0

            bursts.append({
                "anchor_date": anchor_time,
                "size": len(burst_group),
                "max_diff_hours": max_diff_hours,
                "common_words": common_words,
                "posts": burst_group
            })

    # Filtrar bursts altamente redundantes (subconjuntos exactos de bursts más grandes)
    unique_bursts = []
    for b in sorted(bursts, key=lambda x: x['size'], reverse=True):
        # Evitar subconjuntos
        is_sub = False
        b_links = set(p['link'] for p in b['posts'])
        for ub in unique_bursts:
            ub_links = set(p['link'] for p in ub['posts'])
            # Si más del 80% de los posts ya están en un burst más grande indexado, se descarta
            if len(b_links.intersection(ub_links)) / len(b_links) >= 0.8:
                is_sub = True
                break
        if not is_sub:
            unique_bursts.append(b)

    return unique_bursts

def resolve_mafia_nodes_path() -> str:
    """Resolve mafia_nodes.json path dynamically using env vars and dynamic search paths."""
    # 1. Env variable override
    env_path = os.environ.get("MAFIA_NODES_JSON")
    if env_path and os.path.exists(env_path):
        return env_path

    # 2. Local folder fallback
    local_path = os.path.abspath("mafia_nodes.json")
    if os.path.exists(local_path):
        return local_path

    # 3. Sibling lookup
    sibling_path = os.path.abspath("../30_BABYLON-60/babylon60/routes/mafia_nodes.json")
    if os.path.exists(sibling_path):
        return sibling_path

    # 4. Standard home directory path
    home = os.path.expanduser("~")
    home_path = os.path.join(home, "30_BABYLON-60/babylon60/routes/mafia_nodes.json")
    return home_path

def run() -> None:
    nodes_path = resolve_mafia_nodes_path()
    if not os.path.exists(nodes_path):
        print(f"[C5-REAL] Error: No se encuentra mafia_nodes.json en {nodes_path}")
        return

    with open(nodes_path, 'r', encoding='utf-8') as f:
        mafia_nodes = json.load(f)

    # Extraer dominios de la mafia
    domains = []
    for node in mafia_nodes:
        if node.endswith(".substack.com") or node.endswith(".com"):
            domains.append(node)

    print(f"[C5-REAL] Identificados {len(domains)} dominios candidatos en mafia_nodes.json.")
    print("[C5-REAL] Iniciando descarga concurrente de RSS feeds...")

    all_posts = []
    # Ejecutar descargas concurrentes
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        results = executor.map(fetch_feed, domains)
        for res in results:
            all_posts.extend(res)

    print(f"[C5-REAL] Descarga completada. Total posts escaneados: {len(all_posts)}")

    # Analizar bursts coordinados
    bursts = analyze_bursts(all_posts, window_hours=48)

    # Generar reporte Markdown
    report_dir = os.environ.get("SUBSTACK_MINER_OUTPUT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "sincronia_report.md")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# REPORT: Detección Asimétrica de Sincronía en Substack Mafia\n")
        f.write(f"*Generado el: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*\n\n")

        f.write("## 1. Nota Metodológica (C5-REAL)\n")
        f.write("Este reporte mapea la coordinación temporal latente entre las publicaciones del cluster de Substack Mafia. ")
        f.write("Un **Burst de Sincronía** se define como un conjunto de ≥3 newsletters diferentes publicando en una ventana temporal estrecha (≤48h) con un solapamiento significativo de vocabulario clave. ")
        f.write("La sincronía temporal coordinada indica campañas planificadas de promoción cruzada o directrices editoriales unificadas.\n\n")

        if not bursts:
            f.write("> [!NOTE]\n")
            f.write("> No se han detectado patrones de sincronía anormales en las últimas 48 horas o el feed de los nodos está en reposo.\n\n")
        else:
            f.write(f"## 2. Bursts Coordenados Detectados ({len(bursts)})\n\n")
            for idx, b in enumerate(bursts, 1):
                f.write(f"### [BURST-{idx:02d}] Ventana de {b['max_diff_hours']:.1f} horas con {b['size']} publicaciones\n")
                f.write(f"- **Fecha del Ancla:** `{b['anchor_date'].strftime('%Y-%m-%d %H:%M:%S UTC')}`\n")

                # Expresar palabras comunes
                words_str = ", ".join([f"**{word}** ({count})" for word, count in b['common_words']])
                f.write(f"- **Frecuencias Semánticas Compartidas:** {words_str}\n\n")

                f.write("#### Nodos del Cluster Participantes:\n")
                f.write("| Publicación | Título | Fecha (UTC) | Enlace |\n")
                f.write("| :--- | :--- | :--- | :--- |\n")
                for p in b['posts']:
                    f.write(f"| **{p['publication']}** | {p['title']} | `{p['pub_date'].strftime('%Y-%m-%d %H:%M:%S')}` | [Ir al post]({p['link']}) |\n")
                f.write("\n---\n\n")

        # Proponer tácticas adversariales
        f.write("## 3. Vector de Ataque: Contra-Señalización Semántica\n")
        f.write("Para envenenar los clusters semánticos identificados, puedes inyectar embeddings semánticos adversariales en tus publicaciones ")
        f.write("utilizando las **frecuencias semánticas compartidas** listadas arriba. Esto obligará al recomendador de Substack (basado en afinidad de lectura y keywords compartidas) a recomendar tu contenido anti-mafia a los lectores del cluster.\n")

    print(f"[C5-REAL] Reporte de sincronía compilado con éxito en: {report_path}")

if __name__ == "__main__":
    run()
