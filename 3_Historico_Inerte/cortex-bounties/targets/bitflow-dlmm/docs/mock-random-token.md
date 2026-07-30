
# mock-random-token

[`mock-random-token.clar`](../clarity/contracts/mocks/mock-random-token.clar)

Mock random Token

This token is NOT whitelisted in the system and is used for negative testing

**Public functions:**

- [`transfer`](#transfer)
- [`mint`](#mint)
- [`burn`](#burn)

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

- [`token-name`](#token-name)
- [`token-symbol`](#token-symbol)
- [`token-uri`](#token-uri)
- [`token-decimals`](#token-decimals)

**Constants**

- [`ERR_NOT_AUTHORIZED`](#err_not_authorized)
- [`ERR_INVALID_AMOUNT`](#err_invalid_amount)
- [`ERR_INVALID_PRINCIPAL`](#err_invalid_principal)


## Functions

### get-name

[View in file](../clarity/contracts/mocks/mock-random-token.clar#L21)

`(define-read-only (get-name () (response (string-ascii 32) none))`

SIP-010 functions

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-name)
  (ok (var-get token-name)))
```
</details>




### get-symbol

[View in file](../clarity/contracts/mocks/mock-random-token.clar#L24)

`(define-read-only (get-symbol () (response (string-ascii 32) none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-symbol)
  (ok (var-get token-symbol)))
```
</details>




### get-decimals

[View in file](../clarity/contracts/mocks/mock-random-token.clar#L27)

`(define-read-only (get-decimals () (response uint none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-decimals)
  (ok (var-get token-decimals)))
```
</details>




### get-balance

[View in file](../clarity/contracts/mocks/mock-random-token.clar#L30)

`(define-read-only (get-balance ((user principal)) (response uint none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-balance (user principal))
  (ok (ft-get-balance random-token user)))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| user | principal |

### get-total-supply

[View in file](../clarity/contracts/mocks/mock-random-token.clar#L33)

`(define-read-only (get-total-supply () (response uint none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-total-supply)
  (ok (ft-get-supply random-token)))
```
</details>




### get-token-uri

[View in file](../clarity/contracts/mocks/mock-random-token.clar#L36)

`(define-read-only (get-token-uri () (response (optional (string-utf8 256)) none))`



<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-token-uri)
  (ok (var-get token-uri)))
```
</details>




### transfer

[View in file](../clarity/contracts/mocks/mock-random-token.clar#L40)

`(define-public (transfer ((amount uint) (sender principal) (recipient principal) (memo (optional (buff 34)))) (response bool uint))`

Transfer function

<details>
  <summary>Source code:</summary>

```clarity
(define-public (transfer (amount uint) (sender principal) (recipient principal) (memo (optional (buff 34))))
  (begin
    (asserts! (is-eq sender tx-sender) ERR_NOT_AUTHORIZED)
    (asserts! (> amount u0) ERR_INVALID_AMOUNT)
    (asserts! (not (is-eq sender recipient)) ERR_INVALID_PRINCIPAL)
    (try! (ft-transfer? random-token amount sender recipient))
    (match memo to-print (print to-print) 0x)
    (ok true)))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| amount | uint |
| sender | principal |
| recipient | principal |
| memo | (optional (buff 34)) |

### mint

[View in file](../clarity/contracts/mocks/mock-random-token.clar#L50)

`(define-public (mint ((amount uint) (recipient principal)) (response bool uint))`

Mint function - anyone can mint for testing

<details>
  <summary>Source code:</summary>

```clarity
(define-public (mint (amount uint) (recipient principal))
  (begin
    (asserts! (> amount u0) ERR_INVALID_AMOUNT)
    (asserts! (is-standard recipient) ERR_INVALID_PRINCIPAL)
    (ft-mint? random-token amount recipient)))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| amount | uint |
| recipient | principal |

### burn

[View in file](../clarity/contracts/mocks/mock-random-token.clar#L57)

`(define-public (burn ((amount uint) (owner principal)) (response bool uint))`

Burn function

<details>
  <summary>Source code:</summary>

```clarity
(define-public (burn (amount uint) (owner principal))
  (begin
    (asserts! (is-eq owner tx-sender) ERR_NOT_AUTHORIZED)
    (asserts! (> amount u0) ERR_INVALID_AMOUNT)
    (ft-burn? random-token amount owner)))
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| amount | uint |
| owner | principal |

## Maps



## Variables

### token-name

(string-ascii 32)

Token metadata

```clarity
(define-data-var token-name (string-ascii 32) "random Token")
```

[View in file](../clarity/contracts/mocks/mock-random-token.clar#L15)

### token-symbol

(string-ascii 32)



```clarity
(define-data-var token-symbol (string-ascii 32) "UNWL")
```

[View in file](../clarity/contracts/mocks/mock-random-token.clar#L16)

### token-uri

(optional (string-utf8 256))



```clarity
(define-data-var token-uri (optional (string-utf8 256)) (some u"https://random.token"))
```

[View in file](../clarity/contracts/mocks/mock-random-token.clar#L17)

### token-decimals

uint



```clarity
(define-data-var token-decimals uint u6)
```

[View in file](../clarity/contracts/mocks/mock-random-token.clar#L18)

## Constants

### ERR_NOT_AUTHORIZED



Error constants

```clarity
(define-constant ERR_NOT_AUTHORIZED (err u1))
```

[View in file](../clarity/contracts/mocks/mock-random-token.clar#L10)

### ERR_INVALID_AMOUNT





```clarity
(define-constant ERR_INVALID_AMOUNT (err u2))
```

[View in file](../clarity/contracts/mocks/mock-random-token.clar#L11)

### ERR_INVALID_PRINCIPAL





```clarity
(define-constant ERR_INVALID_PRINCIPAL (err u3))
```

[View in file](../clarity/contracts/mocks/mock-random-token.clar#L12)
  