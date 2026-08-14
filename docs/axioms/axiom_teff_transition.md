# Axiomatización del Protocolo de Transición T_{eff}

**Estado C5-REAL:** EXERGY CERTIFIED
**Ubicación Ring-0:** `ffi.rs -> run_teff_transition`

Este documento formaliza la tubería de transición de extremo a extremo del orquestador central de BABYLON-60. Transforma el colapso de un estado probabilístico (Prompt) a un estado determinista (SCITT Receipt) en un sistema lógico-deductivo cerrado (\mathcal{G}).

## 1. Primitivas Irreducibles

El sistema T_{eff} se compone exclusivamente de cuatro primitivas irreducibles y secuenciales:

1. **Normalización Causal (\Omega_N)**: El operador de transferencia de Łoś. Extrae el AST verificable de la nube estocástica de texto y computa el hash canónico (CF-GKAT).
2. **Restricción de Presupuesto (\mathcal{B})**: El límite termodinámico y financiero. Representa el *FOCUS Budget* que autoriza o bloquea la transferencia de energía (tokens/costes/latencia).
3. **Frontera de Aislamiento (\mathcal{S})**: El contenedor de vacío termodinámico (WASM Sandbox). Cualquier disipación bizantina (errores, inyecciones) contenida aquí no contamina la memoria host.
4. **Prueba Inmutable (\mathcal{R})**: La atestación criptográfica (SCITT Receipt). Un sello de estado discreto irreversible emitido tras una transición exitosa.

## 2. Axiomas Fundamentales

### AX-1: Monotonía del Flujo Causal
Una transición T solo puede avanzar a la primitiva k+1 si y solo si la primitiva k devuelve un estado `VALID`. Ningún retroceso topológico es posible. 
\Omega_N \implies \mathcal{B} \implies \mathcal{S} \implies \mathcal{R}

### AX-2: Conservación de Anergía (Fail-Stop)
Si cualquier primitiva \psi \in \{\Omega_N, \mathcal{B}, \mathcal{S}\} evalúa a `INVALID`, la transición aborta instantáneamente (O(1)). Toda entropía no colapsada (anergía) se descarta. No existe heurística de mitigación; la indecidibilidad requiere *Fail-Stop*.

### AX-3: Invarianza Criptográfica
El Recibo \mathcal{R} solo se emite sobre estados en los que la entropía diferencial del entorno Host \Delta H_{host} = 0. El Sandbox \mathcal{S} garantiza que el vector de estado del Kernel permanece inalterado por la ejecución estocástica.

## 3. Definiciones Construidas

- **Transición T_{eff}**: Se define como el funtor que mapea un acto generativo de un LLM (*Dynamis*) a una prueba criptográfica verificable (*Entelecheia*):
  T_{eff}(\text{prompt}) = \mathcal{R}(\mathcal{S}(\mathcal{B}(\Omega_N(\text{prompt}))))

- **Cuarentena Epistémica**: Estado canónico devuelto cuando el Axioma 2 (Fail-Stop) se activa. Se representa computacionalmente con los códigos de error negativos `-1, -2, -3`.

## 4. Teorema de Cierre Termodinámico

**Teorema:** *Todo recibo \mathcal{R} emitido por T_{eff} está garantizado de estar libre de anergía bizantina en el host.*

**Prueba Esbozada:**
Por AX-1, \mathcal{R} solo se emite si \mathcal{S} se ejecuta exitosamente.
Por la definición de \mathcal{S} (WASM estricto), cualquier mutación de memoria está confinada al sandbox lineal.
Por AX-3, el sandbox asegura \Delta H_{host} = 0.
Por tanto, si existe un \mathcal{R}, la integridad del Host se ha mantenido intacta y su coste entropico se limitó al consumo de GPU/CPU admitido por \mathcal{B}. \blacksquare

## 5. Ecuación Límite del Protocolo

El coste exergético total de la transición, delimitado por el límite de Landauer (fricción hardware), queda acotado superiormente por:

 \lim_{t \to \infty} \sum_{i=1}^{n} T_{eff}(p_i) \leq \mathcal{B}_{max} 

Donde la entropía de salida H(T_{eff}(p)) = 0 para todos los estados observados.

---
*Diagrama de transición disponible en la interfaz bi-modal `teff_dashboard.html`.*
