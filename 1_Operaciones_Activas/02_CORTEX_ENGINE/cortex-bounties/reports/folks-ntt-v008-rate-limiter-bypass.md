# Folks Finance NTT — Rate Limiter Bypass via Queued Transfer Completion

## Bug Description

The `NttRateLimiter` implements a token bucket rate-limiting mechanism to constrain cross-chain transfer throughput. When inbound capacity is exhausted, transfers are queued with a timestamp. However, the `complete_inbound_queued_transfer()` function only checks that sufficient time has elapsed — it does **NOT re-consume from the rate limiter bucket** upon completion.

### The Rate Limiting Flow:

**Step 1 — Enqueue (rate limited):**
```python
# NttRateLimiter.py L256-304
def _enqueue_or_consume_inbound_transfer(self, untrimmed_amount, ...):
    has_capacity = self.has_capacity(inbound_bucket, UInt256(untrimmed_amount))
    if not has_capacity:
        # Queue the transfer with current timestamp
        self.inbound_queued_transfers[message_digest] = InboundQueuedTransfer(
            ARC4UInt64(Global.latest_timestamp),
            trimmed_amount, source_chain, recipient
        )
        return Bool(True)  # enqueued, NOT minted
    # If has capacity: consume from bucket and mint
    self._consume_amount(inbound_bucket, UInt256(untrimmed_amount))
    self._fill_amount(outbound_bucket, UInt256(untrimmed_amount))
    return Bool(False)
```

**Step 2 — Complete (NO rate check):**
```python
# NttManager.py L253-269
def complete_inbound_queued_transfer(self, message_digest):
    can_complete, transfer = self.get_inbound_queued_transfer(message_digest)
    assert can_complete  # ONLY checks: elapsed >= rate_duration
    
    self._delete_inbound_transfer(message_digest)
    untrimmed_amount = self._untrim_transfer_amount(transfer.amount)
    
    # DIRECTLY MINTS — no _consume_amount, no capacity check
    abi_call(INttToken.mint, transfer.recipient, untrimmed_amount, ...)
```

**Step 3 — Time check only:**
```python
# NttRateLimiter.py L167-185
def get_inbound_queued_transfer(self, message_digest):
    transfer = self.inbound_queued_transfers[message_digest]
    delta = Global.latest_timestamp - transfer.timestamp.as_uint64()
    can_complete = delta >= self.get_rate_duration(inbound_bucket)
    return Bool(can_complete), transfer
```

## Impact

An attacker (or set of colluding users from a source chain) can:

1. Send N transfers from a source chain, each larger than the inbound rate limit capacity
2. All N transfers get queued (rate limited)
3. Wait for `rate_duration` seconds
4. Call `complete_inbound_queued_transfer()` for each of the N messages
5. **All N transfers mint simultaneously** — total minted = N × transfer_amount

This effectively makes the rate limiter a **delay mechanism**, not a throughput limiter. The designed intent (limiting how many tokens can enter per window) is completely bypassed for queued transfers.

### Concrete Example:

- Inbound rate limit: 1,000,000 tokens per 24h window
- Rate duration: 86400 seconds (24h)
- Attacker queues 10 transfers of 5,000,000 tokens each (all exceed capacity)
- After 24h, attacker completes all 10 → mints 50,000,000 tokens
- Expected behavior: only 1,000,000 tokens should be mintable per 24h window

### Comparison with Outbound:

The outbound path has the **same pattern** — `complete_outbound_queued_transfer()` (NttManager.py L200-229) also skips rate limit consumption:
```python
# "skip rate limit logic and carry out transfer"
self._transfer(fee_payment, message_id, ...)
```

The comment explicitly states "skip rate limit logic" — confirming this is **by design** but represents a fundamental weakness in the rate limiting architecture.

## Risk Breakdown

- **Attack Complexity:** Low — requires only queuing transfers and waiting
- **Impact:** Rate limiter bypass, potential for bridge drain if source chain allows unlimited outbound
- **Affected Assets:** All tokens managed by the NTT bridge on the Algorand side
- **Severity:** Medium-High (security control bypass with potential economic impact)

## Recommendation

Re-consume from the rate limiter bucket when completing queued transfers:

```python
def complete_inbound_queued_transfer(self, message_digest):
    can_complete, transfer = self.get_inbound_queued_transfer(message_digest)
    assert can_complete
    
    self._delete_inbound_transfer(message_digest)
    untrimmed_amount = self._untrim_transfer_amount(transfer.amount)
    
    # ADD: re-check and consume from rate limiter
    assert self.has_capacity(
        self.inbound_bucket_id(transfer.source_chain), 
        UInt256(untrimmed_amount)
    ), "INBOUND_CAPACITY_EXCEEDED"
    self._consume_amount(
        self.inbound_bucket_id(transfer.source_chain),
        UInt256(untrimmed_amount)
    )
    
    abi_call(INttToken.mint, transfer.recipient, untrimmed_amount, ...)
```

## References

- [NttRateLimiter.py L256-304](https://github.com/Folks-Finance/algorand-ntt-contracts/blob/main/ntt_contracts/ntt_manager/NttRateLimiter.py#L256-L304) — `_enqueue_or_consume_inbound_transfer` (rate check + queue)
- [NttManager.py L253-269](https://github.com/Folks-Finance/algorand-ntt-contracts/blob/main/ntt_contracts/ntt_manager/NttManager.py#L253-L269) — `complete_inbound_queued_transfer` (no rate check)
- [NttManager.py L200-229](https://github.com/Folks-Finance/algorand-ntt-contracts/blob/main/ntt_contracts/ntt_manager/NttManager.py#L200-L229) — `complete_outbound_queued_transfer` (same pattern)
- [NttRateLimiter.py L167-185](https://github.com/Folks-Finance/algorand-ntt-contracts/blob/main/ntt_contracts/ntt_manager/NttRateLimiter.py#L167-L185) — `get_inbound_queued_transfer` (time-only check)

## Proof of Concept

```python
"""
Conceptual PoC — demonstrates rate limiter bypass through queued transfers.
Run: python3 poc_v008.py
"""
import time

class MockRateLimiter:
    """Simplified model of NttRateLimiter behavior"""
    def __init__(self, capacity: int, duration: int):
        self.capacity = capacity
        self.current = capacity
        self.duration = duration
        self.queue = {}
    
    def try_consume(self, amount: int, msg_id: str, timestamp: int) -> bool:
        """_enqueue_or_consume_inbound_transfer"""
        if self.current >= amount:
            self.current -= amount
            print(f"  CONSUMED: {amount} tokens (remaining: {self.current})")
            return True  # minted immediately
        else:
            self.queue[msg_id] = {"amount": amount, "timestamp": timestamp}
            print(f"  QUEUED: {amount} tokens (capacity: {self.current}/{self.capacity})")
            return False  # queued
    
    def complete_queued(self, msg_id: str, current_time: int) -> int:
        """complete_inbound_queued_transfer — NO rate check"""
        entry = self.queue.pop(msg_id)
        elapsed = current_time - entry["timestamp"]
        if elapsed >= self.duration:
            # BUG: directly mints without consuming from bucket
            print(f"  COMPLETED: {entry['amount']} tokens (NO capacity check)")
            return entry["amount"]
        raise Exception("Still queued")


# Setup: 1M capacity per 24h window
limiter = MockRateLimiter(capacity=1_000_000, duration=86400)
T0 = 0

print("=== Phase 1: Queue 10 large transfers ===")
total_queued = 0
for i in range(10):
    msg_id = f"msg_{i}"
    amount = 5_000_000
    consumed = limiter.try_consume(amount, msg_id, T0)
    if not consumed:
        total_queued += amount

print(f"\nTotal queued: {total_queued:,} tokens")
print(f"Rate limit capacity: {limiter.capacity:,} tokens/24h")

print("\n=== Phase 2: After 24h, complete all queued transfers ===")
T1 = T0 + 86400  # 24h later
total_minted = 0
for i in range(10):
    msg_id = f"msg_{i}"
    if msg_id in limiter.queue:
        minted = limiter.complete_queued(msg_id, T1)
        total_minted += minted

print(f"\nTotal minted via queue bypass: {total_minted:,} tokens")
print(f"Expected max per window:      {limiter.capacity:,} tokens")
print(f"Bypass ratio:                 {total_minted/limiter.capacity:.0f}x")
```
