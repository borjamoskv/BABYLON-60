<!-- C5-REAL EXERGY CERTIFIED -->
# Invariantes Operativos C5-REAL

Este documento define la capa de ejecución (Operacional) complementaria al nivel doctrinal (`AGENTS.md`).

## INV-1: Alcance Declarado Estricto (Whitelisting Topológico)
Todo acoplamiento entre *Dynamis* (LLM) y *Entelecheia* (Rust) requiere un mapa finito de herramientas y esquemas de memoria compartida explícitamente declarados (Manifiesto de Época $E$). Cualquier intento estocástico de invocar un recurso, binario o socket de red fuera del perímetro del WASM Sandbox provocará un rechazo atómico y la no-actualización del puntero maestro.

## INV-2: Cap Contractual y Circuito de Interrupción (Fail-Stop)
El límite de responsabilidad (Liability Cap) se materializa físicamente mediante la incapacidad del sistema para propagar incertidumbre. Ante cualquier desviación semántica ($H(X) < \epsilon$) o colapso del Manifiesto, el sistema ejecuta un `Fail-Stop` inmediato. El servicio colapsa o entra en Fallback antes de emitir un estado no verificado. El Cap Contractual asegura que el cliente asume que la interrupción del servicio es el comportamiento nominal de protección.

## INV-3: Cobertura Medida (Atestación de Contención)
Ningún código de validación del Kernel (Entelecheia) pasará al árbol principal ni será atestado en Ring-0 sin una prueba de **cobertura del 100%** (o métrica declarada análoga en `autodidact_falsification_test.py`) que certifique algorítmicamente la contención de todas las ramas estocásticas.
Si la cobertura no es medible o la aserción decae, el sistema entra en `Fallback/Quarantine` automáticamente, bloqueando la atestación. No se puede vender contención si no se puede medir la superficie de sellado.
