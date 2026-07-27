#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# CORTEX STRIKE SUBMITTER v2.0 — 7 Reports (6 Immunefi + 1 Code4rena)
# Semi-automated: copies content → opens submission page
# Reality Level: C5-REAL
# ═══════════════════════════════════════════════════════════════

set -e

REPORTS_DIR="/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/reports/FINAL_7_STRIKES_MAY2026"
LOG_FILE="${REPORTS_DIR}/submission_log.txt"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Immunefi universal submission URL (program selected in-form)
IMMUNEFI_URL="https://bugs.immunefi.com/dashboard/new-submission"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ⚡ CORTEX STRIKE SUBMITTER v2.0"
echo "  Reality Level: C5-REAL"  
echo "  Timestamp: ${TIMESTAMP}"
echo "  Reports: 6 Immunefi + 1 Code4rena"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  Programs:"
echo "  ┌─────────────────────────────────────────────────────────┐"
echo "  │ #1 LayerZero    │ Critical │ Max $15,000,000 │ Immunefi│"
echo "  │ #2 Lido V3      │ Critical │ Max  $2,000,000 │ Immunefi│"
echo "  │ #3 Firedancer   │ Critical │ Max    $500,000 │ Immunefi│"
echo "  │ #4 Exactly (x3) │ High-Crt │ Max     $25,000 │ Immunefi│"
echo "  │ #5 K2 Lending   │ Critical │ Code4rena audit │ C4      │"
echo "  └─────────────────────────────────────────────────────────┘"
echo ""
echo "  ⚠️  Each step will:"
echo "     1. Copy the report markdown to your clipboard"
echo "     2. Open the submission page in Brave Browser"
echo "     3. Wait for you to paste, configure, and submit"
echo ""
read -p "  → Press ENTER to begin submissions... "
echo ""

# ──────────────────────────────────────────
# STRIKE 1: LayerZero ($15M max bounty)
# ──────────────────────────────────────────
echo "══════════════════════════════════════════════════════════════"
echo "  STRIKE 1/7: LayerZero — Shadow Library Exploit"
echo "  Severity: CRITICAL  |  Max Bounty: \$15,000,000"
echo "  Program: layerzero"
echo "══════════════════════════════════════════════════════════════"
cat "${REPORTS_DIR}/7_LayerZero_Shadow_Exploit/layerzero-shadow-exploit-immunefi.md" | pbcopy
echo "  ✅ Report copied to clipboard ($(wc -c < "${REPORTS_DIR}/7_LayerZero_Shadow_Exploit/layerzero-shadow-exploit-immunefi.md") bytes)"
osascript -e "tell application \"Brave Browser\" to open location \"${IMMUNEFI_URL}\""
osascript -e 'tell application "Brave Browser" to activate'
echo ""
echo "  📋 IN THE FORM:"
echo "     • Select program: LayerZero"
echo "     • Vulnerability type: Smart Contract"
echo "     • Severity: Critical"
echo "     • Paste report content (Cmd+V)"
echo "     • Review and Submit"
echo ""
read -p "  → Press ENTER after submitting Strike 1 (LayerZero)... "
echo "${TIMESTAMP} | SUBMITTED | LayerZero | Critical | layerzero-shadow-exploit-immunefi.md" >> "${LOG_FILE}"
echo "  ✓ Strike 1 logged"
echo ""

# ──────────────────────────────────────────
# STRIKE 2: Lido V3 ($2M max bounty)
# ──────────────────────────────────────────
echo "══════════════════════════════════════════════════════════════"
echo "  STRIKE 2/7: Lido V3 — VaultHub Untracked ETH Injection"
echo "  Severity: CRITICAL  |  Max Bounty: \$2,000,000"
echo "  Program: lido"
echo "══════════════════════════════════════════════════════════════"
cat "${REPORTS_DIR}/6_Lido_V3_VaultHub_Untracked_ETH/lido-v3-vaulthub-untracked-eth-injection.md" | pbcopy
echo "  ✅ Report copied to clipboard"
osascript -e "tell application \"Brave Browser\" to open location \"${IMMUNEFI_URL}\""
osascript -e 'tell application "Brave Browser" to activate'
echo ""
echo "  📋 IN THE FORM:"
echo "     • Select program: Lido"
echo "     • Vulnerability type: Smart Contract"
echo "     • Severity: Critical"
echo "     • Paste (Cmd+V) and Submit"
echo ""
read -p "  → Press ENTER after submitting Strike 2 (Lido V3)... "
echo "${TIMESTAMP} | SUBMITTED | Lido V3 | Critical | lido-v3-vaulthub-untracked-eth-injection.md" >> "${LOG_FILE}"
echo "  ✓ Strike 2 logged"
echo ""

