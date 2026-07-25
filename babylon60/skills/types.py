"""
Typed definitions and schemas for BABYLON-60 Skill Synthesizer.
Author: Borja Moskv (borjamoskv)
"""

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import time
from typing import Any


class InteractionType(str, Enum):
    CLICK = "CLICK"
    TYPE = "TYPE"
    KEY_PRESS = "KEY_PRESS"
    SCROLL = "SCROLL"
    NAVIGATE = "NAVIGATE"
    VOICE_NOTE = "VOICE_NOTE"
    ASSERTION = "ASSERTION"


@dataclass
class InteractionEvent:
    event_type: InteractionType
    selector: str
    target_text: str = ""
    bounding_box: tuple[int, int, int, int] = (0, 0, 0, 0)
    value: str = ""
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))
    lamport_t: int = 1
    causal_taint: str = "borjamoskv:skill_recorder:v1"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "selector": self.selector,
            "target_text": self.target_text,
            "bounding_box": list(self.bounding_box),
            "value": self.value,
            "timestamp": int(self.timestamp),
            "lamport_t": int(self.lamport_t),
            "causal_taint": self.causal_taint,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InteractionEvent":
        bbox = data.get("bounding_box", [0, 0, 0, 0])
        return cls(
            event_type=InteractionType(data["event_type"]),
            selector=data.get("selector", ""),
            target_text=data.get("target_text", ""),
            bounding_box=(int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])),
            value=data.get("value", ""),
            timestamp=int(data.get("timestamp", int(time.time() * 1000))),
            lamport_t=int(data.get("lamport_t", 1)),
            causal_taint=str(data.get("causal_taint", "borjamoskv:skill_recorder:v1")),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class SkillTelemetrySession:
    session_id: str
    name: str
    events: list[InteractionEvent] = field(default_factory=list)
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))
    causal_taint: str = "borjamoskv:skill_recorder:v1"

    def compute_hash(self) -> str:
        serialized = json.dumps([e.to_dict() for e in self.events], sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "name": self.name,
            "events": [e.to_dict() for e in self.events],
            "created_at": int(self.created_at),
            "causal_taint": self.causal_taint,
            "hash": self.compute_hash(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SkillTelemetrySession":
        return cls(
            session_id=data["session_id"],
            name=data["name"],
            events=[InteractionEvent.from_dict(e) for e in data.get("events", [])],
            created_at=int(data.get("created_at", int(time.time() * 1000))),
            causal_taint=str(data.get("causal_taint", "borjamoskv:skill_recorder:v1")),
        )


@dataclass
class SkillMetadata:
    skill_id: str
    name: str
    description: str
    author: str = "borjamoskv"
    version: str = "1.0.0"
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "version": self.version,
            "created_at": int(self.created_at),
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SkillMetadata":
        return cls(
            skill_id=data["skill_id"],
            name=data["name"],
            description=data.get("description", ""),
            author=data.get("author", "borjamoskv"),
            version=data.get("version", "1.0.0"),
            created_at=int(data.get("created_at", int(time.time() * 1000))),
            tags=list(data.get("tags", [])),
        )


@dataclass
class SkillASTNode:
    action: InteractionType
    target_selector: str
    target_text: str = ""
    parameter_key: str = ""
    default_value: str = ""
    self_healing_anchors: list[str] = field(default_factory=list)
    assertion_invariant: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "target_selector": self.target_selector,
            "target_text": self.target_text,
            "parameter_key": self.parameter_key,
            "default_value": self.default_value,
            "self_healing_anchors": self.self_healing_anchors,
            "assertion_invariant": self.assertion_invariant,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SkillASTNode":
        return cls(
            action=InteractionType(data["action"]),
            target_selector=data.get("target_selector", ""),
            target_text=data.get("target_text", ""),
            parameter_key=data.get("parameter_key", ""),
            default_value=data.get("default_value", ""),
            self_healing_anchors=list(data.get("self_healing_anchors", [])),
            assertion_invariant=data.get("assertion_invariant", ""),
        )


@dataclass
class SkillDefinition:
    metadata: SkillMetadata
    ast_nodes: list[SkillASTNode]
    parameters: dict[str, str] = field(default_factory=dict)
    causal_taint: str = "borjamoskv:skill_compiler:v1"

    def compute_digest(self) -> str:
        payload = {
            "metadata": self.metadata.to_dict(),
            "nodes": [n.to_dict() for n in self.ast_nodes],
            "parameters": self.parameters,
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "ast_nodes": [n.to_dict() for n in self.ast_nodes],
            "parameters": self.parameters,
            "causal_taint": self.causal_taint,
            "digest": self.compute_digest(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SkillDefinition":
        return cls(
            metadata=SkillMetadata.from_dict(data["metadata"]),
            ast_nodes=[SkillASTNode.from_dict(n) for n in data.get("ast_nodes", [])],
            parameters=dict(data.get("parameters", {})),
            causal_taint=str(data.get("causal_taint", "borjamoskv:skill_compiler:v1")),
        )
