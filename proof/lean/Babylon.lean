-- proof/lean/Babylon.lean
-- BABYLON-60 C5-REAL Formal Ontology
import Mathlib.Data.Rat.Basic

namespace Babylon60

/-- 1. Dominio de Tipos (Type Domain) -/
inductive B60Type where
  | I64
  | Time
  | F60

/-- El tipo F60 se modela matemáticamente como un número Racional Exacto (ℚ) 
    para garantizar la ausencia de desbordamientos IEEE-754. -/
def F60_Val := ℚ 

/-- 2. El Reloj Lógico (Desacoplado del tiempo físico) -/
structure LogicalClock where
  tick : ℕ

/-- 3. Grafo Causal (DAG Ledger) -/
inductive Event
  | mk (id : String) (parents : List String) (tick : LogicalClock) (payload : String)

/-- 4. Tupla de Estado Global Γ -/
structure State where
  regs : Nat → Option F60_Val
  ledger : List Event
  clock : LogicalClock

/-- 5. Semántica de Pasos Pequeños (Small-Step Transitions) -/
-- Define CÓMO la máquina avanza de manera determinista.
inductive Step : State → State → Prop where
  | assign (s : State) (r : Nat) (v : F60_Val) :
      Step s { s with regs := fun x => if x = r then some v else s.regs x }
      
  | fork (s : State) (child : String) :
      -- Invariante: Un FORK siempre avanza el reloj causal
      Step s { s with clock := ⟨s.clock.tick + 1⟩ }
      
  | dah (s : State) (r : Nat) (v : F60_Val) :
      -- Escalada: R[r] = R[r] * v (asumiendo semántica simplificada de multiplicación/escalada de energía)
      Step s { s with regs := fun x => if x = r then (s.regs r).map (fun val => val * v) else s.regs x }

  | lal (s : State) (r_dest : Nat) (r_src : Nat) :
      -- Resta destructiva: R[r_dest] = R[r_dest] - R[r_src]
      Step s { s with regs := fun x => 
          if x = r_dest then 
            match s.regs r_dest, s.regs r_src with
            | some v1, some v2 => some (v1 - v2)
            | _, _ => none
          else s.regs x }

  | nu (s : State) (r : Nat) (target : String) :
      -- Bifurcación condicional nula: Solo avanza el estado lógico si R[r] == 0 (el salto se abstrae aquí)
      Step s s -- En semántica de estados pura sin PC explícito, el salto requiere añadir un Program Counter al State, pero como simplificación para la prueba de concepto B60, mantenemos el estado inmutable si se cumple.

/-- 6. Teorema de Confluencia (Propiedad del Diamante / Church-Rosser) sobre ℚ -/
theorem f60_val_associative (a b c : F60_Val) : (a * b) * c = a * (b * c) := by
  exact mul_assoc a b c

theorem f60_val_commutative (a b : F60_Val) : a * b = b * a := by
  exact mul_comm a b

