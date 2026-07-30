
# mock-sbtc-token

[`mock-sbtc-token.clar`](../clarity/contracts/mocks/mock-sbtc-token.clar)

Mock sBTC token for testing

**Public functions:**

- [`transfer`](#transfer)
- [`mint`](#mint)

**Read-only functions:**

- [`get-name`](#get-name)
- [`get-symbol`](#get-symbol)
- [`get-decimals`](#get-decimals)
- [`get-balance`](#get-balance)
- [`get-total-supply`](#get-total-supply)
- [`get-token-uri`](#get-token-uri)

**Private functions:**



**Maps**



**Variables**



**Constants**

- [`contract-owner`](#contract-owner)
- [`err-owner-only`](#err-owner-only)
- [`err-not-token-owner`](#err-not-token-owner)
- [`err-insufficient-balance`](#err-insufficient-balance)


## Functions

### transfer

[View in file](../clarity/contracts/mocks/mock-sbtc-token.clar#L12)

`(define-public (transfer ((amount uint) (from principal) (to principal) (memo (optional (buff 34)))) (response bool uint))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (transfer (amount uint) (from principal) (to principal) (memo (optional (buff 34))))
  (begin
    (asserts! (or (is-eq tx-sender from) (is-eq contract-caller from)) err-not-token-owner)
    (ft-transfer? sbtc amount from to)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| amount | uint |
| from | principal |
| to | principal |
| memo | (optional (buff 34)) |

### get-name

[View in file](../clarity/contracts/mocks/mock-sbtc-token.clar#L19)

`(define-read-only (get-name () (response (string-ascii 9) none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-name)
  (ok "Mock sBTC")
)
```
</details>




### get-symbol

[View in file](../clarity/contracts/mocks/mock-sbtc-token.clar#L23)

`(define-read-only (get-symbol () (response (string-ascii 4) none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-symbol)
  (ok "SBTC")
)
```
</details>




### get-decimals

[View in file](../clarity/contracts/mocks/mock-sbtc-token.clar#L27)

`(define-read-only (get-decimals () (response uint none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-decimals)
  (ok u8)
)
```
</details>




### get-balance

[View in file](../clarity/contracts/mocks/mock-sbtc-token.clar#L31)

`(define-read-only (get-balance ((who principal)) (response uint none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-balance (who principal))
  (ok (ft-get-balance sbtc who))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| who | principal |

### get-total-supply

[View in file](../clarity/contracts/mocks/mock-sbtc-token.clar#L35)

`(define-read-only (get-total-supply () (response uint none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-total-supply)
  (ok (ft-get-supply sbtc))
)
```
</details>




### get-token-uri

[View in file](../clarity/contracts/mocks/mock-sbtc-token.clar#L39)

`(define-read-only (get-token-uri () (response (optional none) none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-token-uri)
  (ok none)
)
```
</details>




### mint

[View in file](../clarity/contracts/mocks/mock-sbtc-token.clar#L43)

`(define-public (mint ((amount uint) (to principal)) (response bool uint))`



<details>
  <summary>Source code:</summary>

```clarity
(define-public (mint (amount uint) (to principal))
  (begin
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    (ft-mint? sbtc amount to)
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| amount | uint |
| to | principal |

## Maps



## Variables



## Constants

### contract-owner





```clarity
(define-constant contract-owner tx-sender)
```

[View in file](../clarity/contracts/mocks/mock-sbtc-token.clar#L6)

### err-owner-only





```clarity
(define-constant err-owner-only (err u100))
```

[View in file](../clarity/contracts/mocks/mock-sbtc-token.clar#L8)

### err-not-token-owner





```clarity
(define-constant err-not-token-owner (err u101))
```

[View in file](../clarity/contracts/mocks/mock-sbtc-token.clar#L9)

### err-insufficient-balance





```clarity
(define-constant err-insufficient-balance (err u102))
```

[View in file](../clarity/contracts/mocks/mock-sbtc-token.clar#L10)
  