# 🐤 Canary Tokens Guide (OPSEC-Ω Taskforce-16)

## 📌 Propósito

Los Canary Tokens son trampas criptográficas/de red diseñadas para alertar al operador si un actor malicioso o un subagente no autorizado intenta acceder o exfiltrar credenciales simuladas en el ecosistema BABYLON-60.

---

## 🛡️ Despliegue de Canary Tokens

### 1. Webhook Canary Token
Plantar en archivos ficticios de configuración de pruebas (e.g., `tests/fixtures/fake_aws_credentials`):

- **Tipo:** AWS Key / HTTP Webhook
- **Alert Target:** Alerta inmediata vía Telegram / Webhook a la pasarela `whatsapp-nexus` o canal seguro.

### 2. DNS Canary Token
Plantar en comentarios de código o manifiestos de simulación:

- **Dominio:** `*.canarytokens.com` o subdominio Soberano privado.
- **Acción:** Registro de accesos IP no autorizados en tiempo real.

---

## 🔒 Invariantes de Seguridad

1. **Jamás commit de tokens reales.** Todos los canary tokens son inocuos y solo registran metadatos de acceso (IP, User-Agent, timestamp).
2. **Alerting Automático:** Si un token salta, el `opsec_sentinel_c5.py` debe congelar inmediatamente los workflows de CI/CD.
