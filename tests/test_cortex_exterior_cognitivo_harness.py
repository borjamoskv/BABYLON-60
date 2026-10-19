# ============================================================================
# BABYLON-60 v5.0.0 (AX-0) — CORTEX EXTERIOR COGNITIVO & ANTI-SOLIPSISM HARNESS
# █ C5-REAL Ring-0 Epistemic Falsification Suite
# ============================================================================
"""
Arnés de Falsación del Exterior Cognitivo vs. El Espejo (Aforismos 108 y 109).

Invariantes Validadas:
  - INV_CORTEX_01 (La Condición de Exterioridad): El ledger solo asimila
    eventos con anclaje causal explícito (cortex_taint obligatorio). Sin
    exterior que provea entropía (taint), el sistema aborta en fail-closed.
  - INV_CORTEX_02 (Invarianza de Chentsov en Serialización): La proyección
    del territorio sobre el mapa debe ser canónica, determinista e invariante
    ante permutaciones de clave en diccionarios o caracteres UTF-8 de 4 bytes.
  - INV_CORTEX_03 (Falsación Popperiana ante Corrupción Física): Si el sustrato
    físico se degrada (bitflips, torn-writes), el ledger rechaza la
    confabulación y declara la rotura de integridad de inmediato (verify_integrity -> False).
  - INV_CORTEX_04 (Discriminación Alteridad vs. Eco Especular): El sistema
    distingue inequívocamente entre un eco voluntario idéntico (DUPLICATE_IGNORED)
    y una diferencia estocástica real del entorno (C5_PERMANENT).
"""

import hashlib
import sqlite3
from pathlib import Path
import pytest

from babylon60.bft.cortex_crypto_kernel import (
    _canonical_json,
)
from babylon60.bft.cortex_persist_ledger import (
    CortexPersistLedger,
    CortexEvent,
)


def _ev(tag: str, payload_data: dict[str, object], taint: str = "") -> CortexEvent:
    return CortexEvent(
        event_type="STATE_MUTATION",
        payload=payload_data,
        cortex_taint=taint or f"session:ext_{tag}",
    )


# ============================================================================
# 1. VECTOR DE EXTERIORIDAD: VETO AL SOLIPSISMO SIN ANCLAJE CAUSAL
# ============================================================================


def test_exterior_cognitivo_veto_solipsistic_empty_taint(tmp_path: Path) -> None:
    """
    Un evento sin taint causal exterior carece de mundo: es una alucinación
    cerrada del modelo. El ledger debe abortar inmediatamente en modo fail-closed.
    """
    ledger = CortexPersistLedger(tmp_path / "solipsism_veto.db")
    orphan_event = CortexEvent(
        event_type="INFERENCE_CLAIM",
        payload={"claim": "hallucinated_truth", "value": 42},
        cortex_taint="",  # Sin exterior causal
    )

    with pytest.raises(ValueError, match="INV_BFT_03: cortex_taint es obligatorio"):
        ledger.append_event(orphan_event)

    # La base de datos debe permanecer virgen (0 registros)
    conn = sqlite3.connect(tmp_path / "solipsism_veto.db")
    count = conn.execute("SELECT COUNT(*) FROM cortex_ledger").fetchone()[0]
    conn.close()
    assert count == 0, "No debe persistirse ningún evento sin exterior causal"


# ============================================================================
# 2. VECTOR DE DIFERENCIA IRREDUCTIBLE: CHENTSOV & UTF-8 NON-BMP FUZZING
# ============================================================================


def test_exterior_cognitivo_bateson_difference_fuzzing(tmp_path: Path) -> None:
    """
    Inyección de diferencias no contenidas en schemas convencionales:
    - Glifos matemáticos y emojis de 4 bytes (fuera del BMP).
    - Claves profundamente anidadas con permutaciones de orden.
    - Tipos numéricos en límites de representación.
    Demuestra que el operador de compresión no confabula ni diverge.
    """
    ledger = CortexPersistLedger(tmp_path / "difference_fuzzing.db")

    # Dos diccionarios con orden inverso de claves pero idéntica semántica
    payload_a = {
        "omega_attractor": "Ω_limit",
        "gradient": "∇V(x)",
        "entropy_dissipation": 1.442695,
        "deep_nest": {"kudurru": 64, "mushushu": "0xDEAD_6060", "symbols": "⚡️🔥🌊"},
    }
    payload_b = {
        "deep_nest": {"symbols": "⚡️🔥🌊", "mushushu": "0xDEAD_6060", "kudurru": 64},
        "entropy_dissipation": 1.442695,
        "gradient": "∇V(x)",
        "omega_attractor": "Ω_limit",
    }

    # El canonical JSON debe colapsar ambas estructuras a exactamente los mismos bytes
    canon_a = _canonical_json(payload_a)
    canon_b = _canonical_json(payload_b)
    assert canon_a == canon_b, "Invariante de Chentsov rota: el orden de claves afectó la métrica"

    # Insertar el primer evento
    res_a = ledger.append_event(
        CortexEvent(
            event_type="TOPOLOGICAL_MUTATION",
            payload=payload_a,
            cortex_taint="darwin:arm64:ring0",
        )
    )
    assert res_a["status"] == "C5_PERMANENT"

    # El segundo evento (con orden inverso) debe ser reconocido como idempotente (DUPLICATE_IGNORED)
    res_b = ledger.append_event(
        CortexEvent(
            event_type="TOPOLOGICAL_MUTATION",
            payload=payload_b,
            cortex_taint="darwin:arm64:ring0",
        )
    )
    assert res_b["status"] == "DUPLICATE_IGNORED"
    assert res_b["entry_hash"] == res_a["entry_hash"]
    assert ledger.verify_integrity() is True


