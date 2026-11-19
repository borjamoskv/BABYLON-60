"""Version dependencies over real MCP processes, native broker and temporary SQLite."""

from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import shutil
import threading
from typing import Any, Iterator

import pytest

from babylon60.mcp import cortex_memory_core as core
from test_cortex_memory_mcp import BROKER_LIB, Client, ws as ws

pytestmark = pytest.mark.skipif(not BROKER_LIB.exists(), reason=f"native broker missing: {BROKER_LIB}")


@pytest.fixture
def dep_ws(ws: Path, tmp_path: Path) -> Path:
    for name in ("writer.json", "reader.json", "other.json", "op.key.pub"):
        shutil.copy2(ws / name, tmp_path / name)
    return tmp_path


@contextmanager
def client(workspace: Path, binding: str = "writer") -> Iterator[Client]:
    connection = Client(workspace, workspace / f"{binding}.json")
    try:
        yield connection
    finally:
        connection.close()


def append(connection: Client, request_id: str, value: str, **extra: Any) -> dict[str, Any]:
    result = connection.call("memory_append", request_id=request_id, value=value, **extra)
    assert result["status"] == "committed", result
    return result


@pytest.mark.parametrize("new_limit", [300, 600])
def test_source_correction_requires_revalidation_in_fresh_process(dep_ws: Path, new_limit: int) -> None:
    with client(dep_ws) as writer:
        s1 = append(writer, "s1", "El límite de aprobación es 500 €")
        i1 = append(writer, "i1", "El pedido de 400 € no requiere revisión", depends_on=[s1["memory_id"]])
        other = append(writer, "other-source", "El almacén abre a las 09:00")
        control = append(writer, "control", "Recoger el pedido a las 10:00 es posible", depends_on=[other["memory_id"]])
        before = writer.call("memory_read", text="pedido")
        assert {i["memory_id"] for i in before["items"]} == {i1["memory_id"], control["memory_id"]}
        s2 = writer.call(
            "memory_supersede", request_id="s2", target=s1["memory_id"], value=f"El límite es {new_limit} €"
        )
        assert s2["status"] == "committed"

    with client(dep_ws, "reader") as reader:
        current = reader.call("memory_read", text="pedido")
        history = reader.call("memory_read", view="history", limit=100)
    assert not current["error"] and not history["error"]
    assert current["served_by"]["instance_id"] != before["served_by"]["instance_id"]
    assert current["served_by"]["pid"] != before["served_by"]["pid"]
    assert [i["memory_id"] for i in current["items"]] == [control["memory_id"]]
    records = {i["memory_id"]: i for i in history["items"]}
    assert records[i1["memory_id"]]["status"] == "PENDING_REVALIDATION"
    assert records[i1["memory_id"]]["depends_on"] == [s1["memory_id"]]
    assert records[i1["memory_id"]]["value"] == "El pedido de 400 € no requiere revisión"
    assert records[s1["memory_id"]]["status"] == "SUPERSEDED"
    assert records[s1["memory_id"]]["superseded_by"] == s2["memory_id"]
    assert records[s1["memory_id"]]["provenance"]["entry_hash"] == s1["entry_hash"]
    assert records[control["memory_id"]]["status"] == "ACTIVE"
    report = core.replay(dep_ws / "ledger.db")
    assert report["chain_ok"] and report["receipt_mismatches"] == []
    assert report["receipts_checked"] == 3
    (dep_ws / "acceptance-trace.json").write_text(
        json.dumps(
            {
                "new_limit": new_limit,
                "s1": s1,
                "i1": i1,
                "s2": s2,
                "before": before,
                "current": current,
                "history": history,
                "replay": report,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize("operation", ["memory_supersede", "memory_forget"])
def test_transitive_dependencies_and_explicit_revalidation(dep_ws: Path, operation: str) -> None:
    with client(dep_ws) as writer:
        source = append(writer, "source", "threshold 500")
        independent = append(writer, "independent", "the request is complete")
        first_args = {"request_id": "first", "value": "review unnecessary", "depends_on": [source["memory_id"]]}
        first = writer.call("memory_append", **first_args)
        assert first["status"] == "committed"
        last = append(writer, "last", "submit the order", depends_on=[first["memory_id"], independent["memory_id"]])
        replacement_args = {"value": "threshold 600"} if operation == "memory_supersede" else {}
        change = writer.call(operation, request_id="change", target=source["memory_id"], **replacement_args)
        assert change["status"] == "committed"
        # Retries acknowledge the original event; they never renew its justification.
        retry = writer.call("memory_append", **first_args)
        assert retry["replayed"] and retry["memory_id"] == first["memory_id"]
        for n, parent in enumerate((source, first, last)):
            rejected = writer.call(
                "memory_append", request_id=f"stale-{n}", value="new", depends_on=[parent["memory_id"]]
            )
            assert rejected["status"] == "denied" and rejected["reason"] == "dependency is not active"
        history = writer.call("memory_read", view="history", limit=100)
        by_id = {i["memory_id"]: i for i in history["items"]}
        assert by_id[first["memory_id"]]["status"] == by_id[last["memory_id"]]["status"] == "PENDING_REVALIDATION"
        assert by_id[independent["memory_id"]]["status"] == "ACTIVE"
        assert by_id[source["memory_id"]]["status"] == (
            "SUPERSEDED" if operation == "memory_supersede" else "FORGOTTEN"
        )
        detached = writer.call("memory_supersede", request_id="detached", target=first["memory_id"], value="still true")
        assert detached["status"] == "denied"
        new_source = change if operation == "memory_supersede" else append(writer, "new-source", "threshold 600")
        revalidated = writer.call(
            "memory_supersede",
            request_id="revalidate",
            target=first["memory_id"],
            value=first_args["value"],
            depends_on=[new_source["memory_id"]],
        )
        assert revalidated["status"] == "committed"
    with client(dep_ws, "reader") as reader:
        current = reader.call("memory_read", limit=100)
        ids = {i["memory_id"] for i in current["items"]}
        assert revalidated["memory_id"] in ids and last["memory_id"] not in ids
        assert first["memory_id"] not in ids
    assert core.replay(dep_ws / "ledger.db")["receipt_mismatches"] == []


def test_dependency_scope_and_replacement_cannot_invalidate_its_own_support(dep_ws: Path) -> None:
    with client(dep_ws, "other") as other:
        foreign = append(other, "foreign", "private source")
    with client(dep_ws) as writer:
        for n, reference in enumerate((foreign["memory_id"], "unknown")):
            response = writer.call(
                "memory_append", request_id=f"missing-{n}", value="inference", depends_on=[reference]
            )
            assert response["status"] == "denied" and response["reason"] == "dependency not found in this project"
        source = append(writer, "source", "source")
        child = append(writer, "child", "child", depends_on=[source["memory_id"]])
        for n, dependency in enumerate((source, child)):
            response = writer.call(
                "memory_supersede",
                request_id=f"circular-{n}",
                target=source["memory_id"],
                value="replacement",
                depends_on=[dependency["memory_id"]],
            )
            assert response["status"] == "denied" and "version it supersedes" in response["reason"]
        current = writer.call("memory_read", limit=100)
        assert {i["memory_id"] for i in current["items"]} == {source["memory_id"], child["memory_id"]}


@pytest.mark.parametrize(
    "dependencies", ["source", [1], [True], [{}], [""], ["x" * 65], ["x", "x"], list(map(str, range(33)))]
)
def test_malformed_dependencies_are_rejected(dep_ws: Path, dependencies: Any) -> None:
    with client(dep_ws) as writer:
        result = writer.call("memory_append", request_id="bad", value="inference", depends_on=dependencies)
        assert result["status"] == "invalid"
        assert writer.call("memory_read")["items"] == []


def test_unrecorded_semantic_dependency_is_not_invented(dep_ws: Path) -> None:
    with client(dep_ws) as writer:
        source = append(writer, "source", "threshold 500")
        unsupported = append(writer, "unsupported", "order 400 needs no review")
        response = writer.call(
            "memory_supersede", request_id="change", target=source["memory_id"], value="threshold 300"
        )
        assert response["status"] == "committed"
        result = writer.call("memory_read", text="order")
        assert [i["memory_id"] for i in result["items"]] == [unsupported["memory_id"]]
        assert result["items"][0]["depends_on"] == []


def test_correction_racing_derivation_never_leaves_current_inference(dep_ws: Path) -> None:
    # Two warmup rounds, then twenty rounds through two independent MCP processes.
    with client(dep_ws) as writer, client(dep_ws) as deriving:
        for round_no in range(22):
            source = append(writer, f"s-{round_no}", f"source {round_no}")
            barrier = threading.Barrier(2)
            results: dict[str, dict[str, Any]] = {}
            errors: list[BaseException] = []

            def run(connection: Client, tool: str, **arguments: Any) -> None:
                try:
                    barrier.wait(timeout=10)
                    results[tool] = connection.call(tool, **arguments)
                except BaseException as exc:
                    errors.append(exc)

            writes = [
                threading.Thread(
                    target=run,
                    args=(writer, "memory_supersede"),
                    kwargs={
                        "request_id": f"replace-{round_no}",
                        "target": source["memory_id"],
                        "value": "corrected",
                    },
                ),
                threading.Thread(
                    target=run,
                    args=(deriving, "memory_append"),
                    kwargs={
                        "request_id": f"derive-{round_no}",
                        "value": f"inference {round_no}",
                        "depends_on": [source["memory_id"]],
                    },
                ),
            ]
            for thread in writes:
                thread.start()
            for thread in writes:
                thread.join(timeout=15)
                assert not thread.is_alive()
            assert not errors
            assert results["memory_supersede"]["status"] == "committed"
            inference = results["memory_append"]
            assert inference["status"] in ("committed", "denied")
            assert writer.call("memory_read", text="inference", limit=100)["items"] == []
            if inference["status"] == "committed":
                history = writer.call("memory_read", text=f"inference {round_no}", view="history", limit=100)
                saved = next(i for i in history["items"] if i["memory_id"] == inference["memory_id"])
                assert saved["status"] == "PENDING_REVALIDATION"
            else:
                assert inference["reason"] == "dependency is not active"
    replay = core.replay(dep_ws / "ledger.db")
    assert replay["chain_ok"] and replay["receipt_mismatches"] == []
