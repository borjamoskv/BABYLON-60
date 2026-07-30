# Evidence Summary — Exactly VerifiedMarket Delegate Bypass

**Date**: 2026-04-08
**Repo**: `/tmp/exactly-protocol-clean`
**Ref**: `c62bf4c`
**Command**: `forge test --match-contract VerifiedMarketBypassPoC --json`
**Raw output file**: `/tmp/exactly-clean-bypass.json`

## Parsed Results
- `test_poc_disallowedDelegateCanBorrowForAllowedBorrower()` -> `Success`
- `test_poc_disallowedDelegateCanWithdrawFromAllowedOwner()` -> `Success`

## Interpretation
- Both exploitably reachable paths validated on current public `main`: delegated `borrow` and delegated `withdraw`.
- A disallowed delegate can still open debt for an allowed borrower and receive borrowed assets if the borrower granted allowance before the delegate was removed from the firewall allowlist.
- A disallowed delegate can also still withdraw an allowed owner's assets to an attacker-controlled receiver after revocation.
- This matches the static call-path review:
  - [Market.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/Market.sol#L70)
  - [Market.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/Market.sol#L726)
  - [VerifiedAuditor.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/verified/VerifiedAuditor.sol#L35)
  - [Market.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/Market.sol#L857)

## Public Audit Sweep
- Audit index used: [Exactly audits](https://docs.exact.ly/security/audits)
- Public audit repo used: [exactly/audits](https://github.com/exactly/audits)
- Sweep method:
  - Downloaded and text-scanned the 31 public PDF reports in `exactly/audits`.
  - Searched for `VerifiedMarket`, `VerifiedAuditor`, `NotAllowed`, `firewall`, and `allowlist`.
- Result:
  - No public finding matched stale delegated execution after firewall revocation.
  - The two April 2024 "Installments Router and New Market Roles" audits did not surface direct hits for those identifiers.
  - The only direct verified-market hit was [ABDK Protocol Update (Oct-25)](https://raw.githubusercontent.com/exactly/audits/main/ABDK%20Protocol%20Update%20(Oct-25).pdf).
- Relevant public context:
  - The October 2025 ABDK report describes `VerifiedMarket` as if transfer, borrow, repay, and withdraw operations are guarded by allowedness checks.
  - That description is inconsistent with the current delegated `borrow` and delegated `withdraw` paths validated in the clean-clone PoC, where the disallowed delegate remains able to operate via stale approval.

## Public Commit Intent
- On October 16, 2025, Exactly merged [✨ verified: firewall borrows](https://github.com/exactly/protocol/commit/0e5281e3b0d656ca5581fcfa3c29f5ff2906f9ac).
- That public change added verified-market tests only for `borrower` allowedness and changed `VerifiedAuditor.checkBorrow(...)` to reject disallowed borrowers.
- It did not add a `msg.sender` allowlist check on `borrow()` or `borrowAtMaturity()`, and it did not add receiver checks there either.
- On October 16, 2025, Exactly also merged [✨ verified: firewall redeem and withdraw](https://github.com/exactly/protocol/commit/bb51de1981c039a694975cfae3bc1f777d86c177).
- That public change made `VerifiedAuditor.checkShortfall(...)` reject disallowed owners and added tests for sender/owner allowlisted behavior on `withdraw()` and `redeem()`.
- It still did not add a delegated-spender allowlist check to `withdraw()` or `redeem()`.
- These commits are useful evidence of intended policy: verified-market access was meant to be firewall-restricted, but the delegated spender surface remained incompletely covered.

## Notes
- The clean-clone source used for validation matched the scoped local target exactly on the relevant files:
  - [VerifiedMarket.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/verified/VerifiedMarket.sol)
  - [VerifiedAuditor.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/verified/VerifiedAuditor.sol)
  - [Market.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/Market.sol)
- The temporary PoC contract used during validation is removed after the run and was not kept in the clean clone.
- The JSON artifact was preserved in `/tmp/exactly-clean-bypass.json` for immediate inspection during this session.
- A stable copy of the PoC source is saved at [exactly-verifiedmarket-bypass-poc.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/reports/exactly-verifiedmarket-bypass-poc.sol).
