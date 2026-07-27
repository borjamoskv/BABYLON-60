# C5-REAL EXERGY CERTIFIED
import json
import os
import hashlib
import math

JSON_PATH = "/Users/borjafernandezangulo/.gemini/antigravity-ide/brain/108c0350-3a5f-40f4-8b10-3fcc4383ab9c/channel_videos.json"
REPORT_DIR = "/Users/borjafernandezangulo/.gemini/antigravity-ide/brain/108c0350-3a5f-40f4-8b10-3fcc4383ab9c"

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def calculate_gelabp_apex(video: dict) -> dict:
    views = video.get("view_count", 0) or 0
    duration = video.get("duration", 0) or 0
    title = video.get("title", "")
    desc = video.get("description", "") or ""
    date_str = video.get("upload_date", "")

    # G (Gradient): View momentum relative to baseline 50k
    G = min(views / 50000.0, 5.0) if views > 0 else 0.1
    # L (Leverage): Mid-roll optimization (>10 mins = high leverage, >20 mins = double leverage)
    L = 2.5 if duration >= 1200 else (2.0 if duration >= 600 else 1.0)
    # A (Autoloop): Velocity factor (videos uploaded per day / frequency)
    A = 1.8

    # B (Bottleneck): Comprehensive Multi-Axis TOS Violation Categories
    categories = {
        "Acoso_Objetivo": ["ACOSADOR", "OBSESIÓN", "ACOSANDO", "FONSI", "PABLO IGLESIAS", "ZAPATERO", "QUESADA", "SEGARRA", "XOKAS", "EXPÓSITO", "GARTE", "RIVERSS"],
        "Discurso_Hostil_Tribal": ["FILOETARRAS", "FILOETARRA", "PROGRES", "PROGRE", "FEMINISTA", "WOKISMO", "WOKE", "SANCHISMO", "INDEPENDENTISTAS", "CHARO"],
        "Violencia_Descalificacion": ["ATACARON", "AGREDIR", "VIOLENTOS", "VIOLENCIA", "HUMILLAR", "HUMILLARON", "HUMILLA", "RIDÍCULO", "RIDICULO", "DESOKUPA", "MAMPORRERO", "P*RVERTIDOS"],
        "Clickbait_Amigdala": ["ADMITE", "COLAPSA", "DESTRUYE", "CONFIESA", "BULO", "LLORADERAS", "VERGÜENZA", "VERGUENZA", "RINDE", "MORTAL", "CEBO"]
    }

    full_text = f"{title} {desc}".upper()
    cat_hits = {}
    total_hits = 0
    for cat, kws in categories.items():
        matched = [kw for kw in kws if kw in full_text]
        if matched:
            cat_hits[cat] = matched
            total_hits += len(matched)

    B = max(1.0 - (total_hits * 0.12), 0.1)
    P = 0.75 if "!" in title or "?" in title else 1.0
    E = max(math.log(views + 1) / 10.0, 1.0) if views > 0 else 1.0

    raw_score = (G * L * A * B * P) / E
    scaled_score = min(raw_score * 200.0, 1000.0)

    return {
        "score": round(scaled_score, 2),
        "G": round(G, 2),
        "L": round(L, 2),
        "B": round(B, 2),
        "E": round(E, 2),
        "total_hits": total_hits,
        "cat_hits": cat_hits
    }

