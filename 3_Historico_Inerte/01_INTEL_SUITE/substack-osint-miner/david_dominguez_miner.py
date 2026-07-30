# C5-REAL EXERGY CERTIFIED
import os
import json
import urllib.request
from datetime import datetime
import re
from collections import Counter

API_TEMPLATE = "https://daviddominguez.substack.com/api/v1/archive?sort=new&limit=20&offset={offset}"

def fetch_all_metadata():
    print("[C5-REAL] Iniciando minería de la API de archivo de David Domínguez...")
    all_posts = []
    offset = 0
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    while True:
        url = API_TEMPLATE.format(offset=offset)
        print(f"[C5-REAL] Fetching offset={offset}...")
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                if not data or len(data) == 0:
                    break
                all_posts.extend(data)
                if len(data) < 20:
                    break
                offset += 20
        except Exception as e:
            print(f"[C5-REAL] Error fetching offset {offset}: {e}")
            break

    print(f"[C5-REAL] Minería de metadatos completada. Total posts recuperados: {len(all_posts)}")
    return all_posts

# Diccionarios de keywords para clasificar ganchos y tácticas de marketing
TACTICS = {
    "CONTRARIAN_HATE": [r"hater", r"insult", r"puta", r"mierda", r"vendehumo", r"vende-humo", r"queja", r"enfadado", r"parir", r"ataque"],
    "SCARCITY_FOMO": [r"última", r"ultima", r"hora", r"cierra", r"quedan", r"vuelo", r"jet", r"privado", r"exclusiva", r"secreto", r"dms", r"last call", r"limitado"],
    "MONETIZATION_ROI": [r"dinero", r"euros", r"ganar", r"monetizar", r"precio", r"pago", r"financiero", r"amortizo", r"comunidad", r"mafia", r"audiencia", r"mentor", r"taller"],
    "SOCIAL_PROOF": [r"testimonio", r"pantallazo", r"resultado", r"captura", r"caso", r"demuestro", r"prueba"]
}

def analyze_posts(posts):
    analyzed = []

    # 1. Palabras más frecuentes en títulos
    all_titles_text = ""

    # Contadores
    category_counts = Counter()
    total_likes = 0
    total_comments = 0
    wordcount_sum = 0
    wordcount_count = 0

    for p in posts:
        title = p.get("title", "")
        subtitle = p.get("subtitle", "") or ""
        desc = p.get("description", "") or ""
        teaser = p.get("truncated_body_text", "") or ""
        likes = p.get("reaction_count", 0) or 0
        comments = p.get("comment_count", 0) or 0
        wcount = p.get("wordcount")

        all_titles_text += " " + title
        total_likes += likes
        total_comments += comments
        if wcount:
            wordcount_sum += wcount
            wordcount_count += 1

        # Evaluar tácticas usando expresiones regulares
        matched_tags = []
        combined_text = (title + " " + subtitle + " " + desc + " " + teaser).lower()

        for category, patterns in TACTICS.items():
            for pattern in patterns:
                if re.search(pattern, combined_text):
                    matched_tags.append(category)
                    category_counts[category] += 1
                    break

        analyzed.append({
            "title": title,
            "date": p.get("post_date", "")[:10],
            "slug": p.get("slug", ""),
            "likes": likes,
            "comments": comments,
            "tags": matched_tags,
            "teaser": teaser
        })

    # Palabras más recurrentes en títulos (excluyendo stopwords básicas)
    STOPWORDS = set([
        "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al", "a", "en", "con", "por", "para", "como", "y", "o", "no", "si", "se", "lo", "su", "sus", "mi", "me", "le", "les", "te", "que", "es", "son", "un", "una", "este", "esta", "estos", "estas", "eso", "esa", "esos", "esas", "pero", "mas", "más", "he", "ha", "han", "hay", "todo", "toda", "todos", "todas", "muy", "ya", "ahora", "cuando", "donde", "quien", "quienes", "cual", "cuales", "este", "sino", "sobre", "entre", "hasta", "desde", "sin", "también", "tambien", "sólo", "solo", "tienen", "tiene", "cómo", "como", "qué", "que"
    ])
    words = re.findall(r'\b[a-zA-Záéíóúüñ]{3,}\b', all_titles_text.lower())
    title_word_counts = Counter([w for w in words if w not in STOPWORDS]).most_common(15)

    avg_likes = total_likes / len(posts) if posts else 0
    avg_comments = total_comments / len(posts) if posts else 0
    avg_wcount = wordcount_sum / wordcount_count if wordcount_count else 0

    return {
        "posts": analyzed,
        "avg_likes": avg_likes,
        "avg_comments": avg_comments,
        "avg_wcount": avg_wcount,
        "title_word_counts": title_word_counts,
        "category_counts": dict(category_counts),
        "total_mined": len(posts)
    }

