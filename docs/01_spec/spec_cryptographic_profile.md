---
title: Perfil Criptográfico BABYLON-60
status: Perfil-normativo-con-implementaciones-legacy
version: 4.4.0
---

# Perfil criptográfico: requisitos y formatos versionados

Revisión científica: 2026-10-26. Este documento distingue requisitos de diseño y formatos observados en código. Se retira el sello genérico «Verified». La conformidad completa, la autenticidad de datos externos y la integración entre todos los productores/consumidores quedan **NO_VERIFICADAS** en esta revisión documental. [Informe y evidencia](AUDIT_SCIENTIFIC_GUARANTEES_2026.md).

---

## 1. Matriz normativa y compatibilidad

La referencia normativa del proyecto es la matriz de [CLAIMS.toml](../../CLAIMS.toml). Su declaración no demuestra por sí sola que cada ruta la implemente.

Existe además una discrepancia normativa: esa matriz incluye testigos/checksums SHA-256, mientras el [contrato Ring-0](../03_guides/agent_contracts.md#ring-0) lo reserva al prehash hardware P-256. La tabla siguiente identifica lo declarado/observado; no resuelve ese desacuerdo ni altera la precedencia de las instrucciones canónicas. La conformidad integral requiere resolverlo y verificar sus consumidores.

| Superficie | Perfil declarado u observado | Alcance |
| --- | --- | --- |
| IPC, digests de código/herramientas y Merkle conforme v1 | BLAKE3 canónico, según la matriz normativa | Requisito para sus formatos; no migra ni reinterpreta formatos legacy |
| Prehash de firmas hardware, testigos de descriptor y checksums de release | SHA-256, según la matriz normativa | Hash y firma son operaciones distintas; no acredita origen hardware o presencia humana |
| WAL binario legacy `.effect_wal.bin` de 154 bytes | SHA-256 de los primeros 122 bytes, tanto al escribir como al leer | Formato observado sin versión de algoritmo; BLAKE3 exige un formato sucesor y migración explícitos |
| Sobres/filas Python y árboles de auditoría legacy | SHA3-256; `compute_envelope_hash` usa JSON ordenado, no CBOR | Compatibilidad explícita con rutas históricas; no se renombra su digest a BLAKE3 |
| Tiempo y causalidad | Reloj lógico para hashes canónicos del protocolo; UTC como metadato | La existencia de un timestamp no prueba causalidad ni tiempo confiable; formatos legacy se verifican conforme a su versión |

La tabla anterior asignaba SHA3-256 y CBOR a todas las categorías. No describía la implementación actual: [cortex_crypto_kernel.py](../../01_KISH_ENGINE/babylon60/bft/cortex_crypto_kernel.py) contiene rutas JSON/SHA3-256 y [merkle_b3.py](../../01_KISH_ENGINE/babylon60/attestation/merkle_b3.py) define otro formato. Esta corrección documental no migra ni reinterpreta bytes persistidos.

### 1.1. Contrato del WAL binario legacy

[`WalRecord`](../../src/secure_fs.rs) conserva el formato existente: estado y efecto (`u8`), época (`u64` little-endian), nonce de 32 bytes, dispositivo e inodo (`u64` little-endian), hashes previo y posterior de 32 bytes, y digest SHA-256 de 32 bytes. Los primeros 122 bytes forman el payload y los últimos 32 su digest; el total es 154 bytes. No hay cabecera de versión ni etiqueta de algoritmo. El lector rechaza truncados y checksums distintos; no intenta BLAKE3 como alternativa. Un checksum no autentica al escritor frente a alguien que pueda reescribir payload y checksum.

Las referencias anteriores a «WAL de 154 bytes protegido con BLAKE3» eran incorrectas: el constructor y el lector ya usaban SHA-256. Se corrigen las declaraciones, conservando bytes, algoritmo y recuperación. El requisito normativo BLAKE3 para un sucesor no certifica la conformidad del formato legacy ni autoriza sustituir su hash sin versionado. [`wal_record_legacy_format.rs`](../../tests/wal_record_legacy_format.rs) fija un vector independiente, compara los bytes del escritor, comprueba lectura y reapertura del WAL real y rechaza BLAKE3, alteraciones y truncados. Las pruebas de proceso no acreditan corte eléctrico ni retención física de caché NVMe.

## 2. Separación de dominios: bytes concretos, no etiquetas intercambiables

El módulo BLAKE3 v1 observado define:

```text
leaf = BLAKE3(b"B60-LEAF-v1\x00" || data)
node = BLAKE3(b"B60-NODE-v1\x00" || left || right)
root = "b3:" || hex(BLAKE3(b"B60-ROOT-v1\x00" || count_u64_LE || top))
```

Los prefijos completos, el orden, el tratamiento de hojas impares y la cardinalidad forman parte del formato. Sustituirlos por los bytes únicos `0x00`/`0x01` produciría otro esquema. La separación de dominios distingue clases de entrada bajo las hipótesis criptográficas aplicables; no elimina todas las colisiones ni demuestra custodia de claves o validez factual de las hojas.

## 3. Serialización determinista: perfil que debe fijarse y comprobarse

Una superficie que declare CBOR determinista DEBE identificar el perfil, esquema, versión y reglas numéricas. En el perfil core de [RFC 8949 §4.2.1](https://www.rfc-editor.org/rfc/rfc8949.html#section-4.2.1), las claves se ordenan por sus codificaciones deterministas en orden lexicográfico de bytes; se exige la representación preferida y longitudes definidas. El orden length-first de §4.2.3 es distinto. El protocolo debe fijar equivalencias numéricas, claves duplicadas y valores no admitidos; UTF-8 y enteros cortos por sí solos no establecen canonicidad.

Este requisito no convierte el JSON legacy en CBOR ni demuestra correspondencia entre todas las codificaciones Rust/Python. La aceptación requiere vectores de bytes por perfil y versión, rechazo de entradas inválidas y comparación entre implementaciones identificadas.

## 4. Qué permite comprobar un compromiso criptográfico

Una cadena o árbol permite comprobar relaciones entre bytes y un compromiso de referencia, bajo el algoritmo y formato elegidos. La detección de una reescritura completa exige un checkpoint confiable independiente. Un hash aislado no identifica al autor ni autentica una observación externa.

Una firma válida requiere además vincular clave, identidad y autoridad. [RFC 9052 §4.4](https://www.rfc-editor.org/rfc/rfc9052.html#section-4.4) separa verificación criptográfica y comprobaciones de autorización de la aplicación. Ninguna de esas operaciones demuestra por sí sola que el efecto declarado ocurrió o que el contenido firmado es verdadero. No se certifican esas propiedades mediante este perfil.
