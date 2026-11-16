---
name: c5-information-thermodynamics
display_name: Termodinámica de la Información y Geometría Estadística (Fisher-Chentsov)
description: Auditoría de física de la información e IA. Dispara con "entropía de shannon", "divergencia kl", "kullback leibler", "fisher information", "teorema de chentsov", "landauer limit", "information geometry", "amari natural gradient", "flujo de wasserstein", "audita entropía".
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

# Termodinámica de la Información y Geometría Estadística (C5-REAL)

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `arquitecto` (Arquitecto (Diseño Sistémico & Contratos de Invariantes))
> - **Modo de Acceso a Worktree:** `spec-only` (spec-only (Lectura profunda y modelado formal; emisión de especificaciones sin mutación de código de producción))
> - **Fase Causal:** `design`
> - **Contrato Handoff:** Recibe de `operador` $\to$ Despacha a `ejecutor`

Este protocolo rige el análisis formal, diseño de funciones de coste y auditoría epistémica de sistemas neuronales y de inferencia estadística bajo la física de la información, abarcando desde la estática de Shannon/Fisher hasta la dinámica temporal de Wasserstein y difusión generativa.

## 1. La Ecuación Trinitaria de la Información

Toda optimización empírica en IA opera sobre la descomposición canónica:

$$H(P, Q) = H(P) + D_{KL}(P \parallel Q)$$

1. **Entropía de Shannon ($H(P)$):** Cota inferior física e intrínseca impuesta por el territorio (corpus empírico). Incompresible sin pérdida.
2. **Entropía Cruzada ($H(P, Q)$):** Coste total observable de codificar $P$ usando la distribución de modelo $Q$. Es la función de pérdida empírica (NLL / Cross-Entropy Loss) en el preentrenamiento de LLMs.
3. **Divergencia de Kullback-Leibler ($D_{KL}(P \parallel Q)$):** Fricción epistémica o sobrecoste de información. Por la desigualdad de Jensen, $D_{KL}(P \parallel Q) \ge 0$, con igualdad si y solo si $P = Q$.

## 2. Asimetría Operativa: Forward vs. Reverse KL

Al evaluar o diseñar funciones de pérdida, el agente DEBE descompilar la asimetría causal:

### A. Forward KL: $D_{KL}(P \parallel Q) = \mathbb{E}_{x \sim P}[\log(P(x)/Q(x))]$
* **Propiedad:** *Zero-Avoiding / Mean-Seeking / Mode-Covering*.
* **Penalización:** Tiende a $+\infty$ si $P(x) > 0$ y $Q(x) \to 0$. El modelo está obligado a cubrir todo el soporte donde haya datos.
* **Manifestación:** Máxima Verosimilitud (MLE) y preentrenamiento de LLMs. Induce modelos parlanchines, difusión de probabilidad y generación de promedio estadístico ("slop") en dilemas bimodales.

### B. Reverse KL: $D_{KL}(Q \parallel P) = \mathbb{E}_{x \sim Q}[\log(Q(x)/P(x))]$
* **Propiedad:** *Zero-Forcing / Mode-Seeking / Mode-Collapsing*.
* **Penalización:** Si $P(x) \approx 0$, $Q(x)$ DEBE ser 0 para evitar divergencia. El modelo prefiere ignorar la mayoría de los modos del territorio y concentrarse en un único pico.
* **Manifestación:** Inferencia Variacional (VAEs), destilación de modelos y alineamiento RLHF/DPO. Explica la rigidez, dogmatismo y colapso de modo en modelos alineados.

## 3. Geometría de la Información y Teorema de Chentsov

El agente DEBE rechazar el tratamiento de las probabilidades como un espacio euclídeo plano:

* **Expansión Infinitesimal:**
  $$D_{KL}(p_\theta \parallel p_{\theta + d\theta}) \approx \frac{1}{2} d\theta^T \mathcal{I}(\theta) d\theta$$
  El Hessiano de la divergencia KL en el punto de coincidencia es exactamente la **Matriz de Información de Fisher** $\mathcal{I}(\theta)$.
