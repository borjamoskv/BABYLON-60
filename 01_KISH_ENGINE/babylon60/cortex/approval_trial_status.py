"""Read-only Spanish status for the supervised FL-APPROVAL-01 pilot.

Counts describe imported declarations, never authenticated people, signatures,
confirmed efficacy or authority to activate CORTEX.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, TypeVar

from babylon60.cortex.approval_human_trial import analyze_pilot, validate_readiness

JsonContainer = TypeVar("JsonContainer", dict[str, Any], list[Any])


def _read(path: Path, expected: type[JsonContainer]) -> JsonContainer:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise ValueError(f"No se pudo leer {path.name}: {exc}") from exc
    if not isinstance(value, expected):
        raise ValueError(f"{path.name} no contiene el tipo de datos esperado")
    return value


def trial_status(
    kit: Path,
    *,
    adjudications: Path | None = None,
    enrollment: Path | None = None,
    observations: Path | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    """Check the actual private inputs; do not trust a saved readiness report."""
    private = kit / "coordinator"
    pilot = _read(private / "pilot_private.json", dict)
    adjudication_data = _read(adjudications or private / "adjudication_template.json", dict)
    enrollment_data = _read(enrollment or private / "enrollment_template.json", list)
    observation_data = _read(observations or private / "observations_template.json", list)
    if source not in (None, "human", "simulation"):
        raise ValueError("El origen debe ser human o simulation")
    if observation_data and source is None:
        raise ValueError("Hay respuestas: indica --source human o --source simulation")
    try:
        readiness = validate_readiness(pilot, adjudication_data, enrollment_data)
        # No observations need an origin declaration. The internal empty
        # analysis uses simulation so it never assumes human provenance.
        analysis = analyze_pilot(pilot, observation_data, source=source or "simulation")
    except (KeyError, TypeError, AttributeError, IndexError) as exc:
        raise ValueError("La estructura del paquete está incompleta o es inválida") from exc
    pending_cases = len(readiness["unresolved_case_ids"])
    pending_slots = len(readiness["pending_reviewer_ids"])
    declared_complete = readiness["ready_for_pilot"]
    count = analysis["observed_decisions"]
    if source == "simulation":
        status = "SIMULACION_SOLO_PRUEBA"
        next_step = (
            "Usar esta salida para comprobar el software. Conservar las respuestas humanas "
            "reales en un archivo separado de la simulación."
        )
    elif not declared_complete:
        status = "RESPUESTAS_CON_PREPARACION_PENDIENTE" if count else "PREPARACION_PENDIENTE"
        next_step = (
            f"Dos especialistas deben revisar por separado los {pending_cases} casos pendientes."
            if pending_cases
            else f"Completar consentimiento, formación e inscripción de los {pending_slots} puestos pendientes."
        )
    elif not count:
        status = "REQUISITOS_DECLARADOS_COMPLETOS"
        next_step = "Cotejar los documentos originales y preparar la primera sesión supervisada."
    elif not analysis["complete"]:
        status = "PILOTO_EN_CURSO_SEGUN_DECLARACIONES"
        next_step = "Completar las sesiones previstas y conservar sus registros originales para auditoría."
    else:
        status = "PILOTO_COMPLETO_SEGUN_DECLARACIONES"
        next_step = (
            "Revisar calidad, incidencias y viabilidad con las personas responsables. "
            "El piloto no demuestra la reducción del 30 %."
        )
    return {
        "status": status,
        "pending_cases": pending_cases,
        "reviewer_slots_pending": pending_slots,
        "human_observations_declared": count if source == "human" else 0,
        "simulation_observations": count if source == "simulation" else 0,
        "planned_decisions": analysis["planned_decisions"],
        "protocol_deviations": sum(row["protocol_deviations"] for row in analysis["reviewers"]),
        "source": source,
        "declared_ready_for_pilot": declared_complete and source != "simulation",
        "human_identity_verified": False,
        "provenance": "IMPORTED_DECLARATIONS_NOT_IDENTITY_OR_SIGNATURE_VERIFIED",
        "hypothesis_confirmed": False,
        "activation_allowed": False,
        "next_step": next_step,
    }


def status_text(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "Ensayo humano FL-APPROVAL-01",
            "Estado: " + result["status"].replace("_", " ").lower(),
            f"Casos pendientes de revisión: {result['pending_cases']}",
            f"Puestos de revisor pendientes: {result['reviewer_slots_pending']}",
            f"Respuestas humanas declaradas: {result['human_observations_declared']}",
            f"Respuestas de simulación: {result['simulation_observations']}",
            f"Incidencias de protocolo: {result['protocol_deviations']}",
            "Próximo paso: " + result["next_step"],
            "Reducción del 30 %: no confirmada.",
            "Activación en CORTEX: no permitida.",
            "El estado se basa en declaraciones importadas; no autentica identidades ni firmas.",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kit", type=Path, required=True, help="Carpeta que contiene coordinator")
    parser.add_argument("--adjudications", type=Path)
    parser.add_argument("--enrollment", type=Path)
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--source", choices=("human", "simulation"))
    parser.add_argument("--json", action="store_true", help="Mostrar un informe JSON")
    args = parser.parse_args(argv)
    try:
        result = trial_status(
            args.kit,
            adjudications=args.adjudications,
            enrollment=args.enrollment,
            observations=args.observations,
            source=args.source,
        )
    except ValueError as exc:
        print(f"Error de datos: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else status_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
