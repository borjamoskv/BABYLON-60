/-
AUDITORÍA DE ALCANCE · 2026-10-26
Parser CSV y clasificador del autómata de umbrales NavierStokesBKM. Sus mensajes describen flags del autómata, sin afirmar singularidad o regularidad PDE; no hay cota probada O(1) de memoria o coste de parseo.
Nombres públicos y lógica preservados; mensajes revisados el 2026-10-26 para describir solo el modelo.
Detalle: ../../docs/06_theory/AUDIT_LEAN_SCOPE_2026.md
-/

import NavierStokesBKM

open B60.NavierStokes

namespace B60.NavierStokes.Oracle

/-- Parser de una línea CSV variable: tick,actionCode,payload. Sin cota O(1) de recursos demostrada. -/
def parseLine (line : String) : Option FluidEvent :=
  let chars := line.toList.filter (fun c => c != '\n' && c != '\r')
  let cleanLine := String.ofList chars
  match cleanLine.splitOn "," with
  | [tickStr, actionCodeStr, payloadStr] =>
    match tickStr.toNat?, actionCodeStr.toNat?, payloadStr.toNat? with
    | some tick, some 0, some delta =>
      some { tick := tick, action := VortexAction.vorticityStep delta }
    | some tick, some 1, some lip =>
      some { tick := tick, action := VortexAction.directionalCurvature lip }
    | some tick, some 2, some bkmDelta =>
      some { tick := tick, action := VortexAction.bkmAccumulate bkmDelta }
    | some tick, some 3, _ =>
      some { tick := tick, action := VortexAction.haltCriticalCandidate }
    | _, _, _ => none
  | _ => none

/-- Bucle IO sobre un registro abstracto. No se demuestra memoria total constante ni coste físico. -/
partial def consumeStream (h : IO.FS.Handle) (state : FluidState) : IO UInt32 := do
  let line ← h.getLine
  if line == "" then
    -- Fin del flujo: describir los flags del autómata.
    if state.isQuarantined then
      IO.println s!"[FLUID_MODEL] Clasificación del autómata: candidato por umbral; tick={state.tick}, acumulado={state.accumulatedBkm}, indicador={state.lipschitzModulus}. No demuestra singularidad PDE."
      return 10 -- Código de clasificación numérica; no prueba de singularidad continua
    else if state.isDepleted then
      IO.println s!"[FLUID_MODEL] Clasificación del autómata: isDepleted=true; indicador={state.lipschitzModulus}. No demuestra regularidad PDE."
      return 0
    else
      IO.println s!"[FLUID_MODEL] Clasificación del autómata: sin cuarentena e isDepleted=false; acumulado={state.accumulatedBkm}. No demuestra regularidad PDE."
      return 0
  else
    match parseLine line with
    | none =>
      IO.println s!"[FLUID_MODEL] Registro CSV inválido: {line}"
      return 1
    | some ev =>
      let nextState := step state ev
      consumeStream h nextState

end B60.NavierStokes.Oracle

def main (args : List String) : IO UInt32 := do
  if args.length == 0 then
    IO.println "Uso: ./navier_stokes_oracle <trace.csv>"
    return 1
  let path := args.head!
  IO.println s!"[FLUID_MODEL] Lectura de eventos: {path}"
  let h ← IO.FS.Handle.mk path IO.FS.Mode.read
  B60.NavierStokes.Oracle.consumeStream h B60.NavierStokes.initialState
