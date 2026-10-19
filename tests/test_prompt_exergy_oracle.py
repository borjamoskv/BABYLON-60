"""Contract checks for the lexical index and evidence-based work summary."""

from dataclasses import FrozenInstanceError, asdict
import json
import os
from pathlib import Path
import random
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from scripts.c5_quality_gates import prompt_exergy_oracle as oracle

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/c5_quality_gates/prompt_exergy_oracle.py"


def run_cli(*arguments: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *arguments],
        input=stdin,
        text=True,
        capture_output=True,
        env=env,
        cwd=REPO_ROOT,
        timeout=15,
        check=False,
    )


def write_json(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("text", "count", "unique", "classification"),
    [
        ("", 0, 0, "SIN_TEXTO_EVALUABLE"),
        (" \t\n", 0, 0, "SIN_TEXTO_EVALUABLE"),
        ("___ !!! 😀", 0, 0, "SIN_TEXTO_EVALUABLE"),
        ("https://example.org/path?token=secret", 0, 0, "SIN_TEXTO_EVALUABLE"),
        ("HTTP://EXAMPLE.ORG/path", 0, 0, "SIN_TEXTO_EVALUABLE"),
        ("ftp://example.org/hidden/tokens", 0, 0, "SIN_TEXTO_EVALUABLE"),
        ("mailto:person@example.org", 0, 0, "SIN_TEXTO_EVALUABLE"),
        ("file:///root/secret/file.md", 0, 0, "SIN_TEXTO_EVALUABLE"),
        ("antes ftp://example.org/hidden después", 2, 2, "MUESTRA_BREVE"),
        ("antes mailto:person@example.org después", 2, 2, "MUESTRA_BREVE"),
        ("antes file:///root/secret/file.md después", 2, 2, "MUESTRA_BREVE"),
        ("itera", 1, 1, "MUESTRA_BREVE"),
        ("ITERA itera ÍTERA", 3, 1, "MUESTRA_BREVE"),
        ("café cafe cafe\u0301", 3, 1, "MUESTRA_BREVE"),
        ("ＡＢＣ abc", 2, 1, "MUESTRA_BREVE"),
        ("Straße STRASSE", 2, 1, "MUESTRA_BREVE"),
        ("acción_legal acción-legal", 4, 2, "MUESTRA_BREVE"),
        ("漢字 漢字 λογος", 3, 2, "MUESTRA_BREVE"),
        ("[Estado verificable](https://example.org/hidden/tokens)", 2, 2, "MUESTRA_BREVE"),
        ("[Estado](docs/hidden/tokens.md)", 1, 1, "MUESTRA_BREVE"),
        ('[Estado](https://example.org/a(b)c "hidden title")', 1, 1, "MUESTRA_BREVE"),
        ("[Estado](https://example.org/a(b)c) después", 2, 2, "MUESTRA_BREVE"),
        ("[label][ref]\n[ref]:\n  /root/secret/file.md", 1, 1, "MUESTRA_BREVE"),
        ('[label][ref]\n[ref]: /root/secret/file.md\n  "hidden title words"', 1, 1, "MUESTRA_BREVE"),
        ('[label][ref]\n[ref]:\n  /root/secret/file.md\n  "hidden title words"', 1, 1, "MUESTRA_BREVE"),
        (
            '[label][ref]\n[ref]:\n  /root/secret/file.md\n  "hidden title words"\n\ntexto posterior',
            3,
            3,
            "MUESTRA_BREVE",
        ),
        ("antes https://example.org/hidden/tokens después", 2, 2, "MUESTRA_BREVE"),
        ("eco " * 19, 19, 1, "MUESTRA_BREVE"),
        ("eco " * 20, 20, 1, "INDICE_LEXICO"),
        ("eco " * 21, 21, 1, "INDICE_LEXICO"),
        (" ".join(f"term{i}" for i in range(20)), 20, 20, "INDICE_LEXICO"),
    ],
)
def test_normalization_formula_and_classification(text: str, count: int, unique: int, classification: str) -> None:
    score = oracle.evaluate_prompt_exergy(text)
    expected = 21000 * unique // max(count, 20)
    assert score.method == "c5-lexical-v2"
    assert score.token_count == count
    assert score.unique_token_count == unique
    assert score.c5_score == expected
    assert score.raw_score == pytest.approx(expected / 21000)
    assert score.classification == classification
    assert isinstance(score.diagnostic, str) and score.diagnostic


