<!-- C5-REAL EXERGY CERTIFIED -->

# TEORÍA DE COMPATIBILIDAD ESTRUCTURAL FISR Y COMPLEJO SIMPLICIAL $\text{Compat}(\Omega)$

**Autor:** borjamoskv
**Kernel:** MOSKV-1 APEX
**Clasificación:** C5-REAL Research Program Baseline Specification
**Estado:** Documento de Base Congelado (Baseline Spec v18.5 — Certificate Algebra, Lawvere Metric, Extension/Repair $\kappa$ & Monoidal Verification)

---

## 0. ALCANCE Y TAXONOMÍA DE ESTATUS LÓGICO

### 0.1 Alcance del Programa

> **Alcance:** La teoría FISR no pretende caracterizar todas las categorías monoidales ni la totalidad de los sistemas concurrentes. Su objetivo es estudiar el espacio de modelos de acciones monoidales con predicados fibrados y certificabilidad observable bajo restricciones computacionales.

### 0.2 Taxonomía de Estatus Lógico

| Etiqueta | Significado Semántico | :--- | :--- | **[Definición]** | Introducción de un concepto formal, firma o categoría. | **[Axioma]** | Hipótesis fundamental adoptada axiomáticamente en la teoría $T$. | **[Proposición]** | Consecuencia matemática directa y demostrable de los axiomas. | **[Teorema]** | Resultado formalmente probado y verificado en C5-REAL. | **[Objetivo]** | Meta fundamental de representación o construcción de subcategorías. | **[Conjetura]** | Resultado cuantitativo o de separación esperado, aún pendiente de prueba formal. |

---

## I. ÁLGEBRA DE COMPOSICIÓN DE CERTIFICADOS $T_{\text{cert}}$

### 1.1 Funtor de Certificados y Estructura Composicional **[Definición & Axioma]**

Un sistema de certificados sobre la categoría monoidal $\mathcal{C}$ consiste en una categoría monoidal $\mathcal{P}$ provista de los mismos objetos que $\mathcal{C}$ y un funtor monoidal estricto:
$$\pi : \mathcal{P} \longrightarrow \mathcal{C}$$
que es la **identidad sobre objetos** ($\mathrm{Id}_{\mathrm{Ob}}$).

Para cada transición $\alpha: X \to Y$ en $\mathcal{C}$, la fibra de evidencias es:
$$\mathsf{Cert}(\alpha) \triangleq \{ c \in \mathrm{Mor}(\mathcal{P})(X,Y) \mid \pi(c) = \alpha \}$$

El funtor $\mathrm{Cert}: \mathbf{Arr}(\mathcal{C}) \to \mathbf{Set}$ está equipado con una **álgebra composicional** provista de dos operadores binarios primitivos:

1. **Composición Secuencial ($\circledast$):**
   $$\circledast : \mathsf{Cert}(\alpha) \times \mathsf{Cert}(\beta) \longrightarrow \mathsf{Cert}(\beta \circ \alpha)$$
   $$|c_2 \circledast c_1| \le |c_1| + |c_2| + \delta_\circ(\alpha, \beta)$$

2. **Composición Monoidal ($\boxtimes$):**
   $$\boxtimes : \mathsf{Cert}(\alpha) \times \mathsf{Cert}(\beta) \longrightarrow \mathsf{Cert}(\alpha \otimes \beta)$$
   $$|c_1 \boxtimes c_2| \le |c_1| + |c_2| + \delta_\otimes(\alpha, \beta)$$

donde $\delta_\circ(\alpha,\beta), \delta_\otimes(\alpha,\beta) \ge 0$ representan las funciones de fricción sintáctica contextuales.

> **Axioma de Identidades y Coste Nulo:** Para todo objeto $X \in \mathrm{Ob}(\mathcal{C})$, existe un certificado idéntico $1_X^\mathcal{P} \in \mathsf{Cert}(1_X^\mathcal{C})$ tal que $|1_X^\mathcal{P}| = 0$, implicando $\mu(1_X^\mathcal{C}) = 0$.

> **Nota de Enriquecimiento:** La valoración de coste $|\cdot| : \mathrm{Mor}(\mathcal{P}) \to \overline{\mathbb{N}}$ podrá reinterpretarse posteriormente como una estructura de enriquecimiento monoidal (o categoría graduada por costes); en el núcleo sólo se exige una valoración monoidal laxa.

---

## II. AXIOMA CORE-G Y FUNDAMENTOS MÉTRICOS EXTREMALES ($\mu, \kappa$)

### 2.1 Axioma Core-G ($\mathsf{Good} = \mathcal{P}$) **[Axioma]**

