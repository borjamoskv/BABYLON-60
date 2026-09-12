import ProofWidgets.Component.HtmlDisplay
import Lean

open Lean ProofWidgets

-- [ESTRATO UI]: Renderizado de estado termodinámico en el IDE.
def AlertaColapso (energia_req energia_disp : Nat) : Html :=
  Html.element "div" #[("style", "padding: 1rem; border: 2px solid red; background-color: #330000; color: white; border-radius: 8px; font-family: monospace;")] #[
    Html.element "h2" #[("style", "color: #ff4444; margin: 0 0 10px 0;")] #[Html.text "🚨 COLAPSO AXIOMÁTICO (Lóbulo Inhibidor)"],
    Html.element "p" #[] #[Html.text s!"El LLM (Corteza) intentó extraer {energia_req} unidades de exergía, pero el sistema solo dispone de {energia_disp}."],
    Html.element "p" #[("style", "font-weight: bold; color: #ff9999;")] #[Html.text "Acción Termodinámica: Bloqueo de Membrana. Concurrencia Abortada."]
  ]

-- El comando #html inyecta el React/DOM directamente en el VS Code Infoview.
#html AlertaColapso 500 100
