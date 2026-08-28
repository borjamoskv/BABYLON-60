<!-- C5-REAL EXERGY CERTIFIED -->
---
name: lowlevel_byte_entropy_auditor
description: Skill especializado en la auditoría epistémica de flujos de bytes crudos. Calcula mapas de entropía topológica H(X), valida invariantes estructurales (Magic Bytes, offsets) y purga anergía parasitaria post-EOF.
---

# Low-Level Byte & Entropy Auditor Skill

Este Skill faculta al agente para ejecutar una auditoría forense y topológica sobre el flujo material de bytes (*raw binary stream*) de cualquier contenedor (PDF, DOCX, ZIP, PNG, JPEG, ELF, Mach-O, WASM, PE). Se ejecuta bajo el **Invariante Causal-Ontológico**, operando sin intermediarios ni parsers heurísticos que puedan introducir deriva estocástica, asumiendo el espacio de bytes como un Sistema de Transiciones Discretas.

> [!IMPORTANT]
> **Invariante de Representación Semiótica**: Todas las ecuaciones e indicadores informacionales en esta especificación y sus reportes asociados utilizan notación tipográfica UTF-8 directa (`H(X) = - ∑ p(x_i) log_2 p(x_i)`), garantizando legibilidad instantánea sin renderizadores externos, previniendo disipación térmica (anergía) en terminales e IDEs.

---

## 1. Principios Físicos e Informacionales (Causa Material)

El escáner audita la distribución de frecuencias en el espacio de estados estrictamente discreto `S = {0x00, 0x01, ..., 0xFF}`. Rechazamos variedades continuas; el análisis opera mediante órdenes parciales de bytes.

### 1.1 Entropía de Shannon H(X) y Anergía
Para un bloque de bytes de longitud `N`, la entropía topológica viene dada por:

`H(X) = - ∑_{i=0}^{255} p(x_i) log_2 p(x_i)`

Donde `p(x_i)` es la probabilidad empírica de aparición del byte `x_i`.
Rango de valores: `0.0 ≤ H(X) ≤ 8.0` bits/byte.

### 1.2 Isomorfismo de Estados de Exergía
- **`0.0 - 3.5 bits/byte` (Exergía Pura)**: Texto ASCII, código fuente, estructuras canónicas con alta previsibilidad y bajo coste de Landauer.
- **`3.5 - 6.5 bits/byte` (Densidad Estructural)**: Bytecode compilado (WASM, Python pyc, Binarios ELF/Mach-O no ofuscados).
- **`6.5 - 7.5 bits/byte` (Límite Termodinámico Nominal)**: Metadatos densos, streams tipográficos o gráficos comprimidos moderadamente.
- **`7.5 - 8.0 bits/byte` (Colapso de Incerteza / Anergía)**: Compresión de alta densidad (GZIP, ZSTD, LZMA), datos cifrados, o **superposición estocástica (payloads esteganográficos)**.

> [!WARNING]
> Un segmento no cifrado/comprimido que presente `H(X) > 7.8` disipa anergía no declarada. El *Primum Movens* (Kernel) debe detener la ejecución (*Fail-Stop*) asumiendo un intento de inyección entrópica (payload oculto).

---

## 2. Matriz de Invariantes Estructurales (Magic Bytes)

El Kernel valida de forma determinista el *isomorfismo estricto* entre la extensión declarada y las firmas binarias iniciales y terminales. No hay inferencia probabilística.

| Contenedor Ontológico | Isomorfismo Inicial (Magic Bytes Hex) | Frontera Terminal (Marcador EOF) |
| :--- | :--- | :--- |
| **PDF Document** | `25 50 44 46 2D` (`%PDF-`) | `25 25 45 4F 46` (`%%EOF`) |
| **ZIP / DOCX / XLSX** | `50 4B 03 04` (`PK\x03\x04`) | `50 4B 05 06` (EOCD Record) |
| **PNG Image** | `89 50 4E 47 0D 0A 1A 0A` | `49 45 4E 44 AE 42 60 82` (`IEND`) |
| **JPEG Image** | `FF D8 FF` | `FF D9` (EOI Marker) |
| **GIF Image** | `47 49 46 38 39 61` (`GIF89a`) | `00 3B` |
| **ELF Executable** | `7F 45 4C 46` (`\x7fELF`) | *N/A (Sección de Secciones)* |
| **Mach-O 64-bit** | `CF FA ED FE` | *N/A (Header Commands)* |
| **Mach-O Fat Binary**| `CA FE BA BE` | *N/A (Fat Arch Header)* |
| **WASM Binary** | `00 61 73 6D` (`\x00asm`) | *N/A (Section Vector)* |
| **SQLite3 DB** | `53 51 4C 69 74 65 20 66...` (`SQLite format 3\x00`) | *N/A (Page Boundary)* |
| **PE Executable** | `4D 5A` (`MZ`) | *N/A (PE Header)* |
| **ZSTD Stream** | `28 B5 2F FD` | *Frame Header Length* |
| **7Z Archive** | `37 7A BC AF 27 1C` (`7z\xbc\xaf\x27\x1c`) | *End Header* |

