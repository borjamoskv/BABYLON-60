/-
AUDITORÍA DE ALCANCE · 2026-10-26
FIXTURE NEGATIVO: el generador Rust produce esta lista para que Lean rechace la afirmación de aceptación.
El rechazo de decide es esperado; no importar como biblioteca positiva ni invertir la conclusión a false.
Verificar también un control nominal y el diagnóstico: un error de imports no cuenta como rechazo semántico.
Nombres públicos preservados; este cambio solo corrige comentarios.
Detalle: ../../docs/06_theory/AUDIT_LEAN_SCOPE_2026.md
-/

import BabylonTrace

namespace B60.Ledger

def auto_execution_trace : List Event := [
  { threadId := 1, seq := 1, action := Action.writeBegin },
  { threadId := 2, seq := 1, action := Action.read },
  { threadId := 1, seq := 2, action := Action.writeEnd }
]

-- ⚡ El Teorema A+ (Proof by Reflection)
theorem trace_is_paradox_free_auto : validateTrace auto_execution_trace = true := by
  decide

end B60.Ledger
