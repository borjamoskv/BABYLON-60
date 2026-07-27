import pytest
from unittest.mock import MagicMock

from babylon60.swarm.hydrate import _classify_tier

def test_classify_tier_t0():
    entry = MagicMock()
    entry.tools = ["a", "b", "c", "d", "e"]
    entry.intent = "code"
    entry.provider = "dummy"
    entry.system_prompt = "Short"
    entry.memory.causal_memory = False
    assert _classify_tier(entry) == "T0"

def test_classify_tier_t1_tools():
    entry = MagicMock()
    entry.tools = ["a", "b"]
    entry.intent = "code"
    entry.provider = "dummy"
    entry.system_prompt = "Short"
    entry.memory.causal_memory = False
    assert _classify_tier(entry) == "T1"

def test_classify_tier_t1_prompt():
    entry = MagicMock()
    entry.tools = ["a"]
    entry.intent = ""
    entry.provider = ""
    entry.system_prompt = "A" * 501
    entry.memory.causal_memory = False
    assert _classify_tier(entry) == "T1"

def test_classify_tier_t1_memory():
    entry = MagicMock()
    entry.tools = []
    entry.intent = ""
    entry.provider = ""
    entry.system_prompt = "Short"
    entry.memory.causal_memory = True
    assert _classify_tier(entry) == "T1"

def test_classify_tier_t2():
    entry = MagicMock()
    entry.tools = []
    entry.intent = ""
    entry.provider = ""
    entry.system_prompt = "Short"
    entry.memory.causal_memory = False
    assert _classify_tier(entry) == "T2"
