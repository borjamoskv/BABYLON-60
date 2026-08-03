from .lexer import DslParser
from .kernel import SimulationKernel
from .state_graph import UniverseSnapshot

class Movie:
    """API Fluida / Entrypoint para TimelineIR"""
    def __init__(self, source_code: str):
        self.parser = DslParser(source_code)
        self.kernel = self.parser.compile()
        
    def evaluate_at(self, time_sec: float) -> UniverseSnapshot:
        """Devuelve el estado inmutable del universo en el tiempo t."""
        return self.kernel.evaluate_state(time_sec)

__all__ = ["Movie", "UniverseSnapshot"]
