# [C5-REAL] Memory models for Cortex Fact representations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CortexFactModel:
    id: str
    tenant_id: str = "sovereign"
    project_id: str = "autodidact_knowledge"
    content: str = ""
    embedding: list[float] | None = None
    timestamp: float = 0.0
    is_diamond: bool = True
    confidence: str = "C5"
    cognitive_layer: str = "semantic"
    metadata: dict[str, Any] = field(default_factory=dict)
    _recall_score: float = 0.0
