---
title: Especificación de Serialización Canónica de Grafos
status: Formato-legado-y-comprobadores-con-regresiones-acotadas
version: 4.5.0
---

# BABYLON-60: serialización de grafos y filtro 1-WL

Revisión científica y reparación: 2026-10-26. Se mantiene retirado el sello genérico «Verified». El comprobador del demo usa ahora una búsqueda exacta tras el filtro 1-WL; el otro método inspeccionado usa una ronda simultánea. Una serialización ordenada o un hash por sí solos siguen sin certificar isomorfismo, procedencia ni ejecución física. Los identificadores OBSOLETO son trazabilidad, no normas superiores a [.babylon60rules](../../.babylon60rules).

## 1. Objetivo y principio de canonicidad

Para los mismos campos normalizados, un codificador determinista puede producir los mismos bytes con independencia del orden de inserción. Eso requiere fijar dominio de datos, codificación, escapes, orden, algoritmo y versión. Ordenar líneas que contienen IDs no da por sí solo una forma canónica independiente de renombrados de vértices.

Una canonización estructural completa exigiría demostrar, para la relación de isomorfismo elegida, `C(G) = C(H) ↔ G ≅ H`. El esquema y el filtro de esta página no prueban esa equivalencia. El tipo de grafo —dirigido, con etiquetas, multiaristas o AST con orden de hijos— debe formar parte del contrato; cambiarlo puede cambiar la respuesta correcta.

## 2. Formato de serialización pipe-delimited

El perfil textual legado propone una línea por nodo de DAGLedger:

$$\text{LineaFormat} := \text{ID} \mid \text{PARENTS} \mid \text{TICK} \mid \text{PAYLOAD} \mid \text{AUTH}$$

```text
EV_0||0|R0=60|SIG_OK
EV_1|EV_0|1|R1+=120|SIG_OK
EV_2|EV_0,EV_1|2|AWAIT(SIG_SYNC)|SIG_OK
```

`SIG_OK` es un marcador de ejemplo, no una firma verificable. El campo antes denominado SIGNATURE no especificaba una representación autenticada; un digest y un HMAC tampoco son intercambiables con una firma pública.

### 2.1 Campos estrictos

1. **ID:** identificador del nodo, único dentro del artefacto; validación de duplicados pendiente de la implementación que adopte el perfil.
2. **PARENTS:** IDs de predecesores inmediatos separados por comas; vacío en una raíz y ordenado según la codificación elegida. Deben validarse referencias y semántica de aristas.
3. **TICK:** entero del reloj lógico; dominio, monotonía exigida y tratamiento de overflow deben especificarse y comprobarse.
4. **PAYLOAD:** representación versionada del opcode o mutación; la intención de determinismo no sustituye definir su encoder.
5. **AUTH:** representación autenticada con algoritmo, clave, dominio y bytes firmados definidos por el perfil aplicable.

El borrador no define escapes de `|`, coma, retorno de carro o salto de línea dentro de campos, ni normalización Unicode. No se presenta como codec completo e inyectivo para entradas arbitrarias. Una implementación conforme debe fijar esas reglas o rechazar esos datos antes de aceptar el artefacto; esta revisión no cambia un formato de producción.

### 2.2 Invariante de ordenamiento lexicográfico

Los requisitos conservados del perfil son ordenar los padres y las líneas completas por una regla de bytes explícita, codificar en UTF-8 sin BOM y terminar cada línea, incluida la última, con `\n`. Para campos ASCII el orden coincide con ASCII. No se debe atribuir normalización Unicode a una mera ordenación.

Ordenar las líneas no establece un orden causal, valida firmas ni autentica el origen. La conformidad de un encoder concreto requiere casos golden y roundtrips sobre su dominio, además de comprobar entradas inválidas y versiones. Esta página no aporta una prueba de equivalencia con todos los emisores del repositorio.

## 3. Algoritmo 1-WL: filtro de refinamiento de colores

