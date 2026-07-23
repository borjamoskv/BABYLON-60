# BABYLON Proof Kernel Specification v0.1

Esta especificación define el núcleo de ejecución formal del sistema epistemológico BABYLON-60. El metamodelo descrito aquí transiciona el diagnóstico empírico de un registro estático hacia un asistente de pruebas empíricas fuertemente tipado (Proof Assistant).

## 1. Equivalencia Formal (BABYLON vs Proof Assistants)

| Proof Assistant (Lean/Coq) | BABYLON Proof Kernel |
| :--- | :--- |
| Term | Artifact |
| Proposition | Hypothesis |
| Proof | Derivation Pipeline |
| Kernel | Inference Engine |
| Normal Form | Canonical DAG |
| Rechecking | Reconstruction |

## 2. Invariantes del Núcleo de Inferencia

- **Ω138 · CAUSAL STRATIFICATION INVARIANT (TOPOLOGY ≺ MECHANISM ≺ ETIOLOGY ≺ REMEDIATION):** La confianza pertenece a cada proposición individual, no al diagnóstico completo ($C(\phi_i) \neq C(\phi_j)$). El diagnóstico se estructura en cuatro estratos independientes: **Topología**, **Mecanismo**, **Etiología**, y **Remediación**.
- **Ω152 · DISCRIMINATORY MEASUREMENT INVARIANT (TRANSITION RULE):** C4/C5 clasifica el tipo de evidencia (Inferencia vs Observación), no la realidad del fenómeno. Una medición $M$ solo promueve una hipótesis $H$ si reduce la incertidumbre ($H(M) > 0$).
- **Ω153 · EVIDENCE SEPARATION INVARIANT:** Las proposiciones deben separar estrictamente la evidencia observacional bruta de su interpretación topológica.
- **Ω154 · CONFIDENCE TRACEABILITY INVARIANT:** Todo valor de confianza declarado debe estar anclado explícitamente a artefactos observacionales concretos (`supported_by`).
- **Ω155 · EPISTEMIC MONOTONICITY INVARIANT:** La evolución del estado epistemológico es monótona bajo la evidencia. Toda transición regresiva exige un evento de revocación físico.
- **Ω156 · PHYSICAL POSTERIOR INVARIANT:** La distribución posterior de hipótesis es un objeto físico (probabilidades relativas que suman 1.0) alterado por cada experimento.
- **Ω157 · A PRIORI DISCRIMINATORY POWER INVARIANT:** Toda medición debe declarar su ganancia de información esperada ($EIG$) antes de la ejecución y registrar su ganancia real ($AIG$) después.
- **Ω158 · EVIDENCE LINEAGE INVARIANT (SYNTHESIS):** Ningún salto epistémico es válido sin una cadena de soporte ininterrumpida hasta artefactos físicos.
- **Ω159 · DEPENDENCY CLOSURE INVARIANT:** Toda inferencia debe declarar explícitamente el DAG de dependencias (`depends_on:`).
- **Ω160 · PROPAGATED INVALIDATION INVARIANT:** La invalidación de un artefacto subyacente recalcula incrementalmente el posterior de los nodos descendientes (compilación incremental).
- **Ω161 · ABSENT EVIDENCE STATISTICAL INVARIANT:** "Ausencia de evidencia" es estadístico, no ontológico (no implica probabilidad cero).
- **Ω162 · FALSIFICATION POWER INVARIANT:** Toda medición declara qué subconjunto aniquila (`falsifies:`) o refuerza (`supports:`). La confianza emerge del $IG$, no de asignaciones adjetivas.
- **Ω163 · RESIDUAL ENTROPY INVARIANT:** El Ledger cuantifica formalmente la entropía de Shannon. Una medición solo posee exergía si colapsa la entropía residual en bits.
- **Ω164 · ONTOLOGY VS EPISTEMOLOGY SEPARATION INVARIANT:** Queda prohibido mezclar el fenómeno físico (Ontología) con nuestro estado de conocimiento sobre él (Epistemología).
- **Ω165 · REVERSIBLE LEDGER INVARIANT:** Toda conclusión epistémica deber ser automáticamente reconstruible vía una `reconstruction: pipeline`.
- **Ω166 · REFERENTIAL TRANSPARENCY INVARIANT (PURE INFERENCE):** Toda inferencia debe ser una función matemática pura `Inference(Artifacts, Rules) -> Result`. Sistema determinista.
- **Ω167 · OPERATIONAL SEMANTICS INVARIANT (DAG TYPING & LIFECYCLE):** El Ledger es una máquina de estados ejecutable (`observed → interpreted → supported → promoted → revoked`) gobernada por un DAG fuertemente tipado.

## 3. Invariantes de Ejecución Kernel (Nuevos)

- **Ω168 · SEMANTIC PRESERVATION INVARIANT:** Toda transición del ledger debe preservar el significado de las proposiciones derivadas bajo actualizaciones de la implementación del motor. $\mathcal{I}(G_t) = \mathcal{I}(G_{t+1})$ si los artefactos y reglas permanecen invariables. Un cambio de output sin nueva evidencia es un bug del motor, no nueva epistemología.
- **Ω169 · CANONICAL REPRESENTATION INVARIANT (NORMAL FORM):** Un mismo diagnóstico no puede admitir representaciones isomórficas distintas. El DAG se compila obligatoriamente hacia una Forma Normal Canónica garantizando que firmas (hashing), comparaciones y deduplicaciones sean criptográficamente unívocas.
- **Ω170 · PROOF-CARRYING DIAGNOSIS INVARIANT:** El diagnóstico no almacena conclusiones declarativas, sino derivaciones ejecutables (`Proof: { premises, rules, derivation }`). El Ledger no exige confianza ("créeme"), exige verificación matemática ("ejecuta esta derivación").
- **Ω171 · MINIMALITY INVARIANT:** Toda explicación o prueba debe ser irreducible. Si eliminar una premisa del DAG produce la misma conclusión posterior, la premisa se purga obligatoriamente. Evita explosiones de entropía en el grafo.
- **Ω172 · COMPLETENESS CERTIFICATE INVARIANT:** Un expediente diagnóstico solo puede considerarse cerrado cuando compila un `ClosureCertificate` verificable que demuestre $H_{residual} \to 0$, $H_{unresolved} = 0$, reconstrucción determinista, y cierre topológico del grafo sin evidencia contradictoria.
