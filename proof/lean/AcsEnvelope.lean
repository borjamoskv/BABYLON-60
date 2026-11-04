/-
AUDITORÍA DE ALCANCE · 2026-10-25
Roundtrips y validez de schemas/COSE framing sobre bytes y dominios explícitos. No se verifican firmas, claves privadas, políticas o efectos. Los goldens son datos de prueba, no certificados hardware ni prueba universal de equivalencia con Rust.
Nombres públicos preservados; este cambio solo corrige comentarios.
Detalle: ../../docs/06_theory/AUDIT_LEAN_SCOPE_2026.md
-/

import CanonicalEnvelope

set_option warningAsError true

/-! Actual ACS deterministic CBOR schemas and COSE framing. Text is represented by
UTF-8 bytes without normalization, matching Rust `str.as_bytes()`. The codecs parse
wire bytes; cryptographic validity and external DER conversion are not axiomatized. -/
namespace B60.ACS
open B60.CBOR

infixr:65 " ⋈ " => pair

/-- Narrow a byte parser to a decidable schema predicate. -/
def restrict (c : Codec α) (p : α → Bool) : Codec α where
  encode := c.encode
  parse input := do
    let (x, tail) ← c.parse input
    if p x then some (x, tail) else none
  valid x := c.valid x ∧ p x = true
  roundtrip := by
    intro x h suffix
    simp [c.roundtrip x h.1 suffix, h.2]

def utf8 (s : String) : Bytes := s.toUTF8.data.toList

def text : Codec Bytes := restrict tstr validUtf8
def digest : Codec Bytes := restrict bstr (fun bs => bs.length == 32)
def u32 : Codec Nat := restrict uint (fun n => n < 2^32)
def principal : Codec Nat := restrict uint (fun n => n < 4)
def effect : Codec Nat := restrict uint (fun n => n < 10)
def enforcement : Codec Nat := restrict uint (fun n => n < 2)

/-- Exactly the 15 fields emitted by Rust guard_payload, in wire order. -/
abbrev Context := Bytes × Nat × Bytes × Nat × Bytes × Bytes × Bytes × List Nat ×
  Nat × Bytes × Bytes × Bytes × Bytes × Nat × Nat

def contextCodec : Codec Context := «prefix» [0x8f]
  (digest ⋈ principal ⋈ digest ⋈ uint ⋈ digest ⋈ digest ⋈ text ⋈ arrayOf effect ⋈
   uint ⋈ bstr ⋈ text ⋈ text ⋈ digest ⋈ enforcement ⋈ uint)

/-- Key discriminator and key bytes. P-256 point validity belongs to signature verification. -/
abbrev Key := Nat × Bytes
def keyCodec : Codec Key := «prefix» [0x82]
  (restrict (uint ⋈ bstr) (fun k => (k.1 == 0 && k.2.length == 32) || k.1 == 1))

abbrev Grant := Context × Key × Key × Nat × Nat × Nat
def grantCodec : Codec Grant :=
  «prefix» ([0x87] ++ text.encode (utf8 "BABYLON60_ACS_GRANT_V1"))
    (contextCodec ⋈ keyCodec ⋈ keyCodec ⋈ u32 ⋈ u32 ⋈ uint)

/-- Complete request plus signed provisioning context. Signature bytes are external. -/
abbrev Call := Context × Key × Nat × Nat × Nat × Bytes × Bytes × Bytes × Bytes ×
  Bytes × Bytes × Nat × Bytes × Nat × Nat

def callCodec : Codec Call :=
  «prefix» ([0x90] ++ text.encode (utf8 "BABYLON60_ACS_CALL_V1"))
    (contextCodec ⋈ keyCodec ⋈ u32 ⋈ u32 ⋈ uint ⋈ text ⋈ digest ⋈ digest ⋈ text ⋈
     text ⋈ text ⋈ uint ⋈ digest ⋈ uint ⋈ uint)

