;; dlmm-core-multi-helper-v-1-1

;; Use DLMM core trait, DLMM pool trait, and SIP 010 trait
(use-trait dlmm-core-trait .dlmm-core-trait-v-1-1.dlmm-core-trait)
(use-trait dlmm-pool-trait .dlmm-pool-trait-v-1-1.dlmm-pool-trait)
(use-trait sip-010-trait .sip-010-trait-ft-standard-v-1-1.sip-010-trait)

;; Migrate multiple pools to the target core contract
(define-public (migrate-pool-multi (pool-traits (list 120 <dlmm-pool-trait>)) (core-traits (list 120 <dlmm-core-trait>)))
	(ok (map migrate-pool pool-traits core-traits))
)

;; Set swap fee exemption for multiple addresses across multiple pools
(define-public (set-swap-fee-exemption-multi
		(pool-traits (list 120 <dlmm-pool-trait>))
		(addresses (list 120 principal))
		(exempts (list 120 bool))
	)
	(ok (map set-swap-fee-exemption pool-traits addresses exempts))
)

;; Claim protocol fees for multiple pools
(define-public (claim-protocol-fees-multi
		(pool-traits (list 120 <dlmm-pool-trait>))
		(x-token-traits (list 120 <sip-010-trait>))
		(y-token-traits (list 120 <sip-010-trait>))
	)
	(ok (map claim-protocol-fees pool-traits x-token-traits y-token-traits))
)

;; Set pool uri for multiple pools
(define-public (set-pool-uri-multi
		(pool-traits (list 120 <dlmm-pool-trait>))
		(uris (list 120 (string-ascii 256)))
	)
	(ok (map set-pool-uri pool-traits uris))
)

;; Set pool status for multiple pools
(define-public (set-pool-status-multi
		(pool-traits (list 120 <dlmm-pool-trait>))
		(statuses (list 120 bool))
	)
	(ok (map set-pool-status pool-traits statuses))
)

;; Set variable fees manager for multiple pools
(define-public (set-variable-fees-manager-multi
		(pool-traits (list 120 <dlmm-pool-trait>))
		(managers (list 120 principal))
	)
	(ok (map set-variable-fees-manager pool-traits managers))
)

;; Set fee address for multiple pools
(define-public (set-fee-address-multi
		(pool-traits (list 120 <dlmm-pool-trait>))
		(addresses (list 120 principal))
	)
	(ok (map set-fee-address pool-traits addresses))
)

;; Set variable fees for multiple pools
(define-public (set-variable-fees-multi
		(pool-traits (list 120 <dlmm-pool-trait>))
		(x-fees (list 120 uint))
		(y-fees (list 120 uint))
	)
	(ok (map set-variable-fees pool-traits x-fees y-fees))
)

;; Set x fees for multiple pools
(define-public (set-x-fees-multi
		(pool-traits (list 120 <dlmm-pool-trait>))
		(protocol-fees (list 120 uint))
		(provider-fees (list 120 uint))
	)
	(ok (map set-x-fees pool-traits protocol-fees provider-fees))
)

;; Set y fees for multiple pools
(define-public (set-y-fees-multi
		(pool-traits (list 120 <dlmm-pool-trait>))
		(protocol-fees (list 120 uint))
		(provider-fees (list 120 uint))
	)
	(ok (map set-y-fees pool-traits protocol-fees provider-fees))
)

;; Set variable fees cooldown for multiple pools
(define-public (set-variable-fees-cooldown-multi
		(pool-traits (list 120 <dlmm-pool-trait>))
		(cooldowns (list 120 uint))
	)
	(ok (map set-variable-fees-cooldown pool-traits cooldowns))
)

;; Set freeze variable fees manager for multiple pools
(define-public (set-freeze-variable-fees-manager-multi (pool-traits (list 120 <dlmm-pool-trait>)))
	(ok (map set-freeze-variable-fees-manager pool-traits))
)

;; Reset variable fees for multiple pools
(define-public (reset-variable-fees-multi (pool-traits (list 120 <dlmm-pool-trait>)))
	(ok (map reset-variable-fees pool-traits))
)

;; Set dynamic config for multiple pools
(define-public (set-dynamic-config-multi
		(pool-traits (list 120 <dlmm-pool-trait>))
		(configs (list 120 (buff 4096)))
	)
	(ok (map set-dynamic-config pool-traits configs))
)

(define-private (migrate-pool (pool-trait <dlmm-pool-trait>) (core-trait <dlmm-core-trait>))
	(contract-call? .dlmm-core-v-1-1 migrate-pool pool-trait core-trait)
)

(define-private (set-swap-fee-exemption (pool-trait <dlmm-pool-trait>) (address principal) (exempt bool))
	(contract-call? .dlmm-core-v-1-1 set-swap-fee-exemption pool-trait address exempt)
)

(define-private (claim-protocol-fees (pool-trait <dlmm-pool-trait>) (x-token-trait <sip-010-trait>) (y-token-trait <sip-010-trait>))
	(contract-call? .dlmm-core-v-1-1 claim-protocol-fees pool-trait x-token-trait y-token-trait)
)

(define-private (set-pool-uri (pool-trait <dlmm-pool-trait>) (uri (string-ascii 256)))
	(contract-call? .dlmm-core-v-1-1 set-pool-uri pool-trait uri)
)

(define-private (set-pool-status (pool-trait <dlmm-pool-trait>) (status bool))
	(contract-call? .dlmm-core-v-1-1 set-pool-status pool-trait status)
)

(define-private (set-variable-fees-manager (pool-trait <dlmm-pool-trait>) (manager principal))
	(contract-call? .dlmm-core-v-1-1 set-variable-fees-manager pool-trait manager)
)

(define-private (set-fee-address (pool-trait <dlmm-pool-trait>) (address principal))
	(contract-call? .dlmm-core-v-1-1 set-fee-address pool-trait address)
)

(define-private (set-variable-fees (pool-trait <dlmm-pool-trait>) (x-fee uint) (y-fee uint))
	(contract-call? .dlmm-core-v-1-1 set-variable-fees pool-trait x-fee y-fee)
)

(define-private (set-x-fees (pool-trait <dlmm-pool-trait>) (protocol-fee uint) (provider-fee uint))
	(contract-call? .dlmm-core-v-1-1 set-x-fees pool-trait protocol-fee provider-fee)
)

(define-private (set-y-fees (pool-trait <dlmm-pool-trait>) (protocol-fee uint) (provider-fee uint))
	(contract-call? .dlmm-core-v-1-1 set-y-fees pool-trait protocol-fee provider-fee)
)

(define-private (set-variable-fees-cooldown (pool-trait <dlmm-pool-trait>) (cooldown uint))
	(contract-call? .dlmm-core-v-1-1 set-variable-fees-cooldown pool-trait cooldown)
)

(define-private (set-freeze-variable-fees-manager (pool-trait <dlmm-pool-trait>))
	(contract-call? .dlmm-core-v-1-1 set-freeze-variable-fees-manager pool-trait)
)

(define-private (reset-variable-fees (pool-trait <dlmm-pool-trait>))
	(contract-call? .dlmm-core-v-1-1 reset-variable-fees pool-trait)
)

(define-private (set-dynamic-config (pool-trait <dlmm-pool-trait>) (config (buff 4096)))
	(contract-call? .dlmm-core-v-1-1 set-dynamic-config pool-trait config)
)