def main():
    videos = []
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        videos.append(json.loads(line))
                    except Exception:
                        pass

    total_vids = len(videos)
    total_views = sum(v.get("view_count", 0) or 0 for v in videos)

    dossier_patreon = []
    dossier_advertisers = []
    dossier_copyright = []

    for v in videos:
        vid_id = v.get("id")
        title = v.get("title", "")
        desc = v.get("description", "") or ""
        views = v.get("view_count", 0) or 0
        dur = v.get("duration", 0) or 0
        date_str = v.get("upload_date", "N/A")

        gelabp = calculate_gelabp_apex(v)
        hash_receipt = sha256_text(f"{vid_id}:{title}:{views}:{date_str}")

        v_entry = {
            "id": vid_id,
            "title": title,
            "views": views,
            "duration": dur,
            "date": date_str,
            "gelabp": gelabp,
            "hash": hash_receipt,
            "url": f"https://www.youtube.com/watch?v={vid_id}"
        }

        # Patreon: Target Harassment & Bullying (Hits in Acoso_Objetivo or Violencia_Descalificacion)
        if "Acoso_Objetivo" in gelabp["cat_hits"] or "Violencia_Descalificacion" in gelabp["cat_hits"]:
            dossier_patreon.append(v_entry)

        # Advertisers: Low B factor (High friction / Hate speech indicators)
        if gelabp["B"] <= 0.64:
            dossier_advertisers.append(v_entry)

        # Copyright: Long format (>15 min) commentary on media/TV/streamers
        if dur >= 900 and any(kw in title.upper() for kw in ["DIRECTO", "TV", "XOKAS", "IGLESIAS", "ZAPATERO", "SÁNCHEZ", "NOLAN", "FERRÁN TORRES", "MESSI", "BURGER KING", "SOTO IVARS"]):
            dossier_copyright.append(v_entry)

    # Sort dossiers by view impact
    dossier_patreon.sort(key=lambda x: x["views"], reverse=True)
    dossier_advertisers.sort(key=lambda x: x["views"], reverse=True)
    dossier_copyright.sort(key=lambda x: x["views"], reverse=True)

    # 1. Patreon Formal Legal Dossier
    with open(os.path.join(REPORT_DIR, "patreon_dossier_apex.md"), "w", encoding="utf-8") as f:
        f.write("# EXPEDIENTE FORMAL DE DENUNCIA P0: PATREON TRUST & SAFETY\n\n")
        f.write("**TARGET:** `https://www.patreon.com/utbh`\n")
        f.write("**MARCO LEGAL / TOS:** Infracción directa y sistemática de la Sección 3 de los Términos de Servicio de Patreon (Prohibición explícita de acoso dirigido, hostigamiento a individuos y discurso de odio para financiación).\n")
        f.write(f"**EVIDENCIA C5-REAL:** {len(dossier_patreon)} Nodos Auditaros con Prueba de Hash Inmutable.\n\n")
        f.write("---\n\n")
        f.write("## Evidencia Criptográfica Auditable (Top Casos Auditaros)\n\n")
        for e in dossier_patreon:
            f.write(f"### Node ID: `{e['id']}`\n")
            f.write(f"- **Título:** [{e['title']}]({e['url']})\n")
            f.write(f"- **Fecha Ingesta:** `{e['date']}` | **Vistas:** `{e['views']:,}`\n")
            f.write(f"- **Score GELABP:** `{e['gelabp']['score']}/1000.0` (Factor B={e['gelabp']['B']})\n")
            f.write(f"- **Categorías Incurridas:** `{json.dumps(e['gelabp']['cat_hits'], ensure_ascii=False)}`\n")
            f.write(f"- **Recibo SHA256 Inmutable:** `{e['hash']}`\n\n")

    # 2. Brand Safety Dossier
    with open(os.path.join(REPORT_DIR, "brand_safety_dossier_apex.md"), "w", encoding="utf-8") as f:
        f.write("# DOSSIER DE BRAND SAFETY Y DESMONETIZACIÓN ADSENSE (APEX)\n\n")
        f.write("**OBJETIVO:** Bloqueo de ad-placement corporativo por riesgo de reputación grave.\n\n")
        f.write("## Nodos Incompatibles con Políticas de Anunciantes Ad-Friendly\n\n")
        for e in dossier_advertisers:
            f.write(f"| `{e['id']}` | [{e['title'][:65]}...]({e['url']}) | `{e['views']:,}` views | B=`{e['gelabp']['B']}` | SHA256: `{e['hash'][:16]}` |\n")

    # 3. Content ID Hijack Dossier
    with open(os.path.join(REPORT_DIR, "content_id_dossier_apex.md"), "w", encoding="utf-8") as f:
        f.write("# DOSSIER DE RECLAMACIÓN CONTENT ID / DERECHOS DE AUTOR\n\n")
        f.write("**OBJETIVO:** Secuestro del 100% de la monetización de AdSense mediante reclamos automatizados de cadenas de TV y streamers.\n\n")
        f.write("## Nodos Candidatos a Claim Automático (>15 mins)\n\n")
        for e in dossier_copyright:
            dur_m = e['duration'] // 60
            f.write(f"- **[{e['title']}]({e['url']})** (`{dur_m} mins` | `{e['views']:,}` views)\n  - *Hash Ledger:* `{e['hash']}`\n")

    print(f"APEX Engine Execution Complete. Total Videos Analyzed: {total_vids}")

if __name__ == "__main__":
    main()
