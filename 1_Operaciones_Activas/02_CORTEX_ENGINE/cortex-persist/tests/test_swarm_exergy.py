import pytest
from babylon60.swarm.exergy import ExergyBank, AgentWallet

def test_exergy_bank_register():
    bank = ExergyBank()
    wallet = bank.register_agent("agent-1")
    assert wallet.agent_id == "agent-1"
    assert wallet.balance == ExergyBank.INITIAL_EXERGY
    assert wallet.is_alive is True

def test_exergy_bank_stake():
    bank = ExergyBank()
    bank.register_agent("agent-1")

    success = bank.stake("agent-1")
    assert success is True

    wallet = bank.wallets["agent-1"]
    assert wallet.staked == ExergyBank.STAKE_REQUIRED_PER_PROPOSAL
    assert wallet.balance == ExergyBank.INITIAL_EXERGY - ExergyBank.STAKE_REQUIRED_PER_PROPOSAL

def test_exergy_bank_stake_bankrupt():
    bank = ExergyBank()
    wallet = bank.register_agent("agent-1")
    wallet.balance = 0.0 # Force bankrupt

    success = bank.stake("agent-1")
    assert success is False
    assert wallet.is_alive is False

def test_exergy_bank_slash():
    bank = ExergyBank()
    bank.register_agent("agent-1")
    bank.stake("agent-1")

    bank.slash("agent-1")
    wallet = bank.wallets["agent-1"]
    assert wallet.staked == 0.0
    assert wallet.failed_commits == 1

def test_exergy_bank_reward():
    bank = ExergyBank()
    bank.register_agent("agent-1")
    bank.stake("agent-1")

    bank.reward("agent-1")
    wallet = bank.wallets["agent-1"]
    assert wallet.staked == 0.0
    assert wallet.successful_commits == 1
    expected_balance = (ExergyBank.INITIAL_EXERGY - ExergyBank.STAKE_REQUIRED_PER_PROPOSAL) + (ExergyBank.STAKE_REQUIRED_PER_PROPOSAL * ExergyBank.REWARD_MULTIPLIER)
    assert wallet.balance == expected_balance

def test_exergy_bank_dissipate():
    class DummyRegistry:
        def __init__(self):
            class DummyAgent:
                agent_id = "agent-1"
            self._agents = {"key1": DummyAgent()}

    bank = ExergyBank()
    bank.register_agent("agent-1")
    registry = DummyRegistry()

    bank.dissipate_agent("agent-1", registry)

    wallet = bank.wallets["agent-1"]
    assert wallet.is_alive is False
    assert wallet.balance == 0.0
    assert "key1" not in registry._agents

def test_exergy_bank_get_state():
    bank = ExergyBank()
    bank.register_agent("agent-1")
    bank.stake("agent-1")
    bank.reward("agent-1")

    state = bank.get_state()
    assert "agent-1" in state
    assert state["agent-1"]["staked"] == 0.0
    assert state["agent-1"]["win_rate"] == 1.0
