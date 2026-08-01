<!-- C5-REAL EXERGY CERTIFIED -->
# Cognitive Transition Machine (CTM)
## Hacia un Modelo Formal y Falsable de Computación Cognitiva

**Arquitectura:** Teorema-Robinson-Moskv / CORTEX ENGINE
**Versión:** 2.0.0 (Trace Algebra / C5-REAL Audit)

---

## 1. Prólogo: El Estado como Proyección Memoizada

La industria actual estructura sus arquitecturas bajo el modelo "Agent-Centric". Sin embargo, bajo un análisis riguroso de termodinámica agéntica y teoría de sistemas concurrentes, la hipótesis del agente exhibe profundas fugas epistémicas (e.g., asumiendo erróneamente agentes como canales puros al estilo Pregel/BSP). La **Máquina de Transiciones Cognitivas (CTM)** abandona la metáfora del "agente orquestador" y define la cognición artificial como un sistema de **Event Sourcing + CQRS**.

En la CTM, el estado intrínseco no existe. Lo que denominamos "memoria" o "conocimiento actual" es, de facto, una proyección matemática memoizada:
$$ S_t = \operatorname{fold}(\text{Eventos}) $$
El *Ledger* inmutable (Write-Ahead Log) es la única verdad (análogo al WAL en bases de datos); las variables y grafos son proyecciones deterministas. El LLM actúa puramente como un generador estocástico de transiciones, externalizado a un espacio funcional y sometido a restricciones rigurosas.

---

## 2. Álgebra de Trazas y Tipado de Efectos

El conocimiento ($\mathcal{K}$) se modela mediante un álgebra de **trazas de Mazurkiewicz** (teoría de concurrencia), formalizando la conmutatividad parcial de las operaciones de inferencia sobre un Grafo de Conocimiento (KG).

