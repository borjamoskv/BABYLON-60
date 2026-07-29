# C5-REAL EXERGY CERTIFIED
"""
Generate Interactive HTML Dashboard for Mined Substack Data
"""

import json
import os
import sys

def generate_html(json_file_path: str, output_html_path: str):
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    profile = data.get("profile", {})
    notes = data.get("notes", [])
    posts = data.get("posts", [])
    recommendations = data.get("recommendations", [])

    notes_html = ""
    for note in notes:
        if note.get("body"):
            body_clean = note.get("body").replace("\n", "<br>")
            notes_html += f"""
            <div class="card note-card">
                <div class="note-header">
                    <span class="badge note-badge">NOTE {note.get('note_id')}</span>
                    <a href="{note.get('url')}" target="_blank" class="note-link">Ver en Substack ↗</a>
                </div>
                <div class="note-body">{body_clean}</div>
                <div class="note-footer">
                    <span>❤ {note.get('reactions', 0)} Reacciones</span>
                    <span>🔄 {note.get('restacks', 0)} Restacks</span>
                    <span>💬 {note.get('replies', 0)} Respuestas</span>
                </div>
            </div>
            """

    posts_html = ""
    for post in posts:
        tts_badge = f'<a href="{post.get("tts_audio_url")}" target="_blank" class="tts-link">🎧 Escuchar Audio TTS</a>' if post.get("tts_audio_url") else ""
        posts_html += f"""
        <div class="card post-card">
            <div class="post-header">
                <h3><a href="{post.get('canonical_url')}" target="_blank">{post.get('title')}</a></h3>
                <span class="badge word-badge">{post.get('wordcount', 0)} palabras</span>
            </div>
            <p class="subtitle">{post.get('subtitle', '')}</p>
            <div class="post-footer">
                <span>❤ {post.get('reaction_count', 0)} Me Gusta</span>
                <span>💬 {post.get('comment_count', 0)} Comentarios</span>
                {tts_badge}
            </div>
        </div>
        """

    recs_html = ""
    for rec in recommendations:
        recs_html += f'<li class="rec-item"><a href="https://{rec}" target="_blank">🔗 {rec}</a></li>'

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Substack Intel Dashboard — @{profile.get('handle', 'victormillan')}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Lora:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #0d0f12;
            --card-bg: rgba(22, 25, 33, 0.8);
            --border: rgba(255, 255, 255, 0.08);
            --accent: #ff6719;
            --accent-glow: rgba(255, 103, 25, 0.25);
            --text-main: #f0f2f5;
            --text-muted: #9ba3af;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            line-height: 1.6;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        header {{
            display: flex;
            align-items: center;
            gap: 20px;
            padding: 30px;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            backdrop-filter: blur(12px);
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }}

        .avatar {{
            width: 90px;
            height: 90px;
            border-radius: 50%;
            border: 3px solid var(--accent);
            box-shadow: 0 0 20px var(--accent-glow);
        }}

        .profile-info h1 {{
            font-size: 1.8rem;
            font-weight: 700;
            color: #fff;
        }}

        .profile-info .handle {{
            color: var(--accent);
            font-weight: 600;
            margin-bottom: 8px;
        }}

        .profile-info .bio {{
            color: var(--text-muted);
            font-size: 0.95rem;
            max-width: 800px;
        }}

        .grid {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 30px;
        }}

        @media (max-width: 900px) {{
            .grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .section-title {{
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .section-title::before {{
            content: '';
            width: 4px;
            height: 20px;
            background: var(--accent);
            border-radius: 2px;
        }}

        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }}

        .card:hover {{
            transform: translateY(-2px);
            border-color: rgba(255, 103, 25, 0.4);
        }}

        .note-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}

        .badge {{
            font-size: 0.75rem;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 20px;
            text-transform: uppercase;
        }}

        .note-badge {{
            background: rgba(255, 103, 25, 0.15);
            color: var(--accent);
            border: 1px solid rgba(255, 103, 25, 0.3);
        }}

        .word-badge {{
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
        }}

        .note-link {{
            color: var(--text-muted);
            text-decoration: none;
            font-size: 0.85rem;
        }}

        .note-link:hover {{
            color: var(--accent);
        }}

        .note-body {{
            font-family: 'Lora', serif;
            font-size: 1.05rem;
            color: #e2e8f0;
            margin-bottom: 15px;
            white-space: pre-line;
        }}

        .note-footer, .post-footer {{
            display: flex;
            gap: 20px;
            font-size: 0.85rem;
            color: var(--text-muted);
            border-top: 1px solid var(--border);
            padding-top: 12px;
        }}

        .post-card h3 a {{
            color: #fff;
            text-decoration: none;
        }}

        .post-card h3 a:hover {{
            color: var(--accent);
        }}

        .subtitle {{
            color: var(--text-muted);
            font-size: 0.9rem;
            margin: 8px 0 15px 0;
        }}

        .tts-link {{
            color: #38bdf8;
            text-decoration: none;
            margin-left: auto;
            font-weight: 600;
        }}

        .tts-link:hover {{
            text-decoration: underline;
        }}

        .rec-list {{
            list-style: none;
        }}

        .rec-item {{
            margin-bottom: 10px;
        }}

        .rec-item a {{
            color: var(--text-main);
            text-decoration: none;
            font-size: 0.9rem;
            display: block;
            padding: 10px 14px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border);
            border-radius: 8px;
            transition: all 0.2s ease;
        }}

        .rec-item a:hover {{
            background: rgba(255, 103, 25, 0.1);
            border-color: var(--accent);
            color: var(--accent);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <img src="{profile.get('photo_url', '')}" alt="{profile.get('name')}" class="avatar">
            <div class="profile-info">
                <h1>{profile.get('name')}</h1>
                <div class="handle">@{profile.get('handle')} | User ID: {profile.get('id')}</div>
                <div class="bio">{profile.get('bio')}</div>
            </div>
        </header>

        <div class="grid">
            <div class="left-col">
                <div class="section-title">Substack Notes Extraídas ({len(notes)})</div>
                {notes_html}

                <div class="section-title" style="margin-top: 40px;">Publicaciones Recientes ({len(posts)})</div>
                {posts_html}
            </div>

            <div class="right-col">
                <div class="section-title">Red de Recomendaciones ({len(recommendations)})</div>
                <ul class="rec-list">
                    {recs_html}
                </ul>
            </div>
        </div>
    </div>
</body>
</html>
"""

    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[C5-REAL] Dashboard HTML interactivo generado en: {output_html_path}")

if __name__ == "__main__":
    json_path = sys.argv[1] if len(sys.argv) > 1 else "output/intel_victormillan.json"
    html_path = sys.argv[2] if len(sys.argv) > 2 else "output/intel_victormillan.html"
    generate_html(json_path, html_path)