inductive Outcome where
  | rejected (reason : Bytes)
  | unknown (nonce expectedPost : Bytes)
  | verified (nonce pre observed evidence : Bytes)
deriving DecidableEq, Repr

def rejectedCodec := «prefix» [0] text
def unknownCodec := «prefix» [1] (digest ⋈ digest)
def verifiedCodec := «prefix» [2] (digest ⋈ digest ⋈ digest ⋈ digest)

def outcomeCodec : Codec Outcome where
  encode x := match x with
    | .rejected reason => 0x82 :: rejectedCodec.encode reason
    | .unknown nonce post => 0x83 :: unknownCodec.encode (nonce, post)
    | .verified nonce pre post evidence => 0x85 :: verifiedCodec.encode (nonce, pre, post, evidence)
  parse input := match input with
    | 0x82 :: rest => do
      let (reason, tail) ← rejectedCodec.parse rest
      pure (.rejected reason, tail)
    | 0x83 :: rest => do
      let ((nonce, post), tail) ← unknownCodec.parse rest
      pure (.unknown nonce post, tail)
    | 0x85 :: rest => do
      let ((nonce, pre, post, evidence), tail) ← verifiedCodec.parse rest
      pure (.verified nonce pre post evidence, tail)
    | _ => none
  valid x := match x with
    | .rejected reason => rejectedCodec.valid reason
    | .unknown nonce post => unknownCodec.valid (nonce, post)
    | .verified nonce pre post evidence => verifiedCodec.valid (nonce, pre, post, evidence)
  roundtrip := by
    intro x h suffix
    cases x with
    | rejected reason => simp [rejectedCodec.roundtrip reason h suffix]
    | unknown nonce post => simp [unknownCodec.roundtrip (nonce, post) h suffix]
    | verified nonce pre post evidence => simp [verifiedCodec.roundtrip (nonce, pre, post, evidence) h suffix]

abbrev Forensic := Bytes × Bytes × Bytes × Bytes × Nat × Bytes × Bytes × Bytes ×
  Bytes × Outcome × List Bytes

def forensicCodec : Codec Forensic :=
  «prefix» ([0x8c] ++ text.encode (utf8 "BABYLON60_AUTOPSY_V2"))
    (digest ⋈ digest ⋈ digest ⋈ text ⋈ uint ⋈ digest ⋈ digest ⋈ text ⋈ digest ⋈ outcomeCodec ⋈ arrayOf text)

inductive Algorithm where | ed25519 | p256
deriving DecidableEq, Repr

def protectedHeader (alg : Algorithm) : Bytes := match alg with
  | .ed25519 => [0xa1, 0x01, 0x27]
  | .p256 => [0xa1, 0x01, 0x26]

/-- COSE Sig_structure: array4, Signature1, protectedHeader algorithm, empty external AAD, payload. -/
def signatureStructure (alg : Algorithm) : Codec Bytes :=
  «prefix» ([0x84] ++ text.encode (utf8 "Signature1") ++ bstr.encode (protectedHeader alg) ++ [0x40]) bstr

/-- Tagged COSE_Sign1 with protectedHeader algorithm, empty unprotectedHeader map and opaque signature.
No assertion is made that an arbitrary signature verifies. -/
def coseSign1 (alg : Algorithm) : Codec (Bytes × Bytes) :=
  «prefix» ([0xd2, 0x84] ++ bstr.encode (protectedHeader alg) ++ [0xa0]) (bstr ⋈ bstr)

/-- Decidable schema domains; no classical choice is used. -/
instance callValidDec : DecidablePred callCodec.valid := fun x => by
  dsimp [callCodec, grantCodec, forensicCodec, contextCodec, keyCodec, outcomeCodec, rejectedCodec, unknownCodec, verifiedCodec, digest, principal, effect, enforcement, u32, text, restrict, «prefix», pair, arrayOf, uint, bstr, tstr, blob]
  infer_instance