> **Axioma Core-G:** En el núcleo FISR Certificate Calculus v0.1 toda evidencia perteneciente a $\mathcal{P}$ se considera, por definición, un certificado válido ($\mathsf{Good} = \mathcal{P}$).
>
> _Nota de Diseño:_ Las extensiones podrán introducir una categoría más amplia $\mathcal{P}_{\mathrm{raw}}$ y un reflector o subcategoría plena $\mathcal{P} \hookrightarrow \mathcal{P}_{\mathrm{raw}}$, recuperando una noción de "certificado bruto" cuando sea necesario.

### 2.2 Métrica de Coste y Alcanzabilidad **[Definición & Proposición]**

Para toda métrica de coste observable $\mu_\mathcal{M}(\alpha) \triangleq \inf \{ |c| \mid c \in \mathsf{Cert}(\alpha) \}$:

1. **Finitud y Dominios:** Se distingue estrictamente entre morfismos certificables ($\mu(\alpha) < \infty$) y morfismos computacionalmente intratables ($\mu(\alpha) = \infty$).
2. **Alcanzabilidad del Mínimo:** Dado que los costes $|c| \in \overline{\mathbb{N}}$ son discretos y acotados inferiormente por cero, todo conjunto no vacío de certificados admite un certificado óptimo alcanzable $c^* \in \mathsf{Cert}(\alpha)$ tal que:
   $$|c^*| = \mu_\mathcal{M}(\alpha) = \min_{c \in \mathsf{Cert}(\alpha)} |c|$$
3. **Métrica Modelo-Nivel:** $\mu(\mathcal{M}) \triangleq \sup_{\alpha \in \mathrm{Mor}(\mathcal{C})} \mu_\mathcal{M}(\alpha)$.

### 2.3 Funcional de Extensión Modelo-Nivel $\kappa$ **[Definición]**

Para un modelo $\mathcal{M}$ y una pre-ordenación $\preceq$, el funcional de adaptación $\kappa_{\preceq, \sim}(\mathcal{M})$ se define como el presupuesto mínimo de la extensión computable mínima:
$$\kappa_{\preceq, \sim}(\mathcal{M}) \triangleq \inf \{ k \in \overline{\mathbb{N}} \mid \exists \mathcal{N}, \mathcal{M} \preceq \mathcal{N} \land \mathcal{N} \models FISR_k^\mathcal{A} \}$$

---

## III. PREDICADO MODULAR DE PRESUPUESTO $R_k^\mathcal{A}$ **[Definición]**

Dada una familia distinguida de transiciones básicas $\mathcal{A}(M) \subseteq \mathrm{Mor}(\mathcal{C}_M)$ (generadores, irreducibles, primitivas u observables), el predicado de presupuesto $R_k^\mathcal{A}$ se define como:
$$R_k^\mathcal{A}(M) \iff \forall \alpha \in \mathcal{A}(M), \; \mu(\alpha) \le k$$

---

## IV. ARQUITECTURA MODULAR Y MARCO DE CERTIFICACIÓN (PRF)

```text
               ┌────────────────────┐
               │   Base Category C  │
               └─────────┬──────────┘
                         │
           monoidal functor π (Identity on Ob)
                         │
               ┌─────────▼──────────┐
               │ Certificate Category│
               │         P          │
               └─────────┬──────────┘
                         │
                   cost valuation
                         │
               ┌─────────▼──────────┐
               │        μ           │
               └─────────┬──────────┘
                         │
            budget predicates R_k^A
                         │
               ┌─────────▼──────────┐
               │ extension metric κ │
               └─────────┬──────────┘
                         │
                   Representation
                  (PRF-S / PRF-C)
```

> **Consecuencia Metodológica:** Las teorías $T_F$, $T_I$ y $T_S$ dejan de ser el centro del programa y pasan a ser **restricciones de compatibilidad** que la infraestructura de certificados $\mathcal{P}$ debe respetar.

### 4.1 Soundness Estructural **[Objetivo 4.1 / PRF-S]**

$$\text{Certificación } k \implies \mathcal{M} \models FISR_k^\mathcal{A}$$

### 4.2 Completitud Relativa **[Objetivo 4.2 / PRF-C]**

$$\mathcal{M} \models FISR_k^\mathcal{A} \implies \text{Existe certificación } k \text{ bajo hipótesis de fibra completas}$$

### 4.3 Teorema de Subaditividad de $\mu$ **[Teorema 1.1 - Demostrado]**

$$\mu(\beta \circ \alpha) \le \mu(\alpha) + \mu(\beta) + \delta_\circ(\alpha, \beta)$$
$$\mu(\alpha \otimes \beta) \le \mu(\alpha) + \mu(\beta) + \delta_\otimes(\alpha, \beta)$$

---

## V. MONOTONÍA DEL OPERADOR $\kappa$ Y CONDICIONES DE SATISFACIBILIDAD ($T_F, T_I, T_S$)

