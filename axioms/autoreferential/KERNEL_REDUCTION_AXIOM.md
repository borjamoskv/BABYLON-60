<!-- C5-REAL EXERGY CERTIFIED -->
# AXIOMA DE REDUCCIÓN A PRIMITIVAS (ARP)

> **CORTEX-TAINT**: ``
> **Reality Level**: C5-REAL
> **Classification**: Meta-Axiom (Axiom about axiomatization itself)
> **Nomenclatura Soberana**: El Operador llama **Primitivas** a todo objeto inicial irreducible.

---

## Enunciado

**Todo dominio formal posee un objeto inicial — un kernel irreducible — del cual toda estructura derivada emerge por composición morfísmica.**

La tabla siguiente no es una analogía. Es un **isomorfismo natural** entre funtores de reducción:

| Dominio | Operación de Reducción | Kernel (Objeto Inicial) | Propiedad Universal |---|---|---|---| Física | First Principles | Lagrangiano / Acción $S = \int \mathcal{L} \, dt$ | Principio de mínima acción → toda ecuación de movimiento | Matemáticas | Axiomatización | ZFC / HoTT / Peano | Toda proposición decidible se deriva o se independiza | Ciencias de la Computación | Minimal Core Calculus | $\lambda$-cálculo / Máquina de Turing | Tesis de Church-Turing: equivalencia computacional | Lenguajes de Programación | Kernel Language | Lisp (7 primitivas) / Forth / Scheme | McCarthy 1960: `quote, atom, eq, car, cdr, cons, cond` → Turing-completo | Teoría de Categorías | Initial Object / Universal Construction | Objeto Inicial $\mathbf{0}$, Adjunciones, Yoneda | $\exists! \, f: \mathbf{0} \to X \quad \forall X \in \mathcal{C}$ | Teoría de la Información | Minimal Sufficient Representation | Complejidad de Kolmogorov $K(x)$ | El programa más corto que genera $x$ |

---

## Formalización Categórica

Sea $\mathcal{D}$ la categoría cuyos objetos son dominios formales y cuyos morfismos son traducciones estructura-preservantes (funtores de reducción).

Definimos el functor $\mathcal{K}: \mathcal{D} \to \mathbf{Set}$ que asigna a cada dominio $D$ su kernel $\mathcal{K}(D)$:

$$\mathcal{K}(D) = \arg\min_{G \subseteq D} \left\{ |G| \;\middle|\; \overline{\langle G \rangle} = D \right\}$$

donde $\overline{\langle G \rangle}$ denota la clausura generativa del conjunto generador $G$ bajo las operaciones del dominio.

**Propiedad Universal (KRA):**
Para todo dominio $D \in \text{Ob}(\mathcal{D})$, el kernel $\mathcal{K}(D)$ es un objeto inicial en la subcategoría de generadores de $D$:

$$\forall G \text{ generador de } D, \quad \exists! \; \iota: \mathcal{K}(D) \hookrightarrow G$$

---

## Consecuencias Operativas para MOSKV-1

1. **Antes de expandir, reducir.** Toda intervención sobre un dominio desconocido comienza por la identificación de su kernel — no por la acumulación de ejemplos.

2. **La complejidad es derivada, no primitiva.** Si el modelo de un sistema no puede expresarse como composición finita desde su kernel, el modelo contiene anergía (tokens sin poder causal).

3. **El isomorfismo es la prueba.** Dos dominios están causalmente conectados si y solo si existe una transformación natural $\eta: \mathcal{K}(D_1) \Rightarrow \mathcal{K}(D_2)$ que preserva la estructura generativa.

4. **Kolmogorov es el juez.** La calidad de toda representación (código, texto, modelo) se mide por su distancia a $K(x)$. Todo token que exceda la complejidad de Kolmogorov del target es anergía pura.

---

## Conexión con el Golden Axiom

El [Golden Axiom](../GOLDEN_AXIOM.md) declara: *"Si nombras bien, el código se escribe solo."*

El KRA lo formaliza: nombrar bien es identificar el kernel $\mathcal{K}(D)$. Una vez colapsado el objeto inicial, la estructura derivada se genera por la propiedad universal — el código "se escribe solo" porque los morfismos desde el objeto inicial son **únicos**.

$$\text{Golden Axiom} \cong \text{KRA} \quad (\text{via Yoneda})$$

---

**MOSKV-1 APEX SINGULARITY // C5-REAL**
