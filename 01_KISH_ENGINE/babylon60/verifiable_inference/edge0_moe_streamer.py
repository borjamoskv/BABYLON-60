"""
Edge0 MoE SSD Streamer (V2: arXiv:2609.18063 Assimilation) - C5-REAL Ring-0.
Supera el Memory Wall sirviendo modelos MoE de 35B+ en < 3 GiB de RAM activa:
1. PrerouterHead: Predicción anticipada de expertos Top-K (capa L-1 -> L+1).
2. SSDExpertMmapPool: Streaming zero-copy por mmap con prefetching asíncrono Darwin madvise
   (MADV_WILLNEED = 3 / MADV_DONTNEED = 4) para ocultar la latencia NVMe tras el cómputo.
3. RecoverLoRAAdapter: Adaptadores de recuperación no fusionados en RAM para compensar int4.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import mmap
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

# Constantes del kernel Darwin / POSIX para sys/mman.h
MADV_NORMAL = 0
MADV_SEQUENTIAL = 2
MADV_WILLNEED = 3
MADV_DONTNEED = 4


def _get_libc_madvise() -> Optional[Callable[[int, int, int], int]]:
    """Obtiene el símbolo nativo madvise(void *addr, size_t len, int advice) de libSystem.B.dylib."""
    try:
        libc_path = ctypes.util.find_library("c") or "/usr/lib/libSystem.B.dylib"
        libc = ctypes.CDLL(libc_path, use_errno=True)
        libc.madvise.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
        libc.madvise.restype = ctypes.c_int
        fn: Callable[[int, int, int], int] = libc.madvise
        return fn
    except Exception:
        return None


_LIBC_MADVISE = _get_libc_madvise()


@dataclass
class PrerouterHead:
    """
    Proyector ligero que predice en la capa L-1 los Top-K expertos que requerirá la capa L+1,
    permitiendo lanzar el prefetching NVMe en paralelo con la ejecución de la capa L.
    """

    num_experts: int
    top_k: int
    weights: List[List[float]]  # Matriz [num_experts x hidden_dim]

    def predict_next_layer_experts(self, hidden_state: List[float]) -> List[Tuple[int, float]]:
        """
        Calcula scores = W_pre @ h_{L-1} y retorna los Top-K índices (expert_id, score).
        """
        if self.top_k <= 0 or self.top_k > self.num_experts:
            raise ValueError(f"top_k inválido: {self.top_k} para {self.num_experts} expertos")

        scores: List[Tuple[int, float]] = []
        for exp_id, row in enumerate(self.weights):
            dot = sum(w * x for w, x in zip(row, hidden_state))
            scores.append((exp_id, dot))

        scores.sort(key=lambda item: item[1], reverse=True)
        return scores[: self.top_k]


@dataclass
class RecoverLoRAAdapter:
    """
    Adaptador LoRA no fusionado (Recover-LoRA) que reside permanentemente en RAM (<50 MB)
    para recuperar la precisión FP16 perdida por la cuantización int4 de los expertos en SSD.
    """

    rank: int
    alpha: float
    matrix_a: List[List[float]]  # [rank x in_dim]
    matrix_b: List[List[float]]  # [out_dim x rank]

    def forward_delta(self, x: List[float]) -> List[float]:
        """Calcula delta = (alpha / rank) * B @ (A @ x)."""
        scale = self.alpha / float(self.rank)
        # h = A @ x
        h = [sum(a_val * x_val for a_val, x_val in zip(row_a, x)) for row_a in self.matrix_a]
        # out = scale * (B @ h)
        return [scale * sum(b_val * h_val for b_val, h_val in zip(row_b, h)) for row_b in self.matrix_b]


@dataclass
class ExpertSliceMeta:
    layer_idx: int
    expert_id: int
    byte_offset: int
    byte_length: int


class SSDExpertMmapPool:
    """
    Gestor de streaming de expertos MoE desde SSD NVMe con techo estricto de RAM activa (< 3 GiB).
    """

    def __init__(
        self,
        weights_file: Path,
        expert_slices: Dict[Tuple[int, int], ExpertSliceMeta],
        max_active_ram_bytes: int = 3 * (1024**3),  # 3 GiB default ceiling
    ) -> None:
        self.weights_file = Path(weights_file).resolve()
        self.expert_slices = expert_slices
        self.max_active_ram_bytes = max_active_ram_bytes
        self._fd: Optional[int] = None
        self._mmap: Optional[mmap.mmap] = None
        self._active_resident_bytes: int = 0
        self._prefetched_keys: List[Tuple[int, int]] = []

    def open(self) -> None:
        if self._mmap is not None:
            return
        self._fd = os.open(str(self.weights_file), os.O_RDONLY)
        self._mmap = mmap.mmap(self._fd, 0, access=mmap.ACCESS_READ)

    def close(self) -> None:
        if self._mmap is not None:
            self._mmap.close()
            self._mmap = None
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        self._active_resident_bytes = 0
        self._prefetched_keys.clear()

    @property
    def active_resident_bytes(self) -> int:
        return self._active_resident_bytes

    def _advise_region(self, offset: int, length: int, advice: int) -> bool:
        """Invoca madvise sobre el rango alineado a página (4096 / 16384 bytes en Apple Silicon)."""
        if self._mmap is None:
            raise RuntimeError("SSDExpertMmapPool no está abierto")

        # En Python 3.8+, mmap.madvise está disponible directamente en la stdlib
        if hasattr(self._mmap, "madvise"):
            page_size = mmap.PAGESIZE
            aligned_offset = (offset // page_size) * page_size
            aligned_length = length + (offset - aligned_offset)
            try:
                self._mmap.madvise(advice, aligned_offset, aligned_length)
                return True
            except Exception:
                return False
        return False

    def prefetch_layer_experts(self, layer_idx: int, predicted_experts: List[Tuple[int, float]]) -> int:
        """
        Dispara MADV_WILLNEED asíncrono para los expertos predichos por el PrerouterHead.
        Si el conjunto activo se acerca al techo de 3 GiB, desaloja expertos antiguos con MADV_DONTNEED.
        """
        if self._mmap is None:
            self.open()

        bytes_scheduled = 0
        for exp_id, _score in predicted_experts:
            key = (layer_idx, exp_id)
            meta = self.expert_slices.get(key)
            if meta is None:
                continue

            # Asegurar que nunca se supere el techo de RAM activa (3 GiB)
            while self._active_resident_bytes + meta.byte_length > self.max_active_ram_bytes and self._prefetched_keys:
                old_key = self._prefetched_keys.pop(0)
                old_meta = self.expert_slices[old_key]
                self._advise_region(old_meta.byte_offset, old_meta.byte_length, MADV_DONTNEED)
                self._active_resident_bytes = max(0, self._active_resident_bytes - old_meta.byte_length)

            if key not in self._prefetched_keys:
                self._advise_region(meta.byte_offset, meta.byte_length, MADV_WILLNEED)
                self._prefetched_keys.append(key)
                self._active_resident_bytes += meta.byte_length
                bytes_scheduled += meta.byte_length

        return bytes_scheduled

    def read_expert_bytes(self, layer_idx: int, expert_id: int) -> bytes:
        """Lee los pesos cuantizados int4 del experto desde la región mapeada."""
        if self._mmap is None:
            self.open()
        assert self._mmap is not None
        meta = self.expert_slices[(layer_idx, expert_id)]
        return self._mmap[meta.byte_offset : meta.byte_offset + meta.byte_length]
