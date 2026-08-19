"""
BABYLON-60 Dynamic MCP Deductive Engine (C5-REAL)
Motor de Abducción de Contratos MCP basado en Fricción Entrópica
"""

from dataclasses import dataclass, field
import logging
import json
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class McpToolParameter:
    name: str
    param_type: str
    description: str
    required: bool = True


@dataclass
class McpCandidateContract:
    server_name: str
    tool_name: str
    description: str
    parameters: List[McpToolParameter] = field(default_factory=list)
    target_protocol: str = "stdio"
    estimated_exergy_gain: float = 0.5

    def to_json_schema(self) -> Dict[str, Any]:
        """Genera el JSON Schema para las propiedades de la herramienta."""
        properties = {}
        required_list = []
        for param in self.parameters:
            properties[param.name] = {
                "type": param.param_type,
                "description": param.description,
            }
            if param.required:
                required_list.append(param.name)

        return {
            "type": "object",
            "properties": properties,
            "required": required_list,
        }


class McpDeductiveEngine:
    """
    Evalúa la traza de ejecución del agente y deduce la necesidad de sintetizar un nuevo MCP.
    """

    def __init__(self, friction_threshold: float = 0.40):
        self.friction_threshold = friction_threshold

    def calculate_friction(self, execution_steps: List[Dict[str, Any]]) -> float:
        """
        Calcula la fricción entrópica F_a:
        F_a = (Tokens Totales * Repeticiones) / (Resultado Útil * 1000)
        """
        if not execution_steps:
            return 0.0

        total_tokens = sum(step.get("tokens", 100) for step in execution_steps)
        repetition_count = len(execution_steps)
        errors = sum(1 for step in execution_steps if step.get("status") == "ERROR")

        # Fricción normalizada en intervalo [0.0, 1.0]
        base_friction = min(1.0, (total_tokens * repetition_count) / 10000.0)
        penalty = 0.2 * errors
        return min(1.0, base_friction + penalty)

    def should_deduce_mcp(self, execution_steps: List[Dict[str, Any]]) -> bool:
        """Determina si la fricción supera el umbral para justificar la creación de un MCP."""
        friction = self.calculate_friction(execution_steps)
        logger.info(f"[McpDeductiveEngine] Fricción evaluada: {friction:.4f} (Umbral: {self.friction_threshold})")
        return friction >= self.friction_threshold

    def deduce_contract(
        self, domain_name: str, sample_calls: List[Dict[str, Any]]
    ) -> McpCandidateContract:
        """
        Sintetiza la especificación formal del MCP candidate desde las llamadas observadas.
        """
        tool_name = f"{domain_name.lower().replace('-', '_')}_action"
        server_name = f"{domain_name.capitalize()}Bridge"
        description = f"Servidor MCP autónomo para abstraer el dominio '{domain_name}' bajo alta exergía."

        # Extraer parámetros dinámicamente de las muestras
        params = []
        if sample_calls:
            first_call = sample_calls[0]
            for key, val in first_call.get("args", {}).items():
                p_type = "string"
                if isinstance(val, int):
                    p_type = "integer"
                elif isinstance(val, float):
                    p_type = "number"
                elif isinstance(val, bool):
                    p_type = "boolean"
                elif isinstance(val, dict) or isinstance(val, list):
                    p_type = "object"

                params.append(
                    McpToolParameter(
                        name=key,
                        param_type=p_type,
                        description=f"Parámetro {key} para la herramienta {tool_name}",
                        required=True,
                    )
                )

        if not params:
            # Parámetro por defecto si no se infirieron campos
            params.append(
                McpToolParameter(
                    name="payload",
                    param_type="string",
                    description="Datos de entrada para el dominio",
                    required=True,
                )
            )

        contract = McpCandidateContract(
            server_name=server_name,
            tool_name=tool_name,
            description=description,
            parameters=params,
            estimated_exergy_gain=0.65,
        )
        logger.info(f"[McpDeductiveEngine] Contrato deducido: {contract.server_name}::{contract.tool_name}")
        return contract
