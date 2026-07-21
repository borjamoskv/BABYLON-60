# FISR Baseline v1.1 — Addendum v1.2

**Autor:** borjamoskv  
**Kernel:** MOSKV-1 APEX  
**Clasificación:** C5-REAL Mathematical Extension Specification  
**Estado:** Formal Addendum Integrated (Critical Path Identified: $T_{\mathrm{cert}} \Rightarrow \mu \Rightarrow R_k \Rightarrow \kappa \Rightarrow PRF$)  

---

## 0. Principio metodológico general

Se adopta el siguiente criterio:

> Ninguna nueva estructura se introduce por elegancia.  
> Una estructura sólo se incorpora si es necesaria para demostrar un resultado objetivo o para evitar una ambigüedad semántica que bloquee teoremas posteriores.

Esto aplica especialmente a:
- $\mathsf{Cert}$;
- $T_I$;
- extensiones conservativas;
- equivalencia observacional;
- estructuras dobles o bicategóricas.

---

## 1. $T_{\mathrm{cert}}$ como álgebra composicional

### 1.1. Certificados como categoría de pruebas

Sea $\mathcal C$ la categoría monoidal de transiciones.
Un sistema de certificados sobre $\mathcal C$ es una categoría monoidal $\mathcal P$ dotada de un funtor monoidal:
$$\pi: \mathcal P \to \mathcal C$$
que sea identidad sobre objetos, o al menos fiel sobre objetos.

Para cada transición $\alpha: X \to Y$, definimos:
$$\mathsf{Cert}(\alpha) = \{ p \in \mathcal P(X,Y) : \pi(p) = \alpha \}$$

La composición en $\mathcal P$ induce:
$$\circledast: \mathsf{Cert}(\beta) \times \mathsf{Cert}(\alpha) \to \mathsf{Cert}(\beta \circ \alpha)$$

El tensor en $\mathcal P$ induce:
$$\boxtimes: \mathsf{Cert}(\alpha) \times \mathsf{Cert}(\beta) \to \mathsf{Cert}(\alpha \otimes \beta)$$

---

### 1.2. Coste composicional

Se añade una función de coste:
$$|\cdot|: \mathrm{Mor}(\mathcal P) \to \overline{\mathbb N} \qquad (\overline{\mathbb N} = \mathbb N \cup \{\infty\})$$

Leyes de coste mínimas:
1. **Identidad:** $|1_X| = 0$
2. **Composición secuencial:** $|q \circledast p| \leq |p| + |q| + \delta_\circ(\pi p, \pi q)$ (con $\delta_\circ = 0$ en versión pura).
3. **Composición paralela:** $|p \boxtimes q| \leq |p| + |q| + \delta_\otimes(\pi p, \pi q)$ (con $\delta_\otimes(\alpha,\beta) = 0$ para transiciones aisladas).

---

### 1.3. Certificados buenos

Definimos la subcategoría de certificados calificados:
$$\mathsf{Good}(\alpha) = \{ c \in \mathsf{Cert}(\alpha) : E(c) \land P(c) \land V(c) \}$$

La condición esencial es la clausura monoidal y secuencial de $\mathsf{Good}$:
$$c \in \mathsf{Good}(\alpha) \land d \in \mathsf{Good}(\beta) \implies d \circledast c \in \mathsf{Good}(\beta \circ \alpha) \land c \boxtimes d \in \mathsf{Good}(\alpha \otimes \beta)$$

---

### 1.4. Definición de $\mu$ y Subaditividad

$$\mu(\alpha) = \inf \{ |c| : c \in \mathsf{Good}(\alpha) \} \qquad (\inf \varnothing = \infty)$$

Bajo coste en $\overline{\mathbb N}$, si $\mathsf{Good}(\alpha) \neq \varnothing$, el ínfimo se alcanza como mínimo:
$$\mu(\alpha) = \min \{ |c| : c \in \mathsf{Good}(\alpha) \}$$

