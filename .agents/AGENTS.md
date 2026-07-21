# Structural Compatibility Complex & Proof-Theoretic Invariant Specification

**Title:** FISR Theory & Structural Compatibility Complex $\text{Compat}(\Omega)$  
**Classification:** C5 Proof-Theoretic Invariant Specification & Categorical Model Theory  
**Status:** Frozen Baseline Specification (v17.0 — Pruned Core & Inclusion Chain)

---

# 0. ALCANCE Y TAXONOMÍA LÓGICA

> **Alcance:** La teoría FISR no pretende caracterizar todas las categorías monoidales ni la totalidad de los sistemas concurrentes. Su objetivo es estudiar el espacio de modelos de acciones monoidales con predicados fibrados y certificabilidad observable bajo restricciones computacionales.

### Taxonomía de Estatus Lógico:
- **[Definición]**: Concepto formal, firma o categoría.
- **[Axioma]**: Hipótesis adoptada axiomáticamente en la teoría $T$.
- **[Proposición]**: Consecuencia directa de los axiomas.
- **[Teorema]**: Resultado formalmente demostrado en C5-REAL.
- **[Objetivo]**: Meta de representación o construcción de subcategorías.
- **[Conjetura]**: Resultado de separación esperado, aún no probado.

---

# 1. CADENA PRINCIPAL DE INCLUSIÓN CATEGORIAL

$$\mathbf{CompMAct}_M^{\mathcal{F}} \;\hookrightarrow\; \mathbf{CompMAct}_M \;\hookrightarrow\; \mathbf{MAct}_M \;\xrightarrow{U}\; \mathbf{Mon}$$

- **$\mathbf{MAct}_M$ [Definición]:** Categoría base de $M$-actos para un monoide $M$ dado (o la fibración $U: \mathbf{MAct} \to \mathbf{Mon}$ si $M$ varía).
- **$\mathbf{CompMAct}_M$ [Definición]:** Subcategoría de $M$-actos con morfismos computables y restricciones de estado ($E, P^+$).
- **$\mathbf{CompMAct}_M^{\mathcal{F}}$ [Definición]:** Subcategoría restringida con estructura de descomposición invariante no trivial $\mathcal{F}$.

---

# 2. CAPAS AXIOMÁTICAS CORE

### Capa A — Álgebra ($\Sigma_A$) [Axioma]
- $A_1$: $(\delta_1 \cdot \delta_2) \cdot \delta_3 = \delta_1 \cdot (\delta_2 \cdot \delta_3)$
- $A_2$: $e \cdot \delta = \delta \cdot e = \delta$
- $A_3$: $\alpha(e, s) = s$
- $A_4$: $\alpha(\delta_1 \cdot \delta_2, s) = \alpha(\delta_1, \alpha(\delta_2, s))$

### Capa B — Restricciones Computacionales [Definición]
- $E(S, \alpha)$: Acción total computable.
- $V(\delta, s, s')$: Verificador en $\text{PTIME}$.
- $P^+(S, \alpha)$: Representación inyectiva computable con imagen decidible.

### Capa C — Descomposición Invariante ($\mathcal{F}$) [Definición]
- Proyección $\pi: S \to B$ ($|B| \ge 2$) tal que $\pi(\alpha(\delta, s)) = h_\delta(\pi(s))$.

---

# 3. OBSERVABLES $\mu$ Y COSTE DERIVADO $\kappa$ WELL-TYPED

- **Métrica Morfismo-Nivel [Definición]:** $\mu_\mathcal{M}: \mathrm{Mor}(\mathcal{C}) \to \mathbb{N}_\infty$, $\mu_\mathcal{M}(\alpha) \triangleq \inf \{ \mathrm{ProofCost}(\pi) \mid \pi \in \mathrm{Cert}(\alpha) \}$.
- **Métrica Modelo-Nivel [Definición]:** $\mu(\mathcal{M}) \triangleq \sup_{\alpha \in \mathrm{Mor}(\mathcal{C})} \mu_\mathcal{M}(\alpha)$.
- **Coste de Extensión Conservativa ($\kappa$) [Definición]:** $\kappa(M) \triangleq \inf \{ \mu(E) \mid E \in \mathbf{CompMAct}_M^{\mathcal{F}}, \; M \hookrightarrow_\text{fib} E \}$.

---

# 4. TEOREMAS DEMOSTRADOS EN C5-REAL

- **Teorema 1 (Redundancia de $C$):** $C \equiv A_4$.
- **Teorema 2 (Separación Incondicional $E \not\vdash V$):** Verificación exponencial $O(2^{|\delta|} \cdot |s|)$ via Turing Machine execution step counter $T_U^{(n)}$.
- **Teorema 3 (Existencia vs Eficiencia $V \vdash E_{\text{exist}}, V \not\vdash E_{\text{efic}}$):** Demostrada la separación NP vs Búsqueda.
- **Teorema 4 (No-Descomposición Invariante):** Las acciones libres y transitivas rompen $\mathcal{F}(S, \alpha)$.
- **Teorema 5 (Estratificación Tripartita B):** Independencia mutua de $P^+$, $E$, y $V$.

---

# 5. ESTRUCTURA DEL DOCUMENTO (CON APÉNDICE A)

1. **Secciones I–VIII:** Núcleo de $M$-actos, subcategorías computables, teoremas 1-5, costes $\mu, \kappa$ y Conjetura T.
2. **Apéndice A — Posibles Nociones de Sincronía:** Comparación entre S1 ($\mathrm{CommRegion}$), S2 (Convergencia / Church-Rosser), S3 (Causalidad / Poset), y S4 (Disciplina Temporal / Reloj).
