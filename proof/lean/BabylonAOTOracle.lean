/-
AUDITORÍA DE ALCANCE · 2026-10-26
Parser binario y bucle IO con chunks de 8192 bytes y resto. Esto no prueba memoria total O(1), zero-copy o ausencia de asignaciones. Las salidas de consola son mensajes del programa, no certificados de efectos físicos.
Nombres públicos y lógica preservados; mensajes revisados el 2026-10-26 para describir solo el modelo.
Detalle: ../../docs/06_theory/AUDIT_LEAN_SCOPE_2026.md
-/

import BabylonTrace

open B60.Ledger

namespace B60.AOTOracle

-- 1. Decodificador de un UInt64 ya cargado: [ seq (32) | thread_id (24) | action (8) ]
def decodePacked (packed : UInt64) : Option Event :=
  let actionCode := packed.toUInt8
  let threadId := ((packed >>> 8) &&& 0xFFFFFF).toNat
  let seq := (packed >>> 32).toNat
  match actionCode.toNat with
  | 0 => some { threadId := threadId, seq := seq, action := Action.writeBegin }
  | 1 => some { threadId := threadId, seq := seq, action := Action.writeEnd }
  | 2 => some { threadId := threadId, seq := seq, action := Action.read }
  | _ => none

-- Extraer un UInt64 (Little Endian) desde ByteArray
def readUInt64LE (b : ByteArray) (offset : Nat) : UInt64 :=
  let b0 := b.get! offset
  let b1 := b.get! (offset + 1)
  let b2 := b.get! (offset + 2)
  let b3 := b.get! (offset + 3)
  let b4 := b.get! (offset + 4)
  let b5 := b.get! (offset + 5)
  let b6 := b.get! (offset + 6)
  let b7 := b.get! (offset + 7)
  (b0.toUInt64) |||
  (b1.toUInt64 <<< 8) |||
  (b2.toUInt64 <<< 16) |||
  (b3.toUInt64 <<< 24) |||
  (b4.toUInt64 <<< 32) |||
  (b5.toUInt64 <<< 40) |||
  (b6.toUInt64 <<< 48) |||
  (b7.toUInt64 <<< 56)

-- 2. Bucle binario con chunks de 8KB; no prueba memoria total constante
partial def consumeStream (h : IO.FS.Handle) (state : LockState) (count : Nat)
    (pending : ByteArray := ByteArray.empty) : IO UInt32 := do
  let chunk ← h.read 8192
  if chunk.isEmpty then
    if pending.isEmpty then
      IO.println s!"[TRACE_BIN] Fin de entrada: {count} registros aceptados por el modelo de secuencias."
      return 0
    else
      IO.println s!"[TRACE_BIN] Registro incompleto en byte {count * 8}: {pending.size} bytes pendientes."
      return 1
  else
    -- `read` puede devolver menos bytes que los solicitados. Conservar como
    -- máximo siete bytes entre lecturas y rechazar un registro incompleto al EOF.
    let buffer := pending ++ chunk
    let num_events := buffer.size / 8
    let mut currState := state
    for i in [0:num_events] do
      let offset := i * 8
      let packed := readUInt64LE buffer offset
      match decodePacked packed with
      | none =>
          IO.println s!"[TRACE_BIN] Registro binario inválido en byte {count * 8 + offset}."
          return 1
      | some ev =>
          match step currState ev with
          | none =>
              IO.println s!"[TRACE_BIN] Registro rechazado por el modelo: seq={ev.seq}, thread={ev.threadId}."
              return 2
          | some nextState =>
              currState := nextState
    let remaining := buffer.extract (num_events * 8) buffer.size
    consumeStream h currState (count + num_events) remaining

-- 3. Punto de Entrada Físico
def main (args : List String) : IO UInt32 := do
  if args.length == 0 then
    IO.println "Uso: ./babylon_aot_oracle <trace.bin>"
    return 1
  let path := args.head!
  IO.println s!"[TRACE_BIN] Lectura de traza: {path}"
  let h ← IO.FS.Handle.mk path IO.FS.Mode.read
  let initialState : LockState := { seq := 0, writer := none }
  consumeStream h initialState 0

end B60.AOTOracle

def main : List String → IO UInt32 := B60.AOTOracle.main
