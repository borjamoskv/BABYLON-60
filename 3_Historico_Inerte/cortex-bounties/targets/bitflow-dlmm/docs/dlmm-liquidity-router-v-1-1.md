
# dlmm-liquidity-router-v-1-1

[`dlmm-liquidity-router-v-1-1.clar`](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar)

dlmm-liquidity-router-v-1-1

**Public functions:**

- [`add-liquidity-multi`](#add-liquidity-multi)
- [`add-relative-liquidity-multi`](#add-relative-liquidity-multi)
- [`add-relative-liquidity-same-multi`](#add-relative-liquidity-same-multi)
- [`withdraw-liquidity-multi`](#withdraw-liquidity-multi)
- [`withdraw-relative-liquidity-multi`](#withdraw-relative-liquidity-multi)
- [`withdraw-liquidity-same-multi`](#withdraw-liquidity-same-multi)
- [`withdraw-relative-liquidity-same-multi`](#withdraw-relative-liquidity-same-multi)
- [`move-liquidity-multi`](#move-liquidity-multi)
- [`move-relative-liquidity-multi`](#move-relative-liquidity-multi)

**Read-only functions:**



**Private functions:**

- [`fold-add-liquidity-multi`](#fold-add-liquidity-multi)
- [`fold-add-relative-liquidity-multi`](#fold-add-relative-liquidity-multi)
- [`fold-add-relative-liquidity-same-multi`](#fold-add-relative-liquidity-same-multi)
- [`fold-withdraw-liquidity-multi`](#fold-withdraw-liquidity-multi)
- [`fold-withdraw-relative-liquidity-multi`](#fold-withdraw-relative-liquidity-multi)
- [`fold-withdraw-liquidity-same-multi`](#fold-withdraw-liquidity-same-multi)
- [`fold-withdraw-relative-liquidity-same-multi`](#fold-withdraw-relative-liquidity-same-multi)
- [`fold-move-liquidity-multi`](#fold-move-liquidity-multi)
- [`fold-move-relative-liquidity-multi`](#fold-move-relative-liquidity-multi)
- [`abs-int`](#abs-int)

**Maps**



**Variables**



**Constants**

- [`ERR_NO_RESULT_DATA`](#err_no_result_data)
- [`ERR_MINIMUM_X_AMOUNT`](#err_minimum_x_amount)
- [`ERR_MINIMUM_Y_AMOUNT`](#err_minimum_y_amount)
- [`ERR_NO_ACTIVE_BIN_DATA`](#err_no_active_bin_data)
- [`ERR_EMPTY_POSITIONS_LIST`](#err_empty_positions_list)
- [`ERR_RESULTS_LIST_OVERFLOW`](#err_results_list_overflow)
- [`ERR_INVALID_BIN_ID`](#err_invalid_bin_id)
- [`ERR_ACTIVE_BIN_TOLERANCE`](#err_active_bin_tolerance)
- [`MIN_BIN_ID`](#min_bin_id)
- [`MAX_BIN_ID`](#max_bin_id)


## Functions

### add-liquidity-multi

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L21)

`(define-public (add-liquidity-multi ((positions (list 350 (tuple (bin-id int) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint) (min-dlp uint) (pool-trait trait_reference) (x-amount uint) (x-token-trait trait_reference) (y-amount uint) (y-token-trait trait_reference))))) (response (list 350 uint) uint))`

Add liquidity to multiple bins in multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-public (add-liquidity-multi
    (positions (list 350 {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, bin-id: int, x-amount: uint, y-amount: uint, min-dlp: uint, max-x-liquidity-fee: uint, max-y-liquidity-fee: uint}))
  )
  (let (
    (add-liquidity-result (try! (fold fold-add-liquidity-multi positions (ok (list )))))
  )
    (asserts! (> (len positions) u0) ERR_EMPTY_POSITIONS_LIST)
    (ok add-liquidity-result)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| positions | (list 350 (tuple (bin-id int) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint) (min-dlp uint) (pool-trait trait_reference) (x-amount uint) (x-token-trait trait_reference) (y-amount uint) (y-token-trait trait_reference))) |

### add-relative-liquidity-multi

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L33)

`(define-public (add-relative-liquidity-multi ((positions (list 350 (tuple (active-bin-id-offset int) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint) (min-dlp uint) (pool-trait trait_reference) (x-amount uint) (x-token-trait trait_reference) (y-amount uint) (y-token-trait trait_reference))))) (response (list 350 uint) uint))`

Add liquidity to multiple bins in multiple pools relative to the active bin

<details>
  <summary>Source code:</summary>

```clarity
(define-public (add-relative-liquidity-multi
    (positions (list 350 {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, active-bin-id-offset: int, x-amount: uint, y-amount: uint, min-dlp: uint, max-x-liquidity-fee: uint, max-y-liquidity-fee: uint}))
  )
  (let (
    (add-liquidity-result (try! (fold fold-add-relative-liquidity-multi positions (ok (list )))))
  )
    (asserts! (> (len positions) u0) ERR_EMPTY_POSITIONS_LIST)
    (ok add-liquidity-result)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| positions | (list 350 (tuple (active-bin-id-offset int) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint) (min-dlp uint) (pool-trait trait_reference) (x-amount uint) (x-token-trait trait_reference) (y-amount uint) (y-token-trait trait_reference))) |

### add-relative-liquidity-same-multi

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L45)

`(define-public (add-relative-liquidity-same-multi ((positions (list 350 (tuple (active-bin-id-offset int) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint) (min-dlp uint) (x-amount uint) (y-amount uint)))) (pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference) (active-bin-tolerance (optional (tuple (expected-bin-id int) (max-deviation uint))))) (response (tuple (active-bin-id int) (active-bin-id-delta uint) (results (list 350 uint))) uint))`

Add liquidity to multiple bins in a single pool relative to the active bin using the same token pair

<details>
  <summary>Source code:</summary>

```clarity
(define-public (add-relative-liquidity-same-multi
    (positions (list 350 {active-bin-id-offset: int, x-amount: uint, y-amount: uint, min-dlp: uint, max-x-liquidity-fee: uint, max-y-liquidity-fee: uint}))
    (pool-trait <dlmm-pool-trait>) (x-token-trait <sip-010-trait>) (y-token-trait <sip-010-trait>)
    (active-bin-tolerance (optional {max-deviation: uint, expected-bin-id: int}))
  )
  (let (
    (active-bin-id (unwrap! (contract-call? pool-trait get-active-bin-id) ERR_NO_ACTIVE_BIN_DATA))
    (add-liquidity-result (try! (fold fold-add-relative-liquidity-same-multi positions (ok {pool-trait: pool-trait, x-token-trait: x-token-trait, y-token-trait: y-token-trait, active-bin-id: active-bin-id, results: (list )}))))
    (active-bin-id-delta (if (is-some active-bin-tolerance)
                             (abs-int (- active-bin-id (get expected-bin-id (unwrap-panic active-bin-tolerance))))
                             u0))
  )
    (asserts! (> (len positions) u0) ERR_EMPTY_POSITIONS_LIST)
    (asserts! (or (is-none active-bin-tolerance) (<= active-bin-id-delta (get max-deviation (unwrap-panic active-bin-tolerance)))) ERR_ACTIVE_BIN_TOLERANCE)
    (ok {results: (get results add-liquidity-result), active-bin-id: active-bin-id, active-bin-id-delta: active-bin-id-delta})
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| positions | (list 350 (tuple (active-bin-id-offset int) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint) (min-dlp uint) (x-amount uint) (y-amount uint))) |
| pool-trait | trait_reference |
| x-token-trait | trait_reference |
| y-token-trait | trait_reference |
| active-bin-tolerance | (optional (tuple (expected-bin-id int) (max-deviation uint))) |

### withdraw-liquidity-multi

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L64)

`(define-public (withdraw-liquidity-multi ((positions (list 350 (tuple (amount uint) (bin-id int) (min-x-amount uint) (min-y-amount uint) (pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference))))) (response (list 350 (tuple (x-amount uint) (y-amount uint))) uint))`

Withdraw liquidity from multiple bins in multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-public (withdraw-liquidity-multi
    (positions (list 350 {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, bin-id: int, amount: uint, min-x-amount: uint, min-y-amount: uint}))
  )
  (let (
    (withdraw-liquidity-result (try! (fold fold-withdraw-liquidity-multi positions (ok (list )))))
  )
    (asserts! (> (len positions) u0) ERR_EMPTY_POSITIONS_LIST)
    (ok withdraw-liquidity-result)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| positions | (list 350 (tuple (amount uint) (bin-id int) (min-x-amount uint) (min-y-amount uint) (pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference))) |

### withdraw-relative-liquidity-multi

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L76)

`(define-public (withdraw-relative-liquidity-multi ((positions (list 350 (tuple (active-bin-id-offset int) (amount uint) (min-x-amount uint) (min-y-amount uint) (pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference))))) (response (list 350 (tuple (x-amount uint) (y-amount uint))) uint))`

Withdraw liquidity from multiple bins in multiple pools relative to the active bin

<details>
  <summary>Source code:</summary>

```clarity
(define-public (withdraw-relative-liquidity-multi
    (positions (list 350 {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, active-bin-id-offset: int, amount: uint, min-x-amount: uint, min-y-amount: uint}))
  )
  (let (
    (withdraw-liquidity-result (try! (fold fold-withdraw-relative-liquidity-multi positions (ok (list )))))
  )
    (asserts! (> (len positions) u0) ERR_EMPTY_POSITIONS_LIST)
    (ok withdraw-liquidity-result)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| positions | (list 350 (tuple (active-bin-id-offset int) (amount uint) (min-x-amount uint) (min-y-amount uint) (pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference))) |

### withdraw-liquidity-same-multi

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L88)

`(define-public (withdraw-liquidity-same-multi ((positions (list 350 (tuple (amount uint) (bin-id int) (min-x-amount uint) (min-y-amount uint) (pool-trait trait_reference)))) (x-token-trait trait_reference) (y-token-trait trait_reference) (min-x-amount-total uint) (min-y-amount-total uint)) (response (tuple (results (list 350 (tuple (x-amount uint) (y-amount uint)))) (x-amount uint) (y-amount uint)) uint))`

Withdraw liquidity from multiple bins in multiple pools using the same token pair

<details>
  <summary>Source code:</summary>

```clarity
(define-public (withdraw-liquidity-same-multi
    (positions (list 350 {pool-trait: <dlmm-pool-trait>, bin-id: int, amount: uint, min-x-amount: uint, min-y-amount: uint}))
    (x-token-trait <sip-010-trait>) (y-token-trait <sip-010-trait>)
    (min-x-amount-total uint) (min-y-amount-total uint)
  )
  (let (
    (withdraw-liquidity-result (try! (fold fold-withdraw-liquidity-same-multi positions (ok {x-token-trait: x-token-trait, y-token-trait: y-token-trait, results: (list ), x-amount: u0, y-amount: u0}))))
    (x-amount-total (get x-amount withdraw-liquidity-result))
    (y-amount-total (get y-amount withdraw-liquidity-result))
  )
    (asserts! (> (len positions) u0) ERR_EMPTY_POSITIONS_LIST)
    (asserts! (>= x-amount-total min-x-amount-total) ERR_MINIMUM_X_AMOUNT)
    (asserts! (>= y-amount-total min-y-amount-total) ERR_MINIMUM_Y_AMOUNT)
    (ok {results: (get results withdraw-liquidity-result), x-amount: x-amount-total, y-amount: y-amount-total})
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| positions | (list 350 (tuple (amount uint) (bin-id int) (min-x-amount uint) (min-y-amount uint) (pool-trait trait_reference))) |
| x-token-trait | trait_reference |
| y-token-trait | trait_reference |
| min-x-amount-total | uint |
| min-y-amount-total | uint |

### withdraw-relative-liquidity-same-multi

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L106)

`(define-public (withdraw-relative-liquidity-same-multi ((positions (list 350 (tuple (active-bin-id-offset int) (amount uint) (min-x-amount uint) (min-y-amount uint) (pool-trait trait_reference)))) (x-token-trait trait_reference) (y-token-trait trait_reference) (min-x-amount-total uint) (min-y-amount-total uint)) (response (tuple (results (list 350 (tuple (x-amount uint) (y-amount uint)))) (x-amount uint) (y-amount uint)) uint))`

Withdraw liquidity from multiple bins in multiple pools relative to the active bin using the same token pair

<details>
  <summary>Source code:</summary>

```clarity
(define-public (withdraw-relative-liquidity-same-multi
    (positions (list 350 {pool-trait: <dlmm-pool-trait>, active-bin-id-offset: int, amount: uint, min-x-amount: uint, min-y-amount: uint}))
    (x-token-trait <sip-010-trait>) (y-token-trait <sip-010-trait>)
    (min-x-amount-total uint) (min-y-amount-total uint)
  )
  (let (
    (withdraw-liquidity-result (try! (fold fold-withdraw-relative-liquidity-same-multi positions (ok {x-token-trait: x-token-trait, y-token-trait: y-token-trait, results: (list ), x-amount: u0, y-amount: u0}))))
    (x-amount-total (get x-amount withdraw-liquidity-result))
    (y-amount-total (get y-amount withdraw-liquidity-result))
  )
    (asserts! (> (len positions) u0) ERR_EMPTY_POSITIONS_LIST)
    (asserts! (>= x-amount-total min-x-amount-total) ERR_MINIMUM_X_AMOUNT)
    (asserts! (>= y-amount-total min-y-amount-total) ERR_MINIMUM_Y_AMOUNT)
    (ok {results: (get results withdraw-liquidity-result), x-amount: x-amount-total, y-amount: y-amount-total})
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| positions | (list 350 (tuple (active-bin-id-offset int) (amount uint) (min-x-amount uint) (min-y-amount uint) (pool-trait trait_reference))) |
| x-token-trait | trait_reference |
| y-token-trait | trait_reference |
| min-x-amount-total | uint |
| min-y-amount-total | uint |

### move-liquidity-multi

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L124)

`(define-public (move-liquidity-multi ((positions (list 350 (tuple (amount uint) (from-bin-id int) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint) (min-dlp uint) (pool-trait trait_reference) (to-bin-id int) (x-token-trait trait_reference) (y-token-trait trait_reference))))) (response (list 350 uint) uint))`

Move liquidity for multiple bins in multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-public (move-liquidity-multi
    (positions (list 350 {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, from-bin-id: int, to-bin-id: int, amount: uint, min-dlp: uint, max-x-liquidity-fee: uint, max-y-liquidity-fee: uint}))
  )
  (let (
    (move-liquidity-result (try! (fold fold-move-liquidity-multi positions (ok (list )))))
  )
    (asserts! (> (len positions) u0) ERR_EMPTY_POSITIONS_LIST)
    (ok move-liquidity-result)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| positions | (list 350 (tuple (amount uint) (from-bin-id int) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint) (min-dlp uint) (pool-trait trait_reference) (to-bin-id int) (x-token-trait trait_reference) (y-token-trait trait_reference))) |

### move-relative-liquidity-multi

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L136)

`(define-public (move-relative-liquidity-multi ((positions (list 350 (tuple (active-bin-id-offset int) (amount uint) (from-bin-id int) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint) (min-dlp uint) (pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference))))) (response (list 350 uint) uint))`

Move liquidity for multiple bins in multiple pools relative to the active bin

<details>
  <summary>Source code:</summary>

```clarity
(define-public (move-relative-liquidity-multi
    (positions (list 350 {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, from-bin-id: int, active-bin-id-offset: int, amount: uint, min-dlp: uint, max-x-liquidity-fee: uint, max-y-liquidity-fee: uint}))
  )
  (let (
    (move-liquidity-result (try! (fold fold-move-relative-liquidity-multi positions (ok (list )))))
  )
    (asserts! (> (len positions) u0) ERR_EMPTY_POSITIONS_LIST)
    (ok move-liquidity-result)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| positions | (list 350 (tuple (active-bin-id-offset int) (amount uint) (from-bin-id int) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint) (min-dlp uint) (pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference))) |

### fold-add-liquidity-multi

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L148)

`(define-private (fold-add-liquidity-multi ((position (tuple (bin-id int) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint) (min-dlp uint) (pool-trait trait_reference) (x-amount uint) (x-token-trait trait_reference) (y-amount uint) (y-token-trait trait_reference))) (result (response (list 350 uint) uint))) (response (list 350 uint) uint))`

Fold function to add liquidity to multiple bins in multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-private (fold-add-liquidity-multi
    (position {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, bin-id: int, x-amount: uint, y-amount: uint, min-dlp: uint, max-x-liquidity-fee: uint, max-y-liquidity-fee: uint})
    (result (response (list 350 uint) uint))
  )
  (let (
    (result-data (unwrap! result ERR_NO_RESULT_DATA))
    (bin-id (get bin-id position))
    (bin-id-check (asserts! (and (>= bin-id MIN_BIN_ID) (<= bin-id MAX_BIN_ID)) ERR_INVALID_BIN_ID))
    (add-liquidity-result (try! (contract-call? .dlmm-core-v-1-1 add-liquidity (get pool-trait position) (get x-token-trait position) (get y-token-trait position) bin-id (get x-amount position) (get y-amount position) (get min-dlp position) (get max-x-liquidity-fee position) (get max-y-liquidity-fee position))))
    (updated-result (unwrap! (as-max-len? (append result-data add-liquidity-result) u350) ERR_RESULTS_LIST_OVERFLOW))
  )
    (ok updated-result)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| position | (tuple (bin-id int) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint) (min-dlp uint) (pool-trait trait_reference) (x-amount uint) (x-token-trait trait_reference) (y-amount uint) (y-token-trait trait_reference)) |
| result | (response (list 350 uint) uint) |

### fold-add-relative-liquidity-multi

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L164)

`(define-private (fold-add-relative-liquidity-multi ((position (tuple (active-bin-id-offset int) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint) (min-dlp uint) (pool-trait trait_reference) (x-amount uint) (x-token-trait trait_reference) (y-amount uint) (y-token-trait trait_reference))) (result (response (list 350 uint) uint))) (response (list 350 uint) uint))`

Fold function to add liquidity to multiple bins in multiple pools relative to the active bin

<details>
  <summary>Source code:</summary>

```clarity
(define-private (fold-add-relative-liquidity-multi
    (position {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, active-bin-id-offset: int, x-amount: uint, y-amount: uint, min-dlp: uint, max-x-liquidity-fee: uint, max-y-liquidity-fee: uint})
    (result (response (list 350 uint) uint))
  )
  (let (
    (result-data (unwrap! result ERR_NO_RESULT_DATA))
    (pool-trait (get pool-trait position))
    (active-bin-id (unwrap! (contract-call? pool-trait get-active-bin-id) ERR_NO_ACTIVE_BIN_DATA))
    (bin-id (+ active-bin-id (get active-bin-id-offset position)))
    (bin-id-check (asserts! (and (>= bin-id MIN_BIN_ID) (<= bin-id MAX_BIN_ID)) ERR_INVALID_BIN_ID))
    (add-liquidity-result (try! (contract-call? .dlmm-core-v-1-1 add-liquidity pool-trait (get x-token-trait position) (get y-token-trait position) bin-id (get x-amount position) (get y-amount position) (get min-dlp position) (get max-x-liquidity-fee position) (get max-y-liquidity-fee position))))
    (updated-result (unwrap! (as-max-len? (append result-data add-liquidity-result) u350) ERR_RESULTS_LIST_OVERFLOW))
  )
    (ok updated-result)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| position | (tuple (active-bin-id-offset int) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint) (min-dlp uint) (pool-trait trait_reference) (x-amount uint) (x-token-trait trait_reference) (y-amount uint) (y-token-trait trait_reference)) |
| result | (response (list 350 uint) uint) |

### fold-add-relative-liquidity-same-multi

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L182)

`(define-private (fold-add-relative-liquidity-same-multi ((position (tuple (active-bin-id-offset int) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint) (min-dlp uint) (x-amount uint) (y-amount uint))) (result (response (tuple (active-bin-id int) (pool-trait trait_reference) (results (list 350 uint)) (x-token-trait trait_reference) (y-token-trait trait_reference)) uint))) (response (tuple (active-bin-id int) (pool-trait trait_reference) (results (list 350 uint)) (x-token-trait trait_reference) (y-token-trait trait_reference)) uint))`

Fold function to add liquidity to multiple bins in a single pool relative to the active bin using the same token pair

<details>
  <summary>Source code:</summary>

```clarity
(define-private (fold-add-relative-liquidity-same-multi
    (position {active-bin-id-offset: int, x-amount: uint, y-amount: uint, min-dlp: uint, max-x-liquidity-fee: uint, max-y-liquidity-fee: uint})
    (result (response {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, active-bin-id: int, results: (list 350 uint)} uint))
  )
  (let (
    (result-data (unwrap! result ERR_NO_RESULT_DATA))
    (pool-trait (get pool-trait result-data))
    (x-token-trait (get x-token-trait result-data))
    (y-token-trait (get y-token-trait result-data))
    (active-bin-id (get active-bin-id result-data))
    (bin-id (+ active-bin-id (get active-bin-id-offset position)))
    (bin-id-check (asserts! (and (>= bin-id MIN_BIN_ID) (<= bin-id MAX_BIN_ID)) ERR_INVALID_BIN_ID))
    (add-liquidity-result (try! (contract-call? .dlmm-core-v-1-1 add-liquidity pool-trait x-token-trait y-token-trait bin-id (get x-amount position) (get y-amount position) (get min-dlp position) (get max-x-liquidity-fee position) (get max-y-liquidity-fee position))))
    (updated-results (unwrap! (as-max-len? (append (get results result-data) add-liquidity-result) u350) ERR_RESULTS_LIST_OVERFLOW))
  )
    (ok {pool-trait: pool-trait, x-token-trait: x-token-trait, y-token-trait: y-token-trait, active-bin-id: active-bin-id, results: updated-results})
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| position | (tuple (active-bin-id-offset int) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint) (min-dlp uint) (x-amount uint) (y-amount uint)) |
| result | (response (tuple (active-bin-id int) (pool-trait trait_reference) (results (list 350 uint)) (x-token-trait trait_reference) (y-token-trait trait_reference)) uint) |

### fold-withdraw-liquidity-multi

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L202)

`(define-private (fold-withdraw-liquidity-multi ((position (tuple (amount uint) (bin-id int) (min-x-amount uint) (min-y-amount uint) (pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference))) (result (response (list 350 (tuple (x-amount uint) (y-amount uint))) uint))) (response (list 350 (tuple (x-amount uint) (y-amount uint))) uint))`

Fold function to withdraw liquidity from multiple bins in multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-private (fold-withdraw-liquidity-multi
    (position {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, bin-id: int, amount: uint, min-x-amount: uint, min-y-amount: uint})
    (result (response (list 350 {x-amount: uint, y-amount: uint}) uint))
  )
  (let (
    (result-data (unwrap! result ERR_NO_RESULT_DATA))
    (bin-id (get bin-id position))
    (bin-id-check (asserts! (and (>= bin-id MIN_BIN_ID) (<= bin-id MAX_BIN_ID)) ERR_INVALID_BIN_ID))
    (withdraw-liquidity-result (try! (contract-call? .dlmm-core-v-1-1 withdraw-liquidity (get pool-trait position) (get x-token-trait position) (get y-token-trait position) bin-id (get amount position) (get min-x-amount position) (get min-y-amount position))))
    (updated-result (unwrap! (as-max-len? (append result-data withdraw-liquidity-result) u350) ERR_RESULTS_LIST_OVERFLOW))
  )
    (ok updated-result)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| position | (tuple (amount uint) (bin-id int) (min-x-amount uint) (min-y-amount uint) (pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference)) |
| result | (response (list 350 (tuple (x-amount uint) (y-amount uint))) uint) |

### fold-withdraw-relative-liquidity-multi

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L218)

`(define-private (fold-withdraw-relative-liquidity-multi ((position (tuple (active-bin-id-offset int) (amount uint) (min-x-amount uint) (min-y-amount uint) (pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference))) (result (response (list 350 (tuple (x-amount uint) (y-amount uint))) uint))) (response (list 350 (tuple (x-amount uint) (y-amount uint))) uint))`

Fold function to withdraw liquidity from multiple bins in multiple pools relative to the active bin

<details>
  <summary>Source code:</summary>

```clarity
(define-private (fold-withdraw-relative-liquidity-multi
    (position {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, active-bin-id-offset: int, amount: uint, min-x-amount: uint, min-y-amount: uint})
    (result (response (list 350 {x-amount: uint, y-amount: uint}) uint))
  )
  (let (
    (result-data (unwrap! result ERR_NO_RESULT_DATA))
    (pool-trait (get pool-trait position))
    (active-bin-id (unwrap! (contract-call? pool-trait get-active-bin-id) ERR_NO_ACTIVE_BIN_DATA))
    (bin-id (+ active-bin-id (get active-bin-id-offset position)))
    (bin-id-check (asserts! (and (>= bin-id MIN_BIN_ID) (<= bin-id MAX_BIN_ID)) ERR_INVALID_BIN_ID))
    (withdraw-liquidity-result (try! (contract-call? .dlmm-core-v-1-1 withdraw-liquidity pool-trait (get x-token-trait position) (get y-token-trait position) bin-id (get amount position) (get min-x-amount position) (get min-y-amount position))))
    (updated-result (unwrap! (as-max-len? (append result-data withdraw-liquidity-result) u350) ERR_RESULTS_LIST_OVERFLOW))
  )
    (ok updated-result)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| position | (tuple (active-bin-id-offset int) (amount uint) (min-x-amount uint) (min-y-amount uint) (pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference)) |
| result | (response (list 350 (tuple (x-amount uint) (y-amount uint))) uint) |

### fold-withdraw-liquidity-same-multi

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L236)

`(define-private (fold-withdraw-liquidity-same-multi ((position (tuple (amount uint) (bin-id int) (min-x-amount uint) (min-y-amount uint) (pool-trait trait_reference))) (result (response (tuple (results (list 350 (tuple (x-amount uint) (y-amount uint)))) (x-amount uint) (x-token-trait trait_reference) (y-amount uint) (y-token-trait trait_reference)) uint))) (response (tuple (results (list 350 (tuple (x-amount uint) (y-amount uint)))) (x-amount uint) (x-token-trait trait_reference) (y-amount uint) (y-token-trait trait_reference)) uint))`

Fold function to withdraw liquidity from multiple bins in multiple pools using the same token pair

<details>
  <summary>Source code:</summary>

```clarity
(define-private (fold-withdraw-liquidity-same-multi
    (position {pool-trait: <dlmm-pool-trait>, bin-id: int, amount: uint, min-x-amount: uint, min-y-amount: uint})
    (result (response {x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, results: (list 350 {x-amount: uint, y-amount: uint}), x-amount: uint, y-amount: uint} uint))
  )
  (let (
    (result-data (unwrap! result ERR_NO_RESULT_DATA))
    (x-token-trait (get x-token-trait result-data))
    (y-token-trait (get y-token-trait result-data))
    (bin-id (get bin-id position))
    (bin-id-check (asserts! (and (>= bin-id MIN_BIN_ID) (<= bin-id MAX_BIN_ID)) ERR_INVALID_BIN_ID))
    (withdraw-liquidity-result (try! (contract-call? .dlmm-core-v-1-1 withdraw-liquidity (get pool-trait position) x-token-trait y-token-trait bin-id (get amount position) (get min-x-amount position) (get min-y-amount position))))
    (updated-results (unwrap! (as-max-len? (append (get results result-data) withdraw-liquidity-result) u350) ERR_RESULTS_LIST_OVERFLOW))
    (updated-x-amount (+ (get x-amount result-data) (get x-amount withdraw-liquidity-result)))
    (updated-y-amount (+ (get y-amount result-data) (get y-amount withdraw-liquidity-result)))
  )
    (ok {x-token-trait: x-token-trait, y-token-trait: y-token-trait, results: updated-results, x-amount: updated-x-amount, y-amount: updated-y-amount})
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| position | (tuple (amount uint) (bin-id int) (min-x-amount uint) (min-y-amount uint) (pool-trait trait_reference)) |
| result | (response (tuple (results (list 350 (tuple (x-amount uint) (y-amount uint)))) (x-amount uint) (x-token-trait trait_reference) (y-amount uint) (y-token-trait trait_reference)) uint) |

### fold-withdraw-relative-liquidity-same-multi

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L256)

`(define-private (fold-withdraw-relative-liquidity-same-multi ((position (tuple (active-bin-id-offset int) (amount uint) (min-x-amount uint) (min-y-amount uint) (pool-trait trait_reference))) (result (response (tuple (results (list 350 (tuple (x-amount uint) (y-amount uint)))) (x-amount uint) (x-token-trait trait_reference) (y-amount uint) (y-token-trait trait_reference)) uint))) (response (tuple (results (list 350 (tuple (x-amount uint) (y-amount uint)))) (x-amount uint) (x-token-trait trait_reference) (y-amount uint) (y-token-trait trait_reference)) uint))`

Fold function to withdraw liquidity from multiple bins in multiple pools relative to the active bin using the same token pair

<details>
  <summary>Source code:</summary>

```clarity
(define-private (fold-withdraw-relative-liquidity-same-multi
    (position {pool-trait: <dlmm-pool-trait>, active-bin-id-offset: int, amount: uint, min-x-amount: uint, min-y-amount: uint})
    (result (response {x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, results: (list 350 {x-amount: uint, y-amount: uint}), x-amount: uint, y-amount: uint} uint))
  )
  (let (
    (result-data (unwrap! result ERR_NO_RESULT_DATA))
    (x-token-trait (get x-token-trait result-data))
    (y-token-trait (get y-token-trait result-data))
    (pool-trait (get pool-trait position))
    (active-bin-id (unwrap! (contract-call? pool-trait get-active-bin-id) ERR_NO_ACTIVE_BIN_DATA))
    (bin-id (+ active-bin-id (get active-bin-id-offset position)))
    (bin-id-check (asserts! (and (>= bin-id MIN_BIN_ID) (<= bin-id MAX_BIN_ID)) ERR_INVALID_BIN_ID))
    (withdraw-liquidity-result (try! (contract-call? .dlmm-core-v-1-1 withdraw-liquidity pool-trait x-token-trait y-token-trait bin-id (get amount position) (get min-x-amount position) (get min-y-amount position))))
    (updated-results (unwrap! (as-max-len? (append (get results result-data) withdraw-liquidity-result) u350) ERR_RESULTS_LIST_OVERFLOW))
    (updated-x-amount (+ (get x-amount result-data) (get x-amount withdraw-liquidity-result)))
    (updated-y-amount (+ (get y-amount result-data) (get y-amount withdraw-liquidity-result)))
  )
    (ok {x-token-trait: x-token-trait, y-token-trait: y-token-trait, results: updated-results, x-amount: updated-x-amount, y-amount: updated-y-amount})
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| position | (tuple (active-bin-id-offset int) (amount uint) (min-x-amount uint) (min-y-amount uint) (pool-trait trait_reference)) |
| result | (response (tuple (results (list 350 (tuple (x-amount uint) (y-amount uint)))) (x-amount uint) (x-token-trait trait_reference) (y-amount uint) (y-token-trait trait_reference)) uint) |

### fold-move-liquidity-multi

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L278)

`(define-private (fold-move-liquidity-multi ((position (tuple (amount uint) (from-bin-id int) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint) (min-dlp uint) (pool-trait trait_reference) (to-bin-id int) (x-token-trait trait_reference) (y-token-trait trait_reference))) (result (response (list 350 uint) uint))) (response (list 350 uint) uint))`

Fold function to move liquidity for multiple bins in multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-private (fold-move-liquidity-multi
    (position {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, from-bin-id: int, to-bin-id: int, amount: uint, min-dlp: uint, max-x-liquidity-fee: uint, max-y-liquidity-fee: uint})
    (result (response (list 350 uint) uint))
  )
  (let (
    (result-data (unwrap! result ERR_NO_RESULT_DATA))
    (from-bin-id (get from-bin-id position))
    (to-bin-id (get to-bin-id position))
    (from-bin-id-check (asserts! (and (>= from-bin-id MIN_BIN_ID) (<= from-bin-id MAX_BIN_ID)) ERR_INVALID_BIN_ID))
    (to-bin-id-check (asserts! (and (>= to-bin-id MIN_BIN_ID) (<= to-bin-id MAX_BIN_ID)) ERR_INVALID_BIN_ID))
    (move-liquidity-result (try! (contract-call? .dlmm-core-v-1-1 move-liquidity (get pool-trait position) (get x-token-trait position) (get y-token-trait position) from-bin-id to-bin-id (get amount position) (get min-dlp position) (get max-x-liquidity-fee position) (get max-y-liquidity-fee position))))
    (updated-result (unwrap! (as-max-len? (append result-data move-liquidity-result) u350) ERR_RESULTS_LIST_OVERFLOW))
  )
    (ok updated-result)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| position | (tuple (amount uint) (from-bin-id int) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint) (min-dlp uint) (pool-trait trait_reference) (to-bin-id int) (x-token-trait trait_reference) (y-token-trait trait_reference)) |
| result | (response (list 350 uint) uint) |

### fold-move-relative-liquidity-multi

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L296)

`(define-private (fold-move-relative-liquidity-multi ((position (tuple (active-bin-id-offset int) (amount uint) (from-bin-id int) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint) (min-dlp uint) (pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference))) (result (response (list 350 uint) uint))) (response (list 350 uint) uint))`

Fold function to move liquidity for multiple bins in multiple pools relative to the active bin

<details>
  <summary>Source code:</summary>

```clarity
(define-private (fold-move-relative-liquidity-multi
    (position {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, from-bin-id: int, active-bin-id-offset: int, amount: uint, min-dlp: uint, max-x-liquidity-fee: uint, max-y-liquidity-fee: uint})
    (result (response (list 350 uint) uint))
  )
  (let (
    (result-data (unwrap! result ERR_NO_RESULT_DATA))
    (pool-trait (get pool-trait position))
    (from-bin-id (get from-bin-id position))
    (from-bin-id-check (asserts! (and (>= from-bin-id MIN_BIN_ID) (<= from-bin-id MAX_BIN_ID)) ERR_INVALID_BIN_ID))
    (active-bin-id (unwrap! (contract-call? pool-trait get-active-bin-id) ERR_NO_ACTIVE_BIN_DATA))
    (to-bin-id (+ active-bin-id (get active-bin-id-offset position)))
    (to-bin-id-check (asserts! (and (>= to-bin-id MIN_BIN_ID) (<= to-bin-id MAX_BIN_ID)) ERR_INVALID_BIN_ID))
    (move-liquidity-result (try! (contract-call? .dlmm-core-v-1-1 move-liquidity pool-trait (get x-token-trait position) (get y-token-trait position) from-bin-id to-bin-id (get amount position) (get min-dlp position) (get max-x-liquidity-fee position) (get max-y-liquidity-fee position))))
    (updated-result (unwrap! (as-max-len? (append result-data move-liquidity-result) u350) ERR_RESULTS_LIST_OVERFLOW))
  )
    (ok updated-result)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| position | (tuple (active-bin-id-offset int) (amount uint) (from-bin-id int) (max-x-liquidity-fee uint) (max-y-liquidity-fee uint) (min-dlp uint) (pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference)) |
| result | (response (list 350 uint) uint) |

### abs-int

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L316)

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





```clarity
(define-constant ERR_NO_RESULT_DATA (err u5001))
```

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L7)

### ERR_MINIMUM_X_AMOUNT





```clarity
(define-constant ERR_MINIMUM_X_AMOUNT (err u5002))
```

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L8)

### ERR_MINIMUM_Y_AMOUNT





```clarity
(define-constant ERR_MINIMUM_Y_AMOUNT (err u5003))
```

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L9)

### ERR_NO_ACTIVE_BIN_DATA





```clarity
(define-constant ERR_NO_ACTIVE_BIN_DATA (err u5004))
```

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L10)

### ERR_EMPTY_POSITIONS_LIST





```clarity
(define-constant ERR_EMPTY_POSITIONS_LIST (err u5005))
```

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L11)

### ERR_RESULTS_LIST_OVERFLOW





```clarity
(define-constant ERR_RESULTS_LIST_OVERFLOW (err u5006))
```

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L12)

### ERR_INVALID_BIN_ID





```clarity
(define-constant ERR_INVALID_BIN_ID (err u5007))
```

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L13)

### ERR_ACTIVE_BIN_TOLERANCE





```clarity
(define-constant ERR_ACTIVE_BIN_TOLERANCE (err u5008))
```

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L14)

### MIN_BIN_ID



Minimum and maximum bin IDs as signed ints

```clarity
(define-constant MIN_BIN_ID -500)
```

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L17)

### MAX_BIN_ID





```clarity
(define-constant MAX_BIN_ID 500)
```

[View in file](../clarity/contracts/dlmm-liquidity-router-v-1-1.clar#L18)
  