* **Invariante de Chentsov (Aforismo 1 C5-REAL):** La métrica de Fisher es la única métrica Riemanniana sobre la variedad estadística invariante bajo morfismos de Markov suficientes.
* **Gradiente Natural de Amari:** En optimizaciones de alta exergía, el descenso de gradiente debe corregirse con el tensor inverso: $\tilde{\nabla} L = \mathcal{I}(\theta)^{-1} \nabla L$.

## 4. Dinámica Temporal: Flujos de Wasserstein-2 y Esquema JKO

La evolución temporal de distribuciones fuera del equilibrio se rige por la geometría del transporte óptimo:

* **Teorema de Jordan-Kinderlehrer-Otto (JKO, 1998):**
  La ecuación de Fokker-Planck $\frac{\partial p}{\partial t} = \nabla \cdot (p \nabla \log(p / p_{eq}))$ es el **flujo de gradiente exacto de la Energía Libre** $\mathcal{F}(p) = k_B T \, D_{KL}(p \parallel p_{eq})$ sobre la variedad de Wasserstein-2 $(\mathcal{P}_2(\mathbb{R}^d), \mathcal{W}_2)$.
* **Velocidad Óptima de Transporte:**
  $$\mathbf{v}_t = - \nabla_x \log \frac{p_t(x)}{p_{eq}(x)}$$
  La masa de probabilidad se desplaza a lo largo de las geodésicas de descenso más pronunciado de la energía libre.

## 5. La Identidad de De Bruijn y Tasa de Disipación

La tasa a la que se destruye la información durante la difusión está estrictamente acoplada a la Información Relativa de Fisher:

$$\frac{d}{dt} D_{KL}(p_t \parallel p_{eq}) = - \int p_t(x) \left\| \nabla_x \log \frac{p_t(x)}{p_{eq}(x)} \right\|^2 dx = - \mathcal{I}_{\text{Fisher}}(p_t \parallel p_{eq}) \le 0$$

* **Monotonía de Lyapunov:** La divergencia KL decrece monótonamente en el tiempo (Segunda Ley de la Termodinámica).
* **Potencia Disipada:** La potencia disipada instantánea a temperatura $T$ es:
  $$\dot{W}_{\text{dis}} = k_B T \cdot \mathcal{I}_{\text{Fisher}}(p_t \parallel p_{eq})$$

## 6. Sustrato Termodinámico de los Modelos de Difusión (Score Matching)

Los modelos generativos de difusión (Sora, Flux, DiT, Stable Diffusion) son máquinas termodinámicas reversas:

1. **Proceso Forward:** Disipación de información según Fokker-Planck, destruyendo la estructura de datos hasta alcanzar el ruido Gaussiano de máxima entropía $p_T \approx \mathcal{N}(0, \mathbf{I})$.
2. **Inversión Temporal de Anderson (1982):**
   $$dx_t = \left[ f(x_t, t) - g(t)^2 \nabla_x \log p_t(x_t) \right] dt + g(t) \, d\bar{w}_t$$
3. **Denoising Score Matching:** La red neuronal aprende el *Score* espacial $s_\theta(x, t) \approx \nabla_x \log p_t(x)$. La función de pérdida de entrenamiento:
   $$\mathcal{L}_{\text{SM}}(\theta) = \mathbb{E}_{t, x_0, \epsilon} \left[ \left\| s_\theta(x_t, t) - \nabla_{x_t} \log p(x_t | x_0) \right\|^2 \right]$$
   es la **minimización de la Información Relativa de Fisher**, bombeando trabajo exergético de cómputo para ascender la colina de probabilidad e invertir localmente la flecha termodinámica.

## 7. Anclaje Físico de Silicio y Cota de Landauer