def test_legacy_constructor_accepts_original_eight_fields() -> None:
    score = oracle.ExergyScore(0.5, 10500, "legacy", 4.0, 1.0, 0.0, False, "legacy diagnostic")
    assert score.raw_score == 0.5
    assert score.c5_score == 10500
    assert score.method == "c5-lexical-v2"
    assert score.token_count == 0
    assert score.unique_token_count == 0
    assert len(asdict(score)) == 11


def test_one_thousand_deterministic_random_cases() -> None:
    rng = random.Random(6060)
    vocabulary = [f"term{i}" for i in range(40)]
    for case in range(1000):
        words = rng.choices(vocabulary, k=rng.randrange(101))
        expected_unique = len(set(words))
        text = " ".join(words)
        if case % 3 == 0:
            text += " https://example.org/not/countable?hidden=words"
        score = oracle.evaluate_prompt_exergy(text)
        assert score.token_count == len(words), case
        assert score.unique_token_count == expected_unique, case
        assert score.c5_score == 21000 * expected_unique // max(len(words), 20), case
        assert 0 <= score.c5_score <= 21000, case
        rng.shuffle(words)
        reordered = oracle.evaluate_prompt_exergy(" ".join(words).upper())
        assert (reordered.token_count, reordered.unique_token_count, reordered.c5_score) == (
            score.token_count,
            score.unique_token_count,
            score.c5_score,
        ), case
        duplicated = oracle.evaluate_prompt_exergy(" ".join(words * 2))
        assert duplicated.token_count == 2 * len(words), case
        assert duplicated.unique_token_count == expected_unique, case
        assert duplicated.c5_score <= score.c5_score, case


def test_distinct_technical_and_common_words_receive_the_same_score() -> None:
    technical = oracle.evaluate_prompt_exergy("seqlock mmap fsync rust lean z3")
    common = oracle.evaluate_prompt_exergy("mesa silla puerta casa calle ventana")
    assert technical.token_count == common.token_count == 6
    assert technical.unique_token_count == common.unique_token_count == 6
    assert technical.c5_score == common.c5_score == 6300


@pytest.mark.parametrize("text", ["itera", "deploy", "prueba de estres", "touch id secure enclave"])
def test_special_vocabulary_receives_no_score_override(text: str) -> None:
    score = oracle.evaluate_prompt_exergy(text)
    assert score.c5_score == 21000 * score.unique_token_count // max(score.token_count, 20)
    assert score.classification == "MUESTRA_BREVE"


def test_summary_counts_all_three_states_and_preserves_evidence() -> None:
    criteria = [
        oracle.WorkCriterion("build", "Compile", "passed", ("build exit 0",)),
        oracle.WorkCriterion("test", "Check behavior", "failed", ("assertion failed",)),
        oracle.WorkCriterion("remote", "Check remote state", "pending", ()),
    ]
    summary = oracle.summarize_work(criteria)
    assert (summary.passed, summary.failed, summary.pending, summary.total) == (1, 1, 1, 3)
    assert summary.criteria == tuple(criteria)
    assert isinstance(summary.summary, str) and summary.summary
    assert summary.criteria[0].evidence == ("build exit 0",)


def test_empty_summary_and_immutable_criterion() -> None:
    summary = oracle.summarize_work([])
    assert (summary.passed, summary.failed, summary.pending, summary.total) == (0, 0, 0, 0)
    assert summary.criteria == ()
    assert summary.summary == "Sin criterios definidos"
    criterion = oracle.WorkCriterion("read", "Read state", "pending", ())
    with pytest.raises(FrozenInstanceError):
        setattr(criterion, "status", "passed")


def test_summary_rejects_duplicate_ids() -> None:
    with pytest.raises(ValueError):
        oracle.summarize_work(
            [
                oracle.WorkCriterion("same", "One", "pending", ()),
                oracle.WorkCriterion("same", "Two", "failed", ()),
            ]
        )


