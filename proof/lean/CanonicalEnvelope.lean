/-
AUDITORÍA DE ALCANCE · 2026-10-25
Leyes de codecs y constructores sobre dominios declarados; Codec.roundtrip es hipótesis genérica y los constructores proporcionan pruebas concretas. No certifica toda la norma CBOR/UTF-8, recursos del parser o implementación externa.
Nombres públicos preservados; este cambio solo corrige comentarios.
Detalle: ../../docs/06_theory/AUDIT_LEAN_SCOPE_2026.md
-/

import CanonicalHead

set_option warningAsError true

namespace B60.CBOR

abbrev Bytes := List UInt8

def between (b : UInt8) (lo hi : Nat) : Bool := decide (lo ≤ b.toNat ∧ b.toNat ≤ hi)

/-- RFC 3629 byte validation, rejecting overlong forms, surrogates and > U+10FFFF.
    Structural recursion avoids the classical witness construction in String. -/
def validUtf8 : Bytes → Bool
  | [] => true
  | b :: bs =>
    if b.toNat < 128 then validUtf8 bs else
    match bs with
    | c :: cs =>
      if between b 0xc2 0xdf && between c 0x80 0xbf then validUtf8 cs else
      match cs with
      | d :: ds =>
        if ((b == 0xe0 && between c 0xa0 0xbf) ||
            ((between b 0xe1 0xec || between b 0xee 0xef) && between c 0x80 0xbf) ||
            (b == 0xed && between c 0x80 0x9f)) && between d 0x80 0xbf then validUtf8 ds else
        match ds with
        | e :: es =>
          if ((b == 0xf0 && between c 0x90 0xbf) ||
              (between b 0xf1 0xf3 && between c 0x80 0xbf) ||
              (b == 0xf4 && between c 0x80 0x8f)) && between d 0x80 0xbf && between e 0x80 0xbf
          then validUtf8 es else false
        | [] => false
      | [] => false
    | [] => false

/-- A byte codec with an independently executed prefix parser. Validity bounds
    wire integers and lengths; schemas can add semantic and UTF-8 conditions. -/
structure Codec (α : Type) where
  encode : α → Bytes
  parse : Bytes → Option (α × Bytes)
  valid : α → Prop
  roundtrip : ∀ x, valid x → ∀ suffix, parse (encode x ++ suffix) = some (x, suffix)

/-- Consume the entire input and reject every noncanonical representation. -/
def decode (c : Codec α) (input : Bytes) : Option α :=
  match c.parse input with
  | some (x, []) => if c.encode x = input then some x else none
  | _ => none

theorem decode_encode (c : Codec α) (x : α) (h : c.valid x) :
    decode c (c.encode x) = some x := by
  have hr := c.roundtrip x h []
  simp only [List.append_nil] at hr
  simp [decode, hr]

theorem encode_decode (c : Codec α) (input : Bytes) (x : α)
    (h : decode c input = some x) : c.encode x = input := by
  unfold decode at h
  split at h
  next y he =>
    split at h
    next hc => cases h; exact hc
    next => contradiction
  next => contradiction

theorem encode_injective (c : Codec α) (x y : α)
    (hx : c.valid x) (hy : c.valid y) (he : c.encode x = c.encode y) : x = y := by
  have h := congrArg (decode c) he
  rw [decode_encode c x hx, decode_encode c y hy] at h
  exact Option.some.inj h

/-- A schema-facing decoder also enforces the declared domain. -/
def decodeChecked (c : Codec α) [DecidablePred c.valid] (input : Bytes) : Option α := do
  let x ← decode c input
  if c.valid x then some x else none

theorem decodeChecked_encode (c : Codec α) [DecidablePred c.valid]
    (x : α) (h : c.valid x) : decodeChecked c (c.encode x) = some x := by
  simp [decodeChecked, decode_encode c x h, h]

theorem decodeChecked_valid (c : Codec α) [DecidablePred c.valid]
    (input : Bytes) (x : α) (h : decodeChecked c input = some x) : c.valid x := by
  unfold decodeChecked at h
  cases he : decode c input with
  | none => simp [he] at h
  | some y =>
    simp only [he] at h
    change (if c.valid y then some y else none) = some x at h
    split at h
    next hv => cases h; exact hv
    next => contradiction

theorem encode_decodeChecked (c : Codec α) [DecidablePred c.valid]
    (input : Bytes) (x : α) (h : decodeChecked c input = some x) : c.encode x = input := by
  unfold decodeChecked at h
  cases he : decode c input with
  | none => simp [he] at h
  | some y =>
    simp only [he] at h
    change (if c.valid y then some y else none) = some x at h
    split at h
    next => cases h; exact encode_decode c input x he
    next => contradiction

def pair (a : Codec α) (b : Codec β) : Codec (α × β) where
  encode x := a.encode x.1 ++ b.encode x.2
  parse input := do
    let (x, rest) ← a.parse input
    let (y, tail) ← b.parse rest
    pure ((x, y), tail)
  valid x := a.valid x.1 ∧ b.valid x.2
  roundtrip := by
    intro x h suffix
    simp [List.append_assoc, a.roundtrip x.1 h.1, b.roundtrip x.2 h.2]

def «prefix» (header : Bytes) (c : Codec α) : Codec α where
  encode x := header ++ c.encode x
  parse input := if input.take header.length = header then c.parse (input.drop header.length) else none
  valid := c.valid
  roundtrip := by
    intro x h suffix
    simp [List.append_assoc, c.roundtrip x h]

