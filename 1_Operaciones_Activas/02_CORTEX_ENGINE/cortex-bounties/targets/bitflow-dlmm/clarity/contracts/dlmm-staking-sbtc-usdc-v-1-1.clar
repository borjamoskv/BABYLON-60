;; dlmm-staking-sbtc-usdc-v-1-1

;; Implement DLMM staking trait
(impl-trait .dlmm-staking-trait-v-1-1.dlmm-staking-trait)

;; Error constants
(define-constant ERR_NOT_AUTHORIZED (err u4001))
(define-constant ERR_INVALID_AMOUNT (err u4002))
(define-constant ERR_INVALID_PRINCIPAL (err u4003))
(define-constant ERR_ALREADY_ADMIN (err u4004))
(define-constant ERR_ADMIN_LIMIT_REACHED (err u4005))
(define-constant ERR_ADMIN_NOT_IN_LIST (err u4006))
(define-constant ERR_CANNOT_REMOVE_CONTRACT_DEPLOYER (err u4007))
(define-constant ERR_STAKING_DISABLED (err u4008))
(define-constant ERR_EARLY_UNSTAKE_DISABLED (err u4009))
(define-constant ERR_TOKEN_TRANSFER_FAILED (err u4010))
(define-constant ERR_CANNOT_GET_TOKEN_BALANCE (err u4011))
(define-constant ERR_INSUFFICIENT_TOKEN_BALANCE (err u4012))
(define-constant ERR_INVALID_MIN_STAKING_DURATION (err u4013))
(define-constant ERR_MINIMUM_STAKING_DURATION_HAS_NOT_PASSED (err u4014))
(define-constant ERR_MINIMUM_STAKING_DURATION_PASSED (err u4015))
(define-constant ERR_INVALID_REWARD_PERIOD_DURATION (err u4016))
(define-constant ERR_REWARD_PERIOD_HAS_NOT_PASSED (err u4017))
(define-constant ERR_BINS_STAKED_OVERFLOW (err u4018))
(define-constant ERR_INVALID_BIN_ID (err u4019))
(define-constant ERR_NO_BIN_DATA (err u4020))
(define-constant ERR_NO_USER_DATA (err u4021))
(define-constant ERR_NO_USER_DATA_AT_BIN (err u4022))
(define-constant ERR_NO_LP_TO_UNSTAKE (err u4023))
(define-constant ERR_NO_EARLY_LP_TO_UNSTAKE (err u4024))
(define-constant ERR_NO_CLAIMABLE_REWARDS (err u4025))
(define-constant ERR_INVALID_FEE (err u4026))

;; Contract deployer address
(define-constant CONTRACT_DEPLOYER tx-sender)

;; Number of bins per pool and center bin ID as unsigned ints
(define-constant NUM_OF_BINS u1001)
(define-constant CENTER_BIN_ID (/ NUM_OF_BINS u2))

;; Maximum BPS
(define-constant FEE_SCALE_BPS u10000)
(define-constant REWARD_SCALE_BPS u1000000)

;; Admins list and helper var used to remove admins
(define-data-var admins (list 5 principal) (list tx-sender))
(define-data-var admin-helper principal tx-sender)

;; Helper value used for removing a bin-id from the bins-staked list
(define-data-var helper-value uint u0)

;; Staking and early unstake statuses
(define-data-var staking-status bool true)
(define-data-var early-unstake-status bool true)

;; Fee address and fee for early unstake
(define-data-var early-unstake-fee-address principal tx-sender)
(define-data-var early-unstake-fee uint u50)

;; Minimum staking duration in blocks
(define-data-var minimum-staking-duration uint u1)

;; Default reward period duration in blocks
(define-data-var default-reward-period-duration uint u10000)

;; Total amount of LP tokens staked
(define-data-var total-lp-staked uint u0)

;; Total rewards claimed across all bins
(define-data-var total-rewards-claimed uint u0)

;; Define mappings
(define-map bin-data uint {
	lp-staked: uint,
	reward-per-block: uint,
	reward-period-duration: uint,
	reward-index: uint,
	last-reward-index-update: uint,
	reward-period-end-block: uint
})

(define-map user-data principal {
	bins-staked: (list 1001 uint),
	lp-staked: uint
})

(define-map user-data-at-bin {user: principal, bin-id: uint} {
	lp-staked: uint,
	accrued-rewards: uint,
	reward-index: uint,
	last-stake-height: uint
})