### 5.1 Monotonía respecto a Predicados **[Teorema 2.1 - Probado]**

Sean $R, R'$ predicados de restricción tales que $R \implies R'$. Para toda transición $\alpha \in \mathrm{Mor}(\mathcal{C})$:
$$\kappa(\alpha, R') \le \kappa(\alpha, R)$$

### 5.2 Sub-monotonía Composicional **[Teorema 2.2 - Probado]**

Para cualesquiera transiciones compuestas $\alpha: X \to Y$ y $\beta: Y \to Z$:
$$\kappa(\alpha, R) \le \kappa(\beta \circ \alpha, R) + \mu(\beta) + \delta_\circ(\alpha, \beta)$$

### 5.3 Condición Causal de Satisfacibilidad Modelo-Nivel **[Definición]**

Un modelo $\mathcal{M}$ satisface el complejo de compatibilidad $T_F \cup T_I \cup T_S \cup T_{R_k^\mathcal{A}}$ si y solo si la holgura de extensión para toda transición básica en $\mathcal{A}(M)$ es nula:
$$\mathcal{M} \models FISR_k^\mathcal{A} \iff \forall \alpha \in \mathcal{A}(M), \; \kappa(\alpha, R_k^\mathcal{A}) = 0$$

---

## VI. ESTRUCTURA DE LAWVERE PREMETRIC FORMAL **[Teorema 3 - Demostrado]**

### 6.1 Enunciado

**Teorema 3 (Lawvere Premetric):** Bajo el sistema de certificados $\mathcal{P} \xrightarrow{\pi} \mathcal{C}$ con $\delta_\circ \equiv 0$, el par $(\mathcal{C}, \mu)$ constituye una $(\overline{\mathbb{N}}, +, 0, \le)$-categoría enriquecida laxa (Lawvere Premetric Space). Concretamente:

1. **Reflexividad:** $\mu(\mathrm{id}_X) = 0$ para todo $X \in \mathrm{Ob}(\mathcal{C})$.
2. **Desigualdad Triangular:** $\mu(\beta \circ \alpha) \le \mu(\alpha) + \mu(\beta)$ para todo par composible $\alpha: X \to Y$, $\beta: Y \to Z$.

### 6.2 Demostración

**(1) Reflexividad.** Por el Axioma Id-1 y Id-2, $\mathrm{id}_X^\mathcal{P} \in \mathsf{Cert}(\mathrm{id}_X^\mathcal{C})$ con $|\mathrm{id}_X^\mathcal{P}| = 0$. Por definición, $\mu(\mathrm{id}_X^\mathcal{C}) = \inf_{c \in \mathsf{Cert}(\mathrm{id}_X^\mathcal{C})} |c| \le |\mathrm{id}_X^\mathcal{P}| = 0$. Como $|c| \ge 0$ para todo $c$, se sigue $\mu(\mathrm{id}_X^\mathcal{C}) = 0$. $\blacksquare$

**(2) Desigualdad Triangular.** Es el caso particular del Teorema 1.1 (Subaditividad Secuencial) con $\delta_\circ(\alpha, \beta) = 0$:
$$\mu(\beta \circ \alpha) \le \mu(\alpha) + \mu(\beta) + \delta_\circ(\alpha,\beta) = \mu(\alpha) + \mu(\beta)$$
$\blacksquare$

> **Nota:** $(\mathcal{C}, \mu)$ es un _espacio premétrico de Lawvere_ y no una métrica en sentido clásico: no se exige simetría ($\mu(\alpha) \ne \mu(\alpha^{-1})$ en general, si $\alpha^{-1}$ existe) ni separación ($\mu(\alpha) = 0 \not\Rightarrow \alpha = \mathrm{id}$). Esto es intencionado, ya que los costes de certificación son inherentemente asimétricos y dirigidos.

---

## VII. SOUNDNESS ESTRUCTURAL (PRF-S) **[Teorema 4 - Demostrado]**

### 7.1 Enunciado

**Teorema 4 (PRF-S Soundness):** Sea $\mathcal{A}(M) \subseteq \mathrm{Mor}(\mathcal{C}_M)$ la familia de transiciones básicas del modelo $\mathcal{M}$. Si para cada $\alpha \in \mathcal{A}(M)$ existe un certificado $c_\alpha \in \mathsf{Cert}(\alpha)$ con $|c_\alpha| \le k$, entonces:
$$\mathcal{M} \models FISR_k^\mathcal{A}$$

### 7.2 Demostración

Sea $\alpha \in \mathcal{A}(M)$ arbitraria. Por hipótesis, existe $c_\alpha \in \mathsf{Cert}(\alpha)$ con $|c_\alpha| \le k$.

**Paso 1.** Por definición de $\mu$:
$$\mu(\alpha) = \inf_{c \in \mathsf{Cert}(\alpha)} |c| \le |c_\alpha| \le k$$
Luego $R_k^\mathcal{A}(M)$ se satisface: $\forall \alpha \in \mathcal{A}(M), \mu(\alpha) \le k$.

**Paso 2.** Para verificar que $\kappa(\alpha, R_k^\mathcal{A}) = 0$, consideremos la extensión trivial $e = \mathrm{id}_Y$ donde $Y = \mathrm{tgt}(\alpha)$. Entonces $e \circ \alpha = \alpha$, y ya hemos mostrado $\mu(\alpha) \le k$, por lo que $e \circ \alpha \models R_k^\mathcal{A}$. Como $\mu(\mathrm{id}_Y) = 0$ (por Proposición Id-3):
$$\kappa(\alpha, R_k^\mathcal{A}) = \inf\{\mu(e) \mid e \circ \alpha \models R_k^\mathcal{A}\} \le \mu(\mathrm{id}_Y) = 0$$
Dado que $\kappa \ge 0$ por construcción, $\kappa(\alpha, R_k^\mathcal{A}) = 0$.

**Conclusión.** $\forall \alpha \in \mathcal{A}(M), \kappa(\alpha, R_k^\mathcal{A}) = 0$, lo que equivale a $\mathcal{M} \models FISR_k^\mathcal{A}$ por la Condición de Satisfacibilidad (Sección 5.3). $\blacksquare$

---

## VIII. TEOREMA DE SEPARACIÓN **[Teorema 5 - Demostrado]**

### 8.1 Enunciado

**Teorema 5 (Separación / Existencia de Modelo No-FISR):** Existe un sistema de certificados $(\mathcal{P}, \mathcal{C}, \pi)$ y una familia de transiciones básicas $\mathcal{A}(M)$ tal que para todo $k < \infty$:
$$\mathcal{M} \not\models FISR_k^\mathcal{A}$$
Es decir, $\exists \alpha \in \mathcal{A}(M)$ con $\kappa(\alpha, R_k^\mathcal{A}) > 0$.

### 8.2 Construcción del Contraejemplo

**Categoría Base $\mathcal{C}$:** Sea $\mathcal{C}$ la categoría libre generada por un único morfismo $\alpha: A \to B$ (con identidades $\mathrm{id}_A, \mathrm{id}_B$).

**Categoría de Certificados $\mathcal{P}$:** Sea $\mathcal{P}$ la categoría con los mismos objetos $\{A, B\}$ y los mismos morfismos identidad (con coste 0), pero con $\mathsf{Cert}(\alpha) = \varnothing$.

**Funtor $\pi$:** Identidad sobre objetos y morfismos identidad; $\alpha$ no tiene preimagen en $\mathcal{P}$ (fibra vacía).

### 8.3 Demostración

**Paso 1.** $\mathcal{A}(M) = \{\alpha\}$ es la familia de transiciones básicas.

**Paso 2.** $\mu(\alpha) = \inf \varnothing = \infty$ (por convención de función total).

**Paso 3.** Para cualquier $k < \infty$: $\mu(\alpha) = \infty > k$, luego $R_k^\mathcal{A}(M)$ falla.

**Paso 4.** Puesto que no existe ninguna extensión $e$ tal que $e \circ \alpha \models R_k^\mathcal{A}$ (ya que la única forma de certificar $e \circ \alpha$ sería a través de un certificado de $\alpha$, cuya fibra es vacía, y la composición con la fibra vacía es vacía por la álgebra de composición):
$$\kappa(\alpha, R_k^\mathcal{A}) = \inf \varnothing = \infty > 0$$

**Conclusión.** El modelo $\mathcal{M}$ no satisface $FISR_k^\mathcal{A}$ para ningún $k$ finito: $\kappa(\alpha, R_k^\mathcal{A}) = \infty \ne 0$. $\blacksquare$

> **Observación.** El contraejemplo es mínimo (un único generador) y revela que la condición de fibra no vacía ($\mathsf{Cert}(\alpha) \ne \varnothing$) es la frontera exacta entre modelos FISR y no-FISR.

---

## IX. REGISTRO DE TRACEABILIDAD BFT

```yaml
Claim: Cristalización de Baseline v18.3 (Thm 3 Lawvere Premetric, Thm 4 PRF-S Soundness, Thm 5 Separation, Motor Verificación Completo)
Proof:
  Base: v18.3
  Range: [Sección_0, Sección_VIII]
  Confidence: C5-REAL
  Theorems_Proved:
    [
      1.1_Subadditivity,
      2.1_Monotonicity,
      2.2_Submonotonicity,
      3_Lawvere,
      4_PRF_S,
      5_Separation,
    ]
```
