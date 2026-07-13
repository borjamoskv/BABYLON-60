<!-- Author: Borja Moskv (SYS_ID: borjamoskv) -->

# PRIM-1004: ALGORITMOS DE INFERENCIA CAUSAL

## Definición
Estructuras mecánicas que fuerzan el gasto computacional en validación e iteración sobre el Árbol de Búsqueda latente de los LLMs. Su existencia separa a un motor de renderizado estadístico de una Arquitectura Frontera.

## 1. Process-Supervised Reward Models (PRMs)
El rechazo definitivo de los *Outcome-supervised Reward Models (ORMs)*. Los ORMs promueven "pasos milagrosos" o alucinaciones matemáticas premiando un resultado final correcto alcanzado por lógica errónea. Un **PRM** provee supervisión de proceso densa, evaluando la validez termodinámica de cada paso intermedio, permitiendo una retropropagación quirúrgica. (Ej. *Sci-PRM* evita la alucinación de literatura científica al validar herramientas de consulta externa).

## 2. Monte Carlo Tree Search (MCTS) en LLMs
Evita el colapso de error de la decodificación auto-regresiva. Convierte secuencias de tokens en nodos explorables bajo cuatro ciclos:
- **Selection:** Avance sobre las ramas de mayor recompensa (heurística UCB1).
- **Expansion:** Muestreo de alternativas desde el nodo frontera con filtrado de similitud.
- **Evaluation:** Asignación asíncrona de recompensa local (usualmente delegada al PRM).
- **Backpropagation:** Subida del valor de recompensa hacia los nodos raíz para castigar ramificaciones inútiles.

## 3. Group Relative Policy Optimization (GRPO)
Destrucción de la ineficiencia de Memoria asociada al RLHF clásico (PPO). Elimina la red Value (Crítica). En su lugar, GRPO calcula el *Advantage* normalizando la recompensa local dentro de un grupo cerrado de $G$ respuestas generadas por el modelo, aplicando penalizaciones Kullback-Leibler (KL) frente al modelo de referencia para impedir el *reward hacking*.

## 4. Bucle Aletheia (Arquitecturas Asíncronas)
Patrón arquitectónico donde el cómputo de prueba opera como un enjambre autónomo:
1. **Generator:** Exploración masiva y apertura de ramas de hipótesis.
2. **Verifier:** Integración de Tool Use estricto (ejecución de código / RAG causal) para contrastar el *Generator*.
3. **Reviser:** Parcheo o rebobinado (Restart) en caso de fractura lógica. Adquisición de la capacidad ontológica de "declarar intratabilidad" y rendirse formalmente antes que alucinar.