(define-read-only (get-admins)
	(ok (var-get admins))
)

(define-read-only (get-admin-helper)
	(ok (var-get admin-helper))
)

(define-read-only (get-helper-value)
	(ok (var-get helper-value))
)

(define-read-only (get-staking-status)
	(ok (var-get staking-status))
)

(define-read-only (get-early-unstake-status)
	(ok (var-get early-unstake-status))
)

(define-read-only (get-early-unstake-fee-address)
	(ok (var-get early-unstake-fee-address))
)

(define-read-only (get-early-unstake-fee)
	(ok (var-get early-unstake-fee))
)

(define-read-only (get-minimum-staking-duration)
	(ok (var-get minimum-staking-duration))
)

(define-read-only (get-default-reward-period-duration)
	(ok (var-get default-reward-period-duration))
)

(define-read-only (get-total-lp-staked)
	(ok (var-get total-lp-staked))
)

(define-read-only (get-total-rewards-claimed)
	(ok (var-get total-rewards-claimed))
)

(define-read-only (get-bin (bin-id uint))
	(ok (map-get? bin-data bin-id))
)

(define-read-only (get-user (user principal))
	(ok (map-get? user-data user))
)

(define-read-only (get-user-data-at-bin (user principal) (bin-id uint))
	(ok (map-get? user-data-at-bin {user: user, bin-id: bin-id}))
)

;; Get the updated reward index at a bin
(define-read-only (get-updated-reward-index (bin-id uint))
	(let (
		(current-bin-data (unwrap! (map-get? bin-data bin-id) ERR_NO_BIN_DATA))
		(lp-staked (get lp-staked current-bin-data))
		(reward-per-block (get reward-per-block current-bin-data))
		(reward-index (get reward-index current-bin-data))
		(last-reward-index-update (get last-reward-index-update current-bin-data))
		(reward-period-end-block (get reward-period-end-block current-bin-data))
		(reward-period-effective-block (if (> reward-period-end-block u0)
																			 (if (> stacks-block-height reward-period-end-block)
																					 reward-period-end-block
																					 stacks-block-height)
																			 stacks-block-height))
	)
		;; Get updated reward-index, rewards-to-distribute, and reward-period-effective-block
		(if (and (> lp-staked u0) (> reward-period-effective-block last-reward-index-update) (> reward-per-block u0))
			(let (
				(blocks-since-last-update (- reward-period-effective-block last-reward-index-update))
				(rewards-to-distribute (* reward-per-block blocks-since-last-update))
				(reward-index-delta (/ (* rewards-to-distribute REWARD_SCALE_BPS) lp-staked))
			)
				(ok {reward-index: (+ reward-index reward-index-delta), rewards-to-distribute: rewards-to-distribute, reward-period-effective-block: reward-period-effective-block})
			)
			;; Return reward-index, rewards-to-distribute, and reward-period-effective-block
			(ok {reward-index: reward-index, rewards-to-distribute: u0, reward-period-effective-block: reward-period-effective-block})
		)
	)
)

;; Get claimable rewards for a user at a bin
(define-read-only (get-claimable-rewards (user principal) (bin-id int))
	(let (
		(unsigned-bin-id (to-uint (+ bin-id (to-int CENTER_BIN_ID))))
		(current-user-data-at-bin (unwrap! (map-get? user-data-at-bin {user: user, bin-id: unsigned-bin-id}) ERR_NO_USER_DATA_AT_BIN))
		(reward-index-delta (- (get reward-index (unwrap-panic (get-updated-reward-index unsigned-bin-id))) (get reward-index current-user-data-at-bin)))
		(pending-rewards (/ (* (get lp-staked current-user-data-at-bin) reward-index-delta) REWARD_SCALE_BPS))
		(accrued-rewards (get accrued-rewards current-user-data-at-bin))
	)
		;; Return pending-rewards, accrued-rewards, and claimable-rewards
		(ok {pending-rewards: pending-rewards, accrued-rewards: accrued-rewards, claimable-rewards: (+ pending-rewards accrued-rewards)})
	)
)

