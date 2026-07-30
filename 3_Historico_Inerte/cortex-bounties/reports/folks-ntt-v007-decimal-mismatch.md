# Folks Finance NTT — Inbound Decimal Mismatch Vulnerability

## Bug Description

The `NttManager._handle_message()` function on the inbound cross-chain path trusts the `from_decimals` field extracted directly from the Wormhole VAA payload **without validating it against the `peer_decimals` configured via `set_ntt_manager_peer()`**.

This creates an asymmetry between the outbound and inbound precision handling:

### Outbound (properly validated):
```python
# NttManager.py L462-467
def _trim_transfer_amount(self, amount, to_decimals):
    from_decimals = self._get_asset_decimals()
    trimmed_amount = TrimmedAmountLib.trim(amount, from_decimals, to_decimals)
    new_amount = TrimmedAmountLib.untrim(trimmed_amount, from_decimals)
    assert amount == new_amount, err.TRANSFER_AMOUNT_HAS_DUST  # ← round-trip check
    return trimmed_amount
```

### Inbound (NO validation):
```python
# NttManager.py L414-453
def _handle_message(self, message_digest, message):
    ntt_manager_peer = self.get_ntt_manager_peer(message.source_chain_id)
    assert message.source_address == ntt_manager_peer.peer_contract  # ← peer address only

    payload = message.payload.bytes
    # ...
    from_decimals = ARC4UInt8(op.btoi(op.extract(payload, index, 1)))  # ← FROM PAYLOAD
    from_amount = ARC4UInt64(op.extract_uint64(payload, index))

    trimmed_amount = TrimmedAmount(from_amount, from_decimals)  # ← trusts payload decimals
    untrimmed_amount = self._untrim_transfer_amount(trimmed_amount)  # ← scale up using payload decimals
    # NO validation that from_decimals == ntt_manager_peer.decimals
```

The `ntt_manager_peer.peer_decimals` is available (stored when peer was configured) but is **never checked** on the inbound path. The `from_decimals` in the payload is whatever the source chain's `_transfer` method encoded.

## Impact

If a registered peer's NttManager on the source chain is compromised, upgraded, or misconfigured, an attacker can craft a Wormhole message where `from_decimals` differs from the expected `peer_decimals`. Through the `TrimmedAmountLib.scale()` function:

```python
# TrimmedAmountLib.py L20-26
def scale(amt, from_decimals, to_decimals):
    if from_decimals == to_decimals:
        return amt
    elif from_decimals > to_decimals:
        return amt // (10 ** (from_decimals - to_decimals))
    else:
        return amt * (10 ** (to_decimals - from_decimals))  # ← MULTIPLICATION
```

Setting a smaller `from_decimals` in the payload than the actual asset decimals causes the `untrim` step to **multiply by a larger power of 10**, minting more tokens than were burned on the source chain.

**Example:** If the Algorand asset has 6 decimals and the peer normally sends with `from_decimals = 6`, but a crafted message sets `from_decimals = 2`:
- `amount = 1000000` (1 token with 6 decimals)
- Normal: `scale(1000000, 6, 6) = 1000000` → mints 1 token
- Attack: `scale(1000000, 2, 6) = 1000000 * 10^4 = 10000000000` → mints **10,000 tokens**

This breaks the cross-chain invariant: `sum(minted) == sum(burned)`.

## Risk Breakdown

- **Attack Complexity:** Requires peer NttManager compromise or malicious peer registration by admin
- **Impact:** Infinite mint on the Algorand side, breaking 1:1 cross-chain peg
- **Affected Assets:** All tokens managed by the NTT bridge
- **Severity:** High (cross-chain invariant violation leading to potential loss of funds for all bridge users)

## Recommendation

Add `peer_decimals` validation in `_handle_message`:

```python
# After line 421 in NttManager.py
from_decimals = ARC4UInt8(op.btoi(op.extract(payload, index, 1)))
# ADD: validate from_decimals matches configured peer
assert from_decimals == ntt_manager_peer.decimals, "DECIMALS_MISMATCH"
```

## References

- [NttManager.py L414-453](https://github.com/Folks-Finance/algorand-ntt-contracts/blob/main/ntt_contracts/ntt_manager/NttManager.py#L414-L453) — `_handle_message` inbound path
- [NttManager.py L462-469](https://github.com/Folks-Finance/algorand-ntt-contracts/blob/main/ntt_contracts/ntt_manager/NttManager.py#L462-L469) — `_trim_transfer_amount` outbound path (with validation)
- [TrimmedAmountLib.py L19-26](https://github.com/Folks-Finance/algorand-ntt-contracts/blob/main/ntt_contracts/library/TrimmedAmountLib.py#L19-L26) — `scale` function
- [NttManager.py L137-157](https://github.com/Folks-Finance/algorand-ntt-contracts/blob/main/ntt_contracts/ntt_manager/NttManager.py#L137-L157) — `set_ntt_manager_peer` stores `peer_decimals` but it's unused on inbound

## Proof of Concept

```python
"""
Conceptual PoC — demonstrates the decimal mismatch in TrimmedAmountLib.scale()
Run: python3 poc_v007.py
"""

def scale(amt: int, from_decimals: int, to_decimals: int) -> int:
    """Mirror of TrimmedAmountLib.scale"""
    if from_decimals == to_decimals:
        return amt
    elif from_decimals > to_decimals:
        return amt // (10 ** (from_decimals - to_decimals))
    else:
        return amt * (10 ** (to_decimals - from_decimals))

# Scenario: Algorand asset has 6 decimals, peer configured with peer_decimals=6
ASSET_DECIMALS = 6
PEER_DECIMALS = 6  # configured via set_ntt_manager_peer

# Normal inbound: from_decimals in payload matches peer config
from_amount = 1_000_000  # 1 token (6 decimals)
normal_from_decimals = 6  # matches peer config
normal_result = scale(from_amount, normal_from_decimals, ASSET_DECIMALS)
print(f"Normal:  scale({from_amount}, {normal_from_decimals}, {ASSET_DECIMALS}) = {normal_result}")
print(f"         Mints: {normal_result / 10**ASSET_DECIMALS:.6f} tokens")

# Attack: from_decimals in payload is 2 (attacker-controlled via compromised peer)
attack_from_decimals = 2  # NOT validated against PEER_DECIMALS
attack_result = scale(from_amount, attack_from_decimals, ASSET_DECIMALS)
print(f"\nAttack:  scale({from_amount}, {attack_from_decimals}, {ASSET_DECIMALS}) = {attack_result}")
print(f"         Mints: {attack_result / 10**ASSET_DECIMALS:.6f} tokens")
print(f"         Amplification: {attack_result / normal_result}x")

# With TRIMMED_DECIMALS cap = 8
TRIMMED_DECIMALS = 8
min_decimals = min(TRIMMED_DECIMALS, min(PEER_DECIMALS, attack_from_decimals))
print(f"\nTrim cap check: min({TRIMMED_DECIMALS}, {PEER_DECIMALS}, {attack_from_decimals}) = {min_decimals}")
print(f"This does NOT prevent the attack because from_decimals in payload")
print(f"is used directly in untrim, bypassing the trim cap entirely.")
```