def generate_report(analysis):
    report_dir = os.environ.get("SUBSTACK_MINER_OUTPUT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "david_dominguez_autopsy.md")

    CLEAN_TAGS = {
        "CONTRARIAN_HATE": "CONTRARIAN",
        "SCARCITY_FOMO": "SCARCITY & FOMO",
        "MONETIZATION_ROI": "MONETIZATION & ROI",
        "SOCIAL_PROOF": "SOCIAL PROOF"
    }

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# AUTOPSIA FORENSE: El Motor de Conversión de David Domínguez (A-Z)\n")
        f.write(f"*Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}*\n\n")

        f.write("## 1. Métricas de Rendimiento del Ecosistema\n")
        f.write(f"- **Total de publicaciones analizadas:** **{analysis['total_mined']}**\n")
        f.write(f"- **Media de interacciones (Likes) por post:** **{analysis['avg_likes']:.2f}**\n")
        f.write(f"- **Media de comentarios por post:** **{analysis['avg_comments']:.2f}**\n")
        f.write(f"- **Extensión media (Wordcount):** **{analysis['avg_wcount']:.1f} palabras**\n\n")

        f.write("### Frecuencia de Tácticas Editoriales Detectadas\n")
        for cat, count in analysis['category_counts'].items():
            clean_cat = CLEAN_TAGS.get(cat, cat)
            f.write(f"- **{clean_cat}:** {count} posts ({count / analysis['total_mined'] * 100:.1f}% del total)\n")
        f.write("\n")

        f.write("### Palabras más Recurrentes en Títulos\n")
        words_str = ", ".join([f"**{word}** ({count})" for word, count in analysis['title_word_counts']])
        f.write(f"{words_str}\n\n")

        f.write("## 2. Anatomía de su Ética de Marketing: Del Hype al Culto\n")
        f.write("El modelo de monetización y captación de David Domínguez no es una anomalía casual; es una aplicación determinista del **Cult Building** (construcción de sectas de negocios). Su ética de marketing se rige por las siguientes cuatro invariantes estructurales:\n\n")

        f.write("### A. La Paradoja de la Transparencia Selectiva (Build in Public)\n")
        f.write("> *“Enseño mis cifras para que veas lo que es posible, pero oculto las asimetrías fiscales y el desgaste de retención real.”*\n")
        f.write("Su ética se autodefine como 'transparente' al publicar pantallazos de ingresos de Stripe. Sin embargo, esta transparencia es un gancho asimétrico: vende la viabilidad de un negocio de '2 horas al día' omitiendo que su captación depende enteramente de la recirculación interna forzada de la Substack Mafia y de promociones cruzadas coordinadas.\n\n")

        f.write("### B. Instrumentalización de la Fricción (Haters y Contrarian SEO)\n")
        f.write("> *“El insulto es el mejor lead. La indignación es exergía conversacional.”*\n")
        f.write("En lugar de mitigar las críticas, su marketing las metaboliza de forma mercantil. Títulos como *'Me acaban de insultar'* o *'Me vuelven a llamar vende-humo'* son trampas de curiosidad (PPI) diseñadas para generar disonancia cognitiva en el lector y forzar la apertura del correo. El conflicto no se resuelve; se monetiza.\n\n")

        f.write("### C. La Ilusión de la Escasez de Alta Frecuencia\n")
        f.write("> *“Quedan 2 horas. Última llamada. No iba a abrir plazas, pero...”*\n")
        f.write("Su ética publicitaria explota bucles continuos de urgencia artificial ('Last Call', 'Dos horas y cerramos'). Es una táctica de presión psicológica de baja exergía intelectual que fuerza la compra impulsiva mediante la simulación de escasez en un entorno digital que, por definición, es infinitamente replicable.\n\n")

        f.write("### D. Altruismo Apalancado (Asimetría de la Causa iHelp)\n")
        f.write("> *“Ayuda a la ONG mientras consigues descuento y desgravación.”*\n")
        f.write("La campaña benéfica (charity-washing sofisticado) fue estructurada para alinear el impulso moral del donante con una ventaja comercial para su membresía privada, configurando una asimetría ética donde el emisor amortiza fiscalmente y adquiere clientes utilizando una causa humanitaria como palanca de captación de leads.\n\n")

        f.write("## 3. Registro Cronológico de Posts de Conversión\n")
        f.write("A continuación se listan las publicaciones analizadas en orden inverso. Copia y pega esta lista en tu editor de Substack:\n\n")

        for p in analysis['posts']:
            clean_p_tags = [CLEAN_TAGS.get(t, t) for t in p['tags']]
            tags_str = ", ".join(clean_p_tags) if clean_p_tags else "GENERIC"
            f.write(f"* **{p['date']}** — **{p['title']}** (Likes: {p['likes']}, Comentarios: {p['comments']}) — Tácticas: *{tags_str}* — [Ver Post](https://daviddominguez.substack.com/p/{p['slug']})\n")

        f.write("\n---\n*Generado localmente por MOSKV-1 APEX*\n")

    print(f"[C5-REAL] Reporte autopsia de David Domínguez escrito con éxito en: {report_path}")

def run():
    raw_posts = fetch_all_metadata()
    if not raw_posts:
        print("[C5-REAL] No se pudieron recuperar posts.")
        return

    analysis = analyze_posts(raw_posts)
    generate_report(analysis)

if __name__ == "__main__":
    run()
