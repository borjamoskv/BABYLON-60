#!/usr/bin/env python3
"""
Generador estático de naroagutierrezgil.com
Sitio de Naroa Gutiérrez Gil — la obra como protagonista.

Uso:  python3 build_site.py [--mirror DIR]
      --mirror: carpeta con el espejo de naroa.online (assets/, data/, index.html)

Salida: ./web/  (carpeta lista para `vercel --prod`)
"""

import logging
import argparse
import html
import json
import os
import shutil
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = date.today().isoformat()
DOMAIN = "https://naroagutierrezgil.com"

# ---------------------------------------------------------------- OBRAS
# Solo datos verificables: títulos/captions publicados en naroa.online
# y metadatos de data/database.json cuando la correspondencia es exacta.
WORKS = [
    {
        "slug": "marilyn-rocks",
        "title": "Marilyn Rocks",
        "img": "marilyn-rocks--qPeLHxE.webp",
        "technique": "Acrílico sobre pizarra",
        "series": "Rocks",
        "desc": "Retrato hiperrealista de Marilyn Monroe en acrílico sobre pizarra con mica mineral.",
    },
    {
        "slug": "amy",
        "title": "Amy",
        "img": "hq-amy-BRTriASV.webp",
        "year": 2023,
        "technique": "Acrílico sobre pizarra",
        "series": "Rocks",
        "desc": "Retrato de Amy Winehouse en hiperrealismo POP sobre pizarra natural.",
    },
    {
        "slug": "james-dean",
        "title": "James Dean",
        "img": "hq-james-CjsTrO7r.webp",
        "series": "Rocks",
        "desc": "Retrato de James Dean, icono eterno del cine, en hiperrealismo POP.",
    },
    {
        "slug": "johnny",
        "title": "Johnny",
        "img": "hq-johnny-5ueL8eU0.webp",
        "series": "Rocks",
        "desc": "Retrato de Johnny Depp en hiperrealismo POP sobre soporte mineral.",
    },
    {
        "slug": "retrato-i",
        "title": "Retrato I",
        "img": "hq-portrait-1-bV-_WHlX.webp",
        "desc": "Retrato hiperrealista por encargo — la mirada como centro de la obra.",
    },
    {
        "slug": "el-gran-dakari",
        "title": "El Gran Dakari",
        "img": "el-gran-dakari-C1tAWAhR.webp",
        "desc": "Retrato de gran formato con la fuerza expresiva del hiperrealismo POP.",
    },
    {
        "slug": "audrey-hepburn",
        "title": "Audrey Hepburn",
        "img": "audrey-hepburn-DbIBTtIp.webp",
        "desc": "Audrey Hepburn reimaginada — elegancia clásica en clave pop contemporánea.",
    },
    {
        "slug": "geisha",
        "title": "Geisha",
        "img": "geisha-MfRtKWdu.webp",
        "desc": "Retrato de inspiración japonesa — delicadeza y color en técnica mixta.",
    },
    {
        "slug": "lagrimas-de-oro",
        "title": "Lágrimas de Oro",
        "img": "lagrimas-de-oro-DikHc-Tk.webp",
        "desc": "La emoción hecha materia: lágrimas doradas sobre un rostro hiperrealista.",
    },
    {
        "slug": "love",
        "title": "Love",
        "img": "love-DA7L_L5F.webp",
        "desc": "Una declaración en color — el amor como gesto pictórico.",
    },
    {
        "slug": "la-pensadora",
        "title": "La Pensadora",
        "img": "la-pensadora-CFHSnMA0.webp",
        "desc": "Retrato introspectivo — el pensamiento como paisaje interior.",
    },
    {
        "slug": "amor-en-conserva",
        "title": "Amor en Conserva",
        "img": "amor-en-conserva-CMHRIKXx.webp",
        "technique": "Intervención en lata de conserva",
        "series": "En.lata.das",
        "desc": "Intervención artística en lata de conserva — el amor, listo para abrir.",
    },
    {
        "slug": "baroque-farrokh",
        "title": "Baroque Farrokh",
        "img": "baroque-farrokh-mjg4ClA9.webp",
        "series": "Tributos Musicales",
        "desc": "Tributo barroco a Farrokh Bulsara — Freddie Mercury como icono clásico.",
    },
    {
        "slug": "cantinflas-i",
        "title": "Cantinflas I",
        "img": "cantinflas-0-D712oJYO.webp",
        "desc": "Homenaje a Mario Moreno «Cantinflas» — humor y humanidad en retrato.",
    },
    {
        "slug": "dar-la-lata",
        "title": "Dar la Lata",
        "img": "dar-la-lata-DxWlKgS-.webp",
        "technique": "Reciclaje artístico",
        "series": "En.lata.das",
        "desc": "Reciclaje artístico — la lata cotidiana convertida en pieza única.",
    },
    {
        "slug": "mr-fahrenheit",
        "title": "Mr. Fahrenheit",
        "img": "mr-fahrenheit-BzcoVisa.webp",
        "technique": "Pintura sobre pizarra",
        "series": "Tributos Musicales",
        "desc": "Freddie Mercury a 200 grados — tributo musical sobre pizarra.",
    },
    {
        "slug": "divinos-amy",
        "title": "DiviNos Amy",
        "img": "divinos-amy-Celol3XJ.webp",
        "series": "DiviNos",
        "desc": "Amy Winehouse en la serie DiviNos — iconos divinos, humanos demasiado humanos.",
    },
    {
        "slug": "divinos-marilyn",
        "title": "DiviNos Marilyn",
        "img": "divinos-marilyn-By8KYPMI.webp",
        "series": "DiviNos",
        "desc": "Marilyn Monroe en la serie DiviNos — el mito y su fragilidad.",
    },
    {
        "slug": "divinos-johnny",
        "title": "DiviNos Johnny",
        "img": "divinos-johnny-gl9M1ZKj.webp",
        "series": "DiviNos",
        "desc": "Johnny Depp en la serie DiviNos — retrato entre lo sagrado y lo pop.",
    },
    {
        "slug": "asucar-celia-cruz",
        "title": "Asúcar (Celia Cruz)",
        "img": "celia-cruz-cantinflowers-DO-SRKMB.webp",
        "year": 2020,
        "technique": "Acrílico y collage (sobres de azúcar, envoltorios) sobre lienzo 3D",
        "series": "DiviNos",
        "desc": "Retrato vibrante de Celia Cruz en formato grande, integrando un collage de sobres de azúcar reales y colores saturados que homenajean el «Sugar Blues».",
    },
    {
        "slug": "tedas-queen",
        "title": "Tedás Queen",
        "img": "tedas-queen-GT9W8egT.webp",
        "series": "Tributos Musicales",
        "desc": "Tributo a Queen — energía escénica trasladada al lienzo.",
    },
    {
        "slug": "hammock-in-tin",
        "title": "Hammock in Tin",
        "img": "hammock-in-tin-XD5nAoyg.webp",
        "series": "En.lata.das",
        "desc": "Micromundo en lata: una hamaca, una siesta, un océano de metal.",
    },
    {
        "slug": "sardine-tin",
        "title": "Sardine Tin",
        "img": "sardine-tin-collage-Bo41LZ-o.webp",
        "series": "En.lata.das",
        "desc": "Collage en lata de sardinas — lo cotidiano elevado a arte objeto.",
    },
    {
        "slug": "en-caja",
        "title": "En Caja",
        "img": "en-caja-CDdrJMsP.webp",
        "desc": "Arte objeto — una historia guardada en caja, lista para descubrir.",
    },
    {
        "slug": "soy-un-amor",
        "title": "Soy un Amor y tengo Alas",
        "img": "soy-un-amor-y-tengo-alas-ItTo7aOd.webp",
        "desc": "Ternura con alas — pieza que celebra el amor que levanta el vuelo.",
    },
    {
        "slug": "the-golden-couple",
        "title": "The Golden Couple",
        "img": "the-golden-couple-C9C95N75.webp",
        "desc": "Retrato de pareja en dorados — dos vidas, un mismo brillo.",
    },
    {
        "slug": "pink-and-sparkles",
        "title": "Pink and Sparkles",
        "img": "pink-and-sparkles-c4K6RUzC.webp",
        "desc": "Rosa y destellos — color, brillo y actitud en una pieza luminosa.",
    },
    {
        "slug": "monster-dragon",
        "title": "Monster Dragon",
        "img": "monster-dragon-QQiqdImO.webp",
        "desc": "Criatura fantástica en clave pop — imaginación sin correa.",
    },
]

