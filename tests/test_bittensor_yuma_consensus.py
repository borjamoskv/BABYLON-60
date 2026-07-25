import os
import sqlite3
from scripts.bittensor_yuma_consensus_c5 import compute_yuma_consensus, simulate_adversarial_matrix, simulate_subnet_emission, simulate_subnet_epochs

def test_compute_yuma_consensus_clipping_sybil() -> None:
    stakes = [500000.0, 250000.0, 150000.0, 100000.0]
    weights = [[0.3, 0.4, 0.2, 0.1, 0.0], [0.25, 0.45, 0.2, 0.1, 0.0], [0.2, 0.3, 0.3, 0.2, 0.0], [0.0, 0.0, 0.0, 0.0, 1.0]]
    ranks, trust, consensus, dividends, state_hash = compute_yuma_consensus(weights, stakes)
    assert consensus[4] == 0.0, f'Sybil miner threshold should be clipped to 0, got {consensus[4]}'
    assert ranks[4] == 0.0, f'Sybil miner rank should be 0, got {ranks[4]}'
    assert dividends[3] == 0.0, f'Sybil validator dividend should be 0, got {dividends[3]}'
    assert len(state_hash) == 64, f'Invalid SHA3-256 anchor length: {len(state_hash)}'

def test_simulate_subnet_emission_balance() -> None:
    ranks = [0.4, 0.3, 0.2, 0.1, 0.0]
    dividends = [0.5, 0.3, 0.2, 0.0]
    emission = simulate_subnet_emission(10.0, ranks, dividends, subnet_owner_cut=0.18)
    total_distributed = emission['subnet_owner_tao'] + emission['total_miner_tao'] + emission['total_validator_tao']
    assert abs(total_distributed - 10.0) < 1e-05, f'Emission leakage detected: {total_distributed} vs 10.0'

def test_multi_epoch_and_wal_persistence(tmp_path) -> None:
    db_file = str(tmp_path / 'test_bittensor_ledger.db')
    stakes = [500000.0, 250000.0, 150000.0, 100000.0]
    weights = [[0.3, 0.4, 0.2, 0.1, 0.0], [0.25, 0.45, 0.2, 0.1, 0.0], [0.2, 0.3, 0.3, 0.2, 0.0], [0.0, 0.0, 0.0, 0.0, 1.0]]
    sim = simulate_subnet_epochs(5, weights, stakes, db_path=db_file)
    assert sim['epochs_executed'] == 5
    assert len(sim['history']) == 5
    assert os.path.exists(db_file)
    conn = sqlite3.connect(db_file)
    try:
        cursor = conn.execute('SELECT count(*) FROM yuma_consensus_ledger;')
        count = cursor.fetchone()[0]
        assert count == 5, f'Expected 5 epochs in WAL DB, found {count}'
        cursor = conn.execute('SELECT epoch, state_hash FROM yuma_consensus_ledger ORDER BY epoch ASC;')
        rows = cursor.fetchall()
        assert rows[0][0] == 1
        assert rows[-1][0] == 5
    finally:
        conn.close()

def test_adversarial_stress_matrix_suppression() -> None:
    results = simulate_adversarial_matrix()
    assert results['sybil_swarm_attack']['status'] == 'MITIGATED'
    assert results['sybil_swarm_attack']['sybil_suppression_ratio'] >= 0.99
    assert results['ouroboros_attack']['status'] == 'MITIGATED'
    assert results['ouroboros_attack']['ouroboros_miner_rank'] <= 0.05