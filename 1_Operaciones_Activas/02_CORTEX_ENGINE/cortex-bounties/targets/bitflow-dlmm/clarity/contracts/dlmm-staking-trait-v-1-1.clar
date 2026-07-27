;; dlmm-staking-trait-v-1-1

(define-trait dlmm-staking-trait
	(
		(get-helper-value () (response uint uint))
		(get-staking-status () (response bool uint))
		(get-early-unstake-status () (response bool uint))
		(get-early-unstake-fee-address () (response principal uint))
		(get-early-unstake-fee () (response uint uint))
		(get-minimum-staking-duration () (response uint uint))
		(get-default-reward-period-duration () (response uint uint))
		(get-total-lp-staked () (response uint uint))
		(get-total-rewards-claimed () (response uint uint))
		(get-bin (uint) (response (optional {
			lp-staked: uint,
			reward-per-block: uint,
			reward-period-duration: uint,
			reward-index: uint,
			last-reward-index-update: uint,
			reward-period-end-block: uint
		}) uint))
		(get-user (principal) (response (optional {
			bins-staked: (list 1001 uint),
			lp-staked: uint
		}) uint))
		(get-user-data-at-bin (principal uint) (response (optional {
			lp-staked: uint,
			accrued-rewards: uint,
			reward-index: uint,
			last-stake-height: uint
		}) uint))
		(get-updated-reward-index (uint) (response {
			reward-index: uint,
			rewards-to-distribute: uint,
			reward-period-effective-block: uint
		} uint))
		(get-claimable-rewards (principal int) (response {
			pending-rewards: uint,
			accrued-rewards: uint,
			claimable-rewards: uint
		} uint))
		(stake-lp-tokens (int uint) (response bool uint))
		(unstake-lp-tokens (int) (response bool uint))
		(early-unstake-lp-tokens (int) (response bool uint))
		(claim-rewards (int) (response uint uint))
		(update-reward-index (uint) (response bool uint))
	)
)