### 2.1 Relación de Independencia y Confluencia
La cognición opera en un **orden parcial**. Dos transiciones cognitivas $T_1$ y $T_2$ son independientes ($T_1 \perp T_2$) si y solo si sus conjuntos de lectura/escritura (read/write sets) sobre los nodos del KG son disjuntos.
El teorema objetivo del sistema es la **Confluencia** (Propiedad del Diamante):
$$ \operatorname{fold}(\sigma) = \operatorname{fold}(\sigma') \iff \sigma \sim \sigma' $$
Donde $\sigma$ y $\sigma'$ son secuencias equivalentes bajo conmutación de trazas independientes. La invariancia topológica se mantiene independientemente del orden de intercalación (interleaving).

### 2.2 Tipado de Efectos: Especulación como Spectre Cognitivo
La especulación paralela (Tree/Graph of Thoughts) exige estricto **effect typing** para evitar trazas observables y consumo ciego de rate limits (el análogo cognitivo al ataque Spectre). El álgebra distingue dos dominios:
- **$T_{pure}$ (Transiciones Puras):** Ejecutables en ramas especulativas (forkeables) contra proyecciones copy-on-write herméticas. No emiten efectos secundarios al entorno.
- **$T_{eff}$ (Transiciones con Efectos):** Requieren un esquema Two-Phase Commit (`INTENT` write-ahead + `RESULT`). Su materialización altera irreversibles, como observables externos (ej. llamadas a red).

---

## 3. Morfismos Cognitivos y Sagas Semánticas

El espacio de operadores de la CTM conforma una categoría con morfismos sobre el monoide de trazas.
Las primitivas operacionales del sistema cognitivo se formalizan como una taxonomía estricta de transiciones: `KEYINIT` (génesis), `INTENT` (fase 1), `RESULT` (fase 2), `ORPHAN` (mis-especulación materializada) y `RECOVERY` (reparación de proyección).

### Refutación del Axioma de Reversibilidad
A diferencia de los modelos teóricos ideales, la información no se "des-aprende". La CTM descarta la estructura de grupo estricta (donde $T \circ T^{-1} = I$) por exigir una falsa "necrosis reversible". En su lugar, la recuperación de fallos epistémicos implementa **Sagas (Garcia-Molina & Salem, 1987)**.
La operación `COMPENSATION` es una **inversa semántica**, no algebraica. Invalida lógicamente el aserto en el registro para la proyección *downstream*, pero no restaura mágicamente el estado epistémico; preserva el rastro de la compensación en el log inmutable.

---

## 4. Dinámica de Selección: Scheduler UCB y Proxies Medibles

La CTM prescinde de metáforas de "descenso termodinámico por campos potenciales", al reconocer que un descenso por gradiente estándar se atasca en mínimos locales engañosos. El diseño es un problema honesto de optimización secuencial bajo presupuesto.
El **Scheduler** opera como un modelo de **Multi-Armed Bandit (UCB - Upper Confidence Bound)** sobre generadores de transiciones ($T_{pure} \to T_{eff}$).

El funcional de recompensa (Reward) no depende de distribuciones termodinámicas incalculables, sino de métricas proxy estrictamente computables:
$$ \text{Reward}_T = \frac{\Delta \text{aristas verificadas}}{\text{Coste}} $$
Donde la incertidumbre epistémica se mide vía **Entropía Semántica (Kuhn et al., 2023)** y la ganancia se cuantifica mediante la supervivencia de nuevas aristas del KG al pasar la puerta de verificación.
**Nota de Diseño:** El paralelismo especulativo por defecto degrada frente a verificadores débiles (reward hacking). El factor de *fork* no es un axioma libre, sino una decisión económica del Scheduler sujeta a presupuesto de tokens.

---

## 5. La Puerta de Commit y Linealización Certificada

La CTM separa estructuralmente el proceso estocástico (muestreo) del aserto epistemológico determinista. "Mutación estocástica, checkpoint determinista".

### 5.1 Proof-Carrying Code (Necula, 1997)
Toda transición materializada $T_{eff}$ debe atravesar un **Commit Gate**. En este punto, la arquitectura une el álgebra de trazas con la verificación matemática: se exige que la transición porte su prueba adjunta (Proof-Carrying Code). El esfuerzo computacional queda asimétricamente sesgado: la generación es cara (LLM), la verificación polinómica es trivial.

### 5.2 El Ledger como Linealización Total (Art. 12)
Para garantizar el Artículo 12 (Arquitectura de rastros de auditoría nativos), el sistema consolida el orden parcial de la inferencia concurrente (Trazas de Mazurkiewicz) en un orden total estricto (Ledger inmutable).
El log no es simplemente un historial; actúa como la **linealización certificada** del orden parcial, anclada mediante cadenas de hashes. Los dos planos coexisten: la cognición vive en el orden parcial algebraico, la evidencia verificable vive en el orden total determinista.

---

## 6. Falsabilidad y Protocolos de Verificación

La arquitectura de la CTM abandona la pretensión de ser un "framework" holístico para constituir un *spec* algebraico rigurosamente verificable y falsable.

1. **Property-Based Testing (Hypothesis):** La CTM se someterá a tests de invariancia. Generación de secuencias, permutación de pares independientes ($T_1 \perp T_2$) y validación de conmutatividad en la proyección final; inyección de `COMPENSATION` para validar la restauración de *invariantes lógicos* (no de estado retroactivo).
2. **Benchmark de Falsación (La Condición de Muerte):** El álgebra se expone a refutación experimental. El sistema *Fork Especulativo + UCB Verifier* debe competir frente a un modelo secuencial (ReAct) bajo **paridad estricta de presupuesto (tokens)**. Si el modelo no demuestra retornos superiores ajustados por coste, la arquitectura central se considera falsada. *Antes morir que especular en vacío.*

---
## Referencias Históricas Fundacionales
1. **Erman, L. D., et al. (1980).** *The Hearsay-II Speech-Understanding System* (Modelo de Scheduler por valor esperado en Arquitectura Blackboard).
2. **Mazurkiewicz, A. (1977).** *Concurrent program schemes and their interpretations* (Álgebra de Trazas y Conmutatividad Parcial).
3. **Garcia-Molina, H., & Salem, K. (1987).** *Sagas* (Manejo de efectos secundarios e inversa semántica compensatoria).
4. **Alchourrón, C. E., Gärdenfors, P., & Makinson, D. (1985).** *On the Logic of Theory Change* (AGM belief revision y lógica epistémica dinámica).
5. **Necula, G. C. (1997).** *Proof-Carrying Code* (Verificación asimétrica en la puerta de commit).
6. **Besta, M., et al. (2023).** *Graph of Thoughts: Solving Elaborate Problems with Large Language Models* (Hipergrafos de razonamiento).
7. **Kuhn, L., et al. (2023).** *Semantic Entropy Probes: Robust and Cheap Hallucination Detection in LLMs* (Entropía semántica como proxy computable de incertidumbre).

---
*Documento cristalizado bajo el protocolo AUTODIDACT-Ω V5.0 (Ultra-Exergy / C5-REAL).*