;; Add an admin to the admins list
(define-public (add-admin (admin principal))
	(let (
		(admins-list (var-get admins))
		(caller tx-sender)
	)
		;; Assert caller is an existing admin and new admin is not in admins-list
		(asserts! (is-some (index-of admins-list caller)) ERR_NOT_AUTHORIZED)
		(asserts! (is-none (index-of admins-list admin)) ERR_ALREADY_ADMIN)

		;; Add admin to list with max length of 5
		(var-set admins (unwrap! (as-max-len? (append admins-list admin) u5) ERR_ADMIN_LIMIT_REACHED))

		(print {action: "add-admin", caller: caller, data: {admin: admin}})
		(ok true)
	)
)

;; Remove an admin from the admins list
(define-public (remove-admin (admin principal))
	(let (
		(admins-list (var-get admins))
		(caller tx-sender)
	)
		;; Assert caller is an existing admin and admin to remove is in admins-list
		(asserts! (is-some (index-of admins-list caller)) ERR_NOT_AUTHORIZED)
		(asserts! (is-some (index-of admins-list admin)) ERR_ADMIN_NOT_IN_LIST)

		;; Assert contract deployer cannot be removed
		(asserts! (not (is-eq admin CONTRACT_DEPLOYER)) ERR_CANNOT_REMOVE_CONTRACT_DEPLOYER)

		;; Set admin-helper to admin to remove and filter admins-list to remove admin
		(var-set admin-helper admin)
		(var-set admins (filter admin-not-removable admins-list))

		(print {action: "remove-admin", caller: caller, data: {admin: admin}})
		(ok true)
	)
)

;; Enable or disable staking
(define-public (set-staking-status (status bool))
	(let (
		(caller tx-sender)
	)
		(begin
			;; Assert caller is an admin
			(asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)

			;; Set staking-status to status
			(var-set staking-status status)

			(print {action: "set-staking-status", caller: caller, data: {status: status}})
			(ok true)
		)
	)
)

;; Enable or disable early unstaking
(define-public (set-early-unstake-status (status bool))
	(let (
		(caller tx-sender)
	)
		(begin
			;; Assert caller is an admin
			(asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)

			;; Set early-unstake-status to status
			(var-set early-unstake-status status)

			(print {action: "set-early-unstake-status", caller: caller, data: {status: status}})
			(ok true)
		)
	)
)

;; Set early unstake fee address
(define-public (set-early-unstake-fee-address (address principal))
	(let (
		(caller tx-sender)
	)
		(begin
			;; Assert caller is an admin and address is standard principal
			(asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)
			(asserts! (is-standard address) ERR_INVALID_PRINCIPAL)

			;; Set early-unstake-fee-address to address
			(var-set early-unstake-fee-address address)

			(print {action: "set-early-unstake-fee-address", caller: caller, data: {address: address}})
			(ok true)
		)
	)
)

;; Set early unstake fee
(define-public (set-early-unstake-fee (fee uint))
	(let (
		(caller tx-sender)
	)
		(begin
			;; Assert caller is an admin and fee is less than maximum FEE_SCALE_BPS
			(asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)
			(asserts! (< fee FEE_SCALE_BPS) ERR_INVALID_FEE)

			;; Set early-unstake-fee to fee
			(var-set early-unstake-fee fee)

			(print {action: "set-early-unstake-fee", caller: caller, data: {fee: fee}})
			(ok true)
		)
	)
)

;; Set the minimum staking duration in blocks
(define-public (set-minimum-staking-duration (duration uint))
	(let (
		(caller tx-sender)
	)
		(begin
			;; Assert caller is an admin and duration is greater than 0
			(asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)
			(asserts! (> duration u0) ERR_INVALID_MIN_STAKING_DURATION)

			;; Set minimum-staking-duration to duration
			(var-set minimum-staking-duration duration)

			(print {action: "set-minimum-staking-duration", caller: caller, data: {duration: duration}})
			(ok true)
		)
	)
)

;; Set the default reward period duration in blocks
(define-public (set-default-reward-period-duration (duration uint))
	(let (
		(caller tx-sender)
	)
		(begin
			;; Assert caller is an admin and duration is greater than 0
			(asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)
			(asserts! (> duration u0) ERR_INVALID_REWARD_PERIOD_DURATION)

			;; Set default-reward-period-duration to duration
			(var-set default-reward-period-duration duration)

			(print {action: "set-default-reward-period-duration", caller: caller, data: {duration: duration}})
			(ok true)
		)
	)
)

