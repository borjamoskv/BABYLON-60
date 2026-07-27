# C5-REAL EXERGY CERTIFIED
import os
import sys
from subscriber_engine import SubstackSubscriberEngine

def sync() -> None:
    """Delegated sync entry point that runs the SubstackSubscriberEngine pipeline."""
    home = os.path.expanduser("~")
    json_path = "/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/01_INTEL_SUITE/substack-osint-miner/output/subscriber_analysis.json"
    db_path = os.path.join(home, ".babylon60/substack_subscribers_vault.db")
    report_path = "/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/01_INTEL_SUITE/substack-osint-miner/output/vault_sync_report.md"

    engine = SubstackSubscriberEngine()
    success = engine.sync_to_vault(json_path, db_path, report_path)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    sync()
