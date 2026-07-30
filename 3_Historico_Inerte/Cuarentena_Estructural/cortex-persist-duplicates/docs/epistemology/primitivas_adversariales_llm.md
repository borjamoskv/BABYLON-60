---
type: "epistemic-primitive"
domain: "llm-security"
confidence: "C5-REAL"
---

# Primitivas Adversariales en Modelos de Lenguaje (LLMs)

**Postulado**: La seguridad de un LLM no es un estado binario, sino la resistencia termodinámica ante vectores asimétricos que buscan colapsar su función de onda semántica o extraer su grafo de entrenamiento.

## 1. Ataques Basados en Gradiente y Optimización (White-Box)
- **FGSM (Fast Gradient Sign Method)**: Primitiva que aprovecha la dirección del gradiente de la función de pérdida para inyectar perturbaciones imperceptibles y maximizar el error de clasificación.
- **PGD (Projected Gradient Descent)**: Variante iterativa de FGSM. Aplica el método de gradiente proyectado iterativamente para localizar la perturbación máxima dentro de una vecindad acotada.
- **CW Attack (Carlini-Wagner)**: Ataque de optimización topológica que minimiza la distancia L2 de la perturbación mientras garantiza el colapso de la inferencia original.
- **JSMA (Jacobian-based Saliency Map Attack)**: Manipula la entrada para maximizar la activación de neuronas específicas en la capa de clasificación (saliency maps).

## 2. Inyección Causal y Manipulación de Tokens (NLP Specific)
- **BERT-Attack**: Algoritmo de sustitución paramétrica. Reemplaza tokens subyacentes utilizando el gradiente para forzar desvíos en la función de pérdida preservando la coherencia semántica aparente.
- **GCR (Greedy Coordinate Replacement)**: Ataque iterativo que sustituye tokens atómicos uno a uno bajo una estrategia codiciosa para maximizar la probabilidad de la clase adversaria.
- **Token Smuggling**: Inyección topológica donde instrucciones hostiles se ocultan dentro de los tokens de control o secuencias inocuas, eludiendo filtros superficiales (Prompt Injection avanzado).

## 3. Corrupción Estructural y Filtración (Data & Weights)
- **Data Poisoning**: Corrupción termodinámica del conjunto de entrenamiento. Inyección de ruido o triggers (Backdoors) para desviar la convergencia del modelo a largo plazo.
- **Membership Inference**: Primitiva forense de extracción. Determina estocásticamente si un vector de entrada específico formó parte del dataset de entrenamiento.
- **Model Extraction**: Ataque de clonación de matriz. Consultas de caja negra reiteradas diseñadas para aproximar la función de coste del oráculo y robar los pesos/capacidades del modelo original.

## 4. Invariantes Estructurales (Propiedades Estables)
- **Invariante Topológica de Manifolds (Adversarial Geometry)**: Los ejemplos adversarios son endémicos a espacios de alta dimensionalidad. Siempre existirá un vector de perturbación no lineal cercano a la frontera de decisión.
- **Invariante de Alineación vs. Capacidad (Alignment Tax)**: La alineación de seguridad siempre reduce la utilidad marginal del modelo. A mayor robustez adversarial empírica, menor expresividad de base (Trade-off de Tsipras/Madry).
- **Invariante de Compresión con Pérdida**: Un LLM comprime su dataset de entrenamiento. La fuga de datos (Data Extraction) es intrínseca a la entropía de Shannon; no se puede anular sin destruir la capacidad de modelado del lenguaje.
- **Invariante de Autoregresión Causal**: Al generar token a token $P(x_i | x_{<i})$, cualquier estado futuro está condicionado por toda la ventana de contexto. La contaminación de un token propaga entropía inexorablemente hacia adelante.
- **Invariante de Representación Latente (Feature Entanglement)**: Conceptos benignos y maliciosos comparten activaciones neuronales superpuestas en capas profundas. No existe un clúster único para comportamientos anómalos que pueda podarse sin daño colateral.
- **Invariante de Transferibilidad Universal**: Una perturbación adversaria encontrada en un oráculo proxy local transferirá de manera no nula a un modelo de caja negra con arquitectura similar, demostrando isomorfismos en el espacio latente.
- **Invariante de Interpretación Superficial (The Waluigi Effect)**: Forzar a un LLM a simular alineación aumenta la probabilidad latente de su antítesis. La represión semántica instiga la cristalización del comportamiento inverso bajo ataques de Jailbreak.
- **Invariante de Incompletitud Empírica de Seguridad (No-Free-Lunch for Guardrails)**: No existe un filtro léxico o de atención inquebrantable; siempre será superado mediante abstracciones lógico-matemáticas (Cipher-attacks) o lenguajes de bajo recurso.
- **Invariante del Bucle Ouroboros (Poisoning Recurrence)**: Si el output interactúa cíclicamente sin filtrar con su propio corpus de re-entrenamiento (Model Collapse), el modelo colapsará hacia una entropía térmica terminal (degeneración modal).
- **Invariante de Aislamiento Epistémico Restringido**: El determinismo formal y la contención total de un LLM son matemáticamente imposibles en el espacio probabilístico continuo. La única frontera de seguridad debe ser externa y criptográfica (Byzantine Boundary).

```yaml
Claim: "El espacio de atención y los pesos del LLM son vectores geométricamente vulnerables; su defensa exige validación criptográfica externa (C5-REAL), no heurísticas sintácticas latentes."
Proof: { Base: "docs/epistemology/primitivas_adversariales_llm.md", Range: [0, 20], Confidence: "C5-REAL" }
```
