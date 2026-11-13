-- Ejemplo aritmético heredado de governance_agent.b60.
-- Solo comprueba la fracción de la suma, no la ejecución ni los efectos del programa.
import Babylon

set_option warningAsError true

namespace Babylon.GeneratedTrace
theorem trace_exactness : (Babylon.add_tick60 (Babylon.Tick60.mk 0 4320000 (by decide)) (Babylon.Tick60.mk 0 8640000 (by decide))).sexa_fraction = 0 := by
  decide

/-- info: 'Babylon.GeneratedTrace.trace_exactness' does not depend on any axioms -/
#guard_msgs in
#print axioms trace_exactness
end Babylon.GeneratedTrace