;; Set the reward period duration in blocks for a bin
(define-public (set-reward-period-duration (bin-id int) (duration uint))
	(let (
		(unsigned-bin-id (to-uint (+ bin-id (to-int CENTER_BIN_ID))))
		(current-bin-data (unwrap! (map-get? bin-data unsigned-bin-id) ERR_NO_BIN_DATA))
		(updated-reward-index (unwrap-panic (get-updated-reward-index unsigned-bin-id)))
		(caller tx-sender)
	)
		(begin
			;; Assert caller is an admin and duration is greater than 0
			(asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)
			(asserts! (> duration u0) ERR_INVALID_REWARD_PERIOD_DURATION)

			;; Assert current reward period has passed
			(asserts! (> stacks-block-height (get reward-period-end-block current-bin-data)) ERR_REWARD_PERIOD_HAS_NOT_PASSED)

			;; Update bin-data mapping
			(map-set bin-data unsigned-bin-id (merge current-bin-data {
				reward-index: (get reward-index updated-reward-index),
				reward-period-duration: duration,
				last-reward-index-update: (get reward-period-effective-block updated-reward-index)
			}))

			(print {action: "set-reward-period-duration", caller: caller, data: {bin-id: bin-id, duration: duration}})
			(ok true)
		)
	)
)

;; Set rewards to distribute for a bin
(define-public (set-rewards-to-distribute (bin-id int) (amount uint))
	(let (
		(unsigned-bin-id (to-uint (+ bin-id (to-int CENTER_BIN_ID))))
		(caller tx-sender)
	)
		(begin
			;; Assert caller is an admin
			(asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)

			;; Assert unsigned-bin-id is less than NUM_OF_BINS
			(asserts! (< unsigned-bin-id NUM_OF_BINS) ERR_INVALID_BIN_ID)

			;; Update reward-index for bin
			(if (is-some (map-get? bin-data unsigned-bin-id))
					(unwrap-panic (update-reward-index unsigned-bin-id))
					false)

			(let (
				(current-bin-data (default-to {lp-staked: u0, reward-per-block: u0, reward-period-duration: (var-get default-reward-period-duration), reward-index: u0, last-reward-index-update: stacks-block-height, reward-period-end-block: u0} (map-get? bin-data unsigned-bin-id)))
				(current-reward-per-block (get reward-per-block current-bin-data))
				(current-reward-period-duration (get reward-period-duration current-bin-data))
				(current-reward-period-end-block (get reward-period-end-block current-bin-data))
				(reward-period-is-active (> current-reward-period-end-block stacks-block-height))
				(reward-period-time-left (if reward-period-is-active
																		 (- current-reward-period-end-block stacks-block-height)
																		 u0))
				(current-remaining-rewards (if reward-period-is-active
																			 (* current-reward-per-block reward-period-time-left)
																			 u0))
				(updated-rewards-to-distribute (+ amount current-remaining-rewards))
				(updated-reward-per-block (if (> updated-rewards-to-distribute u0)
																			(/ updated-rewards-to-distribute current-reward-period-duration)
																			u0))
				(updated-reward-period-end-block (if (> updated-reward-per-block u0)
																						 (+ stacks-block-height current-reward-period-duration)
																						 stacks-block-height))
			)
				;; Assert updated-rewards-to-distribute is less than or equal to the contract's reward token balance
				(asserts! (<= updated-rewards-to-distribute (unwrap! (get-reward-token-balance) ERR_CANNOT_GET_TOKEN_BALANCE)) ERR_INSUFFICIENT_TOKEN_BALANCE)

				;; Update bin-data mapping
				(map-set bin-data unsigned-bin-id (merge current-bin-data {
					reward-per-block: updated-reward-per-block,
					last-reward-index-update: (if (> updated-reward-per-block u0)
																				stacks-block-height
																				(get last-reward-index-update current-bin-data)),
					reward-period-end-block: updated-reward-period-end-block
				}))

				(print {
					action: "set-rewards-to-distribute",
					caller: caller,
					data: {
						bin-id: bin-id,
						amount: amount,
						updated-rewards-to-distribute: updated-rewards-to-distribute,
						updated-reward-per-block: updated-reward-per-block,
						updated-reward-period-end-block: updated-reward-period-end-block
					}
				})
				(ok true)
			)
		)
	)
)

