# Configuración e Integración de Recepción Inbound Enterprise para borja@babylon60.com y support@babylon60.com

<div align="center">

[![C5-REAL Verified](https://img.shields.io/badge/C5--REAL-Verified-00F0FF?style=for-the-badge&logo=shield)](https://github.com/borjamoskv/BABYLON-60)
[![Régimen](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)

</div>

Esta guía documenta los pasos necesarios para habilitar la recepción programática de correos electrónicos en **`borja@babylon60.com`**, **`support@babylon60.com`** y cualquier alias comodín (`*@babylon60.com`) utilizando **Cloudflare Email Workers v2** y el **Receptor Backend Enterprise en Python (FastAPI)**.

---

## Arquitectura de la Solución v2

```mermaid
sequenceDiagram
    participant Sender as Remitente (Cliente/Dev)
    participant CF_MX as Cloudflare Email Routing (MX)
    participant CF_Worker as Cloudflare Email Worker v2
    participant Backend as Webhook Backend (FastAPI / Agent)

    Sender->>CF_MX: Envía email a borja@ o support@babylon60.com
    CF_MX->>CF_Worker: Dispara el evento email()
    CF_Worker->>CF_Worker: Parsea MIME, codifica adjuntos Base64 y firma con HMAC-SHA256
    CF_Worker->>Backend: HTTP POST con reintentos exponenciales (up to 3x)
    Backend->>Backend: 1. Verifica Firma HMAC & Token Bearer
    Backend->>Backend: 2. Control de Idempotencia (omite message_id duplicados)
    Backend->>Backend: 3. Clasificación de Intención (Security/Bug/Support) y Severidad (Urgent/High/Low)
    Backend->>Backend: 4. Decodificación de adjuntos de texto/código (Base64)
    Backend-->>CF_Worker: 200 OK (Procesado)
```

---

## Novedades de la Versión v2 (Enterprise)

1. **Reintentos Exponenciales en Cloudflare Worker**: El Worker reintenta la entrega hasta 3 veces si la API backend está temporalmente fuera de servicio.
2. **Extracción e Inspección de Adjuntos Base64**: Adjuntos de código, logs, archivos JSON o Markdown (hasta 2MB por adjunto) se decodifican automáticamente para que los agentes de IA de BABYLON-60 puedan analizarlos inmediatamente.
3. **Control de Idempotencia Integrado**: Previene el procesamiento duplicado de correos reenviados mediante rastreo en memoria de `message_id`.
4. **Clasificación de Intención y Severidad**: Categorización automática de incidentes (`SECURITY_INCIDENT`, `BUG_REPORT`, `TECHNICAL_SUPPORT`, `FEATURE_REQUEST`) y cálculo de urgencia (`URGENT`, `HIGH`, `MEDIUM`, `LOW`).

---

## 1. Configuración de Cloudflare Email Routing

Los registros MX de `babylon60.com` están apuntando a Cloudflare:
- `route1.mx.cloudflare.net` (Prioridad 12)
- `route2.mx.cloudflare.net` (Prioridad 61)
- `route3.mx.cloudflare.net` (Prioridad 29)

### Crear las Reglas en Cloudflare
1. Accede al panel de **Cloudflare** -> `babylon60.com`.
2. Ve a **Email** -> **Email Routing** -> pestaña **Routes**.
3. Configura las direcciones personalizadas apuntando al Worker `babylon60-email-inbound`:
   - `borja@babylon60.com` -> `Send to Worker` (`babylon60-email-inbound`)
   - `support@babylon60.com` -> `Send to Worker` (`babylon60-email-inbound`)
   - *(Opcional)* `*@babylon60.com` (Catch-all) -> `Send to Worker` (`babylon60-email-inbound`)

---

## 2. Despliegue del Email Worker v2

El código del Worker se encuentra en [`services/email_inbound/worker.js`](../01_KISH_ENGINE/services/email_inbound/worker.js).

```bash
cd 01_KISH_ENGINE/services/email_inbound
npx wrangler deploy
```

Configurar claves secretas en Cloudflare:
```bash
npx wrangler secret put WEBHOOK_SECRET
npx wrangler secret put WEBHOOK_URL
```

---

## 3. Integración Backend en Python (FastAPI)

El receptor backend se encuentra en [`01_KISH_ENGINE/babylon60/services/inbound_email.py`](../01_KISH_ENGINE/babylon60/services/inbound_email.py).

El receptor es una integración opcional: instalar `pip install '.[mail]'` y montar
su router explícitamente en una aplicación FastAPI. El servidor MCP base no
importa FastAPI ni carga este receptor. La verificación HMAC del webhook conserva
su contrato; configurar el secreto compartido de forma explícita.

### Ejemplo Completo de Uso:

```python
from fastapi import FastAPI
from babylon60.services.inbound_email import (
    InboundEmailProcessor,
    create_inbound_email_router,
    EnglishSupportAgentHandler,
)

app = FastAPI(title="BABYLON-60 Inbound Email API")

# 1. Crear el procesador con la clave secreta compartida con Cloudflare
processor = InboundEmailProcessor(secret="tu_clave_secreta_super_segura")

# 2. Registrar el handler de soporte con capacidad de análisis de adjuntos e intención
agent_handler = EnglishSupportAgentHandler()
processor.register_handler(agent_handler.handle)

# 3. Incluir el router en la app FastAPI
app.include_router(create_inbound_email_router(processor))
```

### Registro local de correo mediante MCP

El servidor `babylon60-mcp` arranca sin herramientas de correo y sin crear una
base de datos para correo. Para habilitar el registro local, proporcionar una
ruta explícita mediante el argumento existente:

```bash
babylon60-mcp --mail-ledger "$HOME/.babylon60/data/mail_ledger.db"
```

En Python, el mismo opt-in se realiza con
`CortexMCPServer(mail_ledger_path="/ruta/mail_ledger.db")`. La herramienta
`bft_send_sovereign_mail` y su implementación se cargan desde
[`mail_integration.py`](../01_KISH_ENGINE/babylon60/mcp/mail_integration.py)
solo en ese caso. Este registro MCP no necesita el extra FastAPI `mail`.

La herramienta conserva el nombre y el evento `BABYLON_MAIL_SENT` por
compatibilidad, pero su efecto es únicamente añadir un registro al ledger local.
No entrega mensajes por SMTP ni autentica al remitente: la etiqueta `from` se
deriva de `USER`. Habilitarla no sustituye autorización humana ni acredita un
envío. Las herramientas base, el CLI general y las implementaciones de
persistencia mantienen sus contratos.

---

## 4. Pruebas Automatizadas

Para ejecutar la suite de pruebas unitarias e integración:
```bash
pytest tests/test_inbound_email.py tests/test_optional_mail_mcp.py tests/test_cortex_mcp_server.py
```

---

## 5. Registro DNS DMARC Recomendado

Añade en la consola DNS de Cloudflare para maximizar la reputación del dominio:

| Tipo | Nombre | Contenido | TTL |
| :--- | :--- | :--- | :--- |
| **TXT** | `_dmarc` | `v=DMARC1; p=none;` | Auto |
