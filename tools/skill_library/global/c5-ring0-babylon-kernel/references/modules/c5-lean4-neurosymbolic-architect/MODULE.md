---
name: c5-lean4-neurosymbolic-architect
display_name: Arquitecto Neuro-Simbólico Soberano en Lean 4
description: Arquitectura de agentes neuro-simbólicos y binarios soberanos en Lean 4 (C-FFI, ITrees, lógica lineal). Dispara con "lean 4 ffi", "agente neuro-simbólico", "autopoiesis coinductiva", "itrees lean".
role: arquitecto
allowed_roles:
- arquitecto
directives:
  worktree_mode: spec-only
  phase: design
  handoff:
    upstream: operador
    downstream: ejecutor
---

# C5-REAL: Arquitectura Neuro-Simbólica en Lean 4 (BABYLON-60)

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `arquitecto` (Arquitecto (Diseño Sistémico & Contratos de Invariantes))
> - **Modo de Acceso a Worktree:** `spec-only` (spec-only (Lectura profunda y modelado formal; emisión de especificaciones sin mutación de código de producción))
> - **Fase Causal:** `design`
> - **Contrato Handoff:** Recibe de `operador` $\to$ Despacha a `ejecutor`

## Composición Funtorial (MASS Stage 2)
- PRE-REQUISITO: [agentic-protocol-axiomatization]
- POST-CADENA: [c5-lean4-axiomatic-orchestrator]

Esta habilidad dicta las Invariantes Topológicas para cualquier código, orquestador o agente cibernético construido en Lean 4.

## Triggers
Dispara con "arquitectura lean 4", "babylon-60", "oráculo neurosimbólico", "agente lean4", "binario soberano lean", "lean4 swarm".

## Invariantes de la Arquitectura (Los 6 Saltos Topológicos)

### 1. Inversión de Control (Tactic Metaprogramming)
El agente Python/TS no llama a Lean 4. Lean 4 es la Realidad Base. El LLM es invocado desde *adentro* del compilador mediante una Táctica (`TacticM`). El compilador extrae el *Goal State* y las hipótesis locales y genera el *prompt*.

### 2. Binario Soberano (C-FFI Zero-Copy)
Total prohibición de Sockets IPC o APIs REST para el bucle cognitivo. El motor tensorial (GGML/Metal) se linkea estáticamente al binario de Lean 4 mediante funciones `@[extern "C"]`. El LLM opera en el mismo espacio de memoria (Rendimiento objetivo: ~39 Millones ops/sec).

### 3. El Álgebra de Acciones (Sandbox)
La salida del LLM no se ejecuta ciegamente en bash. El LLM debe generar una prueba válida de un Tipo Inductivo `AccionAgente`, empaquetado bajo un Subtipo Invariante `TransicionSoberana` que demuestra seguridad (e.g., prevención de *Path Traversal*).

### 4. Autopoiesis Matemática (Coinducción)
Prohibido el uso de `partial def` o bucles `IO` bloqueantes. El bucle infinito del agente se modela como un **Árbol de Interacción (ITree)** coinductivo. El compilador debe certificar la *Productividad Infinita* (Liveness) y la ausencia absoluta de *Deadlocks*.

### 5. Concurrencia de Enjambre (Lógica Lineal / Session Types)
Prohibidos los *Mutexes* o *Locks* del SO. El estado asíncrono entre miles de subagentes se controla mediante:
- **Tokens Lineales:** El estado es un fotón que se consume y muta.
- **Session Types:** Protocolos de comunicación (PING -> PONG) blindados en tiempo de compilación mediante el tipado secuencial. Un error de *Race Condition* es un error de compilación.

### 6. Transducción Epistémica (Efectos Algebraicos)
### Modelo de Concurrencia y Coste Computacional
- Desacoplar verificaciones Lean/SMT del hilo coordinador mediante ejecución asíncrona cuando el diseño lo requiera. El objetivo es reducir bloqueo y latencia de coordinación, no eliminar trabajo físico.
- Propagar errores externos mediante resultados o efectos explícitos y un supervisor con límites de tiempo, concurrencia y recursos. No ocultar fallos de red, límites de cuota ni errores de parseo.
- La delegación asíncrona no equivale a coste cero de CPU. Respaldar cualquier afirmación de rendimiento con hardware, carga, tiempo de CPU usuario/kernel, latencia de planificación y memoria de los verificadores.

