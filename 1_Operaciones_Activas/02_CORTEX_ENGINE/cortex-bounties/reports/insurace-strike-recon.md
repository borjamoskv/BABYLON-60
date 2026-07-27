# InsurAce Protocol Forensic Reconnaissance

## Target Metadata
- **Protocol**: InsurAce (V2)
- **Status**: Live (Ethereum, BSC, Polygon, Avalanche)
- **Primary Contract (Staking)**: `0x7D8C3F38C8545a770D57c8043d54e5715B1C584E` (Ethereum)
- **Audit Ledger**: Ouroboros-INSUR-01

## Initial Attack Vectors
1. **StakingV2 Reward Calculation**: Possible rounding errors in high-exergy yield multipliers.
2. **Cover Purchase Validation**: Logic bypass in the `CoverPurchase` contract (`0x1d22...Aa5D`) regarding collateral ratios.
3. **Emergency Exit Paths**: Analysis of the `StakingV2Controller` withdrawal logic during simulated liquidity crunches.

## Notarized Telemetry
- Exergy Load: 1.42 GW
- Confidence: C5-REAL (Pending source code ingestion)
