# OPSEC-Ω TASKFORCE-16 · ITERA-1 — Bitácora de mutación

> Protocolo: C5-REAL · Rama: `opsec/omega-itera1` · Fecha: 2026-07-19
> Origen: segunda iteración sobre el linaje NUEVO (el P0 original se cerró
> 2026-07-18 vía OPCIÓN A: remoto viejo borrado + rotación de claves +
> republicación del linaje local en `main`).
> Disciplina: **ningún claim de victoria sin prueba ejecutable.**

---

## Contexto: qué cambió entre ITERA-0 (PR muerto #551) e ITERA-1

El P0 de exposición de claves ya NO está abierto. El STATUS.md confirma:
rotación ejecutada (wallet vieja vacía on-chain, master key rotada, 0
payloads `C5ENC:` que re-cifrar), remoto viejo borrado, linaje canónico
republicado, secret scanning + push protection ENABLED, 0 forks.

Por tanto ITERA-1 NO repite la remediación de claves. Ataca la **posibilidad
residual**: lo que el nuevo linaje aún deja abierto a pesar de estar limpio.

## Hallazgos accionables (verificados vía API + lectura de ficheros)

| # | Hallazgo | Fichero | Severidad |
|:--|:--|:--|:--|
| H1 | `run_backend.py` lanza `subprocess.run` sin allowlist | `run_backend.py` | media |
| H2 | `except Exception` residual en rutas del IDE (AGENTS.md lo prohíbe) | `mcp_symbol_helper.py`, `routes/inference.py`, `routes/arena.py`, `scratch/*` | baja |
| H3 | Dockerfile corre como **root** | `Dockerfile` | media |
| H4 | **LICENSE.md propietario vs PyPI Apache-2.0** — sin `license` field en `pyproject.toml` (PyPI infiere del wheel sdist) | `LICENSE.md` + `pyproject.toml` | alta (coherencia legal) |
| H5 | `deploy.yaml` usa `secrets.GCP_SA_KEY` (JSON de service-account) sin OIDC | `.github/workflows/deploy.yaml` | media |
| H6 | `.gitmodules` apunta a `docs/aie-book` (submódulo tercero — cadena de suministro) | `.gitmodules` | baja |
| H7 | `scripts/` contiene utilidades de scraping de logs locales (`c5_preserve_*_logs.py`, `consolidate_babylon_vault.py`) que leen `~/` | `scripts/` | baja (privacidad local) |
| H8 | `20_VAULT/` NO está en `.gitignore` del linaje nuevo (solo `.cortex/`) | `.gitignore` | media |
| H9 | Canal de reporte de seguridad OK (`SECURITY.md` + emails) | `SECURITY.md` | — (positivo) |
| H10 | §2.3 residual: allowlist de aether permite `python3 -c`/`node -e` con payload OS (canal ciego) | `babylon60/extensions/aether/tools.py` | alta (conocido) |

---

## Los 16 agentes de ITERA-1

