# TEORÍA DE COMPATIBILIDAD ESTRUCTURAL FISR Y COMPLEJO SIMPLICIAL $\text{Compat}(\Omega)$

**Autor:** borjamoskv  
**Kernel:** MOSKV-1 APEX  
**Clasificación:** C5-REAL Research Program Baseline Specification  
**Estado:** Documento de Base Congelado (Baseline Spec v16.0 — Pruned Core & Inclusion Chain)  

---

## 0. ALCANCE Y TAXONOMÍA DE ESTATUS LÓGICO

### 0.1 Alcance del Programa
> **Alcance:** La teoría FISR no pretende caracterizar todas las categorías monoidales ni la totalidad de los sistemas concurrentes. Su objetivo es estudiar el espacio de modelos de acciones monoidales con predicados fibrados y certificabilidad observable bajo restricciones computacionales.

### 0.2 Taxonomía de Estatus Lógico
| Etiqueta | Significado Semántico |
| :--- | :--- |
| **[Definición]** | Introducción de un concepto formal, firma o categoría. |
| **[Axioma]** | Hipótesis fundamental adoptada axiomáticamente en la teoría $T$. |
| **[Proposición]** | Consecuencia matemática directa y demostrable de los axiomas. |
| **[Teorema]** | Resultado formalmente probado y verificado en C5-REAL. |
| **[Objetivo]** | Meta fundamental de representación o construcción de subcategorías. |
| **[Conjetura]** | Resultado cuantitativo o de separación esperado, aún pendiente de prueba formal. |

---

## I. DIAGRAMA DE INCLUSIÓN CATEGORIAL DE NIVELES

El eje estructural del programa se organiza mediante la cadena de inclusiones de subcategorías:

$$\mathbf{CompMAct}_M^{\mathcal{F}} \;\stackrel{j_2}{\hookrightarrow}\; \mathbf{CompMAct}_M \;\stackrel{j_1}{\hookrightarrow}\; \mathbf{MAct}_M$$

```text
Nivel 0 | Categoría Base de M-Actos [Definición]
--------
MAct_M (para monoide M fijo) o Fibración U: MAct -> Mon (si M varía)

Nivel 1 | Subcategoría de Restricciones Computacionales [Definición]
--------
CompMAct_M (Morfismos computables y restricciones de estado)

Nivel 2 | Subcategoría Fibrada [Definición]
--------
CompMAct_M^F (Estructura fibrada de predicados y preservación monoidal)

Nivel 3 | Descomposición Invariante & Observables [Definición]
--------
Propiedades F, I, S; Métrica μ; Presupuesto R_k; Coste derivado κ
```

---

## II. FIRMA ESTRUCTURAL CORE $\Sigma_{\text{Core}}$ Y PODA CONCEPTUAL

### 2.1 Firma Estructural Core **[Definición]**
El núcleo irreducible del programa viene dado por:

$$\Sigma_{\text{Core}} = (\otimes, I, \mathbf{Arr}(\mathcal{C}), \text{Pred}, \Box_t, \text{Cert}, \mu)$$

### 2.2 Poda de Primitivas y Aplazamiento Categorial
- **Purga de `Sync` del Núcleo:** La noción de sincronización temporal no forma parte del núcleo primario. Las regiones de conmutatividad local ($\mathrm{CommRegion}$) o protocolos de barrera se desvinculan del núcleo y se analizan en el **Apéndice A**.
- **Aplazamiento de Doble Categoría:** La estructura de doble categoría se aplaza explícitamente hasta que se demuestre la existencia de un segundo tipo de morfismo irreducible que induzca celdas cuadradas no degeneradas.

---

## III. PROPIEDADES ESTRUCTURALES CORE WELL-TYPED **[Definición]**

Dado un modelo $\mathcal{M} \in \mathbf{Mod}(\Sigma_{\text{Core}}, T)$ y un morfismo $\alpha: A \to B \in \mathrm{Mor}(\mathcal{C})$:

