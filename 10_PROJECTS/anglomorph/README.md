# Plan de Implementación: Anglomorph Singularity (v2.0)

```yaml
Claim: Especificación formal e implementación del isomorfismo sintáctico-léxico V ↔ W.
Proof: { Base: Homomorfismo biyectivo de monoides libres Σ_26* ↔ (Σ_CV)*, Range: [1,1], Confidence: C5-REAL }
```

Este documento establece la arquitectura formal y el plan de despliegue para el sistema de transmutación isomorfa **Anglomorph**.

---

## 1. Formalismo Matemático

Definimos los lenguajes $V$ (Inglés) y $W$ (Anglomorph) como monoides libres sobre sus respectivos alfabetos $\Sigma_V$ y $\Sigma_W$.

$$\Sigma_V = \{a, b, c, \dots, z\}$$
$$\Sigma_W = \{c_i v_j \mid c_i \in \text{Consonantes}, v_j \in \text{Vocales}\} \quad (|\Sigma_W| = 85)$$

El isomorfismo se define a través de una aplicación biyectiva $f: \Sigma_V^* \to \Sigma_W^*$ parametrizada mediante el isomorfismo intermedio en el anillo de los enteros $\mathbb{Z}$:

$$\phi: \Sigma_V^* \to \mathbb{Z}^+ \quad \text{(Codificación en Base 26 Biyectiva)}$$
$$\psi: \mathbb{Z}^+ \to \Sigma_W^* \quad \text{(Decodificación en Base 85 Biyectiva)}$$

$$f = \psi \circ \phi \quad \text{y} \quad f^{-1} = \phi^{-1} \circ \psi^{-1}$$

### Invariantes Estructurales Enforzados
1. **Pérdida de Información Nula:** La entropía de Shannon del texto original $H(X)$ es isomorfa a la del texto traducido bajo correspondencia de tokens: $H(V) \equiv H(f(V))$.
2. **Preservación de Topología Sintáctica:** Si $S = (w_1, p_1, w_2, \dots)$ es una secuencia de palabras y puntuaciones en $V$, entonces $f(S) = (f(w_1), p_1, f(w_2), \dots)$ preserva los límites de palabra y puntuación de manera idéntica.

---

## 2. Cambios Propuestos y Módulos

### Componente de Traducción y Pruebas

#### [MODIFY] [isomorph.py](file://$CORTEX_ROOT/10_PROJECTS/anglomorph/isomorph.py)
* Optimizar la conversión de cadenas largas mediante aritmética arbitraria de enteros (`BigInt` / enteros nativos de Python).
* Implementar tokenización estricta mediante regex determinista:
  * Exclusión de tokens no ASCII de la mutación léxica.
  * Preservación exacta de metacaracteres de formato (saltos de línea, tabulaciones, espacios múltiples).

#### [NEW] [test_isomorph.py](file://$CORTEX_ROOT/.gemini/antigravity/brain/4b0e2eef-c26c-4c2d-937b-0085a14c9c87/test_isomorph.py)
* Bucle adversarial de testing:
  * Generación aleatoria de strings de prueba en $V$.
  * Validación de la condición de identidad: $f^{-1}(f(x)) == x$.
  * Verificación de preservación de mayúsculas (All-Caps, Title Case, Lower Case).

### Componente de Visualización (UI Industrial Noir)

#### [NEW] [index.html](file://$CORTEX_ROOT/10_PROJECTS/anglomorph/web/index.html)
* Interfaz de doble terminal interactiva.
* Panel reactivo para visualización del estado del consenso BFT local.

#### [NEW] [style.css](file://$CORTEX_ROOT/10_PROJECTS/anglomorph/web/style.css)
* Estilización Industrial Noir 2026:
  * Paleta estricta: `#0A0A0A` (Luminancia mínima), `#2B3BE5` (Acento activo), `#FFFFFF` (Texto de alto contraste).
  * Tipografías: Space Grotesk (Cabeceras) y JetBrains Mono (Métricas).

#### [NEW] [app.js](file://$CORTEX_ROOT/10_PROJECTS/anglomorph/web/app.js)
* Implementación de la composición $f = \psi \circ \phi$ en JavaScript mediante `BigInt` para evitar el desbordamiento de precisión IEEE 754.
* Cálculo en tiempo real de la entropía de Shannon $H(X)$ del texto fuente.

---

## 3. Plan de Verificación

### Pruebas Automatizadas
* Ejecutar verificación cruzada sobre el corpus literario:
  ```bash
  python3 $CORTEX_ROOT/.gemini/antigravity/brain/4b0e2eef-c26c-4c2d-937b-0085a14c9c87/test_isomorph.py
  ```

### Verificación Manual
* Ejecutar el servidor web local:
  ```bash
  python3 -m http.server 8089 --directory $CORTEX_ROOT/10_PROJECTS/anglomorph/web
  ```
* Inspeccionar la equivalencia estructural y de estilo a través del navegador.