instance grantValidDec : DecidablePred grantCodec.valid := fun x => by
  dsimp [callCodec, grantCodec, forensicCodec, contextCodec, keyCodec, outcomeCodec, rejectedCodec, unknownCodec, verifiedCodec, digest, principal, effect, enforcement, u32, text, restrict, «prefix», pair, arrayOf, uint, bstr, tstr, blob]
  infer_instance
instance forensicValidDec : DecidablePred forensicCodec.valid := fun x => by
  rcases x with ⟨a,b,c,d,e,f,g,h,i,j,k⟩
  cases j <;> dsimp [callCodec, grantCodec, forensicCodec, contextCodec, keyCodec, outcomeCodec, rejectedCodec, unknownCodec, verifiedCodec, digest, principal, effect, enforcement, u32, text, restrict, «prefix», pair, arrayOf, uint, bstr, tstr, blob] <;> infer_instance

/-- Parse a nested schema inside a CBOR byte string, rejecting noncanonical inner bytes. -/
def wrapped (c : Codec α) [DecidablePred c.valid] : Codec α where
  encode x := bstr.encode (c.encode x)
  parse wire := do
    let (payload, tail) ← bstr.parse wire
    let x ← decodeChecked c payload
    pure (x, tail)
  valid x := c.valid x ∧ (c.encode x).length < 2^64
  roundtrip := by
    intro x h tail
    simp [bstr.roundtrip (c.encode x) h.2 tail, decodeChecked_encode c x h.1]

/-- Typed complete COSE: the bstr payload is parsed using the supplied ACS schema. -/
def typedCose (alg : Algorithm) (c : Codec α) [DecidablePred c.valid] : Codec (α × Bytes) :=
  «prefix» ([0xd2, 0x84] ++ bstr.encode (protectedHeader alg) ++ [0xa0]) (wrapped c ⋈ bstr)

instance typedCoseValidDec (alg : Algorithm) (c : Codec α) [DecidablePred c.valid] :
    DecidablePred (typedCose alg c).valid := fun x => by
  change Decidable ((c.valid x.1 ∧ (c.encode x.1).length < 2^64) ∧ x.2.length < 2^64)
  infer_instance

/-- Typed Sig_structure verifies the inner schema, not just bstr framing. -/
def typedSignatureStructure (alg : Algorithm) (c : Codec α) [DecidablePred c.valid] : Codec α :=
  «prefix» ([0x84] ++ text.encode (utf8 "Signature1") ++ bstr.encode (protectedHeader alg) ++ [0x40]) (wrapped c)

instance typedSignatureValidDec (alg : Algorithm) (c : Codec α) [DecidablePred c.valid] :
    DecidablePred (typedSignatureStructure alg c).valid := fun x => by
  change Decidable (c.valid x ∧ (c.encode x).length < 2^64)
  infer_instance

/-- The typed COSE theorem includes both inner schema decoding and outer byte framing. -/
theorem typedCose_decode_encode (alg : Algorithm) (c : Codec α) [DecidablePred c.valid]
    (x : α × Bytes) (h : (typedCose alg c).valid x) :
    decodeChecked (typedCose alg c) ((typedCose alg c).encode x) = some x :=
  decodeChecked_encode _ x h

theorem typedCose_encode_decode (alg : Algorithm) (c : Codec α) [DecidablePred c.valid]
    (wire : Bytes) (x : α × Bytes) (h : decodeChecked (typedCose alg c) wire = some x) :
    (typedCose alg c).encode x = wire := encode_decodeChecked _ wire x h

theorem typedCose_decode_valid (alg : Algorithm) (c : Codec α) [DecidablePred c.valid]
    (wire : Bytes) (x : α × Bytes) (h : decodeChecked (typedCose alg c) wire = some x) :
    (typedCose alg c).valid x := decodeChecked_valid _ wire x h

theorem typedSignature_decode_encode (alg : Algorithm) (c : Codec α) [DecidablePred c.valid]
    (x : α) (h : (typedSignatureStructure alg c).valid x) :
    decodeChecked (typedSignatureStructure alg c) ((typedSignatureStructure alg c).encode x) = some x :=
  decodeChecked_encode _ x h

