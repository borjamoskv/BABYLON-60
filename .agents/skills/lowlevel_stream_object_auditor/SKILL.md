<!-- C5-REAL EXERGY CERTIFIED -->
---
name: lowlevel_stream_object_auditor
description: Skill especializado en descompresión aislada de streams y topología algebraica discreta de objetos. Valida invariantes estructurales bajo el Invariante Causal-Ontológico C5-REAL.
---

# Low-Level Stream & Object Auditor Skill

Este Skill dota al agente de los axiomas operacionales para descomprimir flujos de datos (*streams*) y auditar la topología algebraica de objetos binarios anidados (PDF, contenedores ASN.1, TIFF). Se ejecuta bajo estricta **Contención Epistémica**: todo *stream* entrante permanece en estado de pura potencia estocástica (*Dynamis*) hasta que el *Primum Movens* certifique su estructura discreta, rechazando el parseo probabilístico y evitando la activación de recolectores de basura o heurísticas de renderizado.

## 1. Fundamentos Termodinámicos (Descompresión y Límite de Landauer)
El procesamiento de un *stream* comprimido exige disipación térmica. El agente debe tratar la descompresión (ej. `FlateDecode`, `LZWDecode`) bajo el límite de Landauer (ΔQ ≥ k_B · T · ln(2) · ΔI).
- **Control de Anergía**: La descompresión se restringe estrictamente a *buffers* crudos pre-asignados (Zero-Disk I/O).
- **Rechazo Atómico de Zip Bombs**: Cualquier desbordamiento asimétrico del ratio de compresión se identifica como inyección deliberada de anergía y desencadena un *Fail-Stop* inmediato.

## 2. Topología Algebraica Discreta (Bisimulación Observacional)
El flujo de objetos se modela como un **Sistema de Transiciones Discreto**. Las variedades continuas están estrictamente prohibidas.
- Se impone un isomorfismo estricto sobre el grafo dirigido de objetos (`N M obj ... endobj`).
- Cualquier discrepancia entre la longitud declarada (`/Length`) y el tamaño material del buffer rompe la bisimulación observacional, provocando el colapso inmediato a Cuarentena Epistémica.
- **Prohibición de Ciclos**: La validación exige la ausencia formal de referencias cíclicas, obligando al contenedor a operar como un DAG (Directed Acyclic Graph) canónico.

## 3. Contención Causal de Indecidibilidad (Teorema de Rice)
Frente a diccionarios que declaran ejecución dinámica, el sistema asume incomputabilidad incondicional.
- Aplicando heurísticas de *Minimum Description Length (MDL)*, los objetos con estado activo o mutabilidad latente (`/JavaScript`, `/Launch`, `/SubmitForm`, `/OpenAction`) son rechazados en origen.
- **No se interpreta, se disipa**: Se prohíbe el uso de sandboxes de evaluación JS en Ring-0. La simple presencia del atributo es causal matemática de *Epistemic Halt*.

## 4. Purga No Estándar y Disipación de Overlay
Se auditan manipulaciones topológicas inyectadas fuera de las fronteras declaradas o mediante homóglifos.
- **Truncado de Anergía Post-EOF**: Todo bloque de bytes residual (`trailing_bytes`) que no mapee a un estado finito indexado se disipa sin análisis, devolviendo el contenedor a su estado canónico discreto (st: *R → R).
- **Homóglifos Topológicos**: Las secuencias de ancho cero (`U+200B`) inyectadas dentro de claves estructurales (ej. `/Auth​or`) se interceptan y neutralizan como canales paralelos de exfiltración.

## 5. Arquitectura de Ejecución FFI (C-ABI & Lock-Free EBR)
La validación no bloqueante se delega al Kernel Ring-0 (Rust), garantizando la latencia estricta T_eff < 5 ms.
- **Memoria Alineada**: Los manifiestos de estado se intercambian mediante estructuras empaquetadas `#[repr(C, align(64))]` (o 128 bytes en Apple Silicon) para evadir la contención por *False Sharing* y asegurar la coherencia *Zero-Split Cache-Line*.
- **Transición al Acto (*Entelecheia*)**: Tras la validación determinista del álgebra CF-GKAT, el objeto purgado abandona la cuarentena. El Kernel ejecuta un `CAS` atómico de 64 bits, conmutando el puntero y emitiendo el recibo SCITT (Merkle SHA3-256) que soporta matemáticamente el Cap Contractual de Responsabilidad.
