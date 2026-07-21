# Structural Compatibility Complex & Proof-Theoretic Invariant Specification

**Title:** FISR Theory & Structural Compatibility Complex $\text{Compat}(\Omega)$  
**Classification:** C5 Proof-Theoretic Invariant Specification & Categorical Model Theory  
**Status:** Frozen Baseline Specification (v18.3 — Lawvere Enriched Metric & Extension/Repair Operator $\kappa$)

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
   $$|c_2 \circledast c_1| \le |c_1| + |c_2| + \delta_\circ(\alpha, \beta)$$

2. **Composición Monoidal ($\boxtimes$):**
   $$\boxtimes : \mathsf{Cert}(\alpha) \times \mathsf{Cert}(\beta) \longrightarrow \mathsf{Cert}(\alpha \otimes \beta)$$
   $$|c_1 \boxtimes c_2| \le |c_1| + |c_2| + \delta_\otimes(\alpha, \beta)$$

donde $|\cdot| : \mathrm{Mor}(\mathcal{P}) \to \overline{\mathbb{N}}$ es la valoración de coste monoidal laxa y $\delta_\circ(\alpha,\beta), \delta_\otimes(\alpha,\beta) \ge 0$ son las funciones de fricción sintáctica contextuales.

### Bloque Axiomático de Identidades
- **Axioma Id-1:** $\pi(\mathrm{id}_X^\mathcal{P}) = \mathrm{id}_X^\mathcal{C}$
- **Axioma Id-2:** $|\mathrm{id}_X^\mathcal{P}| = 0$
- **Proposición Id-3:** $\mu(\mathrm{id}_X^\mathcal{C}) = 0$  
  *Demostración:* Como $\mathrm{id}_X^\mathcal{P} \in \mathsf{Cert}(\mathrm{id}_X^\mathcal{C})$, $\mu(\mathrm{id}_X^\mathcal{C}) \le |\mathrm{id}_X^\mathcal{P}| = 0$. Puesto que $|\cdot| \in \overline{\mathbb{N}}$, $0 \le \mu(\mathrm{id}_X^\mathcal{C})$, luego $\mu(\mathrm{id}_X^\mathcal{C}) = 0$. $\blacksquare$

---

# 3. AXIOMA CORE-G ($\mathsf{Good} = \mathcal{P}$) Y ESTRUCTURA DE LAWVERE ($\mu$) [Definición]

> **Axioma Core-G:** En el núcleo FISR Certificate Calculus v0.1 toda evidencia perteneciente a $\mathcal{P}$ se considera, por definición, un certificado válido ($\mathsf{Good} = \mathcal{P}$).

Para toda métrica de coste observable con la convención de función total $\inf \varnothing = \infty$:
$$\mu(\alpha) \triangleq \inf_{c \in \mathsf{Cert}(\alpha)} |c|$$

- **Finitud y Dominios:** Distinción estricta entre $\mu(\alpha) < \infty$ (certificable) y $\mu(\alpha) = \infty$ (intratable).
- **Alcanzabilidad:** En $\overline{\mathbb{N}}$, todo conjunto no vacío de costes admite un mínimo alcanzable $c^* \in \mathsf{Cert}(\alpha)$ tal que $|c^*| = \mu(\alpha)$.
- **Estructura Categórica Enriquecida:** $(\mathcal{C}, \mu)$ constituye formalmente una **$(\overline{\mathbb{N}}, +, 0, \le)$-categoría enriquecida laxa (Lawvere Premetric)** con holgura de composición $\delta$.

---

# 4. PREDICADO MODULAR DE PRESUPUESTO $R_k^\mathcal{A}$ Y OPERADOR DE REPARACIÓN $\kappa$ [Definición]

Dada una familia distinguida de transiciones básicas $\mathcal{A}(M) \subseteq \mathrm{Mor}(\mathcal{C}_M)$:
$$R_k^\mathcal{A}(M) \iff \forall \alpha \in \mathcal{A}(M), \; \mu(\alpha) \le k$$

### Operador de Extensión / Reparación $\kappa$
El funcional $\kappa$ se define como el coste óptimo de reparación sobre la métrica $\mu$ para satisfacer la restricción de presupuesto $R$:
$$\kappa(\alpha, R) \triangleq \inf \{ \mu(e) \mid e \circ \alpha \models R \}$$

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
               │  Lawvere Metric μ  │
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

---

# 6. LEMA DE SEPARACIÓN DEL ÍNFIMO Y TEOREMA DE SUBADITIVIDAD [Teorema 1.1 - Probado]

**Lema 1.1 (Separación del Ínfimo):**  
Para cualesquiera subconjuntos no vacíos $A, B \subseteq \overline{\mathbb{N}}$, se verifica:
$$\inf(A + B) = \inf(A) + \inf(B) \qquad \text{donde } A+B \triangleq \{a+b \mid a \in A, b \in B\}$$

**Teorema 1.1 (Subaditividad de $\mu$):**  
Bajo el sistema de certificados $\mathcal{P} \xrightarrow{\pi} \mathcal{C}$ (Opción A), la valoración laxa $|\cdot|$ y el Axioma Core-G ($\mathsf{Good} = \mathcal{P}$), para todo par de transiciones compuestas se verifica:

1. **Subaditividad Secuencial:**  
   $$\mu(\beta \circ \alpha) \le \mu(\alpha) + \mu(\beta) + \delta_\circ(\alpha, \beta)$$
2. **Subaditividad Monoidal:**  
   $$\mu(\alpha \otimes \beta) \le \mu(\alpha) + \mu(\beta) + \delta_\otimes(\alpha, \beta)$$

*Demostración:* Aplicando el Lema 1.1 de separación del ínfimo sobre el producto cartesiano de fibras $\mathsf{Cert}(\alpha) \times \mathsf{Cert}(\beta)$ y la evaluación $c_2 \circledast c_1 \in \mathsf{Cert}(\beta \circ \alpha)$, obtenemos $\mu(\beta \circ \alpha) \le \inf_{c_1, c_2} (|c_1| + |c_2| + \delta_\circ) = \inf(c_1) + \inf(c_2) + \delta_\circ = \mu(\alpha) + \mu(\beta) + \delta_\circ(\alpha, \beta)$. Analogamente para $\boxtimes$. $\blacksquare$




