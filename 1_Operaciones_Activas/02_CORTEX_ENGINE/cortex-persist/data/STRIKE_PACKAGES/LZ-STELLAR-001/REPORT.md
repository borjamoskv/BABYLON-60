---
vulnerability_id: "LZ-STELLAR-001"
project: "LayerZero"
platform: "Code4rena"
warden: "borja_moskv"
target_url: "https://code4rena.com/audits/2026-04-layerzero-stellar-endpoint"
severity: "High/Critical"
---

# Finding: Multi-user Fee Drain via Global Balance Refund

- **Severity**: Critical
- **Project**: LayerZero - Stellar Endpoint
- **Contract**: `EndpointV2` (`endpoint_v2.rs`)
- **Vulnerability Type**: Accounting Drift / Race Condition

## Summary
The `pay_messaging_fees` function in the `EndpointV2` contract calculates the technical native fee surplus by checking the contract's global token balance instead of tracking the specific amount supplied by the current transaction's sender. This allow an attacker to hijack the native tokens transferred by other users to the contract, claiming them as an "excess fee refund".

## Severity
**Critical**. An attacker can drain all unspent native fees transferred to the contract by other users. In a high-traffic environment, this results in significant capital loss for OApp protocols and their users.

## Vulnerability Detail
In `endpoint_v2.rs`, the `send` function (line 63) and `quote` function (line 45) rely on `pay_messaging_fees` to distribute native fees:

```rust
// line 256
let mut native_fee_supplied = native_token_client.balance(&this_contract);
```

The contract uses the global `balance()` of the contract to determine how much was "supplied" for the current `send` call. Since Stellar/Soroban does not have a native `msg.value` mechanism that automatically isolates funds per call, the contract assumes that whatever balance it has represents the fees for the current operation.

The issue arises in lines 270-272:
```rust
// Refund remaining native fees
if native_fee_supplied > 0 {
    native_token_client.transfer(&this_contract, refund_address, &native_fee_supplied);
}
```

If User B transfers 200 USDC to the contract (intended for their own upcoming `send` call) and User A (Attacker) immediately calls `send` with a minimal fee requirement, the contract will:
1. Detect a balance of `201` USDC.
2. Deduct only `1` USDC for User A's fee.
3. Refund the remaining `200` USDC (User B's funds) to User A's `refund_address`.

## Recommendation
The contract must track the exact amount supplied by the sender for the specific transaction. Since Soroban requires explicit authorization for transfers, a safer pattern is to use `transfer_from` from the sender to the contract within the `send` function itself, or to implement a rigorous "Balance Snapshot" mechanism that tracks the delta of the balance between the start and end of the `send` call (though this is still susceptible to race conditions within the same block if multiple `send` calls are batched by a single contract).

The most secure approach for Soroban is:
1. The `send` function takes the `native_fee` as an argument.
2. It calls `native_token_client.transfer_from(sender, &env.current_contract_address(), &native_fee)`.
3. It then distributes EXACTLY that amount, without relying on global balance checks.
