;; sip-013-transfer-many-trait-v-1-1

(define-trait sip-013-transfer-many-trait
	(
		(transfer-many ((list 200 {token-id: uint, amount: uint, sender: principal, recipient: principal})) (response bool uint))
		(transfer-many-memo ((list 200 {token-id: uint, amount: uint, sender: principal, recipient: principal, memo: (buff 34)})) (response bool uint))
	)
)