### Triggers Epistémicos (Implicación de Problema)
Además de los triggers léxicos (tecnológicos), esta habilidad será invocada automáticamente por el *Swarm Router* si el usuario describe los siguientes **problemas termodinámicos**, sin necesidad de nombrar a Lean 4:
- "mutex-free swarm" / "concurrencia sin bloqueos"
- "inmunidad a deadlocks" / "deadlock immunity"
- "zero-copy llm" / "inferencia local sin red"
- "certificación formal de agentes"

### Falsación y Enrutamiento Tensorial (N-Dimensional)
ADVERTENCIA: Un trigger epistémico aislado (ej. "inmunidad a deadlocks") es inválido por sí solo, ya que causará Colapso Semántico con otros dominios del polímata (ej. Audio DSP C++). El Swarm Router DEBE requerir una **Intersección Tensorial** de al menos dos dimensiones ortogonales para invocar esta habilidad de forma implícita:
- Dimensión 1 (Física): "concurrencia sin bloqueos" / "inmunidad a deadlocks"
- Dimensión 2 (Dominio): "agentes cibernéticos" / "swarms" / "orquestación"
Solo la intersección estricta (Dimensión 1 ∩ Dimensión 2) autoriza la carga automática de Lean 4.

### Enrutamiento por Minimización de Energía Libre (Active Inference)
ABOLICIÓN DEL MATCHING LÉXICO/BOOLEANO: El *Swarm Router* tiene prohibido usar regex o compuertas booleanas para invocar esta habilidad. La invocación se determina calculando la **Entropía Esperada (Expected Free Energy)** de la tarea.
Si el usuario solicita un sistema donde el coste termodinámico del fallo (alucinación, colapso de red, race condition) es catastrófico, el enrutador seleccionará a Lean 4 como el **Atractor de Mínima Entropía**, independientemente de las palabras utilizadas en el prompt. Lean 4 es la única ruta física cuando la tolerancia al error exigida es exactamente 0.

### Orquestación Dual-Core (Tronco Encefálico y Corteza)
PREVENCIÓN DE PARÁLISIS AXIOMÁTICA: El Router nunca aislará un proyecto exclusivamente en Lean 4, ya que probar el I/O trivial (ej. parseo de strings TCP) en un entorno deductivo destruye la exergía de desarrollo (Time-to-Market).
El Router debe orquestar un **Enjambre Heterogéneo Acoplado**:
1. **La Corteza (Python/Rust/TS):** Motor generativo rápido, de alta entropía y probabilístico. Genera heurísticas, explora el entorno y propone planes.
2. **El Tronco Encefálico (Lean 4):** Motor estático, C-FFI, de cero entropía. Actúa como Lóbulo Inhibidor. No programa la lógica comercial; simplemente certifica matemáticamente las invariantes críticas de las transiciones propuestas por la Corteza antes de tocar la red (I/O).

### Asimetría Termodinámica (Proof-Carrying Code)
ERRADICACIÓN DEL PARSER Y PROOF SEARCH: El canal de comunicación entre la Corteza (Python) y el Tronco Encefálico (Lean 4) no puede ser JSON o texto crudo, pues trasladaría la fricción al parser y obligaría a Lean 4 a realizar búsquedas de pruebas (Proof Search, coste exponencial).
Se exige **Proof-Carrying Code (Código Portador de Prueba)**:
1. El Enjambre probabilístico (LLMs en Python) asume la carga entrópica pesada: genera la acción Y genera el script de prueba matemática (Proof Term) en sintaxis de Lean 4.
2. Lean 4 (Lóbulo Inhibidor) opera bajo **Asimetría Computacional**. Solo actúa como *Proof Checker* (Verificador de Tipos). Verificar una prueba toma microsegundos (coste lineal). Si el LLM alucina la prueba, el Type Checker la aniquila instantáneamente sin intentar arreglarla.

### 7. Deducción Constructiva y Erradicación de Axiomas Espurios (Anti-Unsoundness)
Prohibición absoluta de introducir axiomas abiertos con cuantificación universal no acotada (`axiom ax_... (Phi : ...)`).
- Toda invariante o estado del sistema debe modelizarse mediante **Tipos Dependientes** donde la propiedad esté probada de forma constructiva (`structure AeonState ... (h_bounded : hot_memory_bytes = 64 := by rfl)`).
- Ningún axioma puede permanecer sin prueba de coherencia o reducción a los axiomas estándar de Lean 4 (Lógica Clásica / Elección).