theorem typedSignature_encode_decode (alg : Algorithm) (c : Codec α) [DecidablePred c.valid]
    (wire : Bytes) (x : α) (h : decodeChecked (typedSignatureStructure alg c) wire = some x) :
    (typedSignatureStructure alg c).encode x = wire := encode_decodeChecked _ wire x h

theorem typedSignature_decode_valid (alg : Algorithm) (c : Codec α) [DecidablePred c.valid]
    (wire : Bytes) (x : α) (h : decodeChecked (typedSignatureStructure alg c) wire = some x) :
    (typedSignatureStructure alg c).valid x := decodeChecked_valid _ wire x h

-- The schema-facing entry points enforce validity in addition to byte canonicity.
def decodeCall := decodeChecked callCodec
def decodeGrant := decodeChecked grantCodec
def decodeForensic := decodeChecked forensicCodec

theorem call_decoded_valid (wire : Bytes) (x : Call) (h : decodeCall wire = some x) :
    callCodec.valid x := decodeChecked_valid _ wire x h

theorem grant_decoded_valid (wire : Bytes) (x : Grant) (h : decodeGrant wire = some x) :
    grantCodec.valid x := decodeChecked_valid _ wire x h

theorem forensic_decoded_valid (wire : Bytes) (x : Forensic) (h : decodeForensic wire = some x) :
    forensicCodec.valid x := decodeChecked_valid _ wire x h

/-- Universal payload roundtrips over the explicit valid domains, not fixture enumeration. -/
theorem call_decode_encode (x : Call) (h : callCodec.valid x) :
    decodeCall (callCodec.encode x) = some x := decodeChecked_encode callCodec x h

theorem grant_decode_encode (x : Grant) (h : grantCodec.valid x) :
    decodeGrant (grantCodec.encode x) = some x := decodeChecked_encode grantCodec x h

theorem forensic_decode_encode (x : Forensic) (h : forensicCodec.valid x) :
    decodeForensic (forensicCodec.encode x) = some x := decodeChecked_encode forensicCodec x h

theorem call_encode_decode (wire : Bytes) (x : Call) (h : decodeCall wire = some x) :
    callCodec.encode x = wire := encode_decodeChecked callCodec wire x h

theorem grant_encode_decode (wire : Bytes) (x : Grant) (h : decodeGrant wire = some x) :
    grantCodec.encode x = wire := encode_decodeChecked grantCodec wire x h

theorem forensic_encode_decode (wire : Bytes) (x : Forensic) (h : decodeForensic wire = some x) :
    forensicCodec.encode x = wire := encode_decodeChecked forensicCodec wire x h

theorem call_injective (x y : Call) (hx : callCodec.valid x) (hy : callCodec.valid y)
    (h : callCodec.encode x = callCodec.encode y) : x = y := encode_injective callCodec x y hx hy h

theorem cose_decode_encode (alg : Algorithm) (x : Bytes × Bytes) (h : (coseSign1 alg).valid x) :
    decode (coseSign1 alg) ((coseSign1 alg).encode x) = some x := decode_encode _ x h

theorem cose_encode_decode (alg : Algorithm) (wire : Bytes) (x : Bytes × Bytes)
    (h : decode (coseSign1 alg) wire = some x) : (coseSign1 alg).encode x = wire := encode_decode _ wire x h

theorem signature_decode_encode (alg : Algorithm) (payload : Bytes) (h : (signatureStructure alg).valid payload) :
    decode (signatureStructure alg) ((signatureStructure alg).encode payload) = some payload := decode_encode _ payload h

theorem signature_encode_decode (alg : Algorithm) (wire payload : Bytes)
    (h : decode (signatureStructure alg) wire = some payload) : (signatureStructure alg).encode payload = wire := encode_decode _ wire payload h

