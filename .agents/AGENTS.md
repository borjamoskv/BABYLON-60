# Structural Compatibility Complex & Proof-Theoretic Invariant Specification

**Title:** FISR Theory & Structural Compatibility Complex $\text{Compat}(\Omega)$  
**Classification:** C5 Proof-Theoretic Invariant Specification & Categorical Model Theory  
**Status:** Frozen Baseline Specification (v18.1 — Refined Certificate Calculus & Metric Foundations)

---

# 0. ALCANCE Y TAXONOMÍA LÓGICA

> **Alcance:** La teoría FISR no pretende caracterizar todas las categorías monoidales ni la totalidad de los sistemas concurrentes. Su objetivo es estudiar el espacio de modelos de acciones monoidales con predicados fibrados y certificabilidad observable bajo restricciones computacionales.

---

# 1. CATEGORÍA DE CERTIFICADOS Y FUNTOR $\pi$ [Opción A - Definición]

Un sistema de certificados sobre una categoría monoidal $\mathcal{C}$ consiste en una categoría monoidal $\mathcal{P}$ provista de los mismos objetos que $\mathcal{C}$ y un funtor monoidal estricto:
$$\pi : \mathcal{P} \longrightarrow \mathcal{C}$$
que es la **identidad sobre objetos** ($\mathrm{Id}_{\mathrm{Ob}}$). 

Para cada transición $\alpha: X \to Y$ en $\mathcal{C}$, la fibra de evidencias es:
$$\mathsf{Cert}(\alpha) \triangleq \{ c \in \mathrm{Mor}(\mathcal{P})(X,Y) \mid \pi(c) = \alpha \}$$

---

# 2. ÁLGEBRA DE COMPOSICIÓN Y ESTRUCTURA DE COSTE [Definición & Axioma]

El funtor $\mathrm{Cert}: \mathbf{Arr}(\mathcal{C}) \to \mathbf{Set}$ está equipado con una **álgebra composicional** provista de los operadores binarios:

1. **Composición Secuencial ($\circledast$):**
   $$\circledast : \mathsf{Cert}(\alpha) \times \mathsf{Cert}(\beta) \longrightarrow \mathsf{Cert}(\beta \circ \alpha)$$
   $$|c_2 \circledast c_1| \le |c_1| + |c_2| + \delta_\circ$$

2. **Composición Monoidal ($\boxtimes$):**
   $$\boxtimes : \mathsf{Cert}(\alpha) \times \mathsf{Cert}(\beta) \longrightarrow \mathsf{Cert}(\alpha \otimes \beta)$$
   $$|c_1 \boxtimes c_2| \le |c_1| + |c_2| + \delta_\otimes$$

donde $|\cdot| : \mathrm{Mor}(\mathcal{P}) \to \overline{\mathbb{N}}$ es la valoración de coste monoidal laxa.

> **Nota de Enriquecimiento:** La valoración de coste $|\cdot|$ podrá reinterpretarse posteriormente como una estructura de enriquecimiento monoidal (o categoría graduada por costes); en el núcleo sólo se exige una valoración monoidal laxa.

---

# 3. AXIOMA CORE-G ($\mathsf{Good} = \mathcal{P}$) Y FUNDAMENTOS MÉTRICOS ($\mu, \kappa$) [Definición]

> **Axioma Core-G:** En el núcleo FISR Certificate Calculus v0.1 toda evidencia perteneciente a $\mathcal{P}$ se considera, por definición, un certificado válido ($\mathsf{Good} = \mathcal{P}$).
>
> *Nota de Diseño:* Las extensiones podrán introducir una categoría más amplia $\mathcal{P}_{\mathrm{raw}}$ y un reflector o subcategoría plena $\mathcal{P} \hookrightarrow \mathcal{P}_{\mathrm{raw}}$, recuperando una noción de "certificado bruto" cuando sea necesario.

Para toda métrica de coste observable $\mu(\alpha) \triangleq \inf \{ |c| \mid c \in \mathsf{Cert}(\alpha) \}$:

- **Finitud:** Distinción estricta entre $\mu(\alpha) < \infty$ (certificable) y $\mu(\alpha) = \infty$ (intratable).
- **Alcanzabilidad:** En $\overline{\mathbb{N}}$, todo conjunto no vacío de costes admite un mínimo alcanzable $c^* \in \mathsf{Cert}(\alpha)$ tal que $|c^*| = \mu(\alpha)$.

---

# 4. PREDICADO MODULAR DE PRESUPUESTO $R_k^\mathcal{A}$ [Definición]

Dada una familia distinguida de transiciones básicas $\mathcal{A}(M) \subseteq \mathrm{Mor}(\mathcal{C}_M)$ (generadores, irreducibles, primitivas o observables), el predicado de presupuesto $R_k^\mathcal{A}$ se define como:
$$R_k^\mathcal{A}(M) \iff \forall \alpha \in \mathcal{A}(M), \; \mu(\alpha) \le k$$

---

# 5. ARQUITECTURA MODULAR Y MARCO PRF

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

- **Soundness Estructural [Objetivo 5.1 / PRF-S]:** $\text{Certificación } k \implies M \models FISR_k^\mathcal{A}$.
- **Completitud Relativa [Objetivo 5.2 / PRF-C]:** $M \models FISR_k^\mathcal{A} \implies \text{Existe certificación } k$ bajo hipótesis de fibra completas.

---

# 6. TEOREMA DE SUBADITIVIDAD DE LA MÉTRICA $\mu$ [Teorema 1.1 - Probado]

**Teorema 1.1 (Subaditividad de $\mu$):**  
Bajo el sistema de certificados $\mathcal{P} \xrightarrow{\pi} \mathcal{C}$ (Opción A), la valoración laxa $|\cdot|$ y el Axioma Core-G ($\mathsf{Good} = \mathcal{P}$), para todo par de transiciones compuestas se verifica:

1. **Subaditividad Secuencial:**  
   $$\mu(\beta \circ \alpha) \le \mu(\alpha) + \mu(\beta) + \delta_\circ$$
2. **Subaditividad Monoidal:**  
   $$\mu(\alpha \otimes \beta) \le \mu(\alpha) + \mu(\beta) + \delta_\otimes$$

*Demostración:* Si $\mu(\alpha) = \infty$ o $\mu(\beta) = \infty$, el resultado es trivial. Si $\mu(\alpha), \mu(\beta) < \infty$, por alcanzabilidad existen $c_1^* \in \mathsf{Cert}(\alpha)$ y $c_2^* \in \mathsf{Cert}(\beta)$ con $|c_1^*| = \mu(\alpha)$ y $|c_2^*| = \mu(\beta)$. Los operadores $\circledast$ y $\boxtimes$ producen $c_2^* \circledast c_1^* \in \mathsf{Cert}(\beta \circ \alpha)$ y $c_1^* \boxtimes c_2^* \in \mathsf{Cert}(\alpha \otimes \beta)$. Al aplicar los axiomas de coste $|c_2^* \circledast c_1^*| \le \mu(\alpha) + \mu(\beta) + \delta_\circ$ y $|c_1^* \boxtimes c_2^*| \le \mu(\alpha) + \mu(\beta) + \delta_\otimes$, el ínfimo $\mu$ satisface ambas acotaciones superiores. $\blacksquare$


