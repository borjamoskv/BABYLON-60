# -*- coding: utf-8 -*-
---
description: "Exponer CORTEX y MOSKV‑1 para análisis por IA externas"
workflow: analysis_pipeline
expected_duration_min: 15
---
1. **Crear un entorno virtual** (si aún no existe)
   ```bash
   python -m venv .venv && source .venv/bin/activate
   ```

2. **Instalar dependencias necesarias** (FastAPI, Uvicorn, PyJWT, cryptography, httpx)
   // turbo
   ```bash
   pip install fastapi uvicorn[standard] pyjwt cryptography httpx
   ```

3. **Agregar el módulo API** – crear `cortex/api/analysis.py` (ver código a continuación).

4. **Añadir tema personalizado para Swagger** – crear `cortex/api/swagger_theme.css` (ver código a continuación).

5. **Registrar el servicio en el registro CORTEX** usando la skill `singularity-nexus`:
   ```bash
   cortex nexus register --name cortex-analysis --url http://localhost:8000/openapi.json --auth jwt
   ```

6. **Ejecutar el servicio localmente** (modo desarrollo)
   // turbo
   ```bash
   uvicorn cortex.api.analysis:app --host 0.0.0.0 --port 8000 --reload
   ```

7. **Ejecutar comprobación de sanidad** – invocar el endpoint de salud y una consulta de ejemplo:
   ```bash
   curl -s http://localhost:8000/health | jq .
   curl -s http://localhost:8000/facts?query=security | jq .
   ```

8. **(Opcional) Desplegar a producción** – sustituir el paso 6 por una unidad systemd o contenedor Docker.
   ```bash
   # Ejemplo Dockerfile (no ejecutado aquí)
   FROM python:3.12-slim
   WORKDIR /app
   COPY . .
   RUN pip install -r requirements.txt
   CMD ["uvicorn", "cortex.api.analysis:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

9. **Documentar la API** – la UI de Swagger estará disponible en `http://localhost:8000/docs` con el tema oscuro personalizado.