# ──────────────────────────────────────────
# STRIKE 3: Firedancer ($500K max bounty)
# ──────────────────────────────────────────
echo "══════════════════════════════════════════════════════════════"
echo "  STRIKE 3/7: Firedancer — Funk State Ghosting"
echo "  Severity: CRITICAL  |  Max Bounty: \$500,000"
echo "  Program: firedancer"
echo "══════════════════════════════════════════════════════════════"
cat "${REPORTS_DIR}/5_Firedancer_Funk_State_Ghosting/firedancer-funk-state-ghosting-c5.md" | pbcopy
echo "  ✅ Report copied to clipboard"
osascript -e "tell application \"Brave Browser\" to open location \"${IMMUNEFI_URL}\""
osascript -e 'tell application "Brave Browser" to activate'
echo ""
echo "  📋 IN THE FORM:"
echo "     • Select program: Firedancer"
echo "     • Vulnerability type: Smart Contract / Blockchain/DLT"
echo "     • Severity: Critical"
echo "     • Paste (Cmd+V) and Submit"
echo "     • ALSO ATTACH: test_ghosting_poc.c from the same directory"
echo ""
read -p "  → Press ENTER after submitting Strike 3 (Firedancer)... "
echo "${TIMESTAMP} | SUBMITTED | Firedancer | Critical | firedancer-funk-state-ghosting-c5.md" >> "${LOG_FILE}"
echo "  ✓ Strike 3 logged"
echo ""

# ──────────────────────────────────────────
# STRIKE 4: Exactly — Stale Oracle ($25K max)
# ──────────────────────────────────────────
echo "══════════════════════════════════════════════════════════════"
echo "  STRIKE 4/7: Exactly — Stale Oracle L2 (Optimism/Base)"
echo "  Severity: HIGH  |  Max Bounty: \$25,000"
echo "  Program: exactly"
echo "══════════════════════════════════════════════════════════════"
cat "${REPORTS_DIR}/2_Exactly_Stale_Oracle/exactly-stale-oracle-immunefi-submission.md" | pbcopy
echo "  ✅ Report copied to clipboard"
osascript -e "tell application \"Brave Browser\" to open location \"${IMMUNEFI_URL}\""
osascript -e 'tell application "Brave Browser" to activate'
echo ""
echo "  📋 IN THE FORM:"
echo "     • Select program: Exactly"
echo "     • Vulnerability type: Smart Contract"
echo "     • Severity: High"
echo "     • Paste (Cmd+V) and Submit"
echo ""
read -p "  → Press ENTER after submitting Strike 4 (Exactly Stale Oracle)... "
echo "${TIMESTAMP} | SUBMITTED | Exactly | High | exactly-stale-oracle-immunefi-submission.md" >> "${LOG_FILE}"
echo "  ✓ Strike 4 logged"
echo ""

# ──────────────────────────────────────────
# STRIKE 5: Exactly — VerifiedMarket Borrow Bypass
# ──────────────────────────────────────────
echo "══════════════════════════════════════════════════════════════"
echo "  STRIKE 5/7: Exactly — VerifiedMarket Borrow Bypass"
echo "  Severity: HIGH  |  Max Bounty: \$25,000"
echo "  Program: exactly"
echo "══════════════════════════════════════════════════════════════"
cat "${REPORTS_DIR}/3_Exactly_VerifiedMarket_Borrow_Bypass/exactly-verifiedmarket-borrow-bypass-immunefi.md" | pbcopy
echo "  ✅ Report copied to clipboard"
osascript -e "tell application \"Brave Browser\" to open location \"${IMMUNEFI_URL}\""
osascript -e 'tell application "Brave Browser" to activate'
echo ""
echo "  📋 IN THE FORM:"
echo "     • Select program: Exactly"
echo "     • Vulnerability type: Smart Contract"
echo "     • Severity: High"
echo "     • Affected Asset: Base MarketUSDC proxy"
echo "     • Paste (Cmd+V) and Submit"
echo ""
read -p "  → Press ENTER after submitting Strike 5 (Exactly Borrow Bypass)... "
echo "${TIMESTAMP} | SUBMITTED | Exactly | High | exactly-verifiedmarket-borrow-bypass-immunefi.md" >> "${LOG_FILE}"
echo "  ✓ Strike 5 logged"
echo ""

