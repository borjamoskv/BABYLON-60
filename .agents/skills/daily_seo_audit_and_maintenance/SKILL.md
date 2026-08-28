<!-- C5-REAL EXERGY CERTIFIED -->
---
name: daily_seo_audit_and_maintenance
description: Protocolo automatizado y herramienta de mantenimiento diario para SEO, GEO Local (ICBM, geo.position), sitemap.xml, robots.txt, metadatos Open Graph y validación de Schema.org JSON-LD (VisualArtist, ArtGallery, FAQPage, VisualArtwork).
---

# Skill: Auditoría y Mantenimiento Diario de SEO & GEO Local

Esta skill define la rutina automatizada para mantener la indexación, frescura de sitemap, posicionamiento local y metadatos SEO/GEO en proyectos web:

## Rutina de Verificación Diaria

1. **Sincronización de Sitemap & Dominio Canónico**:
   - **Matriz de Alineación de Dominio Canónico**: Garantizar que el dominio principal seleccionado (ej. `https://example.com/`) esté unificado en todos los puntos de la pila:
     - **HTML Head**: `<link rel="canonical" href="https://<domain>/" />`.
     - **OpenGraph & Twitter Cards**: `og:url`, `og:image`, `og:image:secure_url`, `twitter:url`, `twitter:image`.
     - **Grafo Schema.org JSON-LD**: Todos los `@id`, `url`, `publisher` y `creator` del grafo (`VisualArtist`, `WebSite`, `ArtGallery`, `VisualArtwork`, `FAQPage`).
     - **Sitemap & Robots**: `public/sitemap.xml` (`<loc>` e `<image:loc>`), `public/robots.txt` (`Sitemap:`) y `public/llms.txt` (`Sitio Web Oficial`).
     - **Código Fuente SPA**: Constantes de dominio en código (ej. `export const PORTAL` en `src/artworks.ts`).
   - Actualizar la fecha `<lastmod>YYYY-MM-DD</lastmod>` en `public/sitemap.xml` a la fecha actual del sistema.
   - Garantizar la referencia a `/llms.txt` en `robots.txt` para motores generativos de IA (ChatGPT, Perplexity, Claude, Gemini).

2. **Etiquetas Geográficas Locales (Local GEO & ICBM)**:
   - Verificar presencia de cabeceras de posicionamiento geográfico local:
     ```html
     <meta name="geo.region" content="ES-PV" />
     <meta name="geo.placename" content="Bilbao" />
     <meta name="geo.position" content="43.2630;-2.9350" />
     <meta name="ICBM" content="43.2630, -2.9350" />
     ```

3. **Auditoría del Grafo de Entidades Schema.org JSON-LD**:
   - Validar grafo `@graph` con nodos interconectados:
     - `@type: "VisualArtist"` (`@id: "#artist"`) con `jobTitle`, `knowsAbout`, `genre`, `knowsLanguage`.
     - `@type: "ArtGallery"` (`@id: "#gallery"` con dirección física en Bolueta, Bilbao, `postalCode` y `GeoCoordinates`).
     - `@type: "FAQPage"` (`@id: "#faq"` con `mainEntity` conteniendo preguntas/respuestas frecuentes sobre encargos y técnicas).
     - `@type: "VisualArtwork"` (con `creator: { "@id": "#artist" }` para piezas clave como `Marilyn Rocks` o `Amy Rocks`).

4. **Ejecución Programada por Cron**:
   - Programar auditorías recurrentes mediante `schedule` con la expresión `0 9 * * *`.
