# C5-REAL EXERGY CERTIFIED
import os
import json
import urllib.request
import re
from bs4 import BeautifulSoup
import concurrent.futures
import time

# Endpoints
API_TEMPLATE = "https://daviddominguez.substack.com/api/v1/archive?sort=new&limit=20&offset={offset}"

def clean_url(url):
    url = url.strip().lower()
    url = re.sub(r"^(https?://)?(www\.)?", "", url)
    url = url.split("/")[0].split("?")[0]
    return url

def fetch_david_posts():
    print("[C5-REAL] Descargando histórico de posts de David Domínguez...")
    posts = []
    offset = 0
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    while True:
        url = API_TEMPLATE.format(offset=offset)
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                if not data or len(data) == 0:
                    break
                posts.extend(data)
                if len(data) < 20:
                    break
                offset += 20
        except Exception as e:
            print(f"[C5-REAL] Error en offset {offset}: {e}")
            break

    print(f"[C5-REAL] Posts de David descargados: {len(posts)}")
    return posts

def fetch_recs(domain):
    url = f"https://{domain}/recommendations"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    recs = []
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as response:
            html = response.read().decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")
            links = soup.find_all("a", href=lambda href: href and "utm_source=recommendations_page" in href)
            for link in links:
                href = link.get("href")
                target = clean_url(href)
                if target and target != domain and target not in recs:
                    recs.append(target)
    except Exception:
        pass
    return domain, recs

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

