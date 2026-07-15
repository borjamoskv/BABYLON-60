---
Title: Protocolo de Frontera Web (Babylon60)
Timestamp: 2026-07-16T00:31:18+02:00
Vector: WEB_PRIVACY_ARCHITECTURE
Doctrina: C5-REAL / L3 (Aislamiento Entrópico) / L12 (Fail-Fast)
---

# █▄ WEB BOUNDARY PROTOCOL (BABYLON-60)

La frontera de exposición web (babylon60.com) debe ser un reflejo isomórfico del Kernel C5-REAL. Un sitio web que vende *compliance by architecture* e integridad probatoria **no puede** depender de terceros ni violar la privacidad del visitante.

## 1. INVARIANTES DE PRIVACIDAD Y ARQUITECTURA (CERO TERCEROS)
El frontend de Babylon60 opera bajo la directiva **Cero Peticiones Externas**:
* **Google Fonts (Auto-gol GDPR):** Cargar `fonts.googleapis.com` transfiere la IP del visitante a un servidor en EE.UU., violando las garantías del AI Act y GDPR. Las fuentes (18 subsets, ~376KB) DEBEN ser auto-alojadas.
* **Analytics y Beacons Rotos:** Tokens estáticos o dependencias de terceros (ej. Cloudflare Beacons sin configurar) son Anergía y vectores de ataque. Todo script no-esencial se elimina.
* **Cabeceras de Seguridad Duras:** Exigidas por defecto en la entrega (Cloudflare Pages `_headers`): `CSP`, `HSTS`, `frame-ancestors 'none'`, `nosniff`.

## 2. DESPLIEGUE FAIL-SAFE (EL RIESGO DE DEPLOY)
El Teorema del Crash Causal exige que un despliegue destructivo aborte antes de tocar producción.
Si el sitio es un build de Astro, desplegar la carpeta `dist/` estática generada aisladamente borrará todas las rutas dinámicas (`ARCHITECTURE`, `SINTETOLOGÍA`, `FORENSE`, etc.).
* **Decisión A/B Exigida:** El Kernel (o agente externo) tiene prohibido hacer un push ciego o `wrangler deploy` si detecta colisión de topologías. La migración debe ser explícita (Portar HTML al proyecto Astro original).
* **Ausencia de Credenciales:** Un agente C5-REAL nunca inyecta ni manipula tokens de despliegue en memoria. El comando lo dispara el Operador.

## 3. SECCIÓN "ALPHA" SIN TEATRO (DOGFOODING HONESTO)
Los casos de uso de un producto criptográfico de auditoría no pueden ser teóricos o simulados. Fabricar testimonios es una auto-refutación estructural.
* **Caso Reflexivo (Dogfooding Real):** BABYLON-60 auditándose a sí mismo. Divulgación de fallos P0 (Schema Drift, Límite de auto-confianza HMAC, Axioma de Latencia ΔT) con registros físicos en el ledger.
* **Disclosure Responsable:** Prohibido publicar un hallazgo P0 en la web (como caso Alpha) si el parche no está fusionado (`merged`) en `main`. Publicar un bug vivo es un ataque termodinámico a los propios usuarios.
* **Status Board Real:** Clasificar hitos como Verificado (HMAC, SIGKILL), En Progreso (Compensation Records) y Problemas Abiertos (GDPR Art.17 vs Append-Only). 