EMAIL = "naroa@naroa.eu"
IG = "https://instagram.com/naroagutierrezgil"


# ---------------------------------------------------------------- HELPERS
def e(s):
    return html.escape(str(s), quote=True)


def meta_line(w):
    parts = []
    if w.get("year"):
        parts.append(str(w["year"]))
    if w.get("technique"):
        parts.append(w["technique"])
    if not parts and w.get("series"):
        parts.append("Serie " + w["series"])
    return " · ".join(parts)


# ---------------------------------------------------------------- LAYOUT
def page(title, desc, canonical, body, og_image=None, extra_head="", body_class=""):
    og_image = og_image or f"{DOMAIN}/images/obra/marilyn-rocks.webp"
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="author" content="Naroa Gutiérrez Gil">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Naroa Gutiérrez Gil">
<meta property="og:locale" content="es_ES">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:creator" content="@naroagutierrezgil">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{og_image}">
<meta name="geo.region" content="ES-PV">
<meta name="geo.placename" content="Bilbao">
<link rel="icon" type="image/png" href="/assets/favicon-Inu7iesc.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;700;900&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/style.css">
{extra_head}
</head>
<body class="{body_class}">
<a class="skip" href="#content">Ir al contenido</a>
<div class="progress" aria-hidden="true"></div>
<header class="nav">
  <a class="nav__logo" href="/" aria-label="Inicio — Naroa Gutiérrez Gil">N</a>
  <nav aria-label="Principal">
    <a href="/obra/">Obra</a>
    <a href="/encargos/">Encargos</a>
    <a href="/sobre-mi/">Sobre mí</a>
    <a href="/juegos/" data-ext>Juegos</a>
    <a class="nav__cta" href="mailto:{EMAIL}?subject=Encargo%20art%C3%ADstico">Contacto</a>
  </nav>
</header>
<main id="content">
{body}
</main>
<footer class="footer">
  <div class="footer__inner">
    <p class="footer__name">Naroa Gutiérrez Gil</p>
    <p class="footer__tag">Hiperrealismo POP · Bilbao, País Vasco</p>
    <p class="footer__links">
      <a href="mailto:{EMAIL}">{EMAIL}</a> ·
      <a href="{IG}" rel="me noopener" target="_blank">@naroagutierrezgil</a>
    </p>
    <p class="footer__legal">© 2026 Naroa Gutiérrez Gil · Todas las obras son originales y están protegidas por derechos de autor.</p>
  </div>
</footer>
<script src="/static/site.js" defer></script>
</body>
</html>"""


# ---------------------------------------------------------------- SECTIONS
def gallery_grid(works, heading_level="h3"):
    cards = []
    for w in works:
        m = meta_line(w)
        meta_html = f'<p class="card__meta">{e(m)}</p>' if m else ""
        cards.append(f"""    <a class="card reveal" href="/obra/{w["slug"]}/">
      <figure><img src="/images/obra/thumbs/{w["slug"]}.webp" alt="{e(w["title"])} — obra de Naroa Gutiérrez Gil" loading="lazy" decoding="async" width="640" style="view-transition-name:vt-{w["slug"]}"></figure>
      <{heading_level} class="card__title">{e(w["title"])}</{heading_level}>{meta_html}
    </a>""")
    return "\n".join(cards)


def build_home():
    featured = WORKS[:1][0]
    body = f"""
<section class="hero">
  <img class="hero__img" src="/images/obra/{featured["slug"]}.webp" alt="{e(featured["title"])} — Naroa Gutiérrez Gil, acrílico sobre pizarra" fetchpriority="high">
  <div class="hero__scrim"></div>
  <div class="hero__content">
    <p class="hero__kicker">Artista visual · Bilbao</p>
    <h1>Naroa Gutiérrez Gil</h1>
    <p class="hero__sub">Hiperrealismo POP · Retratos por encargo · Acrílico, pizarra y mica mineral</p>
    <div class="hero__actions">
      <a class="btn" href="/obra/">Explorar la obra</a>
      <a class="btn btn--ghost" href="/encargos/">Encargar un retrato</a>
    </div>
  </div>
  <span class="hero__cue" aria-hidden="true"></span>
</section>

<div class="marquee" aria-hidden="true">
  <div class="marquee__track">
    <span>Hiperrealismo POP <b>·</b> Retratos por encargo <b>·</b> Pizarra &amp; mica mineral <b>·</b> Bilbao <b>·</b></span>
    <span>Hiperrealismo POP <b>·</b> Retratos por encargo <b>·</b> Pizarra &amp; mica mineral <b>·</b> Bilbao <b>·</b></span>
  </div>
</div>

<section class="section">
  <div class="section__head">
    <h2>La Obra</h2>
    <p>Cada trazo es una historia. Cada obra, un fragmento del alma.</p>
  </div>
  <div class="grid">
{gallery_grid(WORKS)}
  </div>
</section>

