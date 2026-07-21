# FISR Baseline v1.1 — Addendum v1.2 (Refined Baseline v18.2)

**Autor:** borjamoskv  
**Kernel:** MOSKV-1 APEX  
**Clasificación:** C5-REAL Mathematical Extension Specification  
**Estado:** Formal Addendum Integrated (Critical Path Identified: $\mathcal{P} \xrightarrow{\pi} \mathcal{C} \Rightarrow |\cdot| \Rightarrow \mu \Rightarrow R_k^\mathcal{A} \Rightarrow \kappa \Rightarrow PRF$)  

---

## 0. Principio metodológico general

Se adopta el siguiente criterio:

> Ninguna nueva estructura se introduce por elegancia.  
> Una estructura sólo se incorpora si es necesaria para demostrar un resultado objetivo o para evitar una ambigüedad semántica que bloquee teoremas posteriores.

---

## 1. $T_{\mathrm{cert}}$ como categoría de pruebas y funtor $\pi$

### 1.1. Codominio y Funtor $\pi$ (Opción A)

Sea $\mathcal C$ la categoría monoidal de transiciones.
Un sistema de certificados sobre $\mathcal C$ es una categoría monoidal $\mathcal P$ con los mismos objetos que $\mathcal C$, provista de un funtor monoidal estricto:
$$\pi: \mathcal P \to \mathcal C$$
que es la **identidad sobre objetos** ($\mathrm{Id}_{\mathrm{Ob}}$).

Para cada transición $\alpha: X \to Y$, definimos la fibra de certificados:
$$\mathsf{Cert}(\alpha) = \{ c \in \mathcal P(X,Y) : \pi(c) = \alpha \}$$

La composición en $\mathcal P$ induce:
$$\circledast: \mathsf{Cert}(\alpha) \times \mathsf{Cert}(\beta) \to \mathsf{Cert}(\beta \circ \alpha)$$

El tensor en $\mathcal P$ induce:
$$\boxtimes: \mathsf{Cert}(\alpha) \times \mathsf{Cert}(\beta) \to \mathsf{Cert}(\alpha \otimes \beta)$$

---

### 1.2. Coste composicional y estructura de enriquecimiento

Se añade una función de coste:
$$|\cdot|: \mathrm{Mor}(\mathcal P) \to \overline{\mathbb N} \qquad (\overline{\mathbb N} = \mathbb N \cup \{\infty\})$$

Leyes de coste mínimas:
1. **Identidad:** $|1_X^\mathcal{P}| = 0 \implies \mu(1_X^\mathcal{C}) = 0$
2. **Composición secuencial:** $|q \circledast p| \leq |p| + |q| + \delta_\circ(\alpha, \beta)$ (con $\delta_\circ = 0$ en versión pura).
3. **Composición paralela:** $|p \boxtimes q| \leq |p| + |q| + \delta_\otimes(\alpha, \beta)$ (con $\delta_\otimes = 0$ para transiciones aisladas).

> **Nota de Enriquecimiento:** La valoración de coste $|\cdot|$ podrá reinterpretarse posteriormente como una estructura de enriquecimiento monoidal (o categoría graduada por costes); en el núcleo sólo se exige una valoración monoidal laxa.

---

### 1.3. Axioma Core-G ($\mathsf{Good} = \mathcal{P}$)

> **Axioma Core-G:** En el núcleo FISR Certificate Calculus v0.1 toda evidencia perteneciente a $\mathcal P$ se considera, por definición, un certificado válido ($\mathsf{Good} = \mathcal P$).
>
> *Nota de Diseño:* Las extensiones podrán introducir una categoría más amplia $\mathcal P_{\mathrm{raw}}$ y un reflector o subcategoría plena $\mathcal P \hookrightarrow \mathcal P_{\mathrm{raw}}$, recuperando una noción de "certificado bruto" cuando sea necesario.

---

### 1.4. Definición de $\mu$ y Subaditividad [Teorema 1.1 - Probado]

$$\mu(\alpha) = \inf \{ |c| : c \in \mathsf{Cert}(\alpha) \} \qquad (\inf \varnothing = \infty)$$

