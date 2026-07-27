# Triage Notes — Exactly VerifiedMarket Delegate Bypass

## Recommended Severity Position

Primary ask: `Critical`

Reason:
- Exactly's current scope lists `Direct theft of any user funds, whether at-rest or in-motion, other than unclaimed yield` as `Critical`.
- The validated `withdraw()` branch lets a revoked delegate transfer an allowlisted owner's deposited assets to an attacker-controlled receiver using stale approval after firewall revocation.
- Those are user funds at rest in the market, not unclaimed yield.

Fallback ask: `High`

Reason:
- Exactly's current scope lists `Substantial generation of bad debt on the protocol` as `High`.
- The validated `borrow()` branch lets a revoked delegate create debt in an allowlisted victim's name and route assets to the attacker.

## Why This Should Not Be Dismissed As Intended

- `VerifiedMarket` is explicitly documented as a market that "can only be used by allowed accounts".
- The public repo history shows Exactly intentionally trying to firewall these surfaces:
  - [0e5281e](https://github.com/exactly/protocol/commit/0e5281e3b0d656ca5581fcfa3c29f5ff2906f9ac): `verified: firewall borrows`
  - [bb51de1](https://github.com/exactly/protocol/commit/bb51de1981c039a694975cfae3bc1f777d86c177): `verified: firewall redeem and withdraw`
  - [1c5e295](https://github.com/exactly/protocol/commit/1c5e295016a4c358883280accb1a558869c9513b): `verified: firewall withdraw at maturity`
- Those public changes cover borrower/owner checks, but not revoked delegated spenders. The PoC lands precisely in that gap.

## Likely Reviewer Objections

### "The victim approved the delegate, so this is allowed behavior"

Response:
- The approval predates firewall revocation.
- The whole purpose of the verified market and firewall model is that non-allowlisted accounts should not keep operating after revocation.
- If stale delegated approvals survive revocation, the verified-market access boundary is not actually enforced for delegated paths.

### "This is just griefing"

Response:
- The `withdraw()` branch is not griefing. It is direct user-fund extraction to an attacker-controlled receiver.
- The `borrow()` branch is not mere griefing either because it can generate protocol bad debt and force liquidation risk while sending assets to the attacker.

### "This needs privileged access"

Response:
- The attacker only needs to have been previously approved by the victim on-market, then later revoked by the firewall.
- No leaked keys, governance role, admin role, or privileged contract access is required.

### "The public tests already cover this"

Response:
- Public `main` tests cover borrower/owner allowlisted cases, not revoked delegated spenders.
- The clean-clone PoC on public `main` validated both branches successfully.

## Current Scope References

Exactly scope, last updated March 19, 2026:
- Asset in scope: `MarketUSDC`
- `Critical`: direct theft of user funds
- `High`: substantial generation of bad debt on the protocol
- Out of scope: griefing

Source:
- [Exactly scope](https://immunefi.com/bug-bounty/exactly/scope/)
