# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
Experiment: primer_experimento_c5
Physical implementation: Substack Feed Thermodynamic Audit
Executes the subscriber audit engine and reports exergy metrics.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from cortex.substack_subscriber_audit import SubstackSubscriberAuditor

def execute() -> None:
    """Run the subscriber audit against the default export CSV."""
    default_csv = Path.home() / "Downloads" / "subscriber-export-2026-07-20-02-35-19.csv"
    if not default_csv.exists():
        print(f"[WARN] CSV not found at {default_csv}. Provide path as argument.")
        return

    auditor = SubstackSubscriberAuditor.from_csv(default_csv)
    summary = auditor.generate_summary()

    print(f"Total subscribers:          {summary.total_subscribers}")
    print(f"High-exergy (Activity >= 3): {summary.high_exergy_count}")
    print(f"VIP institutional:          {summary.vip_count}")
    print(f"Deliverability hazards:     {summary.deliverability_hazard_count}")
    print(f"Exergy ratio:               {summary.high_exergy_count / summary.total_subscribers * 100:.1f}%")
    print(f"Anergy load:                {summary.deliverability_hazard_count / summary.total_subscribers * 100:.1f}%")

if __name__ == "__main__":
    execute()
