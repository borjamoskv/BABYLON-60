/-
AUDITORÍA DE ALCANCE · 2026-10-26
Parser CSV y bucle IO sobre el modelo BabylonTrace. No hay cota probada O(1) para líneas/Nat arbitrarios ni medición física. Los mensajes describen la aceptación o rechazo de registros por el modelo; no acreditan rendimiento físico.
Nombres públicos y lógica preservados; mensajes revisados el 2026-10-26 para describir solo el modelo.
Detalle: ../../docs/06_theory/AUDIT_LEAN_SCOPE_2026.md
-/

import BabylonTrace

open B60.Ledger

namespace B60.Oracle

-- 1. Parser de una línea CSV de longitud variable (CSV: Thread,Seq,Action)
def parseLine (line : String) : Option Event :=
  -- Eliminar retornos de carro manuales
  let chars := line.toList.filter (fun c => c != '\n' && c != '\r')
  let cleanLine := String.ofList chars
  match cleanLine.splitOn "," with
  | [tStr, sStr, aStr] =>
    match tStr.toNat?, sStr.toNat? with
    | some threadId, some seq =>
      match aStr with
      | "0" => some { threadId := threadId, seq := seq, action := Action.writeBegin }
      | "1" => some { threadId := threadId, seq := seq, action := Action.writeEnd }
      | "2" => some { threadId := threadId, seq := seq, action := Action.read }
      | _ => none
    | _, _ => none
  | _ => none

-- 2. Bucle de lectura por líneas, sin cota global de recursos demostrada
-- Lee datos y aplica la función abstracta step; no mide entropía física.
partial def consumeStream (h : IO.FS.Handle) (state : LockState) : IO UInt32 := do
  let line ← h.getLine
  if line == "" then
    IO.println "[TRACE_CSV] Fin de entrada: los registros leídos fueron aceptados por el modelo de secuencias."
    return 0
  else
    match parseLine line with
    | none => 
        IO.println s!"[TRACE_CSV] Registro CSV inválido: {line}"
        return 1
    | some ev =>
        -- Comprobar el siguiente registro con la función abstracta step.
        match step state ev with
        | none => 
            IO.println s!"[TRACE_CSV] Registro rechazado por el modelo: seq={ev.seq}, thread={ev.threadId}."
            return 2 -- Código de rechazo del registro según el modelo.
        | some nextState => consumeStream h nextState

end B60.Oracle

-- 3. Punto de Entrada Físico (Compilación a Binario C)
def main (args : List String) : IO UInt32 := do
  if args.length == 0 then
    IO.println "Uso: ./oracle <trace.csv>"
    return 1
  
  let path := args.head!
  IO.println s!"[TRACE_CSV] Lectura de traza: {path}"
  
  let h ← IO.FS.Handle.mk path IO.FS.Mode.read
  let initialState : B60.Ledger.LockState := { seq := 0, writer := none }
  
  B60.Oracle.consumeStream h initialState
