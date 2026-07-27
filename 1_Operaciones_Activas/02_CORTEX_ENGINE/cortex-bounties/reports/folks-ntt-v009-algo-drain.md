# Folks Finance NTT — Excess ALGO Drain via Refund Mechanism

## Bug Description

The `NttManager._refund_min_balance_to_caller()` subroutine sends **all excess ALGO** (above minimum balance) to `Txn.sender` when completing or canceling queued transfers. This includes accumulated fee surplus, not just the box storage costs.

```python
# NttManager.py L476-480
@subroutine
def _refund_min_balance_to_caller(self) -> None:
    # this will also send all donated ALGO to the caller
    amount = Global.current_application_address.balance - Global.current_application_address.min_balance
    itxn.Payment(amount=amount, receiver=Txn.sender, fee=0).submit()
```

This function is called from:
1. `complete_outbound_queued_transfer()` — L227
2. `cancel_outbound_queued_transfer()` — L250
3. `complete_inbound_queued_transfer()` — L269

## Impact

### Fee Surplus Accumulation

The `_transfer` function collects fees and refunds **only the excess** above `total_delivery_price`:

```python
# NttManager.py L399-404
assert fee_payment.amount >= total_delivery_price
excess_fee_payment = fee_payment.amount - total_delivery_price
if excess_fee_payment:
    itxn.Payment(amount=excess_fee_payment, receiver=fee_payment.sender, fee=0).submit()
```

However, if `fee_payment.amount == total_delivery_price` (exact payment), no ALGO accumulates from this path. The real issue is:

1. **Box storage MBR accumulation:** Each queued transfer creates a BoxMap entry, increasing `min_balance`. When deleted, `min_balance` decreases, but `balance` stays the same → the difference becomes "excess" that ALL goes to the first completer.

2. **Multi-user race condition:** If users A, B, and C all have queued transfers:
   - User A completes first → receives refund for ALL deleted boxes (including future refunds that B and C should get)
   - Users B and C complete → receive 0 ALGO refund (contract has no excess left)

3. **Griefing via donation:** An attacker can:
   - Donate ALGO to the contract (any Algorand address can send ALGO to any account)
   - Queue a minimal transfer
   - Wait for duration
   - Complete and drain all donated ALGO + other users' box MBR refunds

### Economic Impact

On Algorand, box storage costs 0.0025 ALGO per byte + 0.1 ALGO base. A queued transfer struct is ~200 bytes → ~0.6 ALGO per box. With 100 queued transfers, ~60 ALGO is at risk of being claimed by the first completer instead of distributed fairly.

## Risk Breakdown

- **Attack Complexity:** Low — queue a small transfer, wait, complete
- **Impact:** Economic fairness violation, ALGO theft from other queue participants
- **Affected Assets:** ALGO (native Algorand token), not the bridged token
- **Severity:** Medium (unfair distribution of protocol ALGO)

## Recommendation

Track individual box storage costs per queued transfer and refund only the proportional amount:

```python
@subroutine
def _refund_box_storage_to_caller(self, box_size: UInt64) -> None:
    # Refund only the MBR for the specific box deleted
    box_cost = UInt64(2500) * box_size + UInt64(100_000)  # 0.0025 ALGO/byte + 0.1 base
    refund = min(box_cost, Global.current_application_address.balance - Global.current_application_address.min_balance)
    if refund:
        itxn.Payment(amount=refund, receiver=Txn.sender, fee=0).submit()
```

## References

- [NttManager.py L476-480](https://github.com/Folks-Finance/algorand-ntt-contracts/blob/main/ntt_contracts/ntt_manager/NttManager.py#L476-L480) — `_refund_min_balance_to_caller`
- [NttManager.py L200-229](https://github.com/Folks-Finance/algorand-ntt-contracts/blob/main/ntt_contracts/ntt_manager/NttManager.py#L200-L229) — `complete_outbound_queued_transfer` caller
- [NttManager.py L253-269](https://github.com/Folks-Finance/algorand-ntt-contracts/blob/main/ntt_contracts/ntt_manager/NttManager.py#L253-L269) — `complete_inbound_queued_transfer` caller
