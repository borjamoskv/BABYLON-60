import os


from babylon60.license_manager import generate_license_key
import time


def test_community_limit():
    db_path = "scratch/test_community.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    # Community License (None)
    ledger = LedgerPersist(db_path, license_key=None)
    assert ledger.license_status.tier == "community"

    # Create 101 nodes
    graph = GraphLedger()
    last_id = graph.genesis_id
    for i in range(101):
        node = graph.mut_append_node(last_id, f"claim_{i}", "0" * 64)
        last_id = node.node_id

    try:
        ledger.io_persist_ledger(graph)
        assert False, "Should have raised ValueError for batch > 100 on community tier"
    except ValueError as e:
        assert "Community tier limits batch inserts" in str(e)
        print("Community limit check passed.")
    ledger.close()


def test_enterprise_unlimited():
    db_path = "scratch/test_enterprise.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    # Generate Enterprise Key
    exp = int(time.time()) + 3600
    ent_key = generate_license_key("TestCorp", "enterprise", exp)

    # Enterprise License
    ledger = LedgerPersist(db_path, license_key=ent_key)
    assert ledger.license_status.tier == "enterprise"

    # Create 150 nodes
    graph = GraphLedger()
    last_id = graph.genesis_id
    for i in range(150):
        node = graph.mut_append_node(last_id, f"claim_{i}", "0" * 64)
        last_id = node.node_id

    inserted = ledger.io_persist_ledger(graph)
    assert inserted == 150
    print("Enterprise unlimited check passed.")
    ledger.close()


if __name__ == "__main__":
    test_community_limit()
    test_enterprise_unlimited()
    print("All tests passed.")
