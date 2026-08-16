# C5_IGNORE_NESTING
#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED
"""
Conversation Transcript Epistemic Auditor CLI
Scans <appDataDir>/brain/<id>/.system_generated/logs/transcript.jsonl files,
extracts user prompts, categorizes sessions, builds friction matrices,
and generates Markdown summary reports and historical atlases.
"""

import argparse
import glob
import json
import os
import re
from datetime import datetime
from collections import defaultdict, Counter

def clean_req(text):
    if not text:
        return ""
    m = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", text, re.DOTALL)
    if m:
        text = m.group(1)
    text = re.sub(r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", "", text, flags=re.DOTALL)
    text = re.sub(r"<EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>", "", text, flags=re.DOTALL)
    text = re.sub(r"^\s*Continue\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def categorize(initial_prompt, all_prompts, files_touched):
    p = (initial_prompt + " " + " ".join(all_prompts)).lower()
    files = " ".join(files_touched).lower()

    if any(k in p or k in files for k in ["escohotado", "libertad", "verdad", "caos", "enemigos del comercio", "prigogine", "ultradiano", "genialidad"]):
        return "Filosofía Escohotado & Epistemología"
    elif any(k in p or k in files for k in ["resend", "smtp", "mail", "hotmail", "babylon60", "spamhaus", "cloudflare", "routing", "webhook", "pixel"]):
        return "Infraestructura Email & Delivery"
    elif any(k in p or k in files for k in ["nexus", "whatsapp", "wa-nexus", "chat"]):
        return "WA-Nexus & WhatsApp MCP"
    elif any(k in p or k in files for k in ["archive.org", "ingestion", "corpus", "hocr", "pdf", "escota"]):
        return "Corpus Ingestion & Archive.org"
    elif any(k in p or k in files for k in ["cortex", "kernel", "rust", "moskv", "robinson", "teorema", "primitives", "gkat", "scitt", "merkle", "ebr", "ffi"]):
        return "Teorema Robinson-Moskv / Kernel C5-REAL"
    elif any(k in p or k in files for k in ["purging", "disk", "clean", "higiene", "entropia", "m1", "macos", "ram", "gb"]):
        return "Higiene macOS & Mantenimiento"
    elif any(k in p or k in files for k in ["zurita", "ignacio", "sanedrín", "jurídico", "derecho", "prevalencia humana", "eu ai act", "contractual"]):
        return "Gobernanza & Estrategia Comercial"
    else:
        return "Investigación & Desarrollo General"

def main():
    parser = argparse.ArgumentParser(description="Audit conversation transcripts from brain directory.")
    parser.add_argument("--brain-dir", default=os.path.expanduser("~/.gemini/antigravity-ide/brain"), help="Path to brain directory")
    parser.add_argument("--output-dir", default=".", help="Output directory for generated markdown reports")
    parser.add_argument("--limit", type=int, default=200, help="Number of recent conversations to process")
    args = parser.parse_args()

    transcripts = glob.glob(os.path.join(args.brain_dir, "*", ".system_generated", "logs", "transcript.jsonl"))
    print(f"🔍 Found {len(transcripts)} transcripts in {args.brain_dir}")

    conv_details = []

    for t_path in transcripts:
        conv_id = t_path.split("/")[-4]
        mtime = os.path.getmtime(t_path)
        dt = datetime.fromtimestamp(mtime)

        user_prompts = []
        files_touched = set()
        tools_used = set()
        step_count = 0

        try:
            with open(t_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not line.strip():
                        continue
                    step_count += 1
                    try:
                        data = json.loads(line)
                        ttype = data.get("type")
                        source = data.get("source")
                        content = data.get("content", "")

                        if ttype == "USER_INPUT" or source == "USER_EXPLICIT":
                            cleaned = clean_req(content)
                            if cleaned and cleaned not in user_prompts:
                                user_prompts.append(cleaned)
                        elif ttype == "PLANNER_RESPONSE" or source == "MODEL":
                            for tc in data.get("tool_calls", []):
                                tname = tc.get("name", "")
                                if tname:
                                    tools_used.add(tname)
                                args_tc = tc.get("args", {})
                                for k in ["TargetFile", "AbsolutePath", "SearchPath", "Cwd"]:
                                    if k in args_tc and isinstance(args_tc[k], str):
                                        fname = args_tc[k].split("/")[-1]
                                        if fname:
                                            files_touched.add(fname)
                    except Exception:
                        pass
        except Exception:
            pass

        initial_p = user_prompts[0] if user_prompts else "(Sin prompt explicito)"
        category = categorize(initial_p, user_prompts, list(files_touched))

        conv_details.append({
            "conv_id": conv_id,
            "mtime": mtime,
            "date_str": dt.strftime("%Y-%m-%d %H:%M"),
            "step_count": step_count,
            "prompt_count": len(user_prompts),
            "initial_prompt": initial_p,
            "user_prompts": user_prompts,
            "category": category,
            "files_touched": list(files_touched),
            "tools_used": list(tools_used)
        })

    conv_details.sort(key=lambda x: x["mtime"], reverse=True)
    target_convs = conv_details[:args.limit]

    os.makedirs(args.output_dir, exist_ok=True)

    summary_file = os.path.join(args.output_dir, f"resumen_ultimas_{len(target_convs)}_conversaciones.md")

    md_lines = [
        f"# Resumen Ejecutivo y Auditoría de Conversaciones ({len(target_convs)} Sesiones)\n",
        f"> **Fecha del reporte:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"> **Total analizante:** {len(target_convs)} conversaciones de {len(conv_details)} históricas\n",
        "## 1. Distribución por Categorías\n",
        "| Categoría | Sesiones | % Total |",
        "| :--- | :---: | :---: |"
    ]

    cat_counts = Counter(c["category"] for c in target_convs)
    for cat, cnt in cat_counts.most_common():
        pct = (cnt / len(target_convs)) * 100
        md_lines.append(f"| **{cat}** | {cnt} | {pct:.1f}% |")

    md_lines.append("\n---\n## 2. Registro Cronológico Completo\n")
    md_lines.append("| ID | Fecha | Categoría | Pasos | Prompt Inicial |")
    md_lines.append("| :---: | :---: | :--- | :---: | :--- |")

    for c in target_convs:
        cid = c["conv_id"][:8]
        dt_s = c["date_str"]
        cat = c["category"]
        steps = c["step_count"]
        p = c["initial_prompt"].replace("|", "\\|")[:90]
        md_lines.append(f"| `{cid}` | {dt_s} | {cat} | {steps} | {p} |")

    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"✅ Generated report: {summary_file}")

if __name__ == "__main__":
    main()
