# [C5-REAL] Optional dependencies compatibility module
try:
    import numpy as np
except ImportError:
    np = None  # type: ignore[assignment]

__all__ = ["np"]
