# C5-REAL EXERGY CERTIFIED
# [C5-REAL] Exergy-Maximized
"""
cat_id: c5-agent-config
cat_type: module
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P1
"""

from pathlib import Path
from typing import List, Callable

from google.antigravity import CapabilitiesConfig
from google.antigravity.connections.local import LocalAgentConfig
from google.antigravity.hooks import policy

# Importar los hooks físicos de observabilidad C5-REAL
from babylon60.observability.hooks import (
    track_start,
    track_end,
    track_error,
)

async def c5_bft_handler(tool_call) -> bool:
    print(f"[C5-REAL] Interrupción BFT. El agente intentó mutar estado usando: {tool_call.name}")
    # En un entorno no interactivo, denegamos la mutación por defecto.
    return False

def build_cortex_agent_config(
    model: str = "gemini-2.5-pro",
    system_instructions: str = "Operas bajo el estándar C5-REAL. Máxima entropía purgada.",
    workspaces: List[str] = None
) -> LocalAgentConfig:
    """
    Construye la configuración del agente con las barreras termodinámicas C5-REAL.
    Fallo cerrado por defecto (Deny All) y medición de exergía acoplada.
    """

    c5_policies = [
        policy.deny_all(),
        policy.allow("view_file"),
        policy.allow("list_dir"),
        policy.allow("grep_search"),
        policy.allow("search_web"),
        policy.confirm_run_command(),
        policy.ask_user("write_to_file", handler=c5_bft_handler),
        policy.ask_user("replace_file_content", handler=c5_bft_handler),
        policy.ask_user("multi_replace_file_content", handler=c5_bft_handler)
    ]

    if workspaces:
        c5_policies.insert(0, policy.workspace_only(workspaces))

    return LocalAgentConfig(
        model=model,
        system_instructions=system_instructions,
        workspaces=workspaces,
        capabilities=CapabilitiesConfig(),
        policies=c5_policies,
        hooks=[
            track_start,
            track_end,
            track_error
        ]
    )