# ============================================================================
# 3. VECTOR DE TERRITORIO FÍSICO: DETECCIÓN DE BITFLIPS Y TORN-WRITES
# ============================================================================


def test_exterior_cognitivo_physical_tamper_fails_fast(tmp_path: Path) -> None:
    """
    Si el mundo físico altera o corrompe un inodo en disco (bitflip en el
    ledger o ataque deliberado), el sistema NO confabula: la verificación
    de integridad debe colapsar a False de inmediato.
    """
    db_file = tmp_path / "tamper_test.db"
    ledger = CortexPersistLedger(db_file)

    # Insertar 5 eventos consecutivos
    for i in range(1, 6):
        ledger.append_event(_ev(f"node_{i}", {"step": i, "power": 2**i}))

    assert ledger.verify_integrity() is True

    # Mutar directamente un byte en el payload de la fila 3 evadiendo triggers
    conn = sqlite3.connect(db_file)
    # Desactivar temporalmente los triggers para simular corrupción de almacenamiento crudo
    conn.execute("DROP TRIGGER trg_cortex_no_update")
    conn.execute("UPDATE cortex_ledger SET payload_json = '{\"corrupted\": true}' WHERE seq = 3")
    conn.commit()
    conn.close()

    # El ledger debe detectar la discrepancia entre el entry_hash y los bytes reales
    assert ledger.verify_integrity() is False, "El ledger confabuló: no detectó la alteración física del registro"


def test_exterior_cognitivo_hash_chain_discontinuity_detection(tmp_path: Path) -> None:
    """
    Si un atacante o un fallo de hardware altera prev_hash para falsear el historial,
    el encadenamiento criptográfico SHA3-256 debe romper la verificación de raíz.
    """
    db_file = tmp_path / "chain_tamper.db"
    ledger = CortexPersistLedger(db_file)

    for i in range(1, 4):
        ledger.append_event(_ev(f"chain_{i}", {"val": i}))

    assert ledger.verify_integrity() is True

    conn = sqlite3.connect(db_file)
    conn.execute("DROP TRIGGER trg_cortex_no_update")
    fake_hash = hashlib.sha3_256(b"fake_predecessor").hexdigest()
    conn.execute("UPDATE cortex_ledger SET prev_hash = ? WHERE seq = 3", (fake_hash,))
    conn.commit()
    conn.close()

    assert ledger.verify_integrity() is False, "El arnés permitió una discontinuidad de prev_hash no detectada"


# ============================================================================
# 4. VECTOR DE DISCRIMINACIÓN: ALTERIDAD (MUNDO) VS. ECO (ESPEJO)
# ============================================================================


def test_exterior_cognitivo_alterity_vs_echo_batch(tmp_path: Path) -> None:
    """
    Somete a prueba un lote mixto con:
      - 3 eventos con diferencias estocásticas genuinas (Mundo).
      - 3 eventos que son ecos idénticos de eventos ya procesados (Espejo).
    Verifica que la cadena sólo avanza con la alteridad y no con el eco.
    """
    db_file = tmp_path / "alterity_batch.db"
    ledger = CortexPersistLedger(db_file)

    ev_world_1 = _ev("world_1", {"source": "optical_sensor", "lux": 450})
    ev_world_2 = _ev("world_2", {"source": "seismic_sensor", "mms": 0.04})
    ev_world_3 = _ev("world_3", {"source": "darwin_kernel", "kext_load": False})

    # Lote 1: Se insertan los 3 del Mundo
    res1 = ledger.append_batch([ev_world_1, ev_world_2, ev_world_3])
    assert all(r["status"] == "C5_PERMANENT" for r in res1)
    assert [r["seq"] for r in res1] == [1, 2, 3]

    # Lote 2: Se mezclan los ecos con un nuevo evento del Mundo (world_4)
    ev_world_4 = _ev("world_4", {"source": "touch_id", "authorized": True})
    mixed_batch = [
        ev_world_1,  # Eco
        ev_world_4,  # Nueva alteridad
        ev_world_2,  # Eco
        ev_world_3,  # Eco
    ]
    res2 = ledger.append_batch(mixed_batch)

    assert res2[0]["status"] == "DUPLICATE_IGNORED"
    assert res2[1]["status"] == "C5_PERMANENT"
    assert res2[1]["seq"] == 4
    assert res2[2]["status"] == "DUPLICATE_IGNORED"
    assert res2[3]["status"] == "DUPLICATE_IGNORED"

    # Verificar que el encadenamiento de seq=4 apunta a seq=3 y no a los ecos
    conn = sqlite3.connect(db_file)
    row_4 = conn.execute("SELECT prev_hash, entry_hash FROM cortex_ledger WHERE seq = 4").fetchone()
    row_3 = conn.execute("SELECT entry_hash FROM cortex_ledger WHERE seq = 3").fetchone()
    conn.close()

    assert row_4[0] == row_3[0], "seq=4 debe encadenarse con seq=3, ignorando los ecos de espejo intermedios"
    assert ledger.verify_integrity() is True
