# Deploy — naroagutierrezgil.com

Sitio generado en `web/` (estático, listo para Cloudflare Pages). Regenerar: `python3 build_site.py`.

## 1. Desplegar

```bash
npx wrangler pages deploy web/ --project-name naroagutierrezgil
```

## 2. Asignar dominios al proyecto (Cloudflare Pages → Custom Domains)

Añade, en este orden:

1. `naroagutierrezgil.com` ← dominio principal
2. `www.naroagutierrezgil.com`
3. `naroa.online` y `www.naroa.online` ← necesarios para que el redirect 301 funcione

Los redirects 301 (`naroa.online/* → naroagutierrezgil.com/*`, y `www → apex`) ya están
definidos en `web/_redirects` — solo funcionan si los 4 dominios cuelgan del mismo proyecto.

## 3. Qué se ha mejorado respecto a naroa.online

- **URLs reales indexables** (`/obra/marilyn-rocks`) en vez de rutas hash (`#/destacada`)
  → 28 páginas de obra con `VisualArtwork` schema.org, título, descripción y og:image propios.
- **og:image roto arreglado**: la web actual apunta a `/images/artworks/…` que devuelve 404
  (las tarjetas de WhatsApp/Twitter salen sin imagen). Ahora `/images/obra/<slug>.webp` existe.
- **Landing `/retratos-hiperrealistas-bilbao` recuperada**: estaba en el sitemap pero daba 404.
  Ahora existe con FAQ schema.org.
- **Sitemap sin URLs muertas** + robots.txt sin bloquear las imágenes.
- **Miniaturas 640px** en la galería (2 MB vs 6,6 MB) — carga mucho más rápida.
- **Los 21 minijuegos se conservan** intactos en `/juegos/` (la SPA original completa).
- Cache immutable para `/assets/`, headers de seguridad básicos.

## 4. Pendiente / notas

- El catálogo `data/database.json` tiene 74 obras pero solo 28 con imagen real
  (el resto `placeholder.webp`, y muchos años "2026" por defecto). Cuando haya fotos
  nuevas: añadir la obra a `WORKS` en `build_site.py` y regenerar.
- Las exposiciones de `exhibitions.json` no se han publicado por no poder verificarlas.
- Search Console: dar de alta `naroagutierrezgil.com` y enviar `sitemap.xml` tras el deploy.
