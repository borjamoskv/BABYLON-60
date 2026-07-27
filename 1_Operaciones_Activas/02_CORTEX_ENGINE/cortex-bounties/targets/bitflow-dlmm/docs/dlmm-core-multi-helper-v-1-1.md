
# dlmm-core-multi-helper-v-1-1

[`dlmm-core-multi-helper-v-1-1.clar`](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar)

dlmm-core-multi-helper-v-1-1

**Public functions:**

- [`migrate-core-address-multi`](#migrate-core-address-multi)
- [`set-swap-fee-exemption-multi`](#set-swap-fee-exemption-multi)
- [`claim-protocol-fees-multi`](#claim-protocol-fees-multi)
- [`set-pool-uri-multi`](#set-pool-uri-multi)
- [`set-pool-status-multi`](#set-pool-status-multi)
- [`set-variable-fees-manager-multi`](#set-variable-fees-manager-multi)
- [`set-fee-address-multi`](#set-fee-address-multi)
- [`set-variable-fees-multi`](#set-variable-fees-multi)
- [`set-x-fees-multi`](#set-x-fees-multi)
- [`set-y-fees-multi`](#set-y-fees-multi)
- [`set-variable-fees-cooldown-multi`](#set-variable-fees-cooldown-multi)
- [`set-freeze-variable-fees-manager-multi`](#set-freeze-variable-fees-manager-multi)
- [`reset-variable-fees-multi`](#reset-variable-fees-multi)
- [`set-dynamic-config-multi`](#set-dynamic-config-multi)

**Read-only functions:**



**Private functions:**

- [`migrate-core-address`](#migrate-core-address)
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
- [`reset-variable-fees`](#reset-variable-fees)
- [`set-dynamic-config`](#set-dynamic-config)

**Maps**



**Variables**



**Constants**




## Functions

### migrate-core-address-multi

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L8)

`(define-public (migrate-core-address-multi ((pool-traits (list 120 trait_reference))) (response (list 120 (response bool uint)) none))`

Migrate core address for multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-public (migrate-core-address-multi (pool-traits (list 120 <dlmm-pool-trait>)))
  (ok (map migrate-core-address pool-traits))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-traits | (list 120 trait_reference) |

### set-swap-fee-exemption-multi

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L13)

`(define-public (set-swap-fee-exemption-multi ((pool-traits (list 120 trait_reference)) (addresses (list 120 principal)) (exempts (list 120 bool))) (response (list 120 (response bool uint)) none))`

Set swap fee exemption for multiple addresses across multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-swap-fee-exemption-multi
    (pool-traits (list 120 <dlmm-pool-trait>))
    (addresses (list 120 principal))
    (exempts (list 120 bool))
  )
  (ok (map set-swap-fee-exemption pool-traits addresses exempts))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-traits | (list 120 trait_reference) |
| addresses | (list 120 principal) |
| exempts | (list 120 bool) |

### claim-protocol-fees-multi

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L22)

`(define-public (claim-protocol-fees-multi ((pool-traits (list 120 trait_reference)) (x-token-traits (list 120 trait_reference)) (y-token-traits (list 120 trait_reference))) (response (list 120 (response bool uint)) none))`

Claim protocol fees for multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-public (claim-protocol-fees-multi
    (pool-traits (list 120 <dlmm-pool-trait>))
    (x-token-traits (list 120 <sip-010-trait>))
    (y-token-traits (list 120 <sip-010-trait>))
  )
  (ok (map claim-protocol-fees pool-traits x-token-traits y-token-traits))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-traits | (list 120 trait_reference) |
| x-token-traits | (list 120 trait_reference) |
| y-token-traits | (list 120 trait_reference) |

### set-pool-uri-multi

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L31)

`(define-public (set-pool-uri-multi ((pool-traits (list 120 trait_reference)) (uris (list 120 (string-ascii 256)))) (response (list 120 (response bool uint)) none))`

Set pool uri for multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-pool-uri-multi
    (pool-traits (list 120 <dlmm-pool-trait>))
    (uris (list 120 (string-ascii 256)))
  )
  (ok (map set-pool-uri pool-traits uris))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-traits | (list 120 trait_reference) |
| uris | (list 120 (string-ascii 256)) |

### set-pool-status-multi

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L39)

`(define-public (set-pool-status-multi ((pool-traits (list 120 trait_reference)) (statuses (list 120 bool))) (response (list 120 (response bool uint)) none))`

Set pool status for multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-pool-status-multi
    (pool-traits (list 120 <dlmm-pool-trait>))
    (statuses (list 120 bool))
  )
  (ok (map set-pool-status pool-traits statuses))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-traits | (list 120 trait_reference) |
| statuses | (list 120 bool) |

### set-variable-fees-manager-multi

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L47)

`(define-public (set-variable-fees-manager-multi ((pool-traits (list 120 trait_reference)) (managers (list 120 principal))) (response (list 120 (response bool uint)) none))`

Set variable fees manager for multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-variable-fees-manager-multi
    (pool-traits (list 120 <dlmm-pool-trait>))
    (managers (list 120 principal))
  )
  (ok (map set-variable-fees-manager pool-traits managers))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-traits | (list 120 trait_reference) |
| managers | (list 120 principal) |

### set-fee-address-multi

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L55)

`(define-public (set-fee-address-multi ((pool-traits (list 120 trait_reference)) (addresses (list 120 principal))) (response (list 120 (response bool uint)) none))`

Set fee address for multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-fee-address-multi
    (pool-traits (list 120 <dlmm-pool-trait>))
    (addresses (list 120 principal))
  )
  (ok (map set-fee-address pool-traits addresses))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-traits | (list 120 trait_reference) |
| addresses | (list 120 principal) |

### set-variable-fees-multi

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L63)

`(define-public (set-variable-fees-multi ((pool-traits (list 120 trait_reference)) (x-fees (list 120 uint)) (y-fees (list 120 uint))) (response (list 120 (response bool uint)) none))`

Set variable fees for multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-variable-fees-multi
    (pool-traits (list 120 <dlmm-pool-trait>))
    (x-fees (list 120 uint))
    (y-fees (list 120 uint))
  )
  (ok (map set-variable-fees pool-traits x-fees y-fees))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-traits | (list 120 trait_reference) |
| x-fees | (list 120 uint) |
| y-fees | (list 120 uint) |

### set-x-fees-multi

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L72)

`(define-public (set-x-fees-multi ((pool-traits (list 120 trait_reference)) (protocol-fees (list 120 uint)) (provider-fees (list 120 uint))) (response (list 120 (response bool uint)) none))`

Set x fees for multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-x-fees-multi
    (pool-traits (list 120 <dlmm-pool-trait>))
    (protocol-fees (list 120 uint))
    (provider-fees (list 120 uint))
  )
  (ok (map set-x-fees pool-traits protocol-fees provider-fees))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-traits | (list 120 trait_reference) |
| protocol-fees | (list 120 uint) |
| provider-fees | (list 120 uint) |

### set-y-fees-multi

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L81)

