---
title: Invariantes del Dominio C5-REAL BABYLON-60
status: Requisitos-con-verificacion-delimitada
version: 4.5.0
---

# Invariantes del dominio: requisitos y alcance de evidencia

Revisión científica: 2026-10-26. Se retira el sello genérico «Verified» y la afirmación de que todo este catálogo está formalmente verificado por el kernel. Un invariante propuesto es una obligación del diseño: su nombre no demuestra implementación, instrumentación ni efecto de `CRITICAL_HALT`. La ausencia de evidencia deja la garantía NO_VERIFICADA, sin afirmar que sea falsa.

Los identificadores OBSOLETO se conservan para rastrear documentos antiguos. No sustituyen [.babylon60rules](../../.babylon60rules), [AGENTS.md](../../AGENTS.md) ni los [contratos técnicos vigentes](../03_guides/agent_contracts.md). Se mantienen los requisitos de rechazo y seguridad aplicables; no se atribuye su cumplimiento universal a esta especificación.

## 1. Inventario de requisitos del dominio

Cada requisito necesita identificar implementación, dominio de entradas, condiciones de fallo y evidencia reproducible antes de presentarse como garantía. La [auditoría de alcance Lean](../06_theory/AUDIT_LEAN_SCOPE_2026.md) distingue las pruebas del modelo de las propiedades físicas y de Rust.

### 1.1 `[OBSOLETO: INV_BFT_04]`: Non-Silent Collision Fail-Fast

**Propósito:** evitar aceptación silenciosa de inconsistencias causales o temporales.

**Requisito:** rechazar mutaciones con referencias a padres inválidas, reloj lógico incompatible o conflicto de identidad, y propagar un error según el contrato del componente. Conservar la prohibición de sustituir esa validación por espera o fusión silenciosa. No se prescribe aquí un `panic!` universal ni se afirma que todo rechazo cueste O(1): hay que contar lectura, hashing, búsqueda y persistencia sobre un tamaño de entrada definido.

**Límite:** un reloj lógico ordena eventos según reglas; no constituye por sí solo una prueba criptográfica de su ocurrencia. Una colisión real de hash produce el mismo digest y no puede detectarse comparando únicamente ese digest. Un detector necesita información independiente pertinente. La ruta heredada SQLiteCommitter, la cobertura de estas comprobaciones y el efecto terminal quedan NO_VERIFICADOS por este catálogo.

### 1.2 `[OBSOLETO: INV_C5_15]`: Raw 32-Byte OP_RETURN Payload Encoding

**Propósito:** especificar la representación binaria de un compromiso en el roadmap de Bitcoin L1.

**Representación propuesta:** para un compromiso de 32 bytes, `6a20<root>` ocupa 34 bytes de script: opcode OP_RETURN, push de longitud 32 y los bytes del compromiso. Esos 34 bytes no son el tamaño de toda la salida ni de la transacción. La identidad del algoritmo no se deduce de la longitud.

**Evidencia acotada:** [l1_sink_bitcoin.py](../../scripts/c5_l1_ledger/l1_sink_bitcoin.py) calcula SHA-256 sobre datos de ejemplo y genera una transacción dummy en dry-run. Esto no verifica inclusión en Bitcoin, aceptación de la transacción ni alimentación desde el ledger real. El SHA-256 legado discrepa del perfil BLAKE3 para datos/Merkle/IPC exigido por el contrato vigente; una migración requiere versión y comprobación de consumidores. No se cambia ese formato mediante esta rectificación documental.

### 1.3 `[OBSOLETO: INV_C5_17]`: Sovereign Dual-Licensing Invariant

**Propósito histórico:** conservar atribución y trazabilidad de licencia en distribución.

**Requisito:** usar la licencia y cabeceras efectivamente aplicables del repositorio, y comprobar su inclusión donde proceda. Una cabecera o una firma no impide copias, no garantiza trazabilidad de toda reutilización ni constituye evaluación jurídica. No se certifica aquí cumplimiento ni se crea un régimen de licencia distinto del vigente.

### 1.4 `[OBSOLETO: INV_C5_18]`: Zero-Worktree Swarm Scaling

**Propósito histórico:** reducir escrituras y contención durante ejecución de agentes.

**Estatus:** objetivo de diseño, sin medición de escalado o contención aportada aquí. Ejecutar tareas en memoria no elimina interferencias, carreras, recursos compartidos o agotamiento de memoria. La prohibición histórica universal de worktrees no prevalece sobre el flujo autorizado de aislamiento de tareas y preservación de cambios del proyecto. La elección debe respetar las instrucciones vigentes y verificarse en el componente afectado.

