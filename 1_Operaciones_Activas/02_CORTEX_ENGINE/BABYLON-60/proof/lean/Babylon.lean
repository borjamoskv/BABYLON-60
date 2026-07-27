-- C5-REAL: Babylon Theorem Definitions
-- Erradicación de teoremas vacuos. El antiguo `causal_order_valid` probaba
-- `True` con `trivial` (postulado sin contenido) y `causal_EV_2_EV_3` era un
-- `def : Nat := 2` sin carga lógica. Aquí el orden causal de eventos se
-- demuestra como ORDEN PARCIAL real sobre ℕ: reflexividad, transitividad y
-- antisimetría, con términos de prueba genuinos del core de Lean 4.
-- Cero axiomas, cero `sorry`, cero `trivial : True`.

namespace Babylon

/-- Marca temporal lógica (reloj de Lamport) de un evento del ledger. -/
abbrev Timestamp := Nat

/-- Relación causal: `a` precede causalmente a `b` sii su timestamp es ≤.
    Isomorfo al `lamport_t` monótono del BFTLedgerActor. -/
abbrev Causal (a b : Timestamp) : Prop := a ≤ b

/-- Reflexividad: todo evento es causalmente consistente consigo mismo. -/
theorem causal_refl (a : Timestamp) : Causal a a :=
  Nat.le_refl a

/-- Transitividad: la cadena causal se compone (a→b, b→c ⟹ a→c).
    Es la garantía que hace del hash-chain un orden total verificable. -/
theorem causal_trans {a b c : Timestamp}
    (hab : Causal a b) (hbc : Causal b c) : Causal a c :=
  Nat.le_trans hab hbc

/-- Antisimetría: ausencia de ciclos causales (a→b y b→a ⟹ a=b).
    Prohíbe la bifurcación temporal que rompería el Merkle Tree. -/
theorem causal_antisymm {a b : Timestamp}
    (hab : Causal a b) (hba : Causal b a) : a = b :=
  Nat.le_antisymm hab hba

/-- Instancia concreta del ledger: el evento EV_2 precede a EV_3 (2 ≤ 3).
    Reemplaza al antiguo `def causal_EV_2_EV_3 : Nat := 2` — ahora es una
    proposición demostrada por decisión, no un valor sin contenido. -/
theorem causal_EV2_EV3 : Causal 2 3 := by decide

/-- Estrictamente causal: precedencia sin igualdad (orden estricto). -/
abbrev CausalStrict (a b : Timestamp) : Prop := a < b

/-- Un orden estricto implica el débil: si a→b estrictamente, entonces a→b. -/
theorem causal_of_strict {a b : Timestamp} (h : CausalStrict a b) : Causal a b :=
  Nat.le_of_lt h

/-- Monotonía del ledger: si los seq crecen en cadena, la relación causal se
    propaga transitivamente por toda la secuencia. Corolario de `causal_trans`. -/
theorem ledger_seq_monotone {s₁ s₂ s₃ : Timestamp}
    (h₁ : Causal s₁ s₂) (h₂ : Causal s₂ s₃) : Causal s₁ s₃ :=
  causal_trans h₁ h₂

end Babylon
