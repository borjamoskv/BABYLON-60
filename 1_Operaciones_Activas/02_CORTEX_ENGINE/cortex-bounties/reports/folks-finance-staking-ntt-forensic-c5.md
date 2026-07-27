# 🔬 Folks Finance Staking — Forensic Audit Analysis

> **Target:** `Folks-Finance/folks-staking-contracts` | **Solidity 0.8.30**
> **Surface:** `Staking.sol` (360 LOC) + `IStakingV1.sol` + `IMigratorV1.sol` + `MigratorV1.sol`
> **Competition:** Immunefi Audit Comp | $250,000 | EVALUATING (26d remaining)
> **Contracts:** `0xFF7F8F301F7A706E3CfD3D2275f5dc0b9EE8009B`, `0x019a179Afe07BdaD72E1F37CcBec42310C4bd012`

---

## Architecture Summary

Fixed APR staking with linear unlock vesting:

```
User → stake(periodIndex, amount, params) → locks TOKEN for stakingDuration
                                           → earns reward = (amount × aprBps × duration) / (1e4 × 365d)
     → after unlockTime → linear vesting over unlockDuration
     → withdraw(stakeIndex) → claims proportional amount + reward
```

**Key primitives:**
- `StakingPeriod` — configurable pools with cap, APR, durations
- `UserStake` — per-user position tracking with claimed amounts
- `_getAccrued()` — linear vesting via `Math.mulDiv(amount, min(elapsed, duration), duration)`
- Migration system — permits + MIGRATOR_ROLE can move positions to V2

---

## Vulnerability Analysis

### 🔴 V-001: Reward Calculation Precision Loss (MEDIUM → HIGH)

