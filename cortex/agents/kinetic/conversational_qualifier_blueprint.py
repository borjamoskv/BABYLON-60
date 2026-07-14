#!/usr/bin/env python3
# C5-REAL
# SYS_ID: borjamoskv
"""CONVERSATIONAL LEAD QUALIFIER & DIAGNOSTIC BLUEPRINT (Isomorphic to Marta / Descubre tu primer empleado IA).

Kinetic Vector synthesized during AUTODIDACT-OMEGA / ULTRATHINK P0.
Replaces static 20-field lead capture forms with an active, time-bounded (<= 10 min)
diagnostic interview that compiles a custom automation sheet and 7-day actionable plan.
"""

import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

class ConversationalLeadQualifier:
    def __init__(self, agent_name: str = "Marta-C5-REAL", max_duration_minutes: int = 10):
        self.agent_name = agent_name
        self.max_duration_minutes = max_duration_minutes
        self.start_time = datetime.datetime.now(datetime.timezone.utc)
        self.interview_state: dict[str, Any] = {}

    def _assert_invariants(self):
        elapsed_min = (datetime.datetime.now(datetime.timezone.utc) - self.start_time).total_seconds() / 60.0
        assert elapsed_min <= self.max_duration_minutes, f"Invariante rota: La entrevista excede los {self.max_duration_minutes} min máximos definidos."
        assert "bottleneck_task" in self.interview_state, "Invariante rota: Cuello de botella principal no identificado."
        assert "weekly_hours_wasted" in self.interview_state, "Invariante rota: Horas semanales disipadas no cuantificadas."

    def run_automated_diagnostic(self, simulated_input: dict[str, Any]) -> dict[str, Any]:
        """Runs the diagnostic interview loop (or simulated profile ingestion)."""
        print(f"[*] [{self.agent_name}] Iniciando entrevista diagnóstica C5-REAL (Máx. {self.max_duration_minutes} min)...")
        
        # Step 1: Ingest business profile & friction points
        self.interview_state["business_type"] = simulated_input.get("business_type", "Empresa B2B / Servicios")
        self.interview_state["bottleneck_task"] = simulated_input.get("bottleneck_task", "Cualificación manual de leads entrantes y agendamiento")
        self.interview_state["weekly_hours_wasted"] = float(simulated_input.get("weekly_hours_wasted", 15.0))
        self.interview_state["current_stack"] = simulated_input.get("current_stack", ["HubSpot / Excel", "Gmail", "WhatsApp"])
        self.interview_state["target_outcome"] = simulated_input.get("target_outcome", "Agendar citas cualificadas de forma 100% autónoma en calendario 24/7")

        # Verify physical constraints
        self._assert_invariants()

        # Step 2: Compute ROI & Exergy Metrics
        hourly_rate_proxy = 45.0 # EUR/hour average cost of skilled human attention
        monthly_anergy_cost = self.interview_state["weekly_hours_wasted"] * 4.33 * hourly_rate_proxy
        
        # Step 3: Synthesize 7-Day Actionable Plan & Custom Automation Sheet
        sheet: dict[str, Any] = {
            "metadata": {
                "agent_diagnosing": self.agent_name,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "ppi_qualification_score": "HIGH (5/5)" if self.interview_state["weekly_hours_wasted"] >= 10 else "MODERATE (3/5)"
            },
            "automation_sheet": {
                "primer_empleado_ia_recomendado": f"Agente Orquestador Conversacional ('{self.interview_state['bottleneck_task'][:30]}...')",
                "rol_exacto": "Transductor y cualificador autónomo en primera línea (Voz / Chat / Webhook)",
                "impacto_termodinamico_estimado": {
                    "horas_semanales_recuperadas": round(self.interview_state["weekly_hours_wasted"] * 0.9, 1),
                    "anergia_financiera_purgada_mes": f"{round(monthly_anergy_cost * 0.9, 2)} EUR",
                    "friccion_de_entrada_cliente": "0 (Cero formularios estáticos)"
                },
                "stack_propuesto": [
                    "Frontend / Canal: Webhook o Voice/Chat Widget (Next.js 14 / WebSockets)",
                    "Motor Cognitivo: Gemini 3.1 Pro / Flash (Inferencia determinista con function calling)",
                    "Persistencia / CRM: Integración directa al stack actual (" + ", ".join(self.interview_state["current_stack"]) + ")"
                ]
            },
            "plan_accionable_7_dias": [
                "Día 1: Mapear el árbol de decisión causal del cuello de botella actual ('" + self.interview_state["bottleneck_task"] + "').",
                "Día 2-3: Forjar el System Prompt paramétrico con invariantes y candados BFT (cero alucinación en agendamiento).",
                "Día 4-5: Conectar tool_calls para mutación asíncrona de calendario/CRM (O(1) latencia).",
                "Día 6: Pruebas de estrés adversariales locales con bucles de casos límite.",
                "Día 7: Despliegue a producción y sustitución absoluta del formulario de contacto manual."
            ]
        }
        
        # Generate CORTEX proof
        raw_bytes = json.dumps(sheet, sort_keys=True).encode("utf-8")
        sha3_hash = hashlib.sha3_256(raw_bytes).hexdigest()
        sheet["cortex_taint"] = f"[CORTEX-TAINT:borjamoskv:conversational_qualifier:{sheet['metadata']['timestamp']}:{sha3_hash}]"
        
        return sheet

