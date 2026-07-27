
# dlmm-swap-helper-v-1-1

[`dlmm-swap-helper-v-1-1.clar`](..\contracts\dlmm-swap-helper-v-1-1.clar)

dlmm-swap-helper-v-1-1

**Public functions:**

- [`swap-helper`](#swap-helper)

**Read-only functions:**



**Private functions:**

- [`fold-swap-helper`](#fold-swap-helper)
- [`abs-int`](#abs-int)

**Maps**



**Variables**



**Constants**

- [`ERR_NO_RESULT_DATA`](#err_no_result_data)
- [`ERR_BIN_SLIPPAGE`](#err_bin_slippage)
- [`ERR_MINIMUM_RECEIVED`](#err_minimum_received)
- [`ERR_NO_ACTIVE_BIN_DATA`](#err_no_active_bin_data)


## Functions

### swap-helper

[View in file](..\contracts\dlmm-swap-helper-v-1-1.clar#L14)

`(define-public (swap-helper ((swaps (list 120 (tuple (amount uint) (bin-id int) (pool-trait trait_reference) (x-for-y bool) (x-token-trait trait_reference) (y-token-trait trait_reference)))) (min-received uint) (max-unfavorable-bins uint)) (response uint uint))`

Swap through multiple bins in multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-public (swap-helper
    (swaps (list 120 {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, bin-id: int, amount: uint, x-for-y: bool}))
    (min-received uint) (max-unfavorable-bins uint)
  )
  (let (
    (swap-result (try! (fold fold-swap-helper swaps (ok {received: u0, unfavorable: u0}))))
    (received (get received swap-result))
  )
    (asserts! (<= (get unfavorable swap-result) max-unfavorable-bins) ERR_BIN_SLIPPAGE)
    (asserts! (>= received min-received) ERR_MINIMUM_RECEIVED)
    (ok received)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| swaps | (list 120 (tuple (amount uint) (bin-id int) (pool-trait trait_reference) (x-for-y bool) (x-token-trait trait_reference) (y-token-trait trait_reference))) |
| min-received | uint |
| max-unfavorable-bins | uint |

### fold-swap-helper

[View in file](..\contracts\dlmm-swap-helper-v-1-1.clar#L29)

`(define-private (fold-swap-helper ((swap (tuple (amount uint) (bin-id int) (pool-trait trait_reference) (x-for-y bool) (x-token-trait trait_reference) (y-token-trait trait_reference))) (result (response (tuple (received uint) (unfavorable uint)) uint))) (response (tuple (received uint) (unfavorable uint)) uint))`

Fold function to swap through multiple bins in multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-private (fold-swap-helper
    (swap {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, bin-id: int, amount: uint, x-for-y: bool})
    (result (response {received: uint, unfavorable: uint} uint))
  )
  (let (
      (pool-trait (get pool-trait swap))
      (x-token-trait (get x-token-trait swap))
      (y-token-trait (get y-token-trait swap))
      (amount (get amount swap))
      (x-for-y (get x-for-y swap))
      (active-bin-id (unwrap! (contract-call? pool-trait get-active-bin-id) ERR_NO_ACTIVE_BIN_DATA))
      (bin-id-delta (- active-bin-id (get bin-id swap)))
      (is-unfavorable (if x-for-y (> bin-id-delta 0) (< bin-id-delta 0)))
      (swap-result (if x-for-y
                       (try! (contract-call? .dlmm-core-v-1-1 swap-x-for-y pool-trait x-token-trait y-token-trait active-bin-id amount))
                       (try! (contract-call? .dlmm-core-v-1-1 swap-y-for-x pool-trait x-token-trait y-token-trait active-bin-id amount))))
      (result-data (unwrap! result ERR_NO_RESULT_DATA))
  )
    (ok {
      received: (+ (get received result-data) swap-result),
      unfavorable: (+ (get unfavorable result-data) (if is-unfavorable (abs-int bin-id-delta) u0))
    })
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| swap | (tuple (amount uint) (bin-id int) (pool-trait trait_reference) (x-for-y bool) (x-token-trait trait_reference) (y-token-trait trait_reference)) |
| result | (response (tuple (received uint) (unfavorable uint)) uint) |

### abs-int

[View in file](..\contracts\dlmm-swap-helper-v-1-1.clar#L55)

`(define-private (abs-int ((value int)) uint)`

Get absolute value of a signed int as uint

<details>
  <summary>Source code:</summary>

```clarity
(define-private (abs-int (value int))
  (to-uint (if (>= value 0) value (- value)))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| value | int |

## Maps



## Variables



## Constants

### ERR_NO_RESULT_DATA



Error constants

```clarity
(define-constant ERR_NO_RESULT_DATA (err u2001))
```

[View in file](..\contracts\dlmm-swap-helper-v-1-1.clar#L8)

### ERR_BIN_SLIPPAGE





```clarity
(define-constant ERR_BIN_SLIPPAGE (err u2002))
```

[View in file](..\contracts\dlmm-swap-helper-v-1-1.clar#L9)

### ERR_MINIMUM_RECEIVED





```clarity
(define-constant ERR_MINIMUM_RECEIVED (err u2003))
```

[View in file](..\contracts\dlmm-swap-helper-v-1-1.clar#L10)

### ERR_NO_ACTIVE_BIN_DATA





```clarity
(define-constant ERR_NO_ACTIVE_BIN_DATA (err u2004))
```

[View in file](..\contracts\dlmm-swap-helper-v-1-1.clar#L11)
  