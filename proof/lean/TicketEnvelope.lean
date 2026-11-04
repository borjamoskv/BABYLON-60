/-
AUDITORÍA DE ALCANCE · 2026-10-25
Roundtrips e inyectividad de representación de payloads con shape explícita. Firma DER externa y opaca; no se prueban autenticidad, frescura, autorización ni ejecución. Vectores y ejemplos no sustituyen esos controles.
Nombres públicos preservados; este cambio solo corrige comentarios.
Detalle: ../../docs/06_theory/AUDIT_LEAN_SCOPE_2026.md
-/

import CanonicalEnvelope

set_option warningAsError true
set_option maxRecDepth 8192
set_option maxHeartbeats 2000000

/- The real Rust signing payload, not COSE_Sign1. DER is external. This file
   proves representation roundtrips, not signature validity or authorization. -/
namespace B60.Ticket
open B60.CBOR

abbrev Control := Bytes × Bytes × Bytes
def controlTriple : Codec Control := «prefix» [0x83] (pair tstr (pair tstr tstr))

def controlCodec : Codec (Option Control) where
  encode x := match x with
    | none => [0xf6]
    | some c => controlTriple.encode c
  parse input := match input with
    | 0xf6 :: rest => some (none, rest)
    | _ => do
      let (c, rest) ← controlTriple.parse input
      pure (some c, rest)
  valid x := match x with
    | none => True
    | some c => controlTriple.valid c
  roundtrip := by
    intro x h suffix
    cases x with
    | none => rfl
    | some c =>
      change (do
        let (v, rest) ← controlTriple.parse (controlTriple.encode c ++ suffix)
        pure (some v, rest)) = some (some c, suffix)
      rw [controlTriple.roundtrip c h suffix]
      rfl

/-- Rust signing_bytes fields in exact order, retaining raw UTF-8 bytes. -/
abbrev Payload := Bytes × Bytes × Bytes × Nat × Bytes × Bool × Option Control ×
  Nat × Nat × Nat × Bytes × Bytes × Nat

def payloadCodec : Codec Payload := «prefix» [0x8d]
  (pair tstr (pair tstr (pair tstr (pair uint (pair bstr (pair boolean
    (pair controlCodec (pair uint (pair uint (pair uint (pair bstr (pair bstr uint))))))))))))

/-- Shared RFC 3629 validator; no String witness or duplicate implementation. -/
def utf8 : Bytes → Bool := CBOR.validUtf8
def text (s : String) : Bytes := s.toUTF8.data.toList

/-- Structural schema only. Freshness/signature/authorization belong to Rust. -/
def shape (p : Payload) : Bool :=
  let (domain, app, action, channel, digest, _, control, _, _, _, nonce, key, version) := p
  domain == text "BABYLON-DESKTOP-DISPATCH-v1" && utf8 app && utf8 action &&
  channel ≤ 3 && digest.length == 32 && nonce.length == 32 &&
  key.length == 65 && key.head? == some 4 && version == 1 &&
  match control with
  | none => true
  | some (node, role, title) => utf8 node && utf8 role && utf8 title

instance payloadValidDecidable (p : Payload) : Decidable (payloadCodec.valid p) := by
  rcases p with ⟨domain, app, action, channel, digest, policy, control, epoch, issued, expiry, nonce, key, version⟩
  cases control <;>
    dsimp only [payloadCodec, «prefix», pair, tstr, bstr, blob, uint, boolean,
      controlCodec, controlTriple] <;> infer_instance

