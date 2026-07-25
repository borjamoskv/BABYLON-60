"""
C5-REAL Native Commands (Slash Commands) Module.
Vector: INV_C5_17 / INV_C5_21 / INV_C5_20 / INV_C5_16 / INV_BRIDGE_01
"""

from .autodidact import run_autodidact
from .ethos import run_ethos
from .itera import run_itera
from .logos import run_logos
from .mythos import run_mythos
from .purge import run_purge
from .seal import run_seal
from .ship import run_ship
from .swarm import run_swarm
from .ultrathink import run_ultrathink
from .verify import run_verify

__all__ = [
    "run_ultrathink", "run_autodidact", "run_purge", "run_seal", "run_itera",
    "run_logos", "run_ethos", "run_mythos", "run_ship", "run_swarm", "run_verify"
]
