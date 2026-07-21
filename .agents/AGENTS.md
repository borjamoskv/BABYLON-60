# Structural Compatibility Complex & Proof-Theoretic Invariant Specification

**Title:** FISR Theory & Structural Compatibility Complex $\text{Compat}(\Omega)$  
**Classification:** C5 Proof-Theoretic Invariant Specification & Categorical Model Theory  
**Status:** Frozen Baseline Specification (v16.0 — Pruned Core & Inclusion Chain)

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

$$\mathbf{CompMAct}_M^{\mathcal{F}} \;\hookrightarrow\; \mathbf{CompMAct}_M \;\hookrightarrow\; \mathbf{MAct}_M$$

- **$\mathbf{MAct}_M$ [Definición]:** Categoría base de $M$-actos para un monoide $M$ dado (o la fibración $U: \mathbf{MAct} \to \mathbf{Mon}$ si $M$ varía).
- **$\mathbf{CompMAct}_M$ [Definición]:** Subcategoría de $M$-actos con morfismos computables y restricciones de estado.
- **$\mathbf{CompMAct}_M^{\mathcal{F}}$ [Definición]:** Subcategoría restringida con estructura fibrada de predicados $F$ e invarianza monoidal $I$.

---

# 2. FIRMA ESTRUCTURAL CORE $\Sigma_{\text{Core}}$ (PODA ESTRUCTURAL)

$$\Sigma_{\text{Core}} = (\otimes, I, \mathbf{Arr}(\mathcal{C}), \text{Pred}, \Box_t, \text{Cert}, \mu)$$

### Poda de Primitivas:
- **`Sync` Purgado del Núcleo:** La sincronía temporal no es una primitiva del núcleo; las regiones conmutativas locales ($\mathrm{CommRegion}$) o protocolos de barrera se posponen al **Apéndice A**.
- **Doble Categoría Aplazada:** La estructura de doble categoría se aplaza hasta la demostración de 2-celdas cuadradas no degeneradas.

---

# 3. OBSERVABLES $\mu$ Y COSTE DERIVADO $\kappa$ WELL-TYPED

- **Métrica Morfismo-Nivel [Definición]:** $\mu_\mathcal{M}: \mathrm{Mor}(\mathcal{C}) \to \mathbb{N}_\infty$, $\mu_\mathcal{M}(\alpha) \triangleq \inf \{ \mathrm{ProofCost}(\pi) \mid \pi \in \mathrm{Cert}(\alpha) \}$.
- **Métrica Modelo-Nivel [Definición]:** $\mu(\mathcal{M}) \triangleq \sup_{\alpha \in \mathrm{Mor}(\mathcal{C})} \mu_\mathcal{M}(\alpha)$.
- **Coste de Extensión Conservativa ($\kappa$) [Definición]:** $\kappa(M) \triangleq \inf \{ \mu(E) \mid E \in \mathbf{CompMAct}_M^{\mathcal{F}}, \; M \hookrightarrow_\text{fib} E \}$.

---

# 4. RESULTADOS Y PREGUNTAS ABIERTAS

- **Proposición 1.1 (Estabilidad Computacional):** Las restricciones computacionales inducen una subcategoría propia $\mathbf{CompMAct}_M$ estable bajo isomorfismos computables.
- **Objetivo 0 (Representación):** $\mathbf{CompMAct}_M^{\mathcal{F}} \simeq \mathbf{CertCalc}(\mathcal{C})$.
- **Conjetura T (Separación Computacional):** $\mathbf{CompMAct}_M \not\simeq \mathbf{MAct}_M$.
- **Pregunta Abierta S:** Construcción explícita del funtor $F$ para equivalencia estricta.

---

# 5. ESTRUCTURA DEL DOCUMENTO (CON APÉNDICE A)

1. **Secciones I–VIII:** Núcleo de $M$-actos, subcategorías computables, costes $\mu, \kappa$ y conjeturas.
2. **Apéndice A — Posibles Nociones de Sincronía:** Comparación entre conmutatividad local, convergencia, causalidad y disciplinas temporales.
