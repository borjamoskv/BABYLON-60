
# token-stx-v-1-1

[`token-stx-v-1-1.clar`](../clarity/contracts/external/token-stx-v-1-1.clar)

token-stx-v-1-1

**Public functions:**

- [`set-token-uri`](#set-token-uri)
- [`set-contract-owner`](#set-contract-owner)
- [`transfer`](#transfer)

**Read-only functions:**

- [`get-name`](#get-name)
- [`get-symbol`](#get-symbol)
- [`get-decimals`](#get-decimals)
- [`get-total-supply`](#get-total-supply)
- [`get-balance`](#get-balance)
- [`get-token-uri`](#get-token-uri)
- [`get-contract-owner`](#get-contract-owner)

**Private functions:**



**Maps**



**Variables**

- [`token-uri`](#token-uri)
- [`contract-owner`](#contract-owner)

**Constants**

- [`ERR_NOT_AUTHORIZED_SIP_010`](#err_not_authorized_sip_010)
- [`ERR_INVALID_PRINCIPAL_SIP_010`](#err_invalid_principal_sip_010)
- [`ERR_NOT_AUTHORIZED`](#err_not_authorized)
- [`ERR_INVALID_AMOUNT`](#err_invalid_amount)
- [`ERR_INVALID_PRINCIPAL`](#err_invalid_principal)
- [`ERR_INVALID_TOKEN_URI`](#err_invalid_token_uri)


## Functions

### get-name

[View in file](../clarity/contracts/external/token-stx-v-1-1.clar#L21)

`(define-read-only (get-name () (response (string-ascii 6) none))`

SIP 010 function to get token name

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-name)
  (ok "Stacks")
)
```
</details>




### get-symbol

[View in file](../clarity/contracts/external/token-stx-v-1-1.clar#L26)

`(define-read-only (get-symbol () (response (string-ascii 3) none))`

SIP 010 function to get token symbol

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-symbol)
  (ok "STX")
)
```
</details>




### get-decimals

[View in file](../clarity/contracts/external/token-stx-v-1-1.clar#L31)

`(define-read-only (get-decimals () (response uint none))`

SIP 010 function to get token decimals

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-decimals)
  (ok u6)
)
```
</details>




### get-total-supply

[View in file](../clarity/contracts/external/token-stx-v-1-1.clar#L36)

`(define-read-only (get-total-supply () (response uint none))`

SIP 010 function to get total token supply

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-total-supply)
  (ok stx-liquid-supply)
)
```
</details>




### get-balance

[View in file](../clarity/contracts/external/token-stx-v-1-1.clar#L41)

`(define-read-only (get-balance ((address principal)) (response uint none))`

SIP 010 function to get token balance for an address

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-balance (address principal))
  (ok (stx-get-balance address))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| address | principal |

### get-token-uri

[View in file](../clarity/contracts/external/token-stx-v-1-1.clar#L46)

`(define-read-only (get-token-uri () (response (optional (string-utf8 256)) none))`

Get current token uri

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-token-uri)
  (ok (some (var-get token-uri)))
)
```
</details>




### get-contract-owner

[View in file](../clarity/contracts/external/token-stx-v-1-1.clar#L51)

`(define-read-only (get-contract-owner () (response principal none))`

Get current contract owner

<details>
  <summary>Source code:</summary>

```clarity
(define-read-only (get-contract-owner)
  (ok (var-get contract-owner))
)
```
</details>




### set-token-uri

[View in file](../clarity/contracts/external/token-stx-v-1-1.clar#L56)

`(define-public (set-token-uri ((uri (string-utf8 256))) (response bool uint))`

Set token uri

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-token-uri (uri (string-utf8 256)))
  (let (
    (caller tx-sender)
  )
    (begin
      ;; Assert that caller is contract-owner and uri length is greater than 0
      (asserts! (is-eq caller (var-get contract-owner)) ERR_NOT_AUTHORIZED)
      (asserts! (> (len uri) u0) ERR_INVALID_TOKEN_URI)
      (var-set token-uri uri)

      ;; Print function data and return true
      (print {action: "set-token-uri", caller: caller, data: {uri: uri}})
      (ok true)
    )
  )
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| uri | (string-utf8 256) |

### set-contract-owner

[View in file](../clarity/contracts/external/token-stx-v-1-1.clar#L74)

`(define-public (set-contract-owner ((address principal)) (response bool uint))`

Set contract owner

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-contract-owner (address principal))
  (let (
    (caller tx-sender)
  )
    (begin
      ;; Assert that caller is contract-owner
      (asserts! (is-eq caller (var-get contract-owner)) ERR_NOT_AUTHORIZED)
      (asserts! (is-standard address) ERR_INVALID_PRINCIPAL)
      (var-set contract-owner address)

      ;; Print function data and return true
      (print {action: "set-contract-owner", caller: caller, data: {address: address}})
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

### transfer

[View in file](../clarity/contracts/external/token-stx-v-1-1.clar#L92)

`(define-public (transfer ((amount uint) (sender principal) (recipient principal) (memo (optional (buff 34)))) (response bool uint))`

SIP 010 transfer function that transfers native STX tokens

<details>
  <summary>Source code:</summary>

```clarity
(define-public (transfer 
    (amount uint)
    (sender principal) (recipient principal)
    (memo (optional (buff 34)))
  )
  (let (
    (caller tx-sender)
  )
    (begin
      ;; Assert that caller is sender and addresses are standard principals
      (asserts! (is-eq caller sender) ERR_NOT_AUTHORIZED_SIP_010)
      (asserts! (is-standard sender) ERR_INVALID_PRINCIPAL_SIP_010)
      (asserts! (is-standard recipient) ERR_INVALID_PRINCIPAL_SIP_010)
      
      ;; Try performing a STX token transfer and print memo
      (try! (stx-transfer? amount sender recipient))
      (match memo to-print (print to-print) 0x)

      ;; Print function data and return true
      (print {
        action: "transfer",
        caller: caller,
        data: {
          sender: sender,
          recipient: recipient,
          amount: amount,
          memo: memo
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
| amount | uint |
| sender | principal |
| recipient | principal |
| memo | (optional (buff 34)) |

## Maps



## Variables

### token-uri

(string-utf8 256)

Uri for this token 

```clarity
(define-data-var token-uri (string-utf8 256) u"")
```

[View in file](../clarity/contracts/external/token-stx-v-1-1.clar#L15)

### contract-owner

principal

Contract owner defined as a var

```clarity
(define-data-var contract-owner principal tx-sender)
```

[View in file](../clarity/contracts/external/token-stx-v-1-1.clar#L18)

## Constants

### ERR_NOT_AUTHORIZED_SIP_010



Error constants

```clarity
(define-constant ERR_NOT_AUTHORIZED_SIP_010 (err u4))
```

[View in file](../clarity/contracts/external/token-stx-v-1-1.clar#L7)

### ERR_INVALID_PRINCIPAL_SIP_010





```clarity
(define-constant ERR_INVALID_PRINCIPAL_SIP_010 (err u5))
```

[View in file](../clarity/contracts/external/token-stx-v-1-1.clar#L8)

### ERR_NOT_AUTHORIZED





```clarity
(define-constant ERR_NOT_AUTHORIZED (err u5001))
```

[View in file](../clarity/contracts/external/token-stx-v-1-1.clar#L9)

### ERR_INVALID_AMOUNT





```clarity
(define-constant ERR_INVALID_AMOUNT (err u5002))
```

[View in file](../clarity/contracts/external/token-stx-v-1-1.clar#L10)

### ERR_INVALID_PRINCIPAL





```clarity
(define-constant ERR_INVALID_PRINCIPAL (err u5003))
```

[View in file](../clarity/contracts/external/token-stx-v-1-1.clar#L11)

### ERR_INVALID_TOKEN_URI





```clarity
(define-constant ERR_INVALID_TOKEN_URI (err u5004))
```

[View in file](../clarity/contracts/external/token-stx-v-1-1.clar#L12)
  