<section class="section section--band">
  <blockquote class="quote">
    <p>«Cada piedra que uso tiene millones de años. Cada retrato que pinto tiene la edad de quien lo mira.»</p>
    <cite>— Naroa Gutiérrez Gil</cite>
  </blockquote>
</section>

<section class="section section--split">
  <div>
    <h2>Retratos por encargo</h2>
    <p>No hay fórmulas. Me siento contigo, escucho tu historia, y entre los dos decidimos cómo contarla sobre el lienzo. Retratos de pareja, familiares y mascotas — con certificado de autenticidad y envío a toda España.</p>
    <a class="btn" href="/encargos">Cómo funciona →</a>
  </div>
  <div>
    <h2>¿Hablamos?</h2>
    <p>Si tienes una idea, un rostro que quieres inmortalizar, o simplemente curiosidad — escríbeme. Los mejores encargos empiezan con un «oye, tengo una idea».</p>
    <a class="btn btn--ghost" href="mailto:{EMAIL}?subject=Encargo%20art%C3%ADstico">Escríbeme</a>
  </div>
</section>
"""
    schema = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": "Naroa Gutiérrez Gil",
        "jobTitle": "Artista visual",
        "url": DOMAIN,
        "email": f"mailto:{EMAIL}",
        "sameAs": [IG, "https://naroa.online"],
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Bilbao",
            "addressRegion": "País Vasco",
            "addressCountry": "ES",
        },
        "knowsAbout": [
            "Hiperrealismo POP",
            "Retrato por encargo",
            "Pintura sobre pizarra",
            "Mica mineral",
        ],
    }
    head = f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>'
    return page(
        "Naroa Gutiérrez Gil | Retratos Hiperrealismo POP · Bilbao",
        "Naroa Gutiérrez Gil — Artista visual en Bilbao. Retratos por encargo en hiperrealismo POP sobre pizarra y mica mineral. Retratos de pareja, familiares y mascotas. Envío a toda España.",
        f"{DOMAIN}/",
        body,
        extra_head=head,
    )


def build_obra_index():
    body = f"""
<section class="section section--first">
  <div class="section__head">
    <h1>La Obra</h1>
    <p>{len(WORKS)} obras originales — hiperrealismo POP, técnica mixta, pizarra y mica mineral.</p>
  </div>
  <div class="grid">
{gallery_grid(WORKS, heading_level="h2")}
  </div>
</section>
"""
    return page(
        "Obra | Naroa Gutiérrez Gil — Galería de retratos hiperrealistas",
        f"Galería completa de Naroa Gutiérrez Gil: {len(WORKS)} obras originales en hiperrealismo POP. Retratos de iconos — Marilyn, Amy, Johnny — y piezas de técnica mixta.",
        f"{DOMAIN}/obra",
        body,
    )


def build_work_page(w, prev_w, next_w):
    m = meta_line(w)
    meta_html = f'<p class="work__meta">{e(m)}</p>' if m else ""
    series_html = f'<p class="work__series">Serie: {e(w["series"])}</p>' if w.get("series") else ""
    body = f"""
<article class="work">
  <figure class="work__figure">
    <img src="/images/obra/{w["slug"]}.webp" alt="{e(w["title"])} — obra original de Naroa Gutiérrez Gil" fetchpriority="high">
  </figure>
  <div class="work__info">
    <p class="hero__kicker">Obra original</p>
    <h1>{e(w["title"])}</h1>
    {meta_html}
    {series_html}
    <p class="work__desc">{e(w["desc"])}</p>
    <div class="hero__actions">
      <a class="btn" href="mailto:{EMAIL}?subject={e(w["title"])}%20%E2%80%94%20consulta">Preguntar por esta obra</a>
      <a class="btn btn--ghost" href="/encargos">Encargar algo así</a>
    </div>
    <nav class="work__nav" aria-label="Más obras">
      <a href="/obra/{prev_w["slug"]}">← {e(prev_w["title"])}</a>
      <a href="/obra">Toda la obra</a>
      <a href="/obra/{next_w["slug"]}">{e(next_w["title"])} →</a>
    </nav>
  </div>
</article>
"""
    schema = {
        "@context": "https://schema.org",
        "@type": "VisualArtwork",
        "name": w["title"],
        "creator": {"@type": "Person", "name": "Naroa Gutiérrez Gil", "url": DOMAIN},
        "image": f"{DOMAIN}/images/obra/{w['slug']}.webp",
        "description": w["desc"],
        "artMedium": w.get("technique", "Técnica mixta"),
        "artform": "Pintura",
        "url": f"{DOMAIN}/obra/{w['slug']}",
    }
    if w.get("year"):
        schema["dateCreated"] = str(w["year"])
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Inicio", "item": DOMAIN},
            {"@type": "ListItem", "position": 2, "name": "Obra", "item": f"{DOMAIN}/obra"},
            {"@type": "ListItem", "position": 3, "name": w["title"]},
        ],
    }
    head = (
        f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>'
        f'<script type="application/ld+json">{json.dumps(crumbs, ensure_ascii=False)}</script>'
    )
    title_meta = f"{w['title']} | Naroa Gutiérrez Gil"
    return page(
        title_meta,
        f"{w['desc']} Obra original de Naroa Gutiérrez Gil, artista en Bilbao.",
        f"{DOMAIN}/obra/{w['slug']}",
        body,
        og_image=f"{DOMAIN}/images/obra/{w['slug']}.webp",
        extra_head=head,
    )


def build_encargos():
    steps = [
        (
            "01",
            "Primer contacto",
            "Me escribes un email o un DM. Cuéntame a quién quieres retratar y qué significado tiene para ti. No necesitas tenerlo todo claro — para eso estoy yo.",
        ),
        (
            "02",
            "Boceto y propuesta",
            "Unos días después te envío un boceto y una propuesta visual. Hablamos de técnica — hiperrealismo, pop, mica mineral — y de formato. Tú decides la dirección.",
        ),
        (
            "03",
            "La obra cobra vida",
            "Pinto durante semanas y te envío fotos del proceso para que veas cómo la obra va cobrando vida. Si algo no encaja, ajustamos. Es tu retrato.",
        ),
        (
            "04",
            "Entrega",
            "Tu retrato, terminado. Con certificado de autenticidad y envío seguro a toda España. Listo para colgar y para que la gente pregunte quién lo pintó.",
        ),
    ]
    steps_html = "\n".join(
        f"""  <div class="step reveal">
    <span class="step__num">{n}</span>
    <h2>{e(t)}</h2>
    <p>{e(d)}</p>
  </div>"""
        for n, t, d in steps
    )
    body = f"""
<section class="section section--first">
  <div class="section__head">
    <h1>Cada retrato empieza con una conversación</h1>
    <p>No hay fórmulas. Me siento contigo, escucho tu historia, y entre los dos decidimos cómo contarla sobre el lienzo.</p>
  </div>
  <div class="steps">
{steps_html}
  </div>