def test_summary_rejects_duplicate_ids_with_surrounding_spaces() -> None:
    with pytest.raises(ValueError):
        oracle.summarize_work(
            [
                oracle.WorkCriterion("same", "One", "pending", ()),
                oracle.WorkCriterion("  same  ", "Two", "failed", ()),
            ]
        )


def test_loader_rejects_duplicate_ids_with_surrounding_spaces(tmp_path: Path) -> None:
    payload = [
        {"id": "same", "description": "One", "status": "pending", "evidence": []},
        {"id": "  same  ", "description": "Two", "status": "failed", "evidence": []},
    ]
    with pytest.raises(ValueError):
        oracle.load_work_criteria(write_json(tmp_path / "duplicates.json", payload))


def test_summary_rejects_passed_without_evidence() -> None:
    with pytest.raises(ValueError):
        oracle.summarize_work([oracle.WorkCriterion("claim", "Claim", "passed", ())])


def test_load_criteria_preserves_valid_data(tmp_path: Path) -> None:
    payload = [
        {"id": "build", "description": "Compilar", "status": "passed", "evidence": ["exit 0", "hash abc"]},
        {"id": "test", "description": "Probar", "status": "failed", "evidence": []},
        {"id": "remote", "description": "Remoto", "status": "pending", "evidence": []},
    ]
    criteria = oracle.load_work_criteria(write_json(tmp_path / "criteria.json", payload))
    assert isinstance(criteria, list)
    assert criteria == [
        oracle.WorkCriterion("build", "Compilar", "passed", ("exit 0", "hash abc")),
        oracle.WorkCriterion("test", "Probar", "failed", ()),
        oracle.WorkCriterion("remote", "Remoto", "pending", ()),
    ]


def test_load_empty_criteria_list(tmp_path: Path) -> None:
    assert oracle.load_work_criteria(write_json(tmp_path / "empty.json", [])) == []


@pytest.mark.parametrize("payload", [None, {}, "criteria", 42, True, [None], ["criterion"], [[]]])
def test_loader_rejects_wrong_structure(tmp_path: Path, payload: object) -> None:
    with pytest.raises(ValueError):
        oracle.load_work_criteria(write_json(tmp_path / "wrong.json", payload))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", 1),
        ("id", True),
        ("id", None),
        ("id", ""),
        ("id", "  "),
        ("description", 1),
        ("description", None),
        ("description", ""),
        ("description", " \t"),
        ("status", "complete"),
        ("status", "Passed"),
        ("status", 1),
        ("status", None),
        ("evidence", "exit 0"),
        ("evidence", {}),
        ("evidence", None),
        ("evidence", [1]),
        ("evidence", [False]),
        ("evidence", [None]),
        ("evidence", [""]),
        ("evidence", [" \t"]),
    ],
)
def test_loader_rejects_invalid_field_types_and_empty_values(tmp_path: Path, field: str, value: object) -> None:
    criterion: dict[str, object] = {"id": "build", "description": "Compile", "status": "passed", "evidence": ["exit 0"]}
    criterion[field] = value
    with pytest.raises(ValueError):
        oracle.load_work_criteria(write_json(tmp_path / "invalid.json", [criterion]))


@pytest.mark.parametrize("missing", ["id", "description", "status", "evidence"])
def test_loader_rejects_missing_fields(tmp_path: Path, missing: str) -> None:
    criterion: dict[str, object] = {"id": "build", "description": "Compile", "status": "passed", "evidence": ["exit 0"]}
    del criterion[missing]
    with pytest.raises(ValueError):
        oracle.load_work_criteria(write_json(tmp_path / "missing.json", [criterion]))


def test_loader_rejects_extra_fields(tmp_path: Path) -> None:
    payload = [{"id": "build", "description": "Compile", "status": "passed", "evidence": ["exit 0"], "score": 21000}]
    with pytest.raises(ValueError):
        oracle.load_work_criteria(write_json(tmp_path / "extra.json", payload))