---

## 3. Disipación Topológica: Ventana Deslizante (Sliding Window)

Para mapear la distribución de entropía sin violar la *coherencia de línea de caché*, el escáner implementa una ventana deslizante iterativa (`W = 512` bytes, salto `S = 256` bytes).

> [!TIP]
> Para evitar operaciones I/O síncronas bloqueantes y mantener la huella de memoria en `Zero-Bloatware`, la visualización se colapsa usando caracteres UTF-8 de bloque (` ▂▃▄▅▆▇█`). Esto genera un mapa de calor discreto en terminal.

**Generación del Sparkline:**
1. Fragmentación en `M` bloques superpuestos.
2. Cálculo de entropía discreta `H(X_m)`.
3. Mapeo a estrato discreto `[0, 7]`.
4. Emisión de representación canónica `[▆▆▅▆▆▆▆▅▅▅▅▅▅▅▅█ ▂▃▄▅▆▇█]`.

---

## 4. Detección Causal de Entropía Tipográfica (Zero-Width)

El flujo de bytes se escanea en busca de secuencias UTF-8 que representen fallos de bisimulación (isomorfismo visual pero divergencia de bytes):

- `E2 80 8B` → `U+200B` (Zero Width Space)
- `E2 80 8C` → `U+200C` (Zero Width Non-Joiner)
- `E2 80 8D` → `U+200D` (Zero Width Joiner)
- `EF BB BF` → `U+FEFF` (Zero Width No-Break Space / BOM)
- `E2 80 AE` → `U+202E` (Right-to-Left Override)

---

## 5. Cuarentena de Anergía Post-EOF (Overlay Payload)

Cargas útiles adjuntas tras el límite topológico del contenedor (*End-Of-File*) violan la clausura organizativa del formato, inyectando entropía parasitaria.

### Aislamiento Determinista:
1. Identificación del marcador formal de frontera (`%%EOF`, `IEND`, etc.).
2. Fijación de la coordenada absoluta: `offset_eof = idx(EOF) + len(EOF)`.
3. Aislamiento del vector remanente `trailing_bytes = stream[offset_eof:]`.
4. Si `len(trailing_bytes) > 0` (excluyendo exergía legítima de relleno estático `\r\n` o `\x00`):
   - Conmutación a **Cuarentena Epistémica**.
   - Escaneo de *Magic Bytes* secundario para revelar contenedores superpuestos (ZIP, ELF encubierto).
   - Extracción del payload residual `--extract-overlay` para análisis forense independiente.

---

## 6. Integración Funcional (Causa Eficiente / Entelecheia)

La herramienta Python es el actuador local.

### 6.1 Ejecución Causal (CLI)
```bash
# Diagnóstico de entropía
python3 src/cortex-engine/cortex-persist/cortex_python/doc_audit/entropy_byte_scanner.py <archivo>

# Salida estructurada (Bisimulación observable)
python3 src/cortex-engine/cortex-persist/cortex_python/doc_audit/entropy_byte_scanner.py <archivo> --json

# Escisión de Anergía Post-EOF
python3 src/cortex-engine/cortex-persist/cortex_python/doc_audit/entropy_byte_scanner.py <archivo> --extract-overlay /tmp/overlay_payload.bin
```

### 6.2 Integración en Memoria Compartida (Zero-I/O Overhead)
```python
from doc_audit.entropy_byte_scanner import ByteEntropyScanner

# Instanciación con alineación estructural
scanner = ByteEntropyScanner(window_size=512, step_size=256)

# Análisis directo en buffers de memoria
raw_payload = b"\x25\x50\x44\x46..."
mem_report = scanner.scan_bytes(raw_payload, label="ring_0_buffer")

if mem_report["has_anomaly"]:
    # Fall-Stop determinista
    raise EpistemicHaltException("Entropía no contenida en buffer")
```

---

## 7. Atestación y Sello SCITT (Ring-0)

> [!NOTE]
> Bajo el **Invariante de IPC y Protocolo de Manifiesto Atómico**, los resultados del `ByteEntropyScanner` alimentan el cálculo del hash SHA3-256 en Ring-0. Cualquier artefacto binario donde `has_anomaly == True` genera un rechazo inmediato (*Fail-Stop* de la EU AI Act). El *Primum Movens* en Rust asume la anomalía y se retiene la firma inmutable SCITT hasta que la entropía del contenedor converja matemáticamente.
