# [C5-REAL] Exergy-Maximized
import logging
import uuid
from collections.abc import AsyncGenerator, Callable
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

try:
    from langgraph.graph import StateGraph
    LANGGRAPH_AVAILABLE = True
except ImportError:
    StateGraph = Any
    LANGGRAPH_AVAILABLE = False

logger = logging.getLogger("babylon60_extensions.swarm.supervisor")


class NightShiftState(BaseModel):
    """Estado persistente para ejecución duradera (Agent State)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    messages: list[dict[str, Any]] = []
    variables: dict[str, Any] = {}
    next_node: str = "planner"
    retry_count: int = 0
    max_retries: int = 3
    is_paused: bool = False

    @classmethod
    def create(cls, session_id: Optional[str] = None) -> "NightShiftState":
        return cls(session_id=session_id or str(uuid.uuid4()))


class SupervisorNode:
    """Clase base para Nodos de LangGraph."""

    def __init__(self, name: str) -> None:
        self.name = name

    async def execute(self, state: NightShiftState) -> NightShiftState:
        """La mutación del estado O(1)."""
        raise NotImplementedError


class LangGraphSupervisorError(Exception):
    pass


class CortexLangGraphSupervisor:
    """
    Supervisor O(1) de LangGraph adaptado para CORTEX persistency.
    Implementa el paradigma "Night Shift": Durable Execution & Human-in-the-Loop.
    Aplica Ω27 (SUBAGENT RATE-LIMIT FALLBACK INVARIANT).
    """

    def __init__(self, name: str = "cortex-swarm-supervisor") -> None:
        if not LANGGRAPH_AVAILABLE:
            raise LangGraphSupervisorError(
                "LangGraph no está instalado. Ejecute 'pip install langgraph'."
            )

        self.name = name
        self.nodes: dict[str, SupervisorNode] = {}
        self.graph_builder: Any = StateGraph(NightShiftState)
        self.compiled_app: Any = None

    def add_node(self, node: SupervisorNode) -> None:
        """Añade un nodo al grafo."""
        self.nodes[node.name] = node

        async def node_wrapper(state: NightShiftState) -> NightShiftState:
            logger.info("🔄 [SUPERVISOR] Ejecutando nodo: %s", node.name)
            return await node.execute(state)

        self.graph_builder.add_node(node.name, node_wrapper)

    def add_edge(self, source: str, target: str) -> None:
        """Define una arista incondicional."""
        self.graph_builder.add_edge(source, target)

    def add_conditional_edges(self, source: str, decision_func: Callable[[NightShiftState], str], edge_map: dict[str, str]) -> None:
        """Define bifurcación predictible."""
        self.graph_builder.add_conditional_edges(source, decision_func, edge_map)

    def compile(self, checkpointer: Optional[Any] = None) -> Any:
        """Compila la aplicación en un DAG O(1)."""
        self.compiled_app = self.graph_builder.compile(checkpointer=checkpointer)
        return self.compiled_app

    async def fallback_local_execution(self, state: NightShiftState) -> NightShiftState:
        """
        Ω27 · SUBAGENT RATE-LIMIT FALLBACK INVARIANT
        Ejecución directa sobre la CPU local sin delegar en caso de límite de tasa.
        """
        logger.warning("⚡ [SUPERVISOR] Aplicando Ω27 Fallback Local. Ejecución determinista forzada sobre nodo %s.", state.next_node)
        if state.next_node in self.nodes:
            node = self.nodes[state.next_node]
            return await node.execute(state)
        raise LangGraphSupervisorError(f"Fallback fallido: el nodo {state.next_node} no está registrado en el grafo local.")

    async def stream_execution(
        self, initial_state: NightShiftState
    ) -> AsyncGenerator[NightShiftState, None]:
        """Arranca el enjambre y cede estado por cada tick de progreso."""
        if not self.compiled_app:
            self.compile()

        logger.info("🚀 [SUPERVISOR] Lanzando Night Shift (Session: %s)", initial_state.session_id)
        try:
            async for state_update in self.compiled_app.astream(initial_state):
                yield state_update
        except Exception as e:
            error_msg = str(e).upper()
            if "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg or "RATE LIMIT" in error_msg:
                # Ω27 trigger
                fallback_state = await self.fallback_local_execution(initial_state)
                yield fallback_state
            elif isinstance(e, (ValueError, TypeError, RuntimeError)):
                logger.error("☠️ [SUPERVISOR] Fallo de Ejecución Duradera: %s", e)
                raise LangGraphSupervisorError(f"Colapso en grafo: {e}") from e
            else:
                raise LangGraphSupervisorError(f"Falla crítica desconocida: {e}") from e
