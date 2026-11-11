# ⚙️ Tools — Utilidades de Auditoría, Atestación y Biblioteca de Skills (`tools/`)

> **DOMINIO DE HERRAMIENTAS OPERATIVAS Y ORÁCULOS**  
> Ubicación: `tools/`  
> Contiene utilidades de verificación de brechas de referencias (`existence_gap.py`), empaquetado de auditorías de cumplimiento, firmado de recibos TAMKARUM-60 y la biblioteca portable de skills (`skill_library/`).

## 📐 Catálogo de Herramientas en `tools/`

| Herramienta / Directorio | Propósito Funcional |
| :--- | :--- |
| [`existence_gap.py`](existence_gap.py) | Auditoría de *Existence Gap* para detectar imports o referencias a símbolos inexistentes en el repositorio. |
| [`generate_compliance_audit_pack.py`](generate_compliance_audit_pack.py) | Generador de paquetes de evidencia técnica y matrices de trazabilidad para revisiones de cumplimiento. |
| [`babylon60_mcp.py`](babylon60_mcp.py) · [`codex_tunnel.py`](codex_tunnel.py) | Puntos de entrada auxiliares para puente MCP y túnel de integración con Codex. |
| [`grounding_interceptor.py`](grounding_interceptor.py) · [`examples/`](./examples/) | Interceptor de anclaje empírico y ejemplos de scripts `.b60` (`hello_causal.b60`, `scheduler.b60`). |
| [`tamkarum_attestation_engine.py`](tamkarum_attestation_engine.py) · [`tamkarum_batch_signer.py`](tamkarum_batch_signer.py) · [`tamkarum_license_provisioner.py`](tamkarum_license_provisioner.py) | Utilidades de firmado criptográfico por lotes, atestación y aprovisionamiento de licencias para TAMKARUM-60. |
| `skill_library/` | Biblioteca versionada de skills (`global/`, `workspace/`, `codex_overrides/`) mantenida con `scripts/c5_skills_ontology/maintain_skill_library.py`. Privada: excluida de la proyección pública (`VAULT_ONLY_PREFIXES`), por eso no se enlaza. |
| [`Anergy_Audit.yml`](Anergy_Audit.yml) | Especificación declarativa de auditoría de higiene del repositorio. |

## 🛡️ Pautas de Uso
- Las herramientas de verificación y atestación operan de forma determinista y sin estado oculto: leen los artefactos de entrada, comprueban las invariantes y devuelven un código de salida explícito (`0` / `1`).
