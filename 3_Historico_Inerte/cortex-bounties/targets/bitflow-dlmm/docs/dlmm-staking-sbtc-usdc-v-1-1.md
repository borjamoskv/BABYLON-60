
# dlmm-staking-sbtc-usdc-v-1-1

[`dlmm-staking-sbtc-usdc-v-1-1.clar`](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar)

dlmm-staking-sbtc-usdc-v-1-1

**Public functions:**

- [`add-admin`](#add-admin)
- [`remove-admin`](#remove-admin)
- [`set-staking-status`](#set-staking-status)
- [`set-early-unstake-status`](#set-early-unstake-status)
- [`set-early-unstake-fee-address`](#set-early-unstake-fee-address)
- [`set-early-unstake-fee`](#set-early-unstake-fee)
- [`set-minimum-staking-duration`](#set-minimum-staking-duration)
- [`set-default-reward-period-duration`](#set-default-reward-period-duration)
- [`set-reward-period-duration`](#set-reward-period-duration)
- [`set-rewards-to-distribute`](#set-rewards-to-distribute)
- [`stake-lp-tokens`](#stake-lp-tokens)
- [`unstake-lp-tokens`](#unstake-lp-tokens)
- [`early-unstake-lp-tokens`](#early-unstake-lp-tokens)
- [`claim-rewards`](#claim-rewards)
- [`withdraw-rewards`](#withdraw-rewards)
- [`update-reward-index`](#update-reward-index)
- [`get-claimable-rewards-multi`](#get-claimable-rewards-multi)
- [`set-reward-period-duration-multi`](#set-reward-period-duration-multi)
- [`set-rewards-to-distribute-multi`](#set-rewards-to-distribute-multi)
- [`stake-lp-tokens-multi`](#stake-lp-tokens-multi)
- [`unstake-lp-tokens-multi`](#unstake-lp-tokens-multi)
- [`early-unstake-lp-tokens-multi`](#early-unstake-lp-tokens-multi)
- [`claim-rewards-multi`](#claim-rewards-multi)
- [`update-reward-index-multi`](#update-reward-index-multi)

**Read-only functions:**

- [`get-admins`](#get-admins)
- [`get-admin-helper`](#get-admin-helper)
- [`get-helper-value`](#get-helper-value)
- [`get-staking-status`](#get-staking-status)
- [`get-early-unstake-status`](#get-early-unstake-status)
- [`get-early-unstake-fee-address`](#get-early-unstake-fee-address)
- [`get-early-unstake-fee`](#get-early-unstake-fee)
- [`get-minimum-staking-duration`](#get-minimum-staking-duration)
- [`get-default-reward-period-duration`](#get-default-reward-period-duration)
- [`get-total-lp-staked`](#get-total-lp-staked)
- [`get-total-rewards-claimed`](#get-total-rewards-claimed)
- [`get-bin`](#get-bin)
- [`get-user`](#get-user)
- [`get-user-data-at-bin`](#get-user-data-at-bin)
- [`get-updated-reward-index`](#get-updated-reward-index)
- [`get-claimable-rewards`](#get-claimable-rewards)

**Private functions:**

- [`admin-not-removable`](#admin-not-removable)
- [`filter-values-eq-helper-value`](#filter-values-eq-helper-value)
- [`get-reward-token-balance`](#get-reward-token-balance)
- [`transfer-lp-token`](#transfer-lp-token)
- [`transfer-reward-token`](#transfer-reward-token)

**Maps**

- [`bin-data`](#bin-data)
- [`user-data`](#user-data)
- [`user-data-at-bin`](#user-data-at-bin)

**Variables**

- [`admins`](#admins)
- [`admin-helper`](#admin-helper)
- [`helper-value`](#helper-value)
- [`staking-status`](#staking-status)
- [`early-unstake-status`](#early-unstake-status)
- [`early-unstake-fee-address`](#early-unstake-fee-address)
- [`early-unstake-fee`](#early-unstake-fee)
- [`minimum-staking-duration`](#minimum-staking-duration)
- [`default-reward-period-duration`](#default-reward-period-duration)
- [`total-lp-staked`](#total-lp-staked)
- [`total-rewards-claimed`](#total-rewards-claimed)

**Constants**

- [`ERR_NOT_AUTHORIZED`](#err_not_authorized)
- [`ERR_INVALID_AMOUNT`](#err_invalid_amount)
- [`ERR_INVALID_PRINCIPAL`](#err_invalid_principal)
- [`ERR_ALREADY_ADMIN`](#err_already_admin)
- [`ERR_ADMIN_LIMIT_REACHED`](#err_admin_limit_reached)
- [`ERR_ADMIN_NOT_IN_LIST`](#err_admin_not_in_list)
- [`ERR_CANNOT_REMOVE_CONTRACT_DEPLOYER`](#err_cannot_remove_contract_deployer)
- [`ERR_STAKING_DISABLED`](#err_staking_disabled)
- [`ERR_EARLY_UNSTAKE_DISABLED`](#err_early_unstake_disabled)
- [`ERR_TOKEN_TRANSFER_FAILED`](#err_token_transfer_failed)
- [`ERR_CANNOT_GET_TOKEN_BALANCE`](#err_cannot_get_token_balance)
- [`ERR_INSUFFICIENT_TOKEN_BALANCE`](#err_insufficient_token_balance)
- [`ERR_INVALID_MIN_STAKING_DURATION`](#err_invalid_min_staking_duration)
- [`ERR_MINIMUM_STAKING_DURATION_HAS_NOT_PASSED`](#err_minimum_staking_duration_has_not_passed)
- [`ERR_MINIMUM_STAKING_DURATION_PASSED`](#err_minimum_staking_duration_passed)
- [`ERR_INVALID_REWARD_PERIOD_DURATION`](#err_invalid_reward_period_duration)
- [`ERR_REWARD_PERIOD_HAS_NOT_PASSED`](#err_reward_period_has_not_passed)
- [`ERR_BINS_STAKED_OVERFLOW`](#err_bins_staked_overflow)
- [`ERR_INVALID_BIN_ID`](#err_invalid_bin_id)
- [`ERR_NO_BIN_DATA`](#err_no_bin_data)
- [`ERR_NO_USER_DATA`](#err_no_user_data)
- [`ERR_NO_USER_DATA_AT_BIN`](#err_no_user_data_at_bin)
- [`ERR_NO_LP_TO_UNSTAKE`](#err_no_lp_to_unstake)
- [`ERR_NO_EARLY_LP_TO_UNSTAKE`](#err_no_early_lp_to_unstake)
- [`ERR_NO_CLAIMABLE_REWARDS`](#err_no_claimable_rewards)
- [`ERR_INVALID_FEE`](#err_invalid_fee)
- [`CONTRACT_DEPLOYER`](#contract_deployer)
- [`NUM_OF_BINS`](#num_of_bins)
- [`CENTER_BIN_ID`](#center_bin_id)
- [`FEE_SCALE_BPS`](#fee_scale_bps)
- [`REWARD_SCALE_BPS`](#reward_scale_bps)


## Functions

### get-admins

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L97)

`(define-read-only (get-admins () (response (list 5 principal) none))`

Get admins list

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-admins)
  (ok (var-get admins))
)
```
</details>




### get-admin-helper

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L102)

`(define-read-only (get-admin-helper () (response principal none))`

Get admin helper var

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-admin-helper)
  (ok (var-get admin-helper))
)
```
</details>




### get-helper-value

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L107)

`(define-read-only (get-helper-value () (response uint none))`

Get helper value var

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-helper-value)
  (ok (var-get helper-value))
)
```
</details>




### get-staking-status

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L112)

`(define-read-only (get-staking-status () (response bool none))`

Get staking status

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-staking-status)
  (ok (var-get staking-status))
)
```
</details>




### get-early-unstake-status

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L117)

`(define-read-only (get-early-unstake-status () (response bool none))`

Get early unstake status

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-early-unstake-status)
  (ok (var-get early-unstake-status))
)
```
</details>




### get-early-unstake-fee-address

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L122)

`(define-read-only (get-early-unstake-fee-address () (response principal none))`

Get early unstake fee address

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-early-unstake-fee-address)
  (ok (var-get early-unstake-fee-address))
)
```
</details>




### get-early-unstake-fee

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L127)

`(define-read-only (get-early-unstake-fee () (response uint none))`

Get early unstake fee

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-early-unstake-fee)
  (ok (var-get early-unstake-fee))
)
```
</details>




### get-minimum-staking-duration

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L132)

`(define-read-only (get-minimum-staking-duration () (response uint none))`

Get minimum staking duration

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-minimum-staking-duration)
  (ok (var-get minimum-staking-duration))
)
```
</details>




### get-default-reward-period-duration

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L137)

`(define-read-only (get-default-reward-period-duration () (response uint none))`

Get default reward period duration

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-default-reward-period-duration)
  (ok (var-get default-reward-period-duration))
)
```
</details>




### get-total-lp-staked

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L142)

`(define-read-only (get-total-lp-staked () (response uint none))`

Get total LP staked

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-total-lp-staked)
  (ok (var-get total-lp-staked))
)
```
</details>




### get-total-rewards-claimed

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L147)

`(define-read-only (get-total-rewards-claimed () (response uint none))`

Get total rewards claimed

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-total-rewards-claimed)
  (ok (var-get total-rewards-claimed))
)
```
</details>




### get-bin

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L152)

`(define-read-only (get-bin ((bin-id uint)) (response (optional (tuple (last-reward-index-update uint) (lp-staked uint) (reward-index uint) (reward-per-block uint) (reward-period-duration uint) (reward-period-end-block uint))) none))`

Get bin data

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-bin (bin-id uint))
  (ok (map-get? bin-data bin-id))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-id | uint |

### get-user

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L157)

`(define-read-only (get-user ((user principal)) (response (optional (tuple (bins-staked (list 1001 uint)) (lp-staked uint))) none))`

Get user data

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-user (user principal))
  (ok (map-get? user-data user))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| user | principal |

### get-user-data-at-bin

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L162)

`(define-read-only (get-user-data-at-bin ((user principal) (bin-id uint)) (response (optional (tuple (accrued-rewards uint) (last-stake-height uint) (lp-staked uint) (reward-index uint))) none))`

Get user data at a bin

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-user-data-at-bin (user principal) (bin-id uint))
  (ok (map-get? user-data-at-bin {user: user, bin-id: bin-id}))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| user | principal |
| bin-id | uint |

### get-updated-reward-index

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L167)

`(define-read-only (get-updated-reward-index ((bin-id uint)) (response (tuple (reward-index uint) (reward-period-effective-block uint) (rewards-to-distribute uint)) uint))`

Get the updated reward index at a bin

<details>
  <summary>Source code:</summary>

```clarity
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
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-id | uint |

### get-claimable-rewards

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L197)

`(define-read-only (get-claimable-rewards ((user principal) (bin-id int)) (response (tuple (accrued-rewards uint) (claimable-rewards uint) (pending-rewards uint)) uint))`

Get claimable rewards for a user at a bin

<details>
  <summary>Source code:</summary>

```clarity
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
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| user | principal |
| bin-id | int |

### add-admin

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L211)

`(define-public (add-admin ((admin principal)) (response bool uint))`

Add an admin to the admins list

<details>
  <summary>Source code:</summary>

```clarity
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

    ;; Print add admin data and return true
    (print {action: "add-admin", caller: caller, data: {admin: admin}})
    (ok true)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| admin | principal |

### remove-admin

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L230)

`(define-public (remove-admin ((admin principal)) (response bool uint))`

Remove an admin from the admins list

<details>
  <summary>Source code:</summary>

```clarity
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

    ;; Print remove admin data and return true
    (print {action: "remove-admin", caller: caller, data: {admin: admin}})
    (ok true)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| admin | principal |

### set-staking-status

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L253)

`(define-public (set-staking-status ((status bool)) (response bool uint))`

Enable or disable staking

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-staking-status (status bool))
  (let (
    (caller tx-sender)
  )
    (begin
      ;; Assert caller is an admin
      (asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)

      ;; Set staking-status to status
      (var-set staking-status status)

      ;; Print function data and return true
      (print {action: "set-staking-status", caller: caller, data: {status: status}})
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| status | bool |

### set-early-unstake-status

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L272)

`(define-public (set-early-unstake-status ((status bool)) (response bool uint))`

Enable or disable early unstaking

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-early-unstake-status (status bool))
  (let (
    (caller tx-sender)
  )
    (begin
      ;; Assert caller is an admin
      (asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)

      ;; Set early-unstake-status to status
      (var-set early-unstake-status status)

      ;; Print function data and return true
      (print {action: "set-early-unstake-status", caller: caller, data: {status: status}})
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| status | bool |

### set-early-unstake-fee-address

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L291)

`(define-public (set-early-unstake-fee-address ((address principal)) (response bool uint))`

Set early unstake fee address

<details>
  <summary>Source code:</summary>

```clarity
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

      ;; Print function data and return true
      (print {action: "set-early-unstake-fee-address", caller: caller, data: {address: address}})
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| address | principal |

### set-early-unstake-fee

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L311)

`(define-public (set-early-unstake-fee ((fee uint)) (response bool uint))`

Set early unstake fee

<details>
  <summary>Source code:</summary>

```clarity
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

      ;; Print function data and return true
      (print {action: "set-early-unstake-fee", caller: caller, data: {fee: fee}})
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| fee | uint |

### set-minimum-staking-duration

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L331)

`(define-public (set-minimum-staking-duration ((duration uint)) (response bool uint))`

Set the minimum staking duration in blocks

<details>
  <summary>Source code:</summary>

```clarity
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

      ;; Print function data and return true
      (print {action: "set-minimum-staking-duration", caller: caller, data: {duration: duration}})
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| duration | uint |

### set-default-reward-period-duration

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L351)

`(define-public (set-default-reward-period-duration ((duration uint)) (response bool uint))`

Set the default reward period duration in blocks

<details>
  <summary>Source code:</summary>

```clarity
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

      ;; Print function data and return true
      (print {action: "set-default-reward-period-duration", caller: caller, data: {duration: duration}})
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| duration | uint |

### set-reward-period-duration

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L371)

`(define-public (set-reward-period-duration ((bin-id int) (duration uint)) (response bool uint))`

Set the reward period duration in blocks for a bin

<details>
  <summary>Source code:</summary>

```clarity
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

      ;; Print function data and return true
      (print {action: "set-reward-period-duration", caller: caller, data: {bin-id: bin-id, duration: duration}})
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-id | int |
| duration | uint |

### set-rewards-to-distribute

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L401)

`(define-public (set-rewards-to-distribute ((bin-id int) (amount uint)) (response bool uint))`

Set rewards to distribute for a bin

<details>
  <summary>Source code:</summary>

```clarity
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

        ;; Print function data and return true
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
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-id | int |
| amount | uint |

### stake-lp-tokens

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L469)

`(define-public (stake-lp-tokens ((bin-id int) (amount uint)) (response bool uint))`

Stake LP tokens for a bin

<details>
  <summary>Source code:</summary>

```clarity
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

      ;; Print function data and return true
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
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-id | int |
| amount | uint |

### unstake-lp-tokens

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L537)

`(define-public (unstake-lp-tokens ((bin-id int)) (response bool uint))`

Unstake LP tokens for a bin

<details>
  <summary>Source code:</summary>

```clarity
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

      ;; Print function data and return true
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
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-id | int |

### early-unstake-lp-tokens

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L601)

`(define-public (early-unstake-lp-tokens ((bin-id int)) (response bool uint))`

Early unstake LP tokens at a bin

<details>
  <summary>Source code:</summary>

```clarity
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

      ;; Print function data and return true
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
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-id | int |

### claim-rewards

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L675)

`(define-public (claim-rewards ((bin-id int)) (response uint uint))`

Claim any claimable rewards at a bin

<details>
  <summary>Source code:</summary>

```clarity
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

      ;; Print function data and return true
      (print {action: "claim-rewards", caller: caller, data: {bin-id: bin-id, claimable-rewards: claimable-rewards}})
      (ok claimable-rewards)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-id | int |

### withdraw-rewards

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L712)

`(define-public (withdraw-rewards ((amount uint) (recipient principal)) (response bool uint))`

Withdraw reward token from contract

<details>
  <summary>Source code:</summary>

```clarity
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

      ;; Print function data and return true
      (print {action: "withdraw-rewards", caller: caller, data: {amount: amount, recipient: recipient}})
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| amount | uint |
| recipient | principal |

### update-reward-index

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L738)

`(define-public (update-reward-index ((bin-id uint)) (response bool uint))`

Update reward index for a bin

<details>
  <summary>Source code:</summary>

```clarity
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

          ;; Print function data and return true
          (print {action: "update-reward-index", caller: caller, data: {bin-id: bin-id, updated-reward-index: updated-reward-index}})
          (ok true)
        )
        (ok true))
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-id | uint |

### get-claimable-rewards-multi

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L763)

`(define-public (get-claimable-rewards-multi ((users (list 350 principal)) (bin-ids (list 350 int))) (response (list 350 (response (tuple (accrued-rewards uint) (claimable-rewards uint) (pending-rewards uint)) uint)) none))`

Get claimable rewards for multiple bins

<details>
  <summary>Source code:</summary>

```clarity
(define-public (get-claimable-rewards-multi
    (users (list 350 principal))
    (bin-ids (list 350 int))
  )
  (ok (map get-claimable-rewards users bin-ids))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| users | (list 350 principal) |
| bin-ids | (list 350 int) |

### set-reward-period-duration-multi

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L771)

`(define-public (set-reward-period-duration-multi ((bin-ids (list 350 int)) (durations (list 350 uint))) (response (list 350 (response bool uint)) none))`

Set reward period duration for multiple bins

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-reward-period-duration-multi
    (bin-ids (list 350 int))
    (durations (list 350 uint))
  )
  (ok (map set-reward-period-duration bin-ids durations))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-ids | (list 350 int) |
| durations | (list 350 uint) |

### set-rewards-to-distribute-multi

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L779)

`(define-public (set-rewards-to-distribute-multi ((bin-ids (list 350 int)) (amounts (list 350 uint))) (response (list 350 (response bool uint)) none))`

Set rewards to distribute for multiple bins

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-rewards-to-distribute-multi
    (bin-ids (list 350 int))
    (amounts (list 350 uint))
  )
  (ok (map set-rewards-to-distribute bin-ids amounts))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-ids | (list 350 int) |
| amounts | (list 350 uint) |

### stake-lp-tokens-multi

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L787)

`(define-public (stake-lp-tokens-multi ((bin-ids (list 350 int)) (amounts (list 350 uint))) (response (list 350 (response bool uint)) none))`

Stake LP tokens for multiple bins

<details>
  <summary>Source code:</summary>

```clarity
(define-public (stake-lp-tokens-multi
    (bin-ids (list 350 int))
    (amounts (list 350 uint))
  )
  (ok (map stake-lp-tokens bin-ids amounts))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-ids | (list 350 int) |
| amounts | (list 350 uint) |

### unstake-lp-tokens-multi

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L795)

`(define-public (unstake-lp-tokens-multi ((bin-ids (list 350 int))) (response (list 350 (response bool uint)) none))`

Unstake LP tokens for multiple bins

<details>
  <summary>Source code:</summary>

```clarity
(define-public (unstake-lp-tokens-multi
    (bin-ids (list 350 int))
  )
  (ok (map unstake-lp-tokens bin-ids))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-ids | (list 350 int) |

### early-unstake-lp-tokens-multi

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L802)

`(define-public (early-unstake-lp-tokens-multi ((bin-ids (list 350 int))) (response (list 350 (response bool uint)) none))`

Early unstake LP tokens for multiple bins

<details>
  <summary>Source code:</summary>

```clarity
(define-public (early-unstake-lp-tokens-multi
    (bin-ids (list 350 int))
  )
  (ok (map early-unstake-lp-tokens bin-ids))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-ids | (list 350 int) |

### claim-rewards-multi

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L809)

`(define-public (claim-rewards-multi ((bin-ids (list 350 int))) (response (list 350 (response uint uint)) none))`

Claim any claimable rewards for multiple bins

<details>
  <summary>Source code:</summary>

```clarity
(define-public (claim-rewards-multi
    (bin-ids (list 350 int))
  )
  (ok (map claim-rewards bin-ids))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-ids | (list 350 int) |

### update-reward-index-multi

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L816)

`(define-public (update-reward-index-multi ((bin-ids (list 350 uint))) (response (list 350 (response bool uint)) none))`

Update reward index for multiple bins

<details>
  <summary>Source code:</summary>

```clarity
(define-public (update-reward-index-multi
    (bin-ids (list 350 uint))
  )
  (ok (map update-reward-index bin-ids))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-ids | (list 350 uint) |

### admin-not-removable

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L823)

`(define-private (admin-not-removable ((admin principal)) bool)`

Helper function for removing an admin

<details>
  <summary>Source code:</summary>

```clarity
(define-private (admin-not-removable (admin principal))
  (not (is-eq admin (var-get admin-helper)))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| admin | principal |

### filter-values-eq-helper-value

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L828)

`(define-private (filter-values-eq-helper-value ((value uint)) bool)`

Filter function for removing a bin-id from the bins-staked list

<details>
  <summary>Source code:</summary>

```clarity
(define-private (filter-values-eq-helper-value (value uint))
  (not (is-eq value (var-get helper-value)))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| value | uint |

### get-reward-token-balance

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L833)

`(define-private (get-reward-token-balance () (response uint uint))`

Get reward token balance for contract

<details>
  <summary>Source code:</summary>

```clarity
(define-private (get-reward-token-balance)
  (ok (unwrap! (contract-call? .token-stx-v-1-1 get-balance
               current-contract) ERR_CANNOT_GET_TOKEN_BALANCE))
)
```
</details>




### transfer-lp-token

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L839)

`(define-private (transfer-lp-token ((bin-id uint) (amount uint) (sender principal) (recipient principal)) (response bool uint))`

Transfer LP token

<details>
  <summary>Source code:</summary>

```clarity
(define-private (transfer-lp-token (bin-id uint) (amount uint) (sender principal) (recipient principal))
  (ok (unwrap! (contract-call? .dlmm-pool-sbtc-usdc-v-1-1 transfer
               bin-id amount sender recipient) ERR_TOKEN_TRANSFER_FAILED))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-id | uint |
| amount | uint |
| sender | principal |
| recipient | principal |

### transfer-reward-token

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L845)

`(define-private (transfer-reward-token ((amount uint) (sender principal) (recipient principal)) (response bool uint))`

Transfer reward token

<details>
  <summary>Source code:</summary>

```clarity
(define-private (transfer-reward-token (amount uint) (sender principal) (recipient principal))
  (ok (unwrap! (contract-call? .token-stx-v-1-1 transfer
               amount sender recipient none) ERR_TOKEN_TRANSFER_FAILED))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| amount | uint |
| sender | principal |
| recipient | principal |

## Maps

### bin-data

Define bin-data map

```clarity
(define-map bin-data uint {
  lp-staked: uint,
  reward-per-block: uint,
  reward-period-duration: uint,
  reward-index: uint,
  last-reward-index-update: uint,
  reward-period-end-block: uint
})
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L73)

### user-data

Define user-data map

```clarity
(define-map user-data principal {
  bins-staked: (list 1001 uint),
  lp-staked: uint
})
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L83)

### user-data-at-bin

Define user-data-at-bin map

```clarity
(define-map user-data-at-bin {user: principal, bin-id: uint} {
  lp-staked: uint,
  accrued-rewards: uint,
  reward-index: uint,
  last-stake-height: uint
})
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L89)

## Variables

### admins

(list 5 principal)

Admins list and helper var used to remove admins

```clarity
(define-data-var admins (list 5 principal) (list tx-sender))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L46)

### admin-helper

principal



```clarity
(define-data-var admin-helper principal tx-sender)
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L47)

### helper-value

uint

Helper value used for removing a bin-id from the bins-staked list

```clarity
(define-data-var helper-value uint u0)
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L50)

### staking-status

bool

Staking and early unstake statuses

```clarity
(define-data-var staking-status bool true)
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L53)

### early-unstake-status

bool



```clarity
(define-data-var early-unstake-status bool true)
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L54)

### early-unstake-fee-address

principal

Fee address and fee for early unstake

```clarity
(define-data-var early-unstake-fee-address principal tx-sender)
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L57)

### early-unstake-fee

uint



```clarity
(define-data-var early-unstake-fee uint u50)
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L58)

### minimum-staking-duration

uint

Minimum staking duration in blocks

```clarity
(define-data-var minimum-staking-duration uint u1)
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L61)

### default-reward-period-duration

uint

Default reward period duration in blocks

```clarity
(define-data-var default-reward-period-duration uint u10000)
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L64)

### total-lp-staked

uint

Total amount of LP tokens staked

```clarity
(define-data-var total-lp-staked uint u0)
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L67)

### total-rewards-claimed

uint

Total rewards claimed across all bins

```clarity
(define-data-var total-rewards-claimed uint u0)
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L70)

## Constants

### ERR_NOT_AUTHORIZED



Error constants

```clarity
(define-constant ERR_NOT_AUTHORIZED (err u4001))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L7)

### ERR_INVALID_AMOUNT





```clarity
(define-constant ERR_INVALID_AMOUNT (err u4002))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L8)

### ERR_INVALID_PRINCIPAL





```clarity
(define-constant ERR_INVALID_PRINCIPAL (err u4003))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L9)

### ERR_ALREADY_ADMIN





```clarity
(define-constant ERR_ALREADY_ADMIN (err u4004))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L10)

### ERR_ADMIN_LIMIT_REACHED





```clarity
(define-constant ERR_ADMIN_LIMIT_REACHED (err u4005))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L11)

### ERR_ADMIN_NOT_IN_LIST





```clarity
(define-constant ERR_ADMIN_NOT_IN_LIST (err u4006))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L12)

### ERR_CANNOT_REMOVE_CONTRACT_DEPLOYER





```clarity
(define-constant ERR_CANNOT_REMOVE_CONTRACT_DEPLOYER (err u4007))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L13)

### ERR_STAKING_DISABLED





```clarity
(define-constant ERR_STAKING_DISABLED (err u4008))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L14)

### ERR_EARLY_UNSTAKE_DISABLED





```clarity
(define-constant ERR_EARLY_UNSTAKE_DISABLED (err u4009))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L15)

### ERR_TOKEN_TRANSFER_FAILED





```clarity
(define-constant ERR_TOKEN_TRANSFER_FAILED (err u4010))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L16)

### ERR_CANNOT_GET_TOKEN_BALANCE





```clarity
(define-constant ERR_CANNOT_GET_TOKEN_BALANCE (err u4011))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L17)

### ERR_INSUFFICIENT_TOKEN_BALANCE





```clarity
(define-constant ERR_INSUFFICIENT_TOKEN_BALANCE (err u4012))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L18)

### ERR_INVALID_MIN_STAKING_DURATION





```clarity
(define-constant ERR_INVALID_MIN_STAKING_DURATION (err u4013))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L19)

### ERR_MINIMUM_STAKING_DURATION_HAS_NOT_PASSED





```clarity
(define-constant ERR_MINIMUM_STAKING_DURATION_HAS_NOT_PASSED (err u4014))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L20)

### ERR_MINIMUM_STAKING_DURATION_PASSED





```clarity
(define-constant ERR_MINIMUM_STAKING_DURATION_PASSED (err u4015))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L21)

### ERR_INVALID_REWARD_PERIOD_DURATION





```clarity
(define-constant ERR_INVALID_REWARD_PERIOD_DURATION (err u4016))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L22)

### ERR_REWARD_PERIOD_HAS_NOT_PASSED





```clarity
(define-constant ERR_REWARD_PERIOD_HAS_NOT_PASSED (err u4017))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L23)

### ERR_BINS_STAKED_OVERFLOW





```clarity
(define-constant ERR_BINS_STAKED_OVERFLOW (err u4018))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L24)

### ERR_INVALID_BIN_ID





```clarity
(define-constant ERR_INVALID_BIN_ID (err u4019))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L25)

### ERR_NO_BIN_DATA





```clarity
(define-constant ERR_NO_BIN_DATA (err u4020))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L26)

### ERR_NO_USER_DATA





```clarity
(define-constant ERR_NO_USER_DATA (err u4021))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L27)

### ERR_NO_USER_DATA_AT_BIN





```clarity
(define-constant ERR_NO_USER_DATA_AT_BIN (err u4022))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L28)

### ERR_NO_LP_TO_UNSTAKE





```clarity
(define-constant ERR_NO_LP_TO_UNSTAKE (err u4023))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L29)

### ERR_NO_EARLY_LP_TO_UNSTAKE





```clarity
(define-constant ERR_NO_EARLY_LP_TO_UNSTAKE (err u4024))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L30)

### ERR_NO_CLAIMABLE_REWARDS





```clarity
(define-constant ERR_NO_CLAIMABLE_REWARDS (err u4025))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L31)

### ERR_INVALID_FEE





```clarity
(define-constant ERR_INVALID_FEE (err u4026))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L32)

### CONTRACT_DEPLOYER



Contract deployer address

```clarity
(define-constant CONTRACT_DEPLOYER tx-sender)
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L35)

### NUM_OF_BINS



Number of bins per pool and center bin ID as unsigned ints

```clarity
(define-constant NUM_OF_BINS u1001)
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L38)

### CENTER_BIN_ID





```clarity
(define-constant CENTER_BIN_ID (/ NUM_OF_BINS u2))
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L39)

### FEE_SCALE_BPS



Maximum BPS

```clarity
(define-constant FEE_SCALE_BPS u10000)
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L42)

### REWARD_SCALE_BPS





```clarity
(define-constant REWARD_SCALE_BPS u1000000)
```

[View in file](../clarity/contracts/dlmm-staking-sbtc-usdc-v-1-1.clar#L43)
  