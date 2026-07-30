# Exactly VerifiedMarket Delegate Bypass

## Title
Disallowed delegate can keep borrowing from and withdrawing from Base `VerifiedMarket` after firewall revocation

## Program / Asset
- Program: [Exactly on Immunefi](https://immunefi.com/bug-bounty/exactly/)
- Scope: [Exactly scope](https://immunefi.com/bug-bounty/exactly/scope/)
- Resources: [Exactly resources](https://immunefi.com/bug-bounty/exactly/resources/)
- In-scope Base proxy: `MarketUSDC` at `0x61EDAcB54aA8a689013682529df8914C87692E4b`
- VerifiedMarket implementation in local deployment metadata: `0xB4B6d4E969001dccc6bF50c4f4bd394fb4Ed0b77`

## Summary
Exactly's Base `VerifiedMarket` is intended to be usable only by allowlisted accounts, but stale market approvals remain exploitable after firewall revocation on inherited delegated paths.

On public `main` validated at commit `c62bf4ce53f26ea0ca8d7ece2732c84f2b2bfaef`, a revoked delegate can still:
- call `borrow()` / `borrowAtMaturity()` on behalf of an allowlisted borrower because only the `borrower` is firewall-checked,
- call `withdraw()` on behalf of an allowlisted owner because the path relies on owner shortfall plus allowance and does not require the delegated spender to remain allowlisted.

This allows a non-allowlisted account to continue operating a verified market after revocation and either create debt for a victim or extract assets to an attacker-controlled receiver.

## Root Cause
`VerifiedMarket` selectively overrides some flows with `_requireAllowed(...)` checks, but leaves allowance-driven inherited paths incompletely covered.

- `borrow()` and `borrowAtMaturity()` validate only the `borrower`.
- `withdraw()` validates owner shortfall, not delegated spender allowlisted status.
- stale approval remains consumable through `spendAllowance(...)` after firewall revocation.

## Impact
- A revoked delegate can create debt in an allowlisted victim's name and route borrowed funds to itself.
- A revoked delegate can withdraw an allowlisted owner's assets to itself.
- The victim does not need to approve any new action after revocation.
- Borrow victims can be pushed toward liquidation and collateral loss.

## Reproduction
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
Validated against a clean public clone of `exactly/protocol` `main` at commit `c62bf4ce53f26ea0ca8d7ece2732c84f2b2bfaef`.

- `test_poc_disallowedDelegateCanBorrowForAllowedBorrower()` -> `Success`
- `test_poc_disallowedDelegateCanWithdrawFromAllowedOwner()` -> `Success`

Supporting local artifacts:
- Parsed results JSON: `exactly-verifiedmarket-borrow-bypass-results.json`
- PoC source: `exactly-verifiedmarket-bypass-poc.sol`

## Code References
- Verified-market intent:
  - [VerifiedMarket.sol#L7](https://github.com/exactly/protocol/blob/c62bf4ce53f26ea0ca8d7ece2732c84f2b2bfaef/contracts/verified/VerifiedMarket.sol#L7)
- Borrow paths:
  - [Market.sol#L70-L99](https://github.com/exactly/protocol/blob/c62bf4ce53f26ea0ca8d7ece2732c84f2b2bfaef/contracts/Market.sol#L70-L99)
  - [Market.sol#L215-L288](https://github.com/exactly/protocol/blob/c62bf4ce53f26ea0ca8d7ece2732c84f2b2bfaef/contracts/Market.sol#L215-L288)
- Withdraw paths:
  - [Market.sol#L298-L320](https://github.com/exactly/protocol/blob/c62bf4ce53f26ea0ca8d7ece2732c84f2b2bfaef/contracts/Market.sol#L298-L320)
  - [Market.sol#L726-L743](https://github.com/exactly/protocol/blob/c62bf4ce53f26ea0ca8d7ece2732c84f2b2bfaef/contracts/Market.sol#L726-L743)
- Borrower-only firewall check:
  - [VerifiedAuditor.sol#L38-L41](https://github.com/exactly/protocol/blob/c62bf4ce53f26ea0ca8d7ece2732c84f2b2bfaef/contracts/verified/VerifiedAuditor.sol#L38-L41)
- Existing explicit guarded pattern in VerifiedMarket:
  - [VerifiedMarket.sol#L130-L164](https://github.com/exactly/protocol/blob/c62bf4ce53f26ea0ca8d7ece2732c84f2b2bfaef/contracts/verified/VerifiedMarket.sol#L130-L164)
- Stale delegated allowance consumption:
  - [Market.sol#L857-L861](https://github.com/exactly/protocol/blob/c62bf4ce53f26ea0ca8d7ece2732c84f2b2bfaef/contracts/Market.sol#L857-L861)

## Public Intent Evidence
- [✨ verified: firewall borrows](https://github.com/exactly/protocol/commit/0e5281e3b0d656ca5581fcfa3c29f5ff2906f9ac)
  - Added borrower-only firewall checks and borrower-focused tests, but no delegated-spender or receiver checks.
- [✨ verified: firewall redeem and withdraw](https://github.com/exactly/protocol/commit/bb51de1981c039a694975cfae3bc1f777d86c177)
  - Added owner-oriented shortfall protections and owner/sender tests, but no delegated-spender allowlist check.
- [✨ verified: firewall withdraw at maturity](https://github.com/exactly/protocol/commit/1c5e295016a4c358883280accb1a558869c9513b)
  - Added owner-only check for `withdrawAtMaturity`, reinforcing the intended firewall policy.

These public commits support the interpretation that verified-market access was intended to be firewall-restricted, but the delegated spender surface remained incompletely covered.

## Public Audit Context
- I scanned the 31 public PDFs in [exactly/audits](https://github.com/exactly/audits) for `VerifiedMarket`, `VerifiedAuditor`, `NotAllowed`, `firewall`, and `allowlist`.
- I did not find a public finding matching this stale-delegation bypass.
- The only direct verified-market hit was [ABDK Protocol Update (Oct-25)](https://raw.githubusercontent.com/exactly/audits/main/ABDK%20Protocol%20Update%20(Oct-25).pdf), which describes `VerifiedMarket` as if transfer, borrow, repay, and withdraw paths were guarded by allowedness checks.

## Remediation
- Override `borrow()`, `borrowAtMaturity()`, `withdraw()`, and `redeem()` in `VerifiedMarket` and require `_requireAllowed(msg.sender)` before calling the parent implementation.
- For paths that move assets to third parties, also require `_requireAllowed(receiver)`.
- Review every inherited owner/borrower path that depends on `spendAllowance(...)` or owner-only checks, including `withdrawAtMaturity`.
- Add regression tests that vary `msg.sender`, `owner` / `borrower`, and `receiver` independently.
