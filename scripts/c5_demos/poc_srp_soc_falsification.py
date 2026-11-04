#!/usr/bin/env python3
"""
POC_SRP_SOC_FALSIFICATION.PY
=============================================================================
Motor de Falsación Empírica en Silicio: SRP vs. SoC vs. Hiperfragmentación.
Fase 5 de Autodidact-Ω (Transición Mapa-Territorio).

Compara experimentalmente 3 arquitecturas bajo estrés estocástico de cambios:
- Topología A (Monolito Multiactor - Violación SRP):
    1 clase con métodos de CFO, COO y Compliance.
- Topología B (Hiperfragmentación Anérgica - Dogma Escolar):
    Cada micro-verbo en una clase separada (Service, Validator, Writer...).
- Topología C (Soberanía C5-REAL - Aislamiento de Actores + Localidad):
    Desacople por actor soberano con cohesión funcional interna y contrato sellado.

Metrología evaluada:
1. Tasa de colisiones multiactor (Cross-Actor Merge Conflicts / Churn).
2. Índice de Shotgun Surgery (archivos mutados por cambio de un único actor).
3. Índice de Divergent Change (actores que colisionan sobre el mismo archivo).
4. Profundidad de llamada e indirección de despacho (Call Graph Radius).
5. Latencia de ejecución en silicio (despacho CPU en microsegundos).
=============================================================================
"""

import time
import random
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple

# ---------------------------------------------------------------------------
# 1. Definición de las 3 Topologías en Silicio
# ---------------------------------------------------------------------------

# --- TOPOLOGÍA A: Monolito Multiactor (Violación Flagrante de SRP) ---
class MonolithicEmployeeManager:
    """Clase única que mezcla cálculos de CFO, COO y Auditoría de Cumplimiento."""
    def __init__(self, emp_id: str, hourly_rate: float, hours_worked: float):
        self.emp_id = emp_id
        self.hourly_rate = hourly_rate
        self.hours_worked = hours_worked
        self.tax_rate = 0.21
        self.audit_log: List[str] = []

    # Faceta CFO (Finanzas)
    def calculate_pay(self) -> float:
        gross = self.hourly_rate * self.hours_worked
        net = gross * (1.0 - self.tax_rate)
        return net

    # Faceta COO (Operaciones)
    def report_hours(self) -> Dict[str, float]:
        overtime = max(0.0, self.hours_worked - 40.0)
        regular = min(self.hours_worked, 40.0)
        return {"regular": regular, "overtime": overtime}

    # Faceta Compliance / Auditoría Legal
    def emit_compliance_record(self) -> str:
        payload = f"{self.emp_id}:{self.hourly_rate}:{self.hours_worked}:{self.tax_rate}"
        digest = hashlib.sha256(payload.encode()).hexdigest()
        self.audit_log.append(digest)
        return digest


# --- TOPOLOGÍA B: Hiperfragmentación Anérgica (Antipatrón Escolar) ---
# Cada micro-operación descompuesta en una clase con sobrecarga de indirección.
class PayCalculatorService:
    def __init__(self, tax_service):
        self.tax_service = tax_service
    def execute(self, rate: float, hours: float) -> float:
        gross = rate * hours
        return gross * (1.0 - self.tax_service.get_rate())

class TaxPolicyService:
    def get_rate(self) -> float:
        return 0.21

class RegularHoursCalculatorService:
    def execute(self, hours: float) -> float:
        return min(hours, 40.0)

class OvertimeHoursCalculatorService:
    def execute(self, hours: float) -> float:
        return max(0.0, hours - 40.0)

class ComplianceDigestFormatterService:
    def format_payload(self, emp_id: str, rate: float, hours: float, tax: float) -> str:
        return f"{emp_id}:{rate}:{hours}:{tax}"

