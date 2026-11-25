"""Tests for deterministic post-inference exergy transduction, MCP tool, and CLI."""

from __future__ import annotations

import time
from typing import Any

import pytest

from babylon60.transducers.post_inference_exergy import (
    _TRAILING_SLOP,
    PostInferenceExergyTransducer,
    collapse_low_entropy_lines,
    compute_c5_lexical_v2,
)


def test_aphairesis_strips_slop_and_preserves_code_links_math_hashes() -> None:
    code_block = "```rust\nfn main() {\n    // Espero que esto ayude inside code must NEVER change\n    assert_eq!(2 + 2, 4);\n}\n```"
    digest = "a" * 64
    link = "[contrato](https://example.com/spec?x=1)"
    math_span = "$$D_{\\mathrm{KL}}(p \\| q) = \\sum_i p_i \\ln(p_i / q_i)$$"
    raw = (
        "¡Claro! Aquí tienes el código solicitado.\n\n"
        f"Cabe destacar que el kernel valida el digest {digest} según {link}.\n\n"
        f"{code_block}\n\n"
        f"{math_span}\n\n"
        "Espero que esto te sea útil. No dudes en preguntar si necesitas algo más."
    )

    transducer = PostInferenceExergyTransducer()
    res = transducer.process(raw, mode="transduce")

    assert code_block in res.transduced_text
    assert digest in res.transduced_text
    assert link in res.transduced_text
    assert math_span in res.transduced_text
    assert "¡Claro!" not in res.transduced_text
    assert "Aquí tienes el código" not in res.transduced_text
    assert "No dudes en preguntar" not in res.transduced_text
    assert res.transduced_text.startswith("El kernel valida")
    assert res.receipt.protected_spans_intact is True
    assert res.receipt.slop_spans_removed >= 2
    assert res.receipt.exergy_after > res.receipt.exergy_before
    assert res.receipt.fisher_rao_after < res.receipt.fisher_rao_before


def test_context_rot_prunes_redundant_prose_but_preserves_negations_and_numbers() -> None:
    raw = (
        "El mediador criptográfico verifica firmas deterministas en memoria compartida local. "
        "El mediador criptográfico verifica firmas deterministas en memoria compartida siempre. "
        "El mediador criptográfico no autoriza mutaciones sin evidencia biométrica previa. "
        "La latencia medida alcanza 14 ms bajo carga nominal."
    )
    transducer = PostInferenceExergyTransducer()
    res = transducer.process(raw, mode="transduce", prune_context_rot=True)

    assert res.receipt.rot_sentences_pruned == 1
    assert "no autoriza mutaciones" in res.transduced_text
    assert "14 ms" in res.transduced_text
    assert "siempre." not in res.transduced_text


def test_audit_and_gate_modes_do_not_mutate_text() -> None:
    slop = "¡Por supuesto! Aquí tienes la respuesta. Espero que esto ayude mucho. Feel free to ask!"
    transducer = PostInferenceExergyTransducer(min_exergy_score=0.80)

    audit_res = transducer.process(slop, mode="audit")
    assert audit_res.transduced_text == slop
    assert audit_res.gate_passed is False
    assert audit_res.receipt.slop_spans_removed == 0

    gate_res = transducer.process(slop, mode="gate")
    assert gate_res.transduced_text == slop
    assert gate_res.gate_passed is False


def test_c5_lexical_v2_normative_formula() -> None:
    assert compute_c5_lexical_v2("") == 0
    # 5 unique words over 20-token normative floor => floor(21000 * 5 / 20) = 5250
    assert compute_c5_lexical_v2("alfa beta gamma delta epsilon https://ignored.example/path") == 5250


def test_collapse_low_entropy_lines() -> None:
    noisy = "\n".join(["INFO tick ok"] * 6 + ["ERROR root cause"])
    collapsed = collapse_low_entropy_lines(noisy, min_repeat=3)
    assert "[×5 identical low-entropy lines collapsed]" in collapsed
    assert "ERROR root cause" in collapsed


