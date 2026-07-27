#!/usr/bin/env python3
"""
Code4rena K2 Stellar — Submission Helper
Opens the submission page and pre-fills the report content.
REQUIRES: User logged in to Code4rena and joined the K2 audit.
"""
import subprocess

REPORT_PATH = "/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/reports/k2-stellar-admin-takeover-c5-real.md"

def main():
    # Read report
    with open(REPORT_PATH, 'r') as f:
        report = f.read()
    
    # Extract key fields
    title = "Unauthenticated Token Admin Takeover via initialize() — Critical"
    severity = "Critical"
    
    # Copy report to clipboard for easy paste
    process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
    process.communicate(report.encode('utf-8'))
    
    print("=" * 60)
    print("🎯 K2 STELLAR — CODE4RENA SUBMISSION READY")
    print("=" * 60)
    print()
    print(f"📋 Title: {title}")
    print(f"🔴 Severity: {severity}")
    print(f"📄 Report: {REPORT_PATH}")
    print()
    print("✅ Report content copied to clipboard (Cmd+V to paste)")
    print()
    print("📌 STEPS:")
    print("1. Go to: https://code4rena.com/audits/2026-04-k2")
    print("2. Click 'Submit Finding' (must be logged in + joined)")
    print("3. Select severity: Critical (High if Critical not available)")
    print("4. Paste title and report from clipboard")
    print("5. Add PoC: The Rust test is embedded in the report")
    print("6. Submit")
    print()
    print("⏰ Deadline: May 27, 2026 8:00 PM UTC (18 days)")
    print("💰 Pool: $135,000 USDC")
    print()
    
    # Open C4 page
    subprocess.run(['open', 'https://code4rena.com/audits/2026-04-k2'])
    print("🌐 Browser opened to K2 audit page")

if __name__ == "__main__":
    main()