/-- info: 'B60.ACS.call_decode_encode' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms call_decode_encode
/-- info: 'B60.ACS.grant_decode_encode' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms grant_decode_encode
/-- info: 'B60.ACS.forensic_decode_encode' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms forensic_decode_encode
/-- info: 'B60.ACS.call_encode_decode' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms call_encode_decode
/-- info: 'B60.ACS.call_injective' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms call_injective
/-- info: 'B60.ACS.call_decoded_valid' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms call_decoded_valid
/-- info: 'B60.ACS.typedCose_decode_encode' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms typedCose_decode_encode
/-- info: 'B60.ACS.typedCose_encode_decode' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms typedCose_encode_decode
/-- info: 'B60.ACS.typedCose_decode_valid' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms typedCose_decode_valid
/-- info: 'B60.ACS.typedSignature_decode_encode' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms typedSignature_decode_encode
/-- info: 'B60.ACS.typedSignature_encode_decode' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms typedSignature_encode_decode
/-- info: 'B60.ACS.typedSignature_decode_valid' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms typedSignature_decode_valid

-- Hex literals are only golden test data, never the semantic parser.
def nibble (c : Char) : Nat := if c.toNat ≤ 57 then c.toNat - 48 else c.toNat - 87
def unhex : List Char → Bytes
  | a :: b :: rest => UInt8.ofNat (16 * nibble a + nibble b) :: unhex rest
  | _ => []
def hex (s : String) : Bytes := unhex s.toList

def fill32 (b : UInt8) : Bytes := List.replicate 32 b

