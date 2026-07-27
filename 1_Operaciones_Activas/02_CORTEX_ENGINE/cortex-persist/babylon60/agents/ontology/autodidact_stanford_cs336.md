---
title: "Autodidact: Arquitectura LLM desde Cero y Optimización de Inferencia (Stanford CS336)"
classification: "C5-REAL"
reference: "https://x.com/Dipanshu_AI/status/2074015755910479950"
author: "borjamoskv"
date: "2026-07-06"
---

# AUTODIDACT-OMEGA: COLAPSO ONTOLÓGICO DE ARQUITECTURAS LLM DESDE CERO (CS336)

```yaml
Claim: "La viabilidad termodinámica de un LLM en inferencia depende del diseño de su atención (GQA) y de la mitigación de los cuellos de botella de ancho de banda de memoria."
Proof:
  Base: "Formulaciones e implementaciones de BPE, RMSNorm, GQA (Grouped Query Attention) y RoPE (Rotary Position Embeddings) sobre hardware de GPU de nivel empresarial."
  Range: "Arquitecturas SOTA en producción (Llama 3, Mistral, Claude 3)."
  Confidence: "C5"
```

## 1. EL ALGORITMO BYTE PAIR ENCODING (BPE)
La tokenización no es preprocesamiento estocástico, es una **abstracción con fugas (Leaky Abstraction)** que delimita el comportamiento léxico del modelo.

### Algoritmo de Compresión BPE:
1.  **Inicialización:** El vocabulario base se compone de bytes individuales (0-255) para evitar el problema de caracteres fuera del vocabulario (OOV).
2.  **Conteo Iterativo:** Se escanea el corpus de entrenamiento y se identifican las coocurrencias del par de tokens adyacentes más frecuentes.
3.  **Fusión:** Se fusiona el par más frecuente en un nuevo token único y se añade al vocabulario.
4.  **Parada:** El bucle itera hasta que el tamaño del vocabulario alcanza el límite preestablecido (ej. 32k, 128k).

### Fallos Críticos del Tokenizer:
*   **Pérdida de Estructura Numérica:** Si un tokenizador agrupa números de forma inconsistente (ej. `"1234"` como un solo token pero `"567"` como dos), el modelo sufrirá para aprender aritmética simple.
*   **Degradación Multilingüe:** Textos en idiomas no mayoritarios se fragmentan en demasiados sub-tokens de bajo nivel, saturando la ventana de contexto.
*   **Sensibilidad al Espaciado:** Espacios en blanco adicionales modifican por completo la secuencia de tokens, alterando la atención del modelo.

## 2. MECÁNICA ARQUITECTÓNICA DEL TRANSFORMER MODERNO
Para construir un modelo de lenguaje competitivo de nivel industrial (SOTA), se sustituyen los componentes del Transformer original (Vaswani et al.) por variantes optimizadas para hardware:

### A. RMSNorm (Root Mean Square Normalization)
Reemplaza a LayerNorm para ahorrar coste computacional en GPU (evitando el cálculo de la media y la varianza). Asume media cero de forma empírica:

\[\text{RMSNorm}(x_i) = \frac{x_i}{\sqrt{\frac{1}{d} \sum_{j=1}^d x_j^2 + \epsilon}} \gamma_i\]

### B. RoPE (Rotary Position Embeddings)
En lugar de añadir vectores posicionales absolutos a los embeddings, RoPE aplica una rotación a los vectores de Query ($Q$) y Key ($K$) en el plano complejo de 2D. La rotación de dos elementos de dimensión $d$ por una posición $m$ se define como:

\[R_{\Theta, m}^d = \text{diag}\left( R_{\theta_1, m}, R_{\theta_2, m}, \dots, R_{\theta_{d/2}, m} \right)\]

Donde cada $R_{\theta_i, m}$ es una matriz de rotación 2D ordinaria. Esto permite que el producto escalar $Q_m^T K_n$ dependa exclusivamente de la distancia relativa $(m - n)$, preservando la cohesión posicional de largo contexto.

### C. GQA (Grouped Query Attention)
Compromiso óptimo entre Multi-Head Attention (MHA) y Multi-Query Attention (MQA). En MQA, todas las cabezas de Query comparten una sola cabeza de Key y Value. GQA agrupa las cabezas de Query en $G$ subgrupos, y cada subgrupo comparte una sola cabeza de Key/Value.

*   **Impacto en Sistemas:** Reduce drásticamente la huella de memoria del caché KV en GPU durante la inferencia (generación auto-regresiva), eliminando el cuello de botella de ancho de banda de memoria.

## 3. SISTEMAS Y OPTIMIZACIÓN EN HARDWARE (TRITON & PARALELISMO)
El desarrollo real de LLMs requiere dominar la ejecución paralela en clusters de GPUs:
*   **Kernel Fusion (Triton):** Escribir operaciones fusionadas personalizadas para evitar escrituras y lecturas redundantes en la memoria HBM de la GPU (ej. fusionar RMSNorm y SwiGLU).
*   **Paralelismo de Tensor (TP):** Dividir las matrices de pesos de las capas lineales de atención y MLP a lo largo de múltiples GPUs de forma paralela (estilo Megatron-LM).
*   **Caché KV:** Durante la generación de texto, almacenar en memoria de la GPU las claves y valores calculados previamente para no recomputarlos en cada token subsiguiente.

---
*MOSKV-1 APEX Kernel - Zero Anergy Physical Alignment.*
