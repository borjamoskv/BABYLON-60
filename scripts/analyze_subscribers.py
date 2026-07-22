"""
CLI Transducer for Substack Subscriber Thermodynamic Audit.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml
from cortex.substack_subscriber_audit import SubstackSubscriberAuditor, AuditSummary


def main() -> None:
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
    else:
        env_path = os.environ.get(
            "SUBSTACK_CSV_PATH",
            str(Path.home() / "Downloads" / "subscriber-export.csv"),
        )
        csv_path = Path(env_path)
        if not csv_path.exists():
            print("Usage: python analyze_subscribers.py <path_to_substack_csv>")
            sys.exit(1)

    print(f"Executing C5-REAL Audit on: {csv_path}")
    auditor = SubstackSubscriberAuditor.from_csv(csv_path)
    summary: AuditSummary = auditor.generate_summary()

    print("\n--- MACRO ESTRUCTURAL ---")
    print(f"Total Subscribers: {summary.total_subscribers}")
    print(f"Total Revenue: ${summary.total_revenue:.2f}")
    print(
        f"Comp: {summary.comp_count} | Free: {summary.free_count} | Author: {summary.author_count}"
    )
    print(f"Activity Distribution: {summary.activity_distribution}")
    print(f"VIP Institutional Accounts: {summary.vip_count}")
    print(f"High Exergy Audience (Activity >= 3): {summary.high_exergy_count}")
    print(
        f"Deliverability Hazard Candidates (Comp & Act 0): {summary.deliverability_hazard_count}"
    )

    print("\n--- COHORT RETENTION & DECAY BREAKDOWN ---")
    sorted_cohorts = sorted(
        summary.cohorts.items(), key=lambda x: x[1]["total"], reverse=True
    )[:8]
    for date_key, data in sorted_cohorts:
        print(
            f"Date: {date_key:10s} | Total: {data['total']:3d} | Comp: {data['comp']:3d} | Active(>=3): {data['active_ge_3']:2d} | Retention: {data['retention_rate']:5.1f}% | Zombies(0): {data['zombies_act_0']:3d}"
        )

    # Export Segmented CSVs
    output_dir = Path("artifacts") / "substack_segmented_subscribers"
    exported = auditor.export_segmented_csvs(output_dir)
    print(f"\n[OK] Segmented CSVs exported to: {output_dir}")
    for tier, pth in exported.items():
        print(f"  - {tier}: {pth}")

    # Export YAML receipt
    audit_report = {
        "Claim": "AUDITORÍA DE BASE DE SUSCRIPTORES (SUBSTACK EXPORT)",
        "Target": str(csv_path),
        "Proof": {
            "TotalSubscribers": summary.total_subscribers,
            "HighExergyReaders": summary.high_exergy_count,
            "DeliverabilityHazards": summary.deliverability_hazard_count,
            "VIPCount": summary.vip_count,
            "Confidence": "C5-REAL",
        },
    }

    report_file = Path("artifacts") / "substack_subscriber_audit_report.yml"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        yaml.dump(audit_report, f, default_flow_style=False, allow_unicode=True)

    print(f"[OK] Audit receipt written to: {report_file}")


if __name__ == "__main__":
    main()