El propósito de [INV_C5_28 legado](spec_invariants.md) es filtrar candidatos antes de una comprobación exacta. 1-WL distingue algunos pares no isomorfos, pero no todos; la igualdad de sus firmas deja el resultado **INDETERMINADO**. [Arvind, Köbler, Rattan y Verbitsky](https://arxiv.org/abs/1502.01255) estudian precisamente los límites y clases de grafos distinguibles por este método.

### 3.1 Formulación matemática de actualización de color

Para un grafo dirigido y un esquema fijo de etiquetas, una ronda simultánea puede describirse como:

$$c^{(k+1)}(v)=\operatorname{EncColor}\!\left(c^{(k)}(v),\;\{\!\{(\ell_{uv},c^{(k)}(u)):u\to v\}\!\},\;\{\!\{(\ell_{vu},c^{(k)}(u)):v\to u\}\!\}\right).$$

Los dos multiconjuntos separan entradas y salidas; las etiquetas de arista se omiten solo si el dominio no las tiene. `EncColor` representa una codificación no ambigua e inyectiva en el modelo matemático. Un hash de anchura fija es una implementación con posibilidad de colisión, no una función inyectiva sobre todas las entradas. Ambos grafos comparados necesitan el mismo esquema, parámetros, etiquetas iniciales y codificación.

### 3.2 Rondas, estabilidad y coste

El pseudocódigo anterior se retira como especificación formal: comparar `set(new_colors.values())` con `set(colors.values())` no comprueba estabilidad de la partición. Los nombres hash pueden cambiar aunque las clases no se dividan, y un conjunto pierde multiplicidades. Diez rondas son una cota elegida de ejecución, no una prueba de estabilización ni de canonización completa. Las actualizaciones deben usar exclusivamente los colores de la ronda previa; actualizarlos in-place puede introducir dependencia del orden de recorrido.

Con `n = |V|`, `m = |E|`, `r` rondas y colores de anchura fija, un esquema que ordena listas de vecinos por comparación tiene un coste que incluye

$$O\!\left(B+r\left(n+m+\sum_v d(v)\log\max(2,d(v))\right)+n\log\max(2,n)\right),$$

donde `B` incluye los bytes iniciales procesados y `d(v)` cuenta las incidencias usadas. Deben añadirse los costes de etiquetas y codificaciones variables. Es un análisis del esquema, no un benchmark ni una cota probada del código concreto. Existe un algoritmo específico de refinamiento estable canónico en [O((n+m) log n), Berkholz, Bonsma y Grohe](https://arxiv.org/abs/1509.08251); ese resultado no convierte cualquier pseudocódigo de hashing en un algoritmo lineal ni canoniza completamente el grafo.

### 3.3 Política de activación de VF2 y evidencia local

La comparación de dos digests ya calculados, con longitud fija, es O(1) respecto al tamaño del grafo. Construirlos, validar sus entradas y ejecutar el comprobador exacto son costes adicionales. Bajo una implementación que preserve el isomorfismo para el dominio elegido, firmas distintas permiten descartar ese par; firmas iguales requieren una comprobación exacta de aristas, dirección y etiquetas. La igualdad de grados tampoco cierra esa comprobación. No se confunden isomorfismo de grafos completos e isomorfismo de subgrafos como si fueran el mismo problema.

La versión inicial de la [PoC local](../../scripts/c5_demos/poc_graph_isomorphism_wl.py) aceptaba solo por firma WL y grados. Se reprodujo un falso positivo sobre dos DAG de ocho nodos y ocho aristas: uno tiene una componente débil y el otro dos. La versión reparada los rechaza mediante búsqueda exacta, también para un prisma triangular y K₃,₃ conectados y regulares cuyas firmas WL coinciden. Se conserva el contraejemplo histórico en el registro anterior; no se convierte la igualdad WL en criterio suficiente.

El método inicial `compute_1wl_hash` de [c5_ultimate_causal_determinant.py](../../scripts/c5_isomorphisms/c5_ultimate_causal_determinant.py) cambiaba su digest al reordenar los nodos de un camino de tres vértices. Ahora calcula todos los colores nuevos desde los anteriores, conserva multiplicidades y valida nodos/referencias. Las seis permutaciones del camino producen el mismo digest. Sigue siendo un filtro incompleto de un multigrafo no dirigido, distinto del dominio dirigido del primer demo.

### 3.4 Contrato reparado y compatibilidad

`verify_isomorphism` trata diccionarios de adyacencia como multigrafos dirigidos sin etiquetas semánticas: los IDs son nombres, las repeticiones son aristas paralelas y se admiten bucles. Valida ambas entradas antes de descartar por tamaño o colores. Un resultado `True` exige una biyección que preserve dirección, multiplicidad y bucles. La búsqueda es backtracking iterativo, no una implementación de VF2 ni un algoritmo de coste lineal.

El parámetro keyword-only `max_search_states` limita extensiones candidatas (100000 por defecto). Agotarlo lanza `IsomorphismSearchLimitExceeded`; no devuelve `False` como si hubiera probado no isomorfismo. Entradas o límites inválidos producen `ValueError`. Ese presupuesto no acota tiempo, preprocesamiento ni memoria de candidatos O(n²).

Los tokens del hash usan longitudes explícitas para evitar concatenaciones ambiguas. El perfil dirigido devuelve `WL1_V2:<hex>` e incluye las rondas efectivas, acotadas a diez. El perfil no dirigido usa dominio `b60-wl-undirected-v2` y conserva una salida de 64 hexadecimales; su longitud no identifica la versión. Solo se comparan digests del mismo perfil y parámetros. El demo que persiste `wl_color_hash` debe conservar la versión correspondiente; no se reinterpretan ni migran compromisos antiguos en esta reparación.

Las [regresiones](../../tests/test_graph_isomorphism_regressions.py) contrastan 2080 pares del corpus completo de 64 grafos dirigidos simples de tres nodos, y 105 pares de un corpus de 14 multigrafos de cuatro nodos, con un oráculo independiente que enumera biyecciones. Incluyen dirección, multiplicidad, bucles, renombrados, inputs inválidos y agotamiento de búsqueda. Se sustituye además un test de un stub local por llamadas a la API real. Estos dominios finitos y la revisión del algoritmo no equivalen a una prueba Lean de isomorfismo universal. [Evidencia](evidence/algorithm-repairs-20261026.json).

## 4. Digest del archivo y raíz Merkle

La fórmula histórica

$$\text{graph\_hash}_{\rm legado}=\operatorname{SHA256}(\text{line}_1\parallel\cdots\parallel\text{line}_N)$$

define un digest plano de los bytes, no una raíz de árbol Merkle con hojas, nodos internos y pruebas de inclusión. La distinción está explícita en la [definición recursiva de RFC 9162, §2.1.1](https://www.rfc-editor.org/rfc/rfc9162.html#section-2.1.1). No se atribuyen pruebas de inclusión o consistencia al digest plano.

SHA-256 en esta fórmula y en la PoC Bitcoin es un perfil legado observado; el [contrato vigente](../03_guides/agent_contracts.md#ring-0) exige BLAKE3 para datos/Merkle/IPC y reserva SHA-256 al pre-hash de atestación P-256. La discrepancia requiere una migración versionada y verificación de consumidores; esta revisión documental no cambia bytes ni declara conformidad del legado.

El [script de Bitcoin citado](../../scripts/c5_l1_ledger/l1_sink_bitcoin.py) calcula SHA-256 de un estado de ejemplo y genera una transacción dummy en dry-run; no acredita que reciba este archivo, publique una transacción válida ni ancle una raíz de producción. Su presencia no certifica cadena de custodia o autenticidad.
