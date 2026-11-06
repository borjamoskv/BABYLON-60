#!/usr/bin/env python3
"""
Batería de Pruebas de Asimilación de Frontera C5-REAL (Vectores V1, V2, V3).
Verifica en silicio:
- V1: TokenLease & Cost Circuit Breaker Guard (paperclip/skills assimilation).
- V2: Edge0 MoE SSD Streamer (PrerouterHead + mmap madvise + Recover-LoRA).
- V3: CatVTON Spatial Latent Concatenation Transducer (< 8 GiB VRAM).
"""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "01_KISH_ENGINE"))

from babylon60.guards.token_lease_guard import (  # noqa: E402
    SwarmLeaseRegistry,
    TokenLeaseViolationError,
)
from babylon60.verifiable_inference.edge0_moe_streamer import (  # noqa: E402
    ExpertSliceMeta,
    PrerouterHead,
    RecoverLoRAAdapter,
    SSDExpertMmapPool,
)
from babylon60.transducers.catvton_spatial_concat import (  # noqa: E402
    CatVTONSpatialTransducer,
)


class TestV1V2V3FrontierAssimilation(unittest.TestCase):
    def test_v1_token_lease_argon_weighting_and_circuit_breaker(self) -> None:
        """Verifica el descuento 95% de caché implícito, peso 5x de salida y disyuntor."""
        registry = SwarmLeaseRegistry()
        lease = registry.issue_lease(
            agent_id="sharur_worker_01",
            role="ejecutor",
            max_effective_units=10_000.0,
            max_unverified_steps=2,
        )

        # Turno 1: 10.000 input (9.000 cacheados) + 200 output
        # Coste = 1000*1.0 + 9000*0.05 + 200*5.0 = 1000 + 450 + 1000 = 2450 unidades
        step = lease.record_step(
            input_tokens=10_000,
            cached_tokens=9_000,
            output_tokens=200,
            verified_outcome=True,
        )
        self.assertAlmostEqual(step.effective_cost_units, 2450.0)
        self.assertAlmostEqual(lease.remaining_units, 7550.0)

        # Disparar disyuntor por pasos consecutivos no verificados (> 2)
        lease.record_step(100, 10, verified_outcome=False)
        lease.record_step(100, 10, verified_outcome=False)
        with self.assertRaises(TokenLeaseViolationError):
            lease.record_step(100, 10, verified_outcome=False)

        self.assertTrue(lease.tripped)
        self.assertEqual(len(lease.seal_receipt_sha256()), 64)

    def test_v2_edge0_prerouter_and_ssd_mmap_pool(self) -> None:
        """Verifica la predicción Top-K de expertos y el streaming acotado por mmap."""
        prerouter = PrerouterHead(
            num_experts=4,
            top_k=2,
            weights=[
                [0.1, 0.2, 0.1],  # Exp 0
                [0.9, 0.8, 0.7],  # Exp 1 (Top 1)
                [-0.5, 0.0, 0.1],  # Exp 2
                [0.5, 0.6, 0.4],  # Exp 3 (Top 2)
            ],
        )
        top_experts = prerouter.predict_next_layer_experts([1.0, 1.0, 1.0])
        self.assertEqual([idx for idx, _ in top_experts], [1, 3])

        # Crear archivo temporal simulando expertos en SSD (4 páginas de 4096 bytes)
        with tempfile.NamedTemporaryFile() as tmp:
            for exp_id in range(4):
                tmp.write(bytes([exp_id + 1]) * 4096)
            tmp.flush()

            slices = {
                (0, exp_id): ExpertSliceMeta(
                    layer_idx=0,
                    expert_id=exp_id,
                    byte_offset=exp_id * 4096,
                    byte_length=4096,
                )
                for exp_id in range(4)
            }
            # Techo estricto de 8192 bytes (máximo 2 expertos residentes en RAM)
            pool = SSDExpertMmapPool(
                weights_file=Path(tmp.name),
                expert_slices=slices,
                max_active_ram_bytes=8192,
            )
            try:
                scheduled = pool.prefetch_layer_experts(0, top_experts)
                self.assertEqual(scheduled, 8192)
                self.assertLessEqual(pool.active_resident_bytes, 8192)

                # Leer pesos del experto 1 y verificar contenido
                exp1_data = pool.read_expert_bytes(0, 1)
                self.assertEqual(len(exp1_data), 4096)
                self.assertEqual(exp1_data[0], 2)

                # Prefetch de otros expertos desaloja los antiguos sin superar el techo de 8192 bytes
                pool.prefetch_layer_experts(0, [(0, 1.0), (2, 0.9)])
                self.assertLessEqual(pool.active_resident_bytes, 8192)
            finally:
                pool.close()

    def test_v2_recover_lora_adapter(self) -> None:
        """Verifica el cálculo del delta de recuperación LoRA no fusionado en RAM."""
        lora = RecoverLoRAAdapter(
            rank=2,
            alpha=4.0,
            matrix_a=[[1.0, 0.0], [0.0, 1.0]],
            matrix_b=[[2.0, 3.0], [1.0, -1.0]],
        )
        delta = lora.forward_delta([1.0, 2.0])
        # h = [1.0, 2.0], B @ h = [8.0, -1.0], scale = 4/2 = 2.0 -> [16.0, -2.0]
        self.assertEqual(delta, [16.0, -2.0])

    def test_v3_catvton_spatial_concatenation_and_vram_guard(self) -> None:
        """Verifica la concatenación espacial latente (W -> 2W), enmascarado y split."""
        transducer = CatVTONSpatialTransducer()
        vram_mib = transducer.estimate_memory_mib(1024, 768)
        self.assertLess(vram_mib, 8192.0)

        # Latentes [C=1, H=2, W=2]
        person = [[[10.0, 20.0], [30.0, 40.0]]]
        garment = [[[1.0, 2.0], [3.0, 4.0]]]
        mask = [[1, 0], [0, 1]]  # Enmascarar (0,0) y (1,1)

        z_concat, m_concat = transducer.build_concat_input(person, garment, mask)
        self.assertEqual(transducer.get_shape_3d(z_concat), (1, 2, 4))
        self.assertEqual(z_concat[0][0], [0.0, 20.0, 1.0, 2.0])
        self.assertEqual(z_concat[0][1], [30.0, 0.0, 3.0, 4.0])
        self.assertEqual(m_concat, [[1, 0, 0, 0], [0, 1, 0, 0]])

        person_out = transducer.split_person_output(z_concat)
        self.assertEqual(transducer.get_shape_3d(person_out), (1, 2, 2))
        self.assertEqual(person_out[0][0], [0.0, 20.0])


if __name__ == "__main__":
    unittest.main()