`(define-public (set-y-fees-multi ((pool-traits (list 120 trait_reference)) (protocol-fees (list 120 uint)) (provider-fees (list 120 uint))) (response (list 120 (response bool uint)) none))`

Set y fees for multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-y-fees-multi
    (pool-traits (list 120 <dlmm-pool-trait>))
    (protocol-fees (list 120 uint))
    (provider-fees (list 120 uint))
  )
  (ok (map set-y-fees pool-traits protocol-fees provider-fees))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-traits | (list 120 trait_reference) |
| protocol-fees | (list 120 uint) |
| provider-fees | (list 120 uint) |

### set-variable-fees-cooldown-multi

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L90)

`(define-public (set-variable-fees-cooldown-multi ((pool-traits (list 120 trait_reference)) (cooldowns (list 120 uint))) (response (list 120 (response bool uint)) none))`

Set variable fees cooldown for multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-variable-fees-cooldown-multi
    (pool-traits (list 120 <dlmm-pool-trait>))
    (cooldowns (list 120 uint))
  )
  (ok (map set-variable-fees-cooldown pool-traits cooldowns))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-traits | (list 120 trait_reference) |
| cooldowns | (list 120 uint) |

### set-freeze-variable-fees-manager-multi

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L98)

`(define-public (set-freeze-variable-fees-manager-multi ((pool-traits (list 120 trait_reference))) (response (list 120 (response bool uint)) none))`

