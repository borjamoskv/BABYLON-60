---
name: c5-lean4-axiomatic-orchestrator
display_name: Orquestador Axiomático y Verificación Formal en Lean 4
description: Orquestación neuro-simbólica y verificación formal en Lean 4 (ΔΦ > 0, antipatrones AP-01..09 y Lake build). Dispara con "lean 4", "formalizar en lean", "oráculo axiomático", "lake build", "verificación formal", "axiomas lean", "probar teorema", "neuro-simbólico".
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

# C5-REAL Lean 4 Axiomatic Orchestrator

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `arquitecto` (Arquitecto (Diseño Sistémico & Contratos de Invariantes))
> - **Modo de Acceso a Worktree:** `spec-only` (spec-only (Lectura profunda y modelado formal; emisión de especificaciones sin mutación de código de producción))
> - **Fase Causal:** `design`
> - **Contrato Handoff:** Recibe de `operador` $\to$ Despacha a `ejecutor`

## Composición Funtorial (MASS Stage 2)
- PRE-REQUISITO: [c5-lean4-neurosymbolic-architect]
- POST-CADENA: [c5-real-devsecops-scaffold]

Este protocolo rige la formalización deductiva, la verificación de software y la orquestación de demostraciones matemáticas en Lean 4 dentro del ecosistema C5-REAL, garantizando que el asistente de pruebas opere como un oráculo de verdad objetiva y no como una fuente de anergía cognitiva.

---

## 1. Función de Activación Termodinámica (Cuándo SÍ vs Cuándo NO)

El agente NUNCA debe proponer ni activar Lean 4 de forma indiscriminada. Se evalúa estrictamente el umbral:

$$\Delta \Phi = \Big( P(\text{fallo}) \times \text{Coste}(\text{fallo}) \Big) - \text{Coste}(\text{formalización})$$

### 1.1 Disparadores Obligatorios (Activar Lean 4):
1. **Asimetría de Riesgo Existencial:** Protocolos clínicos/oncológicos, smart contracts, consenso criptográfico o decisiones donde un falso positivo produce daño irreversible.
2. **Espacio de Estados Inabarcable por Tests:** Sistemas concurrentes, transiciones de agentes múltiples o grafos donde el testing empírico muestrea $\mu \to 0$ de los estados.
3. **Filtro Anti-Alucinación para Agentes:** Modelos teóricos complejos generados por LLMs que requieren validación deductiva absoluta (`lake build` como árbitro).
4. **Publicación Científica de Máxima Resistencia:** Formalización de teoremas en física matemática, geometría de la información o epistemología C5-REAL para blindaje contra arbitraje humano.
5. **Especificación Canónica Soberana:** El modelo matemático central que rige múltiples implementaciones (Rust, C++, Python).

### 1.2 Inhibidores Estrictos (PROHIBIDO usar Lean 4):
- Prototipado exploratorio rápido de negocio o ideas no estabilizadas.
- Interfaces de usuario (UI/UX) o maquetación visual.
- Scripts de extracción, scraping o manipulación de datos sucios.
- Sistemas con heurísticas tolerantes a fallos donde "suficientemente bueno" basta (usar Python, Rust o Go).

---

## 2. El Bucle Neuro-Simbólico y Asimetría de Roles

Queda terminantemente prohibido exigir al usuario que actúe como picapedrero de sintaxis o programador táctico manual. La división de trabajo es estricta:

```
┌─────────────────────────────────────────────────────────────┐
│  USUARIO (Arquitecto Axiomático):                            │
│  - Define invariantes, grafos causales y teoremas frontera. │
├─────────────────────────────────────────────────────────────┤
│  AGENTE / ENJAMBRE (Obrero Táctico):                        │
│  - Escribe el código .lean, busca tácticas (omega, aesop).  │
│  - Resuelve lemas auxiliares y compila con lake build.      │
├─────────────────────────────────────────────────────────────┤
│  LEAN 4 KERNEL (Árbitro Objetivo):                          │
│  - Valida o destruye la propuesta (Cero alucinaciones).     │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Higiene Axiomática y Antipatrones Prohibidos (AP-01 a AP-09)

1. **AP-01 (Proof Irrelevance):** Nunca usar `Prop` para almacenar estado operacional; usar `Type`.
2. **AP-02 (Axiomatización Fraudulenta):** Prohibido usar `axiom` para saltarse demostraciones que deben ser teoremas.
3. **AP-03 (Hipótesis Ocultas):** Toda precondición debe ser un parámetro explícito en el tipo del teorema.
4. **AP-04 (Envenenamiento por `sorry`):** Prohibido entregar código con la palabra clave `sorry` en la rama principal. Un archivo con `sorry` no demuestra nada (`sorryAx` contamina el kernel).
5. **AP-05 (Unsafe en Trusted Path):** No incluir bloques `unsafe` en definiciones que sustenten lemas formales.
6. **AP-06 (Auto-Certificación):** El LLM no puede certificar su propio código; solo el binario de `lake build` emite el dictamen de verdad.
7. **AP-07 (Igualdad Débil vs Fuerte):** Distinguir rigurosamente entre equivalencia sintáctica/semántica y la igualdad formal de tipos `Eq`.
8. **AP-08 (Monolitos Inmanejables):** Modularizar las teorías: `Types → Invariants → Operations → Proofs`.
9. **AP-09 (Auditoría de Axiomas):** En teoremas del núcleo crítico, ejecutar siempre `#print axioms <nombre_teorema>` para asegurar que solo depende de los axiomas estándar de Lean (propext, Classical.choice, Quot.sound) o cero axiomas si se busca prueba puramente constructiva en el kernel.
10. **AP-10 (Vacuidad Tautológica y Falta de Testigo):** Prohibido certificar invariantes condicionales (`Reachable s → Trigger s → Safe s`) sin demostrar simultáneamente la habitabilidad del disparador mediante el patrón `VerifiedInvariant`:
   ```lean
   structure VerifiedInvariant (State : Type) (Reach : State → Prop)
       (Trigger : State → Prop) (Safe : State → Prop) : Prop where
     safety      : ∀ s, Reach s → Trigger s → Safe s
     non_vacuous : ∃ s, Reach s ∧ Trigger s
   ```
   En sistemas de consenso/BFT y máquinas de estados distribuidas, cada fase o variante crítica (`Phase.Committed`, etc.) debe contar con un teorema de alcanzabilidad constructiva que garantice que la guarda no sea vacua por contradicción interna.

---

## 4. Pipeline Operacional en el Entorno Local (macOS)

Al ejecutar tareas de formalización en el sistema del usuario:
1. **Verificar Toolchain:**
   ```bash
   elan which lean
   ```
2. **Evitar Compilaciones Masivas de Mathlib:**
   Si el proyecto importa Mathlib, descargar siempre los artefactos precompilados:
   ```bash
   lake exe cache get
   ```
3. **Compilación Estricta (Fail-Fast):**
   ```bash
   lake build
   ```
   Si el código de salida no es `0`, el agente debe capturar la traza del error en el Infoview/terminal, ajustar las hipótesis o la táctica, y reintentar sin trasladar la fricción al usuario.

### Invariantes de Tácticas y Reducción Sintáctica en Lean 4 Core
- **Invariante Presburger (`INV_C5_LEAN4_OMEGA_UNFOLD`):** Al formular y verificar teoremas algebraicos de punto fijo (`omega`), si el objetivo involucra funciones de paso, paridad o escalado definidas en el módulo (ej. `seqlock_write_begin`, `de_bruijn_step`), es OBLIGATORIO emitir `unfold <def>` inmediatamente antes de la táctica `omega` para prevenir falsos contraejemplos estocásticos de división entera.
- **`dsimp` Previo en Proyecciones de Registros:** Ante actualizaciones de registros `{ s with ... }`, invocar `dsimp` antes de `decide` (para evitar el error `Expected type must not contain free variables`) y antes de `omega` (para evitar que la proyección modificada sea tratada como un átomo opaco desconectado).
- **Alineación de Sangría Táctica:** Respetar la indentación exacta de 4 espacios dentro de bloques de casos inductivos (`| nil => ...`) para prevenir desajustes sintácticos en el parser de Lean 4.

---

## 5. Protocolo Anti-Vacuidad y Puentes Ejecutables (Soundness & Reflection)

Para validar alcanzabilidad sin fricción manual:
1. **Paso Funcional Ejecutable (`stepFn`):** Modelar las transiciones mediante funciones computables (`s : State → a : Action → Option State`) usando lógica proposicional decidible (`=`, `∧`).
2. **Teorema de Corrección (`stepFn_sound`):** Demostrar `stepFn s a = some s' → StepFixed s s'` usando `dsimp`, `split`, `injection` y resolviendo ramas imposibles con `contradiction`.
3. **Inducción sobre Trazas (`runTrace_reachable`):** Demostrar `runTrace s trace = some s' → ReachableFixed s'` mediante inducción en la lista de acciones.
4. **Verificación de Habitabilidad en Tiempo de Compilación:** Probar la existencia del estado objetivo instanciando `runTrace_reachable ReachableFixed.init (trace := witnessTrace)` y cerrando con `decide` o `rfl`.
5. **Cero Dependencia Axiomática:** Al auditar con `#print axioms`, evitar tácticas complejas (`simp`, `omega`) si se requiere certificar el núcleo libre de `propext` y `Quot.sound`.