</section>
<section class="section section--band">
  <div class="section__head">
    <h2>¿Hablamos?</h2>
    <p>Retratos de pareja, familiares, mascotas, iconos — cuéntame tu idea.</p>
    <p class="cta-row"><a class="btn" href="mailto:{EMAIL}?subject=Encargo%20art%C3%ADstico">Escríbeme →</a></p>
    <p class="footer__links"><a href="mailto:{EMAIL}">{EMAIL}</a> · <a href="{IG}" target="_blank" rel="noopener">@naroagutierrezgil</a> · Estudio en Bilbao</p>
  </div>
</section>
"""
    return page(
        "Encargos | Retratos personalizados — Naroa Gutiérrez Gil",
        "Encarga un retrato personalizado a Naroa Gutiérrez Gil: proceso artesanal en 4 pasos, boceto previo, fotos del proceso, certificado de autenticidad y envío a toda España.",
        f"{DOMAIN}/encargos",
        body,
    )


def build_sobre_mi():
    body = """
<section class="section section--first section--split">
  <figure class="about__portrait reveal">
    <img src="/images/naroa-portrait.jpg" alt="Naroa Gutiérrez Gil, artista visual, en su estudio de Bilbao">
  </figure>
  <div>
    <p class="hero__kicker">Artista visual · Bilbao, País Vasco</p>
    <h1>Naroa Gutiérrez Gil</h1>
    <p>Pinto retratos en <strong>hiperrealismo POP</strong>: rostros que parecen respirar, sobre soportes que llevan millones de años esperando — pizarra natural y mica mineral.</p>
    <p>Mi trabajo reimagina iconos — Amy, Marilyn, Johnny — y retrata a personas reales: parejas, familias, mascotas. Técnica mixta, acrílico y óleo, collage y objeto encontrado. Series como <em>Rocks</em>, <em>DiviNos</em> o <em>En.lata.das</em> exploran lo divino y lo cotidiano.</p>
    <blockquote class="quote quote--inline"><p>«Cada piedra que uso tiene millones de años. Cada retrato que pinto tiene la edad de quien lo mira.»</p></blockquote>
    <div class="hero__actions">
      <a class="btn" href="/obra">Ver la obra</a>
      <a class="btn btn--ghost" href="/encargos">Encargar un retrato</a>
    </div>
  </div>
</section>
"""
    return page(
        "Sobre mí | Naroa Gutiérrez Gil — Artista en Bilbao",
        "Naroa Gutiérrez Gil, artista visual en Bilbao. Hiperrealismo POP sobre pizarra y mica mineral. Series Rocks, DiviNos y En.lata.das. Retratos por encargo.",
        f"{DOMAIN}/sobre-mi",
        body,
        og_image=f"{DOMAIN}/images/naroa-portrait.jpg",
    )


def build_landing_bilbao():
    faqs = [
        (
            "¿Cómo encargo un retrato personalizado en Bilbao?",
            f"Escribe a {EMAIL} o un DM a @naroagutierrezgil contando a quién quieres retratar. Recibirás un boceto y una propuesta visual antes de empezar.",
        ),
        (
            "¿Qué tipos de retrato haces por encargo?",
            "Retratos de pareja, familiares, de mascotas e iconos personales — a partir de una foto, en hiperrealismo POP sobre pizarra, mica mineral o lienzo.",
        ),
        (
            "¿Hacéis envíos fuera de Bilbao?",
            "Sí. Cada obra viaja con embalaje seguro y certificado de autenticidad, con envío a toda España.",
        ),
        (
            "¿Puedo ver el proceso de mi cuadro?",
            "Sí. Durante las semanas de trabajo recibirás fotos del proceso y podrás pedir ajustes. Es tu retrato.",
        ),
    ]
    faq_html = "\n".join(
        f"""  <details class="faq reveal"><summary>{e(q)}</summary><p>{e(a)}</p></details>"""
        for q, a in faqs
    )
    featured = [
        w
        for w in WORKS
        if w["slug"]
        in ("marilyn-rocks", "amy", "retrato-i", "the-golden-couple", "audrey-hepburn", "johnny")
    ]
    body = f"""
<section class="section section--first">
  <div class="section__head">
    <h1>Retratos hiperrealistas por encargo en Bilbao</h1>
    <p>Cuadros pintados a mano a partir de tu foto — hiperrealismo POP sobre pizarra y mica mineral, por la artista Naroa Gutiérrez Gil. Retratos de pareja, familiares y mascotas, con certificado de autenticidad y envío a toda España.</p>
    <div class="hero__actions">
      <a class="btn" href="mailto:{EMAIL}?subject=Encargo%20de%20retrato">Pedir presupuesto</a>
      <a class="btn btn--ghost" href="/encargos">Ver el proceso</a>
    </div>
  </div>
  <div class="grid">
{gallery_grid(featured, heading_level="h2")}
  </div>
</section>
<section class="section">
  <div class="section__head"><h2>Preguntas frecuentes</h2></div>
{faq_html}
</section>
"""
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in faqs
        ],
    }
    head = (
        f'<script type="application/ld+json">{json.dumps(faq_schema, ensure_ascii=False)}</script>'
    )
    return page(
        "Retratos Hiperrealistas por Encargo en Bilbao | Naroa Gutiérrez Gil",
        "Retratos por encargo en Bilbao: cuadros hiperrealistas pintados a mano a partir de foto. Retratos de pareja, familiares y mascotas. Certificado de autenticidad y envío a toda España.",
        f"{DOMAIN}/retratos-hiperrealistas-bilbao",
        body,
        extra_head=head,
    )


def build_404():
    body = """
<section class="section section--first section--band" style="min-height:60vh;display:flex;align-items:center">
  <div class="section__head">
    <h1>404 — Esta obra no existe (todavía)</h1>
    <p>Puede que el enlace haya cambiado. La obra completa está a un clic.</p>
    <p class="cta-row"><a class="btn" href="/obra">Ver la obra</a> <a class="btn btn--ghost" href="/">Inicio</a></p>
  </div>
