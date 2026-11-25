---
title: BABYLON-60 Enterprise Quickstart
status: Causal-Determinist
version: 5.1.0
---

# QUICKSTART: Onboarding Enterprise y Despliegue Sidecar

<div align="center">

[![C5-REAL Verified](https://img.shields.io/badge/C5--REAL-Verified-00F0FF?style=for-the-badge&logo=shield)](https://github.com/borjamoskv/BABYLON-60)
[![Régimen](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)

</div>

**Guía DevOps e Infraestructura para Desplegar el Sidecar BABYLON-60 v5.1.0 en Modo Read-Only**

> BABYLON-60 v5.1.0 · Enterprise Onboarding Guide (espacio de usuario / EL0; todo el código reside en este monorepo, sin repositorios hermanos requeridos)

---

## 1. Prerequisites

Before deploying the BABYLON-60 sidecar container, ensure your environment meets the following minimum requirements:

- **Container Runtime:** Docker 24.0+ or Kubernetes 1.28+ (build the local image from the repository [`Dockerfile`](../../Dockerfile): `docker build -t babylon60/kernel:5.1.0 .`)
- **Hardware:** 1 vCPU, 512MB RAM (Python CLI/MCP `babylon60` / `babylon60-mcp`, plus optional native Rust binaries defined in [`Cargo.toml`](../../Cargo.toml): `babylon-kernel`, `babylon-authorityd`, `babylon-regulatory-gate`, `babylon-dsl`, `babylon-budget-gate`, `babylon-top`)
- **Permissions:** Read-only access to agent execution logs / IPC boundary
- **Handoff:** Python CLI/MCP entrypoint (`babylon60`, `babylon60-mcp`) with optional Rust broker integration (`pyo3` / C-ABI)
- **Hardware Enclave:** Hardware TPM 2.0 integration is currently on the roadmap (software cryptographic notary active by default; macOS Secure Enclave / Touch ID applies to native Apple Silicon hosts).

---

## 2. Option A: Docker Compose Sidecar Deployment

Deploy BABYLON-60 as a sidecar container alongside your agent service (example template; build `babylon60/kernel:5.1.0` locally from the repo `Dockerfile` before launching):

```yaml
services:
  # Agent service communicating over the configured boundary
  native_agent_service:
    image: your-company/native-agent-app:latest
    environment:
      - B60_TELEMETRY_ENDPOINT=http://b60_kernel:8080
      - B60_CABI_IPC=/var/run/b60/manifest.shm
    volumes:
      - b60_ipc_socket:/var/run/b60
    ports:
      - "8000:8000"

  # BABYLON-60 v5.1.0 Sidecar (user-space authorization broker & dashboard/MCP)
  b60_kernel:
    image: babylon60/kernel:5.1.0
    environment:
      - BABYLON60_LICENSE_KEY=${BABYLON60_LICENSE_KEY:-DEMO_EVALUATION_KEY}
      - B60_MODE=READ_ONLY_SHADOW_TAP
      - B60_WORM_QUARANTINE_PATH=/var/log/b60_quarantine
      - B60_CABI_IPC=/var/run/b60/manifest.shm
    volumes:
      - b60_audit_data:/var/log/b60_quarantine
      - b60_ipc_socket:/var/run/b60
    # devices:
    #   - "/dev/tpmrm0:/dev/tpmrm0" # Roadmap: Future TPM 2.0 hardware anchoring

volumes:
  b60_audit_data:
  b60_ipc_socket:
```

Launch with:

```bash
docker build -t babylon60/kernel:5.1.0 .
docker compose up -d
```

---

## 3. Option B: Kubernetes Deployment Template

Inject the BABYLON-60 container into your Kubernetes agent pod (using your internal registry mirror of the image built from `Dockerfile`):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: enterprise-sovereign-agent
spec:
  replicas: 2
  template:
    spec:
      containers:
        - name: native-agent-app
          image: your-company/native-agent-app:latest

        - name: babylon60-governance-sidecar
          image: babylon60/kernel:5.1.0
          env:
            - name: B60_MODE
              value: "READ_ONLY_SHADOW_TAP"
          resources:
            limits:
              cpu: "500m"
              memory: "512Mi"
```

---

## 4. Verification & Testing

Verify the sidecar logs and local CLI health after startup (exact log lines depend on the selected entrypoint: `babylon60` from `Dockerfile` or native Rust `babylon-kernel` / `babylon-authorityd`):

```bash
# Check sidecar logs
docker logs b60_kernel

# Verify CLI availability inside the container
docker exec b60_kernel babylon60 --version
```

---

## 5. Generating Compliance Evidence Reports

Run the compliance exporter to generate localized technical evidence packages for review:

```bash
# Inside the container or via local checkout
python3 scripts/c5_utils/export_country_compliance.py --locale es --output /var/log/b60_quarantine/CERTIFICADO_AESIA.md
```

The generated report provides structured technical evidence (traceability and logging controls) for your compliance officer to review; generating the report does not by itself certify regulatory compliance under the EU AI Act.

---

<sub>BABYLON-60 v5.1.0 · Enterprise Quickstart Guide · Borja Moskv</sub>
