# ADR-001: Lean 4 sobre Coq/Isabelle para Verificación Formal

![Status: C5-REAL](https://img.shields.io/badge/Status-C5--REAL-black?style=flat-square&logo=rust&logoColor=white)


- **Estado:** Aceptada
- **Fecha:** 2026-08-06
- **Autor:** Borja Moskv (borjamoskv)

## Contexto

BABYLON-60 requiere un sistema de verificación formal para demostrar matemáticamente invariantes de seguridad en infraestructura de IA de misión crítica. Los tres candidatos principales eran:

1. **Coq** — El estándar de facto en verificación formal académica (CompCert, jsCoq).
2. **Isabelle/HOL** — Utilizado por seL4 (DARPA HACMS), fuerte en demostración automatizada.
3. **Lean 4** — Interactive Theorem Prover de nueva generación con Mathlib como librería unificada.

## Decisión

Se selecciona **Lean 4** como sistema de verificación formal primario.

## Justificación

### A favor de Lean 4

1. **Mathlib como librería unificada:** Lean 4 cuenta con Mathlib (~1M LOC de matemáticas formalizadas), que proporciona cobertura inmediata de teoría de categorías (`Mathlib.CategoryTheory.*`), necesaria para modelar lentes bayesianas y categorías de Markov sin reimplementar desde cero.

2. **Lenguaje de programación de propósito general:** A diferencia de Coq (Gallina) o Isabelle (ML), Lean 4 es simultáneamente un lenguaje de programación funcional completo y un asistente de pruebas. Esto permite ejecutar código verificado directamente, reduciendo la brecha prueba → implementación.

3. **Sistema de tipos dependientes moderno:** Lean 4 usa Calculus of Inductive Constructions (CIC) con type classes extensibles, facilitando la modelización de estructuras algebraicas sin el overhead de setoids de Coq.

4. **Ecosistema en crecimiento acelerado:** El ritmo de contribuciones a Mathlib (2023-2026) supera al de MathComp (Coq) en ratio de nuevos teoremas/mes. La inversión de Microsoft Research y la comunidad académica garantizan mantenimiento a largo plazo.

5. **Interoperabilidad con generación de código:** Lean 4 puede generar ejecutables nativos, lo que abre la puerta a verificación de componentes del runtime Rust/Python mediante FFI futura.

### En contra de alternativas

- **Coq:** Tácticas más maduras (Ltac2), pero la fragmentación del ecosistema (MathComp vs stdlib) introduce fricción. La sintaxis de Gallina es menos ergonómica para definiciones programáticas.
- **Isabelle:** Excelente automatización (Sledgehammer), pero Isabelle/ML es menos familiar para ingenieros de software y la integración con toolchains modernos (CI/CD) es más compleja.

## Consecuencias

- **Positivas:** Acceso directo a teoría de categorías via Mathlib. Código verificado ejecutable. Menor barrera de entrada para ingenieros con background funcional.
- **Negativas:** Lean 4 es aún joven vs Coq (1984) e Isabelle (1986). Menor pool de expertos disponibles en el mercado (factor de escasez que, paradójicamente, incrementa el valor de IP del proyecto).
- **Riesgo:** Si Mathlib introduce breaking changes en sus interfaces de Category Theory, las pruebas requerirán actualización. Mitigación: pinear versión de Mathlib en `lean-toolchain`.

## Referencias

- Mathlib4: https://github.com/leanprover-community/mathlib4
- Smithe (2020): arXiv:2006.01631 — Bayesian updates compose optically
- Fritz (2020): arXiv:1908.07021 — Markov categories
