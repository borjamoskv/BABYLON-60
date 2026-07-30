# Title
Disallowed delegate can keep borrowing from and withdrawing from Base `VerifiedMarket` after firewall revocation

# Summary
On Exactly's Base verified markets, a delegate that was previously approved by an allowed user can keep using that delegation after the delegate is removed from the firewall allowlist. The root cause is that `VerifiedMarket` leaves several allowance-driven inherited paths without a current-caller firewall check.

On the validated public-main code path:
- delegated `borrow()` and `borrowAtMaturity()` validate only the `borrower`, not `msg.sender` or `receiver`,
- delegated `withdraw()` relies on owner allowance and shortfall checks but does not require the spender to remain allowlisted.

This lets a non-allowed attacker continue operating a verified market after revocation, both by creating debt for an allowed victim and by draining an allowed owner's withdrawable assets.

# Scope
- Program: [Exactly](https://immunefi.com/bug-bounty/exactly/)
- Scope page: [Exactly scope](https://immunefi.com/bug-bounty/exactly/scope/)
- Resources page: [Exactly resources](https://immunefi.com/bug-bounty/exactly/resources/)
- Relevant scoped asset:
  - Base `MarketUSDC` proxy: [MarketUSDC.json](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/deployments/base/MarketUSDC.json#L2)
  - Base `MarketUSDC` implementation metadata: [MarketUSDC_Implementation.json](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/deployments/base/MarketUSDC_Implementation.json#L3124)

# Severity
High

# Vulnerable Code
- Verified-market intent: [VerifiedMarket.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/verified/VerifiedMarket.sol#L7)
- Floating borrow path: [Market.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/Market.sol#L70)
- Fixed borrow path: [Market.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/Market.sol#L215)
- Floating withdraw path: [Market.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/Market.sol#L726)
- Fixed withdraw path uses owner allowance only: [Market.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/Market.sol#L298)
- Borrow validation only checks borrower: [VerifiedAuditor.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/verified/VerifiedAuditor.sol#L35)
- Delegated allowance survives revocation unless explicitly revoked: [Market.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/Market.sol#L857)

# Root Cause
`VerifiedMarket` selectively overrides some functions and adds allowlist checks, but it leaves privileged allowance-driven actions inherited from `Market`. In the inherited implementation:

1. `spendAllowance(owner_or_borrower, amount)` authorizes delegated execution based on stale market approval.
2. `borrow()` and `borrowAtMaturity()` validate only the `borrower`.
3. `withdraw()` validates owner shortfall, not spender allowlisted status.
4. Asset transfers still go to attacker-controlled receivers.

Because the delegate caller is not checked against the firewall on those paths, a delegate removed from the allowlist can continue using stale approval previously granted by an allowed user.

# Impact
This is an authorization bypass with financial impact, not just a compliance inconsistency.

An attacker can:
- stay operational on a verified market after allowlist removal,
- open debt in the victim's name through delegated borrowing,
- route borrowed assets to the attacker's address,
- drain an allowed owner's withdrawable assets through delegated withdrawal,
- push the victim toward liquidation and collateral loss.

The victim does not need to approve any new action after revocation. A stale preexisting allowance is enough.

# Proof of Concept
## Preconditions
1. Victim `BOB` is allowlisted.
2. Victim previously approved `attacker` as delegate on the verified market.
3. For the borrow branch, `BOB` has enough collateral / liquidity to borrow from the verified market.
4. For the withdraw branch, `BOB` has withdrawable balance on the verified market.
5. `attacker` is later removed from the firewall allowlist.

## Reproduction
Borrow branch:
1. `BOB` deposits collateral and enters the collateral market.
2. `BOB` approves `attacker` on the verified borrow market.
3. The firewall removes `attacker` from the allowlist.
4. `attacker` calls `borrow(1 ether, attacker, BOB)`.
5. Borrowed assets are transferred to `attacker`, while debt is assigned to `BOB`.

Withdraw branch:
1. `BOB` holds withdrawable balance on the verified market.
2. `BOB` approves `attacker` on that market.
3. The firewall removes `attacker` from the allowlist.
4. `attacker` calls `withdraw(assets, attacker, BOB)`.
5. Assets are transferred to `attacker` even though `attacker` is no longer allowed.

## Local Validation
I executed a temporary Foundry PoC against a clean public clone of `exactly/protocol` `main` at commit `c62bf4c` and captured machine-readable output.

- Command: `forge test --match-contract VerifiedMarketBypassPoC --json`
- Evidence summary: [exactly-verifiedmarket-borrow-bypass-evidence.md](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/reports/exactly-verifiedmarket-borrow-bypass-evidence.md)
- Parsed results:
  - `test_poc_disallowedDelegateCanBorrowForAllowedBorrower()` -> `Success`
  - `test_poc_disallowedDelegateCanWithdrawFromAllowedOwner()` -> `Success`

This confirms both delegated `borrow` and delegated `withdraw` remain usable after firewall revocation on current public `main`.

# Remediation
Override `borrow()`, `borrowAtMaturity()`, `withdraw()`, and `redeem()` in `VerifiedMarket` and require `_requireAllowed(msg.sender)` before calling the parent implementation. For paths that move assets to third parties, also require `_requireAllowed(receiver)`.

Also review `withdrawAtMaturity()` and any other inherited owner/borrower path that depends on `spendAllowance(...)` or owner-only checks.

Finally, add regression tests that independently vary:
- caller,
- owner / borrower,
- receiver

instead of testing only same-address combinations.

# Notes
- I did not find the issue documented in the public `main` test suite or comments.
- I scanned the 31 public PDFs in [exactly/audits](https://github.com/exactly/audits) for `VerifiedMarket`, `VerifiedAuditor`, `NotAllowed`, `firewall`, and `allowlist` and did not find a public finding matching this stale-delegation bypass.
- The only direct verified-market hit was [ABDK Protocol Update (Oct-25)](https://raw.githubusercontent.com/exactly/audits/main/ABDK%20Protocol%20Update%20(Oct-25).pdf), which describes `VerifiedMarket` as if transfer, borrow, repay, and withdraw paths were guarded by allowedness checks.
- That public audit language strengthens the case that this is a real authorization gap, not an intended scope carve-out.
- The clean-clone validation sources matched the scoped local target exactly on `VerifiedMarket.sol`, `VerifiedAuditor.sol`, and `Market.sol`.
- The public repo history also strengthens intent: on October 16, 2025, Exactly merged [✨ verified: firewall borrows](https://github.com/exactly/protocol/commit/0e5281e3b0d656ca5581fcfa3c29f5ff2906f9ac) and [✨ verified: firewall redeem and withdraw](https://github.com/exactly/protocol/commit/bb51de1981c039a694975cfae3bc1f777d86c177), but those public diffs only covered borrower/owner allowlisted checks, not revoked delegated spenders.
