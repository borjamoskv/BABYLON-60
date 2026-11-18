#!/usr/bin/env python3
"""
c5_norm_compiler.py - Compilador Mínimo Viable de Normas en Prosa (v1.0.0).
Implementa la Tríada de la Sección 7 de 'El compilador que falta':
1. Fuerza tipada (RFC 2119 / Deóntica formal)
2. Banco de pruebas de conformidad (Oráculo ejecutable)
3. Fugas declaradas (Límites computables delegados al criterio humano)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Dict, Any, Tuple
import re
import os
import sys

class DeonticForce(Enum):
    MUST = "MUST"           # Error bloqueante si falla (Fail-Closed)
    MUST_NOT = "MUST_NOT"   # Error bloqueante si detecta presencia
    SHOULD = "SHOULD"       # Advertencia técnica (Warning)
    MAY = "MAY"             # Registro informativo

class Verdict(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    DELEGATED = "DELEGATED" # Fuga activa: el evaluador abdica al criterio humano

@dataclass
class TestCase:
    name: str
    input_data: Any
    expected_verdict: Verdict
    expected_leakage: bool = False

@dataclass
class CompiledNorm:
    norm_id: str
    prose: str
    force: DeonticForce
    predicate: Callable[[Any], Tuple[Verdict, str]]
    test_cases: List[TestCase]
    declared_leaks: List[str]

    def verify_oracle(self) -> bool:
        """Ejecuta el banco de pruebas de conformidad contra su propio predicado."""
        all_passed = True
        print(f"\n[ORÁCULO] Verificando norma: {self.norm_id} ({self.force.value})")
        print(f"  Prosa: «{self.prose}»")
        for test in self.test_cases:
            verdict, detail = self.predicate(test.input_data)
            status = "✅ PASS" if verdict == test.expected_verdict else "❌ FAIL"
            if verdict != test.expected_verdict:
                all_passed = False
            print(f"  [{status}] Test: {test.name}")
            print(f"         ├─ Esperado: {test.expected_verdict.value} | Obtenido: {verdict.value}")
            if detail:
                print(f"         └─ Diagnóstico: {detail}")
        return all_passed

def make_gerund_predicate():
    pattern = re.compile(r'\b\w+ndo\b[^.!?]*?,\s*\b\w+ndo\b', re.IGNORECASE)
    
    def predicate(text: str) -> Tuple[Verdict, str]:
        match = pattern.search(text)
        if match:
            return (Verdict.FAIL, f"Colisión detectada: '{match.group(0)}'")
        if len(re.findall(r'\b\w+ndo\b', text)) > 2:
            return (Verdict.DELEGATED, "Fuga: Múltiples gerundios sin coma intermedia. Criterio delegado.")
        return (Verdict.PASS, "Estructura rítmica limpia.")
    
    return predicate

norma_estilo = CompiledNorm(
    norm_id="STYLE-001",
    prose="Evita el gerundio encadenado en la misma cláusula sintáctica.",
    force=DeonticForce.SHOULD,
    predicate=make_gerund_predicate(),
    declared_leaks=[
        "Falsa alarma: Gerundio temporal correcto ('Estando el rey en la sala, y cantando el coro...')",
        "Escape no detectado: Encadenamiento con conjunción sin coma ('subiendo y bajando escaleras')"
    ],
    test_cases=[
        TestCase(
            name="Gerundio encadenado estándar",
            input_data="El agente continuó operando, ejecutando los comandos en bucle.",
            expected_verdict=Verdict.FAIL
        ),
        TestCase(
            name="Cláusula limpia",
            input_data="Estando el sistema en reposo, el daemon inició el escaneo.",
            expected_verdict=Verdict.PASS
        ),
        TestCase(
            name="Caso límite (fuga asumida)",
            input_data="Entró corriendo cantando silbando sin parar.",
            expected_verdict=Verdict.DELEGATED,
            expected_leakage=True
        )
    ]
)

def make_lock_predicate():
    def predicate(context: Dict[str, Any]) -> Tuple[Verdict, str]:
        lock_path = context.get("lock_path")
        if not lock_path or not os.path.exists(lock_path):
            return (Verdict.FAIL, "DENIED_LOCK_UNAVAILABLE: Archivo de cerrojo inexistente")
        
        if not os.access(lock_path, os.R_OK):
            return (Verdict.FAIL, "DENIED_LOCK_UNAVAILABLE: Permiso de lectura denegado (EACCES)")
        
        try:
            with open(lock_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    return (Verdict.FAIL, "DENIED_LOCK_INVALID: Lockfile vacío")
        except Exception as e:
            return (Verdict.FAIL, f"DENIED_LOCK_INVALID: Error E/S ({str(e)})")
            
        return (Verdict.PASS, "Lock verificado en silicio")

    return predicate

norma_moskv1 = CompiledNorm(
    norm_id="RING0-LOCK-GATE",
    prose="Si skills-lock.json es inaccesible, no existe o no coincide, bloquear de inmediato con causa LOCAL_LOCKFILE_MISSING.",
    force=DeonticForce.MUST,
    predicate=make_lock_predicate(),
    declared_leaks=[
        "TOCTOU: Modificación del archivo entre lectura e invocación (requiere flock a nivel de kernel)",
        "Symlink hijacking: Si el lockfile apunta a un nodo virtual (/dev/null)"
    ],
    test_cases=[
        TestCase(
            name="Lock inexistente",
            input_data={"lock_path": "/tmp/non_existent_lock_999.json"},
            expected_verdict=Verdict.FAIL
        ),
        TestCase(
            name="Contexto nulo",
            input_data={},
            expected_verdict=Verdict.FAIL
        )
    ]
)

def run_suite() -> int:
    print("=================================================================")
    print("   MOTOR DE COMPILACIÓN DE NORMAS (c5_norm_compiler v1.0.0)")
    print("=================================================================")
    
    suite = [norma_estilo, norma_moskv1]
    all_ok = True
    
    for norm in suite:
        passed = norm.verify_oracle()
        if not passed:
            all_ok = False
        print(f"\n  [FUGAS DECLARADAS - {norm.norm_id}]:")
        for leak in norm.declared_leaks:
            print(f"    ⚠️  {leak}")
            
    print("\n-----------------------------------------------------------------")
    if all_ok:
        print("ESTADO DEL BANCO: ✅ 100% CONFORMIDAD OBSERVADA (E2/Silicio)")
        return 0
    else:
        print("ESTADO DEL BANCO: ❌ REGRESIÓN O DISCREPANCIA DETECTADA")
        return 1

if __name__ == "__main__":
    sys.exit(run_suite())
