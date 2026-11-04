import pathlib
import pytest
from babylon60.genomics.vsa_oncology import OncologyOntologyVSA, BFOCategory, HyperVector

_CATALOG = pathlib.Path(__file__).resolve().parent.parent / "data" / "oncology_300.json"
_SKIP_MSG = "oncology_300.json catalog not provisioned in this environment"


def _skip_if_no_catalog() -> None:
    if not _CATALOG.exists():
        pytest.skip(_SKIP_MSG)


def test_vsa_primitives_loaded() -> None:
    _skip_if_no_catalog()
    engine = OncologyOntologyVSA()
    assert len(engine.primitives) == 300
    assert "ONC-001" in engine.primitives
    assert "ONC-300" in engine.primitives


def test_vsa_bfo_classification() -> None:
    _skip_if_no_catalog()
    engine = OncologyOntologyVSA()
    assert engine.classify_bfo("ONC-017") == BFOCategory.CONTINUANT  # KRAS
    assert engine.classify_bfo("ONC-047") == BFOCategory.CONTINUANT  # TP53
    assert engine.classify_bfo("ONC-072") == BFOCategory.OCCURRENT  # MAPK
    assert engine.classify_bfo("ONC-145") == BFOCategory.INFORMATIONAL  # TMB


def test_hypervector_binding_orthogonality() -> None:
    v1 = HyperVector.from_seed("SEED_A")
    v2 = HyperVector.from_seed("SEED_B")
    bound = v1.bind(v2)

    # Dos vectores hiperdimensionales aleatorios son cuasi-ortogonales (similitud cercana a 0)
    assert abs(v1.similarity(v2)) < 0.05
    # El vector producto ligado es también cuasi-ortogonal a sus factores
    assert abs(bound.similarity(v1)) < 0.05
    assert abs(bound.similarity(v2)) < 0.05
    # La auto-similitud es 1.0
    assert v1.similarity(v1) == 1.0


def test_waddington_trajectory_bifurcation() -> None:
    _skip_if_no_catalog()
    engine = OncologyOntologyVSA()
    traj_active = engine.simulate_waddington_trajectory("ONC-017", inhibited=False, steps=60)
    traj_inhibited = engine.simulate_waddington_trajectory("ONC-017", inhibited=True, steps=60)

    # Estado no inhibido converge al atractor maligno
    assert traj_active[-1][0] > 0.8
    # Estado inhibido farmacológicamente converge a la cuenca homeostática
    assert traj_inhibited[-1][0] < -0.8