def main():
    parser = argparse.ArgumentParser(description="Conversational Lead Qualifier Blueprint (C5-REAL)")
    parser.add_argument("--business-type", default="Agencia B2B / Consultoría Tecnológica")
    parser.add_argument("--bottleneck", default="Cualificación inicial de leads y resolución repetitiva de dudas antes de agendar llamada")
    parser.add_argument("--hours-wasted", type=float, default=18.5)
    parser.add_argument("--output", default="ficha_automatizacion_a_medida.md")
    args = parser.parse_args()

    qualifier = ConversationalLeadQualifier(agent_name="Marta-C5-REAL")
    diagnostic_result = qualifier.run_automated_diagnostic({
        "business_type": args.business_type,
        "bottleneck_task": args.bottleneck,
        "weekly_hours_wasted": args.hours_wasted
    })

    # Output formatting as Markdown sheet
    md_lines = [
        f"# FICHA DE AUTOMATIZACIÓN A MEDIDA : {diagnostic_result['automation_sheet']['primer_empleado_ia_recomendado']}",
        f"`SYS_ID borjamoskv` · Sello: {diagnostic_result['cortex_taint']}",
        "",
        "## 01. DIAGNÓSTICO & EXERGÍA DEL NEGOCIO",
        f"- **Tipo de Negocio:** {args.business_type}",
        f"- **Cuello de Botella (Anergía):** {args.bottleneck}",
        f"- **Disipación de Atención:** {args.hours_wasted} horas/semana disipadas en tareas mecánicas.",
        f"- **Puntuación de Cualificación:** **{diagnostic_result['metadata']['ppi_qualification_score']}**",
        "",
        "## 02. TU PRIMER EMPLEADO IA (CONFIGURACIÓN RECOMENDADA)",
        f"- **Rol Asignado:** {diagnostic_result['automation_sheet']['rol_exacto']}",
        f"- **Horas Semanales Recuperadas:** **{diagnostic_result['automation_sheet']['impacto_termodinamico_estimado']['horas_semanales_recuperadas']} h/semana**",
        f"- **Ahorro Termodinámico Estimado:** **{diagnostic_result['automation_sheet']['impacto_termodinamico_estimado']['anergia_financiera_purgada_mes']}**",
        "- **Stack Arquitectónico:**",
    ]
    for st in diagnostic_result['automation_sheet']['stack_propuesto']:
        md_lines.append(f"  - `{st}`")
    
    md_lines.extend([
        "",
        "## 03. PLAN ACCIONABLE DE LOS PRÓXIMOS 7 DÍAS (SÍNTESIS C5-REAL)",
    ])
    for day_step in diagnostic_result['plan_accionable_7_dias']:
        md_lines.append(f"- {day_step}")
        
    md_content = "\n".join(md_lines) + "\n"
    
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md_content, encoding="utf-8")
    
    print(f"[+] Ficha generada y persistida en: {out_path}")
    print(f"[+] Firma: {diagnostic_result['cortex_taint']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