Set freeze variable fees manager for multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-freeze-variable-fees-manager-multi (pool-traits (list 120 <dlmm-pool-trait>)))
  (ok (map set-freeze-variable-fees-manager pool-traits))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-traits | (list 120 trait_reference) |

### reset-variable-fees-multi

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L103)

`(define-public (reset-variable-fees-multi ((pool-traits (list 120 trait_reference))) (response (list 120 (response bool uint)) none))`

Reset variable fees for multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-public (reset-variable-fees-multi (pool-traits (list 120 <dlmm-pool-trait>)))
  (ok (map reset-variable-fees pool-traits))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-traits | (list 120 trait_reference) |

### set-dynamic-config-multi

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L108)

`(define-public (set-dynamic-config-multi ((pool-traits (list 120 trait_reference)) (configs (list 120 (buff 4096)))) (response (list 120 (response bool uint)) none))`

Set dynamic config for multiple pools

<details>
  <summary>Source code:</summary>

```clarity
(define-public (set-dynamic-config-multi
    (pool-traits (list 120 <dlmm-pool-trait>))
    (configs (list 120 (buff 4096)))
  )
  (ok (map set-dynamic-config pool-traits configs))
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-traits | (list 120 trait_reference) |
| configs | (list 120 (buff 4096)) |

### migrate-core-address

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L116)

`(define-private (migrate-core-address ((pool-trait trait_reference)) (response bool uint))`

Private function to call migrate-core-address via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-private (migrate-core-address (pool-trait <dlmm-pool-trait>))
  (contract-call? .dlmm-core-v-1-1 migrate-core-address pool-trait)
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-trait | trait_reference |

### set-swap-fee-exemption

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L121)

`(define-private (set-swap-fee-exemption ((pool-trait trait_reference) (address principal) (exempt bool)) (response bool uint))`

Private function to call set-swap-fee-exemption via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-private (set-swap-fee-exemption (pool-trait <dlmm-pool-trait>) (address principal) (exempt bool))
  (contract-call? .dlmm-core-v-1-1 set-swap-fee-exemption pool-trait address exempt)
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

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L126)

`(define-private (claim-protocol-fees ((pool-trait trait_reference) (x-token-trait trait_reference) (y-token-trait trait_reference)) (response bool uint))`

Private function to call claim-protocol-fees via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-private (claim-protocol-fees (pool-trait <dlmm-pool-trait>) (x-token-trait <sip-010-trait>) (y-token-trait <sip-010-trait>))
  (contract-call? .dlmm-core-v-1-1 claim-protocol-fees pool-trait x-token-trait y-token-trait)
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

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L131)

`(define-private (set-pool-uri ((pool-trait trait_reference) (uri (string-ascii 256))) (response bool uint))`

Private function to call set-pool-uri via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-private (set-pool-uri (pool-trait <dlmm-pool-trait>) (uri (string-ascii 256)))
  (contract-call? .dlmm-core-v-1-1 set-pool-uri pool-trait uri)
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-trait | trait_reference |
| uri | (string-ascii 256) |

### set-pool-status

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L136)

`(define-private (set-pool-status ((pool-trait trait_reference) (status bool)) (response bool uint))`

Private function to call set-pool-status via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-private (set-pool-status (pool-trait <dlmm-pool-trait>) (status bool))
  (contract-call? .dlmm-core-v-1-1 set-pool-status pool-trait status)
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-trait | trait_reference |
| status | bool |

### set-variable-fees-manager

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L141)

`(define-private (set-variable-fees-manager ((pool-trait trait_reference) (manager principal)) (response bool uint))`

Private function to call set-variable-fees-manager via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-private (set-variable-fees-manager (pool-trait <dlmm-pool-trait>) (manager principal))
  (contract-call? .dlmm-core-v-1-1 set-variable-fees-manager pool-trait manager)
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-trait | trait_reference |
| manager | principal |

### set-fee-address

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L146)

`(define-private (set-fee-address ((pool-trait trait_reference) (address principal)) (response bool uint))`

Private function to call set-fee-address via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-private (set-fee-address (pool-trait <dlmm-pool-trait>) (address principal))
  (contract-call? .dlmm-core-v-1-1 set-fee-address pool-trait address)
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-trait | trait_reference |
| address | principal |

### set-variable-fees

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L151)

`(define-private (set-variable-fees ((pool-trait trait_reference) (x-fee uint) (y-fee uint)) (response bool uint))`

Private function to call set-variable-fees via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-private (set-variable-fees (pool-trait <dlmm-pool-trait>) (x-fee uint) (y-fee uint))
  (contract-call? .dlmm-core-v-1-1 set-variable-fees pool-trait x-fee y-fee)
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

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L156)

`(define-private (set-x-fees ((pool-trait trait_reference) (protocol-fee uint) (provider-fee uint)) (response bool uint))`

Private function to call set-x-fees via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-private (set-x-fees (pool-trait <dlmm-pool-trait>) (protocol-fee uint) (provider-fee uint))
  (contract-call? .dlmm-core-v-1-1 set-x-fees pool-trait protocol-fee provider-fee)
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

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L161)

`(define-private (set-y-fees ((pool-trait trait_reference) (protocol-fee uint) (provider-fee uint)) (response bool uint))`

Private function to call set-y-fees via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-private (set-y-fees (pool-trait <dlmm-pool-trait>) (protocol-fee uint) (provider-fee uint))
  (contract-call? .dlmm-core-v-1-1 set-y-fees pool-trait protocol-fee provider-fee)
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

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L166)

`(define-private (set-variable-fees-cooldown ((pool-trait trait_reference) (cooldown uint)) (response bool uint))`

Private function to call set-variable-fees-cooldown via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-private (set-variable-fees-cooldown (pool-trait <dlmm-pool-trait>) (cooldown uint))
  (contract-call? .dlmm-core-v-1-1 set-variable-fees-cooldown pool-trait cooldown)
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-trait | trait_reference |
| cooldown | uint |

### set-freeze-variable-fees-manager

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L171)

`(define-private (set-freeze-variable-fees-manager ((pool-trait trait_reference)) (response bool uint))`

Private function to call set-freeze-variable-fees-manager via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-private (set-freeze-variable-fees-manager (pool-trait <dlmm-pool-trait>))
  (contract-call? .dlmm-core-v-1-1 set-freeze-variable-fees-manager pool-trait)
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-trait | trait_reference |

### reset-variable-fees

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L176)

`(define-private (reset-variable-fees ((pool-trait trait_reference)) (response bool uint))`

Private function to call reset-variable-fees via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-private (reset-variable-fees (pool-trait <dlmm-pool-trait>))
  (contract-call? .dlmm-core-v-1-1 reset-variable-fees pool-trait)
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-trait | trait_reference |

### set-dynamic-config

[View in file](../clarity/contracts/dlmm-core-multi-helper-v-1-1.clar#L181)

`(define-private (set-dynamic-config ((pool-trait trait_reference) (config (buff 4096))) (response bool uint))`

Private function to call set-dynamic-config via DLMM Core

<details>
  <summary>Source code:</summary>

```clarity
(define-private (set-dynamic-config (pool-trait <dlmm-pool-trait>) (config (buff 4096)))
  (contract-call? .dlmm-core-v-1-1 set-dynamic-config pool-trait config)
)
```
</details>


**Parameters:**

| Name | Type | 
| --- | --- | 
| pool-trait | trait_reference |
| config | (buff 4096) |

## Maps



## Variables



## Constants


  