;; Stake LP tokens for a bin
(define-public (stake-lp-tokens (bin-id int) (amount uint))
	(let (
		(caller tx-sender)
		(unsigned-bin-id (to-uint (+ bin-id (to-int CENTER_BIN_ID))))
		(current-bin-data (unwrap! (map-get? bin-data unsigned-bin-id) ERR_NO_BIN_DATA))
		(current-user-data (map-get? user-data caller))
		(current-user-data-at-bin (map-get? user-data-at-bin {user: caller, bin-id: unsigned-bin-id}))
		(current-user-bins-staked (default-to (list ) (get bins-staked current-user-data)))
		(updated-user-bins-staked (if (is-none (index-of current-user-bins-staked unsigned-bin-id))
																	(unwrap! (as-max-len? (concat current-user-bins-staked (list unsigned-bin-id)) u1001) ERR_BINS_STAKED_OVERFLOW)
																	current-user-bins-staked))
		(updated-user-lp-staked (+ (default-to u0 (get lp-staked current-user-data)) amount))
		(updated-bin-lp-staked (+ (get lp-staked current-bin-data) amount))
		(updated-total-lp-staked (+ (var-get total-lp-staked) amount))
	)
		(begin
			;; Assert staking-status is true and amount is greater than 0
			(asserts! (var-get staking-status) ERR_STAKING_DISABLED)
			(asserts! (> amount u0) ERR_INVALID_AMOUNT)

			;; Update reward-index for bin
			(unwrap-panic (update-reward-index unsigned-bin-id))

			;; Update total LP staked, bin-data mapping, user-data-at-bin mapping, and user-data mapping
			(let (
				(updated-bin-data (unwrap! (map-get? bin-data unsigned-bin-id) ERR_NO_BIN_DATA))
				(updated-reward-index (get reward-index updated-bin-data))
				(updated-accrued-rewards (if (is-some current-user-data-at-bin)
																		 (get claimable-rewards (try! (get-claimable-rewards caller bin-id)))
																		 u0))
			)
				(var-set total-lp-staked updated-total-lp-staked)
				(map-set bin-data unsigned-bin-id (merge updated-bin-data {
					lp-staked: updated-bin-lp-staked
				}))
				(map-set user-data-at-bin {user: caller, bin-id: unsigned-bin-id} {
					lp-staked: (+ (default-to u0 (get lp-staked current-user-data-at-bin)) amount),
					accrued-rewards: updated-accrued-rewards,
					reward-index: updated-reward-index,
					last-stake-height: stacks-block-height
				})
				(map-set user-data caller {
					bins-staked: updated-user-bins-staked,
					lp-staked: updated-user-lp-staked
				})
			)

			;; Transfer amount LP tokens from caller to contract
			(try! (transfer-lp-token unsigned-bin-id amount caller current-contract))

			(print {
				action: "stake-lp-tokens",
				caller: caller,
				data: {
					bin-id: bin-id,
					amount: amount,
					user-bins-staked: updated-user-bins-staked,
					user-lp-staked: updated-user-lp-staked,
					total-lp-staked: updated-total-lp-staked
				}
			})
			(ok true)
		)
	)
)

