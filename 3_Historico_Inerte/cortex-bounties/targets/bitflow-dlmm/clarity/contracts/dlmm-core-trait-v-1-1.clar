;; dlmm-core-trait-v-1-1

;; Use DLMM pool trait and SIP 010 trait
(use-trait dlmm-pool-trait .dlmm-pool-trait-v-1-1.dlmm-pool-trait)
(use-trait sip-010-trait .sip-010-trait-ft-standard-v-1-1.sip-010-trait)

(define-trait dlmm-core-trait
	(
		(accept-migrated-pool (principal principal principal uint uint (string-ascii 32) (string-ascii 32) bool) (response bool uint))
		(create-pool (<dlmm-pool-trait> <sip-010-trait> <sip-010-trait> uint uint uint uint uint uint uint uint uint bool (optional (buff 4096)) principal (string-ascii 256) bool) (response bool uint))
		(swap-x-for-y (<dlmm-pool-trait> <sip-010-trait> <sip-010-trait> int uint) (response {in: uint, out: uint} uint))
		(swap-y-for-x (<dlmm-pool-trait> <sip-010-trait> <sip-010-trait> int uint) (response {in: uint, out: uint} uint))
		(add-liquidity (<dlmm-pool-trait> <sip-010-trait> <sip-010-trait> int uint uint uint uint uint) (response uint uint))
		(withdraw-liquidity (<dlmm-pool-trait> <sip-010-trait> <sip-010-trait> int uint uint uint) (response {x-amount: uint, y-amount: uint} uint))
		(move-liquidity (<dlmm-pool-trait> <sip-010-trait> <sip-010-trait> int int uint uint uint uint) (response uint uint))
	)
)