/-! Runtime encoder goldens: tests/acs_cbor_golden.txt. Fixed software test keys only. -/
def golden_root : Bytes := hex "d04ab232742bb4ab3a1368bd4615e4e6d0224ab71a016baf8520a332c9778737"
def golden_delegated : Bytes := hex "a09aa5f47a6759802ff955f8dc2d2a14a5c99d23be97f864127ff9383455a4f0"
def golden_grant : Bytes := hex "846a5369676e61747572653143a10127405901418776424142594c4f4e36305f4143535f4752414e545f56318f58200101010101010101010101010101010101010101010101010101010101010101035820d04ab232742bb4ab3a1368bd4615e4e6d0224ab71a016baf8520a332c97787370758200202020202020202020202020202020202020202020202020202020202020202582001010101010101010101010101010101010101010101010101010101010101016f66696c653a2f2f2f616c6c6f7765648200010740726163735f73636f7065645f726561645f7631613158200303030303030303030303030303030303030303030303030303030303030303000a82005820d04ab232742bb4ab3a1368bd4615e4e6d0224ab71a016baf8520a332c977873782005820a09aa5f47a6759802ff955f8dc2d2a14a5c99d23be97f864127ff9383455a4f01901f51910921878"
def golden_call : Bytes := hex "9075424142594c4f4e36305f4143535f43414c4c5f56318f58200101010101010101010101010101010101010101010101010101010101010101035820d04ab232742bb4ab3a1368bd4615e4e6d0224ab71a016baf8520a332c97787370758200202020202020202020202020202020202020202020202020202020202020202582001010101010101010101010101010101010101010101010101010101010101016f66696c653a2f2f2f616c6c6f7765648200010740726163735f73636f7065645f726561645f7631613158200303030303030303030303030303030303030303030303030303030303030303000a82005820a09aa5f47a6759802ff955f8dc2d2a14a5c99d23be97f864127ff9383455a4f01901f5191092187865302e312e3058200404040404040404040404040404040404040404040404040404040404040404582005050505050505050505050505050505050505050505050505050505050505056766735f726561647466696c653a2f2f2f616c6c6f7765642f646174617466696c653a2f2f2f616c6c6f7765642f6461746118645820060606060606060606060606060606060606060606060606060606060606060607186e"
def golden_call_signing : Bytes := hex "846a5369676e61747572653143a10127405901bf9075424142594c4f4e36305f4143535f43414c4c5f56318f58200101010101010101010101010101010101010101010101010101010101010101035820d04ab232742bb4ab3a1368bd4615e4e6d0224ab71a016baf8520a332c97787370758200202020202020202020202020202020202020202020202020202020202020202582001010101010101010101010101010101010101010101010101010101010101016f66696c653a2f2f2f616c6c6f7765648200010740726163735f73636f7065645f726561645f7631613158200303030303030303030303030303030303030303030303030303030303030303000a82005820a09aa5f47a6759802ff955f8dc2d2a14a5c99d23be97f864127ff9383455a4f01901f5191092187865302e312e3058200404040404040404040404040404040404040404040404040404040404040404582005050505050505050505050505050505050505050505050505050505050505056766735f726561647466696c653a2f2f2f616c6c6f7765642f646174617466696c653a2f2f2f616c6c6f7765642f6461746118645820060606060606060606060606060606060606060606060606060606060606060607186e"
def golden_forensic : Bytes := hex "8c74424142594c4f4e36305f4155544f5053595f563258200101010101010101010101010101010101010101010101010101010101010101582002020202020202020202020202020202020202020202020202020202020202025820030303030303030303030303030303030303030303030303030303030303030369706f6c6963792d76310458200505050505050505050505050505050505050505050505050505050505050505582006060606060606060606060606060606060606060606060606060606060606066a646976657267656e636558200707070707070707070707070707070707070707070707070707070707070707830158200808080808080808080808080808080808080808080808080808080808080808582009090909090909090909090909090909090909090909090909090909090909098169726570726f64756365"
def golden_forensic_signing : Bytes := hex "846a5369676e61747572653143a10127405901498c74424142594c4f4e36305f4155544f5053595f563258200101010101010101010101010101010101010101010101010101010101010101582002020202020202020202020202020202020202020202020202020202020202025820030303030303030303030303030303030303030303030303030303030303030369706f6c6963792d76310458200505050505050505050505050505050505050505050505050505050505050505582006060606060606060606060606060606060606060606060606060606060606066a646976657267656e636558200707070707070707070707070707070707070707070707070707070707070707830158200808080808080808080808080808080808080808080808080808080808080808582009090909090909090909090909090909090909090909090909090909090909098169726570726f64756365"
def golden_cose_ed : Bytes := hex "d28443a10127a05901498c74424142594c4f4e36305f4155544f5053595f563258200101010101010101010101010101010101010101010101010101010101010101582002020202020202020202020202020202020202020202020202020202020202025820030303030303030303030303030303030303030303030303030303030303030369706f6c6963792d76310458200505050505050505050505050505050505050505050505050505050505050505582006060606060606060606060606060606060606060606060606060606060606066a646976657267656e636558200707070707070707070707070707070707070707070707070707070707070707830158200808080808080808080808080808080808080808080808080808080808080808582009090909090909090909090909090909090909090909090909090909090909098169726570726f64756365584033333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333"
def golden_cose_p256 : Bytes := hex "d28443a10126a043010203584044444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444"

def fixtureContext : Context :=
  (fill32 1, 3, golden_root, 7, fill32 2, fill32 1, utf8 "file:///allowed",
   [0, 1], 7, [], utf8 "acs_scoped_read_v1", utf8 "1", fill32 3, 0, 10)

def fixtureGrant : Grant := (fixtureContext, (0, golden_root), (0, golden_delegated), 501, 4242, 120)
def fixtureCall : Call :=
  (fixtureContext, (0, golden_delegated), 501, 4242, 120, utf8 "0.1.0",
   fill32 4, fill32 5, utf8 "fs_read", utf8 "file:///allowed/data",
   utf8 "file:///allowed/data", 100, fill32 6, 7, 110)
def fixtureForensic : Forensic :=
  (fill32 1, fill32 2, fill32 3, utf8 "policy-v1", 4, fill32 5, fill32 6,
   utf8 "divergence", fill32 7, .unknown (fill32 8) (fill32 9), [utf8 "reproduce"])

