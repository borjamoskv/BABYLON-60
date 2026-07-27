# Submission Manifest: HIGH: Disallowed delegate can keep borrowing from and withdrawing from Base VerifiedMarket after firewall revocation
ID: exactly_verifiedmarket_bypass
Status: VERIFIED
Severity: High

## Vulnerability

On Exactly's Base verified markets, a delegate previously approved by an allowed user can continue using that delegation after being removed from the firewall allowlist. `VerifiedMarket.sol` fails to override inherited `Market.sol` functions like `borrow()`, `borrowAtMaturity()`, and `withdraw()` to include `msg.sender` or `receiver` allowlist checks.

**Root Cause:** `contracts/verified/VerifiedMarket.sol` inherits from `Market.sol` but does not override `borrow` and `withdraw` entry points. `VerifiedAuditor.sol:checkBorrow()` only validates `onlyAllowed(borrower)`, ignoring the caller (`msg.sender`) and the `receiver`.

**Impact:** Authorization bypass. A revoked delegate can create debt for an allowed victim and drain their withdrawable assets using stale approvals.

**PoC:** Foundry test `VerifiedMarketBypassPoC` against commit `c62bf4c` confirms:
1. `test_poc_disallowedDelegateCanBorrowForAllowedBorrower()` -> Success
2. `test_poc_disallowedDelegateCanWithdrawFromAllowedOwner()` -> Success

**Contract:** VerifiedMarket (Base Mainnet Implementation)

[FORENSIC DATA ATTACHED]

