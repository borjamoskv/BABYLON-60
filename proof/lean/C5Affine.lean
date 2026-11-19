/-
AUDITORÍA DE ALCANCE · 2026-10-25
Autómata puro sobre valores duplicables. El teorema rechaza el constructor consumed; no implementa propiedad de recursos lineales, liberación de memoria ni ausencia de double-free en un programa externo.
Nombres públicos preservados; este cambio solo corrige comentarios.
Detalle: ../../docs/06_theory/AUDIT_LEAN_SCOPE_2026.md
-/

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
