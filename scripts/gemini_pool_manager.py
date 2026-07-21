#!/usr/bin/env python3
"""
CORTEX Multi-Account Gemini Pro Pool Engine (C5-REAL).
Orchestrates >10 Gemini PRO/Flash API accounts with round-robin load balancing,
cooling map for 429 Rate Limits, and zero static fallbacks (Ω25, Ω26, Ω27).
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from typing import List, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


class EpistemicPoolHalt(Exception):
    """Exclusión rígida de excepciones mudas (Ω26)."""

    pass


class GeminiAccountSlot:
    """Representa una cuenta física de Gemini Pro/Flash aislada."""

    def __init__(self, slot_id: int, api_key: str) -> None:
        self.slot_id = slot_id
        self.api_key = api_key
        self.cooldown_until: float = 0.0
        self.requests_count: int = 0
        self.errors_count: int = 0

    @property
    def is_available(self) -> bool:
        return time.time() >= self.cooldown_until

    def set_cooldown(self, seconds: float = 60.0) -> None:
        self.cooldown_until = time.time() + seconds
        self.errors_count += 1


class GeminiProPoolManager:
    """Manejador de Pool Multi-Cuenta para Gemini Pro/Flash (C5-REAL)."""

    def __init__(self, env_prefix: str = "GEMINI_API_KEY") -> None:
        self.slots: List[GeminiAccountSlot] = []
        self._current_index: int = 0
        self._load_keys(env_prefix)

    def _load_keys(self, env_prefix: str) -> None:
        # Cargar clave primaria
        primary_key = os.environ.get(env_prefix)
        if primary_key:
            self.slots.append(GeminiAccountSlot(0, primary_key))

        # Cargar llaves numeradas GEMINI_API_KEY_01 ... GEMINI_API_KEY_99 o GEMINI_PRO_KEY_*
        prefixes = [env_prefix, "GEMINI_PRO_KEY"]
        for pfx in prefixes:
            for i in range(1, 100):
                key_var = f"{pfx}_{i:02d}"
                key_val = os.environ.get(key_var) or os.environ.get(f"{pfx}_{i}")
                if key_val and not any(s.api_key == key_val for s in self.slots):
                    self.slots.append(GeminiAccountSlot(len(self.slots), key_val))

    def get_next_available_slot(self) -> GeminiAccountSlot:
        """Retorna el siguiente slot libre respetando round-robin y cooldowns."""
        if not self.slots:
            raise EpistemicPoolHalt(
                "No hay llaves de API de Gemini configuradas en el entorno (Ω25)."
            )

        total_slots = len(self.slots)
        for _ in range(total_slots):
            slot = self.slots[self._current_index]
            self._current_index = (self._current_index + 1) % total_slots
            if slot.is_available:
                return slot

        raise EpistemicPoolHalt(
            "Todas las cuentas de Gemini Pro están saturadas en Cooldown (429 Rate Limit)."
        )

    def dispatch_generate_content(
        self, prompt: str, model: str = "gemini-1.5-pro"
    ) -> str:
        """Dispara una inferencia rotando entre las cuentas disponibles."""
        attempts = 0
        max_attempts = len(self.slots) if self.slots else 1

        last_error: Optional[Exception] = None

        while attempts < max_attempts:
            slot = self.get_next_available_slot()
            slot.requests_count += 1
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={slot.api_key}"

            payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode(
                "utf-8"
            )

            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            try:
                with urllib.request.urlopen(req, timeout=12) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts:
                            return str(parts[0].get("text", ""))
                    return ""
            except urllib.error.HTTPError as e:
                if e.code == 429 or e.code == 503:
                    # Enfriar esta cuenta por 60s
                    slot.set_cooldown(60.0)
                    last_error = e
                    attempts += 1
                    continue
                else:
                    raise EpistemicPoolHalt(
                        f"HTTPError Gemini API [{e.code}]: {e.reason}"
                    )
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                slot.set_cooldown(15.0)
                last_error = e
                attempts += 1
                continue

        raise EpistemicPoolHalt(
            f"Agotadas todas las cuentas ({max_attempts}) del pool Gemini Pro. Error: {last_error}"
        )


if __name__ == "__main__":
    print("Gemini Pro Multi-Account Pool Manager (C5-REAL) cargado.")
    manager = GeminiProPoolManager()
    print(f"Cuentas activas en pool: {len(manager.slots)}")
