# C5-REAL EXERGY CERTIFIED
"""
Unit tests for SubstackSubscriberAuditor in cortex.
"""

from __future__ import annotations
import csv
import os
import tempfile
import unittest
from pathlib import Path
from cortex.substack_subscriber_audit import (
    SubstackSubscriberAuditor,
)

class TestSubstackSubscriberAuditor(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dir = tempfile.TemporaryDirectory()
        self.csv_path = Path(self.test_dir.name) / "test_subscribers.csv"

        # Write dummy CSV for testing
        with open(self.csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Email", "Type", "Activity", "Name", "Start date", "Revenue"])
            writer.writerow(
                [
                    "clement@huggingface.co",
                    "Comp",
                    "4",
                    "Clement Delangue",
                    "2026-05-30",
                    "$0.00",
                ]
            )
            writer.writerow(
                [
                    "peter@foundersfund.com",
                    "Comp",
                    "5",
                    "Peter Thiel",
                    "2026-04-30",
                    "$0.00",
                ]
            )
            writer.writerow(["random_zombie@gmail.com", "Comp", "0", "", "2026-07-09", "$0.00"])
            writer.writerow(
                [
                    "casual_reader@domain.com",
                    "Free",
                    "2",
                    "Casual",
                    "2026-06-15",
                    "$0.00",
                ]
            )

    def tearDown(self) -> None:
        self.test_dir.cleanup()

    def test_record_parsing(self) -> None:
        auditor = SubstackSubscriberAuditor.from_csv(self.csv_path)
        self.assertEqual(len(auditor.subscribers), 4)

        vip_sub = auditor.subscribers[0]
        self.assertTrue(vip_sub.is_vip())
        self.assertEqual(vip_sub.activity, 4)
        self.assertEqual(vip_sub.subscriber_type, "Comp")

    def test_audit_summary(self) -> None:
        auditor = SubstackSubscriberAuditor.from_csv(self.csv_path)
        summary = auditor.generate_summary()

        self.assertEqual(summary.total_subscribers, 4)
        self.assertEqual(summary.comp_count, 3)
        self.assertEqual(summary.free_count, 1)
        self.assertEqual(summary.vip_count, 2)
        self.assertEqual(summary.high_exergy_count, 2)
        self.assertEqual(summary.deliverability_hazard_count, 1)
        self.assertIn("2026-05-30", summary.cohorts)

    def test_tier_classification_and_export(self) -> None:
        auditor = SubstackSubscriberAuditor.from_csv(self.csv_path)
        tiers = auditor.classify_tiers()

        self.assertEqual(len(tiers["tier1_c5real_core"]), 2)
        self.assertEqual(len(tiers["tier2_engaged"]), 1)
        self.assertEqual(len(tiers["tier4_deliverability_hazard"]), 1)

        out_dir = Path(self.test_dir.name) / "exported_tiers"
        exported_files = auditor.export_segmented_csvs(out_dir)

        self.assertTrue(os.path.exists(exported_files["tier1_c5real_core"]))
        self.assertTrue(os.path.exists(exported_files["tier4_deliverability_hazard"]))

        # Check content of exported tier 1 file
        with open(exported_files["tier1_c5real_core"], "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines()]
            self.assertEqual(len(lines), 3)  # Header + 2 VIP records

if __name__ == "__main__":
    unittest.main()
