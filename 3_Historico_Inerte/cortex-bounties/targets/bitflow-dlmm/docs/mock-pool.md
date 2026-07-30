
# mock-pool

[`mock-pool.clar`](../clarity/contracts/mocks/mock-pool.clar)

Minimal Mock Pool Contract

This contract provides the bare minimum implementation needed for testing

**Public functions:**

- [`set-revert`](#set-revert)
- [`set-pool-created`](#set-pool-created)
- [`set-active-bin-id-public`](#set-active-bin-id-public)
- [`set-active-bin-id`](#set-active-bin-id)
- [`update-bin-balances`](#update-bin-balances)
- [`update-bin-balances-on-withdraw`](#update-bin-balances-on-withdraw)
- [`pool-mint`](#pool-mint)
- [`pool-burn`](#pool-burn)
- [`pool-transfer`](#pool-transfer)
- [`create-pool`](#create-pool)
- [`transfer`](#transfer)
- [`transfer-memo`](#transfer-memo)
- [`transfer-many`](#transfer-many)
- [`transfer-many-memo`](#transfer-many-memo)
- [`set-pool-uri`](#set-pool-uri)
- [`set-core-address`](#set-core-address)
- [`set-variable-fees-manager`](#set-variable-fees-manager)
- [`set-fee-address`](#set-fee-address)
- [`set-x-fees`](#set-x-fees)
- [`set-y-fees`](#set-y-fees)
- [`set-variable-fees`](#set-variable-fees)
- [`set-variable-fees-cooldown`](#set-variable-fees-cooldown)
- [`set-freeze-variable-fees-manager`](#set-freeze-variable-fees-manager)
- [`set-dynamic-config`](#set-dynamic-config)

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
- [`revert`](#revert)

**Constants**

- [`ERR_NOT_AUTHORIZED_SIP_013`](#err_not_authorized_sip_013)
- [`ERR_INVALID_AMOUNT_SIP_013`](#err_invalid_amount_sip_013)
- [`ERR_INVALID_PRINCIPAL_SIP_013`](#err_invalid_principal_sip_013)
- [`ERR_NOT_AUTHORIZED`](#err_not_authorized)
- [`ERR_INVALID_AMOUNT`](#err_invalid_amount)
- [`CORE_ADDRESS`](#core_address)
- [`CONTRACT_DEPLOYER`](#contract_deployer)


## Functions

### set-revert

[View in file](../clarity/contracts/mocks/mock-pool.clar#L94)

`(define-public (set-revert ((flag bool)) (response bool none))`

Public setters - anyone can call these for testing

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-revert (flag bool))
  (ok (var-set revert flag)))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| flag | bool |

### set-pool-created

[View in file](../clarity/contracts/mocks/mock-pool.clar#L97)

`(define-public (set-pool-created ((created bool)) (response bool none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-pool-created (created bool))
  (ok (var-set pool-info (merge (var-get pool-info) {
        pool-created: created,
}))))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| created | bool |

### set-active-bin-id-public

[View in file](../clarity/contracts/mocks/mock-pool.clar#L102)

`(define-public (set-active-bin-id-public ((id int)) (response bool none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-active-bin-id-public (id int))
  (ok (var-set active-bin-id id)))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| id | int |

### get-name

[View in file](../clarity/contracts/mocks/mock-pool.clar#L112)

`(define-read-only (get-name () (response (string-ascii 9) none))`

SIP 013 functions - minimal implementations

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-name)
  (ok "Mock Pool"))
```
</details>




### get-symbol

[View in file](../clarity/contracts/mocks/mock-pool.clar#L115)

`(define-read-only (get-symbol () (response (string-ascii 4) none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-symbol)
  (ok "MOCK"))
```
</details>




### get-decimals

[View in file](../clarity/contracts/mocks/mock-pool.clar#L118)

`(define-read-only (get-decimals ((token-id uint)) (response uint none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-decimals (token-id uint))
  (ok u6))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| token-id | uint |

### get-token-uri

[View in file](../clarity/contracts/mocks/mock-pool.clar#L121)

`(define-read-only (get-token-uri ((token-id uint)) (response (optional (string-ascii 17)) none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-token-uri (token-id uint))
  (ok (some "https://mock.pool")))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| token-id | uint |

### get-total-supply

[View in file](../clarity/contracts/mocks/mock-pool.clar#L124)

`(define-read-only (get-total-supply ((token-id uint)) (response uint none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-total-supply (token-id uint))
  (ok (default-to u0 (get bin-shares (map-get? balances-at-bin token-id)))))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| token-id | uint |

### get-overall-supply

[View in file](../clarity/contracts/mocks/mock-pool.clar#L127)

`(define-read-only (get-overall-supply () (response uint none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-overall-supply)
  (ok (ft-get-supply pool-token)))
```
</details>




### get-balance

[View in file](../clarity/contracts/mocks/mock-pool.clar#L130)

`(define-read-only (get-balance ((token-id uint) (user principal)) (response uint none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-balance (token-id uint) (user principal))
  (ok (default-to u0 (map-get? user-balance-at-bin {id: token-id, user: user}))))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| token-id | uint |
| user | principal |

### get-overall-balance

[View in file](../clarity/contracts/mocks/mock-pool.clar#L133)

`(define-read-only (get-overall-balance ((user principal)) (response uint none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-overall-balance (user principal))
  (ok (ft-get-balance pool-token user)))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| user | principal |

### get-pool

[View in file](../clarity/contracts/mocks/mock-pool.clar#L136)

`(define-read-only (get-pool () (response (tuple (active-bin-id int) (bin-change-count uint) (bin-step uint) (core-address principal) (creation-height uint) (dynamic-config (buff 4096)) (fee-address principal) (freeze-variable-fees-manager bool) (initial-price uint) (last-variable-fees-update uint) (pool-created bool) (pool-id uint) (pool-name (string-ascii 32)) (pool-symbol (string-ascii 32)) (pool-token principal) (pool-uri (string-ascii 256)) (variable-fees-cooldown uint) (variable-fees-manager principal) (x-protocol-fee uint) (x-provider-fee uint) (x-token principal) (x-variable-fee uint) (y-protocol-fee uint) (y-provider-fee uint) (y-token principal) (y-variable-fee uint)) uint))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-pool)
  (let (
    (check (asserts! (not (var-get revert)) (err u42)))
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
      core-address: CORE_ADDRESS,
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

[View in file](../clarity/contracts/mocks/mock-pool.clar#L175)

`(define-read-only (get-pool-for-swap ((is-x-for-y bool)) (response (tuple (active-bin-id int) (bin-step uint) (fee-address principal) (initial-price uint) (pool-id uint) (pool-name (string-ascii 32)) (protocol-fee uint) (provider-fee uint) (variable-fee uint) (x-token principal) (y-token principal)) uint))`

Get all pool data for swapping

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-pool-for-swap (is-x-for-y bool))
  (let (
    (check (asserts! (not (var-get revert)) (err u42)))
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

[View in file](../clarity/contracts/mocks/mock-pool.clar#L199)

`(define-read-only (get-pool-for-add () (response (tuple (active-bin-id int) (bin-step uint) (initial-price uint) (pool-id uint) (pool-name (string-ascii 32)) (x-protocol-fee uint) (x-provider-fee uint) (x-token principal) (x-variable-fee uint) (y-protocol-fee uint) (y-provider-fee uint) (y-token principal) (y-variable-fee uint)) uint))`

Get all pool data for adding liquidity

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-pool-for-add)
  (let (
    (check (asserts! (not (var-get revert)) (err u42)))
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

[View in file](../clarity/contracts/mocks/mock-pool.clar#L225)

`(define-read-only (get-pool-for-withdraw () (response (tuple (pool-id uint) (pool-name (string-ascii 32)) (x-token principal) (y-token principal)) uint))`

Get all pool data for withdrawing liquidity

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-pool-for-withdraw)
  (let (
      (check (asserts! (not (var-get revert)) (err u42)))
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

[View in file](../clarity/contracts/mocks/mock-pool.clar#L239)

`(define-read-only (get-variable-fees-data () (response (tuple (bin-change-count uint) (dynamic-config (buff 4096)) (freeze-variable-fees-manager bool) (last-variable-fees-update uint) (variable-fees-cooldown uint) (variable-fees-manager principal) (x-variable-fee uint) (y-variable-fee uint)) none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-variable-fees-data)
  (let (
    (current-pool-fees (var-get pool-fees))
    (current-pool-addresses (var-get pool-addresses))
  )
    (ok {
      variable-fees-manager: (get variable-fees-manager current-pool-addresses),
      x-variable-fee: (get x-variable-fee current-pool-fees),
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




### get-active-bin-id

[View in file](../clarity/contracts/mocks/mock-pool.clar#L257)

`(define-read-only (get-active-bin-id () (response int uint))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-active-bin-id)
  (begin
    (asserts! (not (var-get revert)) (err u42))
    (ok (var-get active-bin-id))))
```
</details>




### get-bin-balances

[View in file](../clarity/contracts/mocks/mock-pool.clar#L262)

`(define-read-only (get-bin-balances ((id uint)) (response (tuple (bin-shares uint) (x-balance uint) (y-balance uint)) none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-bin-balances (id uint))
  (ok (default-to {x-balance: u0, y-balance: u0, bin-shares: u0} (map-get? balances-at-bin id))))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| id | uint |

### get-user-bins

[View in file](../clarity/contracts/mocks/mock-pool.clar#L265)

`(define-read-only (get-user-bins ((user principal)) (response (list 1001 uint) none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-user-bins (user principal))
  (ok (default-to (list) (map-get? user-bins user))))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| user | principal |

### set-active-bin-id

[View in file](../clarity/contracts/mocks/mock-pool.clar#L269)

`(define-public (set-active-bin-id ((id int)) (response bool uint))`

Core-only functions (kept minimal but functional)

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-active-bin-id (id int))
  (begin
    (asserts! (is-eq contract-caller CORE_ADDRESS) ERR_NOT_AUTHORIZED)
    (var-set active-bin-id id)
    (ok true)))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| id | int |

### update-bin-balances

[View in file](../clarity/contracts/mocks/mock-pool.clar#L275)

`(define-public (update-bin-balances ((bin-id uint) (x-balance uint) (y-balance uint)) (response bool uint))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (update-bin-balances (bin-id uint) (x-balance uint) (y-balance uint))
  (begin
    (asserts! (is-eq contract-caller CORE_ADDRESS) ERR_NOT_AUTHORIZED)
    (map-set balances-at-bin bin-id {x-balance: x-balance, y-balance: y-balance, bin-shares: (default-to u0 (get bin-shares (map-get? balances-at-bin bin-id)))})
    (ok true)))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| bin-id | uint |
| x-balance | uint |
| y-balance | uint |

### update-bin-balances-on-withdraw

[View in file](../clarity/contracts/mocks/mock-pool.clar#L282)

`(define-public (update-bin-balances-on-withdraw ((bin-id uint) (x-balance uint) (y-balance uint) (bin-shares uint)) (response bool none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (update-bin-balances-on-withdraw (bin-id uint) (x-balance uint) (y-balance uint) (bin-shares uint))
  (begin
    (map-set balances-at-bin bin-id {x-balance: x-balance, y-balance: y-balance, bin-shares: bin-shares})
    (ok true)
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

### pool-mint

[View in file](../clarity/contracts/mocks/mock-pool.clar#L290)

`(define-public (pool-mint ((id uint) (amount uint) (user principal)) (response bool uint))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (pool-mint (id uint) (amount uint) (user principal))
  (begin
    (asserts! (is-eq contract-caller CORE_ADDRESS) ERR_NOT_AUTHORIZED)
    (try! (ft-mint? pool-token amount user))
    (map-set user-balance-at-bin {id: id, user: user} (+ (default-to u0 (map-get? user-balance-at-bin {id: id, user: user})) amount))
    (map-set balances-at-bin id (merge (default-to {x-balance: u0, y-balance: u0, bin-shares: u0} (map-get? balances-at-bin id)) {bin-shares: (+ (default-to u0 (get bin-shares (map-get? balances-at-bin id))) amount)}))
    (ok true)))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| id | uint |
| amount | uint |
| user | principal |

### pool-burn

[View in file](../clarity/contracts/mocks/mock-pool.clar#L298)

`(define-public (pool-burn ((id uint) (amount uint) (user principal)) (response bool uint))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (pool-burn (id uint) (amount uint) (user principal))
  (begin
    (asserts! (is-eq contract-caller CORE_ADDRESS) ERR_NOT_AUTHORIZED)
    (try! (ft-burn? pool-token amount user))
    (map-set user-balance-at-bin {id: id, user: user} (- (default-to u0 (map-get? user-balance-at-bin {id: id, user: user})) amount))
    (map-set balances-at-bin id (merge (default-to {x-balance: u0, y-balance: u0, bin-shares: u0} (map-get? balances-at-bin id)) {bin-shares: (- (default-to u0 (get bin-shares (map-get? balances-at-bin id))) amount)}))
    (ok true)))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| id | uint |
| amount | uint |
| user | principal |

### pool-transfer

[View in file](../clarity/contracts/mocks/mock-pool.clar#L306)

`(define-public (pool-transfer ((token-trait trait_reference) (amount uint) (recipient principal)) (response bool uint))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (pool-transfer (token-trait <sip-010-trait>) (amount uint) (recipient principal))
  (begin
    (asserts! (is-eq contract-caller CORE_ADDRESS) ERR_NOT_AUTHORIZED)
    (try! (as-contract? ((with-all-assets-unsafe)) (try! (contract-call? token-trait transfer amount tx-sender recipient none))))
    (ok true)))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| token-trait | trait_reference |
| amount | uint |
| recipient | principal |

### create-pool

[View in file](../clarity/contracts/mocks/mock-pool.clar#L312)

`(define-public (create-pool ((x-token-contract principal) (y-token-contract principal) (variable-fees-mgr principal) (fee-addr principal) (core-caller principal) (active-bin int) (step uint) (price uint) (id uint) (name (string-ascii 32)) (symbol (string-ascii 32)) (uri (string-ascii 256))) (response bool uint))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (create-pool
    (x-token-contract principal) (y-token-contract principal)
    (variable-fees-mgr principal) (fee-addr principal) (core-caller principal)
    (active-bin int) (step uint) (price uint)
    (id uint) (name (string-ascii 32)) (symbol (string-ascii 32)) (uri (string-ascii 256)))
  (begin
    (asserts! (is-eq contract-caller CORE_ADDRESS) ERR_NOT_AUTHORIZED)
      (var-set pool-info (merge (var-get pool-info) {
        pool-id: id,
        pool-name: name,
        pool-symbol: symbol,
        pool-uri: uri,
        pool-created: true,
        creation-height: burn-block-height
      }))
      (var-set pool-addresses (merge (var-get pool-addresses) {
        variable-fees-manager: variable-fees-mgr,
        fee-address: fee-addr,
        x-token: x-token-contract,
        y-token: y-token-contract
      }))
      (var-set active-bin-id active-bin)
      (var-set bin-step step)
      (var-set initial-price price)
    (ok true)))
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

### transfer

[View in file](../clarity/contracts/mocks/mock-pool.clar#L339)

`(define-public (transfer ((token-id uint) (amount uint) (sender principal) (recipient principal)) (response bool none))`

Stub functions for SIP 013 compliance

<details>
  <summary>Source code:</summary>

```clarity
(define-public (transfer (token-id uint) (amount uint) (sender principal) (recipient principal))
  (ok true))
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

[View in file](../clarity/contracts/mocks/mock-pool.clar#L342)

`(define-public (transfer-memo ((token-id uint) (amount uint) (sender principal) (recipient principal) (memo (buff 34))) (response bool none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (transfer-memo (token-id uint) (amount uint) (sender principal) (recipient principal) (memo (buff 34)))
  (ok true))
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

[View in file](../clarity/contracts/mocks/mock-pool.clar#L345)

`(define-public (transfer-many ((transfers (list 200 (tuple (amount uint) (recipient principal) (sender principal) (token-id uint))))) (response bool none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (transfer-many (transfers (list 200 {token-id: uint, amount: uint, sender: principal, recipient: principal})))
  (ok true))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| transfers | (list 200 (tuple (amount uint) (recipient principal) (sender principal) (token-id uint))) |

### transfer-many-memo

[View in file](../clarity/contracts/mocks/mock-pool.clar#L348)

`(define-public (transfer-many-memo ((transfers (list 200 (tuple (amount uint) (memo (buff 34)) (recipient principal) (sender principal) (token-id uint))))) (response bool none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (transfer-many-memo (transfers (list 200 {token-id: uint, amount: uint, sender: principal, recipient: principal, memo: (buff 34)})))
  (ok true))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| transfers | (list 200 (tuple (amount uint) (memo (buff 34)) (recipient principal) (sender principal) (token-id uint))) |

### set-pool-uri

[View in file](../clarity/contracts/mocks/mock-pool.clar#L352)

`(define-public (set-pool-uri ((uri (string-ascii 256))) (response bool none))`

Stub functions for other core functions

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-pool-uri (uri (string-ascii 256))) (ok true))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| uri | (string-ascii 256) |

### set-core-address

[View in file](../clarity/contracts/mocks/mock-pool.clar#L353)

`(define-public (set-core-address ((address principal)) (response bool none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-core-address (address principal)) (ok true))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| address | principal |

### set-variable-fees-manager

[View in file](../clarity/contracts/mocks/mock-pool.clar#L354)

`(define-public (set-variable-fees-manager ((manager principal)) (response bool none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-variable-fees-manager (manager principal)) (ok true))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| manager | principal |

### set-fee-address

[View in file](../clarity/contracts/mocks/mock-pool.clar#L355)

`(define-public (set-fee-address ((address principal)) (response bool none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-fee-address (address principal)) (ok true))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| address | principal |

### set-x-fees

[View in file](../clarity/contracts/mocks/mock-pool.clar#L356)

`(define-public (set-x-fees ((protocol-fee uint) (provider-fee uint)) (response bool none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-x-fees (protocol-fee uint) (provider-fee uint)) (ok true))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| protocol-fee | uint |
| provider-fee | uint |

### set-y-fees

[View in file](../clarity/contracts/mocks/mock-pool.clar#L357)

`(define-public (set-y-fees ((protocol-fee uint) (provider-fee uint)) (response bool none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-y-fees (protocol-fee uint) (provider-fee uint)) (ok true))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| protocol-fee | uint |
| provider-fee | uint |

### set-variable-fees

[View in file](../clarity/contracts/mocks/mock-pool.clar#L358)

`(define-public (set-variable-fees ((x-fee uint) (y-fee uint)) (response bool none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-variable-fees (x-fee uint) (y-fee uint)) (ok true))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| x-fee | uint |
| y-fee | uint |

### set-variable-fees-cooldown

[View in file](../clarity/contracts/mocks/mock-pool.clar#L359)

`(define-public (set-variable-fees-cooldown ((cooldown uint)) (response bool none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-variable-fees-cooldown (cooldown uint)) (ok true))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| cooldown | uint |

### set-freeze-variable-fees-manager

[View in file](../clarity/contracts/mocks/mock-pool.clar#L360)

`(define-public (set-freeze-variable-fees-manager () (response bool none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-freeze-variable-fees-manager) (ok true))
```
</details>




### set-dynamic-config

[View in file](../clarity/contracts/mocks/mock-pool.clar#L361)

`(define-public (set-dynamic-config ((config (buff 4096))) (response bool none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-dynamic-config (config (buff 4096))) (ok true))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| config | (buff 4096) |

## Maps

### balances-at-bin



```clarity
(define-map balances-at-bin uint {x-balance: uint, y-balance: uint, bin-shares: uint})
```

[View in file](../clarity/contracts/mocks/mock-pool.clar#L85)

### user-balance-at-bin



```clarity
(define-map user-balance-at-bin {id: uint, user: principal} uint)
```

[View in file](../clarity/contracts/mocks/mock-pool.clar#L87)

### user-bins



```clarity
(define-map user-bins principal (list 1001 uint))
```

[View in file](../clarity/contracts/mocks/mock-pool.clar#L89)

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

[View in file](../clarity/contracts/mocks/mock-pool.clar#L26)

### pool-addresses

(tuple (fee-address principal) (variable-fees-manager principal) (x-token principal) (y-token principal))



```clarity
(define-data-var pool-addresses {
  variable-fees-manager: principal,
  fee-address: principal,
  x-token: principal,
  y-token: principal
} {
  variable-fees-manager: tx-sender,
  fee-address: tx-sender,
  x-token: tx-sender,
  y-token: tx-sender
})
```

[View in file](../clarity/contracts/mocks/mock-pool.clar#L42)

### bin-step

uint



```clarity
(define-data-var bin-step uint u0)
```

[View in file](../clarity/contracts/mocks/mock-pool.clar#L54)

### initial-price

uint



```clarity
(define-data-var initial-price uint u0)
```

[View in file](../clarity/contracts/mocks/mock-pool.clar#L56)

### active-bin-id

int



```clarity
(define-data-var active-bin-id int 0)
```

[View in file](../clarity/contracts/mocks/mock-pool.clar#L58)

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

[View in file](../clarity/contracts/mocks/mock-pool.clar#L60)

### bin-change-count

uint



```clarity
(define-data-var bin-change-count uint u0)
```

[View in file](../clarity/contracts/mocks/mock-pool.clar#L76)

### last-variable-fees-update

uint



```clarity
(define-data-var last-variable-fees-update uint u0)
```

[View in file](../clarity/contracts/mocks/mock-pool.clar#L78)

### variable-fees-cooldown

uint



```clarity
(define-data-var variable-fees-cooldown uint u0)
```

[View in file](../clarity/contracts/mocks/mock-pool.clar#L79)

### freeze-variable-fees-manager

bool



```clarity
(define-data-var freeze-variable-fees-manager bool false)
```

[View in file](../clarity/contracts/mocks/mock-pool.clar#L81)

### dynamic-config

(buff 4096)



```clarity
(define-data-var dynamic-config (buff 4096) 0x)
```

[View in file](../clarity/contracts/mocks/mock-pool.clar#L83)

### revert

bool



```clarity
(define-data-var revert bool false)
```

[View in file](../clarity/contracts/mocks/mock-pool.clar#L90)

## Constants

### ERR_NOT_AUTHORIZED_SIP_013



Minimal error constants

```clarity
(define-constant ERR_NOT_AUTHORIZED_SIP_013 (err u4))
```

[View in file](../clarity/contracts/mocks/mock-pool.clar#L15)

### ERR_INVALID_AMOUNT_SIP_013





```clarity
(define-constant ERR_INVALID_AMOUNT_SIP_013 (err u1))
```

[View in file](../clarity/contracts/mocks/mock-pool.clar#L16)

### ERR_INVALID_PRINCIPAL_SIP_013





```clarity
(define-constant ERR_INVALID_PRINCIPAL_SIP_013 (err u5))
```

[View in file](../clarity/contracts/mocks/mock-pool.clar#L17)

### ERR_NOT_AUTHORIZED





```clarity
(define-constant ERR_NOT_AUTHORIZED (err u3001))
```

[View in file](../clarity/contracts/mocks/mock-pool.clar#L18)

### ERR_INVALID_AMOUNT





```clarity
(define-constant ERR_INVALID_AMOUNT (err u3002))
```

[View in file](../clarity/contracts/mocks/mock-pool.clar#L19)

### CORE_ADDRESS



DLMM Core address and contract deployer address

```clarity
(define-constant CORE_ADDRESS .dlmm-core-v-1-1)
```

[View in file](../clarity/contracts/mocks/mock-pool.clar#L22)

### CONTRACT_DEPLOYER





```clarity
(define-constant CONTRACT_DEPLOYER tx-sender)
```

[View in file](../clarity/contracts/mocks/mock-pool.clar#L23)
  