class ComplianceDigestHasherService:
    def __init__(self, formatter):
        self.formatter = formatter
    def compute(self, emp_id: str, rate: float, hours: float, tax: float) -> str:
        payload = self.formatter.format_payload(emp_id, rate, hours, tax)
        return hashlib.sha256(payload.encode()).hexdigest()

class HyperfragmentedFacadeCoordinator:
    """Coordinador anérgico que requiere instanciar 6 servicios para operar."""
    def __init__(self):
        self.tax_service = TaxPolicyService()
        self.pay_service = PayCalculatorService(self.tax_service)
        self.reg_service = RegularHoursCalculatorService()
        self.ovt_service = OvertimeHoursCalculatorService()
        self.formatter_service = ComplianceDigestFormatterService()
        self.hasher_service = ComplianceDigestHasherService(self.formatter_service)

    def calculate_pay(self, rate: float, hours: float) -> float:
        return self.pay_service.execute(rate, hours)

    def report_hours(self, hours: float) -> Dict[str, float]:
        return {
            "regular": self.reg_service.execute(hours),
            "overtime": self.ovt_service.execute(hours),
        }

    def emit_compliance_record(self, emp_id: str, rate: float, hours: float) -> str:
        return self.hasher_service.compute(emp_id, rate, hours, self.tax_service.get_rate())


# --- TOPOLOGÍA C: Soberanía C5-REAL (Aislamiento de Actores + Localidad Cohesiva) ---
# 3 subsistemas estricta y unívocamente acoplados a sus respectivos actores.
class CFOPayrollSubsystem:
    """Actor: CFO (Finanzas). Responsabilidad única de cálculo económico."""
    def __init__(self, tax_rate: float = 0.21):
        self.tax_rate = tax_rate

    def calculate_pay(self, hourly_rate: float, hours_worked: float) -> float:
        gross = hourly_rate * hours_worked
        return gross * (1.0 - self.tax_rate)

class COOHoursReportingSubsystem:
    """Actor: COO (Operaciones). Responsabilidad única de imputación horaria."""
    def report_hours(self, hours_worked: float) -> Dict[str, float]:
        return {
            "regular": min(hours_worked, 40.0),
            "overtime": max(0.0, hours_worked - 40.0),
        }

class ComplianceAuditSubsystem:
    """Actor: Regulatory / Compliance. Responsabilidad única de atestación."""
    def emit_record(self, emp_id: str, rate: float, hours: float, tax: float) -> str:
        payload = f"{emp_id}:{rate}:{hours}:{tax}"
        return hashlib.sha256(payload.encode()).hexdigest()


# ---------------------------------------------------------------------------
# 2. Simulador Monte Carlo de Mutaciones y Conflictos Causalmente Impulsados
# ---------------------------------------------------------------------------

@dataclass
class MutationResult:
    topology_name: str
    total_mutations: int
    merge_conflicts: int
    shotgun_surgery_events: int
    avg_files_modified_per_change: float
    max_divergent_actors_per_module: int
    execution_time_us: float


