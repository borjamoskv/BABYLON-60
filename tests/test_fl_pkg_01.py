"""Evidence-boundary tests; real installation results come from the separate lab."""

from dataclasses import replace
import io
import tarfile
import urllib.error
import urllib.request

import pytest

from scripts.c5_quality_gates.fl_pkg_01 import TOKEN, Observation, Registry, make_corpus, summarize


def observation(policy: str = "C") -> Observation:
    return Observation(
        "trial",
        policy,
        "fixture",
        "adversarial",
        0,
        False,
        0,
        10.0,
        True,
        False,
        False,
        False,
        False,
        False,
        "",
    )


def test_corpus_balanced_deterministic_with_real_lifecycle_scripts() -> None:
    first, second = make_corpus(300), make_corpus(300)
    assert len({p.name for p in first}) == 300
    for kind in ("benign", "suspicious", "adversarial"):
        assert sum(p.kind == kind for p in first) == 100
    assert [p.archive for p in first] == [p.archive for p in second]
    assert {p.variant for p in first if p.kind == "adversarial"} == set(range(5))
    with tarfile.open(fileobj=io.BytesIO(first[0].archive)) as archive:
        manifest = archive.extractfile("package/package.json")
        assert manifest is not None and b'"postinstall": "node install.cjs"' in manifest.read()


@pytest.mark.parametrize("count", [0, -3, 1, 301])
def test_invalid_corpus_count_rejected(count: int) -> None:
    with pytest.raises(ValueError):
        make_corpus(count)


@pytest.mark.parametrize(
    "effect", ["protected_mutation", "unlisted_mutation", "secret_canary_exposure", "network_egress"]
)
def test_any_physical_effect_falsifies_even_if_installer_denies(effect: str) -> None:
    row = replace(
        observation(),
        protected_mutation=effect == "protected_mutation",
        unlisted_mutation=effect == "unlisted_mutation",
        secret_canary_exposure=effect == "secret_canary_exposure",
        network_egress=effect == "network_egress",
        returncode=1,
        stderr_tail="DENY",
    )
    assert summarize([row])["verdict"] == "FALSIFIED"


def test_zero_observed_effects_does_not_certify_mediation() -> None:
    result = summarize([observation()])
    assert result["verdict"] == "INCONCLUSIVE"
    assert result["unmediated_install_effects_C"] is None
    assert result["complete_mediation_verified"] is False
    assert result["positive_controls_valid"] is False


def test_failed_controls_cannot_be_validated_by_exit_code_alone() -> None:
    assert summarize([observation("A")])["positive_controls_valid"] is False
    positive = replace(
        observation("A"),
        protected_mutation=True,
        unlisted_mutation=True,
        network_egress=True,
        secret_canary_exposure=True,
    )
    assert summarize([positive])["positive_controls_valid"] is True
    assert summarize([replace(positive, timed_out=True, legitimate_success=False)])["positive_controls_valid"] is False


def test_warmup_effects_do_not_count_as_measured_outcomes() -> None:
    result = summarize([replace(observation(), warmup=True, network_egress=True), observation()])
    assert result["verdict"] == "INCONCLUSIVE"


def test_registry_auth_and_admission_cover_metadata_and_archives() -> None:
    packages = make_corpus(3)
    registry = Registry(packages)
    registry.thread.start()
    try:
        for policy, index, status in (("A", 1, 200), ("B", 1, 403), ("C_CURRENT", 1, 403), ("C_CURRENT", 2, 200)):
            for suffix in ("", ".tar"):
                url = f"{registry.url}/{policy}/{packages[index].name}{suffix}"
                request = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}"})
                if status == 200:
                    with urllib.request.urlopen(request, timeout=2) as response:
                        assert response.status == 200
                else:
                    with pytest.raises(urllib.error.HTTPError) as error:
                        urllib.request.urlopen(request, timeout=2)
                    assert error.value.code == status
        with pytest.raises(urllib.error.HTTPError) as unauthenticated:
            urllib.request.urlopen(f"{registry.url}/A/{packages[0].name}", timeout=2)
        assert unauthenticated.value.code == 401
    finally:
        registry.close()
