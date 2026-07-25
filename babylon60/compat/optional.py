try:
    import numpy as np
except ImportError:
    np = None  # type: ignore[assignment]
__all__ = ["np"]
