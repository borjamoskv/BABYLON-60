
# dlmm-pool-sbtc-usdc-v-1-1

[`dlmm-pool-sbtc-usdc-v-1-1.clar`](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar)

dlmm-pool-sbtc-usdc-v-1-1

**Public functions:**

- [`set-pool-uri`](#set-pool-uri)
- [`set-core-address`](#set-core-address)
- [`set-variable-fees-manager`](#set-variable-fees-manager)
- [`set-fee-address`](#set-fee-address)
- [`set-active-bin-id`](#set-active-bin-id)
- [`set-x-fees`](#set-x-fees)
- [`set-y-fees`](#set-y-fees)
- [`set-variable-fees`](#set-variable-fees)
- [`set-variable-fees-cooldown`](#set-variable-fees-cooldown)
- [`set-freeze-variable-fees-manager`](#set-freeze-variable-fees-manager)
- [`set-dynamic-config`](#set-dynamic-config)
- [`update-bin-balances`](#update-bin-balances)
- [`update-bin-balances-on-withdraw`](#update-bin-balances-on-withdraw)
- [`transfer`](#transfer)
- [`transfer-memo`](#transfer-memo)
- [`transfer-many`](#transfer-many)
- [`transfer-many-memo`](#transfer-many-memo)
- [`pool-transfer`](#pool-transfer)
- [`pool-mint`](#pool-mint)
- [`pool-burn`](#pool-burn)
- [`create-pool`](#create-pool)

**Read-only functions:**

- [`get-name`](#get-name)
- [`get-symbol`](#get-symbol)
- [`get-decimals`](#get-decimals)
- [`get-token-uri`](#get-token-uri)
- [`get-total-supply`](#get-total-supply)
- [`get-overall-supply`](#get-overall-supply)
- [`get-balance`](#get-balance)
- [`get-overall-balance`](#get-overall-balance)
- [`get-pool`](#get-pool)
- [`get-pool-for-swap`](#get-pool-for-swap)
- [`get-pool-for-add`](#get-pool-for-add)
- [`get-pool-for-withdraw`](#get-pool-for-withdraw)
- [`get-variable-fees-data`](#get-variable-fees-data)
- [`get-active-bin-id`](#get-active-bin-id)
- [`get-bin-balances`](#get-bin-balances)
- [`get-user-bins`](#get-user-bins)

**Private functions:**

- [`fold-transfer-many`](#fold-transfer-many)
- [`fold-transfer-many-memo`](#fold-transfer-many-memo)
- [`get-balance-or-default`](#get-balance-or-default)
- [`update-user-balance`](#update-user-balance)
- [`tag-pool-token-id`](#tag-pool-token-id)

**Maps**

- [`balances-at-bin`](#balances-at-bin)
- [`user-balance-at-bin`](#user-balance-at-bin)
- [`user-bins`](#user-bins)

**Variables**

- [`pool-info`](#pool-info)
- [`pool-addresses`](#pool-addresses)
- [`bin-step`](#bin-step)
- [`initial-price`](#initial-price)
- [`active-bin-id`](#active-bin-id)
- [`pool-fees`](#pool-fees)
- [`bin-change-count`](#bin-change-count)
- [`last-variable-fees-update`](#last-variable-fees-update)
- [`variable-fees-cooldown`](#variable-fees-cooldown)
- [`freeze-variable-fees-manager`](#freeze-variable-fees-manager)
- [`dynamic-config`](#dynamic-config)

**Constants**

- [`ERR_INSUFFICIENT_BALANCE_SIP_013`](#err_insufficient_balance_sip_013)
- [`ERR_MATCHING_PRINCIPALS_SIP_013`](#err_matching_principals_sip_013)
- [`ERR_INVALID_AMOUNT_SIP_013`](#err_invalid_amount_sip_013)
- [`ERR_NOT_AUTHORIZED_SIP_013`](#err_not_authorized_sip_013)
- [`ERR_NOT_AUTHORIZED`](#err_not_authorized)
- [`ERR_INVALID_AMOUNT`](#err_invalid_amount)
- [`ERR_INVALID_PRINCIPAL`](#err_invalid_principal)
- [`ERR_NOT_POOL_CONTRACT_DEPLOYER`](#err_not_pool_contract_deployer)
- [`ERR_MAX_NUMBER_OF_BINS`](#err_max_number_of_bins)
- [`CONTRACT_DEPLOYER`](#contract_deployer)


## Functions

### get-name

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L96)

`(define-read-only (get-name () (response (string-ascii 32) none))`

Get token name

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-name)
  (ok (get pool-name (var-get pool-info)))
)
```
</details>




### get-symbol

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L101)

`(define-read-only (get-symbol () (response (string-ascii 32) none))`

Get token symbol

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-symbol)
  (ok (get pool-symbol (var-get pool-info)))
)
```
</details>




### get-decimals

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L106)

`(define-read-only (get-decimals ((token-id uint)) (response uint none))`

Get token decimals

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-decimals (token-id uint))
  (ok u6)
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| token-id | uint |

### get-token-uri

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L111)

`(define-read-only (get-token-uri ((token-id uint)) (response (optional (string-ascii 256)) none))`

SIP 013 function to get token uri

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-token-uri (token-id uint))
  (ok (some (get pool-uri (var-get pool-info))))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| token-id | uint |

### get-total-supply

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L116)

`(define-read-only (get-total-supply ((token-id uint)) (response uint none))`

SIP 013 function to get total token supply by ID

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-total-supply (token-id uint))
  (ok (default-to u0 (get bin-shares (map-get? balances-at-bin token-id))))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| token-id | uint |

### get-overall-supply

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L121)

`(define-read-only (get-overall-supply () (response uint none))`

SIP 013 function to get overall token supply

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-overall-supply)
  (ok (ft-get-supply pool-token))
)
```
</details>




### get-balance

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L126)

`(define-read-only (get-balance ((token-id uint) (user principal)) (response uint none))`

SIP 013 function to get token balance for an user by ID

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-balance (token-id uint) (user principal))
  (ok (get-balance-or-default token-id user))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| token-id | uint |
| user | principal |

### get-overall-balance

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L131)

`(define-read-only (get-overall-balance ((user principal)) (response uint none))`

SIP 013 function to get overall token balance for an user

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-overall-balance (user principal))
  (ok (ft-get-balance pool-token user))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| user | principal |

### get-pool

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L136)

`(define-read-only (get-pool () (response (tuple (active-bin-id int) (bin-change-count uint) (bin-step uint) (core-address principal) (creation-height uint) (dynamic-config (buff 4096)) (fee-address principal) (freeze-variable-fees-manager bool) (initial-price uint) (last-variable-fees-update uint) (pool-created bool) (pool-id uint) (pool-name (string-ascii 32)) (pool-symbol (string-ascii 32)) (pool-token principal) (pool-uri (string-ascii 256)) (variable-fees-cooldown uint) (variable-fees-manager principal) (x-protocol-fee uint) (x-provider-fee uint) (x-token principal) (x-variable-fee uint) (y-protocol-fee uint) (y-provider-fee uint) (y-token principal) (y-variable-fee uint)) none))`

Get all pool data

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-pool)
  (let (
    (current-pool-info (var-get pool-info))
    (current-pool-fees (var-get pool-fees))
    (current-pool-addresses (var-get pool-addresses))
  )
    (ok {
      pool-id: (get pool-id current-pool-info),
      pool-name: (get pool-name current-pool-info),
      pool-symbol: (get pool-symbol current-pool-info),
      pool-uri: (get pool-uri current-pool-info),
      pool-created: (get pool-created current-pool-info),
      creation-height: (get creation-height current-pool-info),
      core-address: (get core-address current-pool-addresses),
      variable-fees-manager: (get variable-fees-manager current-pool-addresses),
      fee-address: (get fee-address current-pool-addresses),
      x-token: (get x-token current-pool-addresses),
      y-token: (get y-token current-pool-addresses),
      pool-token: current-contract,
      bin-step: (var-get bin-step),
      initial-price: (var-get initial-price),
      active-bin-id: (var-get active-bin-id),
      x-protocol-fee: (get x-protocol-fee current-pool-fees),
      x-provider-fee: (get x-provider-fee current-pool-fees),
      x-variable-fee: (get x-variable-fee current-pool-fees),
      y-protocol-fee: (get y-protocol-fee current-pool-fees),
      y-provider-fee: (get y-provider-fee current-pool-fees),
      y-variable-fee: (get y-variable-fee current-pool-fees),
      bin-change-count: (var-get bin-change-count),
      last-variable-fees-update: (var-get last-variable-fees-update),
      variable-fees-cooldown: (var-get variable-fees-cooldown),
      freeze-variable-fees-manager: (var-get freeze-variable-fees-manager),
      dynamic-config: (var-get dynamic-config)
    })
  )
)
```
</details>




### get-pool-for-swap

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L174)

`(define-read-only (get-pool-for-swap ((is-x-for-y bool)) (response (tuple (active-bin-id int) (bin-step uint) (fee-address principal) (initial-price uint) (pool-id uint) (pool-name (string-ascii 32)) (protocol-fee uint) (provider-fee uint) (variable-fee uint) (x-token principal) (y-token principal)) none))`

Get all pool data for swapping

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-pool-for-swap (is-x-for-y bool))
  (let (
    (current-pool-info (var-get pool-info))
    (current-pool-addresses (var-get pool-addresses))
    (current-pool-fees (var-get pool-fees))
  )
    (ok {
      pool-id: (get pool-id current-pool-info),
      pool-name: (get pool-name current-pool-info),
      fee-address: (get fee-address current-pool-addresses),
      x-token: (get x-token current-pool-addresses),
      y-token: (get y-token current-pool-addresses),
      bin-step: (var-get bin-step),
      initial-price: (var-get initial-price),
      active-bin-id: (var-get active-bin-id),
      protocol-fee: (if is-x-for-y (get x-protocol-fee current-pool-fees) (get y-protocol-fee current-pool-fees)),
      provider-fee: (if is-x-for-y (get x-provider-fee current-pool-fees) (get y-provider-fee current-pool-fees)),
      variable-fee: (if is-x-for-y (get x-variable-fee current-pool-fees) (get y-variable-fee current-pool-fees))
    })
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| is-x-for-y | bool |

### get-pool-for-add

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L197)

`(define-read-only (get-pool-for-add () (response (tuple (active-bin-id int) (bin-step uint) (initial-price uint) (pool-id uint) (pool-name (string-ascii 32)) (x-protocol-fee uint) (x-provider-fee uint) (x-token principal) (x-variable-fee uint) (y-protocol-fee uint) (y-provider-fee uint) (y-token principal) (y-variable-fee uint)) none))`

Get all pool data for adding liquidity

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-pool-for-add)
  (let (
    (current-pool-info (var-get pool-info))
    (current-pool-addresses (var-get pool-addresses))
    (current-pool-fees (var-get pool-fees))
  )
    (ok {
      pool-id: (get pool-id current-pool-info),
      pool-name: (get pool-name current-pool-info),
      x-token: (get x-token current-pool-addresses),
      y-token: (get y-token current-pool-addresses),
      bin-step: (var-get bin-step),
      initial-price: (var-get initial-price),
      active-bin-id: (var-get active-bin-id),
      x-protocol-fee: (get x-protocol-fee current-pool-fees),
      x-provider-fee: (get x-provider-fee current-pool-fees),
      x-variable-fee: (get x-variable-fee current-pool-fees),
      y-protocol-fee: (get y-protocol-fee current-pool-fees),
      y-provider-fee: (get y-provider-fee current-pool-fees),
      y-variable-fee: (get y-variable-fee current-pool-fees)
    })
  )
)
```
</details>




### get-pool-for-withdraw

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L222)

`(define-read-only (get-pool-for-withdraw () (response (tuple (pool-id uint) (pool-name (string-ascii 32)) (x-token principal) (y-token principal)) none))`

Get all pool data for withdrawing liquidity

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-pool-for-withdraw)
  (let (
      (current-pool-info (var-get pool-info))
      (current-pool-addresses (var-get pool-addresses))
    )
    (ok {
      pool-id: (get pool-id current-pool-info),
      pool-name: (get pool-name current-pool-info),
      x-token: (get x-token current-pool-addresses),
      y-token: (get y-token current-pool-addresses)
    })
  )
)
```
</details>




### get-variable-fees-data

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L237)

`(define-read-only (get-variable-fees-data () (response (tuple (bin-change-count uint) (dynamic-config (buff 4096)) (freeze-variable-fees-manager bool) (last-variable-fees-update uint) (variable-fees-cooldown uint) (variable-fees-manager principal) (x-variable-fee uint) (y-variable-fee uint)) none))`

Get all pool data for variable fees

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-variable-fees-data)
  (let (
    (current-pool-fees (var-get pool-fees))
  )
    (ok {
      variable-fees-manager: (get variable-fees-manager (var-get pool-addresses)),
      x-variable-fee: (get x-variable-fee current-pool-fees),
      y-variable-fee: (get y-variable-fee current-pool-fees),
      bin-change-count: (var-get bin-change-count),
      last-variable-fees-update: (var-get last-variable-fees-update),
      variable-fees-cooldown: (var-get variable-fees-cooldown),
      freeze-variable-fees-manager: (var-get freeze-variable-fees-manager),
      dynamic-config: (var-get dynamic-config),
    })
  )
)
```
</details>




### get-active-bin-id

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L255)

`(define-read-only (get-active-bin-id () (response int none))`

Get active bin ID

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-active-bin-id)
  (ok (var-get active-bin-id))
)
```
</details>




### get-bin-balances

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L260)

`(define-read-only (get-bin-balances ((id uint)) (response (tuple (bin-shares uint) (x-balance uint) (y-balance uint)) none))`

Get balance data at a bin

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-bin-balances (id uint))
  (ok (default-to {x-balance: u0, y-balance: u0, bin-shares: u0} (map-get? balances-at-bin id)))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| id | uint |

### get-user-bins

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L265)

`(define-read-only (get-user-bins ((user principal)) (response (list 1001 uint) none))`

Get a list of bins an user has a position in

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-user-bins (user principal))
  (ok (default-to (list ) (map-get? user-bins user)))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| user | principal |

### set-pool-uri

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L270)

`(define-public (set-pool-uri ((uri (string-ascii 256))) (response bool uint))`

Set pool uri via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-pool-uri (uri (string-ascii 256)))
  (let (
    (caller contract-caller)
  )
    (begin
      ;; Assert that caller is core address before setting var
      (asserts! (is-eq caller (get core-address (var-get pool-addresses))) ERR_NOT_AUTHORIZED)
      (var-set pool-info (merge (var-get pool-info) {
        pool-uri: uri
      }))
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| uri | (string-ascii 256) |

### set-core-address

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L286)

`(define-public (set-core-address ((address principal)) (response bool uint))`

Set core address via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-core-address (address principal))
  (let (
    (current-pool-addresses (var-get pool-addresses))
    (caller contract-caller)
  )
    (begin
      ;; Assert that caller is core address before setting var
      (asserts! (is-eq caller (get core-address current-pool-addresses)) ERR_NOT_AUTHORIZED)
      (var-set pool-addresses (merge current-pool-addresses {
        core-address: address
      }))
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

### set-variable-fees-manager

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L303)

`(define-public (set-variable-fees-manager ((manager principal)) (response bool uint))`

Set variable fees manager via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-variable-fees-manager (manager principal))
  (let (
    (current-pool-addresses (var-get pool-addresses))
    (caller contract-caller)
  )
    (begin
      ;; Assert that caller is core address before setting var
      (asserts! (is-eq caller (get core-address current-pool-addresses)) ERR_NOT_AUTHORIZED)
      (var-set pool-addresses (merge current-pool-addresses {
        variable-fees-manager: manager
      }))
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| manager | principal |

### set-fee-address

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L320)

`(define-public (set-fee-address ((address principal)) (response bool uint))`

Set fee address via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-fee-address (address principal))
  (let (
    (current-pool-addresses (var-get pool-addresses))
    (caller contract-caller)
  )
    (begin
      ;; Assert that caller is core address before setting var
      (asserts! (is-eq caller (get core-address current-pool-addresses)) ERR_NOT_AUTHORIZED)
      (var-set pool-addresses (merge current-pool-addresses {
        fee-address: address
      }))
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

### set-active-bin-id

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L337)

`(define-public (set-active-bin-id ((id int)) (response bool uint))`

Set active bin ID via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-active-bin-id (id int))
  (let (
    (caller contract-caller)
  )
    (begin
      ;; Assert that caller is core address before setting vars
      (asserts! (is-eq caller (get core-address (var-get pool-addresses))) ERR_NOT_AUTHORIZED)
      (var-set active-bin-id id)
      (var-set bin-change-count (+ (var-get bin-change-count) u1))
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| id | int |

### set-x-fees

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L352)

`(define-public (set-x-fees ((protocol-fee uint) (provider-fee uint)) (response bool uint))`

Set x fees via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-x-fees (protocol-fee uint) (provider-fee uint))
  (let (
    (caller contract-caller)
  )
    (begin
      ;; Assert that caller is core address before setting vars
      (asserts! (is-eq caller (get core-address (var-get pool-addresses))) ERR_NOT_AUTHORIZED)
      (var-set pool-fees (merge (var-get pool-fees) {
        x-protocol-fee: protocol-fee,
        x-provider-fee: provider-fee
      }))
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| protocol-fee | uint |
| provider-fee | uint |

### set-y-fees

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L369)

`(define-public (set-y-fees ((protocol-fee uint) (provider-fee uint)) (response bool uint))`

Set y fees via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-y-fees (protocol-fee uint) (provider-fee uint))
  (let (
    (caller contract-caller)
  )
    (begin
      ;; Assert that caller is core address before setting vars
      (asserts! (is-eq caller (get core-address (var-get pool-addresses))) ERR_NOT_AUTHORIZED)
      (var-set pool-fees (merge (var-get pool-fees) {
        y-protocol-fee: protocol-fee,
        y-provider-fee: provider-fee
      }))
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| protocol-fee | uint |
| provider-fee | uint |

### set-variable-fees

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L386)

`(define-public (set-variable-fees ((x-fee uint) (y-fee uint)) (response bool uint))`

Set variable fees via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-variable-fees (x-fee uint) (y-fee uint))
  (let (
    (caller contract-caller)
  )
    (begin
      ;; Assert that caller is core address before setting vars
      (asserts! (is-eq caller (get core-address (var-get pool-addresses))) ERR_NOT_AUTHORIZED)
      (var-set pool-fees (merge (var-get pool-fees) {
        x-variable-fee: x-fee,
        y-variable-fee: y-fee
      }))
      (var-set bin-change-count u0)
      (var-set last-variable-fees-update stacks-block-height)
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| x-fee | uint |
| y-fee | uint |

### set-variable-fees-cooldown

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L405)

`(define-public (set-variable-fees-cooldown ((cooldown uint)) (response bool uint))`

Set variable fees cooldown via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-variable-fees-cooldown (cooldown uint))
  (let (
    (caller contract-caller)
  )
    (begin
      ;; Assert that caller is core address before setting var
      (asserts! (is-eq caller (get core-address (var-get pool-addresses))) ERR_NOT_AUTHORIZED)
      (var-set variable-fees-cooldown cooldown)
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

### set-freeze-variable-fees-manager

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L419)

`(define-public (set-freeze-variable-fees-manager () (response bool uint))`

Set freeze variable fees manager via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-freeze-variable-fees-manager)
  (let (
    (caller contract-caller)
  )
    (begin
      ;; Assert that caller is core address before setting var
      (asserts! (is-eq caller (get core-address (var-get pool-addresses))) ERR_NOT_AUTHORIZED)
      (var-set freeze-variable-fees-manager true)
      (ok true)
    )
  )
)
```
</details>




### set-dynamic-config

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L433)

`(define-public (set-dynamic-config ((config (buff 4096))) (response bool uint))`

Set dynamic config via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-dynamic-config (config (buff 4096)))
  (let (
    (caller contract-caller)
  )
    (begin
      ;; Assert that caller is core address before setting var
      (asserts! (is-eq caller (get core-address (var-get pool-addresses))) ERR_NOT_AUTHORIZED)
      (var-set dynamic-config config)
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| config | (buff 4096) |

### update-bin-balances

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L447)

`(define-public (update-bin-balances ((bin-id uint) (x-balance uint) (y-balance uint)) (response bool uint))`

Update bin balances via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-public (update-bin-balances (bin-id uint) (x-balance uint) (y-balance uint))
  (let (
    (caller contract-caller)
  )
    (begin
      ;; Assert that caller is core address before setting vars
      (asserts! (is-eq caller (get core-address (var-get pool-addresses))) ERR_NOT_AUTHORIZED)
      (map-set balances-at-bin bin-id (merge (unwrap-panic (get-bin-balances bin-id)) {x-balance: x-balance, y-balance: y-balance}))

      ;; Print function data and return true
      (print {action: "update-bin-balances", data: {bin-id: bin-id, x-balance: x-balance, y-balance: y-balance}})
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-id | uint |
| x-balance | uint |
| y-balance | uint |

### update-bin-balances-on-withdraw

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L464)

`(define-public (update-bin-balances-on-withdraw ((bin-id uint) (x-balance uint) (y-balance uint) (bin-shares uint)) (response bool uint))`

Update bin balances when withdrawing liquidity via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-public (update-bin-balances-on-withdraw (bin-id uint) (x-balance uint) (y-balance uint) (bin-shares uint))
  (let (
    (caller contract-caller)
  )
    (begin
      ;; Assert that caller is core address before setting vars
      (asserts! (is-eq caller (get core-address (var-get pool-addresses))) ERR_NOT_AUTHORIZED)
      (map-set balances-at-bin bin-id {x-balance: x-balance, y-balance: y-balance, bin-shares: bin-shares})

      ;; Print function data and return true
      (print {action: "update-bin-balances-on-withdraw", data: {bin-id: bin-id, x-balance: x-balance, y-balance: y-balance, bin-shares: bin-shares}})
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-id | uint |
| x-balance | uint |
| y-balance | uint |
| bin-shares | uint |

### transfer

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L481)

`(define-public (transfer ((token-id uint) (amount uint) (sender principal) (recipient principal)) (response bool uint))`

SIP 013 transfer function that transfers pool token

<details>
  <summary>Source code:</summary>

```clarity
(define-public (transfer (token-id uint) (amount uint) (sender principal) (recipient principal))
	(let (
		(sender-balance (get-balance-or-default token-id sender))
    (caller tx-sender)
	)
    (begin
      ;; Assert that caller is sender and sender is not recipient
      (asserts! (or (is-eq caller sender) (is-eq contract-caller sender)) ERR_NOT_AUTHORIZED_SIP_013)
      (asserts! (not (is-eq sender recipient)) ERR_MATCHING_PRINCIPALS_SIP_013)

      ;; Assert that addresses are standard principals and amount is valid
      (asserts! (is-standard sender) ERR_INVALID_PRINCIPAL)
      (asserts! (is-standard recipient) ERR_INVALID_PRINCIPAL)
      (asserts! (> amount u0) ERR_INVALID_AMOUNT_SIP_013)
      (asserts! (<= amount sender-balance) ERR_INSUFFICIENT_BALANCE_SIP_013)

      ;; Try to transfer pool token
      (try! (ft-transfer? pool-token amount sender recipient))

      ;; Try to tag pool token and update balances
      (try! (tag-pool-token-id {token-id: token-id, owner: sender}))
      (try! (tag-pool-token-id {token-id: token-id, owner: recipient}))
      (try! (update-user-balance token-id sender (- sender-balance amount)))
      (try! (update-user-balance token-id recipient (+ (get-balance-or-default token-id recipient) amount)))

      ;; Print SIP 013 data, function data, and return true
      (print {type: "sft_transfer", token-id: token-id, amount: amount, sender: sender, recipient: recipient})
      (print {action: "transfer", caller: caller, data: { id: token-id, sender: sender, recipient: recipient, amount: amount}})
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| token-id | uint |
| amount | uint |
| sender | principal |
| recipient | principal |

### transfer-memo

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L515)

`(define-public (transfer-memo ((token-id uint) (amount uint) (sender principal) (recipient principal) (memo (buff 34))) (response bool uint))`

SIP 013 transfer function that transfers pool token with memo

<details>
  <summary>Source code:</summary>

```clarity
(define-public (transfer-memo (token-id uint) (amount uint) (sender principal) (recipient principal) (memo (buff 34)))
	(begin
		(try! (transfer token-id amount sender recipient))
		(print memo)
		(ok true)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| token-id | uint |
| amount | uint |
| sender | principal |
| recipient | principal |
| memo | (buff 34) |

### transfer-many

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L524)

`(define-public (transfer-many ((transfers (list 200 (tuple (amount uint) (recipient principal) (sender principal) (token-id uint))))) (response bool uint))`

SIP 013 transfer function that transfers many pool token

<details>
  <summary>Source code:</summary>

```clarity
(define-public (transfer-many (transfers (list 200 {token-id: uint, amount: uint, sender: principal, recipient: principal})))
	(fold fold-transfer-many transfers (ok true))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| transfers | (list 200 (tuple (amount uint) (recipient principal) (sender principal) (token-id uint))) |

### transfer-many-memo

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L529)

`(define-public (transfer-many-memo ((transfers (list 200 (tuple (amount uint) (memo (buff 34)) (recipient principal) (sender principal) (token-id uint))))) (response bool uint))`

SIP 013 transfer function that transfers many pool token with memo

<details>
  <summary>Source code:</summary>

```clarity
(define-public (transfer-many-memo (transfers (list 200 {token-id: uint, amount: uint, sender: principal, recipient: principal, memo: (buff 34)})))
	(fold fold-transfer-many-memo transfers (ok true))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| transfers | (list 200 (tuple (amount uint) (memo (buff 34)) (recipient principal) (sender principal) (token-id uint))) |

### pool-transfer

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L534)

`(define-public (pool-transfer ((token-trait trait_reference) (amount uint) (recipient principal)) (response bool uint))`

Transfer tokens from this pool contract via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-public (pool-transfer (token-trait <sip-010-trait>) (amount uint) (recipient principal))
  (let (
    (token-contract (contract-of token-trait))
    (caller contract-caller)
  )
    (begin
      ;; Assert that caller is core address before transferring tokens
      (asserts! (is-eq caller (get core-address (var-get pool-addresses))) ERR_NOT_AUTHORIZED)

      ;; Assert that recipient address is standard principal
      (asserts! (is-standard recipient) ERR_INVALID_PRINCIPAL)

      ;; Assert that amount is greater than 0
      (asserts! (> amount u0) ERR_INVALID_AMOUNT)

      ;; Try to transfer amount of token from pool contract to recipient
      (try! (as-contract? ((with-all-assets-unsafe)) (try! (contract-call? token-trait transfer amount tx-sender recipient none))))

      ;; Print function data and return true
      (print {action: "pool-transfer", data: {token: token-contract, amount: amount, recipient: recipient}})
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| token-trait | trait_reference |
| amount | uint |
| recipient | principal |

### pool-mint

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L560)

`(define-public (pool-mint ((id uint) (amount uint) (user principal)) (response bool uint))`

Mint pool token to an user via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-public (pool-mint (id uint) (amount uint) (user principal))
  (let (
    (caller contract-caller)
  )
    (begin
      ;; Assert that caller is core address before minting tokens
      (asserts! (is-eq caller (get core-address (var-get pool-addresses))) ERR_NOT_AUTHORIZED)

      ;; Assert that user is standard principal and amount is greater than 0
      (asserts! (is-standard user) ERR_INVALID_PRINCIPAL)
      (asserts! (> amount u0) ERR_INVALID_AMOUNT)

      ;; Try to mint amount pool tokens to user
      (try! (ft-mint? pool-token amount user))

      ;; Try to tag pool token and update balances
      (try! (tag-pool-token-id {token-id: id, owner: user}))
      (try! (update-user-balance id user (+ (get-balance-or-default id user) amount)))
      (map-set balances-at-bin id (merge (unwrap-panic (get-bin-balances id)) {bin-shares: (+ (unwrap-panic (get-total-supply id)) amount)}))

      ;; Print SIP 013 data, function data, and return true
      (print {type: "sft_mint", token-id: id, amount: amount, recipient: user})
      (print {action: "pool-mint", data: {id: id, amount: amount, user: user}})
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| id | uint |
| amount | uint |
| user | principal |

### pool-burn

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L589)

`(define-public (pool-burn ((id uint) (amount uint) (user principal)) (response bool uint))`

Burn pool token from an user via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-public (pool-burn (id uint) (amount uint) (user principal))
  (let (
    (user-balance (get-balance-or-default id user))
    (caller contract-caller)
  )
    (begin
      ;; Assert that caller is core address before burning tokens
      (asserts! (is-eq caller (get core-address (var-get pool-addresses))) ERR_NOT_AUTHORIZED)

      ;; Assert that user is standard principal and amount is valid
      (asserts! (is-standard user) ERR_INVALID_PRINCIPAL)
      (asserts! (> amount u0) ERR_INVALID_AMOUNT)
      (asserts! (<= amount user-balance) ERR_INVALID_AMOUNT)

      ;; Try to burn amount pool tokens from user
      (try! (ft-burn? pool-token amount user))

      ;; Try to tag pool token and update balances
      (try! (tag-pool-token-id {token-id: id, owner: user}))
      (try! (update-user-balance id user (- user-balance amount)))
      (map-set balances-at-bin id (merge (unwrap-panic (get-bin-balances id)) {bin-shares: (- (unwrap-panic (get-total-supply id)) amount)}))

      ;; Print SIP 013 data, function data, and return true
      (print {type: "sft_burn", token-id: id, amount: amount, sender: user})
      (print {action: "pool-burn", data: {id: id, amount: amount, user: user}})
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| id | uint |
| amount | uint |
| user | principal |

### create-pool

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L620)

`(define-public (create-pool ((x-token-contract principal) (y-token-contract principal) (variable-fees-mgr principal) (fee-addr principal) (core-caller principal) (active-bin int) (step uint) (price uint) (id uint) (name (string-ascii 32)) (symbol (string-ascii 32)) (uri (string-ascii 256))) (response bool uint))`

Create pool using this pool contract via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-public (create-pool
    (x-token-contract principal) (y-token-contract principal)
    (variable-fees-mgr principal) (fee-addr principal) (core-caller principal)
    (active-bin int) (step uint) (price uint)
    (id uint) (name (string-ascii 32)) (symbol (string-ascii 32)) (uri (string-ascii 256))
  )
  (let (
    (current-pool-addresses (var-get pool-addresses))
    (caller contract-caller)
  )
    (begin
      ;; Assert that caller is core address and core caller is contract deployer before setting vars
      (asserts! (is-eq caller (get core-address current-pool-addresses)) ERR_NOT_AUTHORIZED)
      (asserts! (is-eq core-caller CONTRACT_DEPLOYER) ERR_NOT_POOL_CONTRACT_DEPLOYER)
      (var-set pool-info (merge (var-get pool-info) {
        pool-id: id,
        pool-name: name,
        pool-symbol: symbol,
        pool-uri: uri,
        pool-created: true,
        creation-height: burn-block-height
      }))
      (var-set pool-addresses (merge current-pool-addresses {
        variable-fees-manager: variable-fees-mgr,
        fee-address: fee-addr,
        x-token: x-token-contract,
        y-token: y-token-contract
      }))
      (var-set active-bin-id active-bin)
      (var-set bin-step step)
      (var-set initial-price price)
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| x-token-contract | principal |
| y-token-contract | principal |
| variable-fees-mgr | principal |
| fee-addr | principal |
| core-caller | principal |
| active-bin | int |
| step | uint |
| price | uint |
| id | uint |
| name | (string-ascii 32) |
| symbol | (string-ascii 32) |
| uri | (string-ascii 256) |

### fold-transfer-many

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L657)

`(define-private (fold-transfer-many ((item (tuple (amount uint) (recipient principal) (sender principal) (token-id uint))) (previous-response (response bool uint))) (response bool uint))`

Helper function to transfer many pool token

<details>
  <summary>Source code:</summary>

```clarity
(define-private (fold-transfer-many (item {token-id: uint, amount: uint, sender: principal, recipient: principal}) (previous-response (response bool uint)))
	(match previous-response prev-ok (transfer-memo (get token-id item) (get amount item) (get sender item) (get recipient item) 0x) prev-err previous-response)
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| item | (tuple (amount uint) (recipient principal) (sender principal) (token-id uint)) |
| previous-response | (response bool uint) |

### fold-transfer-many-memo

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L662)

`(define-private (fold-transfer-many-memo ((item (tuple (amount uint) (memo (buff 34)) (recipient principal) (sender principal) (token-id uint))) (previous-response (response bool uint))) (response bool uint))`

Helper function to transfer many pool token with memo

<details>
  <summary>Source code:</summary>

```clarity
(define-private (fold-transfer-many-memo (item {token-id: uint, amount: uint, sender: principal, recipient: principal, memo: (buff 34)}) (previous-response (response bool uint)))
	(match previous-response prev-ok (transfer-memo (get token-id item) (get amount item) (get sender item) (get recipient item) (get memo item)) prev-err previous-response)
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| item | (tuple (amount uint) (memo (buff 34)) (recipient principal) (sender principal) (token-id uint)) |
| previous-response | (response bool uint) |

### get-balance-or-default

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L667)

`(define-private (get-balance-or-default ((id uint) (user principal)) uint)`

Helper function to get token balance for an user by ID

<details>
  <summary>Source code:</summary>

```clarity
(define-private (get-balance-or-default (id uint) (user principal))
	(default-to u0 (map-get? user-balance-at-bin {id: id, user: user}))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| id | uint |
| user | principal |

### update-user-balance

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L672)

`(define-private (update-user-balance ((id uint) (user principal) (balance uint)) (response bool uint))`

Update user balances via pool

<details>
  <summary>Source code:</summary>

```clarity
(define-private (update-user-balance (id uint) (user principal) (balance uint))
  (let (
		(user-bins-data (unwrap-panic (get-user-bins user)))
	)
    (begin
      (match (index-of? user-bins-data id) id-index
        (and
          (is-eq balance u0)
          (map-set user-bins user (unwrap-panic (as-max-len? (concat (unwrap-panic (slice? user-bins-data u0 id-index)) (default-to (list) (slice? user-bins-data (+ id-index u1) (len user-bins-data)))) u1001)))
        )
        (and
          (> balance u0)
          (map-set user-bins user (unwrap! (as-max-len? (append user-bins-data id) u1001) ERR_MAX_NUMBER_OF_BINS))
        )
      )
      (map-set user-balance-at-bin {id: id, user: user} balance)
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| id | uint |
| user | principal |
| balance | uint |

### tag-pool-token-id

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L694)

`(define-private (tag-pool-token-id ((id (tuple (owner principal) (token-id uint)))) (response bool uint))`

Tag pool token

<details>
  <summary>Source code:</summary>

```clarity
(define-private (tag-pool-token-id (id {token-id: uint, owner: principal}))
	(begin
		(and (is-some (nft-get-owner? pool-token-id id)) (try! (nft-burn? pool-token-id id (get owner id))))
		(nft-mint? pool-token-id id (get owner id))
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| id | (tuple (owner principal) (token-id uint)) |

## Maps

### balances-at-bin



```clarity
(define-map balances-at-bin uint {x-balance: uint, y-balance: uint, bin-shares: uint})
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L89)

### user-balance-at-bin



```clarity
(define-map user-balance-at-bin {id: uint, user: principal} uint)
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L91)

### user-bins



```clarity
(define-map user-bins principal (list 1001 uint))
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L93)

## Variables

### pool-info

(tuple (creation-height uint) (pool-created bool) (pool-id uint) (pool-name (string-ascii 32)) (pool-symbol (string-ascii 32)) (pool-uri (string-ascii 256)))

Define all pool data vars and maps

```clarity
(define-data-var pool-info {
  pool-id: uint,
  pool-name: (string-ascii 32),
  pool-symbol: (string-ascii 32),
  pool-uri: (string-ascii 256),
  pool-created: bool,
  creation-height: uint
} {
  pool-id: u0,
  pool-name: "",
  pool-symbol: "",
  pool-uri: "",
  pool-created: false,
  creation-height: u0
})
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L28)

### pool-addresses

(tuple (core-address principal) (fee-address principal) (variable-fees-manager principal) (x-token principal) (y-token principal))



```clarity
(define-data-var pool-addresses {
  core-address: principal,
  variable-fees-manager: principal,
  fee-address: principal,
  x-token: principal,
  y-token: principal
} {
  core-address: .dlmm-core-v-1-1,
  variable-fees-manager: tx-sender,
  fee-address: tx-sender,
  x-token: tx-sender,
  y-token: tx-sender
})
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L44)

### bin-step

uint



```clarity
(define-data-var bin-step uint u0)
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L58)

### initial-price

uint



```clarity
(define-data-var initial-price uint u0)
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L60)

### active-bin-id

int



```clarity
(define-data-var active-bin-id int 0)
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L62)

### pool-fees

(tuple (x-protocol-fee uint) (x-provider-fee uint) (x-variable-fee uint) (y-protocol-fee uint) (y-provider-fee uint) (y-variable-fee uint))



```clarity
(define-data-var pool-fees {
  x-protocol-fee: uint,
  x-provider-fee: uint,
  x-variable-fee: uint,
  y-protocol-fee: uint,
  y-provider-fee: uint,
  y-variable-fee: uint
} {
  x-protocol-fee: u0,
  x-provider-fee: u0,
  x-variable-fee: u0,
  y-protocol-fee: u0,
  y-provider-fee: u0,
  y-variable-fee: u0
})
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L64)

### bin-change-count

uint



```clarity
(define-data-var bin-change-count uint u0)
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L80)

### last-variable-fees-update

uint



```clarity
(define-data-var last-variable-fees-update uint u0)
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L82)

### variable-fees-cooldown

uint



```clarity
(define-data-var variable-fees-cooldown uint u0)
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L83)

### freeze-variable-fees-manager

bool



```clarity
(define-data-var freeze-variable-fees-manager bool false)
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L85)

### dynamic-config

(buff 4096)



```clarity
(define-data-var dynamic-config (buff 4096) 0x)
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L87)

## Constants

### ERR_INSUFFICIENT_BALANCE_SIP_013



Error constants

```clarity
(define-constant ERR_INSUFFICIENT_BALANCE_SIP_013 (err u1))
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L14)

### ERR_MATCHING_PRINCIPALS_SIP_013





```clarity
(define-constant ERR_MATCHING_PRINCIPALS_SIP_013 (err u2))
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L15)

### ERR_INVALID_AMOUNT_SIP_013





```clarity
(define-constant ERR_INVALID_AMOUNT_SIP_013 (err u3))
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L16)

### ERR_NOT_AUTHORIZED_SIP_013





```clarity
(define-constant ERR_NOT_AUTHORIZED_SIP_013 (err u4))
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L17)

### ERR_NOT_AUTHORIZED





```clarity
(define-constant ERR_NOT_AUTHORIZED (err u3001))
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L18)

### ERR_INVALID_AMOUNT





```clarity
(define-constant ERR_INVALID_AMOUNT (err u3002))
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L19)

### ERR_INVALID_PRINCIPAL





```clarity
(define-constant ERR_INVALID_PRINCIPAL (err u3003))
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L20)

### ERR_NOT_POOL_CONTRACT_DEPLOYER





```clarity
(define-constant ERR_NOT_POOL_CONTRACT_DEPLOYER (err u3004))
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L21)

### ERR_MAX_NUMBER_OF_BINS





```clarity
(define-constant ERR_MAX_NUMBER_OF_BINS (err u3005))
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L22)

### CONTRACT_DEPLOYER



Contract deployer address

```clarity
(define-constant CONTRACT_DEPLOYER tx-sender)
```

[View in file](../clarity/contracts/dlmm-pool-sbtc-usdc-v-1-1.clar#L25)
  