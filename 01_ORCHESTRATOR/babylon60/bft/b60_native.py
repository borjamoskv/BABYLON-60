# =============================================================================
# BABYLON-60 C5-REAL: B60 NATIVE FFI BRIDGE (PYTHON <-> RUST SILICON CORE)
# Framework: C5-REAL | Teorema 14: Isomorfismo Semántico C-ABI
# =============================================================================

import ctypes
import math
import os
from pathlib import Path
from typing import List, Optional, Tuple

_LIB_CACHE = None


def _find_b60_dylib() -> Optional[Path]:
    """Busca la librería compartida libb60_lang (.dylib / .so) en el workspace."""
    base_dir = Path(__file__).resolve().parents[3]
    candidate_paths = [
        base_dir / "target" / "release" / "libb60_lang.dylib",
        base_dir / "target" / "debug" / "libb60_lang.dylib",
        base_dir / "target" / "release" / "libb60_lang.so",
        base_dir / "target" / "debug" / "libb60_lang.so",
        Path("/usr/local/lib/libb60_lang.dylib"),
    ]
    for p in candidate_paths:
        if p.exists():
            return p
    return None


def get_b60_dylib() -> Optional[ctypes.CDLL]:
    """Carga y retorna el handle ctypes a libb60_lang con memoización."""
    global _LIB_CACHE
    if _LIB_CACHE is not None:
        return _LIB_CACHE

    lib_path = _find_b60_dylib()
    if not lib_path:
        return None

    try:
        cdll = ctypes.CDLL(str(lib_path))
        # Configuración de tipos C-ABI
        cdll.b60_version.restype = ctypes.c_char_p
        cdll.b60_version.argtypes = []

        cdll.b60_sexa_add.restype = ctypes.c_int32
        cdll.b60_sexa_add.argtypes = [
            ctypes.c_uint64,
            ctypes.c_uint64,
            ctypes.c_uint64,
            ctypes.c_uint64,
            ctypes.POINTER(ctypes.c_uint64),
            ctypes.POINTER(ctypes.c_uint64),
        ]

        cdll.b60_fisher_distance.restype = ctypes.c_double
        cdll.b60_fisher_distance.argtypes = [
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_double),
            ctypes.POINTER(ctypes.c_double),
        ]

        cdll.b60_kullback_leibler.restype = ctypes.c_double
        cdll.b60_kullback_leibler.argtypes = [
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_double),
            ctypes.POINTER(ctypes.c_double),
        ]

        cdll.b60_eval_agent_intent.restype = ctypes.c_int32
        cdll.b60_eval_agent_intent.argtypes = [
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_size_t,
            ctypes.c_size_t,
            ctypes.c_uint64,
            ctypes.c_char_p,
            ctypes.c_size_t,
        ]

        cdll.b60_dag_validate.restype = ctypes.c_int32
        cdll.b60_dag_validate.argtypes = [
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint64),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_size_t),
        ]

        _LIB_CACHE = cdll
        return _LIB_CACHE
    except Exception:
        return None


