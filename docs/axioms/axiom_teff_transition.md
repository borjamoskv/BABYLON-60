<!-- C5-REAL EXERGY CERTIFIED -->
# Axiomatización del Protocolo de Transición T_eff

**Estado C5-REAL:** EXERGY CERTIFIED
**Ubicación Ring-0:** `ffi.rs -> run_teff_transition`

Este documento formaliza la tubería de transición de extremo a extremo del orquestador central de BABYLON-60. Transforma el colapso de un estado probabilístico (Prompt) a un estado determinista (SCITT Receipt) en un sistema lógico-deductivo cerrado (G).

## 1. Primitivas Irreducibles

El sistema T_eff se compone exclusivamente de cuatro primitivas irreducibles y secuenciales:

1. **Normalización Causal (Ω_N)**: El operador de transferencia de Łoś. Extrae el AST verificable de la nube estocástica de texto y computa el hash canónico (CF-GKAT).
2. **Restricción de Presupuesto (B)**: El límite termodinámico y financiero. Representa el *FOCUS Budget* que autoriza o bloquea la transferencia de energía (tokens/costes/latencia).
3. **Frontera de Aislamiento (S)**: El contenedor de vacío termodinámico (WASM Sandbox). Cualquier disipación bizantina (errores, inyecciones) contenida aquí no contamina la memoria host.
4. **Prueba Inmutable (R)**: La atestación criptográfica (SCITT Receipt). Un sello de estado discreto irreversible emitido tras una transición exitosa.

## 2. Axiomas Fundamentales

### AX-1: Monotonía del Flujo Causal
Una transición T solo puede avanzar a la primitiva k+1 si y solo si la primitiva k devuelve un estado `VALID`. Ningún retroceso topológico es posible.
Ω_N ⇒ B ⇒ S ⇒ R

### AX-2: Conservación de Anergía (Fail-Stop)
Si cualquier primitiva ψ ∈ {Ω_N, B, S} evalúa a `INVALID`, la transición aborta instantáneamente (O(1)). Toda entropía no colapsada (anergía) se descarta. No existe heurística de mitigación; la indecidibilidad requiere *Fail-Stop*.

### AX-3: Invarianza Criptográfica
El Recibo R solo se emite sobre estados en los que la entropía diferencial del entorno Host ΔH_host = 0. El Sandbox S garantiza que el vector de estado del Kernel permanece inalterado por la ejecución estocástica.

## 3. Definiciones Construidas

- **Transición T_eff**: Se define como el funtor que mapea un acto generativo de un LLM (*Dynamis*) a una prueba criptográfica verificable (*Entelecheia*):
  T_eff(prompt) = R(S(B(Ω_N(prompt))))

- **Cuarentena Epistémica**: Estado canónico devuelto cuando el Axioma 2 (Fail-Stop) se activa. Se representa computacionalmente con los códigos de error negativos `-1, -2, -3`.

## 4. Teorema de Cierre Termodinámico

**Teorema:** *Todo recibo R emitido por T_eff está garantizado de estar libre de anergía bizantina en el host.*

**Prueba Esbozada:**
Por AX-1, R solo se emite si S se ejecuta exitosamente.
Por la definición de S (WASM estricto), cualquier mutación de memoria está confinada al sandbox lineal.
Por AX-3, el sandbox asegura ΔH_host = 0.
Por tanto, si existe un R, la integridad del Host se ha mantenido intacta y su coste entrópico se limitó al consumo de GPU/CPU admitido por B. ■

## 5. Ecuación Límite del Protocolo

El coste exergético total de la transición, delimitado por el límite de Landauer (fricción hardware), queda acotado superiormente por:

 lim_{t → ∞} ∑_{i=1}^{n} T_eff(p_i) ≤ B_max

Donde la entropía de salida H(T_eff(p)) = 0 para todos los estados observados.

---
*Diagrama de transición disponible en la interfaz bi-modal `teff_dashboard.html`.*
