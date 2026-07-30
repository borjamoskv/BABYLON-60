;; Mock USDC token for testing
(impl-trait .sip-010-trait-ft-standard-v-1-1.sip-010-trait)

(define-fungible-token usdc)

(define-constant contract-owner tx-sender)

(define-constant err-owner-only (err u100))
(define-constant err-not-token-owner (err u101))
(define-constant err-insufficient-balance (err u102))

(define-public (transfer (amount uint) (from principal) (to principal) (memo (optional (buff 34))))
  (begin
    (asserts! (or (is-eq tx-sender from) (is-eq contract-caller from)) err-not-token-owner)
    (ft-transfer? usdc amount from to)
  )
)

(define-read-only (get-name)
  (ok "Mock USDC")
)

(define-read-only (get-symbol)
  (ok "USDC")
)

(define-read-only (get-decimals)
  (ok u6)
)

(define-read-only (get-balance (who principal))
  (ok (ft-get-balance usdc who))
)

(define-read-only (get-total-supply)
  (ok (ft-get-supply usdc))
)

(define-read-only (get-token-uri)
  (ok none)
)

(define-public (mint (amount uint) (to principal))
  (begin
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    (ft-mint? usdc amount to)
  )
)