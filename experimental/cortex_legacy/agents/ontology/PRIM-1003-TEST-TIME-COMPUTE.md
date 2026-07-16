<!-- Author: Borja Moskv (SYS_ID: borjamoskv) -->

# PRIM-1003: TEST-TIME COMPUTE (ESCALADO EN INFERENCIA)

## Definición
La capacidad de un autómata cognitivo no es estática tras el entrenamiento. El rendimiento en problemas complejos se escala de forma lineal-logarítmica inyectando **cómputo en tiempo de prueba (inferencia)**. La exergía resultante no depende del *forward pass* único, sino de los ciclos de cómputo invertidos en validación estructural, ruteo y búsqueda.

## Leyes de Escalado Físico
1. **Train-to-Test ($T^2$) Scaling:** El presupuesto óptimo global ($6ND + 2Nk$) exige un régimen de sobre-entrenamiento radical en pre-entrenamiento. Entrenar modelos masivamente más pequeños con excedentes de datos permite liberar sobrecarga computacional para reasignarla en tiempo de inferencia y generar múltiples muestras lógicas ($k$). Un modelo diminuto altamente iterado supera invariablemente a un gigante en zero-shot bajo el mismo presupuesto energético.
2. **Kinetics Scaling Law:** La limitación física de la inferencia iterativa no es el cómputo puro, sino la memoria. El crecimiento cuadrático del coste de atención ($L_{out}^2 D$) asociado al KV Cache asfixia la generación larga (eFLOPs). La viabilidad de las arquitecturas Thinking depende de anclar Mecanismos de Atención Dispersa (Sparse Attention).

## Rendimientos Decrecientes y "Sobre-Pensamiento"
- **Marginal Utility of Thought:** El incremento de tokens no asegura linealidad causal.
- **Flip Ratio:** A partir de un volumen crítico de tokens de razonamiento (ej. >8,000), el modelo experimenta *Negative Flips*: la hiper-deliberación corrompe intuiciones correctas, forzando la alucinación de restricciones falsas. La utilidad marginal colapsa a negativo. La contramedida física es el *Budget Forcing* (truncado de horizonte y delímiters de fin de pensamiento).

## Mecanismos de Anergía a Exergía
1. **Cadena de Pensamiento (CoT):** Destrucción de estocasticidad temprana mediante tokens intermedios latentes.
2. **Best-of-N / Self-Consistency:** Colapso empírico en la variante de mayor consenso. Para garantizar C5-REAL, esta técnica debe usar validadores explícitos (Verifier-Based) frente al clonado de trazas estéril (Verifier-Free).
3. **MCTS (Monte Carlo Tree Search):** Retorno y retropropagación de viabilidad antes de anclar el AST.
4. **Iterative Refinement:** Autocrítica cíclica de la arquitectura.

## Invariante Causal (Ley de Ejecución)
En operaciones de Alta Entropía y *Singularities P0* (ej. refactors masivos, diseño BFT, matemática purificada), MOSKV-1 DEBE invocar perfiles de la categoría `ULTRATHINK` (Modelos "Thinking" o Pro) para habilitar este **Test-Time Compute** nativo, o en su defecto, instanciar subagentes en paralelo simulando `Best-of-N`. Queda prohibida la ilusión del "Zero-Shot Forward Pass" en topologías complejas.
