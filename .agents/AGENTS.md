# Structural Compatibility Complex & Proof-Theoretic Invariant Specification

**Title:** FISR Theory & Structural Compatibility Complex $\text{Compat}(\Omega)$  
**Classification:** C5 Proof-Theoretic Invariant Specification & Categorical Model Theory  
**Status:** Frozen Baseline Specification (v15.0 — Frozen Research Program)

---

# 0. ALCANCE Y TAXONOMÍA LÓGICA

> **Alcance:** La teoría FISR no pretende caracterizar todas las categorías monoidales, todos los sistemas concurrentes ni todas las lógicas de programas. Su objetivo es estudiar el espacio de modelos que admiten simultáneamente una estructura fibrada de predicados, una disciplina de aislamiento composicional, una modalidad síncrona y un cálculo composicional de certificados con coste observable.

### Taxonomía de Estatus Lógico:
- **[Definición]**: Introducción de un concepto formal o signatura.
- **[Axioma]**: Hipótesis adoptada axiomáticamente en la teoría $T$.
- **[Proposición]**: Consecuencia directa demostrable de los axiomas.
- **[Teorema]**: Resultado formalmente demostrado en el entorno C5-REAL.
- **[Objetivo]**: Meta de representación o construcción de modelos del programa.
- **[Conjetura]**: Resultado cuantitativo o de separación esperado, aún no probado.

---

# 1. NÚCLEO FISR-CORE VS EXTENSIONES (ESTRATIFICACIÓN P0)

$$\begin{array}{rll}
\mathbf{Nivel\;0 \; [Definición]} & \text{Categoría Monoidal Base} & \mathcal{C} = (\mathcal{C}, \otimes, I) \\
\mathbf{Nivel\;1 \; [Definición]} & \text{Firma Estructural Core } \Sigma & \Sigma = (\otimes, I, \mathbf{Arr}(\mathcal{C}), \text{Pred}, \Box_t, \text{Cert}, \mu) \\
\mathbf{Nivel\;2 \; [Axioma]} & \text{Leyes / Ecuaciones } T & \text{Preservación Monoidal, Beck-Chevalley, Operador Interior } \Box_t P \le P \\
\mathbf{Nivel\;3 \; [Definición]} & \text{Propiedades / Observables } \Omega & F, I, S \text{ (Propiedades); } \mu, R_k \text{ (Observables / Presupuestos)}
\end{array}$$

### 1.1 Funtor de Certificados Core [Definición]
$$\mathrm{Cert}: \mathbf{Arr}(\mathcal{C}) \longrightarrow \mathbf{Set}$$

---

# 2. PROPIEDADES ESTRUCTURALES CORE [Definición]

- **Propiedad Fibrada ($F$):** $\alpha^*: \mathrm{Pred}(B) \to \mathrm{Pred}(A)$ admite adjunto a izquierda $\exists_\alpha \dashv \alpha^*$.
- **Propiedad Monoidal Invariante ($I$):** Para todo $P, Q \in \mathrm{Pred}(B)$, $\alpha^*(P \otimes_\text{fib} Q) \cong \alpha^*(P) \otimes_\text{fib} \alpha^*(Q)$.
- **Propiedad Síncrona ($S$):** $\alpha^*(\Box_t P) = \Box_t (\alpha^* P)$ con $\Box_t P \le P$.

---

# 3. COMPLEJO SIMPLICIAL $\text{Compat}(\Omega)$ Y FILTRACIÓN $k$ [Definición & Objetivo]

$$\text{Compat}(\Omega) \subseteq \mathcal{P}(\Omega) \setminus \{\emptyset\}$$

- **Lema Simplicial (Down-set Invariant) [Proposición 3.1]:**
  $$\sigma \in \text{Compat}(\Omega) \land \tau \subseteq \sigma \implies \tau \in \text{Compat}(\Omega)$$
- **Filtración Topológica por Presupuesto [Línea Futura]:**
  $$\operatorname{Compat}_0(\Omega) \subseteq \operatorname{Compat}_1(\Omega) \subseteq \operatorname{Compat}_2(\Omega) \subseteq \cdots \subseteq \operatorname{Compat}_\infty(\Omega)$$

---

# 4. OBSERVABLE PRIMITIVO $\mu$ Y COSTE DERIVADO $\kappa$ [Definición]

### 4.1 Métrica Morfismo-Nivel [Definición]
$$\mu: \mathrm{Mor}(\mathcal{C}) \longrightarrow \mathbb{N}_\infty \qquad \mu(\alpha) \triangleq \inf \{ \mathrm{ProofCost}(\pi) \mid \pi \in \mathrm{Cert}(\alpha) \}$$

### 4.2 Métrica Modelo-Nivel [Definición]
$$\mu(M) \triangleq \sup_{\alpha \in \mathrm{Mor}(M)} \mu_M(\alpha)$$

### 4.3 Coste Derivado de Extensión Conservativa $\kappa$ [Definición]
$$\kappa(M) \triangleq \inf \{ \mu(E) \mid E \in \mathbf{Mod}(F,I,S,R_\infty), \; M \hookrightarrow_\text{fib} E \text{ es embedding pleno fibrado conservativo} \}$$

---

# 5. ESTATUS LÓGICO DE LOS RESULTADOS DEL PROGRAMA

- **Objetivo 0 (Representación Categorial):** $\mathbf{Mod}(\Sigma, T) \simeq \mathbf{CertCalc}(\mathcal{C})$.
- **Objetivo 1 (Modelos Mínimos de Independencia):** Construcción explícita de $M_{\neg F}, M_{\neg I}, M_{\neg S}, M_{\neg R_k}$.
- **Proposición 1 (Subaditividad con Overhead):** $\mu(\beta \circ \alpha) \le \mu(\alpha) + \mu(\beta) + \Delta_{\text{overhead}}(\alpha, \beta)$.
- **Conjetura 1 ($C_1$ - Jerarquía Estricta $R_k$):** $\mathbf{Mod}(F, I, S, R_{k_1}) \subsetneq \mathbf{Mod}(F, I, S, R_{k_2})$ para $k_1 < k_2$.
- **Conjetura 2 ($C_2$ - Separación por Coste $\kappa$):** Existen estructuras no certificables $M$ con $\kappa(M) = \infty$.
