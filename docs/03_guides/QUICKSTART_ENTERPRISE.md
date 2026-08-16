---
title: BABYLON-60 Enterprise Quickstart
status: Causal-Determinist
version: 4.0.0
---

# QUICKSTART: Onboarding Enterprise y Despliegue Sidecar

<div align="center">

[![C5-REAL Verified](https://img.shields.io/badge/C5--REAL-Verified-00F0FF?style=for-the-badge&logo=shield)](https://github.com/borjamoskv/BABYLON-60)
[![Régimen](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)

</div>

**Guía DevOps e Infraestructura para Desplegar el Sidecar BABYLON-60 v4.0 en Modo Read-Only**

> BABYLON-60 v4.0 Sovereign Hardened · Enterprise Onboarding Guide

---

## 1. Prerequisites

Before deploying the BABYLON-60 sidecar container, ensure your environment meets the following minimum requirements:

- **Container Runtime:** Docker 24.0+ or Kubernetes 1.28+
- **Hardware:** 1 vCPU, 512MB RAM (Kernel is the lightweight Rust `moskv-1-apex` binary)
- **Permissions:** Read-only access to agent execution logs / gRPC stream
- **Handoff:** Python bridge delegating to Rust Kernel via zero-overhead `os.execv` (optional `pyo3` integration available)
- **Hardware Enclave (Optional):** TPM 2.0 device mapped at `/dev/tpmrm0` for hardware PCR quotes

---

## 2. Option A: Docker Compose Sidecar Deployment

Deploy BABYLON-60 as a sidecar container alongside your existing LLM agent service:

```yaml
version: '3.8'

services:
  # Your Existing LLM Agent (LangChain / AutoGen / Custom)
  your_agent_service:
    image: your-company/agent-app:latest
    environment:
      - B60_TELEMETRY_ENDPOINT=http://b60_kernel:50051
    ports:
      - "8000:8000"

  # BABYLON-60 v4.0 Sovereign Hardened Sidecar
  b60_kernel:
    image: babylon60/kernel:4.0.0-sovereign
    environment:
      - CORTEX_LICENSE_KEY=${CORTEX_LICENSE_KEY:-DEMO_EVALUATION_KEY}
      - B60_MODE=READ_ONLY_SHADOW_TAP
      - B60_WORM_QUARANTINE_PATH=/var/log/b60_quarantine
    volumes:
      - b60_audit_data:/var/log/b60_quarantine
    devices:
      - "/dev/tpmrm0:/dev/tpmrm0" # Optional TPM 2.0 mapping

volumes:
  b60_audit_data:
```

Launch with:

```bash
docker compose up -d
```

---

## 3. Option B: Kubernetes Helm Chart Deployment

Inject the BABYLON-60 container into your Kubernetes agent pod:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: Enterprise-ai-agent
spec:
  replicas: 2
  template:
    spec:
      containers:
        - name: agent-app
          image: your-company/agent-app:latest

        - name: babylon60-governance-sidecar
          image: babylon60/kernel:4.0.0-sovereign
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

Verify that the BABYLON-60 sidecar is successfully ingesting telemetry and building the Merkle-Causal DAG Ledger:

```bash
# Check sidecar logs
docker logs b60_kernel

# Expected output:
# [MOSKV APEX] Causal-Determinist Kernel v4.0.0 Initialized.
# -> [Telemetry Tap] Ingesting agent events via gRPC stream...
# -> [Merkle DAG] Building local tamper-evident event chain.
```

---

## 5. Generating Day-7 Compliance Reports

Run the compliance exporter to generate localized audit certificates for regulators:

```bash
# Inside the container or via CLI
python3 scripts/export_country_compliance.py --locale es --output /var/log/b60_quarantine/CERTIFICADO_AESIA.md
```

The generated report is ready to submit to your compliance officer or national supervisory authority.

---

<sub>BABYLON-60 v4.0 Sovereign Hardened · Enterprise Quickstart Guide · Borja Moskv</sub>