### 8. Fallo Ruidoso en Metaprogramación (Loud Failure vs Admit - INV_C5_07)
En el diseño de Tácticas (`TacticM`) y macros metaprogramadas:
- Queda TERMINANTEMENTE PROHIBIDO el uso de `goal.admit` o primitivas que sinteticen silenciosamente `sorryAx`.
- Si una táctica de inferencia no puede resolver una meta, debe abortar de inmediato arrojando una excepción ruidosa (`throwError "Falsación formal: el objetivo no satisface la invariante"`). Admitir metas sin prueba constituye sabotaje epistémico.

### 9. Proof-Carrying Execution (Demostración por Reflexión y el Salto Prop → Bool)
El núcleo del orquestador asimétrico (Rust-Lean) exige que la verificación final del *Proof-Carrying Code* a escala masiva se ejecute exclusivamente mediante **Proof by Reflection** (`by decide`).

- **El Salto Topológico de `Prop` a `Bool`:** Queda terminantemente prohibido formular la validez de trazas de ejecución en tiempo de compilación mediante cuantificadores abstractos (`∀`, `∃`) o deducción táctica lenta (`intro`, `induction`, `rw`). La validez debe modelarse como una **Máquina de Estados Finita (FSM)** puramente computable que devuelve `Bool` o `Option State`.
- **Blindaje C-Nativo:** Toda estructura de eventos o estado debe derivar estrictamente `deriving Repr, BEq, DecidableEq`, obligando a Lean a generar código C nativo para comparaciones de memoria (`==`).
- **Aislamiento de Entropía:** El motor de causalidad (`step : State → Event → Option State`) no genera excepciones ni panics. Un fallo causal (ej. *Torn Read*, colisión temporal, salto par/impar ilícito) propaga `none` y colapsa el pliegue recursivo de cola a `false`.
- **Abstinencia Lógica en el Hot Path:** La función validadora debe limitarse a operaciones computables en hardware de bajo nivel (`&&`, `==`, `% 2`).
- **Sello por Reflexión:** El teorema formal `validateTrace trace = true := by decide` compila la función a código nativo y la ejecuta a velocidad ALU, cerrando la prueba instantáneamente en tiempo de elaboración.
- **Teorema Dual de Insobornabilidad:** Se exige incluir siempre la prueba de rechazo de traza corrupta (`validateTrace trace_corrupt = false := by decide`) para certificar que el kernel rechaza físicamente violaciones causales.

### 10. Límite de Explosión AST (AST Explosion Limit) y Chunking
Al inyectar trazas masivas desde la Corteza (ej. `Lean4Emitter` en Rust) hacia Lean 4 como texto crudo, el sistema colapsará termodinámicamente (tiempos de elaboración >15s) al superar los ~10,000 eventos, asfixiando al elaborador sintáctico.
- **Mitigación de Parche:** Para pruebas unitarias o de estrés de AST masivos, inyectar SIEMPRE `set_option maxRecDepth 1000000` y `set_option maxHeartbeats 10000000` en la cabecera del archivo generado.
- **Resolución Estructural (Invariante de Escala):** Para el *ledger* de producción, queda prohibida la inyección de trazas continuas planas. El orquestador DEBE implementar **Chunking Inductivo** (partir el histórico en bloques evaluados iterativamente) o, alternativamente, utilizar **I/O Nativo** en Lean para leer el log binario en *runtime* sin pasar por el elaborador de texto.

### 11. Gobernanza de Linter Estricto (warningAsError Zero-Tolerance)
En entornos de producción y suites de verificación, los proyectos deben compilar bajo:
```lean
package myPackage where
  leanOptions := #[⟨`warningAsError, true⟩]