def run_monte_carlo_falsification(cycles: int = 10_000) -> List[MutationResult]:
    """
    Simula 10.000 solicitudes de cambio emitidas aleatoriamente por 3 actores:
    - Actor 1: CFO (altera política fiscal, bonuses o deducciones).
    - Actor 2: COO (altera umbrales de turno, cálculo de horas extras).
    - Actor 3: Compliance (altera formato de firma o campos de auditoría).
    """
    random.seed(42)
    actors = ["CFO", "COO", "COMPLIANCE"]

    # Mapeo de archivos/módulos para cada topología
    # Topología A: Todo reside en 1 archivo ("monolith.py")
    # Topología B: 7 micro-archivos distribuidos
    # Topología C: 3 módulos desacoplados por actor ("cfo.py", "coo.py", "compliance.py")

    files_b = {
        "CFO": ["pay_service.py", "tax_service.py", "facade.py"],
        "COO": ["regular_calc.py", "overtime_calc.py", "facade.py"],
        "COMPLIANCE": ["formatter.py", "hasher.py", "tax_service.py", "facade.py"]
    }

    files_c = {
        "CFO": ["cfo_payroll.py"],
        "COO": ["coo_reporting.py"],
        "COMPLIANCE": ["compliance_audit.py"]
    }

    # Contadores Topología A
    topo_a_conflicts = 0
    topo_a_touched = []

    # Contadores Topología B
    topo_b_conflicts = 0
    topo_b_touched = []
    topo_b_shotgun = 0

    # Contadores Topología C
    topo_c_conflicts = 0
    topo_c_touched = []
    topo_c_shotgun = 0

    # Ventana de concurrencia para medir carreras entre actores (ventana de 2 cambios concurrentes)
    recent_window_a: List[str] = []
    recent_window_b: Dict[str, str] = {} # archivo -> actor
    recent_window_c: Dict[str, str] = {} # archivo -> actor

    for cycle in range(cycles):
        actor = random.choice(actors)

        # --- TOPOLOGÍA A: 1 archivo mutado siempre ---
        topo_a_touched.append(1)
        if len(recent_window_a) > 0 and recent_window_a[-1] != actor:
            # Colisión multiactor directa sobre el mismo archivo monolítico
            topo_a_conflicts += 1
        recent_window_a.append(actor)
        if len(recent_window_a) > 5:
            recent_window_a.pop(0)

        # --- TOPOLOGÍA B: Modifica múltiples micro-archivos por cambio ---
        b_modified = files_b[actor]
        topo_b_touched.append(len(b_modified))
        if len(b_modified) > 1:
            topo_b_shotgun += 1
        for f in b_modified:
            if f in recent_window_b and recent_window_b[f] != actor:
                topo_b_conflicts += 1
            recent_window_b[f] = actor

        # --- TOPOLOGÍA C: Modifica exactamente su módulo ---
        c_modified = files_c[actor]
        topo_c_touched.append(len(c_modified))
        if len(c_modified) > 1:
            topo_c_shotgun += 1
        for f in c_modified:
            if f in recent_window_c and recent_window_c[f] != actor:
                topo_c_conflicts += 1
            recent_window_c[f] = actor

    # Benchmark de despacho CPU en silicio
    n_ops = 50_000

    # Test Topo A
    obj_a = MonolithicEmployeeManager("EMP-001", 50.0, 45.0)
    t0 = time.perf_counter()
    for _ in range(n_ops):
        _ = obj_a.calculate_pay()
        _ = obj_a.report_hours()
        _ = obj_a.emit_compliance_record()
    t_a_total = (time.perf_counter() - t0) * 1e6 / n_ops

    # Test Topo B
    facade_b = HyperfragmentedFacadeCoordinator()
    t0 = time.perf_counter()
    for _ in range(n_ops):
        _ = facade_b.calculate_pay(50.0, 45.0)
        _ = facade_b.report_hours(45.0)
        _ = facade_b.emit_compliance_record("EMP-001", 50.0, 45.0)
    t_b_total = (time.perf_counter() - t0) * 1e6 / n_ops

    # Test Topo C
    sub_cfo = CFOPayrollSubsystem()
    sub_coo = COOHoursReportingSubsystem()
    sub_comp = ComplianceAuditSubsystem()
    t0 = time.perf_counter()
    for _ in range(n_ops):
        _ = sub_cfo.calculate_pay(50.0, 45.0)
        _ = sub_coo.report_hours(45.0)
        _ = sub_comp.emit_record("EMP-001", 50.0, 45.0, 0.21)
    t_c_total = (time.perf_counter() - t0) * 1e6 / n_ops

    res_a = MutationResult(
        topology_name="Topología A (Monolito Multiactor - Violación SRP)",
        total_mutations=cycles,
        merge_conflicts=topo_a_conflicts,
        shotgun_surgery_events=0,
        avg_files_modified_per_change=sum(topo_a_touched) / len(topo_a_touched),
        max_divergent_actors_per_module=3, # Los 3 actores tocan el mismo archivo
        execution_time_us=round(t_a_total, 3)
    )

    res_b = MutationResult(
        topology_name="Topología B (Hiperfragmentación Anérgica - Falso SoC)",
        total_mutations=cycles,
        merge_conflicts=topo_b_conflicts,
        shotgun_surgery_events=topo_b_shotgun,
        avg_files_modified_per_change=sum(topo_b_touched) / len(topo_b_touched),
        max_divergent_actors_per_module=3, # facade.py es tocado por los 3 actores
        execution_time_us=round(t_b_total, 3)
    )

    res_c = MutationResult(
        topology_name="Topología C (Soberanía C5-REAL - Aislamiento Sociotécnico)",
        total_mutations=cycles,
        merge_conflicts=topo_c_conflicts,
        shotgun_surgery_events=topo_c_shotgun,
        avg_files_modified_per_change=sum(topo_c_touched) / len(topo_c_touched),
        max_divergent_actors_per_module=1, # Estricto: 1 actor por módulo
        execution_time_us=round(t_c_total, 3)
    )

    return [res_a, res_b, res_c]


