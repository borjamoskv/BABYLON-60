<!-- C5-REAL EXERGY CERTIFIED -->
# Invariantes Operativos C5-REAL

Este documento define la capa de ejecución (Operacional) complementaria al nivel doctrinal (`AGENTS.md`).

## INV-1: Alcance Declarado (Validación Semántica S)
La salida de *Dynamis* (LLM) debe pertenecer estrictamente al conjunto formal S (el esquema algebraico CF-GKAT). La pertenencia x \in S es un predicado matemático decidible. Toda evaluación basada en umbrales de entropía o "confianza del modelo" (H(X)) queda explícitamente prohibida. La contención de capacidad (Sandbox WASM) es auxiliar; la contención semántica es el verdadero Gate.

## INV-2: Cap Contractual y Exención de SLA (Fail-Stop Legal)
El `Fail-Stop` transfiere la responsabilidad de la exactitud a la disponibilidad. Para que esto sea jurídicamente blindado, el SLA comercial exige:
1. **Carve-out explícito:** Los bloqueos preventivos del *Commit Gate* no computarán como tiempo de inactividad (downtime) ni devengarán créditos de SLA.
2. **Cap numérico:** La responsabilidad máxima ante una fuga estocástica está numéricamente topada (ej. cuotas de 12 meses). Sin estas dos cláusulas, el "Fail-Stop" es solo una máquina de generar incumplimientos.

## INV-3: Cobertura Medida y Falsabilidad (POPPER)
Ninguna regla de validación semántica pasa al árbol principal sin una demostración empírica de falsabilidad. Todo estado s \in S declarado seguro debe poseer un test negativo explícito en `autodidact_falsification_test.py` que pruebe que el *Commit Gate* rechaza un artefacto malicioso. Su medida explícita es el coeficiente \rho (fiabilidad de A.1.4) medido sobre una muestra N \ge 100 con intervalo de confianza por bootstrap. Este valor \rho DEBE ser emitido en cada corrida. Un INV-3 sin \rho empírico publicado no se considera un invariante válido, sino una suposición.
