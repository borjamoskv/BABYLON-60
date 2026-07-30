
# dlmm-liquidity-helper-v-1-1

[`dlmm-liquidity-helper-v-1-1.clar`](..\contracts\dlmm-liquidity-helper-v-1-1.clar)

dlmm-liquidity-helper-v-1-1

**Public functions:**

- [`add-liquidity-helper`](#add-liquidity-helper)
- [`withdraw-liquidity-helper`](#withdraw-liquidity-helper)

**Read-only functions:**



**Private functions:**

- [`fold-add-liquidity-helper`](#fold-add-liquidity-helper)
- [`fold-withdraw-liquidity-helper`](#fold-withdraw-liquidity-helper)

**Maps**



**Variables**



**Constants**

- [`ERR_NO_RESULT_DATA`](#err_no_result_data)
- [`ERR_MINIMUM_X_AMOUNT`](#err_minimum_x_amount)
- [`ERR_MINIMUM_Y_AMOUNT`](#err_minimum_y_amount)
- [`ERR_MINIMUM_LP_AMOUNT`](#err_minimum_lp_amount)


## Functions

### add-liquidity-helper

[View in file](..\contracts\dlmm-liquidity-helper-v-1-1.clar#L13)

`(define-public (add-liquidity-helper ((positions (list 120 (tuple (bin-id int) (pool-trait trait_reference) (x-amount uint) (x-token-trait trait_reference) (y-amount uint) (y-token-trait trait_reference)))) (min-dlp uint)) (response uint uint))`

Add liquidity to multiple bins in multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-public (add-liquidity-helper
    (positions (list 120 {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, bin-id: int, x-amount: uint, y-amount: uint}))
    (min-dlp uint)
  )
  (let (
    (add-liquidity-result (try! (fold fold-add-liquidity-helper positions (ok u0))))
  )
    (asserts! (>= add-liquidity-result min-dlp) ERR_MINIMUM_LP_AMOUNT)
    (ok add-liquidity-result)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| positions | (list 120 (tuple (bin-id int) (pool-trait trait_reference) (x-amount uint) (x-token-trait trait_reference) (y-amount uint) (y-token-trait trait_reference))) |
| min-dlp | uint |

### withdraw-liquidity-helper

[View in file](..\contracts\dlmm-liquidity-helper-v-1-1.clar#L26)

`(define-public (withdraw-liquidity-helper ((positions (list 120 (tuple (amount uint) (bin-id int) (pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference)))) (min-x-amount uint) (min-y-amount uint)) (response (tuple (x-amount uint) (y-amount uint)) uint))`

Withdraw liquidity from multiple bins in multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-public (withdraw-liquidity-helper
    (positions (list 120 {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, bin-id: int, amount: uint}))
    (min-x-amount uint) (min-y-amount uint)
  )
  (let (
    (withdraw-liquidity-result (try! (fold fold-withdraw-liquidity-helper positions (ok {x-amount: u0, y-amount: u0}))))
  )
    (asserts! (>= (get x-amount withdraw-liquidity-result) min-x-amount) ERR_MINIMUM_X_AMOUNT)
    (asserts! (>= (get y-amount withdraw-liquidity-result) min-y-amount) ERR_MINIMUM_Y_AMOUNT)
    (ok withdraw-liquidity-result)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| positions | (list 120 (tuple (amount uint) (bin-id int) (pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference))) |
| min-x-amount | uint |
| min-y-amount | uint |

### fold-add-liquidity-helper

[View in file](..\contracts\dlmm-liquidity-helper-v-1-1.clar#L41)

`(define-private (fold-add-liquidity-helper ((position (tuple (bin-id int) (pool-trait trait_reference) (x-amount uint) (x-token-trait trait_reference) (y-amount uint) (y-token-trait trait_reference))) (result (response uint uint))) (response uint uint))`

Fold function to add liquidity to multiple bins in multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-private (fold-add-liquidity-helper
    (position {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, bin-id: int, x-amount: uint, y-amount: uint})
    (result (response uint uint))
  )
  (let (
    (add-liquidity-result (try! (contract-call? .dlmm-core-v-1-1 add-liquidity (get pool-trait position) (get x-token-trait position) (get y-token-trait position) (get bin-id position) (get x-amount position) (get y-amount position) u1)))
    (updated-result (+ (unwrap! result ERR_NO_RESULT_DATA) add-liquidity-result))
  )
    (ok updated-result)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| position | (tuple (bin-id int) (pool-trait trait_reference) (x-amount uint) (x-token-trait trait_reference) (y-amount uint) (y-token-trait trait_reference)) |
| result | (response uint uint) |

### fold-withdraw-liquidity-helper

[View in file](..\contracts\dlmm-liquidity-helper-v-1-1.clar#L54)

`(define-private (fold-withdraw-liquidity-helper ((position (tuple (amount uint) (bin-id int) (pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference))) (result (response (tuple (x-amount uint) (y-amount uint)) uint))) (response (tuple (x-amount uint) (y-amount uint)) uint))`

Fold function to withdraw liquidity from multiple bins in multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-private (fold-withdraw-liquidity-helper
    (position {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, bin-id: int, amount: uint})
    (result (response {x-amount: uint, y-amount: uint} uint))
  )
  (let (
    (result-data (unwrap! result ERR_NO_RESULT_DATA))
    (bin-id (get bin-id position))
    (min-x-amount (if (>= bin-id 0) u1 u0))
    (min-y-amount (if (>= bin-id 0) u0 u1))
    (withdraw-liquidity-result (try! (contract-call? .dlmm-core-v-1-1 withdraw-liquidity (get pool-trait position) (get x-token-trait position) (get y-token-trait position) bin-id (get amount position) min-x-amount min-y-amount)))
    (updated-x-amount (+ (get x-amount result-data) (get x-amount withdraw-liquidity-result)))
    (updated-y-amount (+ (get y-amount result-data) (get y-amount withdraw-liquidity-result)))
  )
    (ok {x-amount: updated-x-amount, y-amount: updated-y-amount})
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| position | (tuple (amount uint) (bin-id int) (pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference)) |
| result | (response (tuple (x-amount uint) (y-amount uint)) uint) |

## Maps



## Variables



## Constants

### ERR_NO_RESULT_DATA





```clarity
(define-constant ERR_NO_RESULT_DATA (err u2001))
```

[View in file](..\contracts\dlmm-liquidity-helper-v-1-1.clar#L7)

### ERR_MINIMUM_X_AMOUNT





```clarity
(define-constant ERR_MINIMUM_X_AMOUNT (err u2002))
```

[View in file](..\contracts\dlmm-liquidity-helper-v-1-1.clar#L8)

### ERR_MINIMUM_Y_AMOUNT





```clarity
(define-constant ERR_MINIMUM_Y_AMOUNT (err u2003))
```

[View in file](..\contracts\dlmm-liquidity-helper-v-1-1.clar#L9)

### ERR_MINIMUM_LP_AMOUNT





```clarity
(define-constant ERR_MINIMUM_LP_AMOUNT (err u2004))
```

[View in file](..\contracts\dlmm-liquidity-helper-v-1-1.clar#L10)
  