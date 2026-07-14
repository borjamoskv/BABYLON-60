import pytest
from cortex.daemons.autopoiesis.bitcoin_aci import BitcoinACI, EconomicSIGKILL

def test_bitcoin_aci_initialization():
    """Valida la ignición con balance base."""
    aci = BitcoinACI(rpc_url="http://localhost:8332", atp_threshold_sats=1000)
    assert aci.wallet_balance_sats == 50000

def test_bitcoin_aci_l1_read():
    """Valida lectura de estado físico sin costo."""
    aci = BitcoinACI(rpc_url="http://localhost:8332")
    state = aci.L1_flash_read_state("some_txid")
    assert state["txid"] == "some_txid"
    assert state["confirmations"] == 6

def test_bitcoin_aci_l3_delegation_depletes_balance():
    """Valida que la delegación reste satoshis del balance."""
    aci = BitcoinACI(rpc_url="http://localhost:8332", atp_threshold_sats=1000)
    initial_balance = aci.wallet_balance_sats
    res = aci.L3_delegate_subtask({"task": "test"}, max_sats=2000)
    assert res["status"] == "HTLC_SETTLED"
    assert aci.wallet_balance_sats == initial_balance - 1000

def test_bitcoin_aci_economic_sigkill():
    """Valida que si el balance cae bajo el umbral, se detone la muerte termodinámica."""
    aci = BitcoinACI(rpc_url="http://localhost:8332", atp_threshold_sats=45000)
    # Primera delegación exitosa (saca 5000 sats, balance cae a 45000)
    aci.L3_delegate_subtask({"task": "t1"}, max_sats=10000)
    
    # La siguiente delegación debería disparar el EconomicSIGKILL porque balance ya es <= threshold
    with pytest.raises(EconomicSIGKILL):
        aci.L3_delegate_subtask({"task": "t2"}, max_sats=1000)

def test_bitcoin_aci_l8_bounty_refuels_balance():
    """Valida la inyección de exergía en cobro de PR."""
    aci = BitcoinACI(rpc_url="http://localhost:8332", atp_threshold_sats=1000)
    aci.L8_collapse_bounty("github.com/test", "hash123", reward_sats=10000)
    assert aci.wallet_balance_sats == 60000