### 1.5 `[OBSOLETO: INV_C5_28]`: 1-WL Graph Isomorphism Pre-Filter

**Propósito:** descartar algunos pares antes de una comprobación exacta, conservando la obligación de validar correctamente los pares aceptados.

**Requisito:** si se usa 1-WL como filtro de rechazo, sus firmas deben ser invariantes bajo la relación de isomorfismo del dominio. Firmas iguales no demuestran isomorfismo; deben conducir al comprobador exacto, no a una aceptación por secuencia de grados. Comparar digests fijos precomputados cuesta O(1) respecto al tamaño del grafo; construirlos no. Rondas, ordenaciones, etiquetas y bytes procesados forman parte del coste.

**Evidencia:** la [especificación de grafos](spec_graph_canonical.md#3-algoritmo-1-wl-filtro-de-refinamiento-de-colores) registra el falso positivo y la dependencia de orden originales, ahora corregidos con búsqueda exacta y actualización simultánea. Se mantienen separados los perfiles dirigido/no dirigido y los errores por agotamiento de presupuesto. Las regresiones finitas no certifican un coste asintótico ni una implementación de VF2. Se distinguen isomorfismo de grafos completos e isomorfismo de subgrafos. [Arvind et al.](https://arxiv.org/abs/1502.01255) explican los límites de color refinement y [Berkholz et al.](https://arxiv.org/abs/1509.08251) analizan un algoritmo específico de refinamiento canónico.

### 1.6 `INV_C5_SEMANTIC_ENTROPY_DUAL_FIREWALL`: Zero-Float Dual-Firewall Invariant

**Requisito de diseño:** la implementación que adopte el perfil acotado N ≤ 8 debe respetar las restricciones de representación, aritmética y rechazo del [contrato de firewall](spec_semantic_entropy_dual_firewall.md). La convergencia de respuestas de un modelo no es evidencia factual suficiente.

**Límite científico:** la entropía semántica es una medida de dispersión de respuestas agrupadas por significado bajo un método definido; no es calor ni una prueba general de confabulación. Una respuesta falsa puede ser estable y una consulta ambigua puede producir diversidad válida. SAT verifica satisfacibilidad de la fórmula codificada bajo sus hipótesis, no verdad de todas las afirmaciones del mundo. Tampoco un código de estado demuestra que la operación productiva haya sido bloqueada. La corrección formal y correspondencia de la aritmética Q16, agrupación, SMT, estado y efecto necesitan evidencia separada. No se declara aquí ese circuito completamente verificado.

**Reparación acotada:** el núcleo valida tamaño, bits de dominio y equivalencia antes de calcular; los errores se propagan mediante `Result`/`InvalidInput`. La API tipada distingue SAT, UNSAT, UNKNOWN y error: solo SAT permite una variante positiva; UNKNOWN/error se rechazan por separado, con precedencia de entrada inválida. El adaptador host ejecuta Z3 y exige correspondencia entre recibo y consulta esperada antes de clasificar. Las regresiones, el modelo Lean de resúmenes y sus límites se registran en la [auditoría actualizada](AUDIT_SCIENTIFIC_GUARANTEES_2026.md#7-adaptador-real-y-vinculación-de-consultas--2026-10-26). La vinculación local no autentica el binario ni certifica el circuito productivo o la verdad factual.

## 2. Invariantes de la máquina abstracta

Las siguientes son propiedades propuestas de la semántica F60. Para llamarlas teoremas se requieren definiciones del estado y las transiciones, hipótesis, prueba de preservación y, por separado, correspondencia con el programa real.

- **I1 (Unicidad operacional):** como máximo una instrucción de una corrutina por `UNIT.TICK` en el modelo. No certifica un scheduler físico ni su coste.
- **I2 (Identidad y procedencia):** cada mutación debe tener una identidad y autenticación verificable según el protocolo. Una firma no es por definición un ID único, no impide replay sin estado adicional y no prueba verdad del payload.
- **I3 (Inmutabilidad del pasado):** la transición abstracta debe ser append-only. Resistencia a modificaciones del almacenamiento y recuperación requieren mecanismos y evidencia adicionales; un DAG o hash no bloquea escrituras por sí solo.
- **I4 (Monotonía temporal):** `C.now() ≤ C.next()` expresa no decrecimiento. No demuestra avance estricto, terminación ni frescura; si se exige progreso, debe formularse y comprobarse una condición adicional.
- **I5 (Trazabilidad de mutaciones):** las mutaciones deben disponer de la evidencia que exija el contrato de estado y ledger. Trazabilidad y reversibilidad computacional son propiedades distintas. Ninguna equivale a ausencia de disipación física o de gasto de recursos.
