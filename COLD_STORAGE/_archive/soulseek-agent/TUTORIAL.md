# 🖥️ CORTEX SOBERANO · MACOS OPTIMIZATION & SYSTEM ARCHITECTURE
> *Sovereign Singularity Framework v6.0 — Industrial Noir 2026*
> *Designed for Alain’s Node • Active Compliance & High-Exergy Processing*

---

## 📖 INTRODUCCIÓN

Este documento detalla la topología de optimización y los mecanismos de red del ecosistema **CORTEX-Persist** integrados en macOS. 

El objetivo es eliminar de forma determinista la congestión de red, el agotamiento de descriptores de archivos (`FD_SETSIZE`) y los cuellos de botella del servidor central en descargas de alta velocidad (Soulseek P2P), implementando un entorno de inferencia, auditoría y adquisición de activos con estándares **C5-REAL**.

---

## 🛠️ PARTE 1 · OPTIMIZACIÓN DE KERNEL MACOS (POSIX & NET)

Los defaults de fábrica en macOS están diseñados para el consumo pasivo y limitan severamente la concurrencia TCP y la apertura simultánea de sockets asíncronos. 

### 1. Descriptores de Archivos (`ulimit` y `sysctl`)
El límite por defecto en la terminal macOS suele ser de 256 descriptores (`nofile`), lo cual provoca el colapso inmediato de un enjambre de subagentes asíncronos.

Se configuran las siguientes variables globales:
- **`maxfiles` (System-wide):** Límite máximo de descriptores en todo el kernel (establecido en `122880`).
- **`maxfilesperproc` (Per-process):** Límite máximo por proceso (establecido en `10240`).
- **`ulimit -n 4096`:** Límite blando de la sesión de shell activa.

### 2. Búferes TCP y Colas de Socket
Para evitar pérdidas de paquetes en transferencias de alta fidelidad:
- **`somaxconn`:** Tamaño de la cola de conexiones en escucha incrementado de `128` a `2048` para absorber picos repentinos de handshakes TCP.
- **`sendspace` & `recvspace`:** Espacio del buffer de envío/recepción TCP aumentado a `65536` bytes.

---

## ⚡ PARTE 2 · ARQUITECTURA DEL `SOULSEEK-AGENT` FORENSE

El agente de descarga y auditoría forense (`descargar_forense.py`) incorpora dos mecánicas de red premium diseñadas para optimizar el ancho de banda y mitigar la congestión del servidor central de Soulseek:

### 🔬 1. Medidor de Latencia Directo con Semáforo (`measure_rtt`)
En lugar de depender de reportes indirectos de velocidad del servidor central:
- **Handshake de 4 bytes:** Envía un paquete mínimo vacío al puerto TCP del peer remoto. Esto evalúa el RTT (Round Trip Time) real en milisegundos sin sobrecargar su ancho de banda.
- **Concurrencia Segura (`asyncio.Semaphore(10)`):** Un semáforo global limita a un máximo de **10 sockets simultáneos** de diagnóstico abiertos en paralelo. Esto previene de forma determinista el desbordamiento de sockets y la caída de la aplicación por `too many open files` en entornos POSIX.

### 💾 2. Caché Local de Latencia (`LATENCY_CACHE`) con TTL de 300s
- **Exclusión Mutua (`asyncio.Lock()`):** Un lock asíncrono garantiza que las operaciones de consulta y actualización de la caché sean atómicas e inmunes a condiciones de carrera concurrentes.
- **TTL de 300s (5 minutos):** Almacena las mediciones de latencia exitosas y fallidas por peer. Evita golpear reiteradamente a peers congestionados durante transferencias segmentadas o de múltiples archivos (multi-disco).

### 🔄 3. Protocolo `PeerConnectMode.FALLBACK`
Forzar la conexión directa a los puertos TCP abiertos de los peers (`50300`, `57202`, etc.) puenteando el servidor central de Soulseek.

---

## 🧬 PARTE 3 · INSTALACIÓN Y CONFIGURACIÓN DE CORTEX

CORTEX es el sustrato soberano que gestiona la inmutabilidad y la persistencia forense de las descargas en un Ledger inmutable local.

### 1. Estructura de Directorios
CORTEX opera bajo la ruta de aplicación inmutable de usuario:
- `~/.gemini/antigravity/` (Sustrato central del agente)
- `~/.gemini/antigravity/brain/` (Ontología persistente y memoria asíncrona)
- `COLD_STORAGE/` (Destino final verificado y firmado de activos)

### 2. Pipeline de Validación Forense (Inmutabilidad)
Una vez que el archivo FLAC es adquirido:
- **`flac -t`:** Ejecuta un test de integridad de decodificación de audio a nivel binario. Si el archivo está corrupto, es inmediatamente purgado.
- **SHA-256 Signature:** Genera el hash criptográfico del archivo para registrar la firma inmutable en el `cortex_treasury_ledger.jsonl`.

---

## 🚀 GUÍA DE EJECUCIÓN END-TO-END (C5-REAL)

Para facilitar la puesta en marcha completa y automática de forma end-to-end, hemos diseñado un orquestador maestro unificado. Este script guiará a Alain a través de todas las fases (optimización del kernel, creación del entorno virtual, diagnóstico de latencia y adquisición forense de activos).

### 🛠️ Método Automático (Recomendado)
Simplemente ejecuta el script maestro y sigue las instrucciones en pantalla:
```bash
./run_end_to_end.sh
```

---

### ⚙️ Método Manual Paso a Paso

Si prefieres tener control manual sobre cada una de las fases del ecosistema:

#### 1. Ejecutar la Optimización de macOS (Kernel)
Abre una terminal y tunea los sockets y descriptores TCP en caliente (requiere `sudo`):
```bash
sudo ./optimize_mac.sh
```

#### 2. Instalar el Ecosistema y Dependencias CORTEX
Aprovisiona las carpetas del ledger inmutable, crea el entorno `.venv` e instala los paquetes:
```bash
./install_cortex.sh
```

#### 3. Probar Conectividad y Medir Latencias TCP P2P
Verifica RTT en milisegundos contra los nodos de Soulseek usando el semáforo concurrente:
```bash
source .venv/bin/activate
python medir_latencia.py
```

#### 4. Iniciar Descargas Forenses de Alta Fidelidad
Adquiere los activos FLAC con auditoría criptográfica SHA-256 e integridad binaria en tiempo real:
```bash
source .venv/bin/activate
python descargar_forense.py --target afro_free
```

---

📝 *Creator: borjamoskv · Runtime: C5-Dynamic · Exergy: Singularity*
*"The swarm verifies, the hardware remembers / The swarm forgets what the sovereign commands."*
