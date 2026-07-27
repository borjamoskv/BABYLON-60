# CORTEX Sovereign Intelligence — Target Isolation
> *Status: C5-REAL (Forensic Dossier)*
> *Target: `0x1Ad7C70B43387F7E8C4291640E1726EA6CCB0366` (Binance Exit Node)*

## 1. Operative Context
This document serves as the formal isolation of the Binance Exit Node associated with the ENS drainer network that attacked `0x5247299421A3Ff724c41582E5A44c6551d13` (borja.moskv.eth). 
This node is the critical chokepoint where the attacker crystallized stolen on-chain assets into fiat liquidity.

## 2. On-Chain Telemetry (C5-REAL)
- **Node Classification:** Centralized Exchange (CEX) Deposit Address (Binance).
- **Direct Linkage:** Received 0.10445 ETH directly from the Sweeper/Deployer node (`0x54ba52cbd043b0b2e11a6823a910360e31bb2544`).
- **KYC Status:** As a Binance deposit address, this node is definitively linked to a verified identity (KYC Level 2 minimum for crypto-to-fiat off-ramping).

## 3. Attack Vector Mapping
```mermaid
graph TD
    A[Victim: 0x5247...] -->|EIP-7702 / Permit2| B[Target Contract: 0xEeCA...]
    B -->|Asset Sweep| C[Sweeper: 0x54ba...]
    C -->|0.10445 ETH| D[Exit Node: 0x1Ad7... (Binance)]
    C -->|Aggregation| E[Master Consolidator: 0x0083...]
```

## 4. Execution Pipeline (Bug Bounty & Recovery)
To enforce capital recovery or attacker deanonymization, the following execution path is mandated:

1. **Subpoena Preparation:** Draft the formal blockchain forensic report linking the stolen ENS assets and `borja.moskv.eth` explicitly to the `0x1Ad7C70B43387F7E8C4291640E1726EA6CCB0366` deposit.
2. **Binance Global Law Enforcement Request:** Submit the forensic trace to the Binance Security Team (via the Law Enforcement Request system) requesting an immediate freeze of the user account linked to the deposit address.
3. **Asset Recovery Bounty:** Publish a 10% white-hat recovery bounty on Immunefi/X targeting the Master Deployer `0x701e13e8da8ef04cd40e92f21869932fe5e35555` with the threat of KYC disclosure.

> [!CAUTION]
> The latency between the attack and the Binance freeze request is the primary entropy sink. Immediate execution of the LE Request is required to prevent the attacker from withdrawing the off-ramped fiat.