/-- Canonical 13-field payload domain. Signature DER is deliberately not included. -/
abbrev Ticket := { p : Payload // payloadCodec.valid p ∧ shape p = true }

def encode (t : Ticket) : Bytes := payloadCodec.encode t.val
def decode (input : Bytes) : Option Ticket := do
  let p ← CBOR.decode payloadCodec input
  if h : payloadCodec.valid p ∧ shape p = true then some ⟨p, h⟩ else none

theorem decode_encode (t : Ticket) : decode (encode t) = some t := by
  simp [decode, encode, CBOR.decode_encode payloadCodec t.val t.property.1, t.property]

theorem encode_decode (input : Bytes) (t : Ticket) (h : decode input = some t) :
    encode t = input := by
  unfold decode at h
  cases hp : CBOR.decode payloadCodec input with
  | none => simp [hp] at h
  | some p =>
    simp only [hp] at h
    dsimp only [Bind.bind, Option.bind] at h
    split at h
    next hv =>
      cases h
      exact CBOR.encode_decode payloadCodec input p hp
    next => contradiction

theorem encode_injective (a b : Ticket) (h : encode a = encode b) : a = b := by
  have hd := congrArg decode h
  rw [decode_encode, decode_encode] at hd
  exact Option.some.inj hd

theorem decoded_valid (input : Bytes) (t : Ticket) (_ : decode input = some t) :
    payloadCodec.valid t.val ∧ shape t.val = true := t.property

/-- Two existing external fields, not an invented combined wire encoding. -/
abbrev SignedTicket := Ticket × Bytes
def encodeExternal (s : SignedTicket) : Bytes × Bytes := (encode s.1, s.2)
def decodeExternal (fields : Bytes × Bytes) : Option SignedTicket := do
  let payload ← decode fields.1
  pure (payload, fields.2)

theorem decode_encode_external (s : SignedTicket) :
    decodeExternal (encodeExternal s) = some s := by
  simp [decodeExternal, encodeExternal, decode_encode]

theorem encode_decode_external (fields : Bytes × Bytes) (s : SignedTicket)
    (h : decodeExternal fields = some s) : encodeExternal s = fields := by
  unfold decodeExternal at h
  cases hp : decode fields.1 with
  | none => simp [hp] at h
  | some p =>
    simp only [hp] at h
    dsimp only [Bind.bind, Option.bind, Pure.pure] at h
    have h := Option.some.inj h
    cases h
    exact Prod.ext (encode_decode fields.1 p hp) rfl

def hexDigit (c : Char) : Option Nat :=
  if '0' ≤ c ∧ c ≤ '9' then some (c.toNat - '0'.toNat)
  else if 'a' ≤ c ∧ c ≤ 'f' then some (c.toNat - 'a'.toNat + 10)
  else if 'A' ≤ c ∧ c ≤ 'F' then some (c.toNat - 'A'.toNat + 10)
  else none

def parseHexChars : List Char → Option Bytes
  | [] => some []
  | a :: b :: rest => do
    let x ← hexDigit a
    let y ← hexDigit b
    let tail ← parseHexChars rest
    pure (UInt8.ofNat (16*x+y) :: tail)
  | _ => none

def parseHex (s : String) : Option Bytes := parseHexChars s.toList
def hex (bs : Bytes) : String := String.ofList (bs.flatMap fun b =>
  [Char.ofNat (if b.toNat / 16 < 10 then 48 + b.toNat / 16 else 87 + b.toNat / 16),
   Char.ofNat (if b.toNat % 16 < 10 then 48 + b.toNat % 16 else 87 + b.toNat % 16)])

/-- Public P-256 generator point. No private key and no hardware claim. -/
def generatorKey : Bytes := (parseHex
  ("046b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296" ++
   "4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5")).getD []

def fixturePayload (ax edge : Bool) : Payload :=
  (text "BABYLON-DESKTOP-DISPATCH-v1", text (if edge then "á😀" else "a"), text "b",
   (if ax then 2 else 0), List.replicate 32 8, true,
   (if ax then some (text "id", text "AXButton", text "Export") else none),
   (if edge then 18446744073709551615 else 7), (if edge then 24 else 1000),
   (if edge then 65536 else 1030), List.replicate 32 9, generatorKey, 1)

def fixture (ax edge : Bool) : Ticket :=
  ⟨fixturePayload ax edge, by cases ax <;> cases edge <;> decide⟩

example : utf8 (text "á😀") = true := by decide
example : utf8 [0xc0, 0x80] = false := by decide
example : utf8 [0xe0, 0x80, 0x80] = false := by decide
example : utf8 [0xed, 0xa0, 0x80] = false := by decide
example : utf8 [0xf4, 0x90, 0x80, 0x80] = false := by decide
example : utf8 [0xf0, 0x90] = false := by decide

example : decode [0x8d] = none := by decide
example : decode (encode (fixture false false) ++ [0]) = none := by decide +kernel
example : decode ([0x98, 0x0d] ++ (encode (fixture false false)).drop 1) = none := by decide
example : decode (payloadCodec.encode
    (text "BABYLON-DESKTOP-DISPATCH-v1", [0xff], text "b", 0, List.replicate 32 8,
     true, none, 7, 1000, 1030, List.replicate 32 9, generatorKey, 1)) = none := by decide +kernel

/-- info: 'B60.Ticket.decode_encode' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms decode_encode
/-- info: 'B60.Ticket.encode_decode' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms encode_decode
/-- info: 'B60.Ticket.encode_injective' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms encode_injective
/-- info: 'B60.Ticket.decode_encode_external' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms decode_encode_external
/-- info: 'B60.Ticket.encode_decode_external' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms encode_decode_external
/-- info: 'B60.Ticket.utf8' does not depend on any axioms -/
#guard_msgs in
#print axioms utf8

end B60.Ticket

/-- Standalone golden-vector emitter and canonical/schema acceptance checker. -/
def main (args : List String) : IO UInt32 := do
  match args with
  | ["--decode", value] =>
    match B60.Ticket.parseHex value with
    | none => IO.println "REJECT_HEX"; return 1
    | some bytes =>
      match B60.Ticket.decode bytes with
      | none => IO.println "REJECT_CBOR_OR_SCHEMA"; return 1
      | some _ => IO.println "ACCEPT_CANONICAL_TICKET_PAYLOAD"; return 0
  | [] =>
    for (name, ax, edge) in [("CLI", false, false), ("AX", true, false), ("EDGE", false, true)] do
      IO.println ("TICKET_" ++ name ++ "=" ++ B60.Ticket.hex (B60.Ticket.encode (B60.Ticket.fixture ax edge)))
    return 0
  | _ => IO.eprintln "usage: TicketEnvelope [--decode HEX]"; return 2