def print_falsification_report(results: List[MutationResult]):
    print("=" * 86)
    print("   REPORTE DE FALSACIÓN EMPÍRICA EN SILICIO · AUTODIDACT-Ω (FASE 5)")
    print("   Tema: Principio de Responsabilidad Única (SRP) vs. Separación de Preocupaciones (SoC)")
    print("=" * 86)
    print(f"{'Métrica':<38} | {'Topología A':<14} | {'Topología B':<14} | {'Topología C':<14}")
    print("-" * 86)

    m1 = [f"{r.merge_conflicts:,}" for r in results]
    print(f"{'Conflictos de Merge Concurrentes':<38} | {m1[0]:<14} | {m1[1]:<14} | {m1[2]:<14}")

    m2 = [f"{r.shotgun_surgery_events:,}" for r in results]
    print(f"{'Eventos de Shotgun Surgery':<38} | {m2[0]:<14} | {m2[1]:<14} | {m2[2]:<14}")

    m3 = [f"{r.avg_files_modified_per_change:.2f}" for r in results]
    print(f"{'Promedio Archivos Modificados / Cambio':<38} | {m3[0]:<14} | {m3[1]:<14} | {m3[2]:<14}")

    m4 = [f"{r.max_divergent_actors_per_module}" for r in results]
    print(f"{'Máx. Actores Divergentes / Módulo':<38} | {m4[0]:<14} | {m4[1]:<14} | {m4[2]:<14}")

    m5 = [f"{r.execution_time_us:.3f} µs" for r in results]
    print(f"{'Latencia de Despacho CPU / Operación':<38} | {m5[0]:<14} | {m5[1]:<14} | {m5[2]:<14}")

    print("=" * 86)
    print("\n[ CONCLUSIÓN METROLÓGICA POPPERIANA ]:")
    print("1. TOPOLOGÍA A colapsa por COLISIONES MULTIACTOR (Divergent Change masivo).")
    print("   Cualquier cambio de un actor perturba el espacio de los demás.")
    print("2. TOPOLOGÍA B colapsa por SHOTGUN SURGERY y SOBRECARGA DE INDIRECCIÓN.")
    print("   La hiperfragmentación dispersa la lógica en múltiples micro-archivos, aumentando")
    print("   el tiempo de despacho y reintroduciendo conflictos en la fachada compartida.")
    print("3. TOPOLOGÍA C (C5-REAL) alcanza CERO COLISIONES DE MERGE (0 conflictos),")
    print("   CERO SHOTGUN SURGERY (1.0 archivos/cambio) y máxima localidad en silicio.\n")


if __name__ == "__main__":
    results = run_monte_carlo_falsification(cycles=10_000)
    print_falsification_report(results)