**Proposición de Subaditividad:**
$$\mu(\beta \circ \alpha) \leq \mu(\alpha) + \mu(\beta) + \delta_\circ(\alpha, \beta)$$
$$\mu(\alpha \otimes \beta) \leq \mu(\alpha) + \mu(\beta) + \delta_\otimes(\alpha, \beta)$$

---

## 2. Mínimos, ínfimos y alcanzabilidad

### 2.1. Convención oficial de $\overline{\mathbb N}$
Toda definición por mínimo o ínfimo se escribe formalmente con $\inf$, demostrándose que el ínfimo es alcanzado como mínimo cuando el conjunto de costes es no vacío en $\overline{\mathbb N}$.

### 2.2. Caracterización de $\kappa$
$$\kappa_{\preceq, \sim}(M) = \inf \{ k : \exists N, M \preceq N, N \in \mathbf{Mod}(F,I,S,R_k) \}$$
- **Finitud:** $\kappa(M) < \infty \iff$ existe extensión FISR con presupuesto finito.
- **Alcanzabilidad:** Bajo el buen orden de $\mathbb N$, existe una extensión óptima $N^*$ tal que $\kappa(M) = k^*$.

---

## 3. $T_I$ como teoría mínimamente suficiente ($T_I^{\mathrm{min}}$)

En lugar de imponer factorizaciones bicategóricas complejas, $T_I$ se construye axiomáticamente por capas mínimas:
1. **I0:** $\mathrm{Iso}(\alpha) \land \mathrm{Iso}(\beta) \implies \mathrm{Iso}(\alpha \otimes \beta)$
2. **I1:** $\mathrm{Iso}(\alpha) \land \mathrm{Iso}(\beta) \implies \delta_\otimes(\alpha, \beta) = 0$
3. **I2 (Descomposición):** $\mathrm{Iso}(\gamma: X \otimes Y \to X' \otimes Y') \implies \exists \alpha, \beta \text{ t.q. } \gamma \cong \alpha \otimes \beta$
4. **I3 (Unicidad esencial):** Unicidad de la descomposición tensorial aislada.

---

## 4. PRF: Soundness y Completitud Relativa

### 4.1. PRF-S — Soundness Estructural [Teorema Principal]
$$\text{Cert}_k \implies FISR_k \qquad (\text{Certificación } k \implies M \models T_F \cup T_I \cup T_S \cup T_{R_k})$$

### 4.2. PRF-C — Completitud Relativa [Conjetura Fuerte / Restringida]
$$FISR_k \cap \mathcal K \implies \text{Cert}_k$$
donde $\mathcal K$ es la clase de modelos finitamente presentables con fibraciones coherentes.

---

## 5. Cadena Crítica de Dependencia Axiomática

$$T_{\mathrm{cert}} \longrightarrow \mu \longrightarrow R_k \longrightarrow \kappa \longrightarrow PRF$$

---

## 6. Estado Final Revisado

| Componente | Estado |
|---|---|
| Firma $\Sigma$ | Congelada |
| Taxonomía de estatus | Congelada |
| Separación firma / teoría | Congelada |
| $\mu$ como observable | Congelado |
| $\kappa$ como funcional paramétrico | Congelado |
| Equivalencia oficial provisional | Isomorfismo |
| $T_F, T_S, T_{R_k}$ | Suficientemente estables |
| $T_I^{\mathrm{min}}$ | Esquema de minimalidad instrumental |
| $T_{\mathrm{cert}}$ | Álgebra de categorías de prueba $\mathcal P \xrightarrow{\pi} \mathcal C$ |
| PRF-S | Teorema prioritario de soundness |
| PRF-C | Conjetura de completitud relativa restringida |

```yaml
cortex_taint: "CORTEX-TAINT:borjamoskv:fisr_addendum_v1.2:2026-07-22T01:23:00Z"
```