def uint : Codec Nat where
  encode n := encodeHead 0 n
  parse input := do
    let (major, n, rest) ← decodeHead input
    if major = 0 then some (n, rest) else none
  valid n := n < 2^64
  roundtrip := by
    intro n h suffix
    simp [decodeHead_encodeHead_suffix 0 n suffix (by decide) h]

def blob (major : Nat) (hm : major < 8) : Codec Bytes where
  encode bs := encodeHead major bs.length ++ bs
  parse input := do
    let (tag, n, rest) ← decodeHead input
    if tag = major ∧ n ≤ rest.length then some (rest.take n, rest.drop n) else none
  valid bs := bs.length < 2^64
  roundtrip := by
    intro bs h suffix
    simp [List.append_assoc, decodeHead_encodeHead_suffix major bs.length (bs ++ suffix) hm h]

def bstr : Codec Bytes := blob 2 (by decide)

/-- Text byte framing. Schema validity must additionally require UTF-8.
    This codec intentionally preserves bytes without Unicode normalization. -/
def tstr : Codec Bytes := blob 3 (by decide)

def boolean : Codec Bool where
  encode b := [if b then 0xf5 else 0xf4]
  parse input := match input with
    | 0xf4 :: rest => some (false, rest)
    | 0xf5 :: rest => some (true, rest)
    | _ => none
  valid _ := True
  roundtrip := by intro x _ suffix; cases x <;> simp

def null : Codec Unit where
  encode _ := [0xf6]
  parse input := match input with
    | 0xf6 :: rest => some ((), rest)
    | _ => none
  valid _ := True
  roundtrip := by intro x _ suffix; cases x; rfl

/-- A finite array parser consumes exactly the number of items declared by CBOR. -/
def parseMany (c : Codec α) : Nat → Bytes → Option (List α × Bytes)
  | 0, input => some ([], input)
  | n+1, input => do
      let (x, rest) ← c.parse input
      let (xs, tail) ← parseMany c n rest
      pure (x :: xs, tail)

def encodeMany (c : Codec α) : List α → Bytes
  | [] => []
  | x :: xs => c.encode x ++ encodeMany c xs

theorem parseMany_encodeMany (c : Codec α) (xs : List α)
    (h : ∀ x ∈ xs, c.valid x) (suffix : Bytes) :
    parseMany c xs.length (encodeMany c xs ++ suffix) = some (xs, suffix) := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
    have hx := h x (by simp)
    have ht : ∀ y ∈ xs, c.valid y := by intro y hy; exact h y (by simp [hy])
    simp [parseMany, encodeMany, List.append_assoc, c.roundtrip x hx, ih ht]

def arrayOf (c : Codec α) : Codec (List α) where
  encode xs := encodeHead 4 xs.length ++ encodeMany c xs
  parse input := do
    let (major, n, rest) ← decodeHead input
    if major = 4 then parseMany c n rest else none
  valid xs := xs.length < 2^64 ∧ ∀ x ∈ xs, c.valid x
  roundtrip := by
    intro xs h suffix
    simp [List.append_assoc, decodeHead_encodeHead_suffix 4 xs.length
      (encodeMany c xs ++ suffix) (by decide) h.1, parseMany_encodeMany c xs h.2]

end B60.CBOR

/-- info: 'B60.CBOR.decode_encode' depends on axioms: [propext] -/
#guard_msgs in
#print axioms B60.CBOR.decode_encode
/-- info: 'B60.CBOR.encode_decode' depends on axioms: [propext] -/
#guard_msgs in
#print axioms B60.CBOR.encode_decode
/-- info: 'B60.CBOR.encode_injective' depends on axioms: [propext] -/
#guard_msgs in
#print axioms B60.CBOR.encode_injective
/-- info: 'B60.CBOR.decodeChecked_valid' depends on axioms: [propext] -/
#guard_msgs in
#print axioms B60.CBOR.decodeChecked_valid
/-- info: 'B60.CBOR.arrayOf' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms B60.CBOR.arrayOf

section
attribute [local semireducible] B60.CBOR.decodeBE B60.CBOR.encodeBE

-- Executable boundary regressions complement (not replace) the universal proofs.
example : B60.CBOR.decode B60.CBOR.uint [0x18, 0x17] = none := by decide
example : B60.CBOR.decode B60.CBOR.uint [0x19, 0, 0x18] = none := by decide
example : B60.CBOR.decode B60.CBOR.bstr [0x42, 1] = none := by decide
example : B60.CBOR.decode B60.CBOR.bstr [0x41, 1, 0] = none := by decide
example : B60.CBOR.decode B60.CBOR.bstr [0x5f, 0xff] = none := by decide
example : B60.CBOR.decode (B60.CBOR.arrayOf B60.CBOR.uint) [0x82, 0, 0x18, 0x18] =
    some [0, 24] := by decide
example : B60.CBOR.decode (B60.CBOR.arrayOf B60.CBOR.uint) [0x82, 0] = none := by decide

end

/-- info: 'B60.CBOR.validUtf8' does not depend on any axioms -/
#guard_msgs in
#print axioms B60.CBOR.validUtf8

example : B60.CBOR.validUtf8 [0xc3, 0xa1, 0xf0, 0x9f, 0x98, 0x80] = true := by decide
example : B60.CBOR.validUtf8 [0xc0, 0x80] = false := by decide
example : B60.CBOR.validUtf8 [0xed, 0xa0, 0x80] = false := by decide
example : B60.CBOR.validUtf8 [0xf4, 0x90, 0x80, 0x80] = false := by decide
example : B60.CBOR.validUtf8 [0xf0, 0x9f] = false := by decide
