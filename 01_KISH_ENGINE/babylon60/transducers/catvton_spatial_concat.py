"""
CatVTON Spatial Latent Concatenation Transducer (V3: ICLR CatVTON Assimilation) - C5-REAL.
Implementa la Vía Negativa en transferencia visual / Virtual Try-On:
Elimina ReferenceNet, DINOv2 y módulos de warping geométrico concatenando espacialmente
el latente de persona Z_p y el latente de prenda Z_g en el eje de anchura (W -> 2W),
con un presupuesto de memoria estricto < 8 GiB.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


# 3D Tensor ligero [C][H][W] en stdlib pura para contratos sin dependencia obligatoria de PyTorch
LatentTensor3D = List[List[List[float]]]
MaskTensor2D = List[List[int]]


@dataclass(frozen=True)
class CatVTONConfig:
    latent_channels: int = 4
    vae_downscale_factor: int = 8
    trainable_params_millions: float = 49.57
    total_params_millions: float = 899.00
    max_vram_budget_mib: int = 8192  # Techo < 8 GiB VRAM


class CatVTONSpatialTransducer:
    """
    Transductor de concatenación espacial latente (Z_input = Concat_W(Z_p * (1 - M), Z_g)).
    """

    def __init__(self, config: CatVTONConfig = CatVTONConfig()) -> None:
        self.config = config

    @staticmethod
    def get_shape_3d(tensor: LatentTensor3D) -> Tuple[int, int, int]:
        c = len(tensor)
        h = len(tensor[0]) if c > 0 else 0
        w = len(tensor[0][0]) if h > 0 else 0
        return (c, h, w)

    def estimate_memory_mib(self, height_px: int, width_px: int, batch_size: int = 1) -> float:
        """
        Estima la huella de VRAM en MiB para el backbone despojado de ReferenceNet (899M params FP16)
        más activaciones de autoatención sobre el latente doble (H/8 x 2W/8).
        """
        weights_mib = (self.config.total_params_millions * 1e6 * 2.0) / (1024.0 * 1024.0)
        h_lat = height_px // self.config.vae_downscale_factor
        w_lat_concat = (width_px * 2) // self.config.vae_downscale_factor
        tokens = h_lat * w_lat_concat
        # Activación autoatención FP16 acotada
        activation_mib = (batch_size * tokens * 64 * 2.0) / (1024.0 * 1024.0)
        total_mib = weights_mib + activation_mib
        if total_mib > self.config.max_vram_budget_mib:
            raise MemoryError(
                f"[FAIL-CLOSED] Resolución {width_px}x{height_px} excede presupuesto CatVTON "
                f"({total_mib:.1f} MiB > {self.config.max_vram_budget_mib} MiB)"
            )
        return round(total_mib, 2)

    def build_concat_input(
        self,
        person_latent: LatentTensor3D,
        garment_latent: LatentTensor3D,
        inpaint_mask: MaskTensor2D,
    ) -> Tuple[LatentTensor3D, MaskTensor2D]:
        """
        Aplica la máscara de inpainting sobre person_latent y concatena garment_latent en el eje W:
        Z_concat[c, y, x] = [Z_p * (1 - M) || Z_g] de dimensión (C, H_L, 2 * W_L).
        M_concat[y, x]    = [M             || 0  ] de dimensión (H_L, 2 * W_L).
        """
        shape_p = self.get_shape_3d(person_latent)
        shape_g = self.get_shape_3d(garment_latent)
        if shape_p != shape_g:
            raise ValueError(f"Dimensiones latentes incompatibles: {shape_p} vs {shape_g}")

        c, h, w = shape_p
        if len(inpaint_mask) != h or (h > 0 and len(inpaint_mask[0]) != w):
            raise ValueError("La máscara 2D no coincide con (H_L, W_L) del latente")

        z_concat: LatentTensor3D = []
        for ch_idx in range(c):
            channel_rows: List[List[float]] = []
            for y in range(h):
                masked_person_row = [
                    person_latent[ch_idx][y][x] * (0.0 if inpaint_mask[y][x] else 1.0) for x in range(w)
                ]
                garment_row = list(garment_latent[ch_idx][y])
                channel_rows.append(masked_person_row + garment_row)
            z_concat.append(channel_rows)

        m_concat: MaskTensor2D = [list(inpaint_mask[y]) + ([0] * w) for y in range(h)]

        return z_concat, m_concat

    def split_person_output(self, denoised_concat: LatentTensor3D) -> LatentTensor3D:
        """
        Extrae la mitad izquierda correspondiente a la persona renderizada (C, H_L, W_L)
        descartando la mitad derecha de condicionamiento de prenda.
        """
        c, h, w_double = self.get_shape_3d(denoised_concat)
        if w_double % 2 != 0:
            raise ValueError(f"El ancho concatenado debe ser par, recibido: {w_double}")
        w = w_double // 2
        return [[row[:w] for row in denoised_concat[ch_idx]] for ch_idx in range(c)]
