"""Portable signature negotiation and the read-only MCP Apps boundary."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
from typing import cast

import pytest

from babylon60.mcp.signature_ui import (
    SIGNATURE_SCHEMA_URI,
    SIGNATURE_TOOL_NAME,
    SIGNATURE_UI_MIME,
    SIGNATURE_UI_URI,
    read_signature_resource,
    render_signature_result,
    signature_resources,
    signature_tool_descriptor,
    supports_signature_ui,
)


def _object(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def _payload() -> dict[str, object]:
    return {
        "observed_at": "2026-10-18T09:15:00+02:00",
        "fields": {"LLM": "Modelo de prueba <script>alert(1)</script>"},
        "sources": {"LLM": "Metadatos de una sesión de prueba"},
    }


def _resource_text(uri: str) -> str:
    contents = read_signature_resource(uri)["contents"]
    assert isinstance(contents, list)
    result = _object(contents[0])["text"]
    assert isinstance(result, str)
    return result


@pytest.mark.parametrize(
    "capabilities",
    [
        None,
        [],
        {},
        {"name": "claude-desktop"},
        {"ui": {"mimeTypes": [SIGNATURE_UI_MIME]}},
        {"extensions": {"io.modelcontextprotocol/ui": {"mimeTypes": SIGNATURE_UI_MIME}}},
        {"extensions": {"io.modelcontextprotocol/ui": {"mimeTypes": ["text/html"]}}},
        {"extensions": {"io.modelcontextprotocol/ui": True}},
    ],
)
def test_ui_support_requires_the_negotiated_extension(capabilities: object) -> None:
    assert not supports_signature_ui(capabilities)


def test_ui_capability_exposes_tool_resource_link_and_closed_network_policy() -> None:
    capabilities = {"extensions": {"io.modelcontextprotocol/ui": {"mimeTypes": [SIGNATURE_UI_MIME]}}}
    assert supports_signature_ui(capabilities)
    assert "_meta" not in signature_tool_descriptor()
    descriptor = signature_tool_descriptor(ui_supported=True)
    assert descriptor["name"] == SIGNATURE_TOOL_NAME
    assert _object(descriptor["_meta"])["ui"] == {"resourceUri": SIGNATURE_UI_URI}
    resource_uris = {item["uri"] for item in signature_resources(ui_supported=True)}
    assert resource_uris == {SIGNATURE_UI_URI, SIGNATURE_SCHEMA_URI}
    assert {item["uri"] for item in signature_resources()} == {SIGNATURE_SCHEMA_URI}
    contents = read_signature_resource(SIGNATURE_UI_URI)["contents"]
    assert isinstance(contents, list)
    resource = _object(contents[0])
    assert resource["mimeType"] == SIGNATURE_UI_MIME
    assert _object(resource["_meta"])["ui"] == {
        "csp": {"connectDomains": [], "resourceDomains": []},
        "prefersBorder": False,
    }


def test_schema_is_a_machine_resource_and_unknown_uris_do_not_read_files() -> None:
    assert _object(json.loads(_resource_text(SIGNATURE_SCHEMA_URI)))["type"] == "object"
    with pytest.raises(ValueError, match="resource"):
        read_signature_resource("file:///etc/passwd")


@pytest.mark.parametrize(
    "ui_supported,requested,selected",
    [
        (False, "auto", "markdown"),
        (True, "auto", "ui"),
        (False, "ui", "markdown"),
        (True, "text", "text"),
        (True, "html", "html"),
        (False, "json", "json"),
    ],
)
def test_render_result_preserves_data_and_chooses_supported_output(
    ui_supported: bool,
    requested: str,
    selected: str,
) -> None:
    result = render_signature_result(_payload(), format=requested, ui_supported=ui_supported)
    assert result.get("isError") is not True
    structured = _object(result["structuredContent"])
    assert structured["selected_format"] == selected
    signature = _object(structured["signature"])
    assert signature["observed_at"] == _payload()["observed_at"]
    assert _object(signature["fields"])["LLM"] == _object(_payload()["fields"])["LLM"]
    content = result["content"]
    assert isinstance(content, list)
    rendered = _object(content[0])["text"]
    assert isinstance(rendered, str) and rendered
    if selected == "html":
        assert "<script>alert(1)</script>" not in rendered
        assert "&lt;script&gt;" in rendered


@pytest.mark.parametrize(
    "payload,format",
    [
        ({}, "auto"),
        (_payload(), "pdf"),
        ({"observed_at": "2026-10-18T09:15:00+02:00", "fields": {"LLM": "Inventado"}}, "auto"),
    ],
)
def test_invalid_input_returns_visible_error_without_partial_signature(payload: dict[str, object], format: str) -> None:
    result = render_signature_result(payload, format=format)
    assert result["isError"] is True
    assert "structuredContent" not in result


def test_app_receives_only_parent_data_and_does_not_execute_strings(tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is needed to exercise the browser message bridge")
    app_html = _resource_text(SIGNATURE_UI_URI)
    assert app_html.lower().startswith("<!doctype html>")
    assert "<iframe" not in app_html
    assert "fetch(" not in app_html and "innerHTML" not in app_html
    app_path = tmp_path / "app.html"
    app_path.write_text(app_html, encoding="utf-8")
    # Deliberately tiny DOM: an innerHTML write fails instead of silently allowing injection.
    harness = r"""
