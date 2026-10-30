---
title: Onboarding local y plantilla de observación
status: Integration example
version: 5.0.0
---

# Onboarding local y plantilla de observación

Esta guía parte del [Dockerfile raíz](../../Dockerfile), cuyo punto de entrada
es el CLI Python `babylon60`. Primero comprueba ese CLI y después muestra una
plantilla para su dashboard de lectura. No presupone una imagen publicada en
un registro ni un sidecar de ingesta gRPC listo para producción.

El antiguo nombre de modo `READ_ONLY_SHADOW_TAP` no establece por sí solo un
canal de ingesta, una frontera de autorización ni un cerrojo biométrico. Observar
un ledger no impide que otro proceso ejecute acciones. Una integración con un
agente necesita su propio contrato de entrada, permisos y controles de efectos.

## 1. Construir la imagen y comprobar el CLI

Desde la raíz del checkout, con Docker instalado y acceso a las imágenes base y
a las dependencias fijadas por el proyecto:

```sh
docker build --tag babylon60-local:docs .
docker run --rm --network none babylon60-local:docs --help
```

`babylon60-local:docs` es una etiqueta construida localmente. El éxito del build
y la disponibilidad de las imágenes base deben comprobarse en el entorno de
destino. La ayuda del CLI sólo verifica su arranque, sin lanzar el kernel nativo
ni ejecutar aprobaciones o efectos protegidos.

El dashboard actual utiliza `http.server` de la biblioteca estándar; este flujo
no requiere los extras FastAPI o Jinja2. Los ejemplos desactivan la escritura de
bytecode Python y fijan `BABYLON_HOME` en `/data`. Sin un volumen de datos, no se
crea allí una base ni se configura una ingesta.

## 2. Docker Compose: dashboard local

Guarda como `compose.yaml`. Este ejemplo requiere el plugin Docker Compose y la
imagen local construida en el paso anterior:

```yaml
services:
  babylon60_observer:
    image: babylon60-local:docs
    command: ["dashboard"]
    environment:
      BABYLON_HOME: "/data"
      BABYLON_DASHBOARD_HOST: "0.0.0.0"
      BABYLON_DASHBOARD_PORT: "8080"
      PYTHONDONTWRITEBYTECODE: "1"
    ports:
      - "127.0.0.1:8080:8080"
    read_only: true
    security_opt:
      - no-new-privileges:true
```

```sh
docker compose config --quiet
docker compose up -d
docker compose logs babylon60_observer
```

La interfaz queda en `http://127.0.0.1:8080/`. El dashboard lee una base SQLite
mediante una conexión `mode=ro`; sin la base esperada, `/api/metrics` devuelve una
lista vacía. Para aportar datos, revise el esquema y la ruta esperados en
[dashboard/server.py](../../01_KISH_ENGINE/babylon60/dashboard/server.py) y monte
una exportación compatible en sólo lectura. Este ejemplo no conecta el ledger
de un agente automáticamente ni publica una API de ingesta.

## 3. Kubernetes: manifiesto Deployment de ejemplo

Este es un manifiesto `apps/v1`, no un chart Helm. La imagen local debe estar
disponible en cada nodo que ejecute el pod; el build local de Docker no la
distribuye al clúster. En producción, sustituya la referencia por una imagen
revisada de su registro y fíjela por digest.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: babylon60-observer
spec:
  replicas: 1
  selector:
    matchLabels:
      app: babylon60-observer
  template:
    metadata:
      labels:
        app: babylon60-observer
    spec:
      containers:
        - name: observer
          image: babylon60-local:docs
          imagePullPolicy: Never
          args: ["dashboard"]
          env:
            - name: BABYLON_HOME
              value: "/data"
            - name: BABYLON_DASHBOARD_HOST
              value: "0.0.0.0"
            - name: BABYLON_DASHBOARD_PORT
              value: "8080"
            - name: PYTHONDONTWRITEBYTECODE
              value: "1"
          ports:
            - containerPort: 8080
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
          resources:
            limits:
              cpu: "500m"
              memory: "512Mi"
```

`spec.selector.matchLabels` coincide con las etiquetas del pod, conforme al
[contrato de Deployment de Kubernetes](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#selector).
Los límites de recursos son valores de ejemplo, no capacidad o consumo medidos.
`imagePullPolicy: Never` está limitado al ejercicio con una imagen precargada.

Guarda ese bloque como `deployment.yaml` y comprueba el esquema contra un
clúster de pruebas compatible antes de desplegar:

```sh
kubectl apply --dry-run=server -f deployment.yaml
```

El manifiesto no crea un Service ni una exposición externa. La validación del
servidor no confirma que la imagen arranque, que exista un ledger compatible o
que se estén recibiendo eventos.

## 4. Verificación de datos y exportación

Una respuesta HTTP del dashboard sólo demuestra disponibilidad del servidor.
La ingesta, la identidad del escritor y la integridad del ledger se comprueban
por separado con entradas y resultados conocidos.

Para revisar la interfaz de exportación instalada:

```sh
uv run --locked babylon60-compliance --help
```

La [guía de evidencia regulatoria](../05_compliance_eu_ai_act.md) describe los
argumentos `--bundle` y `--ledger`. Un informe exportado registra evidencia y
requisitos pendientes; no constituye por sí solo una certificación jurídica,
atestación biométrica ni aprobación para producción.