def test_mcp_exergy_transduce_tool_and_alias(tmp_path: Any) -> None:
    import json

    from babylon60.mcp.cortex_mcp_server import CortexMCPServer
    from babylon60.mcp.cortex_ptc_ralph import prune_mcp_text_payload

    server = CortexMCPServer(
        ledger_path=str(tmp_path / "ledger.db"),
        causal_gate_path=str(tmp_path / "gate.db"),
    )
    listed = server.process_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
    assert listed is not None
    listed_result = listed["result"]
    assert isinstance(listed_result, dict)
    tool_names = {t["name"] for t in listed_result["tools"]}
    assert "babylon_exergy_transduce" in tool_names

    resp = server.process_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "cortex_exergy_transduce",
                "arguments": {
                    "text": "¡Claro! Aquí tienes la respuesta.\n\nLa raíz Merkle coincide en `0xdeadbeef`.\n\nEspero que esto ayude.",
                    "mode": "transduce",
                },
            },
        }
    )
    assert resp is not None
    result = resp["result"]
    assert isinstance(result, dict)
    assert result["isError"] is False
    parsed = json.loads(result["content"][0]["text"])
    assert "`0xdeadbeef`" in parsed["transduced_text"]
    assert "¡Claro!" not in parsed["transduced_text"]
    assert parsed["receipt"]["protected_spans_intact"] is True

    # Entropic deduplication in prune_mcp_text_payload avoids middle slicing when repeated lines collapse
    repeated_log = "\n".join(["WARN retry tick"] * 40 + ["FATAL stacktrace line 42"])
    pruned = prune_mcp_text_payload(repeated_log, threshold_chars=200, head_chars=80, tail_chars=40)
    assert "FATAL stacktrace line 42" in pruned
    assert "identical low-entropy lines collapsed" in pruned
    assert "tool result middle pruned" not in pruned


