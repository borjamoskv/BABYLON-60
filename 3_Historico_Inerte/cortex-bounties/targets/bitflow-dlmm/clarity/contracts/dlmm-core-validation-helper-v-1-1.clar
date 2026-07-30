;; dlmm-core-validation-helper-v-1-1

;; Error constants
(define-constant ERR_NO_BLOCK_INFO (err u7001))

;; Get pool by ID at block height
(define-read-only (get-pool-by-id (height uint) (id uint))
	(at-block (unwrap! (get-stacks-block-info? id-header-hash height) ERR_NO_BLOCK_INFO) (contract-call? .dlmm-core-v-1-1 get-pool-by-id id))
)