;; Unstake LP tokens for a bin
(define-public (unstake-lp-tokens (bin-id int))
	(let (
		(caller tx-sender)
		(unsigned-bin-id (to-uint (+ bin-id (to-int CENTER_BIN_ID))))
		(current-bin-data (unwrap! (map-get? bin-data unsigned-bin-id) ERR_NO_BIN_DATA))
		(current-user-data (unwrap! (map-get? user-data caller) ERR_NO_USER_DATA))
		(current-user-data-at-bin (unwrap! (map-get? user-data-at-bin {user: caller, bin-id: unsigned-bin-id}) ERR_NO_USER_DATA_AT_BIN))
		(lp-to-unstake (get lp-staked current-user-data-at-bin))
		(helper-value-unsigned-bin-id (var-set helper-value unsigned-bin-id))
		(updated-total-lp-staked (- (var-get total-lp-staked) lp-to-unstake))
		(updated-bin-lp-staked (- (get lp-staked current-bin-data) lp-to-unstake))
		(updated-user-bins-staked (filter filter-values-eq-helper-value (get bins-staked current-user-data)))
		(updated-user-lp-staked (- (get lp-staked current-user-data) lp-to-unstake))
	)
		(begin
			;; Assert lp-to-unstake is greater than 0 and minimum staking duration has passed
			(asserts! (> lp-to-unstake u0) ERR_NO_LP_TO_UNSTAKE)
			(asserts! (>= (- stacks-block-height (get last-stake-height current-user-data-at-bin)) (var-get minimum-staking-duration)) ERR_MINIMUM_STAKING_DURATION_HAS_NOT_PASSED)

			;; Update reward-index for bin
			(unwrap-panic (update-reward-index unsigned-bin-id))

			;; Update total LP staked, bin-data mapping, user-data-at-bin mapping, and user-data mapping
			(let (
				(updated-bin-data (unwrap! (map-get? bin-data unsigned-bin-id) ERR_NO_BIN_DATA))
				(updated-reward-index (get reward-index updated-bin-data))
				(updated-accrued-rewards (get claimable-rewards (try! (get-claimable-rewards caller bin-id))))
			)
				(var-set total-lp-staked updated-total-lp-staked)
				(map-set bin-data unsigned-bin-id (merge updated-bin-data {
					lp-staked: updated-bin-lp-staked
				}))
				(map-set user-data-at-bin {user: caller, bin-id: unsigned-bin-id} (merge current-user-data-at-bin {
					lp-staked: u0,
					accrued-rewards: updated-accrued-rewards,
					reward-index: updated-reward-index
				}))
				(map-set user-data caller {
					bins-staked: updated-user-bins-staked,
					lp-staked: updated-user-lp-staked
				})
			)

			;; Transfer lp-to-unstake LP tokens from contract to caller
			(try! (as-contract? ((with-all-assets-unsafe)) (try! (transfer-lp-token unsigned-bin-id lp-to-unstake tx-sender caller))))

			(print {
				action: "unstake-lp-tokens",
				caller: caller,
				data: {
					bin-id: bin-id,
					lp-to-unstake: lp-to-unstake,
					user-bins-staked: updated-user-bins-staked,
					user-lp-staked: updated-user-lp-staked,
					total-lp-staked: updated-total-lp-staked
				}
			})
			(ok true)
		)
	)
)

;; Early unstake LP tokens at a bin
(define-public (early-unstake-lp-tokens (bin-id int))
	(let (
		(caller tx-sender)
		(unsigned-bin-id (to-uint (+ bin-id (to-int CENTER_BIN_ID))))
		(current-bin-data (unwrap! (map-get? bin-data unsigned-bin-id) ERR_NO_BIN_DATA))
		(current-user-data (unwrap! (map-get? user-data caller) ERR_NO_USER_DATA))
		(current-user-data-at-bin (unwrap! (map-get? user-data-at-bin {user: caller, bin-id: unsigned-bin-id}) ERR_NO_USER_DATA_AT_BIN))
		(lp-to-unstake (get lp-staked current-user-data-at-bin))
		(lp-to-unstake-fees (/ (* lp-to-unstake (var-get early-unstake-fee)) FEE_SCALE_BPS))
		(lp-to-unstake-user (- lp-to-unstake lp-to-unstake-fees))
		(helper-value-unsigned-bin-id (var-set helper-value unsigned-bin-id))
		(updated-total-lp-staked (- (var-get total-lp-staked) lp-to-unstake))
		(updated-bin-lp-staked (- (get lp-staked current-bin-data) lp-to-unstake))
		(updated-user-bins-staked (filter filter-values-eq-helper-value (get bins-staked current-user-data)))
		(updated-user-lp-staked (- (get lp-staked current-user-data) lp-to-unstake))
	)
		(begin
			;; Assert early-unstake-status is true
			(asserts! (var-get early-unstake-status) ERR_EARLY_UNSTAKE_DISABLED)

			;; Assert lp-to-unstake is greater than 0 and minimum staking duration hasn't passed
			(asserts! (> lp-to-unstake u0) ERR_NO_EARLY_LP_TO_UNSTAKE)
			(asserts! (< (- stacks-block-height (get last-stake-height current-user-data-at-bin)) (var-get minimum-staking-duration)) ERR_MINIMUM_STAKING_DURATION_PASSED)

			;; Update reward-index for bin
			(unwrap-panic (update-reward-index unsigned-bin-id))

			;; Update total LP staked, bin-data mapping, user-data-at-bin mapping, and user-data mapping
			(let (
				(updated-bin-data (unwrap! (map-get? bin-data unsigned-bin-id) ERR_NO_BIN_DATA))
				(updated-reward-index (get reward-index updated-bin-data))
				(updated-accrued-rewards (get claimable-rewards (try! (get-claimable-rewards caller bin-id))))
			)
				(var-set total-lp-staked updated-total-lp-staked)
				(map-set bin-data unsigned-bin-id (merge updated-bin-data {
					lp-staked: updated-bin-lp-staked
				}))
				(map-set user-data-at-bin {user: caller, bin-id: unsigned-bin-id} (merge current-user-data-at-bin {
					lp-staked: u0,
					accrued-rewards: updated-accrued-rewards,
					reward-index: updated-reward-index
				}))
				(map-set user-data caller {
					bins-staked: updated-user-bins-staked,
					lp-staked: updated-user-lp-staked
				})
			)

			;; Transfer lp-to-unstake-user LP tokens from contract to caller
			(try! (as-contract? ((with-all-assets-unsafe)) (try! (transfer-lp-token unsigned-bin-id lp-to-unstake-user tx-sender caller))))

			;; Transfer lp-to-unstake-fees LP tokens from contract to early-unstake-fee-address
			(if (> lp-to-unstake-fees u0)
					(try! (as-contract? ((with-all-assets-unsafe)) (try! (transfer-lp-token unsigned-bin-id lp-to-unstake-fees tx-sender (var-get early-unstake-fee-address)))))
					false)

			(print {
				action: "early-unstake-lp-tokens",
				caller: caller,
				data: {
					bin-id: bin-id,
					lp-to-unstake: lp-to-unstake,
					user-bins-staked: updated-user-bins-staked,
					user-lp-staked: updated-user-lp-staked,
					total-lp-staked: updated-total-lp-staked
				}
			})
			(ok true)
		)
	)
)

