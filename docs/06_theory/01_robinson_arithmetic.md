# 01 — Robinson's Arithmetic (Q)

> **Modulo Teórico 01 | Proyecto BABYLON-60 | Licencia Soberana (`INV_C5_17`)**
> Estudio formal de la Aritmética de Robinson ($Q$), la minimalidad de los 7 axiomas y la génesis de la indecidibilidad esencial.

---

## 1.1 Contexto Histórico y Significación Metamatemática

En 1950, el matemático norteamericano **Raphael M. Robinson** demostró un resultado monumental: identificó el **sistema axiomático mínimo** suficiente para desencadenar los Teoremas de Incompletitud de Gödel y la indecidibilidad de la Lógica de Primer Orden. Este sistema, denominado **$Q$** (o **Aritmética de Robinson**), consta de únicamente 7 axiomas definidos sobre el lenguaje elemental de la aritmética natural.

> [!IMPORTANT]
> **Pregunta Fundamental de Robinson:** ¿Cuál es la cantidad mínima de estructura matemática requerida para que emerjan de forma inevitable la incompletitud, el problema de la parada y los modelos no estándar?

---

## 1.2 El Lenguaje Formall $\mathcal{L}_Q$

El lenguaje formal de primer orden con igualdad $\mathcal{L}_Q$ consta de exactamente **4 símbolos no lógicos**:

| Símbolo | Tipo | Aridad | Significado Pretendido |
| :---: | :--- | :---: | :--- |
| $0$ | Constante | 0 | El elemento cero (origen) |
| $S$ | Función | 1 | Función Sucesora: $S(n) = n + 1$ |
| $+$ | Función | 2 | Operación Adición: $x + y$ |
| $\cdot$ | Función | 2 | Operación Multiplicación: $x \cdot y$ |

### Paradoja de la Definibilidad

A pesar de contar con solo 4 símbolos no lógicos, la **expresividad** de $\mathcal{L}_Q$ es universal: cualquier predicado computable sobre los enteros (primalidad, divisibilidad, exponenciación, secuencias de codificación) se puede formalizar como una fórmula bien formada en $\mathcal{L}_Q$.

Por ejemplo, el predicado " $p$ es primo" se formaliza como:

$$\text{Prime}(p) \equiv p \neq 0 \land p \neq S(0) \land \forall x \forall y \, \big( x \cdot y = p \implies x = S(0) \lor y = S(0) \big)$$

---

## 1.3 Los Siete Axiomas de Robinson ($Q$)

### Q1 — El cero no es sucesor
$$\forall x \; \neg(Sx = 0)$$

### Q2 — Inyectividad del sucesor
$$\forall x \forall y \; (Sx = Sy \implies x = y)$$

### Q3 — Todo elemento distinto de cero tiene predecesor
$$\forall x \; (x \neq 0 \implies \exists y \; (x = Sy))$$

### Q4 — Caso base de la adición
$$\forall x \; (x + 0 = x)$$

### Q5 — Paso recursivo de la adición
$$\forall x \forall y \; (x + Sy = S(x + y))$$

### Q6 — Caso base de la multiplicación
$$\forall x \; (x \cdot 0 = 0)$$

### Q7 — Paso recursivo de la multiplicación
$$\forall x \forall y \; (x + Sy = (x \cdot y) + x)$$

> [!WARNING]
> **Ausencia del Esquema de Inducción:** A diferencia de la Aritmética de Peano ($\text{PA}$), $Q$ carece por completo del esquema axiomático de inducción matemática:
> $$\phi(0) \land \forall n (\phi(n) \implies \phi(Sn)) \implies \forall n \phi(n)$$
> $Q$ reemplaza toda la potencia de inducción por el único axioma existencial $Q3$ (existencia de predecesor).

---

## 1.4 Propiedades Metamatemáticas Clave

### A. $\Sigma_1$-Completud

$Q$ es **$\Sigma_1$-completo**: toda proposición verdaderamente existencial ($\Sigma_1$) sobre los enteros es provable en $Q$. Concretamente, si una función computable $f(n_1, \dots, n_k) = m$, entonces:

$$Q \vdash \phi_f(\bar{n}_1, \dots, \bar{n}_k, \bar{m})$$

> [!NOTE]
> **Mapeo a BABYLON-60:** El motor ejecutor `b60_kernel` funciona como un verificador $\Sigma_1$-completo: comprueba la traza determinista de cualquier cómputo o mutación concreta en tiempo lineal $O(1)$ por paso.

### B. $\Pi_1$-Incompletud

$Q$ **no puede demostrar** generalizaciones universales, incluso verdades universales triviales:
- $Q \nvdash \forall x \; (0 + x = x)$
- $Q \nvdash \forall x \forall y \; (x + y = y + x)$ (conmutatividad de la suma)

### C. Representabilidad Fuerte de Funciones Computables

**Teorema de Robinson (1950):** Toda función computable (recursiva) $f: \mathbb{N}^k \to \mathbb{N}$ es **fuertemente representable** en $Q$ mediante la función $\beta$ de Gödel.

### D. Indecidibilidad Esencial

$Q$ es **esencialmente indecidible**: no solo es indecidible por sí mismo, sino que **toda extensión consistente de $Q$** es también indecidible.

---

## 1.5 La Jerarquía Aritmética Comparada

| Sistema Axiomático | Lenguaje | Inducción | ¿Decidable? | ¿Aplica Gödel? |
| :--- | :--- | :---: | :---: | :---: |
| **Aritmética de Presburger** | $0, S, +$ | Sí | **Sí** | ❌ No (sin $\cdot$) |
| **Aritmética de Skolem** | $0, S, \cdot$ | Sí | **Sí** | ❌ No (sin $+$) |
| **Aritmética de Robinson ($Q$)** | $0, S, +, \cdot$ | **No** | **No** | ✅ **Sí** |
| **Aritmética de Peano ($\text{PA}$)** | $0, S, +, \cdot$ | Sí (esquema) | **No** | ✅ **Sí** |
| **ZFC (Teoría de Conjuntos)** | $\in, =$ | Sí (transfinita) | **No** | ✅ **Sí** |

---

## 1.6 Referencias

- Robinson, R. M. (1950). "An Essentially Undecidable Axiom System." *Proceedings of the International Congress of Mathematicians*, Vol. 1, pp. 729–730.
- Tarski, A., Mostowski, A., & Robinson, R. M. (1953). *Undecidable Theories*. North-Holland.