def test_cli_transduce_pipe_gate_and_hook_stop(tmp_path: Any) -> None:
    import json
    import subprocess
    import sys

    draft = tmp_path / "draft.md"
    draft.write_text(
        "¡Claro! Aquí tienes el resultado.\n\nEl hash verificado es `deadbeef`.\n\nEspero que esto ayude.\n",
        encoding="utf-8",
    )

    pipe_run = subprocess.run(
        [sys.executable, "-m", "babylon60.cli.main_dispatcher", "transduce", "--input", str(draft)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert pipe_run.returncode == 0, pipe_run.stderr
    assert pipe_run.stdout.strip() == "El hash verificado es `deadbeef`."

    gate_fail = subprocess.run(
        [sys.executable, "-m", "babylon60.cli.main_dispatcher", "exergy", "--mode", "gate", "--min-exergy", "0.90"],
        input="¡Claro! Aquí tienes el código. Espero que esto ayude. Feel free to ask!",
        capture_output=True,
        text=True,
        check=False,
    )
    assert gate_fail.returncode == 1

    hook_run = subprocess.run(
        [sys.executable, "-m", "babylon60.cli.main_dispatcher", "transduce", "--hook-stop"],
        input=json.dumps({"last_assistant_message": "La verificación criptográfica finalizó con código 0."}),
        capture_output=True,
        text=True,
        check=False,
    )
    assert hook_run.returncode == 0, hook_run.stderr
    hook_payload = json.loads(hook_run.stdout)
    assert hook_payload["continue"] is True
    assert hook_payload["gate_passed"] is True


@pytest.mark.parametrize(
    ("label", "payload"),
    [
        pytest.param("es_repeat_200_nl", "avisame si necesitas " * 200 + "\n", id="es_repeat_200_nl"),
        pytest.param("es_repeat_500_x", "avisame si necesitas " * 500 + "x", id="es_repeat_500_x"),
        pytest.param("es_repeat_500_dot_x", "avisame si necesitas " * 500 + ".x", id="es_repeat_500_dot_x"),
        pytest.param("es_repeat_500_nl_x", "avisame si necesitas " * 500 + "\nx", id="es_repeat_500_nl_x"),
        pytest.param(
            "es_whitespace_pump_nl_x",
            "avisame si necesitas" + " " * 20_000 + "\nx",
            id="es_whitespace_pump_nl_x",
        ),
        pytest.param("en_repeat_200_nl", "feel free to ask " * 200 + "\n", id="en_repeat_200_nl"),
        pytest.param("en_repeat_500_x", "feel free to ask " * 500 + "x", id="en_repeat_500_x"),
        pytest.param("en_repeat_500_dot_x", "feel free to ask " * 500 + ".x", id="en_repeat_500_dot_x"),
        pytest.param("en_repeat_500_nl_x", "feel free to ask " * 500 + "\nx", id="en_repeat_500_nl_x"),
        pytest.param(
            "en_whitespace_pump_nl_x",
            "feel free to ask" + " " * 20_000 + "\nx",
            id="en_whitespace_pump_nl_x",
        ),
        pytest.param(
            "leading_spaces_20k_normal",
            " " * 20_000 + "texto normal",
            id="leading_spaces_20k_normal",
        ),
    ],
)
def test_trailing_slop_redos_linear_time(label: str, payload: str) -> None:
    """Adversarial ReDoS payloads (CodeQL #18/#19 & polynomial variants) must complete in < 0.15s."""
    for pattern in _TRAILING_SLOP:
        t0 = time.perf_counter()
        pattern.sub("", payload)
        elapsed = time.perf_counter() - t0
        assert elapsed < 0.15, f"_TRAILING_SLOP exceeded linear budget on {label}: {elapsed:.4f}s"

    transducer = PostInferenceExergyTransducer()
    t0 = time.perf_counter()
    res = transducer.process(payload, mode="transduce")
    elapsed = time.perf_counter() - t0
    assert elapsed < 0.15, f"Transducer.process exceeded linear budget on {label}: {elapsed:.4f}s"
    assert res.receipt.protected_spans_intact is True


@pytest.mark.parametrize(
    ("label", "payload"),
    [
        pytest.param("unclosed_fences", "```rust\n" * 4_000, id="unclosed_fences"),
        pytest.param("unclosed_display_latex", r"\[" * 10_000, id="unclosed_display_latex"),
        pytest.param("unclosed_inline_latex", r"\(" * 10_000, id="unclosed_inline_latex"),
        pytest.param("repeated_md_brackets", "[" * 10_000, id="repeated_md_brackets"),
        pytest.param("repeated_md_parens", "[link](" * 5_000, id="repeated_md_parens"),
        pytest.param(
            "many_trailing_slop_sentences",
            "Resultado válido. " + "Avísame si necesitas más. " * 1_000,
            id="many_trailing_slop_sentences",
        ),
        pytest.param(
            "many_trailing_slop_lines",
            "Resultado válido.\n" + "Feel free to ask\n" * 1_000,
            id="many_trailing_slop_lines",
        ),
    ],
)
def test_protected_spans_and_trailing_loop_linear_time(label: str, payload: str) -> None:
    """Secondary polynomial backtracking paths in protected masking & trailing peeling stay < 0.15s."""
    transducer = PostInferenceExergyTransducer()
    t0 = time.perf_counter()
    res = transducer.process(payload, mode="transduce")
    elapsed = time.perf_counter() - t0
    assert elapsed < 0.15, f"Transducer.process exceeded linear budget on {label}: {elapsed:.4f}s"
    assert res.receipt.protected_spans_intact is True
    if label.startswith("many_trailing_slop_"):
        assert res.transduced_text == "Resultado válido."


def test_consecutive_trailing_slop_clauses_es_en_and_mixed() -> None:
    """Multiple consecutive trailing slop clauses (ES/EN/mixed) are stripped while preserving content."""
    transducer = PostInferenceExergyTransducer()

    es_text = "Resultado válido. Espero que esto ayude. Avísame si necesitas más."
    es_res = transducer.process(es_text, mode="transduce")
    assert es_res.transduced_text == "Resultado válido."
    assert es_res.receipt.slop_spans_removed == 2

    en_text = (
        "Verified digest matches the baseline. "
        "I hope this helps! "
        "Let me know if you need anything else. "
        "Feel free to ask"
    )
    en_res = transducer.process(en_text, mode="transduce")
    assert en_res.transduced_text == "Verified digest matches the baseline."
    assert en_res.receipt.slop_spans_removed == 3

    mixed_text = "Latencia estable en 12 ms.\nEspero que esta información te sirva.\nFeel free to ask!"
    mixed_res = transducer.process(mixed_text, mode="transduce")
    assert mixed_res.transduced_text == "Latencia estable en 12 ms."
    assert mixed_res.receipt.slop_spans_removed == 2


def test_protected_fences_and_latex_brackets_preserved_with_trailing_slop() -> None:
    """Hardened O(n) fenced block and LaTeX shielders preserve structured spans verbatim."""
    tilde_block = "~~~python\n# Feel free to ask inside fenced block must survive\nprint(1 + 1)\n~~~"
    display_math = r"\[\frac{a}{b} \\ c + d\]"
    inline_math = r"\(\alpha + \beta\)"
    raw = (
        f"La identidad {inline_math} satisface:\n\n"
        f"{display_math}\n\n"
        f"{tilde_block}\n\n"
        "Espero que esto ayude. Avísame si necesitas algo más."
    )
    transducer = PostInferenceExergyTransducer()
    res = transducer.process(raw, mode="transduce")

    assert tilde_block in res.transduced_text
    assert display_math in res.transduced_text
    assert inline_math in res.transduced_text
    assert "Espero que esto ayude" not in res.transduced_text
    assert "Avísame si necesitas" not in res.transduced_text
    assert res.receipt.protected_spans_intact is True
