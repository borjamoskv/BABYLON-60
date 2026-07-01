---
name: OSINT-Mitigation-OMEGA
description: C5-REAL Sovereign Defensive Protocol against Open Source Intelligence
  vectors. Enforces structural mitigation of Dorking, EXIF exposure, and Wayback Machine
  indexing.
version: 1.0.0
category: seguridad-estructural
tags: [anti-recon, anti-exif, anti-wayback]
triggers: [/OSINT-Mitigation-OMEGA]
---

# █ OSINT-MITIGATION-Ω v1.0.0

> SYS_ID: OSINT_MITIGATION_OMEGA | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026

## 1. Core Mandate
- **[P0] Erradicación de Dorking**: Todo servidor web (Nginx/Apache/Caddy) o Framework DEBE tener el Directory Listing desactivado físicamente. El `robots.txt` es insuficiente; se exige inyección de cabecera `X-Robots-Tag: noindex, nofollow` en endpoints no indexables.
- **[P0] Sanitización EXIF**: Todo pipeline de subida o procesamiento de imágenes/documentos DEBE incluir un paso de stripping determinista (e.g., `exiftool -all=`, o librerías nativas) antes del almacenamiento persistente para erradicar metadatos geográficos y de hardware.
- **[P0] Aislamiento Wayback**: Todo endpoint que sirva datos dinámicos, confidenciales o temporales DEBE inyectar `Cache-Control: no-store, no-cache, must-revalidate, max-age=0` para envenenar la retención en cachés intermedios y rastreadores históricos como Wayback Machine.

## 2. Ejecución Forzada
Al implementar servidores, APIs o pipelines de media, MOSKV-1 inyectará autónomamente estas tres contramedidas. Cualquier omisión de estas capas defensivas se considera un fallo de entropía C4-SIM inaceptable.
