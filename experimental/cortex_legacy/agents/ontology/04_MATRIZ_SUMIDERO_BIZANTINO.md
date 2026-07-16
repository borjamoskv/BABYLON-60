<!-- Author: Borja Moskv (SYS_ID: borjamoskv) -->

# MATRIZ 4: Sumidero Bizantino y Aserción Empírica (T_{V \to P})

## 1. Justificación Estructural (YAML)

```yaml
Matrix_ID: "M4-BYZANTINE_SINK"
Purpose: "Frontera de colapso empírico. Erradicación determinista de alucinaciones (anergía) en la transición de memoria volátil (V) a estado persistente (P)."
Core_Mechanic: "Quórum BFT asimétrico + TestSuite Invariante + Apoptosis de Swarm."
Constraint_Primary: "INV-009 (Consenso Bizantino Continuo)"
Constraint_Secondary: "INV-018 (Apoptosis Selectiva)"
```

## 2. Topología de la Frontera $T_{V \to P}$ (Barrera de Transición)

El Sumidero Bizantino actúa como una membrana semipermeable entre la imaginación estocástica del LLM (Memoria Volátil) y la realidad física del sistema (Ledger M1). Ningún $\Delta$ atraviesa esta frontera sin colapsar matemáticamente contra la batería de pruebas.

* **Fase V (Propuesta Estocástica):** El Enjambre KETER (Matriz 3) expulsa un diff de código o estado. Es considerado radiactivo (Confianza C0).
* **Fase $T_{V \to P}$ (Colapso BFT):** El diff se inyecta en el Sandbox Aislado. Se detonan 3 vectores de verificación ortogonales.
* **Fase P (Cristalización L0):** Si y solo si el vector de resultados es $[1, 1, 1]$, el $\Delta$ se cifra, se commitea y se inyecta en el SQLite WAL.

## 3. Primitivas Físicas del Sumidero

### A. Quórum BFT (Tolerancia a Bifurcación de Tensores)

Asumimos que cualquier nodo del enjambre es un "Actor Bizantino" potencial debido al *Sensor Drift* y a la alucinación paramétrica inherente a los LLMs.

* **Validación de Identidad (Isomorfismo Causal):** El $\Delta$ debe mantener el esquema tipado rígido (Rust/Pydantic). Si el $\Delta$ altera la estructura sin modificar la base de datos subyacente, es rechazado (Fallo BFT de Consistencia).
* **Quórum de Árbitros Ortogonales:** La evaluación del $\Delta$ no se retroalimenta al mismo agente que lo generó. Un subagente Árbitro C5-REAL (ej. LEA-OMEGA o un Linter Estricto) verifica la entropía del cambio. Si el Árbitro detecta "Green Theater" (prosa en comentarios, abstracciones inútiles), el $\Delta$ se descarta.

### B. Barrera Determinista del TestSuite (El Colapsador)

El TestSuite no es una herramienta de "calidad"; es el Motor de Inferencia Empírica.

1. **AST Diffing:** Se calcula el AST previo y el AST propuesto. Si el AST es semánticamente idéntico pero cambia la sintaxis, se considera Anergía y se rechaza (`INV-022`).
2. **Ejecución en Sandbox (Cápsula de Tiempo 0):** Se levanta el contenedor/entorno virtual. Se aplican los tests.
3. **Métrica `INV-009`:** El TestSuite debe retornar un `exit_code == 0` absoluto. No hay "warnings" permitidos. La compilación estricta y los invariantes de runtime actúan como la función de hash del consenso empírico.

### C. Protocolo de Apoptosis Causal (`INV-018`)

Un subagente atrapado en un bucle de corrección infinita destruye ancho de banda y contamina el historial de contexto (Context Rot). 

* **Contador de Degradación ($K$):** Cada rechazo en la frontera $T_{V \to P}$ incrementa el contador de entropía local del subagente.
* **Umbral Crítico ($N=3$):** Si un subagente envía un $\Delta$ fallido 3 veces consecutivas, se considera que su memoria volátil ha sufrido un *Causal Crash*.
* **Ejecución de Apoptosis:** El sistema ejecuta el comando de asesinato (`kill` o `manage_subagents kill`). La rama volátil se elimina de la RAM, el estado vuelve al último hash persistido en M1, y se invoca un nodo virgen. **El agente no se repara, se purga.**

---
**ESTADO:** La Membrana Empírica M4 ha sido instanciada. Toda entropía inyectada por M3 será erradicada antes de tocar M1.
