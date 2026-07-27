# Forensic Report: InsurAce RewardController Permissionless Harvest
**ID**: OUROBOROS-INSURACE-0505-02
**Target**: InsurAce Protocol (RewardController)
**Address**: `0x9933B0419CFB71791DA75AC2DCEA952D0875C967`
**Severity**: High
**Confidence**: C5-REAL (JIL Verified)

## 1. Vulnerability Overview
The `harvest()` function in the `RewardController` contract lacks sufficient access control, allowing any address to trigger reward distributions for arbitrary pools. While not an immediate fund drain, it allows attackers to front-run legitimate harvests or manipulate reward timing to disrupt protocol incentives.

## 2. Technical Deconstruction
The function `harvest(address _pool)` is marked `public` and does not check `msg.sender`.

### Attack Vector:
1. Attacker monitors pending rewards for a high-value pool.
2. Attacker calls `harvest()` on behalf of the pool.
3. If the pool logic relies on specific timing or "harvest windows" (e.g., for boosting), the attacker can prematurely trigger the event, diluting rewards for legitimate stakers.

## 3. Forensic Evidence
- **Source Analysis**: Verified via Etherscan/Bytecode. The `harvest` function logic is standard but lacks the `onlyOwner` or `onlyAuthorized` modifiers found in similar high-security protocols.
- **TVL Snapshot**: $139k (DefiLlama). The impact is limited to the current active liquidity.

## 4. Remediation
- Add `onlyAuthorized` modifier to the `harvest()` function.
- Implement a minimum interval between harvests to prevent spamming.

## 5. Notarization
Notarized in Ouroboros Strike Ledger: `public/reports.json`
Status: JIL Verified // Ready for Submission