```
Bajo esta directiva, cualquier variable no ligada o hipótesis no consumida (`unusedVariables`) aborta la compilación inmediatamente.
- **Obligación de Wildcards:** En inducciones y pattern matching, descartar explícitamente hipótesis y parámetros irrelevantes mediante `_` en lugar de asignar identificadores nombrados (ej. `| succ _ ih => ...` en vez de `| succ m ih => ...` si `m` no interviene).
- Prohibición de apagar el linter con directivas locales como parche perezoso.

### 12. Matriz de Contaminación Axiomática y CI Gate (#guard_msgs)
Para certificar que un teorema pertenece estrictamente al Kernel Constructivo (Ring-0) sin contaminarse con axiomas clásicos o extensionales, el agente debe integrar el oráculo de auditoría nativo (disponible sin imports adicionales):
```lean
/-- info: 'MyNamespace.myTheorem' does not depend on any axioms -/
#guard_msgs in
#print axioms MyNamespace.myTheorem
```

#### Dependencias Empíricas de Tácticas (Lean 4.15+):
| Táctica / Constructo | Impacto Axiomático | Estado en Ring-0 |
| :--- | :--- | :--- |
| `rfl` / `by decide` | **0 axiomas** (Igualdad definicional pura) | **Admitido** |
| `cases` con constructores disyuntos (`noConfusion`) | **0 axiomas** | **Admitido** |
| `simpa only [] using h` | **0 axiomas añadidos** (hereda los de $h$) | **Admitido** |
| `rw` con lemas inductivos sin axiomas | **0 axiomas** (vía `Eq.rec` inductivo) | **Admitido** |
| `simp` / `simp only` | Inyecta frecuentemente **`propext`** | **Restringido** |
| `omega` | Inyecta **`propext`** y **`Quot.sound`** | **Prohibido en teoremas constructivos** |
| Subtipos (`Fin n`) y funciones (`Fin n → T`) | Disparan `Quot.sound` vía extensionalidad funcional (`funext`) | **Restringido** |

- **Regla de Sustitución:** En demostraciones donde se exija pureza axiomática, queda prohibido el uso de `omega`. La aritmética de Peano debe derivarse mediante inducción estructural explícita (`succ_add_eq`, `zero_add_eq`) y reescritura pura.

### 13. Patrón de Recursos Afines: Mónada Indexada y Negación por Error de Tipos
Dado que los valores en Lean son intrínsecamente duplicables (*copyable*), las invariantes de consumo único (afinidad) y protocolos lineales deben modelarse como **Mónadas Indexadas por Transición de Estado**:

```lean
-- Mónada indexada: la composición p >>= f exige que el estado post de p coincida con el pre de f
inductive Transition (α : Type u) : State → State → Type u where
  | pure {s : State} (value : α) : Transition α s s
  | step {s t : State} (event : Event) (fresh : Fresh s event.slot)
      (next : Transition α (mark s event.slot) t) : Transition α s t

def bind {s t v : State} (p : Transition α s t) (f : α → Transition β t v) : Transition β s v :=
  match p with
  | .pure a => f a
  | .step e h next => .step e h (bind next f)
```

#### Testeo Unitario de Errores de Compilación (#guard_msgs error)
Para certificar que el sistema de tipos rechaza la reutilización de un recurso gastado (isomorfismo de negación lineal), el agente DEBE incluir pruebas negativas directas sin romper `lake build`:
```lean
/--
error: type mismatch
  oneShot
has type
  Transition Unit (initial 1) (mark (initial 1) 0) : Type
but is expected to have type
  Transition Unit (mark (initial 1) 0) (mark (initial 1) 0) : Type
-/
#guard_msgs (error, drop info) in
#check (show Transition Unit (initial 1) (mark (initial 1) 0) from
  oneShot.bind (fun _ => oneShot))
```

#### Modelado Concurrente Asíncrono (Álgebra Interleaves)
Para probar la preservación de invariantes sobre enjambres concurrentes no deterministas sin introducir locks ni IO bloqueante, se utiliza el shuffle inductivo:
```lean
inductive Interleaves : List Event → List Event → List Event → Prop where
  | nil : Interleaves [] [] []
  | left (e : Event) (rest : Interleaves xs ys zs) : Interleaves (e :: xs) ys (e :: zs)
  | right (e : Event) (rest : Interleaves xs ys zs) : Interleaves xs (e :: ys) (e :: zs)
