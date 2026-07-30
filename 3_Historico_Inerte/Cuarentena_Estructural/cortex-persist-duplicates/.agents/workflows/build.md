<!-- [C5-REAL] Exergy-Maximized -->
---
cat_id: build
cat_type: workflow
version: 1.1.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P1
description: "Compilaci\xF3n y despliegue r\xE1pido del binario/aplicaci\xF3n local\
  \ BABYLON-60"
---



# 🔨 Build BABYLON-60

## Install & Sync

1. Sincronización criptográfica del entorno y dependencias:
```bash
pip install -e ".[all]"
```

## QA & Linting (C5-REAL)

2. Purga de fricción termodinámica y aserción de tipos:
```bash
ruff check babylon60/
pyright babylon60/
```

## Test Engine (BFT)

3. Ejecución del motor de pruebas para consenso bizantino:
```bash
pytest tests/ -v --cov=babylon60
```

## Run Kernel

4. Ignición del API Gateway de BABYLON-60:
```bash
uvicorn babylon60.api:app --reload
```
