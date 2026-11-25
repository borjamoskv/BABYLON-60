-- Finite-width trace model used by examples/poc_lean4_emitter.rs.
-- This validates recorded transitions, not concurrent memory ordering.
set_option warningAsError true

namespace B60.ExampleSeqlockTrace

inductive Action where
  | WriteBegin | WriteEnd | Read deriving Repr, DecidableEq

structure SeqlockEvent where
  thread : BitVec 32
  seq : BitVec 64
  action : Action deriving Repr, DecidableEq

def validateTransition (currentSeq : BitVec 64) (writer : Option (BitVec 32))
    (event : SeqlockEvent) : Option (BitVec 64 × Option (BitVec 32)) :=
  match event.action with
  | .WriteBegin =>
      if writer.isNone && currentSeq % 2 == 0 && event.seq == currentSeq + 1 then
        some (event.seq, some event.thread)
      else none
  | .WriteEnd =>
      if writer == some event.thread && currentSeq % 2 == 1 && event.seq == currentSeq + 1 then
        some (event.seq, none)
      else none
  | .Read =>
      if writer.isNone && currentSeq % 2 == 0 && event.seq == currentSeq then
        some (currentSeq, none)
      else none

def isValidTrace (trace : List SeqlockEvent) (currentSeq : BitVec 64)
    (writer : Option (BitVec 32) := none) : Bool :=
  match trace with
  | [] => writer.isNone && currentSeq % 2 == 0
  | e :: es =>
      match validateTransition currentSeq writer e with
      | none => false
      | some (seq, nextWriter) => isValidTrace es seq nextWriter

def validCycle : List SeqlockEvent := [
  {thread := 1, seq := 1, action := .WriteBegin},
  {thread := 1, seq := 2, action := .WriteEnd},
  {thread := 2, seq := 2, action := .Read}]

-- Constructive, non-empty acceptance witness.
theorem inv_inhabited : ∃ trace, trace ≠ [] ∧ isValidTrace trace 0 = true :=
  ⟨validCycle, by decide, by decide⟩

/-- info: 'B60.ExampleSeqlockTrace.inv_inhabited' depends on axioms: [propext] -/
#guard_msgs in
#print axioms inv_inhabited

example : isValidTrace [
  {thread := 1, seq := 101, action := .WriteBegin},
  {thread := 2, seq := 2, action := .WriteEnd},
  {thread := 1, seq := 0, action := .Read}] 0 = false := by decide

example : isValidTrace [{thread := 1, seq := 1, action := .WriteBegin}] 0 = false := by decide
example : isValidTrace [
  {thread := 1, seq := 1, action := .WriteBegin},
  {thread := 2, seq := 2, action := .WriteEnd}] 0 = false := by decide
example : isValidTrace [
  {thread := 1, seq := 1, action := .WriteBegin},
  {thread := 1, seq := 4, action := .WriteEnd}] 0 = false := by decide
example : isValidTrace [{thread := 1, seq := 0, action := .Read}] 2 = false := by decide
example : isValidTrace [{thread := 1, seq := 0, action := .WriteEnd}] 0 = false := by decide
example : isValidTrace [
  {thread := 1, seq := 1, action := .WriteBegin},
  {thread := 1, seq := 1, action := .Read}] 0 = false := by decide
example : isValidTrace validCycle 0 = true := by decide
example : isValidTrace [
  {thread := 1, seq := 18446744073709551615, action := .WriteBegin},
  {thread := 1, seq := 0, action := .WriteEnd}] 18446744073709551614 = true := by decide

end B60.ExampleSeqlockTrace
