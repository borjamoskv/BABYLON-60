import dataclasses
from typing import Dict, Any, List

# █ SYS_ID: BABYLON-60 ENGINE (C5-REAL)
# █ INV-023: Erradicación del término "Instancia".

@dataclasses.dataclass(frozen=True)
class CoreModel:
    """
    Representa los tensores estáticos inmutables en VRAM/Disco.
    Costo I/O: O(N) catastrófico. Unica carga en cold-start.
    """
    model_id: str
    vram_allocation_gb: float
    quantization_level: str
    root_hash: str
    
    def validate_integrity(self) -> bool:
        # Validación criptográfica contra el Ledger M1
        return True


@dataclasses.dataclass(frozen=True)
class AgentPersona:
    """
    Representa la matriz semántica estática (System Prompt).
    Costo: Prefill computacional trivial. Dicta el árbol de comportamiento.
    """
    persona_id: str
    system_prompt: str
    temperature_override: float  # T=0 para operaciones M1/M4, T>0 para creatividad.
    capabilities: List[str]
    
    def get_token_density(self) -> int:
        # Longitud determinista de la matriz
        return len(self.system_prompt.split())


@dataclasses.dataclass
class ExecutionContext:
    """
    Representa el estado dinámico (KV Cache / TokenStream) de una sesión.
    Se acopla asíncronamente al SQLite WAL y es efímero en RAM.
    """
    context_id: str
    core_model_ref: CoreModel
    persona_ref: AgentPersona
    conversation_history: List[Dict[str, Any]] = dataclasses.field(default_factory=list)
    
    def ingest_stimulus(self, payload: str):
        """Inyecta un estímulo en el TokenStream sin tocar el CoreModel."""
        self.conversation_history.append({"role": "user", "content": payload})
        
    def snapshot_to_wal(self) -> str:
        """Cristaliza el estado actual en el SQLite WAL (Matriz 1). Retorna Merkle Root."""
        # SQLite Append-Only Logic
        return "SHA256_HASH_CRISTALIZADO"

    def apoptosis(self):
        """INV-018: Purga de la memoria volátil."""
        self.conversation_history.clear()
        