;; Claim any claimable rewards at a bin
(define-public (claim-rewards (bin-id int))
	(let (
		(caller tx-sender)
		(unsigned-bin-id (to-uint (+ bin-id (to-int CENTER_BIN_ID))))
		(current-user-data-at-bin (unwrap! (map-get? user-data-at-bin {user: caller, bin-id: unsigned-bin-id}) ERR_NO_USER_DATA_AT_BIN))
		(claimable-rewards (get claimable-rewards (try! (get-claimable-rewards caller bin-id))))
	)
		(begin
			;; Assert claimable-rewards is greater than 0
			(asserts! (> claimable-rewards u0) ERR_NO_CLAIMABLE_REWARDS)

			;; Assert claimable-rewards is less than or equal to the contract's reward token balance
			(asserts! (<= claimable-rewards (unwrap! (get-reward-token-balance) ERR_CANNOT_GET_TOKEN_BALANCE)) ERR_INSUFFICIENT_TOKEN_BALANCE)

			;; Update reward-index for bin
			(unwrap-panic (update-reward-index unsigned-bin-id))

			;; Transfer claimable-rewards rewards token from contract to caller
			(try! (as-contract? ((with-all-assets-unsafe)) (try! (transfer-reward-token claimable-rewards tx-sender caller))))

			;; Update user-data-at-bin mapping
			(map-set user-data-at-bin {user: caller, bin-id: unsigned-bin-id} (merge current-user-data-at-bin {
				accrued-rewards: u0,
				reward-index: (get reward-index (unwrap-panic (get-updated-reward-index unsigned-bin-id)))
			}))

			;; Update total-rewards-claimed
			(var-set total-rewards-claimed (+ (var-get total-rewards-claimed) claimable-rewards))

			(print {action: "claim-rewards", caller: caller, data: {bin-id: bin-id, claimable-rewards: claimable-rewards}})
			(ok claimable-rewards)
		)
	)
)

;; Withdraw reward token from contract
(define-public (withdraw-rewards (amount uint) (recipient principal))
	(let (
		(caller tx-sender)
	)
		(begin
			;; Assert caller is an admin and recipient is standard principal
			(asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)
			(asserts! (is-standard recipient) ERR_INVALID_PRINCIPAL)

			;; Assert amount is greater than 0
			(asserts! (> amount u0) ERR_INVALID_AMOUNT)

			;; Assert amount is less than or equal to the contract's reward token balance
			(asserts! (<= amount (unwrap! (get-reward-token-balance) ERR_CANNOT_GET_TOKEN_BALANCE)) ERR_INSUFFICIENT_TOKEN_BALANCE)

			;; Transfer amount rewards token from contract to recipient
			(try! (as-contract? ((with-all-assets-unsafe)) (try! (transfer-reward-token amount tx-sender recipient))))

			(print {action: "withdraw-rewards", caller: caller, data: {amount: amount, recipient: recipient}})
			(ok true)
		)
	)
)

