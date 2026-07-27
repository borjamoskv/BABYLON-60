;; dlmm-pool-multi-helper-v-1-1

;; Use DLMM pool trait
(use-trait dlmm-pool-trait .dlmm-pool-trait-v-1-1.dlmm-pool-trait)

;; Get multiple bin balances for multiple pools
(define-public (get-bin-balances-multi
		(pool-traits (list 1001 <dlmm-pool-trait>))
		(ids (list 1001 uint))
	)
	(ok (map get-bin-balances pool-traits ids))
)

;; Get multiple balances for multiple users across multiple pools
(define-public (get-balance-multi
		(pool-traits (list 1001 <dlmm-pool-trait>))
		(token-ids (list 1001 uint))
		(users (list 1001 principal))
	)
	(ok (map get-balance pool-traits token-ids users))
)

(define-private (get-bin-balances (pool-trait <dlmm-pool-trait>) (id uint))
	(contract-call? pool-trait get-bin-balances id)
)

(define-private (get-balance (pool-trait <dlmm-pool-trait>) (token-id uint) (user principal))
	(contract-call? pool-trait get-balance token-id user)
)