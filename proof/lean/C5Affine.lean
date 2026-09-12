-- [AX-1] TOPOLOGY: Lean 4 Formalization of C5-REAL Affine Invariant
-- Isomorfismo de Curry-Howard: Demostración formal de prevención de Double-Free

inductive AffineResource
| uninitialized : AffineResource
| active : AffineResource
| consumed : AffineResource

-- Función de transición causal
def consume (r : AffineResource) : Option AffineResource :=
  match r with
  | AffineResource.active => some AffineResource.consumed
  | _ => none

-- Teorema [INV_C5_NO_DOUBLE_FREE]:
-- Consumir un recurso ya consumido siempre colapsa el estado a 'none' (Fallo termodinámico interceptado)
theorem no_double_free (r : AffineResource) (h : r = AffineResource.consumed) : consume r = none := by
  rw [h]
  rfl
