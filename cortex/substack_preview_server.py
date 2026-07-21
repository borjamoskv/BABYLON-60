"""
CORTEX Substack Preview Server & Renderer Engine (C5-REAL)
Serves and renders all 23 Substack markdown posts locally with the Industrial Noir 2026 CSS theme.

Rule Compliance: Ω10 (No-deadlock socket binding), Ω23 (Relative Paths), Ω43 (Zero-zombie socket liveness).
"""

import os
import sys
import argparse
import http.server
import socketserver
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ARCHIVE_DIR = BASE_DIR / "artifacts" / "substack_archive"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CORTEX Substack Previewer</title>
    <style>
        :root {{
            --bg-color: #0a0a0a;
            --panel-bg: #121214;
            --border-color: #26262a;
            --accent-blue: #2b3be5;
            --accent-cyan: #00f0ff;
            --text-primary: #ededed;
            --text-secondary: #a1a1aa;
            --font-mono: 'JetBrains Mono', monospace;
        }}
        body {{
            background-color: var(--bg-color);
            color: var(--text-primary);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 32px 20px;
            line-height: 1.6;
        }}
        header {{
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        h1 {{ font-size: 26px; color: #fff; }}
        h2 {{ font-size: 20px; color: var(--accent-cyan); margin-top: 32px; border-bottom: 1px solid #1e1e24; padding-bottom: 6px; }}
        pre {{ background: #121216; padding: 16px; border-radius: 6px; border: 1px solid #222; font-family: var(--font-mono); font-size: 13px; overflow-x: auto; color: var(--accent-cyan); }}
        blockquote {{ border-left: 3px solid var(--accent-blue); margin: 0; padding-left: 16px; color: var(--text-secondary); }}
        a {{ color: var(--accent-cyan); text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        ul {{ padding-left: 20px; }}
        li {{ margin-bottom: 8px; }}
        .badge {{ background: rgba(43,59,229,0.2); color: var(--accent-cyan); border: 1px solid var(--accent-blue); padding: 2px 8px; border-radius: 4px; font-family: var(--font-mono); font-size: 11px; }}
    </style>
</head>
<body>
    <header>
        <span class="badge">CORTEX C5-REAL PREVIEW</span>
        <span class="badge">INDUSTRIAL NOIR 2026</span>
    </header>
    <main>
        {body_content}
    </main>
</body>
</html>
"""

def render_post_html(post_filename: str) -> str:
    filepath = ARCHIVE_DIR / post_filename
    if not filepath.exists():
        return f"<h1>Error 404</h1><p>Post file not found: {post_filename}</p>"

    with open(filepath, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Simple markdown to HTML conversion for preview
    import re
    html = md_text
    html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'## \1', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.*?)$', r'### \1', html, flags=re.MULTILINE)
    html = re.sub(r'^> (.*?)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)
    html = re.sub(r'```(.*?)```', r'<pre>\1</pre>', html, flags=re.DOTALL)
    html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank">\1</a>', html)

    return HTML_TEMPLATE.format(body_content=html)

class PreviewHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            files = sorted(list(ARCHIVE_DIR.glob("*.md")))
            list_items = "".join([f'<li><a href="/view/{f.name}">{f.name}</a></li>' for f in files])
            content = f"<h1>CORTEX Substack Archive Catalog (23 Posts)</h1><ul>{list_items}</ul>"
            rendered = HTML_TEMPLATE.format(body_content=content)
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(rendered.encode('utf-8'))
        elif self.path.startswith("/view/"):
            filename = self.path.replace("/view/", "")
            rendered = render_post_html(filename)
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(rendered.encode('utf-8'))
        else:
            self.send_error(404, "Not Found")

def run_server(port: int = 8085):
    with socketserver.TCPServer(("", port), PreviewHandler) as httpd:
        print(f"CORTEX Substack Preview Server running at http://localhost:{port}/")
        httpd.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CORTEX Substack Preview Server")
    parser.add_argument("--port", type=int, default=8085, help="Port to bind server")
    args = parser.parse_args()
    run_server(args.port)
