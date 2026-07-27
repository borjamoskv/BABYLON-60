# Immunefi Fields — Exactly VerifiedMarket Delegate Bypass

## Title
Disallowed delegate can keep borrowing from and withdrawing from Base `VerifiedMarket` after firewall revocation

## Affected Asset
Base `MarketUSDC` verified market proxy in scope.

## Vulnerability Summary
Exactly's Base `VerifiedMarket` is intended to be usable only by allowlisted accounts, but stale market approvals remain exploitable after firewall revocation on inherited delegated paths.

On current public `main`, a revoked delegate can still:
- call `borrow()` / `borrowAtMaturity()` on behalf of an allowlisted borrower because only the `borrower` is firewall-checked,
- call `withdraw()` on behalf of an allowlisted owner because the path relies on owner shortfall plus allowance and does not require the delegated spender to remain allowlisted.

This means a non-allowed account can continue operating a verified market after revocation and can both create debt for a victim and extract assets to an attacker-controlled receiver.

## Root Cause
`VerifiedMarket` selectively overrides some flows with `_requireAllowed(...)` checks, but leaves allowance-driven inherited paths incompletely covered.

- `borrow()` and `borrowAtMaturity()` validate only the `borrower`.
- `withdraw()` validates owner shortfall, not delegated spender allowlisted status.
- stale approval remains consumable through `spendAllowance(...)` after firewall revocation.

## Impact
This is an authorization bypass with direct economic impact.

- A revoked delegate can create debt in an allowlisted victim's name and route borrowed funds to itself.
- A revoked delegate can withdraw an allowlisted owner's assets to itself.
- The victim does not need to approve any new action after revocation.
- Borrow victims can be pushed toward liquidation and collateral loss.

## Steps To Reproduce
Borrow branch:
1. Allowlisted user `BOB` deposits collateral and enters the collateral market.
2. `BOB` approves `attacker` on the verified borrow market.
3. Firewall removes `attacker` from the allowlist.
4. `attacker` calls `borrow(1 ether, attacker, BOB)`.
5. Assets are transferred to `attacker` and debt is assigned to `BOB`.

Withdraw branch:
1. Allowlisted user `BOB` holds withdrawable balance on the verified market.
2. `BOB` approves `attacker` on that market.
3. Firewall removes `attacker` from the allowlist.
4. `attacker` calls `withdraw(10 ether, attacker, BOB)`.
5. Assets are transferred to `attacker` and `BOB`'s market balance is reduced.

## Validation
Validated against a clean public clone of `exactly/protocol` `main` at commit `c62bf4c`.

- `test_poc_disallowedDelegateCanBorrowForAllowedBorrower()` -> `Success`
- `test_poc_disallowedDelegateCanWithdrawFromAllowedOwner()` -> `Success`

Supporting artifacts:
- Long report: [exactly-verifiedmarket-borrow-bypass.md](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/reports/exactly-verifiedmarket-borrow-bypass.md)
- Evidence: [exactly-verifiedmarket-borrow-bypass-evidence.md](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/reports/exactly-verifiedmarket-borrow-bypass-evidence.md)
- Parsed results: [exactly-verifiedmarket-borrow-bypass-results.json](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/reports/exactly-verifiedmarket-borrow-bypass-results.json)
- PoC source: [exactly-verifiedmarket-bypass-poc.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/reports/exactly-verifiedmarket-bypass-poc.sol)

## Key References
- Verified-market intent: [VerifiedMarket.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/verified/VerifiedMarket.sol#L7)
- Floating borrow path: [Market.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/Market.sol#L70)
- Fixed borrow path: [Market.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/Market.sol#L215)
- Floating withdraw path: [Market.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/Market.sol#L726)
- Fixed withdraw path: [Market.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/Market.sol#L298)
- Borrower-only firewall check: [VerifiedAuditor.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/verified/VerifiedAuditor.sol#L35)
- Stale delegated allowance consumption: [Market.sol](/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol-src/contracts/Market.sol#L857)
- Public commit intent on borrows: [0e5281e](https://github.com/exactly/protocol/commit/0e5281e3b0d656ca5581fcfa3c29f5ff2906f9ac)
- Public commit intent on withdraw/redeem: [bb51de1](https://github.com/exactly/protocol/commit/bb51de1981c039a694975cfae3bc1f777d86c177)

## Severity Rationale
High. This is attacker-reachable authorization bypass on an in-scope verified market with direct user-fund extraction and debt creation impact.