**Location:** [Staking.sol:282-283](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/competitions/folks-finance/folks-staking-contracts/src/Staking.sol#L282-L283)

```solidity
uint256 rewardBpsDenominator = 1e4 * 365 days; // = 315,360,000,000
uint256 reward = (amount * stakingPeriod.aprBps * stakingPeriod.stakingDurationSeconds) / rewardBpsDenominator;
```

**Issue:** For small `amount` values, the intermediate multiplication can be smaller than `rewardBpsDenominator`, resulting in `reward = 0` due to integer truncation.

**Example:**
- `amount = 100` (dust), `aprBps = 500` (5%), `duration = 2592000` (30d)
- Numerator: `100 * 500 * 2592000 = 129,600,000,000`
- Result: `129.6B / 315.36B = 0` → **ZERO REWARD**

The user's `amount` is locked but earns nothing. Over many micro-stakes, tokens accumulate in the contract without corresponding reward tracking.

**Severity Assessment:** MEDIUM. Requires dust amounts. Creates a discrepancy between tracked rewards and actual obligations.

---

### 🟡 V-002: `updateStakingPeriod` Retroactive Parameter Change (LOW)

**Location:** [Staking.sol:113-136](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/competitions/folks-finance/folks-staking-contracts/src/Staking.sol#L113-L136)

A malicious/compromised MANAGER can set `aprBps = 0` to deny rewards to new stakers, or set `cap = 0` to lock the pool. **Admin trust assumption — not a code bug.**

---

### ✅ V-003: `_getClaimableAmounts` Underflow — FALSE POSITIVE

**Location:** [Staking.sol:347-358](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/competitions/folks-finance/folks-staking-contracts/src/Staking.sol#L347-L358)

`Math.mulDiv` defaults to `Rounding.Floor`, so `accruedAmount` is monotonically non-decreasing with elapsed time. `claimed` is only ever incremented by `accrued - claimed`. Invariant `accrued >= claimed` holds. **No exploitable underflow.**

---

### 🟡 V-004: Migration Permit Without Expiry (LOW)

**Location:** [Staking.sol:77-83](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/competitions/folks-finance/folks-staking-contracts/src/Staking.sol#L77-L83)

Permits are permanent — no expiry, no nonce. Mitigated by `onlyRole(MIGRATOR_ROLE)` on `migratePositionsFrom`. Only risk: role revoke + re-grant to same address (unlikely sequence).

---

### ✅ V-005: `recoverERC20` Extraction — FALSE POSITIVE

**Location:** [Staking.sol:151-163](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/competitions/folks-finance/folks-staking-contracts/src/Staking.sol#L151-L163)

The invariant `contractBalance >= activeTotalStaked + activeTotalRewards` is consistently enforced across all paths. **Properly guarded.**

---

### ✅ V-006: `stakeIndex` uint8 Overflow — FALSE POSITIVE

`MAX_STAKES_PER_USER = 100` prevents exceeding `uint8` range (max 255). **Safe.**

---

## NTT Cross-Chain Bridge — Deep Analysis

> **Codebase:** `algorand-ntt-contracts` | **Language:** Python/PyTEAL (Algorand AVM)
> **Surface:** NttManager (481 LOC) + NttRateLimiter (335 LOC) + TransceiverManager (369 LOC) + MessageHandler (187 LOC) + TrimmedAmountLib (54 LOC)
> **Total:** ~1,426 LOC of cross-chain bridge logic

### Architecture

```
Source Chain                    Algorand (this codebase)
─────────────                   ────────────────────────
User sends tokens  ──────►  Transceiver receives attestation
                            TransceiverManager records attestation
                            MessageHandler checks threshold
                            NttManager._handle_message() parses payload
                            NttRateLimiter checks rate limits
                            INttToken.mint() creates tokens
```

---

### 🔴 V-007: TrimmedAmount Inbound Decimal Mismatch (HIGH)

**Location:** `TrimmedAmountLib.py:17-40` + `NttManager.py:428-442`

On outbound, the contract validates round-trip precision:
```python
# NttManager.py:465-467 (outbound)
trimmed_amount = TrimmedAmountLib.trim(amount, from_decimals, to_decimals)
new_amount = TrimmedAmountLib.untrim(trimmed_amount, from_decimals)
assert amount == new_amount  # ← round-trip check
```

**But on inbound (L428-442), NO such validation exists:**
```python
from_decimals = ARC4UInt8(op.btoi(op.extract(payload, index, 1)))  # ← from payload
from_amount = ARC4UInt64(op.extract_uint64(payload, index))
trimmed_amount = TrimmedAmount(from_amount, from_decimals)
untrimmed_amount = self._untrim_transfer_amount(trimmed_amount)  # ← scale up
```

The `from_decimals` is extracted directly from the cross-chain payload — it's whatever the source chain encoded. The inbound path does NOT validate that `from_decimals` matches the `peer_decimals` configured in `set_ntt_manager_peer`.

If a source chain is compromised or a malicious peer is registered with incorrect decimals, the `untrim` operation will scale the amount incorrectly, potentially minting more tokens than were burned.

**Severity:** HIGH — cross-chain invariant violation on the mint path.

---

### 🔴 V-008: Rate Limiter Bypass via Queued Transfer Completion (MEDIUM→HIGH)

**Location:** `NttRateLimiter.py:256-304` + `NttManager.py:253-269`

When inbound capacity is exhausted, transfers are queued. The completion path:

```python
# NttManager.py:253-269
def complete_inbound_queued_transfer(self, message_digest):
    can_complete, transfer = self.get_inbound_queued_transfer(message_digest)
    assert can_complete  # only checks time elapsed >= rate_duration
    self._delete_inbound_transfer(message_digest)
    untrimmed_amount = self._untrim_transfer_amount(transfer.amount)
    abi_call(INttToken.mint, transfer.recipient, untrimmed_amount, ...)  # ← direct mint
```

**No rate limit re-check on dequeue.** Once `rate_duration` passes, ANY queued amount is mintable regardless of current bucket capacity. An attacker can:
1. Queue N large transfers (each exceeding capacity)
2. Wait for `rate_duration`
3. Complete all N transfers simultaneously — minting `N × capacity` in one window

The rate limiter is designed to constrain throughput per window, but queued transfers bypass this entirely.

**Severity:** MEDIUM-HIGH — rate limiter control bypass.

---

### 🟡 V-009: `_refund_min_balance_to_caller` Drains All Excess ALGO (MEDIUM)

**Location:** `NttManager.py:476-480`

```python
def _refund_min_balance_to_caller(self) -> None:
    amount = Global.current_application_address.balance - Global.current_application_address.min_balance
    itxn.Payment(amount=amount, receiver=Txn.sender, fee=0).submit()
```

Called after completing/canceling queued transfers. Sends **ALL excess ALGO** to the caller — not just the box storage refund. First user to complete a queued transfer drains all accumulated fee surplus.

**Severity:** MEDIUM — economic fairness violation, first-completer-wins.

---

### 🟡 V-010: Attestation Count Persists After Transceiver Removal (LOW)

**Location:** `TransceiverManager.py:130-142, 189-218`

When a transceiver is removed via `remove_transceiver`, its prior attestations remain in `transceiver_attestations` and `num_attestations`. If a replacement transceiver is added and attests to the same message, the count can exceed current transceiver count.

**Severity:** LOW — requires admin action during in-flight messages.

---

## Combined Verdict

| ID | Finding | Surface | Severity | Actionable? |
|----|---------|---------|----------|-------------|
| **V-007** | **Inbound decimal mismatch — no peer_decimals validation** | **NTT Bridge** | **HIGH** | ✅ **Primary candidate** |
| **V-008** | **Rate limiter bypass via queued completion** | **NTT Bridge** | **MEDIUM-HIGH** | ✅ **Primary candidate** |
| V-009 | Excess ALGO drain via refund | NTT Bridge | MEDIUM | ✅ Worth submitting |
| V-001 | Reward precision loss on dust | Staking | MEDIUM | ✅ Worth submitting |
| V-010 | Attestation count edge case | Transceiver | LOW | ⚠️ Informational |
| V-002 | Retroactive param changes | Staking | LOW | ❌ Admin trust |
| V-004 | Permanent migration permits | Staking | LOW | ⚠️ Informational |
| V-003 | Accrued underflow | Staking | FALSE POSITIVE | ❌ |
| V-005 | recoverERC20 extraction | Staking | FALSE POSITIVE | ❌ |
| V-006 | uint8 overflow | Staking | FALSE POSITIVE | ❌ |

> [!IMPORTANT]
> **V-007 and V-008 are the highest-value findings.** The NTT cross-chain bridge is the critical surface — the missing `peer_decimals` validation on inbound transfers and the rate limiter bypass on queued completions are the most impactful vectors for the $250K pool.
>
> **Next step:** Craft runnable PoCs for V-007 and V-008 using Algorand sandbox/devnet.

---

*CORTEX Arena Agent — Forensic Analysis v1.0*
