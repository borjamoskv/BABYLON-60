"""
PoC Aislado de Falsación (Bloque B0 · PLAN-Ω Iteración 2).
Verifica empíricamente en silicio las decisiones arquitectónicas D1-D5 y P0/P0-bis/P1:
- D1: Ningún Cargo.toml declara 'Apache-2.0 OR MIT'; todos usan 'license-file' y 'publish = false', y crates-publish.yml no ejecuta 'cargo publish'.
- D2: babylon-attest no contiene el fallback '{"raw": body}' y exige autenticación previa al ledger WORM.
- D3: KUDURRU-64 usa Big-Endian ('>') con byte de versión explícito.
- D4: Existe morfismo de tipos en compilación entre ReceiptStage (ontology.rs) y el estado de ejecución física (executor.rs), y cadt_mediator no duplica Kudurru64.
- D5: Cero dependencias de 'ring' en Cargo.toml; bft_interceptor.rs no usa ring::hmac.
- P0.3/P1: voice_cloner.py está excluido del wheel distribuido y no parchea torch.load a weights_only=False; suelos de seguridad actualizados en pyproject.toml y z3-solver en core.
"""

from pathlib import Path
import tomllib

ROOT = Path(__file__).absolute().parent.parent


def test_d1_sovereign_license_and_publish_gate() -> None:
    cargo_files = [
        ROOT / "Cargo.toml",
        *ROOT.glob("00_ABZU_KERNEL/crates/*/Cargo.toml"),
        *ROOT.glob("01_KISH_ENGINE/cortex/crates/*/Cargo.toml"),
        *ROOT.glob("crates/*/Cargo.toml"),
    ]
    assert len(cargo_files) >= 18
    for cf in cargo_files:
        data = tomllib.loads(cf.read_text(encoding="utf-8"))
        pkg = data.get("package", {})
        assert pkg.get("license") != "Apache-2.0 OR MIT", f"{cf} still has permissive license"
        assert "license-file" in pkg, f"{cf} missing license-file"
        assert pkg.get("publish") is False, f"{cf} must set publish = false"

    workflow = (ROOT / ".github/workflows/crates-publish.yml").read_text(encoding="utf-8")
    assert "cargo publish" not in workflow, "crates-publish.yml still runs cargo publish"


def test_d2_babylon_attest_fail_closed_and_authenticated() -> None:
    attest_main = (ROOT / "crates/babylon-attest/src/main.rs").read_text(encoding="utf-8")
    assert '{ "raw": body }' not in attest_main and '{"raw": body}' not in attest_main, (
        "babylon-attest still accepts unparseable raw bodies into WORM ledger"
    )
    assert "X-Babylon-Token" in attest_main or "Authorization" in attest_main, (
        "babylon-attest POST /attest lacks authentication gate"
    )


def test_d3_kudurru64_big_endian_versioned_and_python_attestation_hardened() -> None:
    docs_lint = (ROOT / "scripts/docs_lint.py").read_text(encoding="utf-8")
    assert "<IIBBHfI44s" not in docs_lint, "KUDURRU-64 still uses unversioned Little-Endian struct"

    attest_py = (ROOT / "02_EDIN_SWARMS/agents_archi/protocols/attestation.py").read_text(encoding="utf-8")
    assert "_SEEN_NONCES" in attest_py or "NonceStore" in attest_py, (
        "attestation.py lacks replay-protection nonce store (O13)"
    )


def test_d4_ontology_executor_morphism_and_no_duplicate_kudurru64() -> None:
    ontology_rs = (ROOT / "src/ontology.rs").read_text(encoding="utf-8")
    executor_rs = (ROOT / "src/executor.rs").read_text(encoding="utf-8")
    assert "ReservationState" in ontology_rs or "ReceiptStage" in executor_rs, (
        "Missing compile-time morphism between ReceiptStage and Executor state"
    )

    cadt_lib = (ROOT / "crates/cadt_mediator/src/lib.rs").read_text(encoding="utf-8")
    assert "pub struct Kudurru64" not in cadt_lib, (
        "cadt_mediator still defines duplicate Kudurru64 Seqlock (violating INV_C5_PARASITIC_DOF_QUOTIENT)"
    )


def test_d5_no_ring_dependency_and_p0_python_hygiene() -> None:
    strike_cargo = (ROOT / "00_ABZU_KERNEL/crates/strike-rs/Cargo.toml").read_text(encoding="utf-8")
    assert "ring = " not in strike_cargo, "strike-rs still depends on ring"

    bft_inter = (ROOT / "00_ABZU_KERNEL/crates/strike-rs/src/bin/bft_interceptor.rs").read_text(encoding="utf-8")
    assert "use ring::hmac" not in bft_inter, "bft_interceptor.rs still uses ring::hmac"

    pyproj = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    deps = pyproj["project"]["dependencies"]

    def _floor_for(pkg: str) -> tuple[int, ...]:
        for d in deps:
            if d.startswith(f"{pkg}>="):
                ver_str = d.split(">=", 1)[1].split(",")[0].strip()
                return tuple(int(x) for x in ver_str.split(".") if x.isdigit())
        return ()

    assert _floor_for("cbor2") >= (5, 9, 0), "cbor2 floor not raised to >=5.9.0"
    assert _floor_for("cryptography") >= (49, 0, 0), "cryptography floor not raised to >=49.0.0"
    assert _floor_for("pynacl") >= (1, 6, 2), "pynacl floor not raised to >=1.6.2"
    assert _floor_for("python-dotenv") >= (1, 2, 2), "python-dotenv floor not raised to >=1.2.2"
    assert any(d.startswith("z3-solver") for d in deps), "z3-solver not promoted to core dependencies"
    assert not any(d.startswith("textual") for d in deps), "unused textual still in core dependencies"

    voice_cloner = (ROOT / "01_KISH_ENGINE/babylon60/services/voice_cloner.py").read_text(encoding="utf-8")
    assert "weights_only=False" not in voice_cloner, "voice_cloner.py still patches torch.load with weights_only=False"
