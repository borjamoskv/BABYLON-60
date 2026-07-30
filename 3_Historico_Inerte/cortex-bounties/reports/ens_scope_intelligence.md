# ENS PROTOCOL — SOVEREIGN SCOPE INTELLIGENCE
> *Intelligence Extraction — C5-REAL — Immunefi Audit Program*

## 1. SMART CONTRACTS (P0 TARGETS)
*Source: ENS Contract Deployments Wiki (Mainnet Focus)*

| Contract Name | C5-REAL Target Address |
| :--- | :--- |
| **ENSRegistry** | `0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e` |
| **ETHRegistrarController** | `0x59E16fcCd424Cc24e280Be16E11Bcd56fb0CE547` |
| **BaseRegistrarImplementation** | `0x57f1887a8BF19b14fC0dF6Fd9B2acc9Af147eA85` |
| **NameWrapper** | `0xD4416b13476343Fd98214963Cf8Bb6Cf65279612` |
| **PublicResolver** | `0xF29100983E058B709F3D539b0c765937B804AC15` |
| **UniversalResolver** | `0xED73a03F19e8D849E44a39252d222c6ad5217E1e` |
| **ReverseRegistrar** | `0xa58E81fe9b61B5c3fE2AFD33CF304c454AbFc7Cb` |
| **DNSSECImpl** | `0x0fc3152971714E5ed7723FAFa650F86A4BaF30C5` |
| **DNSRegistrar** | `0xB32cB5677a7C971689228EC835800432B339bA2B` |
| **Root** | `0xaB528d626EC275E3faD363fF1393A41F581c5897` |
| **ExponentialPremiumPriceOracle** | `0x7542565191d074cE84fBfA92cAE13AcB84788CA9` |
| **StaticMetadataService** | `0x3A368e3D5F19aF3DE594A9fC2CFfc6e256a616c7` |

## 2. WEB & APP VECTORS
1.  **ENS Landing Page:** `https://ens.domains/` (Source: `ensdomains/ensdomains-landing`)
2.  **ENS App:** `https://app.ens.domains/` (Source: `ensdomains/ens-app-v3`)
3.  **ENS Metadata Service:** `https://metadata.ens.domains/` (Source: `ensdomains/ens-metadata-service`)
4.  **Metadata Service Docs:** `https://metadata.ens.domains/docs`
5.  **Thorin Design System:** `https://thorin.ens.domains/` (Source: `ensdomains/ens-thorin`)
6.  **Contract Deployments Wiki:** `ensdomains/ens-contracts/wiki/ENS-Contract-Deployments`

## 3. ENTROPY PURGE (OUT-OF-SCOPE RULES)
*Note: Any submission hitting these vectors will be flagged as Entropy (C4) and rejected by Immunefi.*

**A. Structural / Exogenous Exclusions:**
- **Archival Content:** Takeovers of broken links on inactive sources (e.g., meeting minutes).
- **External DAO Assets:** DAO-funded products not explicitly listed.
- **Stablecoin Depegging:** Vulnerabilities relying on external stablecoin failure.
- **Known Issues:** Previously disclosed vulnerabilities or those in official audit reports.

**B. Privileged & Contextual Constraints:**
- **Privileged Access:** Bugs requiring unauthorized use of governance/strategist keys without secondary escalation.
- **Physical Proximity:** Attacks requiring physical device access or local network presence.
- **Social Engineering:** Phishing, spear-phishing against employees or users.
- **Test Environments:** Impacts on test/config files.

**C. Web/App specific Exclusions (Standard Low-Exergy):**
- **Injections:** Reflected plain text injection (if no HTML/JS execution).
- **Self-XSS:** XSS requiring user self-injection.
- **Low Impact Vectors:** CSRF without state modification, missing security headers (e.g., `X-FRAME-OPTIONS`) without PoC, SSL/TLS deviations.
- **Volumetric:** Spam/DDoS attacks requiring mass requests without a core logic flaw.
- **UI/UX:** Minor graphical glitches or general "best practice" recommendations.
- **Non-sensitive Leaks:** Etherscan, Infura, or other non-critical API keys.

---
📝 *Status: C5-REAL | Extracted via AGENT-BROWSER-OMEGA*
