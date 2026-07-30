<!-- [C5-REAL] Exergy-Maximized -->
# CEP-002: Type System (EDL & Primitives)

* Id: CEP-002
* Título: Sistema de Tipos y Epistemic Definition Language (EDL)
* Estado: Borrador Inicial (Draft)
* Ámbito: Arquitectura del Microkernel
* Fecha: Junio 2026

------------------------------
## 1. Definición del Problema
Para que el microkernel garantice la invariancia estructural definida en [CEP-001](CEP-001_Core_Kernel_Contracts.md), la representación en memoria y en disco de los objetos epistemológicos debe ser determinista. Las interfaces y lógicas no pueden procesar `EpistemicObjects` si los tipos fundamentales, los algoritmos de serialización y el cálculo de hashes son ambiguos.

Esta especificación (CEP-002) define formalmente:
1. Las **Primitivas de Datos Criptográficos**.
2. El **Epistemic Definition Language (EDL)**: sintaxis abstracta para Assertions.
3. El **Protocolo de Serialización Canónica** para asegurar que un mismo estado genere siempre el mismo Hash Estructural.

------------------------------
## 2. Tipos Primitivos del Sistema

Ningún objeto del dominio puede utilizar tipos nativos sin envoltura (wrappers) que aseguren la trazabilidad.

* `StateID`, `CommitID`, `AssertionID`, etc.: Mapeados directamente a **UIDv7** (Universally Unique Lexicographically Sortable Identifier).
  * *Justificación:* UUIDv7 incluye un timestamp linealizable en sus primeros 48 bits, lo que permite ordenamiento topológico temporal nativo en la base de datos sin depender de los relojes del proveedor.
* `Hash`: Secuencia binaria de 256 bits calculada mediante **SHA-256** o **SHA3-256**.
  * *Aplicación:* Representación criptográfica del contenido estructural serializado.
* `URI` (Uniform Resource Identifier): Identificador global para sujetos, predicados y vocabularios (ej. `cortex:concept:entropy`, `urn:uuid:...`).
* `TrustValue`: Un array de bytes opaco (`Vec<u8>` o `byte[]`). El Kernel **jamás** deserializa este campo.

------------------------------
## 3. Epistemic Definition Language (EDL)

El EDL es un subconjunto restringido, fuertemente tipado y sin ciclos, diseñado para estructurar las afirmaciones semánticas (`Assertion`) y restricciones (`Constraint`).

### 3.1 Estructura del Sujeto y Predicado
Cada aserción se descompone en un triplete o cuádruple semántico que debe resolverse siempre mediante URIs.

```edl
<Assertion> ::= 
  subject: <URI>
  predicate: <URI>
  object: <URI> | <Literal>
  context: <URI>
```

### 3.2 Literales Estrictos
Para evitar la entropía de formatos (ej: fechas en distintos strings, floats impredecibles), se restringen los literales del EDL:
* `Literal.Int64`: Enteros de 64 bits con signo.
* `Literal.Decimal128`: Alta precisión, evitando la deriva de punto flotante de `f64`.
* `Literal.String`: UTF-8 canónico (NFC normalizado).
* `Literal.Boolean`: `true` | `false`.

------------------------------
## 4. Serialización Canónica (C-JSON / Protobuf)

Para garantizar que el cálculo de `Hash(Object)` sea determinista independientemente de la máquina que lo instancie, todos los `EpistemicObjects` deben pasar por un proceso de serialización canónica antes del hashing.

### 4.1 Algoritmo de Hashing de Objetos
1. **Extracción de Propiedades**: Se ignoran campos efímeros (memoria local) y metadatos no estructurales.
2. **Normalización UTF-8**: Todo string se normaliza bajo NFC.
3. **Ordenamiento Lexicográfico**: Las claves de los diccionarios o structs se ordenan de la A a la Z.
4. **Serialización**: Se convierte a JSON Canónico (RFC 8785) o a formato binario determinista (Protocol Buffers v3 con campos ordenados por tag).
5. **Digestión**: Se aplica `SHA3-256(serialized_bytes)`.

```rust
// Ejemplo referencial en pseudocódigo Rust (Bootstrapping MVP)
fn compute_hash(obj: &EpistemicObject) -> Hash {
    let canonical_bytes = rfc8785::to_vec(&obj.to_structural_map());
    sha3_256(&canonical_bytes)
}
```

------------------------------
## 5. Criterios de Aceptación para MVP

Para que el Tipo de Sistema de BABYLON-60 se considere validado, el MVP (Bootstrapping MVP propuesto) debe demostrar empíricamente:
1. **Determinismo**: Múltiples ejecuciones del mismo objeto en distintas máquinas y tiempos producen idéntico SHA3-256.
2. **Rechazo de Entropía**: Intentar instanciar una `Assertion` con un `float` puro o un string sin normalizar debe ser capturado en tiempo de compilación o fallar inmediatamente en el parser.
3. **Transparencia BFT (Byzantine Fault Tolerance)**: Si un actor malicioso altera un byte en la descripción de un Literal, el ID/Hash resultante muta por avalancha criptográfica, invalidando cualquier `SupportRelation` que apuntase al objeto original.