# ──────────────────────────────────────────
# STRIKE 6: Exactly — VerifiedMarket Delegate Bypass (Re-submission)
# ──────────────────────────────────────────
echo "══════════════════════════════════════════════════════════════"
echo "  STRIKE 6/7: Exactly — VerifiedMarket Delegate Bypass"
echo "  Severity: CRITICAL  |  Max Bounty: \$25,000"
echo "  Program: exactly (RE-SUBMISSION of #77250)"
echo "══════════════════════════════════════════════════════════════"
cat "${REPORTS_DIR}/4_Exactly_VerifiedMarket_Delegate_Bypass/exactly-verifiedmarket-delegate-bypass-reopened.md" | pbcopy
echo "  ✅ Report copied to clipboard"
osascript -e "tell application \"Brave Browser\" to open location \"${IMMUNEFI_URL}\""
osascript -e 'tell application "Brave Browser" to activate'
echo ""
echo "  📋 IN THE FORM:"
echo "     • Select program: Exactly"
echo "     • Vulnerability type: Smart Contract"
echo "     • Severity: Critical (re-submission — asset corrected)"
echo "     • Affected Asset: Base MarketUSDC proxy 0x2776..."
echo "     • NOTE: Reference previous #77250 in description"
echo "     • Paste (Cmd+V) and Submit"
echo ""
read -p "  → Press ENTER after submitting Strike 6 (Exactly Delegate Bypass)... "
echo "${TIMESTAMP} | SUBMITTED | Exactly | Critical | exactly-verifiedmarket-delegate-bypass-reopened.md" >> "${LOG_FILE}"
echo "  ✓ Strike 6 logged"
echo ""

# ──────────────────────────────────────────
# STRIKE 7: K2 Lending (Code4rena, NOT Immunefi)
# ──────────────────────────────────────────
echo "══════════════════════════════════════════════════════════════"
echo "  STRIKE 7/7: K2 Lending — Close Factor Bypass"
echo "  Severity: CRITICAL  |  Platform: Code4rena"
echo "  ⚠️  This is NOT Immunefi — different platform"
echo "══════════════════════════════════════════════════════════════"
cat "${REPORTS_DIR}/1_K2_Lending_Close_Factor_Bypass/k2-lending-close-factor-bypass-c4.md" | pbcopy
echo "  ✅ Report copied to clipboard"
osascript -e 'tell application "Brave Browser" to open location "https://code4rena.com/audits"'
osascript -e 'tell application "Brave Browser" to activate'
echo ""
echo "  📋 IN CODE4RENA:"
echo "     • Find K2 Lending audit (if still open)"
echo "     • Submit as Critical/High finding"
echo "     • Paste (Cmd+V) and Submit"
echo "     • If audit is closed, skip this strike"
echo ""
read -p "  → Press ENTER after submitting Strike 7 (K2 Lending) or SKIP... "
echo "${TIMESTAMP} | SUBMITTED | K2 Lending | Critical | k2-lending-close-factor-bypass-c4.md | Code4rena" >> "${LOG_FILE}"
echo "  ✓ Strike 7 logged"
echo ""

# ──────────────────────────────────────────
# SUMMARY
# ──────────────────────────────────────────
echo "═══════════════════════════════════════════════════════════════"
echo "  ⚡ ALL 7 STRIKES DEPLOYED"
echo ""
echo "  Total Immunefi submissions: 6"
echo "  Total Code4rena submissions: 1"  
echo "  Max theoretical bounty: \$17,575,000"
echo ""
echo "  Pipeline status: PREPARED → SUBMITTED"
echo "  Next milestone: TRIAGED → CONFIRMED"
echo ""
echo "  Log: ${LOG_FILE}"
echo "═══════════════════════════════════════════════════════════════"
