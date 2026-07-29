# C5-REAL EXERGY CERTIFIED
import pytest
from babylon60.extensions.subagents.resilient_browser import ResilientBrowserAgent


class TestResilientBrowserAgent:
    def test_fetch_and_filter_valid_exergy(self):
        """Tests that valid technical content with proof anchor survives Popperian filter."""
        agent = ResilientBrowserAgent()
        valid_text = (
            "BABYLON-60 provides deterministic memory verification. "
            "Proof anchor hash: sha256_e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855. "
            "Tested under C5-REAL silicon standards with sub-5ms latency."
        )
        res = agent.fetch_and_filter("https://babylon60.com", valid_text)
        assert res.is_ok

    def test_fetch_and_filter_hype_discarded(self):
        """Tests that marketing hype is cleanly rejected by 1-WL filter."""
        agent = ResilientBrowserAgent()
        hype_text = "Unlock your true potential with this groundbreaking 100x gains game changer system!"
        res = agent.fetch_and_filter("https://hype.com", hype_text)
        assert not res.is_ok

    def test_resilient_backoff_recovery(self):
        """Tests exponential backoff on simulated 429 errors."""
        agent = ResilientBrowserAgent(max_retries=2, backoff_factor=0.01)
        calls = 0

        def flaky_query():
            nonlocal calls
            calls += 1
            if calls == 1:
                raise RuntimeError("RESOURCE_EXHAUSTED (code 429)")
            return "SUCCESS"

        result = agent.execute_resilient_query(flaky_query)
        assert result == "SUCCESS"
        assert calls == 2
