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

end Babylon60
