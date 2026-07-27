
# dlmm-core-v-1-1

[`dlmm-core-v-1-1.clar`](../clarity/contracts/dlmm-core-v-1-1.clar)

dlmm-core-v-1-1

**Public functions:**

- [`set-core-migration-address`](#set-core-migration-address)
- [`set-core-migration-cooldown`](#set-core-migration-cooldown)
- [`migrate-core-address`](#migrate-core-address)
- [`add-bin-step`](#add-bin-step)
- [`set-minimum-shares`](#set-minimum-shares)
- [`set-public-pool-creation`](#set-public-pool-creation)
- [`add-verified-pool-code-hash`](#add-verified-pool-code-hash)
- [`remove-verified-pool-code-hash`](#remove-verified-pool-code-hash)
- [`set-swap-fee-exemption`](#set-swap-fee-exemption)
- [`claim-protocol-fees`](#claim-protocol-fees)
- [`set-pool-uri`](#set-pool-uri)
- [`set-pool-status`](#set-pool-status)
- [`set-variable-fees-manager`](#set-variable-fees-manager)
- [`set-fee-address`](#set-fee-address)
- [`set-variable-fees`](#set-variable-fees)
- [`set-x-fees`](#set-x-fees)
- [`set-y-fees`](#set-y-fees)
- [`set-variable-fees-cooldown`](#set-variable-fees-cooldown)
- [`set-freeze-variable-fees-manager`](#set-freeze-variable-fees-manager)
- [`set-dynamic-config`](#set-dynamic-config)
- [`reset-variable-fees`](#reset-variable-fees)
- [`create-pool`](#create-pool)
- [`swap-x-for-y`](#swap-x-for-y)
- [`swap-y-for-x`](#swap-y-for-x)
- [`add-liquidity`](#add-liquidity)
- [`withdraw-liquidity`](#withdraw-liquidity)
- [`move-liquidity`](#move-liquidity)
- [`add-admin`](#add-admin)
- [`remove-admin`](#remove-admin)

**Read-only functions:**

- [`get-core-migration-address`](#get-core-migration-address)
- [`get-core-migration-execution-time`](#get-core-migration-execution-time)
- [`get-core-migration-cooldown`](#get-core-migration-cooldown)
- [`get-admins`](#get-admins)
- [`get-admin-helper`](#get-admin-helper)
- [`get-last-pool-id`](#get-last-pool-id)
- [`get-pool-by-id`](#get-pool-by-id)
- [`get-allowed-token-direction`](#get-allowed-token-direction)
- [`get-unclaimed-protocol-fees-by-id`](#get-unclaimed-protocol-fees-by-id)
- [`get-swap-fee-exemption-by-id`](#get-swap-fee-exemption-by-id)
- [`get-bin-steps`](#get-bin-steps)
- [`get-bin-factors-by-step`](#get-bin-factors-by-step)
- [`get-minimum-bin-shares`](#get-minimum-bin-shares)
- [`get-minimum-burnt-shares`](#get-minimum-burnt-shares)
- [`get-public-pool-creation`](#get-public-pool-creation)
- [`get-verified-pool-code-hashes`](#get-verified-pool-code-hashes)
- [`get-verified-pool-code-hashes-helper`](#get-verified-pool-code-hashes-helper)
- [`get-unsigned-bin-id`](#get-unsigned-bin-id)
- [`get-signed-bin-id`](#get-signed-bin-id)
- [`get-bin-price`](#get-bin-price)
- [`get-liquidity-value`](#get-liquidity-value)
- [`get-is-pool-verified`](#get-is-pool-verified)

**Private functions:**

- [`admin-not-removable`](#admin-not-removable)
- [`verified-pool-code-hashes-not-removable`](#verified-pool-code-hashes-not-removable)
- [`fold-are-bin-factors-ascending`](#fold-are-bin-factors-ascending)
- [`create-symbol`](#create-symbol)
- [`is-valid-pool`](#is-valid-pool)
- [`is-enabled-pool`](#is-enabled-pool)

**Maps**

- [`bin-factors`](#bin-factors)
- [`pools`](#pools)
- [`allowed-token-direction`](#allowed-token-direction)
- [`unclaimed-protocol-fees`](#unclaimed-protocol-fees)
- [`swap-fee-exemptions`](#swap-fee-exemptions)

**Variables**

- [`core-migration-address`](#core-migration-address)
- [`core-migration-execution-time`](#core-migration-execution-time)
- [`core-migration-cooldown`](#core-migration-cooldown)
- [`admins`](#admins)
- [`admin-helper`](#admin-helper)
- [`last-pool-id`](#last-pool-id)
- [`bin-steps`](#bin-steps)
- [`minimum-bin-shares`](#minimum-bin-shares)
- [`minimum-burnt-shares`](#minimum-burnt-shares)
- [`public-pool-creation`](#public-pool-creation)
- [`verified-pool-code-hashes`](#verified-pool-code-hashes)
- [`verified-pool-code-hashes-helper`](#verified-pool-code-hashes-helper)

**Constants**

- [`ERR_NOT_AUTHORIZED`](#err_not_authorized)
- [`ERR_INVALID_AMOUNT`](#err_invalid_amount)
- [`ERR_INVALID_PRINCIPAL`](#err_invalid_principal)
- [`ERR_ALREADY_ADMIN`](#err_already_admin)
- [`ERR_ADMIN_LIMIT_REACHED`](#err_admin_limit_reached)
- [`ERR_ADMIN_NOT_IN_LIST`](#err_admin_not_in_list)
- [`ERR_CANNOT_REMOVE_CONTRACT_DEPLOYER`](#err_cannot_remove_contract_deployer)
- [`ERR_NO_POOL_DATA`](#err_no_pool_data)
- [`ERR_POOL_NOT_CREATED`](#err_pool_not_created)
- [`ERR_POOL_DISABLED`](#err_pool_disabled)
- [`ERR_POOL_ALREADY_CREATED`](#err_pool_already_created)
- [`ERR_INVALID_POOL`](#err_invalid_pool)
- [`ERR_INVALID_POOL_URI`](#err_invalid_pool_uri)
- [`ERR_INVALID_POOL_SYMBOL`](#err_invalid_pool_symbol)
- [`ERR_INVALID_POOL_NAME`](#err_invalid_pool_name)
- [`ERR_INVALID_TOKEN_DIRECTION`](#err_invalid_token_direction)
- [`ERR_MATCHING_TOKEN_CONTRACTS`](#err_matching_token_contracts)
- [`ERR_INVALID_X_TOKEN`](#err_invalid_x_token)
- [`ERR_INVALID_Y_TOKEN`](#err_invalid_y_token)
- [`ERR_INVALID_X_AMOUNT`](#err_invalid_x_amount)
- [`ERR_INVALID_Y_AMOUNT`](#err_invalid_y_amount)
- [`ERR_MINIMUM_X_AMOUNT`](#err_minimum_x_amount)
- [`ERR_MINIMUM_Y_AMOUNT`](#err_minimum_y_amount)
- [`ERR_MINIMUM_LP_AMOUNT`](#err_minimum_lp_amount)
- [`ERR_MAXIMUM_X_AMOUNT`](#err_maximum_x_amount)
- [`ERR_MAXIMUM_Y_AMOUNT`](#err_maximum_y_amount)
- [`ERR_INVALID_MIN_DLP_AMOUNT`](#err_invalid_min_dlp_amount)
- [`ERR_INVALID_LIQUIDITY_VALUE`](#err_invalid_liquidity_value)
- [`ERR_INVALID_FEE`](#err_invalid_fee)
- [`ERR_MAXIMUM_X_LIQUIDITY_FEE`](#err_maximum_x_liquidity_fee)
- [`ERR_MAXIMUM_Y_LIQUIDITY_FEE`](#err_maximum_y_liquidity_fee)
- [`ERR_NO_UNCLAIMED_PROTOCOL_FEES_DATA`](#err_no_unclaimed_protocol_fees_data)
- [`ERR_MINIMUM_BURN_AMOUNT`](#err_minimum_burn_amount)
- [`ERR_INVALID_MIN_BURNT_SHARES`](#err_invalid_min_burnt_shares)
- [`ERR_INVALID_BIN_STEP`](#err_invalid_bin_step)
- [`ERR_ALREADY_BIN_STEP`](#err_already_bin_step)
- [`ERR_BIN_STEP_LIMIT_REACHED`](#err_bin_step_limit_reached)
- [`ERR_NO_BIN_FACTORS`](#err_no_bin_factors)
- [`ERR_INVALID_BIN_FACTOR`](#err_invalid_bin_factor)
- [`ERR_INVALID_FIRST_BIN_FACTOR`](#err_invalid_first_bin_factor)
- [`ERR_INVALID_CENTER_BIN_FACTOR`](#err_invalid_center_bin_factor)
- [`ERR_UNSORTED_BIN_FACTORS_LIST`](#err_unsorted_bin_factors_list)
- [`ERR_INVALID_BIN_FACTORS_LENGTH`](#err_invalid_bin_factors_length)
- [`ERR_INVALID_INITIAL_PRICE`](#err_invalid_initial_price)
- [`ERR_INVALID_BIN_PRICE`](#err_invalid_bin_price)
- [`ERR_MATCHING_BIN_ID`](#err_matching_bin_id)
- [`ERR_NOT_ACTIVE_BIN`](#err_not_active_bin)
- [`ERR_NO_BIN_SHARES`](#err_no_bin_shares)
- [`ERR_INVALID_POOL_CODE_HASH`](#err_invalid_pool_code_hash)
- [`ERR_INVALID_VERIFIED_POOL_CODE_HASH`](#err_invalid_verified_pool_code_hash)
- [`ERR_ALREADY_VERIFIED_POOL_CODE_HASH`](#err_already_verified_pool_code_hash)
- [`ERR_VERIFIED_POOL_CODE_HASH_LIMIT_REACHED`](#err_verified_pool_code_hash_limit_reached)
- [`ERR_VERIFIED_POOL_CODE_HASH_NOT_IN_LIST`](#err_verified_pool_code_hash_not_in_list)
- [`ERR_VARIABLE_FEES_COOLDOWN`](#err_variable_fees_cooldown)
- [`ERR_VARIABLE_FEES_MANAGER_FROZEN`](#err_variable_fees_manager_frozen)
- [`ERR_INVALID_DYNAMIC_CONFIG`](#err_invalid_dynamic_config)
- [`ERR_INVALID_CORE_MIGRATION_COOLDOWN`](#err_invalid_core_migration_cooldown)
- [`ERR_CORE_MIGRATION_COOLDOWN`](#err_core_migration_cooldown)
- [`ERR_CORE_ADDRESS_ALREADY_MIGRATED`](#err_core_address_already_migrated)
- [`CONTRACT_DEPLOYER`](#contract_deployer)
- [`BURN_ADDRESS`](#burn_address)
- [`NUM_OF_BINS`](#num_of_bins)
- [`CENTER_BIN_ID`](#center_bin_id)
- [`MIN_BIN_ID`](#min_bin_id)
- [`MAX_BIN_ID`](#max_bin_id)
- [`FEE_SCALE_BPS`](#fee_scale_bps)
- [`PRICE_SCALE_BPS`](#price_scale_bps)
- [`MIN_CORE_MIGRATION_COOLDOWN`](#min_core_migration_cooldown)


## Functions

### get-core-migration-address

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L139)

`(define-read-only (get-core-migration-address () (response principal none))`

Get core migration address

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-core-migration-address)
  (ok (var-get core-migration-address))
)
```
</details>




### get-core-migration-execution-time

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L144)

`(define-read-only (get-core-migration-execution-time () (response uint none))`

Get timestamp of core migration execution time

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-core-migration-execution-time)
  (ok (var-get core-migration-execution-time))
)
```
</details>




### get-core-migration-cooldown

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L149)

`(define-read-only (get-core-migration-cooldown () (response uint none))`

Get core migration cooldown in seconds

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-core-migration-cooldown)
  (ok (var-get core-migration-cooldown))
)
```
</details>




### get-admins

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L154)

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

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L159)

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




### get-last-pool-id

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L164)

`(define-read-only (get-last-pool-id () (response uint none))`

Get ID of last created pool

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-last-pool-id)
  (ok (var-get last-pool-id))
)
```
</details>




### get-pool-by-id

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L169)

`(define-read-only (get-pool-by-id ((id uint)) (response (optional (tuple (id uint) (name (string-ascii 32)) (pool-contract principal) (status bool) (symbol (string-ascii 32)))) none))`

Get a pool by pool ID

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-pool-by-id (id uint))
  (ok (map-get? pools id))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| id | uint |

### get-allowed-token-direction

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L174)

`(define-read-only (get-allowed-token-direction ((x-token principal) (y-token principal)) (response (optional bool) none))`

Get allowed-token-direction for pool creation

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-allowed-token-direction (x-token principal) (y-token principal))
  (ok (map-get? allowed-token-direction {x-token: x-token, y-token: y-token}))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| x-token | principal |
| y-token | principal |

### get-unclaimed-protocol-fees-by-id

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L179)

`(define-read-only (get-unclaimed-protocol-fees-by-id ((id uint)) (response (optional (tuple (x-fee uint) (y-fee uint))) none))`

Get unclaimed-protocol-fees for a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-unclaimed-protocol-fees-by-id (id uint))
  (ok (map-get? unclaimed-protocol-fees id))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| id | uint |

### get-swap-fee-exemption-by-id

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L184)

`(define-read-only (get-swap-fee-exemption-by-id ((address principal) (id uint)) (response bool none))`

Get swap-fee-exemptions for an address for a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-swap-fee-exemption-by-id (address principal) (id uint))
  (ok (default-to false (map-get? swap-fee-exemptions {address: address, id: id})))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| address | principal |
| id | uint |

### get-bin-steps

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L189)

`(define-read-only (get-bin-steps () (response (list 1000 uint) none))`

Get allowed bin steps

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-bin-steps)
  (ok (var-get bin-steps))
)
```
</details>




### get-bin-factors-by-step

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L194)

`(define-read-only (get-bin-factors-by-step ((step uint)) (response (optional (list 1001 uint)) none))`

Get bin factors by bin step

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-bin-factors-by-step (step uint))
  (ok (map-get? bin-factors step))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| step | uint |

### get-minimum-bin-shares

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L199)

`(define-read-only (get-minimum-bin-shares () (response uint none))`

Get min shares required to mint for the active bin when creating a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-minimum-bin-shares)
  (ok (var-get minimum-bin-shares))
)
```
</details>




### get-minimum-burnt-shares

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L204)

`(define-read-only (get-minimum-burnt-shares () (response uint none))`

Get min shares required to burn for the active bin when creating a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-minimum-burnt-shares)
  (ok (var-get minimum-burnt-shares))
)
```
</details>




### get-public-pool-creation

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L209)

`(define-read-only (get-public-pool-creation () (response bool none))`

Get public pool creation status

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-public-pool-creation)
  (ok (var-get public-pool-creation))
)
```
</details>




### get-verified-pool-code-hashes

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L214)

`(define-read-only (get-verified-pool-code-hashes () (response (list 10000 (buff 32)) none))`

Get verified pool code hashes list

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-verified-pool-code-hashes)
  (ok (var-get verified-pool-code-hashes))
)
```
</details>




### get-verified-pool-code-hashes-helper

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L219)

`(define-read-only (get-verified-pool-code-hashes-helper () (response (buff 32) none))`

Get verified pool code hashes helper var

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-verified-pool-code-hashes-helper)
  (ok (var-get verified-pool-code-hashes-helper))
)
```
</details>




### get-unsigned-bin-id

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L224)

`(define-read-only (get-unsigned-bin-id ((bin-id int)) (response uint none))`

Get bin ID as unsigned int

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-unsigned-bin-id (bin-id int))
  (ok (to-uint (+ bin-id (to-int CENTER_BIN_ID))))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-id | int |

### get-signed-bin-id

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L229)

`(define-read-only (get-signed-bin-id ((bin-id uint)) (response int none))`

Get bin ID as signed int

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-signed-bin-id (bin-id uint))
  (ok (- (to-int bin-id) (to-int CENTER_BIN_ID)))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-id | uint |

### get-bin-price

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L234)

`(define-read-only (get-bin-price ((initial-price uint) (bin-step uint) (bin-id int)) (response uint uint))`

Get price for a specific bin

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-bin-price (initial-price uint) (bin-step uint) (bin-id int))
  (let (
    (unsigned-bin-id (to-uint (+ bin-id (to-int CENTER_BIN_ID))))
    (bin-factors-list (unwrap! (map-get? bin-factors bin-step) ERR_NO_BIN_FACTORS))
    (bin-factor (unwrap! (element-at? bin-factors-list unsigned-bin-id) ERR_INVALID_BIN_FACTOR))
    (bin-price (/ (* initial-price bin-factor) PRICE_SCALE_BPS))
  )
    (asserts! (> bin-price u0) ERR_INVALID_BIN_PRICE)
    (ok bin-price)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| initial-price | uint |
| bin-step | uint |
| bin-id | int |

### get-liquidity-value

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L247)

`(define-read-only (get-liquidity-value ((x-amount uint) (y-amount uint) (bin-price uint)) (response uint none))`

Get liquidity value when adding liquidity to a bin by rebasing x-amount to y-units

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-liquidity-value (x-amount uint) (y-amount uint) (bin-price uint))
  (ok (+ (* bin-price x-amount) y-amount))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| x-amount | uint |
| y-amount | uint |
| bin-price | uint |

### get-is-pool-verified

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L252)

`(define-read-only (get-is-pool-verified ((pool-trait trait_reference)) (response bool uint))`

Get pool verification status

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-is-pool-verified (pool-trait <dlmm-pool-trait>))
  (let (
    (pool-code-hash (unwrap! (contract-hash? (contract-of pool-trait)) ERR_INVALID_POOL_CODE_HASH))
  )
    (ok (is-some (index-of (var-get verified-pool-code-hashes) pool-code-hash)))
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-trait | trait_reference |

### set-core-migration-address

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L261)

`(define-public (set-core-migration-address ((address principal)) (response bool uint))`

Set core migration address

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-core-migration-address (address principal))
  (let (
    (migration-execution-time (+ stacks-block-time (var-get core-migration-cooldown)))
    (caller tx-sender)
  )
    (begin
      ;; Assert caller is an admin
      (asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)

      ;; Assert address is standard principal
      (asserts! (is-standard address) ERR_INVALID_PRINCIPAL)

      ;; Transfer 1 uSTX from caller to BURN_ADDRESS
      (try! (stx-transfer? u1 caller BURN_ADDRESS))

      ;; Set core-migration-address and core-migration-execution-time
      (var-set core-migration-address address)
      (var-set core-migration-execution-time migration-execution-time)

      ;; Print function data and return true
      (print {
        action: "set-core-migration-address",
        caller: caller,
        data: {
          address: address,
          migration-execution-time: migration-execution-time,
          current-block-time: stacks-block-time
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
| address | principal |

### set-core-migration-cooldown

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L296)

`(define-public (set-core-migration-cooldown ((cooldown uint)) (response bool uint))`

Set core migration cooldown in seconds

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-core-migration-cooldown (cooldown uint))
  (let (
    (caller tx-sender)
  )
    (begin
      ;; Assert caller is an admin
      (asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)

      ;; Assert cooldown is greater than or equal to MIN_CORE_MIGRATION_COOLDOWN
      (asserts! (>= cooldown MIN_CORE_MIGRATION_COOLDOWN) ERR_INVALID_CORE_MIGRATION_COOLDOWN)

      ;; Transfer 1 uSTX from caller to BURN_ADDRESS
      (try! (stx-transfer? u1 caller BURN_ADDRESS))

      ;; Set core-migration-cooldown to cooldown
      (var-set core-migration-cooldown cooldown)

      ;; Print function data and return true
      (print {action: "set-core-migration-cooldown", caller: caller, data: {cooldown: cooldown}})
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| cooldown | uint |

### migrate-core-address

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L321)

`(define-public (migrate-core-address ((pool-trait trait_reference)) (response bool uint))`

Migrate core address for a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-public (migrate-core-address (pool-trait <dlmm-pool-trait>))
  (let (
    ;; Get pool data
    (pool-data (unwrap! (contract-call? pool-trait get-pool) ERR_NO_POOL_DATA))
    (current-core-migration-address (var-get core-migration-address))
    (current-core-migration-execution-time (var-get core-migration-execution-time))
    (caller tx-sender)
  )
    (begin
      ;; Assert caller is an admin and pool is created and valid
      (asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)
      (asserts! (is-valid-pool (get pool-id pool-data) (contract-of pool-trait)) ERR_INVALID_POOL)
      (asserts! (get pool-created pool-data) ERR_POOL_NOT_CREATED)

      ;; Assert core migration cooldown has passed
      (asserts! (>= stacks-block-time current-core-migration-execution-time) ERR_CORE_MIGRATION_COOLDOWN)

      ;; Assert current-core-migration-address is not equal to the pool's current core address
      (asserts! (not (is-eq current-core-migration-address (get core-address pool-data))) ERR_CORE_ADDRESS_ALREADY_MIGRATED)

      ;; Transfer 1 uSTX from caller to BURN_ADDRESS
      (try! (stx-transfer? u1 caller BURN_ADDRESS))

      ;; Set core address for pool
      (try! (contract-call? pool-trait set-core-address current-core-migration-address))

      ;; Print function data and return true
      (print {
        action: "migrate-core-address",
        caller: caller,
        data: {
          pool-id: (get pool-id pool-data),
          pool-name: (get pool-name pool-data),
          pool-contract: (contract-of pool-trait),
          current-core-migration-address: current-core-migration-address,
          current-core-migration-execution-time: current-core-migration-execution-time,
          current-block-time: stacks-block-time
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
| pool-trait | trait_reference |

### add-bin-step

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L366)

`(define-public (add-bin-step ((step uint) (factors (list 1001 uint))) (response bool uint))`

Add a new bin step and its factors

<details>
  <summary>Source code:</summary>

```clarity
(define-public (add-bin-step (step uint) (factors (list 1001 uint)))
  (let (
    (bin-steps-list (var-get bin-steps))
    (caller tx-sender)
  )
    ;; Assert caller is an admin and step is greater than 0
    (asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)
    (asserts! (> step u0) ERR_INVALID_AMOUNT)

    ;; Assert step is not in bin-steps-list
    (asserts! (is-none (index-of bin-steps-list step)) ERR_ALREADY_BIN_STEP)

    ;; Assert factors list length is 1001
    (asserts! (is-eq (len factors) u1001) ERR_INVALID_BIN_FACTORS_LENGTH)

    ;; Assert first factor is greater than 0
    (asserts! (> (unwrap! (element-at? factors u0) ERR_INVALID_BIN_FACTORS_LENGTH) u0) ERR_INVALID_FIRST_BIN_FACTOR)

    ;; Assert center factor is equal to PRICE_SCALE_BPS
    (asserts! (is-eq (unwrap! (element-at? factors CENTER_BIN_ID) ERR_INVALID_BIN_FACTORS_LENGTH) PRICE_SCALE_BPS) ERR_INVALID_CENTER_BIN_FACTOR)

    ;; Assert factors list is in ascending order
    (try! (fold fold-are-bin-factors-ascending factors (ok u0)))

    ;; Transfer 1 uSTX from caller to BURN_ADDRESS
    (try! (stx-transfer? u1 caller BURN_ADDRESS))

    ;; Add bin step to list with max length of 1000
    (var-set bin-steps (unwrap! (as-max-len? (append bin-steps-list step) u1000) ERR_BIN_STEP_LIMIT_REACHED))

    ;; Add bin factors to bin-factors mapping
    (map-set bin-factors step factors)

    ;; Print function data and return true
    (print {action: "add-bin-step", caller: caller, data: {step: step, factors: factors}})
    (ok true)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| step | uint |
| factors | (list 1001 uint) |

### set-minimum-shares

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L406)

`(define-public (set-minimum-shares ((min-bin uint) (min-burnt uint)) (response bool uint))`

Set min shares required to mint and burn for the active bin when creating a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-minimum-shares (min-bin uint) (min-burnt uint))
  (let (
    (caller tx-sender)
  )
    (begin
      ;; Assert caller is an admin and amounts are greater than 0
      (asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)
      (asserts! (and (> min-bin u0) (> min-burnt u0)) ERR_INVALID_AMOUNT)

      ;; Assert min-bin is greater than min-burnt
      (asserts! (> min-bin min-burnt) ERR_INVALID_MIN_BURNT_SHARES)

      ;; Transfer 1 uSTX from caller to BURN_ADDRESS
      (try! (stx-transfer? u1 caller BURN_ADDRESS))

      ;; Set minimum-bin-shares and minimum-burnt-shares
      (var-set minimum-bin-shares min-bin)
      (var-set minimum-burnt-shares min-burnt)

      ;; Print function data and return true
      (print {
        action: "set-minimum-shares",
        caller: caller,
        data: {
          min-bin: min-bin,
          min-burnt: min-burnt
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
| min-bin | uint |
| min-burnt | uint |

### set-public-pool-creation

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L440)

`(define-public (set-public-pool-creation ((status bool)) (response bool uint))`

Enable or disable public pool creation

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-public-pool-creation (status bool))
  (let (
    (caller tx-sender)
  )
    (begin
      ;; Assert caller is an admin
      (asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)

      ;; Transfer 1 uSTX from caller to BURN_ADDRESS
      (try! (stx-transfer? u1 caller BURN_ADDRESS))

      ;; Set public-pool-creation to status
      (var-set public-pool-creation status)

      ;; Print function data and return true
      (print {action: "set-public-pool-creation", caller: caller, data: {status: status}})
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

### add-verified-pool-code-hash

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L462)

`(define-public (add-verified-pool-code-hash ((hash (buff 32))) (response bool uint))`

Add a new verified pool code hash

<details>
  <summary>Source code:</summary>

```clarity
(define-public (add-verified-pool-code-hash (hash (buff 32)))
  (let (
    (verified-pool-code-hashes-list (var-get verified-pool-code-hashes))
    (caller tx-sender)
  )
    ;; Assert caller is an admin and new code hash is not already in the list
    (asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)
    (asserts! (is-none (index-of verified-pool-code-hashes-list hash)) ERR_ALREADY_VERIFIED_POOL_CODE_HASH)

    ;; Assert hash length is 32
    (asserts! (is-eq (len hash) u32) ERR_INVALID_VERIFIED_POOL_CODE_HASH)

    ;; Transfer 1 uSTX from caller to BURN_ADDRESS
    (try! (stx-transfer? u1 caller BURN_ADDRESS))

    ;; Add code hash to verified pool code hashes list with max length of 10000
    (var-set verified-pool-code-hashes (unwrap! (as-max-len? (append verified-pool-code-hashes-list hash) u10000) ERR_VERIFIED_POOL_CODE_HASH_LIMIT_REACHED))

    ;; Print function data and return true
    (print {action: "add-verified-pool-code-hash", caller: caller, data: {hash: hash}})
    (ok true)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| hash | (buff 32) |

### remove-verified-pool-code-hash

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L487)

`(define-public (remove-verified-pool-code-hash ((hash (buff 32))) (response bool uint))`

Remove a verified pool code hash

<details>
  <summary>Source code:</summary>

```clarity
(define-public (remove-verified-pool-code-hash (hash (buff 32)))
  (let (
    (verified-pool-code-hashes-list (var-get verified-pool-code-hashes))
    (caller tx-sender)
  )
    ;; Assert caller is an admin and code hash to remove is in the list
    (asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)
    (asserts! (is-some (index-of verified-pool-code-hashes-list hash)) ERR_VERIFIED_POOL_CODE_HASH_NOT_IN_LIST)

    ;; Transfer 1 uSTX from caller to BURN_ADDRESS
    (try! (stx-transfer? u1 caller BURN_ADDRESS))

    ;; Set verified-pool-code-hashes-helper to hash to remove and filter verified-pool-code-hashes to remove hash
    (var-set verified-pool-code-hashes-helper hash)
    (var-set verified-pool-code-hashes (filter verified-pool-code-hashes-not-removable verified-pool-code-hashes-list))

    ;; Print function data and return true
    (print {action: "remove-verified-pool-code-hash", caller: caller, data: {hash: hash}})
    (ok true)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| hash | (buff 32) |

### set-swap-fee-exemption

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L510)

`(define-public (set-swap-fee-exemption ((pool-trait trait_reference) (address principal) (exempt bool)) (response bool uint))`

Set swap fee exemption for an address for a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-swap-fee-exemption (pool-trait <dlmm-pool-trait>) (address principal) (exempt bool))
  (let (
    ;; Get pool data
    (pool-data (unwrap! (contract-call? pool-trait get-pool) ERR_NO_POOL_DATA))
    (pool-id (get pool-id pool-data))
    (caller tx-sender)
  )
    (begin
      ;; Assert caller is an admin and pool is created and valid
      (asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)
      (asserts! (is-valid-pool pool-id (contract-of pool-trait)) ERR_INVALID_POOL)
      (asserts! (get pool-created pool-data) ERR_POOL_NOT_CREATED)

      ;; Assert address is standard principal
      (asserts! (is-standard address) ERR_INVALID_PRINCIPAL)

      ;; Transfer 1 uSTX from caller to BURN_ADDRESS
      (try! (stx-transfer? u1 caller BURN_ADDRESS))

      ;; Update swap-fee-exemptions mapping
      (map-set swap-fee-exemptions {address: address, id: pool-id} exempt)

      ;; Print function data and return true
      (print {
        action: "set-swap-fee-exemption",
        caller: caller,
        data: {
          pool-id: pool-id,
          pool-name: (get pool-name pool-data),
          pool-contract: (contract-of pool-trait),
          address: address,
          exempt: exempt
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
| pool-trait | trait_reference |
| address | principal |
| exempt | bool |

### claim-protocol-fees

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L550)

`(define-public (claim-protocol-fees ((pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference)) (response bool uint))`

Claim protocol fees for a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-public (claim-protocol-fees
    (pool-trait <dlmm-pool-trait>)
    (x-token-trait <sip-010-trait>) (y-token-trait <sip-010-trait>)
  )
  (let (
    ;; Get pool data
    (pool-data (unwrap! (contract-call? pool-trait get-pool) ERR_NO_POOL_DATA))
    (pool-id (get pool-id pool-data))
    (pool-contract (contract-of pool-trait))
    (fee-address (get fee-address pool-data))
    (x-token (get x-token pool-data))
    (y-token (get y-token pool-data))
    
    ;; Get current unclaimed protocol fees for pool
    (current-unclaimed-protocol-fees (unwrap! (map-get? unclaimed-protocol-fees pool-id) ERR_NO_UNCLAIMED_PROTOCOL_FEES_DATA))
    (unclaimed-x-fees (get x-fee current-unclaimed-protocol-fees))
    (unclaimed-y-fees (get y-fee current-unclaimed-protocol-fees))
    (caller tx-sender)
  )
    (begin
      ;; Assert pool is created and valid
      (asserts! (is-valid-pool pool-id (contract-of pool-trait)) ERR_INVALID_POOL)
      (asserts! (get pool-created pool-data) ERR_POOL_NOT_CREATED)

      ;; Assert correct token traits are used
      (asserts! (is-eq (contract-of x-token-trait) x-token) ERR_INVALID_X_TOKEN)
      (asserts! (is-eq (contract-of y-token-trait) y-token) ERR_INVALID_Y_TOKEN)

      ;; Transfer unclaimed-x-fees x tokens from pool-contract to fee-address
      (if (> unclaimed-x-fees u0)
        (try! (contract-call? pool-trait pool-transfer x-token-trait unclaimed-x-fees fee-address))
        false)

      ;; Transfer unclaimed-y-fees y tokens from pool-contract to fee-address
      (if (> unclaimed-y-fees u0)
        (try! (contract-call? pool-trait pool-transfer y-token-trait unclaimed-y-fees fee-address))
        false)

      ;; Update unclaimed-protocol-fees for pool
      (map-set unclaimed-protocol-fees pool-id {x-fee: u0, y-fee: u0})

      ;; Print function data and return true
      (print {
        action: "claim-protocol-fees",
        caller: caller,
        data: {
          pool-id: pool-id,
          pool-name: (get pool-name pool-data),
          pool-contract: pool-contract,
          x-token: x-token,
          y-token: y-token,
          unclaimed-x-fees: unclaimed-x-fees,
          unclaimed-y-fees: unclaimed-y-fees
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
| pool-trait | trait_reference |
| x-token-trait | trait_reference |
| y-token-trait | trait_reference |

### set-pool-uri

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L611)

`(define-public (set-pool-uri ((pool-trait trait_reference) (uri (string-ascii 256))) (response bool uint))`

Set pool uri for a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-pool-uri (pool-trait <dlmm-pool-trait>) (uri (string-ascii 256)))
  (let (
    ;; Get pool data
    (pool-data (unwrap! (contract-call? pool-trait get-pool) ERR_NO_POOL_DATA))
    (caller tx-sender)
  )
    (begin
      ;; Assert caller is an admin and pool is created and valid
      (asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)
      (asserts! (is-valid-pool (get pool-id pool-data) (contract-of pool-trait)) ERR_INVALID_POOL)
      (asserts! (get pool-created pool-data) ERR_POOL_NOT_CREATED)

      ;; Assert uri length is greater than 0
      (asserts! (> (len uri) u0) ERR_INVALID_POOL_URI)

      ;; Transfer 1 uSTX from caller to BURN_ADDRESS
      (try! (stx-transfer? u1 caller BURN_ADDRESS))

      ;; Set pool uri for pool
      (try! (contract-call? pool-trait set-pool-uri uri))

      ;; Print function data and return true
      (print {
        action: "set-pool-uri",
        caller: caller,
        data: {
          pool-id: (get pool-id pool-data),
          pool-name: (get pool-name pool-data),
          pool-contract: (contract-of pool-trait),
          uri: uri
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
| pool-trait | trait_reference |
| uri | (string-ascii 256) |

### set-pool-status

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L649)

`(define-public (set-pool-status ((pool-trait trait_reference) (status bool)) (response bool uint))`

Set pool status for a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-pool-status (pool-trait <dlmm-pool-trait>) (status bool))
  (let (
    ;; Get pool data
    (pool-data (unwrap! (contract-call? pool-trait get-pool) ERR_NO_POOL_DATA))
    (pool-map-data (unwrap! (map-get? pools (get pool-id pool-data)) ERR_NO_POOL_DATA))
    (caller tx-sender)
  )
    (begin
      ;; Assert caller is an admin and pool is created and valid
      (asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)
      (asserts! (is-valid-pool (get pool-id pool-data) (contract-of pool-trait)) ERR_INVALID_POOL)
      (asserts! (get pool-created pool-data) ERR_POOL_NOT_CREATED)

      ;; Transfer 1 uSTX from caller to BURN_ADDRESS
      (try! (stx-transfer? u1 caller BURN_ADDRESS))

      ;; Set pool status for pool
      (map-set pools (get pool-id pool-data) (merge pool-map-data {status: status}))

      ;; Print function data and return true
      (print {
        action: "set-pool-status",
        caller: caller,
        data: {
          pool-id: (get pool-id pool-data),
          pool-name: (get pool-name pool-data),
          pool-contract: (contract-of pool-trait),
          status: status
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
| pool-trait | trait_reference |
| status | bool |

### set-variable-fees-manager

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L685)

`(define-public (set-variable-fees-manager ((pool-trait trait_reference) (manager principal)) (response bool uint))`

Set variable fees manager for a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-variable-fees-manager (pool-trait <dlmm-pool-trait>) (manager principal))
  (let (
    ;; Get pool data
    (pool-data (unwrap! (contract-call? pool-trait get-pool) ERR_NO_POOL_DATA))
    (freeze-variable-fees-manager (get freeze-variable-fees-manager pool-data))
    (caller tx-sender)
  )
    (begin
      ;; Assert caller is an admin and pool is created and valid
      (asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)
      (asserts! (is-valid-pool (get pool-id pool-data) (contract-of pool-trait)) ERR_INVALID_POOL)
      (asserts! (get pool-created pool-data) ERR_POOL_NOT_CREATED)

      ;; Assert variable fees manager is not frozen
      (asserts! (not freeze-variable-fees-manager) ERR_VARIABLE_FEES_MANAGER_FROZEN)

      ;; Assert address is standard principal
      (asserts! (is-standard manager) ERR_INVALID_PRINCIPAL)

      ;; Transfer 1 uSTX from caller to BURN_ADDRESS
      (try! (stx-transfer? u1 caller BURN_ADDRESS))

      ;; Set variable fees manager for pool
      (try! (contract-call? pool-trait set-variable-fees-manager manager))

      ;; Print function data and return true
      (print {
        action: "set-variable-fees-manager",
        caller: caller,
        data: {
          pool-id: (get pool-id pool-data),
          pool-name: (get pool-name pool-data),
          pool-contract: (contract-of pool-trait),
          manager: manager
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
| pool-trait | trait_reference |
| manager | principal |

### set-fee-address

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L727)

`(define-public (set-fee-address ((pool-trait trait_reference) (address principal)) (response bool uint))`

Set fee address for a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-fee-address (pool-trait <dlmm-pool-trait>) (address principal))
  (let (
    ;; Get pool data
    (pool-data (unwrap! (contract-call? pool-trait get-pool) ERR_NO_POOL_DATA))
    (caller tx-sender)
  )
    (begin
      ;; Assert caller is an admin and pool is created and valid
      (asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)
      (asserts! (is-valid-pool (get pool-id pool-data) (contract-of pool-trait)) ERR_INVALID_POOL)
      (asserts! (get pool-created pool-data) ERR_POOL_NOT_CREATED)

      ;; Assert address is standard principal
      (asserts! (is-standard address) ERR_INVALID_PRINCIPAL)

      ;; Transfer 1 uSTX from caller to BURN_ADDRESS
      (try! (stx-transfer? u1 caller BURN_ADDRESS))

      ;; Set fee address for pool
      (try! (contract-call? pool-trait set-fee-address address))

      ;; Print function data and return true
      (print {
        action: "set-fee-address",
        caller: caller,
        data: {
          pool-id: (get pool-id pool-data),
          pool-name: (get pool-name pool-data),
          pool-contract: (contract-of pool-trait),
          address: address
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
| pool-trait | trait_reference |
| address | principal |

### set-variable-fees

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L765)

`(define-public (set-variable-fees ((pool-trait trait_reference) (x-fee uint) (y-fee uint)) (response bool uint))`

Set variable fees for a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-variable-fees (pool-trait <dlmm-pool-trait>) (x-fee uint) (y-fee uint))
  (let (
    ;; Get pool data
    (pool-data (unwrap! (contract-call? pool-trait get-pool) ERR_NO_POOL_DATA))
    (variable-fees-manager (get variable-fees-manager pool-data))
    (freeze-variable-fees-manager (get freeze-variable-fees-manager pool-data))
    (x-protocol-fee (get x-protocol-fee pool-data))
    (x-provider-fee (get x-provider-fee pool-data))
    (y-protocol-fee (get y-protocol-fee pool-data))
    (y-provider-fee (get y-provider-fee pool-data))
    (caller tx-sender)
  )
    (begin
      ;; Assert caller is an admin or variable fees manager and pool is created and valid
      (asserts! (or (is-some (index-of (var-get admins) caller)) (is-eq variable-fees-manager caller)) ERR_NOT_AUTHORIZED)
      (asserts! (is-valid-pool (get pool-id pool-data) (contract-of pool-trait)) ERR_INVALID_POOL)
      (asserts! (get pool-created pool-data) ERR_POOL_NOT_CREATED)

      ;; Assert caller is variable fees manager if variable fees manager is frozen
      (asserts! (or (is-eq variable-fees-manager caller) (not freeze-variable-fees-manager)) ERR_NOT_AUTHORIZED)

      ;; Assert x-fee + x-protocol-fee + x-provider-fee is less than max FEE_SCALE_BPS
      (asserts! (< (+ x-fee x-protocol-fee x-provider-fee) FEE_SCALE_BPS) ERR_INVALID_FEE)

      ;; Assert y-fee + y-protocol-fee + y-provider-fee is less than max FEE_SCALE_BPS
      (asserts! (< (+ y-fee y-protocol-fee y-provider-fee) FEE_SCALE_BPS) ERR_INVALID_FEE)

      ;; Transfer 1 uSTX from caller to BURN_ADDRESS
      (try! (stx-transfer? u1 caller BURN_ADDRESS))

      ;; Set variable fees for pool
      (try! (contract-call? pool-trait set-variable-fees x-fee y-fee))

      ;; Print function data and return true
      (print {
        action: "set-variable-fees",
        caller: caller,
        data: {
          pool-id: (get pool-id pool-data),
          pool-name: (get pool-name pool-data),
          pool-contract: (contract-of pool-trait),
          x-protocol-fee: x-protocol-fee,
          x-provider-fee: x-provider-fee,
          x-variable-fee: x-fee,
          y-protocol-fee: y-protocol-fee,
          y-provider-fee: y-provider-fee,
          y-variable-fee: y-fee
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
| pool-trait | trait_reference |
| x-fee | uint |
| y-fee | uint |

### set-x-fees

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L820)

`(define-public (set-x-fees ((pool-trait trait_reference) (protocol-fee uint) (provider-fee uint)) (response bool uint))`

Set x fees for a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-x-fees (pool-trait <dlmm-pool-trait>) (protocol-fee uint) (provider-fee uint))
  (let (
    ;; Get pool data
    (pool-data (unwrap! (contract-call? pool-trait get-pool) ERR_NO_POOL_DATA))
    (x-variable-fee (get x-variable-fee pool-data))
    (caller tx-sender)
  )
    (begin
      ;; Assert caller is an admin and pool is created and valid
      (asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)
      (asserts! (is-valid-pool (get pool-id pool-data) (contract-of pool-trait)) ERR_INVALID_POOL)
      (asserts! (get pool-created pool-data) ERR_POOL_NOT_CREATED)

      ;; Assert protocol-fee + provider-fee + x-variable-fee is less than max FEE_SCALE_BPS
      (asserts! (< (+ protocol-fee provider-fee x-variable-fee) FEE_SCALE_BPS) ERR_INVALID_FEE)

      ;; Transfer 1 uSTX from caller to BURN_ADDRESS
      (try! (stx-transfer? u1 caller BURN_ADDRESS))

      ;; Set x fees for pool
      (try! (contract-call? pool-trait set-x-fees protocol-fee provider-fee))

      ;; Print function data and return true
      (print {
        action: "set-x-fees",
        caller: caller,
        data: {
          pool-id: (get pool-id pool-data),
          pool-name: (get pool-name pool-data),
          pool-contract: (contract-of pool-trait),
          x-protocol-fee: protocol-fee,
          x-provider-fee: provider-fee,
          x-variable-fee: x-variable-fee
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
| pool-trait | trait_reference |
| protocol-fee | uint |
| provider-fee | uint |

### set-y-fees

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L861)

`(define-public (set-y-fees ((pool-trait trait_reference) (protocol-fee uint) (provider-fee uint)) (response bool uint))`

Set y fees for a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-y-fees (pool-trait <dlmm-pool-trait>) (protocol-fee uint) (provider-fee uint))
  (let (
    ;; Get pool data
    (pool-data (unwrap! (contract-call? pool-trait get-pool) ERR_NO_POOL_DATA))
    (y-variable-fee (get y-variable-fee pool-data))
    (caller tx-sender)
  )
    (begin
      ;; Assert caller is an admin and pool is created and valid
      (asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)
      (asserts! (is-valid-pool (get pool-id pool-data) (contract-of pool-trait)) ERR_INVALID_POOL)
      (asserts! (get pool-created pool-data) ERR_POOL_NOT_CREATED)

      ;; Assert protocol-fee + provider-fee + y-variable-fee is less than max FEE_SCALE_BPS
      (asserts! (< (+ protocol-fee provider-fee y-variable-fee) FEE_SCALE_BPS) ERR_INVALID_FEE)

      ;; Transfer 1 uSTX from caller to BURN_ADDRESS
      (try! (stx-transfer? u1 caller BURN_ADDRESS))

      ;; Set y fees for pool
      (try! (contract-call? pool-trait set-y-fees protocol-fee provider-fee))

      ;; Print function data and return true
      (print {
        action: "set-y-fees",
        caller: caller,
        data: {
          pool-id: (get pool-id pool-data),
          pool-name: (get pool-name pool-data),
          pool-contract: (contract-of pool-trait),
          y-protocol-fee: protocol-fee,
          y-provider-fee: provider-fee,
          y-variable-fee: y-variable-fee
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
| pool-trait | trait_reference |
| protocol-fee | uint |
| provider-fee | uint |

### set-variable-fees-cooldown

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L902)

`(define-public (set-variable-fees-cooldown ((pool-trait trait_reference) (cooldown uint)) (response bool uint))`

Set variable fees cooldown for a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-variable-fees-cooldown (pool-trait <dlmm-pool-trait>) (cooldown uint))
  (let (
    ;; Get pool data
    (pool-data (unwrap! (contract-call? pool-trait get-pool) ERR_NO_POOL_DATA))
    (caller tx-sender)
  )
    (begin
      ;; Assert caller is an admin and pool is created and valid
      (asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)
      (asserts! (is-valid-pool (get pool-id pool-data) (contract-of pool-trait)) ERR_INVALID_POOL)
      (asserts! (get pool-created pool-data) ERR_POOL_NOT_CREATED)

      ;; Transfer 1 uSTX from caller to BURN_ADDRESS
      (try! (stx-transfer? u1 caller BURN_ADDRESS))

      ;; Set variable fees cooldown for pool
      (try! (contract-call? pool-trait set-variable-fees-cooldown cooldown))

      ;; Print function data and return true
      (print {
        action: "set-variable-fees-cooldown",
        caller: caller,
        data: {
          pool-id: (get pool-id pool-data),
          pool-name: (get pool-name pool-data),
          pool-contract: (contract-of pool-trait),
          cooldown: cooldown
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
| pool-trait | trait_reference |
| cooldown | uint |

### set-freeze-variable-fees-manager

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L937)

`(define-public (set-freeze-variable-fees-manager ((pool-trait trait_reference)) (response bool uint))`

Make variable fees manager immutable for a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-freeze-variable-fees-manager (pool-trait <dlmm-pool-trait>))
  (let (
    ;; Get pool data
    (pool-data (unwrap! (contract-call? pool-trait get-pool) ERR_NO_POOL_DATA))
    (freeze-variable-fees-manager (get freeze-variable-fees-manager pool-data))
    (caller tx-sender)
  )
    (begin
      ;; Assert caller is an admin and pool is created and valid
      (asserts! (is-some (index-of (var-get admins) caller)) ERR_NOT_AUTHORIZED)
      (asserts! (is-valid-pool (get pool-id pool-data) (contract-of pool-trait)) ERR_INVALID_POOL)
      (asserts! (get pool-created pool-data) ERR_POOL_NOT_CREATED)

      ;; Assert variable fees manager is not frozen
      (asserts! (not freeze-variable-fees-manager) ERR_VARIABLE_FEES_MANAGER_FROZEN)

      ;; Transfer 1 uSTX from caller to BURN_ADDRESS
      (try! (stx-transfer? u1 caller BURN_ADDRESS))

      ;; Set freeze variable fees manager for pool
      (try! (contract-call? pool-trait set-freeze-variable-fees-manager))

      ;; Print function data and return true
      (print {
        action: "set-freeze-variable-fees-manager",
        caller: caller,
        data: {
          pool-id: (get pool-id pool-data),
          pool-name: (get pool-name pool-data),
          pool-contract: (contract-of pool-trait)
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
| pool-trait | trait_reference |

### set-dynamic-config

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L975)

`(define-public (set-dynamic-config ((pool-trait trait_reference) (config (buff 4096))) (response bool uint))`

Set dynamic config for a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-dynamic-config (pool-trait <dlmm-pool-trait>) (config (buff 4096)))
  (let (
    ;; Get pool data
    (pool-data (unwrap! (contract-call? pool-trait get-pool) ERR_NO_POOL_DATA))
    (variable-fees-manager (get variable-fees-manager pool-data))
    (freeze-variable-fees-manager (get freeze-variable-fees-manager pool-data))
    (caller tx-sender)
  )
    (begin
      ;; Assert caller is an admin or variable fees manager and pool is created and valid
      (asserts! (or (is-some (index-of (var-get admins) caller)) (is-eq variable-fees-manager caller)) ERR_NOT_AUTHORIZED)
      (asserts! (is-valid-pool (get pool-id pool-data) (contract-of pool-trait)) ERR_INVALID_POOL)
      (asserts! (get pool-created pool-data) ERR_POOL_NOT_CREATED)

      ;; Assert caller is variable fees manager if variable fees manager is frozen
      (asserts! (or (is-eq variable-fees-manager caller) (not freeze-variable-fees-manager)) ERR_NOT_AUTHORIZED)

      ;; Assert config is greater than 0
      (asserts! (> (len config) u0) ERR_INVALID_DYNAMIC_CONFIG)

      ;; Transfer 1 uSTX from caller to BURN_ADDRESS
      (try! (stx-transfer? u1 caller BURN_ADDRESS))

      ;; Set dynamic config for pool
      (try! (contract-call? pool-trait set-dynamic-config config))

      ;; Print function data and return true
      (print {
        action: "set-dynamic-config",
        caller: caller,
        data: {
          pool-id: (get pool-id pool-data),
          pool-name: (get pool-name pool-data),
          pool-contract: (contract-of pool-trait),
          config: config
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
| pool-trait | trait_reference |
| config | (buff 4096) |

### reset-variable-fees

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L1018)

`(define-public (reset-variable-fees ((pool-trait trait_reference)) (response bool uint))`

Reset variable fees for a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-public (reset-variable-fees (pool-trait <dlmm-pool-trait>))
  (let (
    ;; Get pool data
    (pool-data (unwrap! (contract-call? pool-trait get-pool) ERR_NO_POOL_DATA))
    (last-variable-fees-update (get last-variable-fees-update pool-data))
    (variable-fees-cooldown (get variable-fees-cooldown pool-data))
    (caller tx-sender)
  )
    (begin
      ;; Assert pool is created and valid
      (asserts! (is-valid-pool (get pool-id pool-data) (contract-of pool-trait)) ERR_INVALID_POOL)
      (asserts! (get pool-created pool-data) ERR_POOL_NOT_CREATED)

      ;; Assert variable fees cooldown period has passed
      (asserts! (>= stacks-block-height (+ last-variable-fees-update variable-fees-cooldown)) ERR_VARIABLE_FEES_COOLDOWN)

      ;; Reset variable fees for pool
      (try! (contract-call? pool-trait set-variable-fees u0 u0))

      ;; Print function data and return true
      (print {
        action: "reset-variable-fees",
        caller: caller,
        data: {
          pool-id: (get pool-id pool-data),
          pool-name: (get pool-name pool-data),
          pool-contract: (contract-of pool-trait)
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
| pool-trait | trait_reference |

### create-pool

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L1053)

`(define-public (create-pool ((pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference) (x-amount-active-bin uint) (y-amount-active-bin uint) (burn-amount-active-bin uint) (x-protocol-fee uint) (x-provider-fee uint) (y-protocol-fee uint) (y-provider-fee uint) (bin-step uint) (variable-fees-cooldown uint) (freeze-variable-fees-manager bool) (dynamic-config (optional (buff 4096))) (fee-address principal) (uri (string-ascii 256)) (status bool)) (response bool uint))`

Create a new pool

<details>
  <summary>Source code:</summary>

```clarity
(define-public (create-pool 
    (pool-trait <dlmm-pool-trait>)
    (x-token-trait <sip-010-trait>) (y-token-trait <sip-010-trait>)
    (x-amount-active-bin uint) (y-amount-active-bin uint) (burn-amount-active-bin uint)
    (x-protocol-fee uint) (x-provider-fee uint)
    (y-protocol-fee uint) (y-provider-fee uint)
    (bin-step uint) (variable-fees-cooldown uint) (freeze-variable-fees-manager bool)
    (dynamic-config (optional (buff 4096))) (fee-address principal)
    (uri (string-ascii 256)) (status bool)
  )
  (let (
    ;; Get pool data and pool contract
    (pool-data (unwrap! (contract-call? pool-trait get-pool) ERR_NO_POOL_DATA))
    (pool-contract (contract-of pool-trait))
    (x-variable-fee (get x-variable-fee pool-data))
    (y-variable-fee (get y-variable-fee pool-data))

    ;; Get pool ID and create pool symbol and name
    (new-pool-id (+ (var-get last-pool-id) u1))
    (symbol (unwrap! (create-symbol x-token-trait y-token-trait) ERR_INVALID_POOL_SYMBOL))
    (name (concat symbol "-LP"))

    ;; Check if pool code hash is verified
    (pool-code-hash (unwrap! (contract-hash? (contract-of pool-trait)) ERR_INVALID_POOL_CODE_HASH))
    (pool-verified-check (is-some (index-of (var-get verified-pool-code-hashes) pool-code-hash)))

    ;; Get token contracts
    (x-token-contract (contract-of x-token-trait))
    (y-token-contract (contract-of y-token-trait))

    ;; Get dynamic config if provided
    (unwrapped-dynamic-config (if (is-some dynamic-config) (unwrap-panic dynamic-config) 0x))

    ;; Get initial price at active bin
    (initial-price (/ (* y-amount-active-bin PRICE_SCALE_BPS) x-amount-active-bin))

    ;; Scale up y-amount-active-bin
    (y-amount-active-bin-scaled (* y-amount-active-bin PRICE_SCALE_BPS))

    ;; Get liquidity value and calculate dlp
    (add-liquidity-value (unwrap! (get-liquidity-value x-amount-active-bin y-amount-active-bin-scaled initial-price) ERR_INVALID_LIQUIDITY_VALUE))
    (dlp (sqrti add-liquidity-value))
    (caller tx-sender)
  )
    (begin
      ;; Assert caller is an admin or public-pool-creation is true
      (asserts! (or (is-some (index-of (var-get admins) caller)) (var-get public-pool-creation)) ERR_NOT_AUTHORIZED)

      ;; Assert pool is not created
      (asserts! (not (get pool-created pool-data)) ERR_POOL_ALREADY_CREATED)

      ;; Assert x-token-contract and y-token-contract are not matching
      (asserts! (not (is-eq x-token-contract y-token-contract)) ERR_MATCHING_TOKEN_CONTRACTS)

      ;; Assert fee-address is standard principal
      (asserts! (is-standard fee-address) ERR_INVALID_PRINCIPAL)

      ;; Assert reverse token direction is not registered
      (asserts! (is-none (map-get? allowed-token-direction {x-token: y-token-contract, y-token: x-token-contract})) ERR_INVALID_TOKEN_DIRECTION)

      ;; Assert x-amount-active-bin and y-amount-active-bin are greater than 0
      (asserts! (and (> x-amount-active-bin u0) (> y-amount-active-bin u0)) ERR_INVALID_AMOUNT)

      ;; Assert dlp minted meets min bin shares required
      (asserts! (>= dlp (var-get minimum-bin-shares)) ERR_MINIMUM_LP_AMOUNT)

      ;; Assert burn-amount-active-bin meets min shares required to burn
      (asserts! (>= burn-amount-active-bin (var-get minimum-burnt-shares)) ERR_MINIMUM_BURN_AMOUNT)

      ;; Assert dlp is greater than or equal to 0 after subtracting burn amount
      (asserts! (>= (- dlp burn-amount-active-bin) u0) ERR_MINIMUM_LP_AMOUNT)

      ;; Assert initial price is greater than 0
      (asserts! (> initial-price u0) ERR_INVALID_INITIAL_PRICE)

      ;; Assert length of pool uri, symbol, and name is greater than 0
      (asserts! (> (len uri) u0) ERR_INVALID_POOL_URI)
      (asserts! (> (len symbol) u0) ERR_INVALID_POOL_SYMBOL)
      (asserts! (> (len name) u0) ERR_INVALID_POOL_NAME)

      ;; Assert fees are less than max BPS
      (asserts! (< (+ x-protocol-fee x-provider-fee x-variable-fee) FEE_SCALE_BPS) ERR_INVALID_FEE)
      (asserts! (< (+ y-protocol-fee y-provider-fee y-variable-fee) FEE_SCALE_BPS) ERR_INVALID_FEE)

      ;; Assert bin step is valid
      (asserts! (is-some (index-of (var-get bin-steps) bin-step)) ERR_INVALID_BIN_STEP)

      ;; Assert bin price is valid at extremes
      (try! (get-bin-price initial-price bin-step MIN_BIN_ID))

      ;; Create pool, set fees, and set variable fees cooldown
      (try! (contract-call? pool-trait create-pool x-token-contract y-token-contract CONTRACT_DEPLOYER fee-address caller 0 bin-step initial-price new-pool-id name symbol uri))
      (try! (contract-call? pool-trait set-x-fees x-protocol-fee x-provider-fee))
      (try! (contract-call? pool-trait set-y-fees y-protocol-fee y-provider-fee))
      (try! (contract-call? pool-trait set-variable-fees-cooldown variable-fees-cooldown))

      ;; Freeze variable fees manager if freeze-variable-fees-manager is true
      (if freeze-variable-fees-manager (try! (contract-call? pool-trait set-freeze-variable-fees-manager)) false)

      ;; Set dynamic config if unwrapped-dynamic-config is greater than 0
      (if (> (len unwrapped-dynamic-config) u0) (try! (contract-call? pool-trait set-dynamic-config unwrapped-dynamic-config)) false)

      ;; Update ID of last created pool, add pool to pools map, and add pool to unclaimed-protocol-fees map
      (var-set last-pool-id new-pool-id)
      (map-set pools new-pool-id {id: new-pool-id, name: name, symbol: symbol, pool-contract: pool-contract, status: status})
      (map-set unclaimed-protocol-fees new-pool-id {x-fee: u0, y-fee: u0})

      ;; Update allowed-token-direction map if needed
      (if (is-none (map-get? allowed-token-direction {x-token: x-token-contract, y-token: y-token-contract}))
          (map-set allowed-token-direction {x-token: x-token-contract, y-token: y-token-contract} true)
          false)

      ;; Transfer x-amount-active-bin x tokens and y-amount-active-bin y tokens from caller to pool-contract
      (try! (contract-call? x-token-trait transfer x-amount-active-bin caller pool-contract none))
      (try! (contract-call? y-token-trait transfer y-amount-active-bin caller pool-contract none))

      ;; Update bin balances
      (try! (contract-call? pool-trait update-bin-balances CENTER_BIN_ID x-amount-active-bin y-amount-active-bin))

      ;; Mint LP tokens to caller
      (try! (contract-call? pool-trait pool-mint CENTER_BIN_ID (- dlp burn-amount-active-bin) caller))

      ;; Mint burn amount LP tokens to BURN_ADDRESS
      (try! (contract-call? pool-trait pool-mint CENTER_BIN_ID burn-amount-active-bin BURN_ADDRESS))

      ;; Print create pool data and return true
      (print {
        action: "create-pool",
        caller: caller,
        data: {
          pool-id: new-pool-id,
          pool-name: name,
          pool-contract: pool-contract,
          pool-verified: pool-verified-check,
          x-token: x-token-contract,
          y-token: y-token-contract,
          x-protocol-fee: x-protocol-fee,
          x-provider-fee: x-provider-fee,
          x-variable-fee: x-variable-fee,
          y-protocol-fee: y-protocol-fee,
          y-provider-fee: y-provider-fee,
          y-variable-fee: y-variable-fee,
          x-amount-active-bin: x-amount-active-bin,
          y-amount-active-bin: y-amount-active-bin,
          burn-amount-active-bin: burn-amount-active-bin,
          dlp: dlp,
          add-liquidity-value: add-liquidity-value,
          pool-symbol: symbol,
          pool-uri: uri,
          pool-status: status,
          creation-height: burn-block-height,
          active-bin-id: 0,
          bin-step: bin-step,
          initial-price: initial-price,
          variable-fees-manager: CONTRACT_DEPLOYER,
          fee-address: fee-address,
          variable-fees-cooldown: variable-fees-cooldown,
          freeze-variable-fees-manager: freeze-variable-fees-manager,
          dynamic-config: dynamic-config
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
| pool-trait | trait_reference |
| x-token-trait | trait_reference |
| y-token-trait | trait_reference |
| x-amount-active-bin | uint |
| y-amount-active-bin | uint |
| burn-amount-active-bin | uint |
| x-protocol-fee | uint |
| x-provider-fee | uint |
| y-protocol-fee | uint |
| y-provider-fee | uint |
| bin-step | uint |
| variable-fees-cooldown | uint |
| freeze-variable-fees-manager | bool |
| dynamic-config | (optional (buff 4096)) |
| fee-address | principal |
| uri | (string-ascii 256) |
| status | bool |

### swap-x-for-y

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L1220)

`(define-public (swap-x-for-y ((pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference) (bin-id int) (x-amount uint)) (response (tuple (in uint) (out uint)) uint))`

Swap x token for y token via a bin in a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-public (swap-x-for-y
    (pool-trait <dlmm-pool-trait>)
    (x-token-trait <sip-010-trait>) (y-token-trait <sip-010-trait>)
    (bin-id int) (x-amount uint)
  )
  (let (
    ;; Get pool data and check if pool is valid
    (caller tx-sender)
    (pool-data (unwrap! (contract-call? pool-trait get-pool-for-swap true) ERR_NO_POOL_DATA))
    (pool-id (get pool-id pool-data))
    (pool-contract (contract-of pool-trait))
    (pool-validity-check (asserts! (is-valid-pool pool-id pool-contract) ERR_INVALID_POOL))
    (x-token (get x-token pool-data))
    (y-token (get y-token pool-data))
    (bin-step (get bin-step pool-data))
    (initial-price (get initial-price pool-data))
    (active-bin-id (get active-bin-id pool-data))

    ;; Check if caller is fee exempt and calculate swap fees
    (swap-fee-exemption (default-to false (map-get? swap-fee-exemptions {address: caller, id: pool-id})))
    (protocol-fee (if swap-fee-exemption u0 (get protocol-fee pool-data)))
    (provider-fee (if swap-fee-exemption u0 (get provider-fee pool-data)))
    (variable-fee (if swap-fee-exemption u0 (get variable-fee pool-data)))

    ;; Convert bin-id to an unsigned bin-id
    (unsigned-bin-id (to-uint (+ bin-id (to-int CENTER_BIN_ID))))

    ;; Get balances at bin
    (bin-balances (try! (contract-call? pool-trait get-bin-balances unsigned-bin-id)))
    (x-balance (get x-balance bin-balances))
    (y-balance (get y-balance bin-balances))

    ;; Check if both initial bin balances are equal to 0
    (initial-bin-balances-empty (and (is-eq x-balance u0) (is-eq y-balance u0)))

    ;; Get price at bin
    (bin-price (unwrap! (get-bin-price initial-price bin-step bin-id) ERR_INVALID_BIN_PRICE))

    ;; Calculate max x-amount with fees
    (swap-fee-total (+ protocol-fee provider-fee variable-fee))
    (max-x-amount (/ (+ (* y-balance PRICE_SCALE_BPS) (- bin-price u1)) bin-price))
    (updated-max-x-amount (if (> swap-fee-total u0) (/ (* max-x-amount FEE_SCALE_BPS) (- FEE_SCALE_BPS swap-fee-total)) max-x-amount))

    ;; Calculate x-amount to use for the swap
    (updated-x-amount (if (>= x-amount updated-max-x-amount) updated-max-x-amount x-amount))

    ;; Calculate fees and dx
    (x-amount-fees-total (/ (* updated-x-amount swap-fee-total) FEE_SCALE_BPS))
    (x-amount-fees-protocol (/ (* updated-x-amount protocol-fee) FEE_SCALE_BPS))
    (x-amount-fees-variable (/ (* updated-x-amount variable-fee) FEE_SCALE_BPS))
    (x-amount-fees-provider (- x-amount-fees-total x-amount-fees-protocol x-amount-fees-variable))
    (dx (- updated-x-amount x-amount-fees-total))

    ;; Calculate dy
    (dy-before-cap (/ (* dx bin-price) PRICE_SCALE_BPS))
    (dy (if (> dy-before-cap y-balance) y-balance dy-before-cap))

    ;; Calculate updated bin balances
    (updated-x-balance (+ x-balance dx x-amount-fees-provider x-amount-fees-variable))
    (updated-y-balance (- y-balance dy))

    ;; Calculate new active bin ID (default to bin-id if at the edge of the bin range)
    (updated-active-bin-id (if (and (or (is-eq updated-y-balance u0) initial-bin-balances-empty) (> bin-id MIN_BIN_ID))
                               (- bin-id 1)
                               bin-id))

    ;; Get current unclaimed protocol fees for pool
    (current-unclaimed-protocol-fees (unwrap! (map-get? unclaimed-protocol-fees pool-id) ERR_NO_UNCLAIMED_PROTOCOL_FEES_DATA))
  )
    (begin
      ;; Assert pool-status is true and correct token traits are used
      (asserts! (is-enabled-pool pool-id) ERR_POOL_DISABLED)
      (asserts! (is-eq (contract-of x-token-trait) x-token) ERR_INVALID_X_TOKEN)
      (asserts! (is-eq (contract-of y-token-trait) y-token) ERR_INVALID_Y_TOKEN)

      ;; Assert x-amount is greater than 0
      (asserts! (> x-amount u0) ERR_INVALID_AMOUNT)

      ;; Assert bin-id is equal to active-bin-id
      (asserts! (is-eq bin-id active-bin-id) ERR_NOT_ACTIVE_BIN)

      ;; Transfer updated-x-amount x tokens from caller to pool-contract
      (if (and (> updated-x-amount u0) (not initial-bin-balances-empty))
          (try! (contract-call? x-token-trait transfer updated-x-amount caller pool-contract none))
          false)

      ;; Transfer dy y tokens from pool-contract to caller
      (if (and (> dy u0) (not initial-bin-balances-empty))
          (try! (contract-call? pool-trait pool-transfer y-token-trait dy caller))
          false)

      ;; Update unclaimed-protocol-fees for pool
      (if (> x-amount-fees-protocol u0)
          (map-set unclaimed-protocol-fees pool-id (merge current-unclaimed-protocol-fees {
            x-fee: (+ (get x-fee current-unclaimed-protocol-fees) x-amount-fees-protocol)
          }))
          false)

      ;; Update bin balances
      (if (and (> updated-x-amount u0) (not initial-bin-balances-empty))
          (try! (contract-call? pool-trait update-bin-balances unsigned-bin-id updated-x-balance updated-y-balance))
          false)

      ;; Set active bin ID
      (if (not (is-eq updated-active-bin-id active-bin-id))
          (try! (contract-call? pool-trait set-active-bin-id updated-active-bin-id))
          false)

      ;; Print swap data and return number of y tokens the caller received
      (print {
        action: "swap-x-for-y",
        caller: caller,
        data: {
          pool-id: pool-id,
          pool-name: (get pool-name pool-data),
          pool-contract: pool-contract,
          x-token: x-token,
          y-token: y-token,
          bin-step: bin-step,
          initial-price: initial-price,
          bin-price: bin-price,
          active-bin-id: active-bin-id,
          updated-active-bin-id: updated-active-bin-id,
          bin-id: bin-id,
          unsigned-bin-id: unsigned-bin-id,
          x-amount: x-amount,
          updated-x-amount: updated-x-amount,
          updated-max-x-amount: updated-max-x-amount,
          x-amount-fees-protocol: x-amount-fees-protocol,
          x-amount-fees-provider: x-amount-fees-provider,
          x-amount-fees-variable: x-amount-fees-variable,
          swap-fee-exemption: swap-fee-exemption,
          dx: dx,
          dy: dy,
          updated-x-balance: updated-x-balance,
          updated-y-balance: updated-y-balance,
          initial-bin-balances-empty: initial-bin-balances-empty
        }
      })
      (ok {in: updated-x-amount, out: dy})
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-trait | trait_reference |
| x-token-trait | trait_reference |
| y-token-trait | trait_reference |
| bin-id | int |
| x-amount | uint |

### swap-y-for-x

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L1365)

`(define-public (swap-y-for-x ((pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference) (bin-id int) (y-amount uint)) (response (tuple (in uint) (out uint)) uint))`

Swap y token for x token via a bin in a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-public (swap-y-for-x
    (pool-trait <dlmm-pool-trait>)
    (x-token-trait <sip-010-trait>) (y-token-trait <sip-010-trait>)
    (bin-id int) (y-amount uint)
  )
  (let (
    ;; Get pool data and check if pool is valid
    (caller tx-sender)
    (pool-data (unwrap! (contract-call? pool-trait get-pool-for-swap false) ERR_NO_POOL_DATA))
    (pool-id (get pool-id pool-data))
    (pool-contract (contract-of pool-trait))
    (pool-validity-check (asserts! (is-valid-pool pool-id pool-contract) ERR_INVALID_POOL))
    (x-token (get x-token pool-data))
    (y-token (get y-token pool-data))
    (bin-step (get bin-step pool-data))
    (initial-price (get initial-price pool-data))
    (active-bin-id (get active-bin-id pool-data))

    ;; Check if caller is fee exempt and calculate swap fees
    (swap-fee-exemption (default-to false (map-get? swap-fee-exemptions {address: caller, id: pool-id})))
    (protocol-fee (if swap-fee-exemption u0 (get protocol-fee pool-data)))
    (provider-fee (if swap-fee-exemption u0 (get provider-fee pool-data)))
    (variable-fee (if swap-fee-exemption u0 (get variable-fee pool-data)))

    ;; Convert bin-id to an unsigned bin-id
    (unsigned-bin-id (to-uint (+ bin-id (to-int CENTER_BIN_ID))))

    ;; Get balances at bin
    (bin-balances (try! (contract-call? pool-trait get-bin-balances unsigned-bin-id)))
    (x-balance (get x-balance bin-balances))
    (y-balance (get y-balance bin-balances))

    ;; Check if both initial bin balances are equal to 0
    (initial-bin-balances-empty (and (is-eq x-balance u0) (is-eq y-balance u0)))

    ;; Get price at bin
    (bin-price (unwrap! (get-bin-price initial-price bin-step bin-id) ERR_INVALID_BIN_PRICE))

    ;; Calculate max y-amount with fees
    (swap-fee-total (+ protocol-fee provider-fee variable-fee))
    (max-y-amount (/ (+ (* x-balance bin-price) (- PRICE_SCALE_BPS u1)) PRICE_SCALE_BPS))
    (updated-max-y-amount (if (> swap-fee-total u0) (/ (* max-y-amount FEE_SCALE_BPS) (- FEE_SCALE_BPS swap-fee-total)) max-y-amount))

    ;; Calculate y-amount to use for the swap
    (updated-y-amount (if (>= y-amount updated-max-y-amount) updated-max-y-amount y-amount))

    ;; Calculate fees and dy
    (y-amount-fees-total (/ (* updated-y-amount swap-fee-total) FEE_SCALE_BPS))
    (y-amount-fees-protocol (/ (* updated-y-amount protocol-fee) FEE_SCALE_BPS))
    (y-amount-fees-variable (/ (* updated-y-amount variable-fee) FEE_SCALE_BPS))
    (y-amount-fees-provider (- y-amount-fees-total y-amount-fees-protocol y-amount-fees-variable))
    (dy (- updated-y-amount y-amount-fees-total))

    ;; Calculate dx
    (dx-before-cap (/ (* dy PRICE_SCALE_BPS) bin-price))
    (dx (if (> dx-before-cap x-balance) x-balance dx-before-cap))

    ;; Calculate updated bin balances
    (updated-x-balance (- x-balance dx))
    (updated-y-balance (+ y-balance dy y-amount-fees-provider y-amount-fees-variable))

    ;; Calculate new active bin ID (default to bin-id if at the edge of the bin range)
    (updated-active-bin-id (if (and (or (is-eq updated-x-balance u0) initial-bin-balances-empty) (< bin-id MAX_BIN_ID))
                               (+ bin-id 1)
                               bin-id))

    ;; Get current unclaimed protocol fees for pool
    (current-unclaimed-protocol-fees (unwrap! (map-get? unclaimed-protocol-fees pool-id) ERR_NO_UNCLAIMED_PROTOCOL_FEES_DATA))
  )
    (begin
      ;; Assert pool-status is true and correct token traits are used
      (asserts! (is-enabled-pool pool-id) ERR_POOL_DISABLED)
      (asserts! (is-eq (contract-of x-token-trait) x-token) ERR_INVALID_X_TOKEN)
      (asserts! (is-eq (contract-of y-token-trait) y-token) ERR_INVALID_Y_TOKEN)

      ;; Assert y-amount is greater than 0
      (asserts! (> y-amount u0) ERR_INVALID_AMOUNT)

      ;; Assert bin-id is equal to active-bin-id
      (asserts! (is-eq bin-id active-bin-id) ERR_NOT_ACTIVE_BIN)

      ;; Transfer updated-y-amount y tokens from caller to pool-contract
      (if (and (> updated-y-amount u0) (not initial-bin-balances-empty))
          (try! (contract-call? y-token-trait transfer updated-y-amount caller pool-contract none))
          false)

      ;; Transfer dx x tokens from pool-contract to caller
      (if (and (> dx u0) (not initial-bin-balances-empty))
          (try! (contract-call? pool-trait pool-transfer x-token-trait dx caller))
          false)

      ;; Update unclaimed-protocol-fees for pool
      (if (> y-amount-fees-protocol u0)
          (map-set unclaimed-protocol-fees pool-id (merge current-unclaimed-protocol-fees {
            y-fee: (+ (get y-fee current-unclaimed-protocol-fees) y-amount-fees-protocol)
          }))
          false)

      ;; Update bin balances
      (if (and (> updated-y-amount u0) (not initial-bin-balances-empty))
          (try! (contract-call? pool-trait update-bin-balances unsigned-bin-id updated-x-balance updated-y-balance))
          false)

      ;; Set active bin ID
      (if (not (is-eq updated-active-bin-id active-bin-id))
          (try! (contract-call? pool-trait set-active-bin-id updated-active-bin-id))
          false)

      ;; Print swap data and return number of x tokens the caller received
      (print {
        action: "swap-y-for-x",
        caller: caller,
        data: {
          pool-id: pool-id,
          pool-name: (get pool-name pool-data),
          pool-contract: pool-contract,
          x-token: x-token,
          y-token: y-token,
          bin-step: bin-step,
          initial-price: initial-price,
          bin-price: bin-price,
          active-bin-id: active-bin-id,
          updated-active-bin-id: updated-active-bin-id,
          bin-id: bin-id,
          unsigned-bin-id: unsigned-bin-id,
          y-amount: y-amount,
          updated-y-amount: updated-y-amount,
          updated-max-y-amount: updated-max-y-amount,
          y-amount-fees-protocol: y-amount-fees-protocol,
          y-amount-fees-provider: y-amount-fees-provider,
          y-amount-fees-variable: y-amount-fees-variable,
          swap-fee-exemption: swap-fee-exemption,
          dy: dy,
          dx: dx,
          updated-x-balance: updated-x-balance,
          updated-y-balance: updated-y-balance,
          initial-bin-balances-empty: initial-bin-balances-empty
        }
      })
      (ok {in: updated-y-amount, out: dx})
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-trait | trait_reference |
| x-token-trait | trait_reference |
| y-token-trait | trait_reference |
| bin-id | int |
| y-amount | uint |

### add-liquidity

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L1510)

`(define-public (add-liquidity ((pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference) (bin-id int) (x-amount uint) (y-amount uint) (min-dlp uint) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint)) (response uint uint))`

Add liquidity to a bin in a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-public (add-liquidity
    (pool-trait <dlmm-pool-trait>)
    (x-token-trait <sip-010-trait>) (y-token-trait <sip-010-trait>)
    (bin-id int) (x-amount uint) (y-amount uint) (min-dlp uint)
    (max-x-liquidity-fee uint) (max-y-liquidity-fee uint)
  )
  (let (
    ;; Get pool data and check if pool is valid
    (pool-data (unwrap! (contract-call? pool-trait get-pool-for-add) ERR_NO_POOL_DATA))
    (pool-contract (contract-of pool-trait))
    (pool-validity-check (asserts! (is-valid-pool (get pool-id pool-data) pool-contract) ERR_INVALID_POOL))
    (x-token (get x-token pool-data))
    (y-token (get y-token pool-data))
    (bin-step (get bin-step pool-data))
    (initial-price (get initial-price pool-data))
    (active-bin-id (get active-bin-id pool-data))

    ;; Convert bin-id to an unsigned bin-id
    (unsigned-bin-id (to-uint (+ bin-id (to-int CENTER_BIN_ID))))

    ;; Get balances at bin
    (bin-balances (try! (contract-call? pool-trait get-bin-balances unsigned-bin-id)))
    (x-balance (get x-balance bin-balances))
    (y-balance (get y-balance bin-balances))
    (bin-shares (get bin-shares bin-balances))

    ;; Get price at bin
    (bin-price (unwrap! (get-bin-price initial-price bin-step bin-id) ERR_INVALID_BIN_PRICE))

    ;; Scale up y-amount and y-balance
    (y-amount-scaled (* y-amount PRICE_SCALE_BPS))
    (y-balance-scaled (* y-balance PRICE_SCALE_BPS))

    ;; Get current liquidity values and calculate dlp without fees
    (add-liquidity-value (unwrap! (get-liquidity-value x-amount y-amount-scaled bin-price) ERR_INVALID_LIQUIDITY_VALUE))
    (bin-liquidity-value (unwrap! (get-liquidity-value x-balance y-balance-scaled bin-price) ERR_INVALID_LIQUIDITY_VALUE))
    (dlp (if (or (is-eq bin-shares u0) (is-eq bin-liquidity-value u0))
             (sqrti add-liquidity-value)
             (/ (* add-liquidity-value bin-shares) bin-liquidity-value)))

    ;; Calculate liquidity fees if adding liquidity to active bin based on ratio of bin balances
    (add-liquidity-fees (if (and (is-eq bin-id active-bin-id) (> dlp u0))
      (let (
        (x-liquidity-fee (+ (get x-protocol-fee pool-data) (get x-provider-fee pool-data) (get x-variable-fee pool-data)))
        (y-liquidity-fee (+ (get y-protocol-fee pool-data) (get y-provider-fee pool-data) (get y-variable-fee pool-data)))

        ;; Calculate withdrawable x-amount without fees
        (x-amount-withdrawable (/ (* dlp (+ x-balance x-amount)) (+ bin-shares dlp)))

        ;; Calculate withdrawable y-amount without fees
        (y-amount-withdrawable (/ (* dlp (+ y-balance y-amount)) (+ bin-shares dlp)))

        ;; Calculate max liquidity fee for x-amount and y-amount
        (max-x-amount-fees-liquidity (if (and (> y-amount-withdrawable y-amount) (> x-amount x-amount-withdrawable))
                                         (/ (* (- x-amount x-amount-withdrawable) x-liquidity-fee) FEE_SCALE_BPS)
                                         u0))
        (max-y-amount-fees-liquidity (if (and (> x-amount-withdrawable x-amount) (> y-amount y-amount-withdrawable))
                                         (/ (* (- y-amount y-amount-withdrawable) y-liquidity-fee) FEE_SCALE_BPS)
                                         u0))
      )
        ;; Calculate final liquidity fee for x-amount and y-amount
        {
          x-amount-fees-liquidity: (if (> x-amount max-x-amount-fees-liquidity) max-x-amount-fees-liquidity x-amount),
          y-amount-fees-liquidity: (if (> y-amount max-y-amount-fees-liquidity) max-y-amount-fees-liquidity y-amount)
        }
      )
      {
        x-amount-fees-liquidity: u0,
        y-amount-fees-liquidity: u0
      })
    )

    ;; Get x-amount-fees-liquidity and y-amount-fees-liquidity
    (x-amount-fees-liquidity (get x-amount-fees-liquidity add-liquidity-fees))
    (y-amount-fees-liquidity (get y-amount-fees-liquidity add-liquidity-fees))

    ;; Calculate final x and y amounts post fees
    (x-amount-post-fees (- x-amount x-amount-fees-liquidity))
    (y-amount-post-fees (- y-amount y-amount-fees-liquidity))
    (y-amount-post-fees-scaled (* y-amount-post-fees PRICE_SCALE_BPS))

    ;; Calculate bin balances post fees
    (x-balance-post-fees (+ x-balance x-amount-fees-liquidity))
    (y-balance-post-fees-scaled (* (+ y-balance y-amount-fees-liquidity) PRICE_SCALE_BPS))

    ;; Get final liquidity value and calculate dlp post fees
    (add-liquidity-value-post-fees (unwrap! (get-liquidity-value x-amount-post-fees y-amount-post-fees-scaled bin-price) ERR_INVALID_LIQUIDITY_VALUE))
    (bin-liquidity-value-post-fees (unwrap! (get-liquidity-value x-balance-post-fees y-balance-post-fees-scaled bin-price) ERR_INVALID_LIQUIDITY_VALUE))
    (burn-amount (if (is-eq bin-shares u0) (var-get minimum-burnt-shares) u0))
    (dlp-post-fees (if (is-eq bin-shares u0)
      (let (
        (intended-dlp (sqrti add-liquidity-value-post-fees))
      )
        (asserts! (>= intended-dlp (var-get minimum-bin-shares)) ERR_MINIMUM_LP_AMOUNT)
        (try! (contract-call? pool-trait pool-mint unsigned-bin-id burn-amount BURN_ADDRESS))
        (- intended-dlp burn-amount)
      )
      (if (is-eq bin-liquidity-value-post-fees u0)
          (sqrti add-liquidity-value-post-fees)
          (/ (* add-liquidity-value-post-fees bin-shares) bin-liquidity-value-post-fees))))

    ;; Calculate updated bin balances
    (updated-x-balance (+ x-balance x-amount))
    (updated-y-balance (+ y-balance y-amount))
    (caller tx-sender)
  )
    (begin
      ;; Assert pool-status is true and correct token traits are used
      (asserts! (is-enabled-pool (get pool-id pool-data)) ERR_POOL_DISABLED)
      (asserts! (is-eq (contract-of x-token-trait) x-token) ERR_INVALID_X_TOKEN)
      (asserts! (is-eq (contract-of y-token-trait) y-token) ERR_INVALID_Y_TOKEN)

      ;; Assert x-amount + y-amount is greater than 0
      (asserts! (> (+ x-amount y-amount) u0) ERR_INVALID_AMOUNT)

      ;; Assert correct token amounts are being added based on bin-id and active-bin-id
      (asserts! (or (>= bin-id active-bin-id) (is-eq x-amount u0)) ERR_INVALID_X_AMOUNT)
      (asserts! (or (<= bin-id active-bin-id) (is-eq y-amount u0)) ERR_INVALID_Y_AMOUNT)

      ;; Assert min-dlp is greater than 0 and dlp-post-fees is greater than or equal to min-dlp
      (asserts! (> min-dlp u0) ERR_INVALID_MIN_DLP_AMOUNT)
      (asserts! (>= dlp-post-fees min-dlp) ERR_MINIMUM_LP_AMOUNT)

      ;; Assert x-amount-fees-liquidity is less than or equal to max-x-liquidity-fee
      (asserts! (<= x-amount-fees-liquidity max-x-liquidity-fee) ERR_MAXIMUM_X_LIQUIDITY_FEE)

      ;; Assert y-amount-fees-liquidity is less than or equal to max-y-liquidity-fee
      (asserts! (<= y-amount-fees-liquidity max-y-liquidity-fee) ERR_MAXIMUM_Y_LIQUIDITY_FEE)

      ;; Transfer x-amount x tokens from caller to pool-contract (includes x-amount-fees-liquidity)
      (if (> x-amount u0)
          (try! (contract-call? x-token-trait transfer x-amount caller pool-contract none))
          false)

      ;; Transfer y-amount y tokens from caller to pool-contract (includes y-amount-fees-liquidity)
      (if (> y-amount u0)
          (try! (contract-call? y-token-trait transfer y-amount caller pool-contract none))
          false)

      ;; Update bin balances
      (try! (contract-call? pool-trait update-bin-balances unsigned-bin-id updated-x-balance updated-y-balance))

      ;; Mint LP tokens to caller
      (try! (contract-call? pool-trait pool-mint unsigned-bin-id dlp-post-fees caller))

      ;; Print add liquidity data and return number of LP tokens the caller received
      (print {
        action: "add-liquidity",
        caller: caller,
        data: {
          pool-id: (get pool-id pool-data),
          pool-name: (get pool-name pool-data),
          pool-contract: pool-contract,
          x-token: x-token,
          y-token: y-token,
          bin-step: bin-step,
          initial-price: initial-price,
          bin-price: bin-price,
          active-bin-id: active-bin-id,
          bin-id: bin-id,
          unsigned-bin-id: unsigned-bin-id,
          x-amount: x-amount-post-fees,
          y-amount: y-amount-post-fees,
          x-amount-fees-liquidity: x-amount-fees-liquidity,
          y-amount-fees-liquidity: y-amount-fees-liquidity,
          burn-amount: burn-amount,
          dlp: dlp-post-fees,
          min-dlp: min-dlp,
          max-x-liquidity-fee: max-x-liquidity-fee,
          max-y-liquidity-fee: max-y-liquidity-fee,
          add-liquidity-value-post-fees: add-liquidity-value-post-fees,
          bin-liquidity-value-post-fees: bin-liquidity-value-post-fees,
          updated-x-balance: updated-x-balance,
          updated-y-balance: updated-y-balance,
          updated-bin-shares: (+ bin-shares dlp-post-fees burn-amount)
        }
      })
      (ok dlp-post-fees)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-trait | trait_reference |
| x-token-trait | trait_reference |
| y-token-trait | trait_reference |
| bin-id | int |
| x-amount | uint |
| y-amount | uint |
| min-dlp | uint |
| max-x-liquidity-fee | uint |
| max-y-liquidity-fee | uint |

### withdraw-liquidity

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L1693)

`(define-public (withdraw-liquidity ((pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference) (bin-id int) (amount uint) (min-x-amount uint) (min-y-amount uint)) (response (tuple (x-amount uint) (y-amount uint)) uint))`

Withdraw liquidity from a bin in a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-public (withdraw-liquidity
    (pool-trait <dlmm-pool-trait>)
    (x-token-trait <sip-010-trait>) (y-token-trait <sip-010-trait>)
    (bin-id int) (amount uint) (min-x-amount uint) (min-y-amount uint)
  )
  (let (
    ;; Get pool data and check if pool is valid
    (pool-data (unwrap! (contract-call? pool-trait get-pool-for-withdraw) ERR_NO_POOL_DATA))
    (pool-contract (contract-of pool-trait))
    (pool-validity-check (asserts! (is-valid-pool (get pool-id pool-data) pool-contract) ERR_INVALID_POOL))
    (x-token (get x-token pool-data))
    (y-token (get y-token pool-data))

    ;; Convert bin-id to an unsigned bin-id
    (unsigned-bin-id (to-uint (+ bin-id (to-int CENTER_BIN_ID))))

    ;; Get balances at bin
    (bin-balances (try! (contract-call? pool-trait get-bin-balances unsigned-bin-id)))
    (x-balance (get x-balance bin-balances))
    (y-balance (get y-balance bin-balances))
    (bin-shares (get bin-shares bin-balances))

    ;; Assert bin shares is greater than 0
    (bin-shares-check (asserts! (> bin-shares u0) ERR_NO_BIN_SHARES))

    ;; Calculate x-amount and y-amount to transfer
    (x-amount (/ (* amount x-balance) bin-shares))
    (y-amount (/ (* amount y-balance) bin-shares))

    ;; Calculate updated bin balances
    (updated-x-balance (- x-balance x-amount))
    (updated-y-balance (- y-balance y-amount))
    (caller tx-sender)
  )
    (begin
      ;; Assert correct token traits are used
      (asserts! (is-eq (contract-of x-token-trait) x-token) ERR_INVALID_X_TOKEN)
      (asserts! (is-eq (contract-of y-token-trait) y-token) ERR_INVALID_Y_TOKEN)

      ;; Assert amount is greater than 0
      (asserts! (> amount u0) ERR_INVALID_AMOUNT)

      ;; Assert min-x-amount + min-y-amount is greater than 0
      (asserts! (> (+ min-x-amount min-y-amount) u0) ERR_INVALID_AMOUNT)

      ;; Assert x-amount + y-amount is greater than 0
      (asserts! (> (+ x-amount y-amount) u0) ERR_INVALID_AMOUNT)

      ;; Assert x-amount is greater than or equal to min-x-amount
      (asserts! (>= x-amount min-x-amount) ERR_MINIMUM_X_AMOUNT)

      ;; Assert y-amount is greater than or equal to min-y-amount
      (asserts! (>= y-amount min-y-amount) ERR_MINIMUM_Y_AMOUNT)

      ;; Transfer x-amount x tokens from pool-contract to caller
      (if (> x-amount u0)
          (try! (contract-call? pool-trait pool-transfer x-token-trait x-amount caller))
          false)

      ;; Transfer y-amount y tokens from pool-contract to caller
      (if (> y-amount u0)
          (try! (contract-call? pool-trait pool-transfer y-token-trait y-amount caller))
          false)

      ;; Update bin balances
      (try! (contract-call? pool-trait update-bin-balances-on-withdraw unsigned-bin-id updated-x-balance updated-y-balance bin-shares))

      ;; Burn LP tokens from caller
      (try! (contract-call? pool-trait pool-burn unsigned-bin-id amount caller))

      ;; Print withdraw liquidity data and return number of x and y tokens the caller received
      (print {
        action: "withdraw-liquidity",
        caller: caller,
        data: {
          pool-id: (get pool-id pool-data),
          pool-name: (get pool-name pool-data),
          pool-contract: pool-contract,
          x-token: x-token,
          y-token: y-token,
          bin-id: bin-id,
          unsigned-bin-id: unsigned-bin-id,
          amount: amount,
          x-amount: x-amount,
          y-amount: y-amount,
          min-x-amount: min-x-amount,
          min-y-amount: min-y-amount,
          updated-x-balance: updated-x-balance,
          updated-y-balance: updated-y-balance,
          updated-bin-shares: (- bin-shares amount)
        }
      })
      (ok {x-amount: x-amount, y-amount: y-amount})
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-trait | trait_reference |
| x-token-trait | trait_reference |
| y-token-trait | trait_reference |
| bin-id | int |
| amount | uint |
| min-x-amount | uint |
| min-y-amount | uint |

### move-liquidity

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L1791)

`(define-public (move-liquidity ((pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference) (from-bin-id int) (to-bin-id int) (amount uint) (min-dlp uint) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint)) (response uint uint))`

Move liquidity from one bin to another in a pool

<details>
  <summary>Source code:</summary>

```clarity
(define-public (move-liquidity
    (pool-trait <dlmm-pool-trait>)
    (x-token-trait <sip-010-trait>) (y-token-trait <sip-010-trait>)
    (from-bin-id int) (to-bin-id int) (amount uint) (min-dlp uint)
    (max-x-liquidity-fee uint) (max-y-liquidity-fee uint)
  )
  (let (
    ;; Get pool data and check if pool is valid
    (pool-data (unwrap! (contract-call? pool-trait get-pool-for-add) ERR_NO_POOL_DATA))
    (pool-contract (contract-of pool-trait))
    (pool-validity-check (asserts! (is-valid-pool (get pool-id pool-data) pool-contract) ERR_INVALID_POOL))
    (x-token (get x-token pool-data))
    (y-token (get y-token pool-data))
    (bin-step (get bin-step pool-data))
    (initial-price (get initial-price pool-data))
    (active-bin-id (get active-bin-id pool-data))

    ;; Convert bin IDs to unsigned bin IDs
    (unsigned-from-bin-id (to-uint (+ from-bin-id (to-int CENTER_BIN_ID))))
    (unsigned-to-bin-id (to-uint (+ to-bin-id (to-int CENTER_BIN_ID))))

    ;; Get balances at from-bin-id
    (bin-balances-a (try! (contract-call? pool-trait get-bin-balances unsigned-from-bin-id)))
    (x-balance-a (get x-balance bin-balances-a))
    (y-balance-a (get y-balance bin-balances-a))
    (bin-shares-a (get bin-shares bin-balances-a))

    ;; Assert bin shares for from-bin-id is greater than 0
    (bin-shares-check (asserts! (> bin-shares-a u0) ERR_NO_BIN_SHARES))

    ;; Calculate x-amount and y-amount to withdraw from from-bin-id
    (x-amount (/ (* amount x-balance-a) bin-shares-a))
    (y-amount (/ (* amount y-balance-a) bin-shares-a))

    ;; Calculate updated bin balances for from-bin-id
    (updated-x-balance-a (- x-balance-a x-amount))
    (updated-y-balance-a (- y-balance-a y-amount))

    ;; Get balances at to-bin-id
    (bin-balances-b (try! (contract-call? pool-trait get-bin-balances unsigned-to-bin-id)))
    (x-balance-b (get x-balance bin-balances-b))
    (y-balance-b (get y-balance bin-balances-b))
    (bin-shares-b (get bin-shares bin-balances-b))

    ;; Get price at to-bin-id
    (bin-price (unwrap! (get-bin-price initial-price bin-step to-bin-id) ERR_INVALID_BIN_PRICE))

    ;; Scale up y-amount and y-balance-b
    (y-amount-scaled (* y-amount PRICE_SCALE_BPS))
    (y-balance-b-scaled (* y-balance-b PRICE_SCALE_BPS))

    ;; Get current liquidity values for to-bin-id and calculate dlp without fees
    (add-liquidity-value (unwrap! (get-liquidity-value x-amount y-amount-scaled bin-price) ERR_INVALID_LIQUIDITY_VALUE))
    (bin-liquidity-value (unwrap! (get-liquidity-value x-balance-b y-balance-b-scaled bin-price) ERR_INVALID_LIQUIDITY_VALUE))
    (dlp (if (or (is-eq bin-shares-b u0) (is-eq bin-liquidity-value u0))
             (sqrti add-liquidity-value)
             (/ (* add-liquidity-value bin-shares-b) bin-liquidity-value)))

    ;; Calculate liquidity fees if adding liquidity to active bin based on ratio of bin balances
    (add-liquidity-fees (if (and (is-eq to-bin-id active-bin-id) (> dlp u0))
      (let (
        (x-liquidity-fee (+ (get x-protocol-fee pool-data) (get x-provider-fee pool-data) (get x-variable-fee pool-data)))
        (y-liquidity-fee (+ (get y-protocol-fee pool-data) (get y-provider-fee pool-data) (get y-variable-fee pool-data)))

        ;; Calculate withdrawable x-amount without fees
        (x-amount-withdrawable (/ (* dlp (+ x-balance-b x-amount)) (+ bin-shares-b dlp)))

        ;; Calculate withdrawable y-amount without fees
        (y-amount-withdrawable (/ (* dlp (+ y-balance-b y-amount)) (+ bin-shares-b dlp)))

        ;; Calculate max liquidity fee for x-amount and y-amount
        (max-x-amount-fees-liquidity (if (and (> y-amount-withdrawable y-amount) (> x-amount x-amount-withdrawable))
                                         (/ (* (- x-amount x-amount-withdrawable) x-liquidity-fee) FEE_SCALE_BPS)
                                         u0))
        (max-y-amount-fees-liquidity (if (and (> x-amount-withdrawable x-amount) (> y-amount y-amount-withdrawable))
                                         (/ (* (- y-amount y-amount-withdrawable) y-liquidity-fee) FEE_SCALE_BPS)
                                         u0))
      )
        ;; Calculate final liquidity fee for x-amount and y-amount
        {
          x-amount-fees-liquidity: (if (> x-amount max-x-amount-fees-liquidity) max-x-amount-fees-liquidity x-amount),
          y-amount-fees-liquidity: (if (> y-amount max-y-amount-fees-liquidity) max-y-amount-fees-liquidity y-amount)
        }
      )
      {
        x-amount-fees-liquidity: u0,
        y-amount-fees-liquidity: u0
      })
    )

    ;; Get x-amount-fees-liquidity and y-amount-fees-liquidity
    (x-amount-fees-liquidity (get x-amount-fees-liquidity add-liquidity-fees))
    (y-amount-fees-liquidity (get y-amount-fees-liquidity add-liquidity-fees))

    ;; Calculate final x and y amounts post fees for to-bin-id
    (x-amount-post-fees (- x-amount x-amount-fees-liquidity))
    (y-amount-post-fees (- y-amount y-amount-fees-liquidity))
    (y-amount-post-fees-scaled (* y-amount-post-fees PRICE_SCALE_BPS))

    ;; Calculate bin balances post fees for to-bin-id
    (x-balance-post-fees (+ x-balance-b x-amount-fees-liquidity))
    (y-balance-post-fees-scaled (* (+ y-balance-b y-amount-fees-liquidity) PRICE_SCALE_BPS))

    ;; Get final liquidity value for to-bin-id and calculate dlp post fees
    (add-liquidity-value-post-fees (unwrap! (get-liquidity-value x-amount-post-fees y-amount-post-fees-scaled bin-price) ERR_INVALID_LIQUIDITY_VALUE))
    (bin-liquidity-value-post-fees (unwrap! (get-liquidity-value x-balance-post-fees y-balance-post-fees-scaled bin-price) ERR_INVALID_LIQUIDITY_VALUE))
    (burn-amount (if (is-eq bin-shares-b u0) (var-get minimum-burnt-shares) u0))
    (dlp-post-fees (if (is-eq bin-shares-b u0)
      (let (
        (intended-dlp (sqrti add-liquidity-value-post-fees))
      )
        (asserts! (>= intended-dlp (var-get minimum-bin-shares)) ERR_MINIMUM_LP_AMOUNT)
        (try! (contract-call? pool-trait pool-mint unsigned-to-bin-id burn-amount BURN_ADDRESS))
        (- intended-dlp burn-amount)
      )
      (if (is-eq bin-liquidity-value-post-fees u0)
          (sqrti add-liquidity-value-post-fees)
          (/ (* add-liquidity-value-post-fees bin-shares-b) bin-liquidity-value-post-fees))))

    ;; Calculate updated bin balances for to-bin-id
    (updated-x-balance-b (+ x-balance-b x-amount))
    (updated-y-balance-b (+ y-balance-b y-amount))
    (caller tx-sender)
  )
    (begin
      ;; Assert pool-status is true and correct token traits are used
      (asserts! (is-enabled-pool (get pool-id pool-data)) ERR_POOL_DISABLED)
      (asserts! (is-eq (contract-of x-token-trait) x-token) ERR_INVALID_X_TOKEN)
      (asserts! (is-eq (contract-of y-token-trait) y-token) ERR_INVALID_Y_TOKEN)

      ;; Assert amount is greater than 0
      (asserts! (> amount u0) ERR_INVALID_AMOUNT)

      ;; Assert x-amount + y-amount is greater than 0
      (asserts! (> (+ x-amount y-amount) u0) ERR_INVALID_AMOUNT)

      ;; Assert from-bin-id is not equal to to-bin-id
      (asserts! (not (is-eq from-bin-id to-bin-id)) ERR_MATCHING_BIN_ID)

      ;; Assert correct token amounts are being added based on to-bin-id and active-bin-id
      (asserts! (or (>= to-bin-id active-bin-id) (is-eq x-amount u0)) ERR_INVALID_X_AMOUNT)
      (asserts! (or (<= to-bin-id active-bin-id) (is-eq y-amount u0)) ERR_INVALID_Y_AMOUNT)

      ;; Assert min-dlp is greater than 0 and dlp-post-fees is greater than or equal to min-dlp
      (asserts! (> min-dlp u0) ERR_INVALID_MIN_DLP_AMOUNT)
      (asserts! (>= dlp-post-fees min-dlp) ERR_MINIMUM_LP_AMOUNT)

      ;; Assert x-amount-fees-liquidity is less than or equal to max-x-liquidity-fee
      (asserts! (<= x-amount-fees-liquidity max-x-liquidity-fee) ERR_MAXIMUM_X_LIQUIDITY_FEE)

      ;; Assert y-amount-fees-liquidity is less than or equal to max-y-liquidity-fee
      (asserts! (<= y-amount-fees-liquidity max-y-liquidity-fee) ERR_MAXIMUM_Y_LIQUIDITY_FEE)

      ;; Update bin balances for from-bin-id
      (try! (contract-call? pool-trait update-bin-balances-on-withdraw unsigned-from-bin-id updated-x-balance-a updated-y-balance-a bin-shares-a))

      ;; Burn LP tokens from caller for from-bin-id
      (try! (contract-call? pool-trait pool-burn unsigned-from-bin-id amount caller))

      ;; Update bin balances for to-bin-id
      (try! (contract-call? pool-trait update-bin-balances unsigned-to-bin-id updated-x-balance-b updated-y-balance-b))

      ;; Mint LP tokens to caller for to-bin-id
      (try! (contract-call? pool-trait pool-mint unsigned-to-bin-id dlp-post-fees caller))

      ;; Print move liquidity data and return number of LP tokens the caller received
      (print {
        action: "move-liquidity",
        caller: caller,
        data: {
          pool-id: (get pool-id pool-data),
          pool-name: (get pool-name pool-data),
          pool-contract: pool-contract,
          x-token: x-token,
          y-token: y-token,
          bin-step: bin-step,
          initial-price: initial-price,
          bin-price: bin-price,
          active-bin-id: active-bin-id,
          from-bin-id: from-bin-id,
          to-bin-id: to-bin-id,
          unsigned-from-bin-id: unsigned-from-bin-id,
          unsigned-to-bin-id: unsigned-to-bin-id,
          amount: amount,
          x-amount: x-amount-post-fees,
          y-amount: y-amount-post-fees,
          x-amount-fees-liquidity: x-amount-fees-liquidity,
          y-amount-fees-liquidity: y-amount-fees-liquidity,
          burn-amount: burn-amount,
          dlp: dlp-post-fees,
          min-dlp: min-dlp,
          max-x-liquidity-fee: max-x-liquidity-fee,
          max-y-liquidity-fee: max-y-liquidity-fee,
          add-liquidity-value-post-fees: add-liquidity-value-post-fees,
          bin-liquidity-value-post-fees: bin-liquidity-value-post-fees,
          updated-x-balance-a: updated-x-balance-a,
          updated-y-balance-a: updated-y-balance-a,
          updated-bin-shares-a: (- bin-shares-a amount),
          updated-x-balance-b: updated-x-balance-b,
          updated-y-balance-b: updated-y-balance-b,
          updated-bin-shares-b: (+ bin-shares-b dlp-post-fees burn-amount)
        }
      })
      (ok dlp-post-fees)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-trait | trait_reference |
| x-token-trait | trait_reference |
| y-token-trait | trait_reference |
| from-bin-id | int |
| to-bin-id | int |
| amount | uint |
| min-dlp | uint |
| max-x-liquidity-fee | uint |
| max-y-liquidity-fee | uint |

### add-admin

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L2000)

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

    ;; Transfer 1 uSTX from caller to BURN_ADDRESS
    (try! (stx-transfer? u1 caller BURN_ADDRESS))

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

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L2022)

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

    ;; Transfer 1 uSTX from caller to BURN_ADDRESS
    (try! (stx-transfer? u1 caller BURN_ADDRESS))

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

### admin-not-removable

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L2048)

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

### verified-pool-code-hashes-not-removable

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L2053)

`(define-private (verified-pool-code-hashes-not-removable ((hash (buff 32))) bool)`

Helper function for removing a verified pool code hash

<details>
  <summary>Source code:</summary>

```clarity
(define-private (verified-pool-code-hashes-not-removable (hash (buff 32)))
  (not (is-eq hash (var-get verified-pool-code-hashes-helper)))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| hash | (buff 32) |

### fold-are-bin-factors-ascending

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L2058)

`(define-private (fold-are-bin-factors-ascending ((factor uint) (result (response uint uint))) (response uint uint))`

Helper function to validate bin-factors list is in ascending order

<details>
  <summary>Source code:</summary>

```clarity
(define-private (fold-are-bin-factors-ascending (factor uint) (result (response uint uint)))
  (if (> factor (try! result))
      (ok factor)
      ERR_UNSORTED_BIN_FACTORS_LIST)
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| factor | uint |
| result | (response uint uint) |

### create-symbol

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L2065)

`(define-private (create-symbol ((x-token-trait trait_reference) (y-token-trait trait_reference)) (optional (string-ascii 29)))`

Create pool symbol using x token and y token symbols

<details>
  <summary>Source code:</summary>

```clarity
(define-private (create-symbol (x-token-trait <sip-010-trait>) (y-token-trait <sip-010-trait>))
  (let (
    ;; Get x token and y token symbols
    (x-symbol (unwrap-panic (contract-call? x-token-trait get-symbol)))
    (y-symbol (unwrap-panic (contract-call? y-token-trait get-symbol)))

    ;; Truncate symbols if length exceeds 14
    (x-truncated 
      (if (> (len x-symbol) u14)
          (unwrap-panic (slice? x-symbol u0 u14))
          x-symbol))
    (y-truncated
      (if (> (len y-symbol) u14)
          (unwrap-panic (slice? y-symbol u0 u14))
          y-symbol))
  )
    ;; Return pool symbol with max length of 29
    (as-max-len? (concat x-truncated (concat "-" y-truncated)) u29)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| x-token-trait | trait_reference |
| y-token-trait | trait_reference |

### is-valid-pool

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L2087)

`(define-private (is-valid-pool ((id uint) (contract principal)) bool)`

Check if a pool is valid

<details>
  <summary>Source code:</summary>

```clarity
(define-private (is-valid-pool (id uint) (contract principal))
  (let (
    (pool-data (unwrap! (map-get? pools id) false))
  )
    (is-eq contract (get pool-contract pool-data))
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| id | uint |
| contract | principal |

### is-enabled-pool

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L2096)

`(define-private (is-enabled-pool ((id uint)) bool)`

Check if a pool is enabled

<details>
  <summary>Source code:</summary>

```clarity
(define-private (is-enabled-pool (id uint))
  (let (
    (pool-data (unwrap! (map-get? pools id) false))
  )
    (is-eq (get status pool-data) true)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| id | uint |

## Maps

### bin-factors



```clarity
(define-map bin-factors uint (list 1001 uint))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L105)

### pools

Define pools map

```clarity
(define-map pools uint {
  id: uint,
  name: (string-ascii 32),
  symbol: (string-ascii 32),
  pool-contract: principal,
  status: bool
})
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L121)

### allowed-token-direction

Define allowed-token-direction map

```clarity
(define-map allowed-token-direction {x-token: principal, y-token: principal} bool)
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L130)

### unclaimed-protocol-fees

Define unclaimed-protocol-fees map

```clarity
(define-map unclaimed-protocol-fees uint {x-fee: uint, y-fee: uint})
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L133)

### swap-fee-exemptions

Define swap-fee-exemptions map

```clarity
(define-map swap-fee-exemptions {address: principal, id: uint} bool)
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L136)

## Variables

### core-migration-address

principal

Core migration address and execution time

```clarity
(define-data-var core-migration-address principal current-contract)
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L90)

### core-migration-execution-time

uint



```clarity
(define-data-var core-migration-execution-time uint u0)
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L91)

### core-migration-cooldown

uint

Core migration cooldown in seconds (2 weeks by default)

```clarity
(define-data-var core-migration-cooldown uint u1209600)
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L94)

### admins

(list 5 principal)

Admins list and helper var used to remove admins

```clarity
(define-data-var admins (list 5 principal) (list tx-sender))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L97)

### admin-helper

principal



```clarity
(define-data-var admin-helper principal tx-sender)
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L98)

### last-pool-id

uint

ID of last created pool

```clarity
(define-data-var last-pool-id uint u0)
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L101)

### bin-steps

(list 1000 uint)

Allowed bin steps and factors

```clarity
(define-data-var bin-steps (list 1000 uint) (list ))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L104)

### minimum-bin-shares

uint

Min shares required to mint into the active bin when creating a pool

```clarity
(define-data-var minimum-bin-shares uint u10000)
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L108)

### minimum-burnt-shares

uint

Min shares required to burn from the active bin when creating a pool

```clarity
(define-data-var minimum-burnt-shares uint u1000)
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L111)

### public-pool-creation

bool

Data var used to enable or disable pool creation by anyone

```clarity
(define-data-var public-pool-creation bool false)
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L114)

### verified-pool-code-hashes

(list 10000 (buff 32))

List of verified pool code hashes and helper var used to remove hashes

```clarity
(define-data-var verified-pool-code-hashes (list 10000 (buff 32)) (list ))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L117)

### verified-pool-code-hashes-helper

(buff 32)



```clarity
(define-data-var verified-pool-code-hashes-helper (buff 32) 0x)
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L118)

## Constants

### ERR_NOT_AUTHORIZED



Error constants

```clarity
(define-constant ERR_NOT_AUTHORIZED (err u1001))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L8)

### ERR_INVALID_AMOUNT





```clarity
(define-constant ERR_INVALID_AMOUNT (err u1002))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L9)

### ERR_INVALID_PRINCIPAL





```clarity
(define-constant ERR_INVALID_PRINCIPAL (err u1003))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L10)

### ERR_ALREADY_ADMIN





```clarity
(define-constant ERR_ALREADY_ADMIN (err u1004))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L11)

### ERR_ADMIN_LIMIT_REACHED





```clarity
(define-constant ERR_ADMIN_LIMIT_REACHED (err u1005))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L12)

### ERR_ADMIN_NOT_IN_LIST





```clarity
(define-constant ERR_ADMIN_NOT_IN_LIST (err u1006))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L13)

### ERR_CANNOT_REMOVE_CONTRACT_DEPLOYER





```clarity
(define-constant ERR_CANNOT_REMOVE_CONTRACT_DEPLOYER (err u1007))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L14)

### ERR_NO_POOL_DATA





```clarity
(define-constant ERR_NO_POOL_DATA (err u1008))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L15)

### ERR_POOL_NOT_CREATED





```clarity
(define-constant ERR_POOL_NOT_CREATED (err u1009))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L16)

### ERR_POOL_DISABLED





```clarity
(define-constant ERR_POOL_DISABLED (err u1010))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L17)

### ERR_POOL_ALREADY_CREATED





```clarity
(define-constant ERR_POOL_ALREADY_CREATED (err u1011))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L18)

### ERR_INVALID_POOL





```clarity
(define-constant ERR_INVALID_POOL (err u1012))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L19)

### ERR_INVALID_POOL_URI





```clarity
(define-constant ERR_INVALID_POOL_URI (err u1013))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L20)

### ERR_INVALID_POOL_SYMBOL





```clarity
(define-constant ERR_INVALID_POOL_SYMBOL (err u1014))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L21)

### ERR_INVALID_POOL_NAME





```clarity
(define-constant ERR_INVALID_POOL_NAME (err u1015))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L22)

### ERR_INVALID_TOKEN_DIRECTION





```clarity
(define-constant ERR_INVALID_TOKEN_DIRECTION (err u1016))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L23)

### ERR_MATCHING_TOKEN_CONTRACTS





```clarity
(define-constant ERR_MATCHING_TOKEN_CONTRACTS (err u1017))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L24)

### ERR_INVALID_X_TOKEN





```clarity
(define-constant ERR_INVALID_X_TOKEN (err u1018))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L25)

### ERR_INVALID_Y_TOKEN





```clarity
(define-constant ERR_INVALID_Y_TOKEN (err u1019))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L26)

### ERR_INVALID_X_AMOUNT





```clarity
(define-constant ERR_INVALID_X_AMOUNT (err u1020))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L27)

### ERR_INVALID_Y_AMOUNT





```clarity
(define-constant ERR_INVALID_Y_AMOUNT (err u1021))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L28)

### ERR_MINIMUM_X_AMOUNT





```clarity
(define-constant ERR_MINIMUM_X_AMOUNT (err u1022))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L29)

### ERR_MINIMUM_Y_AMOUNT





```clarity
(define-constant ERR_MINIMUM_Y_AMOUNT (err u1023))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L30)

### ERR_MINIMUM_LP_AMOUNT





```clarity
(define-constant ERR_MINIMUM_LP_AMOUNT (err u1024))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L31)

### ERR_MAXIMUM_X_AMOUNT





```clarity
(define-constant ERR_MAXIMUM_X_AMOUNT (err u1025))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L32)

### ERR_MAXIMUM_Y_AMOUNT





```clarity
(define-constant ERR_MAXIMUM_Y_AMOUNT (err u1026))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L33)

### ERR_INVALID_MIN_DLP_AMOUNT





```clarity
(define-constant ERR_INVALID_MIN_DLP_AMOUNT (err u1027))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L34)

### ERR_INVALID_LIQUIDITY_VALUE





```clarity
(define-constant ERR_INVALID_LIQUIDITY_VALUE (err u1028))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L35)

### ERR_INVALID_FEE





```clarity
(define-constant ERR_INVALID_FEE (err u1029))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L36)

### ERR_MAXIMUM_X_LIQUIDITY_FEE





```clarity
(define-constant ERR_MAXIMUM_X_LIQUIDITY_FEE (err u1030))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L37)

### ERR_MAXIMUM_Y_LIQUIDITY_FEE





```clarity
(define-constant ERR_MAXIMUM_Y_LIQUIDITY_FEE (err u1031))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L38)

### ERR_NO_UNCLAIMED_PROTOCOL_FEES_DATA





```clarity
(define-constant ERR_NO_UNCLAIMED_PROTOCOL_FEES_DATA (err u1032))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L39)

### ERR_MINIMUM_BURN_AMOUNT





```clarity
(define-constant ERR_MINIMUM_BURN_AMOUNT (err u1033))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L40)

### ERR_INVALID_MIN_BURNT_SHARES





```clarity
(define-constant ERR_INVALID_MIN_BURNT_SHARES (err u1034))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L41)

### ERR_INVALID_BIN_STEP





```clarity
(define-constant ERR_INVALID_BIN_STEP (err u1035))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L42)

### ERR_ALREADY_BIN_STEP





```clarity
(define-constant ERR_ALREADY_BIN_STEP (err u1036))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L43)

### ERR_BIN_STEP_LIMIT_REACHED





```clarity
(define-constant ERR_BIN_STEP_LIMIT_REACHED (err u1037))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L44)

### ERR_NO_BIN_FACTORS





```clarity
(define-constant ERR_NO_BIN_FACTORS (err u1038))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L45)

### ERR_INVALID_BIN_FACTOR





```clarity
(define-constant ERR_INVALID_BIN_FACTOR (err u1039))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L46)

### ERR_INVALID_FIRST_BIN_FACTOR





```clarity
(define-constant ERR_INVALID_FIRST_BIN_FACTOR (err u1040))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L47)

### ERR_INVALID_CENTER_BIN_FACTOR





```clarity
(define-constant ERR_INVALID_CENTER_BIN_FACTOR (err u1041))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L48)

### ERR_UNSORTED_BIN_FACTORS_LIST





```clarity
(define-constant ERR_UNSORTED_BIN_FACTORS_LIST (err u1042))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L49)

### ERR_INVALID_BIN_FACTORS_LENGTH





```clarity
(define-constant ERR_INVALID_BIN_FACTORS_LENGTH (err u1043))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L50)

### ERR_INVALID_INITIAL_PRICE





```clarity
(define-constant ERR_INVALID_INITIAL_PRICE (err u1044))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L51)

### ERR_INVALID_BIN_PRICE





```clarity
(define-constant ERR_INVALID_BIN_PRICE (err u1045))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L52)

### ERR_MATCHING_BIN_ID





```clarity
(define-constant ERR_MATCHING_BIN_ID (err u1046))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L53)

### ERR_NOT_ACTIVE_BIN





```clarity
(define-constant ERR_NOT_ACTIVE_BIN (err u1047))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L54)

### ERR_NO_BIN_SHARES





```clarity
(define-constant ERR_NO_BIN_SHARES (err u1048))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L55)

### ERR_INVALID_POOL_CODE_HASH





```clarity
(define-constant ERR_INVALID_POOL_CODE_HASH (err u1049))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L56)

### ERR_INVALID_VERIFIED_POOL_CODE_HASH





```clarity
(define-constant ERR_INVALID_VERIFIED_POOL_CODE_HASH (err u1050))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L57)

### ERR_ALREADY_VERIFIED_POOL_CODE_HASH





```clarity
(define-constant ERR_ALREADY_VERIFIED_POOL_CODE_HASH (err u1051))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L58)

### ERR_VERIFIED_POOL_CODE_HASH_LIMIT_REACHED





```clarity
(define-constant ERR_VERIFIED_POOL_CODE_HASH_LIMIT_REACHED (err u1052))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L59)

### ERR_VERIFIED_POOL_CODE_HASH_NOT_IN_LIST





```clarity
(define-constant ERR_VERIFIED_POOL_CODE_HASH_NOT_IN_LIST (err u1053))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L60)

### ERR_VARIABLE_FEES_COOLDOWN





```clarity
(define-constant ERR_VARIABLE_FEES_COOLDOWN (err u1054))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L61)

### ERR_VARIABLE_FEES_MANAGER_FROZEN





```clarity
(define-constant ERR_VARIABLE_FEES_MANAGER_FROZEN (err u1055))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L62)

### ERR_INVALID_DYNAMIC_CONFIG





```clarity
(define-constant ERR_INVALID_DYNAMIC_CONFIG (err u1056))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L63)

### ERR_INVALID_CORE_MIGRATION_COOLDOWN





```clarity
(define-constant ERR_INVALID_CORE_MIGRATION_COOLDOWN (err u1057))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L64)

### ERR_CORE_MIGRATION_COOLDOWN





```clarity
(define-constant ERR_CORE_MIGRATION_COOLDOWN (err u1058))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L65)

### ERR_CORE_ADDRESS_ALREADY_MIGRATED





```clarity
(define-constant ERR_CORE_ADDRESS_ALREADY_MIGRATED (err u1059))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L66)

### CONTRACT_DEPLOYER



Contract deployer address

```clarity
(define-constant CONTRACT_DEPLOYER tx-sender)
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L69)

### BURN_ADDRESS



Address used when burning LP tokens

```clarity
(define-constant BURN_ADDRESS (unwrap-panic (principal-construct? (if is-in-mainnet 0x16 0x1a) 0x0000000000000000000000000000000000000000)))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L72)

### NUM_OF_BINS



Number of bins per pool and center bin ID as unsigned ints

```clarity
(define-constant NUM_OF_BINS u1001)
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L75)

### CENTER_BIN_ID





```clarity
(define-constant CENTER_BIN_ID (/ NUM_OF_BINS u2))
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L76)

### MIN_BIN_ID



Min and max bin IDs as signed ints

```clarity
(define-constant MIN_BIN_ID -500)
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L79)

### MAX_BIN_ID





```clarity
(define-constant MAX_BIN_ID 500)
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L80)

### FEE_SCALE_BPS



Max BPS

```clarity
(define-constant FEE_SCALE_BPS u10000)
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L83)

### PRICE_SCALE_BPS





```clarity
(define-constant PRICE_SCALE_BPS u100000000)
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L84)

### MIN_CORE_MIGRATION_COOLDOWN



Min core migration cooldown in seconds (1 week min)

```clarity
(define-constant MIN_CORE_MIGRATION_COOLDOWN u604800)
```

[View in file](../clarity/contracts/dlmm-core-v-1-1.clar#L87)
  