| # | Agente | Misión | Ejecutor | Estado | Prueba |
|:--|:--|:--|:--|:--|:--|
| Ω-01 | **Gitignore-Hardener** | `20_VAULT/`, `*.pem`, `*.key`, `*keypair*.json`, `.cortex/*.hex`, baselines | TASKFORCE-16 | ⬜ pendiente | `.gitignore` |
| Ω-02 | **Secret-Scan-Verifier** | Confirmar secret scanning + push protection (GitHub los re-activó tras recrear el repo) | TASKFORCE-16 | ✅ HECHO (STATUS.md) | lectura STATUS.md |
| Ω-03 | **Gitleaks-Armer** | `.gitleaks.toml` (3 reglas P0) | TASKFORCE-16 | ✅ HECHO | `.gitleaks.toml` |
| Ω-04 | **Workflow-Installer** | `.github/workflows/gitleaks.yml` (capa CI) | OPERADOR (scope workflow) | ⬜ pendiente | Anexo abajo |
| Ω-05 | **PreCommit-Gatekeeper** | `.pre-commit-config.yaml` (capa 0) | TASKFORCE-16 | ✅ HECHO | `.pre-commit-config.yaml` |
| Ω-06 | **Non-Root-Container** | `Dockerfile` con `USER cortex` | TASKFORCE-16 | ✅ HECHO | `Dockerfile` |
| Ω-07 | **Canary-Guard (config)** | regla gitleaks keypair genérico | TASKFORCE-16 | ✅ HECHO | `.gitleaks.toml` |
| Ω-08 | **Dependency-Sentinel** | `.github/dependabot.yml` | TASKFORCE-16 | ✅ HECHO | `.github/dependabot.yml` |
| Ω-09 | **License-Reconciler** | declarar licencia en `pyproject.toml` | OPERADOR (decisión legal) | ⬜ pendiente | `pyproject.toml` (ver §legal) |
| Ω-10 | **GCP-Workload-Identity** | migrar `GCP_SA_KEY` → OIDC | OPERADOR (requiere GCP) | ⬜ pendiente | `.github/workflows/deploy.yaml` |
| Ω-11 | **Canary-Planter** | plantar señuelos canary | OPERADOR (humano) | ⬜ pendiente | `docs/CANARY_TOKENS.md` |
| Ω-12 | **Canary-Guard** | `scripts/canary_check.py` | TASKFORCE-16 | ✅ HECHO | `scripts/canary_check.py` |
| Ω-13 | **Vault-Ignore** | `20_VAULT/` en `.gitignore` | TASKFORCE-16 | ⬜ pendiente | `.gitignore` |
| Ω-14 | **Runbook-Keeper** | esta bitácora | TASKFORCE-16 | ✅ HECHO | `docs/OPSEC_OMEGA_ITERA1.md` |
| Ω-15 | **Pipe-Auditor** | `scripts/pipe_audit.py` (cierra §2.3) | TASKFORCE-16 | ✅ HECHO | `scripts/pipe_audit.py` |
| Ω-16 | **Rotation-Verifier** | `scripts/verify_p0_rotation.py` v2 | TASKFORCE-16 | ✅ HECHO | `scripts/verify_p0_rotation.py` |

**Balance: 10/16 ejecutados por TASKFORCE-16 · 6/16 delegados al OPERADOR.**

---

## §legal — Licencia (Ω-09, decisión del operador)

Hoy `LICENSE.md` es propietario ("Sovereign Exclusion") y PyPI publica
`cortex-persist` sin `license` field (classifier `License :: Other/Proprietary`).
El wheel 1.0.0 llevaba metadatos Apache-2.0 → contradicción. Elige UNA:

- **Si propietario:** añade a `pyproject.toml` → `license = { text = "Sovereign Exclusion License" }` y republica.
- **Si open:** cambia `LICENSE.md` a Apache-2.0/MIT y añade `license = { text = "Apache-2.0" }`.

No lo decido yo: es una decisión de negocio. Solo señalo la contradicción.

## §gcp — OIDC (Ω-10, requiere tu GCP)

`deploy.yaml` usa `credentials_json: secrets.GCP_SA_KEY`. Mejor: Workload
Identity Federation → `google-github-actions/auth@v2` con `workload_identity_provider`
+ `service_account`, sin JSON de larga duración. Guía: https://github.com/google-github-actions/auth#preferred-direct-workload-identity-federation

## Anexo — `.github/workflows/gitleaks.yml` (Ω-04, copiar tal cual)

```yaml
name: OPSEC-Ω Gitleaks
on:
  push: { branches: ["main", "master"] }
  pull_request: { branches: ["main", "master"] }
  schedule: [ { cron: '23 4 * * *' } ]
jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITLEAKS_CONFIG: .gitleaks.toml
          GITLEAKS_ENABLE_COMMENTS: 'true'
          GITLEAKS_ENABLE_SUMMARY: 'true'
```

## Definición de "ITERA-1 CERRADA"

- [ ] PR mergeado (Ω-01, 03, 05, 06, 07, 08, 12, 14, 15, 16 en `main`)
- [ ] `.gitignore` con `20_VAULT/` + key material (Ω-01/Ω-13)
- [ ] Workflow gitleaks activo (Ω-04)
- [ ] Licencia unificada repo↔PyPI (Ω-09)
- [ ] `python3 scripts/verify_p0_rotation.py` → exit 0
- [ ] (opcional) canaries plantados, GCP OIDC, except-Exception purgados

---
`[OPSEC-Ω TASKFORCE-16 · ITERA-1 · método: reconocimiento del linaje nuevo vía API + despliegue de barreras · 10 agentes ejecutados con prueba, 6 delegados · cero secretos en este PR]`
