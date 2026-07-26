# C5-REAL EXERGY CERTIFIED
"""Pruebas unitarias para GeminiProPoolManager (C5-REAL)."""

import os
import unittest
from unittest.mock import patch
from scripts.gemini_pool_manager import (
    GeminiProPoolManager,
)

class TestGeminiProPoolManager(unittest.TestCase):
    def setUp(self) -> None:
        self.env_patcher = patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": "key_primary",
                "GEMINI_API_KEY_01": "key_01",
                "GEMINI_API_KEY_02": "key_02",
                "GEMINI_API_KEY_03": "key_03",
            },
            clear=False,
        )
        self.env_patcher.start()

    def tearDown(self) -> None:
        self.env_patcher.stop()

    def test_load_slots_from_env(self) -> None:
        manager = GeminiProPoolManager()
        self.assertGreaterEqual(len(manager.slots), 4)
        keys = [s.api_key for s in manager.slots]
        self.assertIn("key_primary", keys)
        self.assertIn("key_01", keys)
        self.assertIn("key_02", keys)

    def test_round_robin_dispatch(self) -> None:
        manager = GeminiProPoolManager()
        slot1 = manager.get_next_available_slot()
        slot2 = manager.get_next_available_slot()
        self.assertNotEqual(slot1.slot_id, slot2.slot_id)

    def test_cooldown_skips_saturated_slot(self) -> None:
        manager = GeminiProPoolManager()
        slot1 = manager.slots[0]
        slot1.set_cooldown(3600.0)  # Enfriar 1 hora

        selected_slot = manager.get_next_available_slot()
        self.assertNotEqual(selected_slot.slot_id, slot1.slot_id)
        self.assertTrue(selected_slot.is_available)

    def test_get_pool_stats(self) -> None:
        manager = GeminiProPoolManager()
        stats = manager.get_pool_stats()
        self.assertIn("total_slots", stats)
        self.assertIn("available_slots", stats)
        self.assertEqual(stats["total_slots"], len(manager.slots))

    def test_async_dispatch_coroutine(self) -> None:
        import asyncio

        manager = GeminiProPoolManager()
        with patch.object(manager, "dispatch_generate_content", return_value="async_mock_response"):
            res = asyncio.run(manager.adispatch_generate_content("test prompt", "gemini-1.5-pro"))
            self.assertEqual(res, "async_mock_response")

if __name__ == "__main__":
    unittest.main()
