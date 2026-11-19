"""A real stdio CORTEX process exposing only the synthetic presence-test tool."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError

from babylon60.mcp.cortex_mcp_server import CortexMCPServer


VECTORS = json.loads(Path(__file__).with_name("cortex_ptc_presence.json").read_text(encoding="utf-8"))
TOOL = {
    "name": VECTORS["tool"],
    "description": (
        'Update a note initially "original". Omit nota to preserve its value; '
        'nota=null clears it; nota="" sets it to the empty string.'
    ),
    "inputSchema": VECTORS["schema"],
}


class PresenceServer(CortexMCPServer):
    """Keeps real CORTEX framing/initialization; registers no protected tools."""

    def __init__(self, observation: Path) -> None:
        self.observation = observation
        self.state: dict[str, Any] = {"nota": "original"}
        self.received: list[dict[str, Any]] = []
        self.metadata: list[Any] = []
        self.validator = Draft202012Validator(TOOL["inputSchema"])
        self._request_handlers = {
            "initialize": self._handle_initialize,
            "notifications/initialized": self._handle_initialized,
            "ping": self._handle_ping,
            "tools/list": lambda params: {"tools": [TOOL]},
            "tools/call": self.update_note,
        }
        self.observe()

    def observe(self) -> None:
        data = {
            "pid": os.getpid(),
            "state": self.state,
            "received": self.received,
            "metadata": self.metadata,
            "has_openai_key": bool(os.environ.get("OPENAI_API_KEY")),
        }
        pending = self.observation.with_suffix(".pending")
        pending.write_text(json.dumps(data, allow_nan=False), encoding="utf-8")
        pending.replace(self.observation)

    def update_note(self, params: dict[str, object]) -> dict[str, object]:
        if params.get("name") != TOOL["name"]:
            return {"content": [{"type": "text", "text": "Unknown tool"}], "isError": True}
        arguments = params.get("arguments", {})
        try:
            self.validator.validate(arguments)
        except ValidationError:
            return {"content": [{"type": "text", "text": "Invalid arguments"}], "isError": True}
        assert isinstance(arguments, dict)
        self.received.append(deepcopy(arguments))
        self.metadata.append(deepcopy(params.get("_meta")))
        if "nota" in arguments:
            self.state["nota"] = arguments["nota"]
        self.observe()
        return {"content": [{"type": "text", "text": "ok"}], "isError": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observation", type=Path, required=True)
    PresenceServer(parser.parse_args().observation).run_stdio()