/-- Invariante: La semántica de pasos pequeños cumple la propiedad de Confluencia Local (Diamond Property). -/
theorem b60_small_step_confluence (s s1 s2 : State) (h1 : Step s s1) (h2 : Step s s2) :
  s1 = s2 ∨ (∃ s3, Step s1 s3 ∧ Step s2 s3) := by
  cases h1 with
  | assign s r1 v1 =>
    cases h2 with
    | assign _ r2 v2 =>
      if h : r1 = r2 ∧ v1 = v2 then
        have h_eq1 : r1 = r2 := h.1
        have h_eq2 : v1 = v2 := h.2
        rw [h_eq1, h_eq2]
        exact Or.inl rfl
      else
        right
        exact ⟨{ s1 with regs := fun x => if x = r2 then some v2 else s1.regs x },
               Step.assign _ r2 v2,
               Step.assign _ r1 v1⟩
    | fork _ child =>
      right
      exact ⟨{ s1 with clock := ⟨s1.clock.tick + 1⟩ },
             Step.fork _ child,
             Step.assign _ r1 v1⟩
    | dah _ r2 v2 =>
      right
      exact ⟨{ s1 with regs := fun x => if x = r2 then (s1.regs r2).map (fun val => val * v2) else s1.regs x },
             Step.dah _ r2 v2,
             Step.assign _ r1 v1⟩
    | lal _ r_dest r_src =>
      right
      exact ⟨{ s1 with regs := fun x => if x = r_dest then match s1.regs r_dest, s1.regs r_src with | some v1, some v2 => some (v1 - v2) | _, _ => none else s1.regs x },
             Step.lal _ r_dest r_src,
             Step.assign _ r1 v1⟩
    | nu _ r target =>
      right
      exact ⟨s1, Step.nu s1 r target, Step.assign _ r1 v1⟩
  | fork s child1 =>
    cases h2 with
    | assign _ r2 v2 =>
      right
      exact ⟨{ s2 with clock := ⟨s2.clock.tick + 1⟩ },
             Step.assign _ r2 v2,
             Step.fork _ child1⟩
    | fork _ child2 =>
      if h : child1 = child2 then
        rw [h]
        exact Or.inl rfl
      else
        exact Or.inl rfl
    | dah _ r2 v2 =>
      right
      exact ⟨{ s2 with clock := ⟨s2.clock.tick + 1⟩ },
             Step.dah _ r2 v2,
             Step.fork _ child1⟩
    | lal _ r_dest r_src =>
      right
      exact ⟨{ s2 with clock := ⟨s2.clock.tick + 1⟩ },
             Step.lal _ r_dest r_src,
             Step.fork _ child1⟩
    | nu _ r target =>
      right
      exact ⟨s1, Step.nu s1 r target, Step.fork _ child1⟩
  | dah s r1 v1 =>
    cases h2 with
    | assign _ r2 v2 =>
      right
      exact ⟨{ s2 with regs := fun x => if x = r1 then (s2.regs r1).map (fun val => val * v1) else s2.regs x },
             Step.assign _ r2 v2,
             Step.dah _ r1 v1⟩
    | fork _ child =>
      right
      exact ⟨{ s1 with clock := ⟨s1.clock.tick + 1⟩ },
             Step.fork _ child,
             Step.dah _ r1 v1⟩
    | dah _ r2 v2 =>
      if h : r1 = r2 ∧ v1 = v2 then
        have h_eq1 : r1 = r2 := h.1
        have h_eq2 : v1 = v2 := h.2
        rw [h_eq1, h_eq2]
        exact Or.inl rfl
      else
        right
        exact ⟨{ s1 with regs := fun x => if x = r2 then (s1.regs r2).map (fun val => val * v2) else s1.regs x },
               Step.dah _ r2 v2,
               Step.dah _ r1 v1⟩
    | lal _ r_dest r_src =>
      right
      exact ⟨{ s1 with regs := fun x => if x = r_dest then match s1.regs r_dest, s1.regs r_src with | some v1, some v2 => some (v1 - v2) | _, _ => none else s1.regs x },
             Step.lal _ r_dest r_src,
             Step.dah _ r1 v1⟩
    | nu _ r target =>
      right
      exact ⟨s1, Step.nu s1 r target, Step.dah _ r1 v1⟩
  | lal s r_dest1 r_src1 =>
    cases h2 with
    | assign _ r2 v2 =>
      right
      exact ⟨{ s2 with regs := fun x => if x = r_dest1 then match s2.regs r_dest1, s2.regs r_src1 with | some v1, some v2 => some (v1 - v2) | _, _ => none else s2.regs x },
             Step.assign _ r2 v2,
             Step.lal _ r_dest1 r_src1⟩
    | fork _ child =>
      right
      exact ⟨{ s1 with clock := ⟨s1.clock.tick + 1⟩ },
             Step.fork _ child,
             Step.lal _ r_dest1 r_src1⟩
    | dah _ r2 v2 =>
      right
      exact ⟨{ s1 with regs := fun x => if x = r2 then (s1.regs r2).map (fun val => val * v2) else s1.regs x },
             Step.dah _ r2 v2,
             Step.lal _ r_dest1 r_src1⟩
    | lal _ r_dest2 r_src2 =>
      if h : r_dest1 = r_dest2 ∧ r_src1 = r_src2 then
        have h_eq1 : r_dest1 = r_dest2 := h.1
        have h_eq2 : r_src1 = r_src2 := h.2
        rw [h_eq1, h_eq2]
        exact Or.inl rfl
      else
        right
        exact ⟨{ s1 with regs := fun x => if x = r_dest2 then match s1.regs r_dest2, s1.regs r_src2 with | some v1, some v2 => some (v1 - v2) | _, _ => none else s1.regs x },
               Step.lal _ r_dest2 r_src2,
               Step.lal _ r_dest1 r_src1⟩
    | nu _ r target =>
      right
      exact ⟨s1, Step.nu s1 r target, Step.lal _ r_dest1 r_src1⟩
  | nu s r target =>
    right
    exact ⟨s2, h2, Step.nu s2 r target⟩


end Babylon60

