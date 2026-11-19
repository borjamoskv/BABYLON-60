"""Tests for deterministic post-inference exergy transduction, MCP tool, and CLI."""

from __future__ import annotations

from babylon60.transducers.post_inference_exergy import (
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


def test_mcp_exergy_transduce_tool_and_alias(tmp_path) -> None:
    import json

    from babylon60.mcp.cortex_mcp_server import CortexMCPServer
    from babylon60.mcp.cortex_ptc_ralph import prune_mcp_text_payload

    server = CortexMCPServer(
        ledger_path=str(tmp_path / "ledger.db"),
        causal_gate_path=str(tmp_path / "gate.db"),
    )
    listed = server.process_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
    assert listed is not None
    tool_names = {t["name"] for t in listed["result"]["tools"]}
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


def test_cli_transduce_pipe_gate_and_hook_stop(tmp_path) -> None:
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


