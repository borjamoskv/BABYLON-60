#!/usr/bin/env python3
"""
Gemini Pro Multi‑Account Pool Manager with Telemetry (C5‑REAL)

- Adds in‑memory counters for total requests, per‑account usage, successes and failures.
- Records execution latency using `time.perf_counter()`.
- Provides `GeminiProTelemetry` singleton with `record` and `snapshot` methods.
- Integration is passive; the manager calls `GeminiProTelemetry.record` on each dispatch.
- Orchestrates >10 Gemini PRO/Flash API accounts with round-robin load balancing,
  cooling map for 429 Rate Limits, and zero static fallbacks (Ω25, Ω26, Ω27).
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from typing import List, Optional, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


class EpistemicPoolHalt(Exception):
    """Exclusión rígida de excepciones mudas (Ω26)."""

    pass


class GeminiProTelemetry:
    """Simple in‑memory telemetry singleton for the Gemini pool.

    Tracks total requests, successes, failures and per‑key usage counts.
    """

    _instance = None

    def __init__(self):
        self.total_requests = 0
        self.successes = 0
        self.failures = 0
        self.latency_sum = 0.0
        self.per_key_counts = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record(self, key: str, success: bool, latency: float):
        self.total_requests += 1
        self.latency_sum += latency
        self.per_key_counts.setdefault(key, 0)
        self.per_key_counts[key] += 1
        if success:
            self.successes += 1
        else:
            self.failures += 1

    def snapshot(self) -> dict:
        avg_latency = (
            self.latency_sum / self.total_requests if self.total_requests else 0.0
        )
        return {
            "total_requests": self.total_requests,
            "successes": self.successes,
            "failures": self.failures,
            "avg_latency_sec": avg_latency,
            "per_key_counts": self.per_key_counts.copy(),
        }


class GeminiAccountSlot:
    """Representa una cuenta física de Gemini Pro/Flash aislada."""

    def __init__(self, slot_id: int, api_key: str) -> None:
        self.slot_id = slot_id
        self.api_key = api_key
        # Telemetry singleton
        self.telemetry = GeminiProTelemetry.get_instance()
        self.cooldown_until: float = 0.0
        self.requests_count: int = 0
        self.errors_count: int = 0

    @property
    def is_available(self) -> bool:
        return time.time() >= self.cooldown_until

    def set_cooldown(self, base_seconds: float = 60.0) -> None:
        """Aplica enfriamiento con backoff exponencial basado en errores acumulados (Ω27)."""
        factor = min(2 ** (self.errors_count), 16)
        cooldown_time = base_seconds * factor
        self.cooldown_until = time.time() + cooldown_time
        self.errors_count += 1

    def reset_stats(self) -> None:
        """Reinicia el contador de errores al completar exitosamente una petición."""
        if self.errors_count > 0:
            self.errors_count = 0


class GeminiProPoolManager:
    """Manage a pool of Gemini Pro API keys with round‑robin dispatch and telemetry."""

    """Manejador de Pool Multi-Cuenta para Gemini Pro/Flash (C5-REAL)."""

    def __init__(self, env_prefix: str = "GEMINI_API_KEY") -> None:
        self.slots: List[GeminiAccountSlot] = []
        self._current_index: int = 0
        self.telemetry = GeminiProTelemetry.get_instance()
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
        """Dispara una inferencia rotando entre las cuentas disponibles con tolerancia BFT."""
        attempts = 0
        max_attempts = len(self.slots) if self.slots else 1

        last_error: Optional[Exception] = None
        start_time = time.perf_counter()

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
                            slot.reset_stats()
                            latency = time.perf_counter() - start_time
                            self.telemetry.record(slot.api_key[:8], True, latency)
                            return str(parts[0].get("text", ""))
                    return ""
            except urllib.error.HTTPError as e:
                if e.code == 429 or e.code == 503:
                    # Enfriar esta cuenta con Backoff Exponencial
                    slot.set_cooldown(60.0)
                    last_error = e
                    attempts += 1
                    continue
                else:
                    self.telemetry.record(
                        slot.api_key[:8], False, time.perf_counter() - start_time
                    )
                    raise EpistemicPoolHalt(
                        f"HTTPError Gemini API [{e.code}]: {e.reason}"
                    )
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                slot.set_cooldown(15.0)
                last_error = e
                attempts += 1
                continue

        self.telemetry.record("pool_exhausted", False, time.perf_counter() - start_time)
        raise EpistemicPoolHalt(
            f"Agotadas todas las cuentas ({max_attempts}) del pool Gemini Pro. Error: {last_error}"
        )

    async def adispatch_generate_content(
        self, prompt: str, model: str = "gemini-1.5-pro"
    ) -> str:
        """Versión asíncrona no bloqueante de dispatch_generate_content (Ω45/Ω27)."""
        import asyncio

        return await asyncio.to_thread(self.dispatch_generate_content, prompt, model)

    def get_pool_stats(self) -> dict[str, Any]:
        """Devuelve las métricas termodinámicas actuales de cada slot del pool."""
        now = time.time()
        stats = {
            "total_slots": len(self.slots),
            "available_slots": sum(1 for s in self.slots if s.is_available),
            "telemetry": self.telemetry.snapshot(),
            "slots": [
                {
                    "slot_id": s.slot_id,
                    "key_prefix": f"{s.api_key[:8]}...{s.api_key[-4:]}",
                    "requests_count": s.requests_count,
                    "errors_count": s.errors_count,
                    "is_available": s.is_available,
                    "cooldown_remaining_sec": max(
                        0.0, round(s.cooldown_until - now, 2)
                    ),
                }
                for s in self.slots
            ],
        }
        return stats


if __name__ == "__main__":
    print("Gemini Pro Multi-Account Pool Manager (C5-REAL) cargado.")
    manager = GeminiProPoolManager()
    print(f"Cuentas activas en pool: {len(manager.slots)}")
    print(json.dumps(manager.get_pool_stats(), indent=2))
