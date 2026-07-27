# BUG BOUNTY Vulnerability Report — Disallowed delegate can keep borrowing from and withdrawing from VerifiedMarket after firewall revocation

**ID**: HUNT-EXACTLY-MARKETUSDC-VERIFIEDMARKET-20260408
**Date**: 2026-04-08
**Target**: Exactly MarketUSDC / VerifiedMarket
**Severity**: High

## 1. Executive Summary
`VerifiedMarket` is documented as a market that "can only be used by allowed accounts", but current public `main` still leaves allowance-driven inherited paths where a revoked delegate can keep operating through stale approval. In the validated clean-clone PoC, a non-allowed delegate can still (1) open debt on behalf of an allowed borrower while routing borrowed assets to itself and (2) withdraw an allowed owner's assets to itself. This breaks the verified-market access boundary and creates attacker-reachable theft and debt-creation paths against users who granted delegation before the delegate was removed from the allowlist.

## 2. Scope Basis
- Program: bug bounty
- Asset: Exactly MarketUSDC / VerifiedMarket
- Scope URL: https://immunefi.com/bug-bounty/exactly/scope/
- Program URL: https://immunefi.com/bug-bounty/exactly/
- Resources URL: https://immunefi.com/bug-bounty/exactly/resources/
- Scope notes:
  - The scope page showed `MarketUSDC` as an in-scope asset and indicated the asset list was updated on `23 December 2025`.
  - The program page showed `Last Updated 19 March 2026`.
  - The resources page states that implementation changes are in scope only when the proxy is listed in the scope table; `MarketUSDC` is listed there.