</section>
"""
    return page(
        "Página no encontrada | Naroa Gutiérrez Gil",
        "Página no encontrada. Descubre la obra de Naroa Gutiérrez Gil.",
        f"{DOMAIN}/404",
        body,
    )


# ---------------------------------------------------------------- STATIC
CSS = """:root{--void:#050505;--surface:#0a0a0a;--card:#111111;--text:#f2efe9;--muted:#8b867c;--accent:#ff003c;--gold:#d4af37;--radius:16px;--max:1200px}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{background:var(--void);color:var(--text);font-family:Inter,system-ui,sans-serif;font-weight:300;line-height:1.65;-webkit-font-smoothing:antialiased;overflow-x:hidden}
h1,h2,h3{font-family:Outfit,sans-serif;font-weight:700;line-height:1.12;letter-spacing:-.02em}
h1{font-size:clamp(2.5rem,6vw,4.8rem)}
h2{font-size:clamp(1.8rem,4vw,3rem)}
a{color:inherit;text-decoration:none}
img{display:block;max-width:100%;height:auto}
.noise{position:fixed;inset:0;z-index:9999;pointer-events:none;background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");opacity:0.04}
.skip{position:absolute;left:-999px;top:0;background:var(--accent);color:#fff;padding:.6rem 1rem;z-index:9999}
.skip:focus{left:0}
.nav{position:fixed;inset:0 0 auto;z-index:100;display:flex;justify-content:space-between;align-items:center;padding:1.2rem clamp(1.2rem,5vw,3rem);background:linear-gradient(180deg,rgba(5,5,5,.9),rgba(5,5,5,0));backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid rgba(255,255,255,0)}
.nav.is-solid{background:rgba(5,5,5,.95);border-bottom:1px solid rgba(255,255,255,.05);padding-block:1rem}
.nav__logo{font-family:Outfit,sans-serif;font-weight:900;font-size:1.6rem;color:var(--accent);letter-spacing:-.05em}
.nav nav{display:flex;gap:clamp(1rem,3vw,2.2rem);align-items:center;font-size:.95rem;font-weight:500}
.nav nav a{opacity:.7;transition:all .3s ease}
.nav nav a:hover{opacity:1;color:var(--text);transform:translateY(-1px)}
.nav__cta{border:1px solid rgba(255,255,255,.2);border-radius:999px;padding:.4rem 1.2rem;transition:all .3s cubic-bezier(.2,.8,.2,1)!important;opacity:1!important}
.nav__cta:hover{border-color:var(--accent);background:var(--accent);color:#fff!important;transform:translateY(-2px)!important;box-shadow:0 10px 20px rgba(255,0,60,.3)}
.hero{position:relative;min-height:95svh;display:flex;align-items:flex-end;overflow:hidden}
.hero__img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;animation:kenburns 28s ease-in-out infinite alternate}
@keyframes kenburns{from{transform:scale(1)}to{transform:scale(1.1)}}
.hero__scrim{position:absolute;inset:0;background:linear-gradient(180deg,rgba(5,5,5,.4) 0%,rgba(5,5,5,.2) 40%,rgba(5,5,5,1) 100%)}
.hero__content{position:relative;padding:0 clamp(1.2rem,5vw,4rem) clamp(4rem,10vh,7rem);max-width:1000px;z-index:2}
.hero__kicker{font-family:Outfit,sans-serif;font-weight:600;font-size:.85rem;letter-spacing:.35em;text-transform:uppercase;color:var(--gold);margin-bottom:1rem;display:inline-block;border-bottom:1px solid rgba(212,175,55,.3);padding-bottom:.3rem}
.hero__sub{color:var(--muted);font-size:clamp(1.1rem,2.2vw,1.35rem);margin:1rem 0 2rem;max-width:750px;font-weight:300}
.hero__actions{display:flex;gap:1rem;flex-wrap:wrap;margin-top:2rem}
.btn{display:inline-flex;align-items:center;justify-content:center;background:var(--accent);color:#fff;font-family:Outfit,sans-serif;font-weight:600;font-size:1.05rem;padding:.85rem 2rem;border-radius:999px;transition:all .3s cubic-bezier(.2,.8,.2,1)}
.btn:hover{transform:translateY(-3px);box-shadow:0 12px 35px rgba(255,0,60,.4)}
.btn--ghost{background:transparent;border:1px solid rgba(255,255,255,.2);color:var(--text)}
.btn--ghost:hover{box-shadow:none;border-color:var(--text);background:rgba(255,255,255,.05)}
.section{max-width:var(--max);margin:0 auto;padding:clamp(4.5rem,12vh,8rem) clamp(1.2rem,5vw,3rem)}
.section--first{padding-top:clamp(8rem,18vh,11rem)}
.section__head{max-width:800px;margin-bottom:3.5rem}
.section__head p{color:var(--muted);margin-top:1.2rem;font-size:1.15rem}
.section--band{max-width:none;background:var(--surface);border-block:1px solid rgba(255,255,255,.03)}
.section--band>*{max-width:var(--max);margin-left:auto;margin-right:auto}
.section--split{display:grid;gap:4rem;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));align-items:center}
.section--split p{color:var(--muted);margin:1.2rem 0 1.8rem}
.grid{display:grid;gap:clamp(1.5rem,3vw,2.5rem);grid-template-columns:repeat(auto-fill,minmax(min(300px,100%),1fr))}
.card{background:var(--card);border-radius:var(--radius);overflow:hidden;transition:all .4s cubic-bezier(.2,.8,.2,1);border:1px solid rgba(255,255,255,.04)}
.card:hover{transform:translateY(-8px);box-shadow:0 24px 60px rgba(0,0,0,.6);border-color:rgba(255,255,255,.1)}
.card figure{aspect-ratio:4/5;overflow:hidden;background:#0a0a0a;display:flex;align-items:center;justify-content:center;position:relative}
.card figure::after{content:'';position:absolute;inset:0;background:linear-gradient(0deg,rgba(0,0,0,.4) 0%,transparent 50%);opacity:0;transition:opacity .4s}
.card:hover figure::after{opacity:1}
.card img{width:100%;height:100%;object-fit:cover;transition:transform .7s cubic-bezier(.2,.8,.2,1);cursor:zoom-in}
.card:hover img{transform:scale(1.08)}
.card__title{font-size:1.15rem;font-weight:600;padding:1.2rem 1.2rem .3rem}
.card__meta{color:var(--muted);font-size:.85rem;padding:0 1.2rem 1.2rem;font-weight:500}
.quote{padding:clamp(4rem,10vh,7rem) clamp(1.2rem,5vw,3rem);text-align:center;position:relative}
.quote::before{content:'"';position:absolute;top:1rem;left:50%;transform:translateX(-50%);font-family:Outfit;font-size:12rem;color:rgba(255,255,255,.03);line-height:1;z-index:-1}
.quote p{font-family:Outfit,sans-serif;font-weight:300;font-size:clamp(1.5rem,4vw,2.4rem);font-style:italic;max-width:900px;margin:0 auto;color:var(--text)}
.quote cite{display:block;margin-top:1.8rem;color:var(--gold);font-style:normal;font-size:1rem;letter-spacing:.2em;text-transform:uppercase;font-weight:600}
.quote--inline{padding:1.5rem 0;text-align:left}
.quote--inline::before{display:none}
.quote--inline p{font-size:1.25rem;max-width:none}
.work{max-width:var(--max);margin:0 auto;padding:clamp(7rem,16vh,9rem) clamp(1.2rem,5vw,3rem) clamp(4rem,10vh,7rem);display:grid;gap:clamp(2.5rem,6vw,5rem);grid-template-columns:1fr;align-items:start}
@media (min-width:860px){.work{grid-template-columns:1.2fr 1fr}}
.work__figure{background:var(--card);border-radius:var(--radius);overflow:hidden;border:1px solid rgba(255,255,255,.05);box-shadow:0 20px 50px rgba(0,0,0,.4)}
.work__figure img{width:100%;cursor:zoom-in}
.work__content{position:sticky;top:8rem}
.work__meta{color:var(--gold);font-family:Outfit,sans-serif;font-weight:600;letter-spacing:.08em;margin-top:1.2rem;text-transform:uppercase;font-size:.9rem}
.work__series{color:var(--muted);font-size:1rem;margin-top:.4rem;font-weight:500}
.work__desc{color:var(--muted);font-size:1.15rem;margin-top:1.5rem}
.work__nav{display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;margin-top:3rem;padding-top:1.8rem;border-top:1px solid rgba(255,255,255,.08);font-size:.95rem;font-weight:500;color:var(--muted)}
.work__nav a{transition:all .2s;display:inline-flex;align-items:center;gap:.5rem}
.work__nav a:hover{color:var(--gold);transform:translateY(-1px)}
.steps{display:grid;gap:2rem;grid-template-columns:repeat(auto-fit,minmax(min(280px,100%),1fr))}
.step{background:var(--card);border-radius:var(--radius);padding:2.2rem;border:1px solid rgba(255,255,255,.03);transition:transform .3s,box-shadow .3s}
.step:hover{transform:translateY(-5px);box-shadow:0 15px 40px rgba(0,0,0,.3);border-color:rgba(255,255,255,.08)}
.step__num{font-family:Outfit,sans-serif;font-weight:900;font-size:3rem;color:transparent;-webkit-text-stroke:1px var(--accent);display:block;margin-bottom:1rem;line-height:1}
.step h2{font-size:1.3rem;margin-bottom:.8rem}
.step p{color:var(--muted);font-size:1.05rem}
.about__portrait{border-radius:var(--radius);overflow:hidden;filter:saturate(.85) contrast(1.1);border:1px solid rgba(255,255,255,.05);box-shadow:0 20px 50px rgba(0,0,0,.5)}
.faq{background:var(--card);border-radius:var(--radius);margin-bottom:1rem;padding:1.4rem 1.8rem;border:1px solid rgba(255,255,255,.03);transition:all .3s}
.faq:hover{border-color:rgba(255,255,255,.1)}
.faq[open]{background:rgba(255,255,255,.03)}
.faq summary{cursor:pointer;font-family:Outfit,sans-serif;font-weight:600;font-size:1.15rem;list-style:none;position:relative;padding-right:2rem}
.faq summary::after{content:'+';position:absolute;right:0;top:50%;transform:translateY(-50%);color:var(--accent);font-size:1.5rem;transition:transform .3s}
.faq[open] summary::after{transform:translateY(-50%) rotate(45deg)}
.faq summary::-webkit-details-marker{display:none}
.faq p{color:var(--muted);padding-top:1rem;font-size:1.05rem;line-height:1.7}
.cta-row{margin:2rem 0;display:flex;gap:1rem;flex-wrap:wrap}
.footer{border-top:1px solid rgba(255,255,255,.06);margin-top:4rem;background:var(--surface)}
.footer__inner{max-width:var(--max);margin:0 auto;padding:4rem clamp(1.2rem,5vw,3rem);text-align:center}
.footer__name{font-family:Outfit,sans-serif;font-weight:900;font-size:1.5rem;letter-spacing:-.02em}
.footer__tag{color:var(--muted);font-size:1rem;margin:.5rem 0 1.5rem;font-weight:500}
.footer__links{display:flex;gap:1.5rem;justify-content:center;margin-bottom:2rem}
.footer__links a{color:var(--text);font-weight:500;transition:color .2s;display:inline-block}
.footer__links a:hover{color:var(--accent)}
.footer__legal{color:#555;font-size:.85rem}
.reveal{opacity:0;transform:translateY(30px) scale(.98);transition:opacity .8s ease,transform .8s cubic-bezier(.2,.8,.2,1)}
.reveal.is-in{opacity:1;transform:none}
.progress{position:fixed;top:0;left:0;height:3px;width:100%;background:linear-gradient(90deg,var(--accent),#ff8a9f);transform-origin:0 50%;transform:scaleX(0);z-index:1000;pointer-events:none}
.nav{transition:transform .4s cubic-bezier(.2,.8,.2,1),background .3s ease,padding .3s ease}
.nav.is-hidden{transform:translateY(-100%)}
.hero__content>*{opacity:0;transform:translateY(40px);animation:rise .9s cubic-bezier(.2,.8,.2,1) forwards}
.hero__content>:nth-child(1){animation-delay:.15s}
.hero__content>:nth-child(2){animation-delay:.3s}
.hero__content>:nth-child(3){animation-delay:.45s}
.hero__content>:nth-child(4){animation-delay:.6s}
@keyframes rise{to{opacity:1;transform:none}}
.hero__cue{position:absolute;bottom:2.5rem;left:50%;width:2px;height:70px;overflow:hidden;opacity:.6}
.hero__cue::after{content:"";display:block;width:100%;height:100%;background:linear-gradient(180deg,transparent,var(--gold));animation:cue 2s cubic-bezier(.65,0,.35,1) infinite}
@keyframes cue{from{transform:translateY(-100%)}to{transform:translateY(100%)}}
.marquee{overflow:hidden;border-block:1px solid rgba(255,255,255,.05);padding:1.5rem 0;background:rgba(255,255,255,.01)}
.marquee__track{display:flex;width:max-content;animation:marquee 35s linear infinite}
.marquee span{font-family:Outfit,sans-serif;font-weight:900;font-size:clamp(1.2rem,3vw,2rem);letter-spacing:.15em;text-transform:uppercase;white-space:nowrap;padding-right:4rem;color:transparent;-webkit-text-stroke:1px rgba(255,255,255,.2)}
.marquee b{color:var(--accent);-webkit-text-stroke:0}
@keyframes marquee{to{transform:translateX(-50%)}}
.card{will-change:transform}
.card.is-tilt{transition:transform .1s ease-out,box-shadow .35s,border-color .35s}
.btn{will-change:transform}
.lightbox{position:fixed;inset:0;background:rgba(0,0,0,.95);z-index:99999;display:flex;align-items:center;justify-content:center;opacity:0;pointer-events:none;transition:opacity .4s cubic-bezier(.2,.8,.2,1);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px)}
.lightbox.is-active{opacity:1;pointer-events:auto}
.lightbox__content{position:relative;max-width:90vw;max-height:90vh;display:flex;flex-direction:column;align-items:center;gap:1rem}
.lightbox__content img{max-width:100%;max-height:85vh;object-fit:contain;border-radius:8px;box-shadow:0 20px 60px rgba(0,0,0,.8);transform:scale(.95);transition:transform .4s cubic-bezier(.2,.8,.2,1)}
.lightbox.is-active .lightbox__content img{transform:scale(1)}
.lightbox__close{position:absolute;top:1.5rem;right:2rem;background:transparent;border:none;color:#fff;font-size:3rem;font-weight:300;cursor:pointer;transition:color .2s;line-height:1}
.lightbox__close:hover{color:var(--accent)}
#lb-cap{color:var(--gold);font-family:Outfit,sans-serif;font-size:1.1rem;letter-spacing:.05em;text-transform:uppercase}
@view-transition{navigation:auto}
::view-transition-group(*){animation-duration:.5s;animation-timing-function:cubic-bezier(.2,.8,.2,1)}
::view-transition-old(root),::view-transition-new(root){animation-duration:.35s}
@media (prefers-reduced-motion:reduce){
  .hero__img{animation:none}
  .reveal{opacity:1;transform:none;transition:none}
  .hero__content>*{animation:none;opacity:1;transform:none}
  .marquee__track{animation:none}
  .hero__cue{display:none}
  .progress{display:none}
  .lightbox,.lightbox__content img{transition:none}
  @view-transition{navigation:none}
}
@media (max-width:768px){.nav{padding:1rem 1.2rem}.nav nav{gap:1rem}.nav nav a{font-size:.85rem}.nav__cta{padding:.3rem .9rem}.nav__logo{font-size:1.4rem}.work__content{position:static}.section{padding:clamp(3.5rem,10vh,6rem) clamp(1rem,4vw,2rem)}.work{padding:clamp(5rem,12vh,7rem) clamp(1rem,4vw,2rem) clamp(3rem,8vh,5rem)}}
"""

JS = """(function(){
  var reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* --- reveals en cascada --- */
  var io=new IntersectionObserver(function(es){
    es.forEach(function(en){
      if(!en.isIntersecting)return;
      var el=en.target;io.unobserve(el);
      var sibs=[].slice.call(el.parentNode.children).filter(function(c){return c.classList&&c.classList.contains('reveal')});
      var d=reduced?0:Math.min(sibs.indexOf(el),12)*60;
      setTimeout(function(){
        el.classList.add('is-in');
        var fin=function(){el.classList.remove('reveal','is-in');el.removeEventListener('transitionend',fin);};
        el.addEventListener('transitionend',fin);
        setTimeout(fin,1200);
      },d);
    });
  },{rootMargin:'0px 0px -5% 0px',threshold:.05});
  document.querySelectorAll('.reveal').forEach(function(el){io.observe(el)});

  if(!reduced){
    /* --- scroll --- */
    var bar=document.querySelector('.progress'),
        nav=document.querySelector('.nav'),
        hero=document.querySelector('.hero__img'),
        lastY=0,tick=false;
    function frame(){
      var y=scrollY,max=document.documentElement.scrollHeight-innerHeight;
      if(bar)bar.style.transform='scaleX('+(max>0?y/max:0)+')';
      if(nav){
        nav.classList.toggle('is-solid',y>50);
        nav.classList.toggle('is-hidden',y>400&&y>lastY);
      }
      if(hero&&y<innerHeight)hero.style.translate='0 '+(y*.25).toFixed(1)+'px';
      lastY=y;tick=false;
    }
    addEventListener('scroll',function(){if(!tick){tick=true;requestAnimationFrame(frame)}},{passive:true});
    frame();

    /* --- tilt 3D --- */
    if(matchMedia('(hover:hover) and (pointer:fine)').matches){
      document.querySelectorAll('.card').forEach(function(c){
        var r=null;
        c.addEventListener('pointerenter',function(){r=c.getBoundingClientRect();c.classList.add('is-tilt')});
        c.addEventListener('pointermove',function(ev){
          if(!r)return;
          var x=(ev.clientX-r.left)/r.width-.5,y=(ev.clientY-r.top)/r.height-.5;
          c.style.transform='perspective(1000px) translateY(-8px) rotateX('+(-y*8).toFixed(2)+'deg) rotateY('+(x*10).toFixed(2)+'deg)';
        });
        c.addEventListener('pointerleave',function(){r=null;c.classList.remove('is-tilt');c.style.transform='';});
      });
      document.querySelectorAll('.btn').forEach(function(b){
        b.addEventListener('pointermove',function(ev){
          var r=b.getBoundingClientRect(),x=(ev.clientX-r.left)/r.width-.5,y=(ev.clientY-r.top)/r.height-.5;
          b.style.transform='translate('+(x*8).toFixed(1)+'px,'+(y*5).toFixed(1)+'px)';
        });
        b.addEventListener('pointerleave',function(){b.style.transform='';});
      });
    }
  }

  /* --- Lightbox --- */
  var lb=document.getElementById('lightbox');
  if(lb){
    var lbImg=document.getElementById('lb-img'), lbCap=document.getElementById('lb-cap'), lbClose=document.querySelector('.lightbox__close');
    var openLb=function(src,cap){lbImg.src=src;lbCap.textContent=cap;lb.classList.add('is-active');};
    var closeLb=function(){lb.classList.remove('is-active');};
    lb.addEventListener('click',function(e){if(e.target===lb||e.target===lbClose)closeLb()});
    document.addEventListener('keydown',function(e){if(e.key==='Escape')closeLb()});
    
    document.querySelectorAll('.card img, .work__figure img').forEach(function(img){
      img.addEventListener('click',function(e){
        e.preventDefault();
        var card=img.closest('.card');
        var cap=card ? card.querySelector('.card__title').textContent : (document.querySelector('h1') ? document.querySelector('h1').textContent : '');
        openLb(img.src, cap);
      });
    });
  }
})();
"""


# ---------------------------------------------------------------- SEO FILES
def build_sitemap():
    urls = []

    def u(loc, prio, img=None, img_title=None):
        img_xml = ""
        if img:
            img_xml = f"""
    <image:image><image:loc>{img}</image:loc><image:title>{e(img_title or "")}</image:title></image:image>"""
        urls.append(f"""  <url>
    <loc>{loc}</loc>
    <lastmod>{TODAY}</lastmod>
    <priority>{prio}</priority>{img_xml}
  </url>""")

    u(
        f"{DOMAIN}/",
        "1.0",
        f"{DOMAIN}/images/obra/marilyn-rocks.webp",
        "Marilyn Rocks — Naroa Gutiérrez Gil",
    )
    u(f"{DOMAIN}/obra", "0.9")
    for w in WORKS:
        u(
            f"{DOMAIN}/obra/{w['slug']}",
            "0.8",
            f"{DOMAIN}/images/obra/{w['slug']}.webp",
            f"{w['title']} — Naroa Gutiérrez Gil",
        )
    u(f"{DOMAIN}/encargos", "0.9")
    u(f"{DOMAIN}/retratos-hiperrealistas-bilbao", "0.9")
    u(f"{DOMAIN}/sobre-mi", "0.7")
    u(f"{DOMAIN}/juegos/", "0.4")
    return (
        """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
"""
        + "\n".join(urls)
        + "\n</urlset>\n"
    )


ROBOTS = f"""User-agent: *
Allow: /

Sitemap: {DOMAIN}/sitemap.xml
"""

CF_REDIRECTS = f"""
https://naroa.online/* {DOMAIN}/:splat 301
https://www.naroa.online/* {DOMAIN}/:splat 301
https://www.naroagutierrezgil.com/* {DOMAIN}/:splat 301
"""

CF_HEADERS = """
/assets/*
  Cache-Control: public, max-age=31536000, immutable
/images/*
  Cache-Control: public, max-age=604800
/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
"""


# ---------------------------------------------------------------- MAIN
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", default=os.path.join(HERE, "mirror"))
    args = ap.parse_args()
    mirror = args.mirror
    out = os.path.join(HERE, "web")

    if not os.path.isdir(os.path.join(mirror, "assets")):
        sys.exit(f"ERROR: no encuentro el espejo en {mirror} (falta assets/)")

    # limpieza tolerante (en FS montados rmtree puede fallar)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out, exist_ok=True)

    # 1) static shared
    os.makedirs(os.path.join(out, "static"), exist_ok=True)
    open(os.path.join(out, "static", "style.css"), "w").write(CSS)
    open(os.path.join(out, "static", "site.js"), "w").write(JS)

    # 2) assets del build original (bundle SPA + imágenes hasheadas + favicon)
    shutil.copytree(
        os.path.join(mirror, "assets"),
        os.path.join(out, "assets"),
        ignore=shutil.ignore_patterns("main.js", "main.css"),
        dirs_exist_ok=True,
    )
    # data para la SPA (galería/juegos hacen fetch de /data/*.json)
    if os.path.isdir(os.path.join(mirror, "data")):
        shutil.copytree(os.path.join(mirror, "data"), os.path.join(out, "data"), dirs_exist_ok=True)

    # 3) imágenes con nombre limpio para SEO/og
    imgdir = os.path.join(out, "images", "obra")
    os.makedirs(imgdir, exist_ok=True)
    for w in WORKS:
        src = os.path.join(mirror, "assets", w["img"])
        if not os.path.isfile(src):
            sys.exit(f"ERROR: falta imagen {w['img']}")
        shutil.copy2(src, os.path.join(imgdir, w["slug"] + ".webp"))
    # miniaturas para la galería (640px)
    thdir = os.path.join(imgdir, "thumbs")
    os.makedirs(thdir, exist_ok=True)
    try:
        from PIL import Image

        for w in WORKS:
            src = os.path.join(imgdir, w["slug"] + ".webp")
            im = Image.open(src)
            wd, ht = im.size
            if wd > 1200:
                im = im.resize((1200, int(ht * 1200 / wd)), Image.LANCZOS)
            im.save(os.path.join(thdir, w["slug"] + ".webp"), "WEBP", quality=95, method=6)
    except ImportError:
        for w in WORKS:  # fallback sin PIL: copia a tamaño completo
            shutil.copy2(
                os.path.join(imgdir, w["slug"] + ".webp"), os.path.join(thdir, w["slug"] + ".webp")
            )

    # imágenes que la SPA (database.json) espera en /images/artworks/ —
    # solo correspondencias exactas de nombre con los assets reales
    exact_db = {
        "celia-cruz-cantinflowers.webp": "celia-cruz-cantinflowers-DO-SRKMB.webp",
        "amor-en-conserva.webp": "amor-en-conserva-CMHRIKXx.webp",
        "dar-la-lata.webp": "dar-la-lata-DxWlKgS-.webp",
        "baroque-farrokh.webp": "baroque-farrokh-mjg4ClA9.webp",
        "tedas-queen.webp": "tedas-queen-GT9W8egT.webp",
        "marilyn-rocks.webp": "marilyn-rocks--qPeLHxE.webp",
    }
    awdir = os.path.join(out, "images", "artworks")
    os.makedirs(awdir, exist_ok=True)
    for clean, hashed in exact_db.items():
        src = os.path.join(mirror, "assets", hashed)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(awdir, clean))

    # retrato
    for cand in os.listdir(os.path.join(mirror, "assets")):
        if cand.startswith("naroa-portrait"):
            shutil.copy2(
                os.path.join(mirror, "assets", cand),
                os.path.join(out, "images", "naroa-portrait.jpg"),
            )

    # 4) páginas
    def write(path, content):
        p = os.path.join(out, path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(content)

    write("index.html", build_home())
    write("obra/index.html", build_obra_index())
    for i, w in enumerate(WORKS):
        write(
            f"obra/{w['slug']}/index.html",
            build_work_page(w, WORKS[i - 1], WORKS[(i + 1) % len(WORKS)]),
        )
    write("encargos/index.html", build_encargos())
    write("sobre-mi/index.html", build_sobre_mi())
    write("retratos-hiperrealistas-bilbao/index.html", build_landing_bilbao())
    write("404.html", build_404())

    # 5) juegos: SPA original intacta bajo /juegos/
    spa = open(os.path.join(mirror, "index.html"), encoding="utf-8").read()
    spa = spa.replace('href="https://naroa.online/"', f'href="{DOMAIN}/juegos/"')
    spa = spa.replace('content="https://naroa.online"', f'content="{DOMAIN}/juegos/"')
    spa = spa.replace(
        "https://naroa.online/images/artworks/marilyn-rocks-hq-5.webp",
        f"{DOMAIN}/images/obra/marilyn-rocks.webp",
    )
    write("juegos/index.html", spa)

    # 6) SEO + deploy
    write("sitemap.xml", build_sitemap())
    write("robots.txt", ROBOTS)
    write("_redirects", CF_REDIRECTS.strip())
    write("_headers", CF_HEADERS.strip())

    # 7) works.json de referencia
    write("data/works-site.json", json.dumps(WORKS, ensure_ascii=False, indent=2))

    n = sum(len(fs) for _, _, fs in os.walk(out))
    logging.getLogger(__name__).info(f"OK → {out}  ({n} archivos, {len(WORKS)} obras)")


if __name__ == "__main__":
    main()