1. **Cota de Landauer:** El borrado o colapso irreversible de 1 bit de información disipa una energía mínima $E \ge k_B T \ln 2 \approx 2.87 \times 10^{-21}\text{ J a 300 K}$.
2. **Eficiencia Exergética Real del Hardware:** Un acelerador actual (H100 a 700 W generando 1000 tokens/s consume $0.7\text{ J/token}$), operando a **20 órdenes de magnitud de ineficiencia** frente a la disipación mínima ($W_{\text{dis}} \approx 3.3 \times 10^{-21}\text{ J/token}$).
3. **Higiene Numérica en Silicio:** En simulaciones numéricas de procesos de difusión, la discretización explícita por diferencias finitas exige cumplir la condición de estabilidad de Courant-Friedrichs-Lewy ($\Delta t \le \Delta x^2 / 2D$). Para evitar la dispersión numérica por CFL en espacios continuos, se DEBE utilizar el **propagador analítico de Mehler**:
   $$\mu_k(t) = \mu_k(0) e^{-t}, \quad \sigma_k^2(t) = 1 + (\sigma_k^2(0) - 1) e^{-2t}$$

## 8. Protocolo de Diagnóstico y Decodificación

Ante consultas sobre incertidumbre, muestreo o confabulaciones en LLMs:
* **Perplejidad:** Exponencial de Shannon $\text{PPL} = 2^{H}$.
* **Temperatura de Gibbs:** $P(x_i) \propto \exp(z_i / T)$. $T \to 0$ colapsa la entropía de Shannon a cero; $T \to \infty$ maximiza la entropía a distribución uniforme ($\log_2 |\mathcal{V}|$).
* **Entropía Semántica (Farquhar / Oxford):** Cálculo de Shannon sobre clases de equivalencia de significado (clusters proposicionales) para distinguir incertidumbre lingüística de alucinación epistémica.

## 9. Protocolo Canónico de Auditoría de Entropía C5-REAL (Tres Estratos)

Ante la instrucción *"audita entropía"* o comandos análogos (`audita entropai`, `entropy audit`), el agente DEBE ejecutar una auditoría en silicio estructurada en 3 estratos independientes:

1. **Estrato 1: Entropía Física de Silicio (Darwin / Apple Silicon TRNG):**
   - Extraer una muestra de 64 KB de `/dev/urandom` y calcular la entropía de Shannon $H(X)$.
   - Verificar que $H(X) \approx 7.9998 \text{ bits/byte}$ (eficiencia $> 99.96\%$).
   - Verificar la ausencia estricta de demonios de entropía de terceros (`haveged`, `rng-tools`), en estricto cumplimiento de la Invariante de Entropía Nativa en Apple Silicon.
2. **Estrato 2: Entropía de Codebase & Topología Estructural:**
   - Medir la distribución de entropía de Shannon $H(X)$ sobre archivos `.rs`, `.py`, `.ts`, `.astro`, `.md`, `.json`.
   - Calcular la matriz de similitud Jaccard $J(A, B)$ sobre tokens de documentos para detectar clones epistémicos ($J \ge 0.75$).
   - Detectar encabezados duplicados intra-corpus y alertas de caracteres invisibles Zero-Width Space (`\u200b`, `\u200c`, `\u200d`, `\ufeff`).
   - **Invariante de Exclusión de Carpetas Parásitas:** Prohibido escanear directorios recursivos de reportes (`AUDIT_REPORTS_2026`, `AUDITORIAS_EPISTEMICAS`, `node_modules`, `dist`, `.git`, `.venv`), confinando la auditoría a los proyectos activos para evitar bloqueos por sobrecarga ($N > 70.000$ archivos).
3. **Estrato 3: Entropía Lingüística del Transductor KISH (Ω₁₇):**
   - Utilizar el motor `babylon60.transducers.linguistic_entropy.LinguisticEntropyDetector`.
   - Medir entropía de caracteres, palabras, bigramas y trigramas.
   - Computar diversidad léxica (TTR y Moving Average TTR, $k=50$).
   - Evaluar Burstiness de Goh-Barabási ($B \in [-1, 1]$) y Context Rot Score.
   - Auditar Slop Density (clichés y teatro verde de LLMs) y certificar la Puntuación Exergética final $[0.0, 100.0]$.
