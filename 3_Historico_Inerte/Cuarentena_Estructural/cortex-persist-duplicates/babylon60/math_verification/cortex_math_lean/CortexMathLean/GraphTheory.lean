-- [C5-REAL] GraphTheory.lean
-- Sovereign Component: K-Colorability Formalization
-- CORTEX-TAINT: taint:moskv1:formal_sat:gen3:0xa1b2

def Graph (V : Type) := V → V → Prop

def is_symmetric {V : Type} (G : Graph V) : Prop :=
  ∀ u v, G u v → G v u

def is_irreflexive {V : Type} (G : Graph V) : Prop :=
  ∀ v, ¬ G v v

-- Una coloración válida asigna a cada nodo un color (Nat < k) tal que nodos adyacentes no compartan color.
def valid_coloring {V : Type} (G : Graph V) (k : Nat) (color : V → Nat) : Prop :=
  (∀ v, color v < k) ∧ (∀ u v, G u v → color u ≠ color v)

-- Un grafo es K-Colorable si existe al menos una coloración válida.
def KColorable {V : Type} (G : Graph V) (k : Nat) : Prop :=
  ∃ color : V → Nat, valid_coloring G k color