const fs = require("node:fs"), vm = require("node:vm"), assert = require("node:assert/strict");
const html = fs.readFileSync(process.argv[1], "utf8");
const nodes = new Map(), sent = [], handlers = new Map();
function element() {
  return {textContent:"", hidden:false, dataset:{}, children:[], style:{},
    setAttribute(k,v){this[k]=v;}, removeAttribute(k){delete this[k];},
    replaceChildren(...items){this.children=items;}, append(...items){this.children.push(...items);},
    getBoundingClientRect(){return {width:600,height:320};},
    set innerHTML(value){throw new Error("Unsafe innerHTML write");}};
}
const document = {body:element(),documentElement:element(),
  getElementById(id){if(!nodes.has(id))nodes.set(id,element());return nodes.get(id);},
  createElement(){return element();}};
const parent = {postMessage(message){sent.push(message);}};
const window = {parent, addEventListener(k, fn){handlers.set(k,fn);}, removeEventListener(k){handlers.delete(k);}};
const context = {document, window, ResizeObserver:class {observe(){} disconnect(){}},
  setTimeout(){return 1;}, clearTimeout(){}, requestAnimationFrame(fn){fn();}, console};
vm.runInNewContext(html.match(/<script>([\s\S]*?)<\/script>/)[1], context);
assert.equal(sent[0].method,"ui/initialize");
assert.equal(sent[0].params.protocolVersion,"2026-01-26");
function message(data,source=parent){handlers.get("message")({data,source});}
message({jsonrpc:"2.0",id:sent[0].id,result:{protocolVersion:"2026-01-26",hostContext:{theme:"dark"}}},{});
assert.equal(sent.length,1);
message({jsonrpc:"2.0",id:sent[0].id,result:{protocolVersion:"2026-01-26",hostContext:{theme:"dark"}}});
assert.equal(sent[1].method,"ui/notifications/initialized");
assert.equal(document.documentElement.dataset.theme,"dark");
const signature = JSON.parse(process.argv[2]);
message({jsonrpc:"2.0",method:"ui/notifications/tool-result",params:{structuredContent:{signature}}});
assert.equal(nodes.get("signature-model").textContent,signature.fields.LLM);
assert.equal(nodes.get("signature-time").textContent,signature.observed_at);
assert.equal(nodes.get("signature-status").hidden,true);
assert.equal(nodes.get("signature-effort").hidden,true);
assert.equal(nodes.get("signature-context").children.length,0);
const details = {"VERIFICACIÓN":"20 pruebas correctas", "CAMBIOS":"Puente MCP actualizado",
  "LÍMITES":"Clientes sin UI usan texto"};
Object.assign(signature.fields, details);
for (const field of Object.keys(details)) signature.sources[field] = "Registro del turno";
message({jsonrpc:"2.0",method:"ui/notifications/tool-result",params:{structuredContent:{signature}}});
assert.deepEqual(nodes.get("signature-context").children.map(row=>row.children[1].textContent),Object.values(details));
assert.equal(nodes.get("signature-sources").children.length,5);
message({jsonrpc:"2.0",method:"ui/notifications/tool-input",params:{arguments:{}}});
assert.equal(nodes.get("signature-panel").hidden,true);
assert.equal(nodes.get("signature-status").hidden,false);
message({jsonrpc:"2.0",method:"ui/notifications/tool-result",params:{structuredContent:{signature,selected_format:"text"}}});
assert.equal(nodes.get("signature-panel").hidden,true);
assert.equal(nodes.get("signature-status").hidden,true);
message({jsonrpc:"2.0",method:"ui/notifications/tool-result",params:{structuredContent:{signature,selected_format:"ui"}}});
assert.equal(nodes.get("signature-panel").hidden,false);
message({jsonrpc:"2.0",method:"ui/notifications/tool-result",params:{isError:true}});
assert.equal(nodes.get("signature-panel").hidden,true);
assert.equal(nodes.get("signature-status").hidden,false);
message({jsonrpc:"2.0",id:99,method:"ui/resource-teardown",params:{}});
assert.equal(sent.at(-1).id,99);
assert.equal(handlers.has("message"),false);
"""
    result = render_signature_result(_payload())
    signature = _object(result["structuredContent"])["signature"]
    completed = subprocess.run(
        [node, "-e", harness, str(app_path), json.dumps(signature)],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