1. **Propiedad Fibrada ($F$):** $\alpha^*: \mathrm{Pred}(B) \to \mathrm{Pred}(A)$ admite adjunto a izquierda $\exists_\alpha \dashv \alpha^*$ satisfaciendo la condición de Beck-Chevalley sobre cuadrados cartesianos.
2. **Propiedad Monoidal Invariante ($I$):** Para todo par $P, Q \in \mathrm{Pred}(B)$, $\alpha^*(P \otimes_\text{fib} Q) \cong \alpha^*(P) \otimes_\text{fib} \alpha^*(Q)$ sobre la misma fibra de predicados.
3. **Conmutatividad Local ($\mathrm{CommRegion}$):** Para submonoides locales conmutativos, el cambio de base preserva la conmutatividad de las transiciones.

---

## IV. OBSERVABLES NUMÉRICOS $\mu_M$ Y PRESUPUESTO $R_k$ **[Definición]**

### 4.1 Métrica Morfismo-Nivel **[Definición]**
$$\mu_\mathcal{M}: \mathrm{Mor}(\mathcal{C}) \longrightarrow \mathbb{N}_\infty \qquad \mu_\mathcal{M}(\alpha) \triangleq \inf \{ \mathrm{ProofCost}(\pi) \mid \pi \in \mathrm{Cert}(\alpha) \}$$

### 4.2 Métrica Modelo-Nivel **[Definición]**
$$\mu(\mathcal{M}) \triangleq \sup_{\alpha \in \mathrm{Mor}(\mathcal{C})} \mu_\mathcal{M}(\alpha)$$

### 4.3 Predicado de Presupuesto Acotado $R_k$ **[Definición]**
$$R_k(\alpha) \iff \mu_\mathcal{M}(\alpha) \le k, \qquad (k \in \mathbb{N}_\infty)$$

Induciendo la familia de subcategorías: $\mathbf{CompMAct}_M(R_k)$.

---

## V. EL COMPLEJO SIMPLICIAL $\text{Compat}(\Omega)$ **[Definición]**

$$\text{Compat}(\Omega) \subseteq \mathcal{P}(\Omega) \setminus \{\emptyset\}$$

con vértices $\Omega = \{ F, I, \mathrm{CommRegion}, R_k \}$.

### 5.1 Lema de Hereditariedad (Down-set Invariant) **[Proposición 5.1]**
> **Proposición 5.1:** Para todo símplice $\sigma \in \text{Compat}(\Omega)$ y todo subconjunto no vacío $\tau \subseteq \sigma$, se cumple que $\tau \in \text{Compat}(\Omega)$.

*Demostración:* Relajar una restricción preserva la realizabilidad del modelo $M \models \tau$. Por lo tanto, $\text{Compat}(\Omega)$ es un **complejo simplicial estricto**. $\blacksquare$

---

## VI. RESULTADOS CORE Y ESTABILIDAD CATEGORIAL

### 6.1 Estabilidad de Subcategoría Computable **[Proposición 6.1 — Killer Theorem]**
> **Proposición 6.1:** Las restricciones computacionales sobre los morfismos de $M$-actos inducen una subcategoría propia $\mathbf{CompMAct}_M \subsetneq \mathbf{MAct}_M$ estable bajo isomorfismos computables.

### 6.2 Objetivo de Representación Categorial ($T_0$) **[Objetivo 0]**
> **Objetivo 0:** Demostrar formalmente la equivalencia de categorías:
> $$\mathbf{CompMAct}_M^{\mathcal{F}} \;\simeq\; \mathbf{CertCalc}(\mathcal{C})$$
> conectando la subcategoría fibrada con la categoría de cálculos composicionales de certificados sobre $\mathbf{Arr}(\mathcal{C})$.

---

## VII. TEORÍA DE COSTES UNIFICADA ($\mu, \kappa, \Delta_{\text{overhead}}$)