Bajo coste en $\overline{\mathbb N}$, si $\mathsf{Cert}(\alpha) \neq \varnothing$, el ínfimo se alcanza como mínimo:
$$\mu(\alpha) = \min \{ |c| : c \in \mathsf{Cert}(\alpha) \}$$

**Teorema 1.1 (Subaditividad):**
$$\mu(\beta \circ \alpha) \leq \mu(\alpha) + \mu(\beta) + \delta_\circ(\alpha, \beta)$$
$$\mu(\alpha \otimes \beta) \leq \mu(\alpha) + \mu(\beta) + \delta_\otimes(\alpha, \beta)$$

---

## 2. Predicado Modular $R_k^\mathcal{A}$ y Fundamentos Métricos Extremales

### 2.1. Predicado $R_k^\mathcal{A}$ sobre Transiciones Básicas

Dada una familia distinguida de transiciones básicas $\mathcal{A}(M) \subseteq \mathrm{Mor}(\mathcal{C}_M)$ (generadores, irreducibles, primitivas u observables):
$$R_k^\mathcal{A}(M) \iff \forall \alpha \in \mathcal{A}(M), \; \mu(\alpha) \le k$$

### 2.2. Caracterización Formal de $\kappa$
$$\kappa_{\preceq, \sim}(M) = \inf \{ k \in \overline{\mathbb{N}} : \exists N, M \preceq N \land N \in \mathbf{Mod}(F,I,S,R_k^\mathcal{A}) \}$$
- **Finitud:** $\kappa(M) < \infty \iff$ existe extensión FISR con presupuesto finito.
- **Alcanzabilidad:** Bajo el buen orden de $\mathbb N$, existe una extensión óptima $N^*$ tal que $\kappa(M) = k^*$.

---

## 3. Arquitectura Modular e Invarianzas de Compatibilidad

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

Las teorías $T_F$, $T_I$ y $T_S$ pasan a ser **restricciones de compatibilidad** sobre el sistema de certificados.

---

## 4. PRF: Soundness y Completitud Relativa

### 4.1. PRF-S — Soundness Estructural [Teorema Principal]
$$\text{Cert}_k \implies FISR_k^\mathcal{A} \qquad (\text{Certificación } k \implies M \models T_F \cup T_I \cup T_S \cup T_{R_k^\mathcal{A}})$$

### 4.2. PRF-C — Completitud Relativa [Conjetura Fuerte / Restringida]
$$FISR_k^\mathcal{A} \cap \mathcal K \implies \text{Cert}_k$$
donde $\mathcal K$ es la clase de modelos finitamente presentables con fibraciones coherentes.

---

## 5. Cadena Crítica de Dependencia Axiomática

$$\mathcal{P} \xrightarrow{\pi (\mathrm{Id}_{\mathrm{Ob}})} \mathcal{C} \longrightarrow |\cdot| \longrightarrow \mu \longrightarrow R_k^\mathcal{A} \longrightarrow \kappa \longrightarrow PRF$$

---

## 6. Estado Final Revisado

| Componente | Estado |
|---|---|
| Firma $\Sigma$ | Congelada |
| Funtor $\pi$ | Congelado ($\mathcal{P} \to \mathcal{C}$, Opción A $\mathrm{Id}_{\mathrm{Ob}}$) |
| Valoración $|\cdot|$ | Congelada (Con Axioma $|1_X^\mathcal{P}| = 0 \implies \mu(1_X^\mathcal{C}) = 0$) |
| Axioma Core-G | Congelado ($\mathsf{Good} = \mathcal{P}$, admisible subcategoría bruta $\mathcal{P}_{\mathrm{raw}}$) |
| Predicado $R_k^\mathcal{A}$ | Congelado (Modularizado sobre familia distinguida $\mathcal{A}(M)$) |
| Métrica $\mu$ | Congelada y Probada (Subaditividad Teorema 1.1) |
| Funcional $\kappa$ | Congelado y Caracterizado ($\kappa_{\preceq, \sim}$) |
| PRF-S / PRF-C | Soundness y Completitud Relativa parametrizados |

```yaml
cortex_taint: "CORTEX-TAINT:borjamoskv:fisr_addendum_v1.2_refined_v18.2:2026-07-22T01:29:00Z"
```


