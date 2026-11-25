/-
AUDITORÍA DE ALCANCE · 2026-10-26
Ejemplo de renderizado Html en Infoview. Los números son argumentos de demostración; el texto de bloqueo no ejecuta una denegación, no mide exergía ni certifica una frontera de autoridad.
Comprobado el 2026-10-26 con cinco módulos Lean de ProofWidgets compilados desde fuentes locales en un temporal.
El import y la API son correctos; el entorno habitual necesita esos artefactos. No se instaló ni actualizó ningún paquete.
Nombres públicos y lógica preservados; mensajes revisados el 2026-10-26 para describir solo el modelo.
Detalle: ../../docs/06_theory/AUDIT_LEAN_SCOPE_2026.md
-/

import ProofWidgets.Component.HtmlDisplay
import Lean

open Lean ProofWidgets

-- [ESTRATO UI]: Renderizado de argumentos numéricos ilustrativos en el IDE.
def AlertaColapso (energia_req energia_disp : Nat) : Html :=
  Html.element "div" #[("style", "padding: 1rem; border: 2px solid red; background-color: #330000; color: white; border-radius: 8px; font-family: monospace;")] #[
    Html.element "h2" #[("style", "color: #ff4444; margin: 0 0 10px 0;")] #[Html.text "Ejemplo de estado de presupuesto"],
    Html.element "p" #[] #[Html.text s!"Valores de ejemplo: solicitado={energia_req}; disponible={energia_disp}. No son una medición de energía."],
    Html.element "p" #[("style", "font-weight: bold; color: #ff9999;")] #[Html.text "Vista de demostración; no ejecuta ni bloquea operaciones."]
  ]

-- El comando #html inyecta el React/DOM directamente en el VS Code Infoview.
#html AlertaColapso 500 100