### 7.1 Coste Derivado de Extensión Conservativa ($\kappa$) **[Definición]**
$$\kappa(M) \triangleq \inf \{ \mu(E) \mid E \in \mathbf{CompMAct}_M^{\mathcal{F}} \text{ tal que } M \hookrightarrow_\text{fib} E \text{ es un embedding pleno} \}$$

### 7.2 Leyes Métricas de Fricción Síncrona $\Delta_{\text{overhead}}$ **[Axioma]**
1. **Nulidad en Identidad:** $\Delta_{\text{overhead}}(\mathrm{id}_A, \alpha) = \Delta_{\text{overhead}}(\alpha, \mathrm{id}_B) = 0$.
2. **Positividad Métrica:** $\Delta_{\text{overhead}}(\alpha, \beta) \ge 0$.
3. **Desigualdad Triangular:** $\Delta_{\text{overhead}}(\alpha, \gamma) \le \Delta_{\text{overhead}}(\alpha, \beta) + \Delta_{\text{overhead}}(\beta, \gamma)$.

---

## VIII. CONJETURAS Y SEPARACIÓN DE CATEGORÍAS

### 8.1 Conjetura T (Separación Computacional) **[Conjetura T]**
> **Conjetura T:** La inclusión $j_1: \mathbf{CompMAct}_M \hookrightarrow \mathbf{MAct}_M$ no admite adjunto a izquierda, demostrando que $\mathbf{CompMAct}_M \not\simeq \mathbf{MAct}_M$.

### 8.2 Conjetura $C_1$ (Jerarquía Estricta de Presupuesto) **[Conjetura $C_1$]**
> **Conjetura $C_1$:** Para $k_1 < k_2 < \infty$, la inclusión $\mathbf{CompMAct}_M(R_{k_1}) \subsetneq \mathbf{CompMAct}_M(R_{k_2})$ es estricta.

---

## IX. PREGUNTAS ABIERTAS

1. **Pregunta Abierta S:** ¿Existe una construcción explícita del funtor $F: \mathbf{CertCalc}(\mathcal{C}) \to \mathbf{CompMAct}_M^{\mathcal{F}}$ que garantice la equivalencia estricta sin hipótesis adicionales?
2. **Pregunta Abierta $\kappa$:** ¿Bajo qué condiciones exactas un $M$-acto computable admite una extensión conservativa con $\kappa(M) < \infty$?

---

## APÉNDICE A — POSIBLES NOCIONES DE SINCRONÍA

Con el fin de evitar que el núcleo de la teoría quede comprometido por definiciones provisionales de sincronización, se desvincula la sincronía del Núcleo Core y se evalúan cuatro nociones candidatas en este apéndice:

1. **Conmutatividad Local ($\mathrm{CommRegion}$):** Existencia de submonoides conmutativos $N \subseteq M$ donde las transiciones conmutan libremente.
2. **Sincronía por Barrera / Reloj ($\text{Sync}_{\text{barrier}}$):** Presencia de una fase global que fuerza el paso síncrono $local \to communication \to update$ (modelo BSP / Esterel).
3. **Causalidad Parcial ($\text{Sync}_{\text{causal}}$):** Relación de orden parcial de happened-before de Lamport sobre trazas de eventos.
4. **Convergencia Epistémica ($\text{Sync}_{\text{conv}}$):** Propiedad de alcanzar un estado global coherente tras un número finito de rondas de mensajes.

*Conclusión del Apéndice:* El Núcleo FISR-Core v16.0 depende únicamente de $\mathrm{CommRegion}$ (conmutatividad local). La selección entre las nociones 2, 3 o 4 se reserva para módulos de extensión específicos según el dominio de aplicación.

---

## X. REGISTRO DE TRACEABILIDAD BFT

```yaml
Claim: Poda del núcleo teórica v16.0: inclusión de subcategorías MAct, purga de Sync a Apéndice A y tipado estricto
Proof:
  Base: 0x9893c4484b3d30b91e428bc5c65fef56f2f0a1c7
  Range: [Sección_0, Apéndice_A]
  Confidence: C5-REAL
```