@pytest.mark.parametrize("contents", ["", "[", "{not json}", '[{"id":"x"},]', "\ufeff[]"])
def test_loader_rejects_malformed_json(tmp_path: Path, contents: str) -> None:
    path = tmp_path / "malformed.json"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(ValueError):
        oracle.load_work_criteria(path)


@pytest.mark.parametrize("arguments", [(), ("--test",), ("itera",), ("uno", "dos")])
def test_legacy_cli_modes_exit_successfully(arguments: tuple[str, ...]) -> None:
    result = run_cli(*arguments)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip()


def test_stdin_json_preserves_multiline_text(tmp_path: Path) -> None:
    path = write_json(
        tmp_path / "criteria.json",
        [
            {"id": "build", "description": "Compile", "status": "passed", "evidence": ["exit 0"]},
            {"id": "test", "description": "Test", "status": "failed", "evidence": ["failure"]},
            {"id": "remote", "description": "Remote", "status": "pending", "evidence": []},
        ],
    )
    text = "café\nCAFE\n[Estado](https://example.org/hidden)"
    result = run_cli("--stdin", "--json", "--criteria", str(path), stdin=text)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert set(payload) == {"text", "work"}
    assert payload["text"] == asdict(oracle.evaluate_prompt_exergy(text))
    assert (
        payload["work"]["passed"],
        payload["work"]["failed"],
        payload["work"]["pending"],
        payload["work"]["total"],
    ) == (1, 1, 1, 3)
    assert payload["work"]["criteria"][0]["evidence"] == ["exit 0"]


def test_json_positional_text(tmp_path: Path) -> None:
    path = write_json(tmp_path / "criteria.json", [])
    result = run_cli("--json", "--criteria", str(path), "uno", "dos")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["text"] == asdict(oracle.evaluate_prompt_exergy("uno dos"))
    assert payload["work"]["total"] == 0


def test_empty_stdin_is_valid_text() -> None:
    result = run_cli("--stdin", "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["text"]["classification"] == "SIN_TEXTO_EVALUABLE"
    assert payload["text"]["c5_score"] == 0
    assert payload["work"] == {
        "passed": 0,
        "failed": 0,
        "pending": 0,
        "total": 0,
        "criteria": [],
        "summary": "Sin criterios definidos",
    }


@pytest.mark.parametrize(
    "arguments",
    [("--unknown",), ("--criteria",), ("--stdin", "mixed text"), ("--test", "--stdin"), ("--test",)],
)
def test_cli_rejects_invalid_or_mixed_modes_without_partial_json(arguments: tuple[str, ...]) -> None:
    result = run_cli("--json", *arguments, stdin="input")
    assert result.returncode == 2
    assert result.stderr.strip()
    assert not result.stdout.strip()


@pytest.mark.parametrize(
    "payload",
    [
        {},
        [{"id": "x", "description": "Check", "status": "passed", "evidence": []}],
        [{"id": "x", "description": "Check", "status": "pending", "evidence": [3]}],
        [
            {"id": "x", "description": "One", "status": "pending", "evidence": []},
            {"id": "x", "description": "Two", "status": "failed", "evidence": []},
        ],
    ],
)
def test_cli_rejects_bad_criteria_without_partial_json(tmp_path: Path, payload: object) -> None:
    path = write_json(tmp_path / "criteria.json", payload)
    result = run_cli("--stdin", "--json", "--criteria", str(path), stdin="itera")
    assert result.returncode == 2
    assert result.stderr.strip()
    assert not result.stdout.strip()


@pytest.mark.parametrize("kind", ["missing", "malformed", "invalid_utf8", "directory"])
def test_cli_rejects_unreadable_criteria_without_partial_json(tmp_path: Path, kind: str) -> None:
    path = tmp_path / "criteria.json"
    if kind == "malformed":
        path.write_text("[", encoding="utf-8")
    elif kind == "invalid_utf8":
        path.write_bytes(b"\xff")
    elif kind == "directory":
        path.mkdir()
    result = run_cli("--stdin", "--json", "--criteria", str(path), stdin="texto")
    assert result.returncode == 2
    assert result.stderr.strip()
    assert not result.stdout.strip()
