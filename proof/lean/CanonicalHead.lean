/-
AUDITORÍA DE ALCANCE · 2026-10-25
Leyes de representación de cabeceras y enteros CBOR bajo cotas explícitas. No son validación de todos los tipos de CBOR, criptografía, permisos ni correspondencia automática con otro parser.
Nombres públicos preservados; este cambio solo corrige comentarios.
Detalle: ../../docs/06_theory/AUDIT_LEAN_SCOPE_2026.md
-/

import Init

namespace B60.CBOR
set_option warningAsError true

def encodeBE : Nat → Nat → List UInt8
  | 0, _ => []
  | k + 1, n => UInt8.ofNat (n / 256^k) :: encodeBE k (n % 256^k)

def decodeBE : Nat → List UInt8 → Option (Nat × List UInt8)
  | 0, xs => some (0, xs)
  | k + 1, b :: xs => do
      let (v, rest) ← decodeBE k xs
      pure (b.toNat * 256^k + v, rest)
  | _ + 1, [] => none

theorem decodeBE_encodeBE_suffix (k n : Nat) (suffix : List UInt8)
    (hn : n < 256^k) : decodeBE k (encodeBE k n ++ suffix) = some (n, suffix) := by
  induction k generalizing n with
  | zero =>
      have : n = 0 := by simpa using hn
      subst n
      rfl
  | succ k ih =>
      have hp : 0 < 256^k := Nat.pow_pos (by decide)
      have hq : n / 256^k < 256 := by
        apply (Nat.div_lt_iff_lt_mul hp).2
        simpa [Nat.pow_succ, Nat.mul_comm] using hn
      have hr : n % 256^k < 256^k := Nat.mod_lt n hp
      simp only [encodeBE, List.cons_append, decodeBE]
      rw [ih _ hr]
      have he := Nat.mod_add_div n (256^k)
      change some ((UInt8.ofNat (n / 256^k)).toNat * 256^k + n % 256^k, suffix) = some (n, suffix)
      rw [UInt8.toNat_ofNat_of_lt' hq]
      rw [Nat.mul_comm, Nat.add_comm]
      rw [he]

attribute [irreducible] encodeBE decodeBE

def headByte (major info : Nat) : UInt8 := UInt8.ofNat (major * 32 + info)

def encodeHead (major n : Nat) : List UInt8 :=
  if n < 24 then [headByte major n]
  else if n < 256 then headByte major 24 :: encodeBE 1 n
  else if n < 65536 then headByte major 25 :: encodeBE 2 n
  else if n < 4294967296 then headByte major 26 :: encodeBE 4 n
  else headByte major 27 :: encodeBE 8 n

def decodePayload (major width minimum : Nat) (xs : List UInt8) : Option (Nat × Nat × List UInt8) := do
  let (n, rest) ← decodeBE width xs
  if n < minimum then none else some (major, n, rest)

theorem decodePayload_encodeBE (major width minimum n : Nat) (suffix : List UInt8)
    (hn : n < 256^width) (hmin : ¬ n < minimum) :
    decodePayload major width minimum (encodeBE width n ++ suffix) = some (major, n, suffix) := by
  unfold decodePayload
  rw [decodeBE_encodeBE_suffix width n suffix hn]
  simp [hmin]

def decodeHead : List UInt8 → Option (Nat × Nat × List UInt8)
  | [] => none
  | b :: xs =>
      let major := b.toNat / 32
      let info := b.toNat % 32
      if info < 24 then some (major, info, xs)
      else if info = 24 then decodePayload major 1 24 xs
      else if info = 25 then decodePayload major 2 256 xs
      else if info = 26 then decodePayload major 4 65536 xs
      else if info = 27 then decodePayload major 8 4294967296 xs
      else none

theorem headByte_parts (major info : Nat) (hm : major < 8) (hi : info < 32) :
    (headByte major info).toNat / 32 = major ∧
    (headByte major info).toNat % 32 = info := by
  have hb : major * 32 + info < 256 := by omega
  simp only [headByte, UInt8.toNat_ofNat_of_lt' hb]
  constructor
  · rw [Nat.add_comm, Nat.add_mul_div_right _ _ (by decide)]
    rw [Nat.div_eq_of_lt hi, Nat.zero_add]
  · rw [Nat.mul_add_mod_self_right, Nat.mod_eq_of_lt hi]

theorem decodeHead_encodeHead_suffix (major n : Nat) (suffix : List UInt8)
    (hm : major < 8) (hn : n < 2^64) :
    decodeHead (encodeHead major n ++ suffix) = some (major, n, suffix) := by
  by_cases h24 : n < 24
  · have hp := headByte_parts major n hm (by omega)
    simp only [encodeHead, ite_eq_left h24, List.singleton_append, decodeHead, hp.1, hp.2]
  · by_cases h256 : n < 256
    · have hp := headByte_parts major 24 hm (by decide)
      have hd := decodePayload_encodeBE major 1 24 n suffix (by simpa only [Nat.reducePow] using h256) h24
      simp [encodeHead, h24, h256, decodeHead, hp.1, hp.2, hd]
    · by_cases h65536 : n < 65536
      · have hp := headByte_parts major 25 hm (by decide)
        have hd := decodePayload_encodeBE major 2 256 n suffix (by simpa only [Nat.reducePow] using h65536) h256
        simp [encodeHead, h24, h256, h65536, decodeHead, hp.1, hp.2, hd]
      · by_cases h32 : n < 4294967296
        · have hp := headByte_parts major 26 hm (by decide)
          have hd := decodePayload_encodeBE major 4 65536 n suffix (by simpa only [Nat.reducePow] using h32) h65536
          simp [encodeHead, h24, h256, h65536, h32, decodeHead, hp.1, hp.2, hd]
        · have hp := headByte_parts major 27 hm (by decide)
          have hd := decodePayload_encodeBE major 8 4294967296 n suffix (by simpa only [Nat.reducePow] using hn) h32
          simp [encodeHead, h24, h256, h65536, h32, decodeHead, hp.1, hp.2, hd]

/-- info: 'B60.CBOR.decodeBE_encodeBE_suffix' depends on axioms: [propext] -/
#guard_msgs in
#print axioms decodeBE_encodeBE_suffix

/-- info: 'B60.CBOR.decodeHead_encodeHead_suffix' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms decodeHead_encodeHead_suffix

end B60.CBOR