- Repo / deployment references:
  - Repo: https://github.com/exactly/protocol
  - Base `MarketUSDC` proxy: [MarketUSDC.json](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/deployments/base/MarketUSDC.json#L2)
  - Base `MarketUSDC` proxy ABI includes `NotAllowed`: [MarketUSDC.json](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/deployments/base/MarketUSDC.json#L83)
  - Base implementation metadata points to `VerifiedMarket`: [MarketUSDC_Implementation.json](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/deployments/base/MarketUSDC_Implementation.json#L3124)

## 3. Technical Analysis
- Root cause:
  - `VerifiedMarket` only wraps some operations with `_requireAllowed(...)` checks and leaves delegated inherited paths such as `borrow()`, `borrowAtMaturity()`, and `withdraw()` without a current-caller firewall check.
  - `VerifiedAuditor.checkBorrow()` only validates the `borrower`, not `msg.sender` and not `receiver`.
  - `withdraw()` relies on owner shortfall checks plus allowance, not on the spender remaining allowlisted.
  - `approve()` is not hardened by the verified wrapper, so previously granted delegation remains usable after the delegate is removed from the firewall allowlist.
- Preconditions:
  - Victim borrower is still allowed by the firewall.
  - Victim previously approved the attacker as delegate on the verified market.
  - For the borrow branch, the victim has enough collateral / credit capacity to borrow from the verified market.
  - For the withdraw branch, the victim has withdrawable balance on the verified market.
  - Attacker is later removed from the firewall allowlist.
- Trigger:
  - The disallowed delegate calls `borrow(assets, attacker, victim)` or `borrowAtMaturity(..., attacker, victim)` on the verified market, or calls `withdraw(assets, attacker, victim)` using stale approval from an allowed owner.
- Broken invariant:
  - A "verified" market should not be operable by non-allowed accounts. After allowlist removal, the delegate should lose the ability to interact with the market. Instead, stale allowances remain usable for debt creation and direct asset extraction.
- Exact files and lines:
  - Verified-market intent: [VerifiedMarket.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/verified/VerifiedMarket.sol#L7)
  - `refund()` and `repay()` explicitly validate both actor and borrower, showing the intended pattern: [VerifiedMarket.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/verified/VerifiedMarket.sol#L130), [VerifiedMarket.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/verified/VerifiedMarket.sol#L144)
  - Floating borrow path validates only `borrower` then transfers to arbitrary `receiver`: [Market.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/Market.sol#L70)
  - Fixed borrow path does the same: [Market.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/Market.sol#L215)
  - Floating withdraw path validates owner shortfall but not spender allowedness: [Market.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/Market.sol#L726)
  - `withdrawAtMaturity()` only validates `owner`, not `msg.sender` or `receiver`: [VerifiedMarket.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/verified/VerifiedMarket.sol#L193), [Market.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/Market.sol#L298)
  - Allowance is consumed against `allowance[account][msg.sender]`, so delegation survives unless explicitly revoked: [Market.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/Market.sol#L857)
  - Auditor checks only `borrower` and `account`: [VerifiedAuditor.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/verified/VerifiedAuditor.sol#L35)

## 4. Proof of Concept
### Steps to Reproduce
Borrow branch:
1. Use an allowed account `BOB` to deposit collateral and enter the collateral market.
2. From `BOB`, approve an external delegate `attacker` on the verified borrow market.
3. Remove `attacker` from the firewall allowlist.
4. From `attacker`, call `borrow(1 ether, attacker, BOB)` on the verified market.
5. Observe that assets are transferred to `attacker` while debt is booked to `BOB`, even though `attacker` is no longer allowed.

Withdraw branch:
1. Give allowed account `BOB` withdrawable balance on the verified market.
2. From `BOB`, approve `attacker` on that market.
3. Remove `attacker` from the firewall allowlist.
4. From `attacker`, call `withdraw(10 ether, attacker, BOB)`.
5. Observe that assets are transferred to `attacker` while `BOB`'s market balance is reduced to zero.

### Evidence
- Deterministic code-path evidence:
  - `borrow()` in `Market` consumes the victim's allowance, calls `auditor.checkBorrow(this, borrower)`, then executes `asset.safeTransfer(receiver, assets)`.
  - `VerifiedAuditor.checkBorrow()` only enforces `onlyAllowed(borrower)`, so the delegated caller and the receiver are never checked.
  - `withdraw()` in `Market` enforces shortfall on `owner` and then defers to ERC4626 withdrawal logic using stale allowance; it does not require the delegated spender to remain allowlisted.
- Local PoC run:
  - I added a temporary Foundry test contract with two ad hoc tests to a clean public clone of `exactly/protocol` `main` at commit `c62bf4c`:
    - `test_poc_disallowedDelegateCanBorrowForAllowedBorrower`
    - `test_poc_disallowedDelegateCanWithdrawFromAllowedOwner`
  - Command used for machine-readable output: `forge test --match-contract VerifiedMarketBypassPoC --json`
  - Parsed results from `/tmp/exactly-clean-bypass.json`:
    - `test_poc_disallowedDelegateCanBorrowForAllowedBorrower()` → `Success`
    - `test_poc_disallowedDelegateCanWithdrawFromAllowedOwner()` → `Success`
  - This confirms both delegated `borrow` and delegated `withdraw` remain usable after firewall revocation on current public `main`.
- Public audit sweep:
  - I scanned the 31 public PDFs in [exactly/audits](https://github.com/exactly/audits) using text extraction and searched for `VerifiedMarket`, `VerifiedAuditor`, `NotAllowed`, `firewall`, and `allowlist`.
  - The two April 2024 "Installments Router and New Market Roles" reports listed from [Exactly audits](https://docs.exact.ly/security/audits) did not surface direct hits for those identifiers.
  - The only direct verified-market hit was [ABDK Protocol Update (Oct-25)](https://raw.githubusercontent.com/exactly/audits/main/ABDK%20Protocol%20Update%20(Oct-25).pdf), which describes `VerifiedMarket` as if transfer, borrow, repay, and withdraw paths were all guarded by allowedness checks.
  - I did not find any public finding or note in those materials that matches stale delegated execution surviving firewall revocation.
  - I also diffed the clean-clone validation sources against the scoped local target checkout and the relevant files were identical.
- Public commit intent:
  - On October 16, 2025, Exactly merged [✨ verified: firewall borrows](https://github.com/exactly/protocol/commit/0e5281e3b0d656ca5581fcfa3c29f5ff2906f9ac), but the public diff only added borrower-allowlisted tests and a borrower-only firewall check in `VerifiedAuditor.checkBorrow(...)`.
  - On October 16, 2025, Exactly also merged [✨ verified: firewall redeem and withdraw](https://github.com/exactly/protocol/commit/bb51de1981c039a694975cfae3bc1f777d86c177), but the public diff only added owner-oriented shortfall checks and owner/sender tests.
  - Those commits support the interpretation that verified-market access was intended to be firewall-restricted, while the delegated spender surface remained incompletely covered.

## 5. Impact
- Attacker outcome:
  - A non-allowed account can continue using a verified market after revocation and can both route newly borrowed assets to itself and directly withdraw victim assets using stale delegation granted earlier.
- User or protocol loss:
  - The allowed borrower is left with debt they did not intend to create after the delegate lost authorization.
  - The allowed owner can also lose already-deposited assets through delegated withdrawal after revocation.
  - The borrower can be forced into liquidation or collateral loss, while the attacker receives the borrowed assets.
- Why this meets the stated severity:
  - This is not a compliance-only issue. It is a monetary authorization bypass on a listed verified market, with a direct path from stale delegation to attacker-controlled asset extraction and victim insolvency risk.

## 6. Remediation
- Immediate patch:
  - Override `borrow()`, `borrowAtMaturity()`, `withdraw()`, and `redeem()` in `VerifiedMarket` and require `_requireAllowed(msg.sender)` before calling the parent implementation. For paths that transfer assets out, also require `_requireAllowed(receiver)`.
- Hardening follow-up:
  - Review every inherited owner/borrower path that depends on `spendAllowance(...)` or owner-only checks, including `withdrawAtMaturity`.
  - Add regression tests that isolate `msg.sender`, `owner` / `borrower`, and `receiver` separately instead of combining them in the same address.

## 7. Submission Notes
- Duplicate risk:
  - Lower on the public surface than it first looked. I did not find an obvious match in the official public audits or the public `main` test suite.
- Known-issue check:
  - I did not find this behavior documented in the public `main` tests or contract comments.
  - I completed a public-audit sweep of the PDFs linked from [Exactly audits](https://docs.exact.ly/security/audits) and found no public note matching this delegated-execution revocation bypass.
  - The October 2025 ABDK audit appears to assume `VerifiedMarket` borrow paths are guarded, which is consistent with this bug being subtle rather than already disclosed.
  - The public repo history shows Exactly explicitly attempted to firewall these surfaces in October 2025, but only covered borrower/owner allowlisted checks, not revoked delegated spenders.
- Open questions:
  - The clean-clone PoC validated both delegated `borrow` and delegated `withdraw`.
  - I would attach [exactly-verifiedmarket-bypass-poc.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/reports/exactly-verifiedmarket-bypass-poc.sol) and the clean-clone JSON result with the submission if the platform allows attachments.