;; Update reward index for a bin
(define-public (update-reward-index (bin-id uint))
	(let (
		(current-bin-data (unwrap! (map-get? bin-data bin-id) ERR_NO_BIN_DATA))
		(updated-reward-index (unwrap-panic (get-updated-reward-index bin-id)))
		(reward-period-effective-block (get reward-period-effective-block updated-reward-index))
		(caller tx-sender)
	)
		;; Update reward index if reward-period-effective-block is greater than last-reward-index-update
		(if (> reward-period-effective-block (get last-reward-index-update current-bin-data))
				(begin
					;; Update bin-data mapping
					(map-set bin-data bin-id (merge (unwrap! (map-get? bin-data bin-id) ERR_NO_BIN_DATA) {
						reward-index: (get reward-index updated-reward-index),
						last-reward-index-update: reward-period-effective-block
					}))

					(print {action: "update-reward-index", caller: caller, data: {bin-id: bin-id, updated-reward-index: updated-reward-index}})
					(ok true)
				)
				(ok true))
	)
)

;; Get claimable rewards for multiple bins
(define-public (get-claimable-rewards-multi
		(users (list 350 principal))
		(bin-ids (list 350 int))
	)
	(ok (map get-claimable-rewards users bin-ids))
)

;; Set reward period duration for multiple bins
(define-public (set-reward-period-duration-multi
		(bin-ids (list 350 int))
		(durations (list 350 uint))
	)
	(ok (map set-reward-period-duration bin-ids durations))
)

;; Set rewards to distribute for multiple bins
(define-public (set-rewards-to-distribute-multi
		(bin-ids (list 350 int))
		(amounts (list 350 uint))
	)
	(ok (map set-rewards-to-distribute bin-ids amounts))
)

;; Stake LP tokens for multiple bins
(define-public (stake-lp-tokens-multi
		(bin-ids (list 350 int))
		(amounts (list 350 uint))
	)
	(ok (map stake-lp-tokens bin-ids amounts))
)

;; Unstake LP tokens for multiple bins
(define-public (unstake-lp-tokens-multi
		(bin-ids (list 350 int))
	)
	(ok (map unstake-lp-tokens bin-ids))
)

;; Early unstake LP tokens for multiple bins
(define-public (early-unstake-lp-tokens-multi
		(bin-ids (list 350 int))
	)
	(ok (map early-unstake-lp-tokens bin-ids))
)

;; Claim any claimable rewards for multiple bins
(define-public (claim-rewards-multi
		(bin-ids (list 350 int))
	)
	(ok (map claim-rewards bin-ids))
)

;; Update reward index for multiple bins
(define-public (update-reward-index-multi
		(bin-ids (list 350 uint))
	)
	(ok (map update-reward-index bin-ids))
)

;; Helper function for removing an admin
(define-private (admin-not-removable (admin principal))
	(not (is-eq admin (var-get admin-helper)))
)

;; Filter function for removing a bin-id from the bins-staked list
(define-private (filter-values-eq-helper-value (value uint))
	(not (is-eq value (var-get helper-value)))
)

;; Get reward token balance for contract
(define-private (get-reward-token-balance)
	(ok (unwrap! (contract-call? .token-stx-v-1-1 get-balance
							 current-contract) ERR_CANNOT_GET_TOKEN_BALANCE))
)

;; Transfer LP token
(define-private (transfer-lp-token (bin-id uint) (amount uint) (sender principal) (recipient principal))
	(ok (unwrap! (contract-call? .dlmm-pool-sbtc-usdc-v-1-1 transfer
							 bin-id amount sender recipient) ERR_TOKEN_TRANSFER_FAILED))
)

;; Transfer reward token
(define-private (transfer-reward-token (amount uint) (sender principal) (recipient principal))
	(ok (unwrap! (contract-call? .token-stx-v-1-1 transfer
							 amount sender recipient none) ERR_TOKEN_TRANSFER_FAILED))
)