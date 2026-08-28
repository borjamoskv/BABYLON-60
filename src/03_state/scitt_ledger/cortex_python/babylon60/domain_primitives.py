# C5-REAL EXERGY CERTIFIED
from dataclasses import dataclass

# DOMAIN PRIMITIVES (VALUE OBJECTS)
# Purgar Primitive Obsession. Todo estado que fluya por el sistema debe estar tipado y validado en O(1).

@dataclass(frozen=True)
class BFTTransactionHash:
    """
    Primitiva criptográfica inmutable.
    Garantiza que ningún hash malformado corrompa la memoria BFT.
    """
    value: str

    def __post_init__(self):
        if not isinstance(self.value, str):
            raise TypeError("BFTTransactionHash debe ser un string")
        if len(self.value) != 64:
            raise ValueError(f"BFTTransactionHash inválido, entropía incorrecta: {len(self.value)} chars")
        # Enforce hex
        try:
            int(self.value, 16)
        except ValueError:
            raise ValueError("BFTTransactionHash no es hexadecimal")

@dataclass(frozen=True)
class ExergyToken:
    """
    Primitiva termodinámica inmutable.
    Representa un valor de energía purgada, previene propagación de NaN o energía negativa.
    """
    value: float

    def __post_init__(self):
        if not isinstance(self.value, (int, float)):
            raise TypeError("ExergyToken debe ser numérico")
        if self.value < 0.0:
            raise ValueError(f"ExergyToken negativo (anergía detectada): {self.value}")
        import math
        if math.isnan(self.value) or math.isinf(self.value):
            raise ValueError(f"ExergyToken corrupto (NaN/Inf): {self.value}")

@dataclass(frozen=True)
class NodePulse:
    """
    Vector de comunicación O(1) entre nodos.
    """
    source_id: str
    target_id: str
    energy: ExergyToken

    def __post_init__(self):
        if not self.source_id or not self.target_id:
            raise ValueError("NodePulse requiere IDs válidos (no vacíos)")
