# Intuition Bug Bounty

- [Read our guidelines for more details](https://docs.code4rena.com/bounties)
- Submit findings [using the C4 form](https://code4rena.com/bounties/intuition/submit)

## Award levels
| Risk Score |  Payout |
|------------|---------|
| Critical | Up to $100,000 in USDC (depending upon severity and amount of funds at risk, at discretion of Intuition team) |
| High| &#36;3,000 - &#36;5,000 in USDC |
| Medium| &#36;1,000 - &#36;2,500 in USDC |
| Low | &#36;250 - &#36;500 in USDC |

## Background on Intuition

### What is Intuition?

Intuition is an Ethereum-based attestation protocol that makes it easy to create, explore, and incentivize verifiable information. It focuses on a flexible data layer for Web3 where many-to-one relationships between identities and claims are supported and token-based incentive mechanics encourage high-quality data creation. Intuition's flagship app, Portal, enables users to create, navigate, aggregate, and curate attestations about people and entities in the Web3 ecosystem.

### How does it work (high-level)?

- Intuition creates unique identifiers for people/organizations/concepts/etc (known as "atoms", or "identities" in Portal), and semantic triple claims constructred from those identifiers (known as "triples", or "claims" in Portal) on-chain.
- Users can deposit into the "MultiVault" contract to support or oppose atoms and triples. The value of the user's deposit increases or decreases when subsequent users deposit or withdraw from the same vaults, according to various bonding curves.
- Users can stake TRUST to receive protocol emissions each epoch, depending upon their personal utilitzation of the Multivault and the system utilization of all users combined.
- All smart contracts are deployed to the Intuition Network, an EVM-compatible L3, manage the attestation and incentive logic, using $TRUST token as the native currency

### Further technical resources & links

- **Website:** https://intuition.systems
- **Documentation:** https://www.docs.intuition.systems/
- **Whitepaper:** https://cdn.prod.website-files.com/65cdf366e68587fd384547f0/66ccda1f1b3bbf2d30c4f522_intuition_whitepaper.pdf
- **Discord Community:** https://discord.gg/0xintuition
- **X:** https://x.com/0xIntuition

# Scope & Severity Criteria

## Severity matrix:

| Severity level | Description / Examples |
|---|---|
| **Critical** |  Systemic user fund loss or freezing; unauthorized manipulation of critical contract parameters (timelock, pausability); mass-scale unauthorized mint/burn of multivault shares; protocol insolvency. |
| **High** | Direct theft of individual user funds; long-term freezing of individual user funds; ways to avoid expected fees. |
| **Medium** | Economic loss not involving direct on-chain asset theft (short-term freezing, gas griefing, unbounded gas, essential functionality temporarily unusable); theft of unclaimed rewards/yield. |
| **Low** | Behavioral differences from intended behavior or documentation where no funds are at risk; technical issues that lead to impersonation of Intuition team communications; minor logic/documentation mismatches; non-critical edge cases. |

## Smart Contracts and Repos in Scope

- **Repos:**
  - https://github.com/0xIntuition/intuition-contracts-v2
- **Smart Contract Deployments:** https://www.docs.intuition.systems/docs/developer-tools/contracts/deployments
- **Mainnet Deployed Contract Commit:** `20181c162502da226ca25c31aef47872369212c9`

## Out-of-Scope

### Known Issues

Bug reports covering previously-discovered bugs (listed below) are not eligible for a reward within this program. This includes known issues that the project is aware of but has consciously decided not to “fix”, necessary code changes, or any implemented operational mitigating procedures that can lessen potential risk. Every issue opened in the repo, closed PRs, previous contests and audits are out of scope.

All issues submitted by wardens to the Intuition bounty will be added to [this repo](https://github.com/code-423n4/intuition-bug-bounty/issues?q=is%3Aissue%20state%3Aclosed) once they have been reviewed by the sponsors. These are considered known issues and are out-of-scope for bounty rewards.

- Any issues already documented in previously opened issues, previous audits, or otherwise publicly-known vulnerabilities are **out-of-scope** for bounty rewards (reports duplicating those issues will not be paid).
- This includes issues intentionally left as design choices or mitigated operationally by the team.

### Previous audits

Any findings already reported in previous audits are not eligible for new rewards.
- https://www.docs.intuition.systems/docs/developer-tools/audit-reports

[Intuition concluded a Code4rena competitive audit on Monday, March 9, 2026.](https://code4rena.com/audits/2026-03-intuition) Judging is currently in progress, and findings will be published once complete.
Any vulnerabilities identified during the competitive audit are considered known issues and are ineligible for bounty rewards, even if the audit results have not yet been publicly released. This includes:

- Issues currently under review by judges
- Findings awaiting remediation
- Any vulnerability similar in nature to those discovered during the audit

Once the competitive audit results are published, they will be linked here for full transparency. 

If you're unsure whether your finding may have been covered in the audit, we encourage you to submit anyway; we'll review all submissions and provide feedback on eligibility.

### Specific types of issues excluded

- Informational findings (no economic or security impact)
- Design choices documented and accepted by the protocol (e.g., permissioned/centralized upgradeability) unless they lead to a concrete exploit scenario
- Front-end only user errors or UX mistakes that do not lead to contract-level risk
- Rounding differences that have no economic impact
- Known gas consumption characteristics (unless they enable an exploit)

# Additional Context

### Miscellaneous
Employees of Intuition and their family members are ineligible for bounties.

Reward amounts may be displayed using a dollar sign for simplicity, but the underlying valuation is based on a USD-pegged digital asset such as USDC. Because the displayed figure reflects a USD reference value rather than a fiat currency payment, the final amount delivered in the corresponding token may differ slightly at the time of payout.