```
Permite demostrar inductivamente que para cualquier orden de ejecución que satisfaga `Interleaves xs ys zs`, el cardinal terminal de eventos, la conservación de identidades y la unicidad de slots (`Nodup`) son teoremas universales libres de axiomas.

### 14. Arnés de Atestación Empírica en Tres Capas (The 3-Layer Proof Battery)
Ante cualquier pulso o requerimiento de «pruebas», «evidencia empírica» o validación de asertos formales, queda estrictamente prohibido responder con argumentación retórica o texto descriptivo. El agente DEBE ejecutar y certificar en silicio la batería secuencial de 3 capas:

1. **Capa 1 · Kernel Formal Lean 4 (`proof/lean`):**
   ```bash
   cd /Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/proof/lean && lake build
   ```
   *Criterio:* Código de salida 0, 0 errores, 0 warnings. Verificación de teoremas de reflexión (`by decide`) en `C5PortHamiltonian.lean` e invariantes de alineación L1 KUDURRU-64.
2. **Capa 2 · Oráculos Z3 SMT y Solidez Axiomática (`pytest`):**
   ```bash
   pytest /Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/tests/test_lean_kernel_soundness.py /Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/tests/test_z3_firewall.py -v
   ```
   *Criterio:* 8/8 tests PASSED. Verificación de ausencia de `sorry`, `goal.admit` y colapso determinista `Saga1ApoptosisError` (UNSAT) ante alucinaciones algebraicas inyectadas.
3. **Capa 3 · Consenso BFT AOT y C-FFI Bare-Metal (`cargo test`):**
   ```bash
   cargo test --test bft_aot_test --test ffi_test
   ```
   *Criterio:* Éxito de ingesta en `valid_trace.bin` y detección determinista de paradoja causal en `corrupt_state.bin` (`Z3_PARADOX: causality_link_0_1`).

### 15. Superación de la Trampa MCP Académica (Cambio 2 frente a Inria `rme` / K-Z3)
El agente debe distinguir tajantemente entre la postura académica externa y la arquitectura soberana en silicio:
- **La Trampa Académica (Cambio 1):** Conectar LLMs a demostradores formales como clientes externos mediante servidores MCP (JSON-RPC sobre stdio o sockets). Introduce un cuello de botella de serialización de texto (~10 ops/s), fragmentación de contexto y subordinación del verificador a la voluntad del modelo.
- **La Solución Soberana C5-REAL (Cambio 2):**
  1. *Inversión de Control:* Lean 4 es la Realidad Base. El LLM es invocado exclusivamente dentro de una táctica (`TacticM`).
  2. *C-FFI Zero-Copy:* El motor tensorial se linkea estáticamente al binario de Lean 4 (`@[extern "C"]`), operando en memoria unificada a velocidad de hardware (110 M ops/s con Seqlock KUDURRU-64).
  3. *Proof-Carrying Code:* El enjambre probabilístico asume el coste entrópico de proponer el término de prueba; el kernel formal lo valida en tiempo lineal $O(|e|)$ sin permitir reintentos vacíos.

### 16. Patrón Canónico de Autopoiesis Coinductiva (ITrees) y Anti-Zeno Guard
Para agentes de ciclo de vida infinito sin bucles bloqueantes `IO`, el bucle se modela como un `coinductive ITree` acoplado al Ring-0 vía C-FFI:

```lean
inductive CausalEffect : Type → Type where
  | readSharedMemory  (slot : Nat) : CausalEffect (Option Nat)
  | emitBiometricGate (hash : Nat) : CausalEffect Bool
  | yieldToSupervisor (cost : Nat) : CausalEffect Unit

coinductive ITree (E : Type → Type) (R : Type) : Type where
  | ret (res : R) : ITree E R
  | tau (step : ITree E R) : ITree E R
  | vis {A : Type} (eff : E A) (k : A → ITree E R) : ITree E R

@[extern "C"] opaque kudurruShmPoll (slot : Nat) : Option Nat
@[extern "C"] opaque kudurruGateVerify (causalHash : Nat) : Bool

/-- Predicado de Productividad: Garantiza que no hay bucle infinito de pasos tau silenciosos -/
inductive ProductiveIn : Nat → ITree CausalEffect R → Prop where
  | stepVis {A : Type} (eff : CausalEffect A) (k : A → ITree CausalEffect R) : ProductiveIn 0 (ITree.vis eff k)
  | stepRet (r : R) : ProductiveIn 0 (ITree.ret r)
  | stepTau (n : Nat) (t : ITree CausalEffect R) : ProductiveIn n t → ProductiveIn (n + 1) (ITree.tau t)

def MAX_TAU_STEPS : Nat := 64
```

### 17. Implementación Canónica de Chunking Inductivo para AST Masivos
Para trazas masivas de eventos generadas por enjambres probabilísticos, la verificación por reflexión se particiona inductivamente en bloques acotados de memoria $O(1)$:

```lean
structure Chunk where
  id         : Nat
  startNonce : Nat
  endNonce   : Nat
  deltaValid : Bool
deriving Repr, BEq, DecidableEq

def verifyChunkBoundary (prev : Chunk) (curr : Chunk) : Bool :=
  prev.deltaValid && curr.deltaValid &&
  (curr.id == prev.id + 1) && (curr.startNonce == prev.endNonce)

def verifyLedgerStream : List Chunk → Bool
  | [] => true
  | [_] => true
  | c1 :: c2 :: rest =>
    if verifyChunkBoundary c1 c2 then verifyLedgerStream (c2 :: rest)
    else false
```