class B60NativeBridge:
    """
    Pasarela de alta exergía para invocar el silicio bare-metal de B60 desde Python.
    Provee aceleración nativa y degradación elegante a puro Python.
    """

    @classmethod
    def is_available(cls) -> bool:
        return get_b60_dylib() is not None

    @classmethod
    def version(cls) -> str:
        lib = get_b60_dylib()
        if lib:
            raw = lib.b60_version()
            return raw.decode("utf-8") if raw else "unknown"
        return "1.0.0-pyfallback"

    @classmethod
    def sexa_add(cls, s1: int, f1: int, s2: int, f2: int) -> Tuple[int, int]:
        """Suma sexagesimal exacta en base 60^4 (12,960,000)."""
        lib = get_b60_dylib()
        if lib:
            out_s = ctypes.c_uint64()
            out_f = ctypes.c_uint64()
            res = lib.b60_sexa_add(s1, f1, s2, f2, ctypes.byref(out_s), ctypes.byref(out_f))
            if res == 0:
                return out_s.value, out_f.value

        # Pure Python fallback
        base = 12960000
        tot = f1 + f2
        return (s1 + s2 + (tot // base)), (tot % base)

    @classmethod
    def fisher_distance(cls, p: List[float], q: List[float]) -> float:
        """Calcula la distancia de Fisher-Rao en nanosegundos vía silicio nativo."""
        assert len(p) == len(q) and len(p) > 0
        lib = get_b60_dylib()
        if lib:
            arr_type = ctypes.c_double * len(p)
            c_p = arr_type(*p)
            c_q = arr_type(*q)
            dist = lib.b60_fisher_distance(len(p), c_p, c_q)
            if dist >= 0.0:
                return dist

        # Pure Python fallback
        bc = sum(math.sqrt(pi * qi) for pi, qi in zip(p, q))
        bc = max(0.0, min(1.0, bc))
        return 2.0 * math.acos(bc)

    @classmethod
    def kullback_leibler(cls, p: List[float], q: List[float]) -> float:
        """Calcula la divergencia de Kullback-Leibler nativa."""
        assert len(p) == len(q) and len(p) > 0
        lib = get_b60_dylib()
        if lib:
            arr_type = ctypes.c_double * len(p)
            c_p = arr_type(*p)
            c_q = arr_type(*q)
            kl = lib.b60_kullback_leibler(len(p), c_p, c_q)
            if kl >= 0.0:
                return kl

        # Pure Python fallback
        d_kl = 0.0
        for pi, qi in zip(p, q):
            if pi > 1e-12:
                d_kl += pi * math.log(pi / max(1e-12, qi))
        return d_kl

    @classmethod
    def eval_agent_intent(
        cls,
        agent_id: str,
        tool_name: str,
        reasoning_len: int,
        payload_len: int,
        budget: int,
    ) -> Tuple[int, str]:
        """
        Evalúa una intención agéntica bajo la compuerta epistémica Ring-0.
        Retorna: (veredicto, mmr_root_hex)
          veredicto 0 = Admitido
          veredicto 2 = Rechazado (Cheap Talk)
          veredicto 3 = Rechazado (Presupuesto)
        """
        lib = get_b60_dylib()
        if lib:
            buf = ctypes.create_string_buffer(128)
            ret = lib.b60_eval_agent_intent(
                agent_id.encode("utf-8"),
                tool_name.encode("utf-8"),
                reasoning_len,
                payload_len,
                budget,
                buf,
                len(buf),
            )
            root_hex = buf.value.decode("utf-8") if ret == 0 else ""
            return ret, root_hex

        # Pure Python fallback
        if budget > 3600:
            return 3, ""
        eff = 1 if payload_len == 0 else payload_len
        if reasoning_len > 100 and (reasoning_len // eff) > 50:
            return 2, ""
        return 0, "fallback_root_hash"

    @classmethod
    def validate_causal_dag(
        cls,
        nodes: List[Tuple[int, int]],  # (id, lamport_ts)
        edges: List[Tuple[int, int]],  # (from_id, to_id)
    ) -> Tuple[int, int]:
        """
        Valida y compila un grafo acíclico dirigido (DAG) en silicio.
        Retorna: (código_resultado, num_etapas_paralelas)
          0 = Válido
          1 = Paradoja Cíclica
          2 = Inversión Temporal de Lamport
        """
        lib = get_b60_dylib()
        if lib and nodes:
            n_nodes = len(nodes)
            node_ids_type = ctypes.c_uint32 * n_nodes
            ts_type = ctypes.c_uint64 * n_nodes

            c_node_ids = node_ids_type(*[n[0] for n in nodes])
            c_ts = ts_type(*[n[1] for n in nodes])

            n_edges = len(edges)
            if n_edges > 0:
                edge_type = ctypes.c_uint32 * n_edges
                c_edge_from = edge_type(*[e[0] for e in edges])
                c_edge_to = edge_type(*[e[1] for e in edges])
            else:
                c_edge_from = None
                c_edge_to = None

            out_stages = ctypes.c_size_t(0)
            res = lib.b60_dag_validate(
                n_nodes,
                c_node_ids,
                c_ts,
                n_edges,
                c_edge_from,
                c_edge_to,
                ctypes.byref(out_stages),
            )
            return res, out_stages.value

        # Pure Python fallback
        ts_map = {nid: ts for nid, ts in nodes}
        for u, v in edges:
            if ts_map.get(u, 0) >= ts_map.get(v, 0):
                return 2, 0
        return 0, 1