def build_data():
    json_path = resolve_mafia_nodes_path()

    with open(json_path, "r", encoding="utf-8") as f:
        nodes = json.load(f)

    mafia_domains = set()
    for item in nodes:
        item = item.strip().lower()
        if "." in item and " " not in item:
            mafia_domains.add(clean_url(item))

    mafia_list = sorted(list(mafia_domains))

    # 1. Fetch recommendations concurrently
    graph = {}
    print("[C5-REAL] Minando recomendaciones de la red...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_recs, d): d for d in mafia_list}
        for future in concurrent.futures.as_completed(futures):
            domain, recs = future.result()
            if recs:
                graph[domain] = recs
            time.sleep(0.05)

    # 2. Fetch David's posts
    david_posts = fetch_david_posts()

    # 3. Process graph metrics
    in_degree = {}
    out_degree = {}
    edges = []

    for u in mafia_list:
        in_degree[u] = 0
        out_degree[u] = 0

    for source, targets in graph.items():
        out_degree[source] = len(targets)
        for t in targets:
            if t not in in_degree:
                in_degree[t] = 0
            in_degree[t] += 1
            edges.append({"source": source, "target": t})

    reciprocal_pairs = []
    edge_set = set((e["source"], e["target"]) for e in edges)
    for u, v in edge_set:
        if (v, u) in edge_set and u < v:
            reciprocal_pairs.append([u, v])

    # Compile final payload
    payload = {
        "mafia_domains": mafia_list,
        "edges": edges,
        "in_degree": in_degree,
        "out_degree": out_degree,
        "reciprocal_pairs": reciprocal_pairs,
        "david_posts": [{
            "title": p.get("title", ""),
            "subtitle": p.get("subtitle", "") or "",
            "date": p.get("post_date", "")[:10],
            "likes": p.get("reaction_count", 0) or 0,
            "comments": p.get("comment_count", 0) or 0,
            "slug": p.get("slug", ""),
            "wordcount": p.get("wordcount", 0) or 0
        } for p in david_posts]
    }

    return payload

def write_dashboard(data):
    output_dir = os.environ.get("SUBSTACK_MINER_OUTPUT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    html_path = os.path.join(output_dir, "mafia_dashboard.html")

    # Render HTML file
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Substack Mafia OSINT Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Space+Grotesk:wght@400;700&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        :root {{
            --bg-color: #050508;
            --card-bg: #0c0d14;
            --border-color: #1e2235;
            --text-color: #f3f4f6;
            --text-muted: #9ca3af;
            --primary: #2b3be5;
            --primary-glow: rgba(43, 59, 229, 0.4);
            --accent: #ff5600;
            --accent-glow: rgba(255, 86, 0, 0.3);
            --font-main: "Outfit", sans-serif;
            --font-headings: "Space Grotesk", sans-serif;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: var(--font-main);
            overflow-x: hidden;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }}

        header {{
            background-color: rgba(12, 13, 20, 0.8);
            border-bottom: 1px solid var(--border-color);
            padding: 1.5rem 2rem;
            backdrop-filter: blur(12px);
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        header h1 {{
            font-family: var(--font-headings);
            font-size: 1.8rem;
            font-weight: 700;
            letter-spacing: -0.05em;
            background: linear-gradient(135deg, #ffffff 30%, var(--primary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        header .meta-badge {{
            background: rgba(43, 59, 229, 0.1);
            border: 1px solid var(--primary);
            color: #a5b4fc;
            padding: 0.4rem 0.8rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}

        .container {{
            max-width: 1600px;
            width: 100%;
            margin: 0 auto;
            padding: 2rem;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }}

        .grid-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
        }}

        .stat-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
            overflow: hidden;
            transition: border-color 0.3s ease, box-shadow 0.3s ease;
        }}

        .stat-card::after {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background-color: var(--primary);
        }}

        .stat-card.accent::after {{
            background-color: var(--accent);
        }}

        .stat-card:hover {{
            border-color: rgba(255, 255, 255, 0.1);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        }}

        .stat-card h3 {{
            color: var(--text-muted);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }}

        .stat-card .value {{
            font-family: var(--font-headings);
            font-size: 2.2rem;
            font-weight: 700;
        }}

        .main-layout {{
            display: grid;
            grid-template-columns: 350px 1fr;
            gap: 2rem;
            min-height: 700px;
        }}

        @media (max-width: 1024px) {{
            .main-layout {{
                grid-template-columns: 1fr;
            }}
        }}

        .sidebar {{
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }}

        .card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 1.2rem;
            height: 100%;
        }}

        .card h2 {{
            font-family: var(--font-headings);
            font-size: 1.3rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.8rem;
            margin-bottom: 0.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .nav-tabs {{
            display: flex;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            padding: 0.3rem;
            border-radius: 8px;
            gap: 0.2rem;
        }}

        .tab-btn {{
            flex: 1;
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 0.6rem;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            font-family: var(--font-main);
            transition: background 0.2s, color 0.2s;
        }}

        .tab-btn.active {{
            background: var(--primary);
            color: white;
            box-shadow: 0 2px 10px var(--primary-glow);
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
        }}

        #network-container {{
            width: 100%;
            height: 650px;
            border-radius: 12px;
            background-color: #030305;
            border: 1px solid var(--border-color);
            position: relative;
        }}

        .list-items {{
            display: flex;
            flex-direction: column;
            gap: 0.8rem;
            max-height: 500px;
            overflow-y: auto;
            padding-right: 0.5rem;
        }}

        .list-items::-webkit-scrollbar {{
            width: 6px;
        }}

        .list-items::-webkit-scrollbar-thumb {{
            background-color: var(--border-color);
            border-radius: 4px;
        }}

        .list-item {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            padding: 0.8rem 1rem;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background-color 0.2s;
        }}

        .list-item:hover {{
            background: rgba(255, 255, 255, 0.05);
        }}

        .list-item .domain {{
            font-weight: 600;
            font-size: 0.9rem;
            color: #cbd5e1;
        }}

        .list-item .badge {{
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
        }}

        .list-item .badge.in {{
            background: rgba(16, 185, 129, 0.1);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}

        .list-item .badge.out {{
            background: rgba(239, 68, 68, 0.1);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }}

        /* Table styles */
        .table-container {{
            width: 100%;
            overflow-x: auto;
            max-height: 600px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}

        th {{
            background: #090a0f;
            color: var(--text-muted);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 0.05em;
            padding: 1rem;
            border-bottom: 2px solid var(--border-color);
            position: sticky;
            top: 0;
        }}

        td {{
            padding: 1rem;
            border-bottom: 1px solid var(--border-color);
            font-size: 0.9rem;
            color: #e2e8f0;
        }}

        tr:hover td {{
            background: rgba(255, 255, 255, 0.02);
        }}

        .post-link {{
            color: #6366f1;
            text-decoration: none;
            font-weight: 600;
            transition: color 0.2s;
        }}

        .post-link:hover {{
            color: #818cf8;
            text-decoration: underline;
        }}

        .search-box {{
            width: 100%;
            background: #050508;
            border: 1px solid var(--border-color);
            padding: 0.8rem 1rem;
            border-radius: 8px;
            color: var(--text-color);
            font-family: var(--font-main);
            font-size: 0.9rem;
            margin-bottom: 1rem;
            outline: none;
            transition: border-color 0.2s;
        }}

        .search-box:focus {{
            border-color: var(--primary);
            box-shadow: 0 0 8px var(--primary-glow);
        }}

        footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            border-top: 1px solid var(--border-color);
            font-size: 0.8rem;
            letter-spacing: 0.05em;
            background: #07070b;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Substack Mafia OSINT</h1>
        <span class="meta-badge">C5-REAL Ledger verified</span>
    </header>

    <div class="container">
        <div class="grid-stats">
            <div class="stat-card">
                <h3>Nodos Mafia Mapeados</h3>
                <div class="value" id="stat-nodes">0</div>
            </div>
            <div class="stat-card">
                <h3>Total Recomendaciones</h3>
                <div class="value" id="stat-edges">0</div>
            </div>
            <div class="stat-card accent">
                <h3>Pares Recíprocos (Bucles)</h3>
                <div class="value" id="stat-reciprocals">0</div>
            </div>
            <div class="stat-card">
                <h3>Posts David indexados</h3>
                <div class="value" id="stat-posts">0</div>
            </div>
        </div>

        <div class="nav-tabs">
            <button class="tab-btn active" onclick="switchTab('tab-network')">Grafo de Red</button>
            <button class="tab-btn" onclick="switchTab('tab-posts')">Autopsia David Domínguez</button>
            <button class="tab-btn" onclick="switchTab('tab-reciprocals')">Bucles de Reciprocidad</button>
        </div>

        <!-- Tab: Network -->
        <div id="tab-network" class="tab-content active">
            <div class="main-layout">
                <div class="sidebar">
                    <div class="card">
                        <h2>Top Receptores (In-Degree)</h2>
                        <div class="list-items" id="list-in-degree"></div>
                    </div>
                </div>
                <div class="card" style="padding: 0.8rem;">
                    <div id="network-container"></div>
                </div>
            </div>
        </div>

        <!-- Tab: Posts -->
        <div id="tab-posts" class="tab-content">
            <div class="card">
                <h2>Catálogo Completo de Posts (David Domínguez)</h2>
                <input type="text" id="post-search" class="search-box" placeholder="Buscar por título..." onkeyup="filterPosts()">
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Fecha</th>
                                <th>Título</th>
                                <th>Likes</th>
                                <th>Comentarios</th>
                                <th>Palabras</th>
                                <th>Enlace</th>
                            </tr>
                        </thead>
                        <tbody id="posts-table-body"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Tab: Reciprocals -->
        <div id="tab-reciprocals" class="tab-content">
            <div class="card" style="max-width: 800px; margin: 0 auto;">
                <h2>Bucles Recíprocos Identificados</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Nodo A</th>
                                <th>Conexión</th>
                                <th>Nodo B</th>
                            </tr>
                        </thead>
                        <tbody id="reciprocals-table-body"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <footer>
        MOSKV-1 APEX | Diseñado bajo la estética Industrial Noir 2026 | borjamoskv
    </footer>

    <script>
        // Data payload injected from python
        const payload = {json.dumps(data)};

        // Populate stats
        document.getElementById("stat-nodes").innerText = payload.mafia_domains.length;
        document.getElementById("stat-edges").innerText = payload.edges.length;
        document.getElementById("stat-reciprocals").innerText = payload.reciprocal_pairs.length;
        document.getElementById("stat-posts").innerText = payload.david_posts.length;

        // Populate in-degree list
        const inDegArr = Object.entries(payload.in_degree).sort((a,b) => b[1] - a[1]);
        const listIn = document.getElementById("list-in-degree");
        inDegArr.slice(0, 10).forEach(item => {{
            listIn.innerHTML += `
                <div class="list-item">
                    <span class="domain">${{item[0]}}</span>
                    <span class="badge in">${{item[1]}} recs</span>
                </div>
            `;
        }});

        // Populate posts table
        const postsBody = document.getElementById("posts-table-body");
        payload.david_posts.forEach(p => {{
            postsBody.innerHTML += `
                <tr class="post-row">
                    <td>${{p.date}}</td>
                    <td class="post-title" style="font-weight:600;">${{p.title}}</td>
                    <td>${{p.likes}}</td>
                    <td>${{p.comments}}</td>
                    <td>${{p.wordcount}}</td>
                    <td><a href="https://daviddominguez.substack.com/p/${{p.slug}}" target="_blank" class="post-link">Abrir</a></td>
                </tr>
            `;
        }});

        // Populate reciprocals table
        const recBody = document.getElementById("reciprocals-table-body");
        payload.reciprocal_pairs.forEach(pair => {{
            recBody.innerHTML += `
                <tr>
                    <td style="font-weight:600; color:#34d399;">${{pair[0]}}</td>
                    <td style="text-align:center; color:#9ca3af;">&lt;---&gt;</td>
                    <td style="font-weight:600; color:#34d399;">${{pair[1]}}</td>
                </tr>
            `;
        }});

        // Search filter
        function filterPosts() {{
            const query = document.getElementById("post-search").value.toLowerCase();
            const rows = document.querySelectorAll(".post-row");
            rows.forEach(row => {{
                const title = row.querySelector(".post-title").innerText.toLowerCase();
                if (title.includes(query)) {{
                    row.style.display = "";
                }} else {{
                    row.style.display = "none";
                }}
            }});
        }}

        // Tab switching
        function switchTab(tabId) {{
            document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
            document.querySelectorAll(".tab-btn").forEach(el => el.classList.remove("active"));

            document.getElementById(tabId).classList.add("active");
            event.target.classList.add("active");

            if (tabId === "tab-network") {{
                setTimeout(initNetwork, 100);
            }}
        }}

        // Initialize Vis.js Network
        let networkInstance = null;
        function initNetwork() {{
            if (networkInstance) return;

            const nodes = [];
            const edges = [];

            // Build unique nodes
            const uniqueNodes = new Set();
            payload.edges.forEach(e => {{
                uniqueNodes.add(e.source);
                uniqueNodes.add(e.target);
            }});

            uniqueNodes.forEach(nodeId => {{
                const inDeg = payload.in_degree[nodeId] || 0;
                const isMafia = payload.mafia_domains.includes(nodeId);

                nodes.push({{
                    id: nodeId,
                    label: nodeId.split(".")[0],
                    title: `${{nodeId}} (Recomendaciones recibidas: ${{inDeg}})`,
                    value: Math.max(10, inDeg * 3),
                    color: isMafia ? {{
                        background: "#2b3be5",
                        border: "#4f46e5",
                        highlight: {{ background: "#ff5600", border: "#ff7a00" }}
                    }} : {{
                        background: "#1f2937",
                        border: "#374151",
                        highlight: {{ background: "#4b5563", border: "#6b7280" }}
                    }},
                    font: {{ color: "#cbd5e1" }}
                }});
            }});

            // Build edges
            payload.edges.forEach(e => {{
                const isReciprocal = payload.reciprocal_pairs.some(pair =>
                    (pair[0] === e.source && pair[1] === e.target) ||
                    (pair[0] === e.target && pair[1] === e.source)
                );

                edges.push({{
                    from: e.source,
                    to: e.target,
                    arrows: "to",
                    color: isReciprocal ? {{ color: "#ff5600", highlight: "#ff5600" }} : {{ color: "#27272a", highlight: "#4f46e5" }},
                    width: isReciprocal ? 3 : 1
                }});
            }});

            const container = document.getElementById("network-container");
            const networkData = {{
                nodes: new vis.DataSet(nodes),
                edges: new vis.DataSet(edges)
            }};

            const options = {{
                nodes: {{
                    shape: "dot",
                    scaling: {{
                        min: 10,
                        max: 30
                    }},
                    font: {{
                        size: 12,
                        face: "Outfit"
                    }}
                }},
                edges: {{
                    smooth: {{
                        type: "continuous"
                    }}
                }},
                physics: {{
                    barnesHut: {{
                        gravitationalConstant: -8000,
                        springLength: 200
                    }}
                }}
            }};

            networkInstance = new vis.Network(container, networkData, options);
        }}

        // Initial load of network
        window.onload = () => {{
            initNetwork();
        }};
    </script>
</body>
</html>
"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[C5-REAL] Cuadro de mando (dashboard) visual escrito con éxito en: {html_path}")

def run():
    payload = build_data()
    write_dashboard(payload)

if __name__ == "__main__":
    run()
