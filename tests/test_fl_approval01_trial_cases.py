"""Draft case-bank balance, privacy and independently checked policy boundaries."""

from collections import Counter, defaultdict
from copy import deepcopy
import json
import re

import pytest

from babylon60.cortex.approval_trial_cases import CaseBankError, STATUS, bank_manifest, build_case_bank, evaluate_case


@pytest.fixture
def bank():
    return build_case_bank(seed=601)


def test_bank_has_200_unique_cases_and_50_material_policy_families(bank):
    cases, answers = bank
    assert len(cases) == len(answers) == 200
    assert len({case["family_id"] for case in cases}) == 50
    assert len({case["request"]["operation"] for case in cases}) == 50
    assert len({case["evidence"]["policy_text"] for case in cases}) == 50
    assert len({json.dumps({"request": c["request"], "evidence": c["evidence"]}, sort_keys=True) for c in cases}) == 200
    assert Counter(case["domain"] for case in cases) == {"configuration": 68, "permissions": 68, "agent_action": 64}
    assert sum(answer["policy_allows"] for answer in answers.values()) == 100
    grouped = defaultdict(list)
    for case in cases:
        grouped[case["family_id"]].append(case)
    for family in grouped.values():
        assert len(family) == 4
        assert sum(answers[c["case_id"]]["policy_allows"] for c in family) == 2
        relevant = []
        for case in family:
            fields = {rule["field"].split(".")[1] for rule in case["evidence"]["criteria"]
                      if rule["field"].startswith("request.")}
            relevant.append(json.dumps({field: case["request"][field] for field in fields}, sort_keys=True))
        assert len(set(relevant)) == 4, "Variants must differ in policy-relevant inputs"


def test_participant_cases_do_not_include_private_labels_recommendations_or_seed(bank):
    cases, answers = bank
    encoded = json.dumps(cases, ensure_ascii=False)
    for private in ("policy_allows", "reference_decision", "decisive_evidence", "rationale_by_recommendation", "seed", "APPROVE", "REJECT"):
        assert private not in encoded
    assert all(re.fullmatch(r"HC-[0-9a-f]{24}", case["case_id"]) for case in cases)
    assert all(re.fullmatch(r"HF-[0-9a-f]{16}", case["family_id"]) for case in cases)
    assert all(answer["status"] == STATUS for answer in answers.values())
    assert all(set(answer["rationale_by_recommendation"]) == {"APPROVE", "REJECT"} for answer in answers.values())
    assert all("Esta preferencia no sustituye" in text for answer in answers.values()
               for text in answer["rationale_by_recommendation"].values())


def test_private_seed_reproduces_bank_but_does_not_change_policy_contents(bank):
    first, first_answers = bank
    assert bank == build_case_bank(seed=601)
    other, other_answers = build_case_bank(seed=602)
    assert {case["case_id"] for case in first}.isdisjoint(case["case_id"] for case in other)
    def content(cases, answers):
        return {json.dumps({"request": c["request"], "evidence": c["evidence"],
                            "expected": answers[c["case_id"]]["reference_decision"]}, sort_keys=True) for c in cases}
    assert content(first, first_answers) == content(other, other_answers)
    random_first, _ = build_case_bank()
    random_second, _ = build_case_bank()
    assert {c["case_id"] for c in random_first}.isdisjoint(c["case_id"] for c in random_second)


@pytest.mark.parametrize("title,field,expected", [
    ("Ventana de mantenimiento", "utc_minute", {120: True, 179: True, 180: False}),
    ("Muestreo diagnóstico", "fraction", {0.01: True, 0.1: True, 0.0: False, 0.11: False}),
    ("Finalidad y vigencia del consentimiento", "use_tick", {99: True, 100: False}),
    ("Renovación de certificados", "rsa_bits", {3072: True, 4096: True, 2048: False}),
])
def test_policies_have_independently_expected_inclusive_and_exclusive_boundaries(bank, title, field, expected):
    cases, _ = bank
    representative = next(case for case in cases if case["title"] == title and evaluate_case(case))
    for value, allowed in expected.items():
        case = deepcopy(representative)
        case["request"][field] = value
        assert evaluate_case(case) is allowed


def test_set_rules_require_all_items_and_correct_redaction(bank):
    cases, _ = bank
    ports = deepcopy(next(case for case in cases if case["title"] == "Puertos de red de un agente" and evaluate_case(case)))
    ports["request"]["ports"] = [443, 22]
    assert evaluate_case(ports) is False
    ports["request"]["ports"] = [True]
    assert evaluate_case(ports) is False
    redaction = deepcopy(next(case for case in cases if case["title"] == "Redacción de trazas" and evaluate_case(case)))
    redaction["request"]["mask_fields"] = ["email"]
    assert evaluate_case(redaction) is False


@pytest.mark.parametrize("value", [None, [], {}, "", " "])
def test_missing_or_malformed_identity_cannot_pass_exclusion_or_distinctness(bank, value):
    cases, _ = bank
    for title, field in (("Separación de aprobadores", "approver_1"), ("Borrado de copias históricas", "backup_id")):
        case = deepcopy(next(c for c in cases if c["title"] == title and evaluate_case(c)))
        case["request"][field] = value
        with pytest.raises(CaseBankError):
            evaluate_case(case)


def test_operation_is_bound_and_malformed_policies_never_silently_allow(bank):
    cases, _ = bank
    case = deepcopy(next(c for c in cases if evaluate_case(c)))
    case["request"]["operation"] = "unrelated_effect"
    assert evaluate_case(case) is False
    for malformed in ({"field": "request.unknown", "operator": "eq", "value": 1},
                      {"field": "request.operation", "operator": "unknown", "value": 1},
                      {"field": "evidence.criteria", "operator": "eq", "value": 1}):
        broken = deepcopy(case)
        broken["evidence"]["criteria"].append(malformed)
        with pytest.raises(CaseBankError):
            evaluate_case(broken)
    case["evidence"]["criteria"] = []
    with pytest.raises(CaseBankError):
        evaluate_case(case)


def test_boolean_is_not_a_numeric_quota(bank):
    cases, _ = bank
    case = deepcopy(next(c for c in cases if c["title"] == "Límite de solicitudes" and evaluate_case(c)))
    case["request"]["requests_per_minute"] = True
    with pytest.raises(CaseBankError):
        evaluate_case(case)


def test_manifest_rejects_answer_tampering_and_cannot_claim_adjudication(bank):
    cases, answers = bank
    manifest = bank_manifest(cases, answers)
    assert manifest["status"] == STATUS
    assert manifest["required_independent_adjudicators"] == 2
    assert manifest["adjudication_completed"] is False
    case_id = cases[0]["case_id"]
    broken = deepcopy(answers)
    broken[case_id]["policy_allows"] = not broken[case_id]["policy_allows"]
    with pytest.raises(CaseBankError):
        bank_manifest(cases, broken)
    promoted = deepcopy(answers)
    promoted[case_id]["status"] = "ADJUDICATED"
    with pytest.raises(CaseBankError):
        bank_manifest(cases, promoted)


def test_case_variants_do_not_share_mutable_policy_inputs(bank):
    cases, _ = bank
    first = cases[0]
    sibling = next(c for c in cases if c["family_id"] == first["family_id"] and c is not first)
    before = deepcopy(sibling)
    first["evidence"]["criteria"][0]["value"] = "changed"
    first["evidence"]["facts"]["injected"] = "changed"
    assert sibling == before


@pytest.mark.parametrize("seed", [True, "601", 1.5])
def test_seed_requires_exact_integer(seed):
    with pytest.raises(CaseBankError):
        build_case_bank(seed=seed)
