# C5-REAL CENTURIA ARSENAL EXPORT
from .centuria_meta_transducer import CenturiaMetaTransducer
from .registry import execute_primitive, get_all_primitives, get_primitive, list_primitives_by_domain

__all__ = [
    "get_primitive",
    "list_primitives_by_domain",
    "execute_primitive",
    "get_all_primitives",
    "CenturiaMetaTransducer",
]