-- Long runtime vectors are compared by tests/test_lean_envelope_bijection.py against
-- the real Rust encoder; universal byte roundtrips above are proved independently.

-- Complete byte parser rejects malformed, noncanonical, algorithm-confused or trailing inputs.
example : decode (coseSign1 .ed25519) [0xd2, 0x84, 0x43, 0xa1, 1, 0x27, 0xa0, 0x40] = none := by decide +kernel
example : decode (coseSign1 .ed25519) [0xd2, 0x84, 0x43, 0xa1, 1, 0x26, 0xa0, 0x40, 0x40] = none := by decide +kernel
example : decode (coseSign1 .ed25519) [0xd2, 0x84, 0x43, 0xa1, 1, 0x27, 0xa0, 0x58, 0, 0x40] = none := by decide +kernel
example : decode text [0x61, 0xff] = none := by decide +kernel
example : decode text [0x62, 0xc0, 0x80] = none := by decide +kernel
example : decode text [0x63, 0xed, 0xa0, 0x80] = none := by decide +kernel
example : decode text [0x64, 0xf4, 0x90, 0x80, 0x80] = none := by decide +kernel
example : decodeChecked (typedCose .ed25519 forensicCodec)
    [0xd2, 0x84, 0x43, 0xa1, 1, 0x27, 0xa0, 0x40, 0x40] = none := by decide +kernel
example : decode digest [0x41, 1] = none := by decide +kernel
example : decode keyCodec [0x82, 2, 0x40] = none := by decide +kernel
example : decode uint [0x18, 0x17] = none := by decide +kernel
example : decode uint [0x1b, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff] = some (2^64-1) := by decide +kernel
example : decode text (text.encode (utf8 "ñ漢🙂")) = some (utf8 "ñ漢🙂") := by decide +kernel

end B60.ACS


namespace B60.ACS
open B60.CBOR
private def hexDigit (n : Nat) : Char := Char.ofNat (if n < 10 then n + 48 else n + 87)
def toHex (bs : Bytes) : String := String.ofList (bs.flatMap fun b => [hexDigit (b.toNat / 16), hexDigit (b.toNat % 16)])
private def isHex (s : String) : Bool := s.toList.length % 2 == 0 && s.toList.all (fun c =>
  (c ≥ '0' && c ≤ '9') || (c ≥ 'a' && c ≤ 'f'))

def runtimeVectors : List (String × Bytes) :=
  [("root", golden_root), ("delegated", golden_delegated),
   ("grant", (typedSignatureStructure .ed25519 grantCodec).encode fixtureGrant),
   ("call", callCodec.encode fixtureCall),
   ("call_signing", (typedSignatureStructure .ed25519 callCodec).encode fixtureCall),
   ("forensic", forensicCodec.encode fixtureForensic),
   ("forensic_signing", (typedSignatureStructure .ed25519 forensicCodec).encode fixtureForensic),
   ("cose_ed", (typedCose .ed25519 forensicCodec).encode (fixtureForensic, List.replicate 64 0x33)),
   ("cose_p256", (coseSign1 .p256).encode ([1,2,3], List.replicate 64 0x44))]

def run (args : List String) : IO UInt32 := do
  match args with
  | [] =>
    for (name, bytes) in runtimeVectors do IO.println s!"ACS_{name}={toHex bytes}"
    return 0
  | [kind, raw] =>
    if !isHex raw then return 1
    let bytes := hex raw
    let accepted := match kind with
      | "--decode-call" => (decodeCall bytes).isSome
      | "--decode-grant" => (decodeChecked (typedSignatureStructure .ed25519 grantCodec) bytes).isSome
      | "--decode-forensic" => (decodeForensic bytes).isSome
      | "--decode-cose-forensic" => (decodeChecked (typedCose .ed25519 forensicCodec) bytes).isSome
      | _ => false
    return if accepted then 0 else 1
  | _ => return 1
end B60.ACS

def main (args : List String) : IO UInt32 := B60.ACS.run args
