;; dlmm-pool-sbtc-usdc-validation-v-1-1

;; Error constants
(define-constant ERR_NO_BLOCK_INFO (err u6001))

;; Get pool data at block height
(define-read-only (get-pool (height uint))
	(at-block (unwrap! (get-stacks-block-info? id-header-hash height) ERR_NO_BLOCK_INFO) (contract-call? .dlmm-pool-sbtc-usdc-v-1-1 get-pool))
)

;; Get active bin ID at block height
(define-read-only (get-active-bin-id (height uint))
	(at-block (unwrap! (get-stacks-block-info? id-header-hash height) ERR_NO_BLOCK_INFO) (contract-call? .dlmm-pool-sbtc-usdc-v-1-1 get-active-bin-id))
)

;; Get x balance for pool at block height
(define-read-only (get-x-balance (height uint))
	(at-block (unwrap! (get-stacks-block-info? id-header-hash height) ERR_NO_BLOCK_INFO) (contract-call? .mock-sbtc-token get-balance .dlmm-pool-sbtc-usdc-v-1-1))
)

;; Get y balance for pool at block height
(define-read-only (get-y-balance (height uint))
	(at-block (unwrap! (get-stacks-block-info? id-header-hash height) ERR_NO_BLOCK_INFO) (contract-call? .mock-usdc-token get-balance .dlmm-pool-sbtc-usdc-v-1-1))
)

;; Get overall balance for a user at block height
(define-read-only (get-overall-balance (height uint) (user principal))
	(at-block (unwrap! (get-stacks-block-info? id-header-hash height) ERR_NO_BLOCK_INFO) (contract-call? .dlmm-pool-sbtc-usdc-v-1-1 get-overall-balance user))
)

;; Get user bins at block height
(define-read-only (get-user-bins (height uint) (user principal))
	(at-block (unwrap! (get-stacks-block-info? id-header-hash height) ERR_NO_BLOCK_INFO) (contract-call? .dlmm-pool-sbtc-usdc-v-1-1 get-user-bins user))
)

;; Get multiple bin balances for pool at multiple block heights
(define-read-only (get-bin-balances-multi (heights (list 1001 uint)) (ids (list 1001 uint)))
	(ok (map get-bin-balances heights ids))
)

;; Get multiple balances for multiple users for pool at multiple block heights
(define-read-only (get-balance-multi (heights (list 1001 uint)) (token-ids (list 1001 uint)) (users (list 1001 principal)))
	(ok (map get-balance heights token-ids users))
)

(define-private (get-bin-balances (height uint) (id uint))
	(at-block (unwrap! (get-stacks-block-info? id-header-hash height) ERR_NO_BLOCK_INFO) (contract-call? .dlmm-pool-sbtc-usdc-v-1-1 get-bin-balances id))
)

(define-private (get-balance (height uint) (token-id uint) (user principal))
	(at-block (unwrap! (get-stacks-block-info? id-header-hash height) ERR_NO_BLOCK_INFO) (contract-call? .dlmm-pool-sbtc-usdc-v-1-1 get-balance token-id user))
)