# DLMM Contract Architecture

## 1. Contracts

### Core
- `dlmm-core-v-1-1`
- `dlmm-pool-trait-v-1-1`
- `dlmm-pool-sbtc-usdc-v-1-1` (example pool)
- `dlmm-swap-router-v-1-1`
- `dlmm-liquidity-router-v-1-1`
- `dlmm-staking-trait-v-1-1`
- `dlmm-staking-sbtc-usdc-v-1-1`

### External
- `sip-010-trait-ft-standard-v-1-1`
- `sip-013-trait-sft-standard-v-1-1`
- `sip-013-transfer-many-trait-v-1-1`
- `token-stx-v-1-1`

## 2. dlmm-core-v-1-1

### Traits
- `dlmm-pool-trait-v-1-1` (use)
- `sip-010-trait-ft-standard-v-1-1` (use)

### Constants
- Core error codes
- `CONTRACT_DEPLOYER` (`tx-sender`)
- `NUM_OF_BINS` (`u1001`)
- `CENTER_BIN_ID` (`(/ NUM_OF_BINS u2)`)
- `MIN_BIN_ID` (`-500`)
- `MAX_BIN_ID` (`500`)
- `FEE_SCALE_BPS` (`u10000`)
- `PRICE_SCALE_BPS` (`u100000000`)

### Data Variables

#### Admin-Configurable
Set via public admin functions
- `admins` (`(list 5 principal)`): List of principals with admin permissions
- `bin-steps` (`(list 1000 uint)`): List of allowed bin steps (initial: 1, 5, 10, and 20)
- `bin-factors` (`(list 1001 uint)`): List of factors for calculating bin price based on bin step
- `minimum-bin-shares` (`uint`): Minimum shares to mint when creating a pool
- `minimum-burnt-shares` (`uint`): Minimum shares to burn when creating a pool
- `public-pool-creation` (`bool`): Allow pool creation by anyone or admins only
- `verified-pool-code-hashes` (`(list 10000 (buff 32))`): List of verified pool code hashes

#### Indirectly Modified
Updated as a side-effect of other functions
- `admin-helper` (`principal`): Helper variable for removing an admin
- `last-pool-id` (`uint`): ID of last created pool

### Mappings
- `pools` (`uint {id: uint, name: (string-ascii 32), symbol: (string-ascii 32), pool-contract: principal, verified: bool, status: bool}`)
- `allowed-token-direction` (`{x-token: principal, y-token: principal} bool`)
- `unclaimed-protocol-fees` (`uint {x-fee: uint, y-fee: uint}`)
- `swap-fee-exemptions` (`{address: principal, id: uint} bool`)

### Admin Functions
Follows the same design as XYK Core

#### Read-only
- `get-admins`: Returns `admins`
- `get-admin-helper`: Returns `admin-helper`

#### Public
- `add-admin`: Add principal to `admins` (admin-only)
  - Parameters: `(admin principal)`
- `remove-admin`: Remove principal from `admins` (admin-only)
  - Parameters: `(admin principal)`

#### Private
- `admin-not-removable`: Helper for removing a principal from `admins`
  - Parameters: `(admin principal)`

### Pool Management Functions
Manage or retrieve data about pools

#### Read-only
- `get-last-pool-id`: Returns `last-pool-id`
- `get-pool-by-id`: Returns data about a pool from `pools` mapping
  - Parameters: `(id uint)`
- `get-allowed-token-direction`: Returns if token direction exists or is allowed for pool creation
  - Parameters: `(x-token principal) (y-token principal)`
- `get-unclaimed-protocol-fees-by-id`: Returns unclaimed protocol fees for a pool
  - Parameters: `(id uint)`
- `get-swap-fee-exemption-by-id`: Returns swap fee exemption for an address for a pool
  - Parameters: `(address principal) (id uint)`

#### Public
- `claim-protocol-fees`: Claim protocol fees for a pool
  - Parameters: `(pool-trait <dlmm-pool-trait>) (x-token-trait <sip-010-trait>) (y-token-trait <sip-010-trait>)`
- `set-pool-uri`: Set URI for a pool (admin-only)
  - Parameters: `(pool-trait <dlmm-pool-trait>) (uri (string-ascii 256))`
- `set-pool-status`: Set pool status (admin-only)
  - Parameters: `(pool-trait <dlmm-pool-trait>) (status bool)`
- `set-fee-address`: Set fee address (admin-only)
  - Parameters: `(pool-trait <dlmm-pool-trait>) (address principal)`
- `set-x-fees`: Set X protocol and provider fees (admin-only)
  - Parameters: `(pool-trait <dlmm-pool-trait>) (protocol-fee uint) (provider-fee uint)`
- `set-y-fees`: Set Y protocol and provider fees (admin-only)
  - Parameters: `(pool-trait <dlmm-pool-trait>) (protocol-fee uint) (provider-fee uint)`
- `set-dynamic-config`: Set dynamic config for a pool (admin and manager-only)
  - Parameters: `(pool-trait <dlmm-pool-trait>) (config (buff 4096))`
- `claim-protocol-fees-multi`: Batch version of `claim-protocol-fees` (120 max)
  - Parameters: `(pool-traits (list 120 <dlmm-pool-trait>)) (x-token-traits (list 120 <sip-010-trait>)) (y-token-traits (list 120 <sip-010-trait>))`
- `set-pool-uri-multi`: Batch version of `set-pool-uri` (120 max)
  - Parameters: `(pool-traits (list 120 <dlmm-pool-trait>)) (uris (list 120 (string-ascii 256)))`
- `set-pool-status-multi`: Batch version of `set-pool-status` (120 max)
  - Parameters: `(pool-traits (list 120 <dlmm-pool-trait>)) (statuses (list 120 bool))`
- `set-fee-address-multi`: Batch version of `set-fee-address` (120 max)
  - Parameters: `(pool-traits (list 120 <dlmm-pool-trait>)) (addresses (list 120 principal))`
- `set-x-fees-multi`: Batch version of `set-x-fees` (120 max)
  - Parameters: `(pool-traits (list 120 <dlmm-pool-trait>)) (protocol-fees (list 120 uint)) (provider-fees (list 120 uint))`
- `set-y-fees-multi`: Batch version of `set-y-fees` (120 max)
  - Parameters: `(pool-traits (list 120 <dlmm-pool-trait>)) (protocol-fees (list 120 uint)) (provider-fees (list 120 uint))`
- `set-dynamic-config-multi`: Batch version of `set-dynamic-config` (120 max)
  - Parameters: `(pool-traits (list 120 <dlmm-pool-trait>)) (configs (list 120 (buff 4096)))`

#### Private
- `is-valid-pool`: Check the validity of a pool
  - Parameters: `(id uint) (contract principal)`
- `is-enabled-pool`: Check the status of a pool
  - Parameters: `(id uint)`

### Core Management Functions
Manage or retrieve data about the core contract

#### Read-only
- `get-bin-steps`: Returns `bin-steps`
- `get-bin-factors-by-step`: Returns list of factors based on bin step
  - Parameters: `(step uint)`
- `get-minimum-bin-shares`: Returns `minimum-bin-shares`
- `get-minimum-burnt-shares`: Returns `minimum-burnt-shares`
- `get-public-pool-creation`: Returns `public-pool-creation`
- `get-verified-pool-code-hashes`: Returns `verified-pool-code-hashes`
- `get-unsigned-bin-id`: Returns bin ID as unsigned int
  - Parameters: `(bin-id int)`
- `get-signed-bin-id`: Returns bin ID as signed int
  - Parameters: `(bin-id uint)`
- `get-bin-price`: Returns price at bin
  - Parameters: `(initial-price uint) (bin-step uint) (bin-id int)`
- `get-liquidity-value`: Returns rebased liquidity value when adding liquidity to a bin
  - Parameters: `(x-amount uint) (y-amount uint) (bin-price uint)`

#### Public
- `add-bin-step`: Add bin step to `bin-steps` and its list of factors (admin-only)
  - Parameters: `(step uint) (factors (list 1001 uint))`
- `set-minimum-shares`: Set minimum bin and burnt shares (admin-only)
  - Parameters: `(min-bin uint) (min-burnt uint)`
- `set-public-pool-creation`: Enable or disable public pool creation (admin-only)
  - Parameters: `(status bool)`
- `add-verified-pool-code-hash`: Add pool code hash to `verified-pool-code-hashes` (admin-only)
  - Parameters: `(hash (buff 32))`
- `set-swap-fee-exemption`: Set swap fee exemption for an address for a pool (admin-only)
  - Parameters: `(pool-trait <dlmm-pool-trait>) (address principal) (exempt bool)`

### Pool Creation Functions
Create new pools

#### Public
- `create-pool`: Create a new pool (admin-only when `public-pool-creation` is false)
  - Parameters: `(pool-trait <dlmm-pool-trait>) (x-token-trait <sip-010-trait>) (y-token-trait <sip-010-trait>) (x-amount-active-bin uint) (y-amount-active-bin uint) (burn-amount-active-bin uint) (x-protocol-fee uint) (x-provider-fee uint) (y-protocol-fee uint) (y-provider-fee uint) (bin-step uint) (variable-fees-cooldown uint) (freeze-variable-fees-manager bool) (fee-address principal) (uri (string-ascii 256)) (status bool)`  
  _If `public-pool-creation` is `true`, anyone can create pools. Otherwise, only admins can create pools_

#### Private
- `create-symbol`: Create pool symbol using token symbols
  - Parameters: `(x-token-trait <sip-010-trait>) (y-token-trait <sip-010-trait>)`

### Swap Functions
Swap using a single bin in a pool

#### Public
- `swap-x-for-y`: Swap token X → Y
  - Parameters: `(pool-trait  <dlmm-pool-trait>) (x-token-trait <sip-010-trait>) (y-token-trait <sip-010-trait>) (bin-id int) (x-amount uint)`
- `swap-y-for-x`: Swap token Y → X
  - Parameters: `(pool-trait  <dlmm-pool-trait>) (x-token-trait <sip-010-trait>) (y-token-trait <sip-010-trait>) (bin-id int) (y-amount uint)`

### Liquidity Functions
Add or withdraw liquidity using a single bin in a pool

#### Public
- `add-liquidity`: Add liquidity (single-sided for non-active bins)
  - Parameters: `(pool-trait <dlmm-pool-trait>) (x-token-trait <sip-010-trait>) (y-token-trait <sip-010-trait>) (bin-id int) (x-amount uint) (y-amount uint) (min-dlp uint)`
- `withdraw-liquidity`: Withdraw proportional liquidity
  - Parameters: `(pool-trait <dlmm-pool-trait>) (x-token-trait <sip-010-trait>) (y-token-trait <sip-010-trait>) (bin-id int) (amount uint) (min-x-amount uint) (min-y-amount uint)`
- `move-liquidity`: Move liquidity from one bin to another
  - Parameters: `(pool-trait <dlmm-pool-trait>) (x-token-trait <sip-010-trait>) (y-token-trait <sip-010-trait>) (from-bin-id int) (to-bin-id int) (amount uint) (min-dlp uint)`

### Variable Fees Functions
Manage or retrieve data about variable fees for a single bin in a pool 

#### Public
- `set-variable-fees-manager`: Set variable fees manager (admin-only)
  - Parameters: `(pool-trait <dlmm-pool-trait>) (manager principal)`
- `set-variable-fees`: Set variable fees (admin and manager-only)
  - Parameters: `(pool-trait <dlmm-pool-trait>) (x-fee uint) (y-fee uint)`
- `set-variable-fees-cooldown`: Set the cooldown period (Stacks blocks) for resetting variable fees (admin-only)
  - Parameters: `(pool-trait <dlmm-pool-trait>) (cooldown uint)`
- `set-freeze-variable-fees-manager`: Freeze the variable fees manager address (admin-only)
  - Parameters: `(pool-trait <dlmm-pool-trait>)`
- `reset-variable-fees`: Reset variable fees if the cooldown period has passed
  - Parameters: `(pool-trait <dlmm-pool-trait>)`
- `set-variable-fees-multi`: Batch version of `set-variable-fees` (120 max)
  - Parameters: `(pool-traits (list 120 <dlmm-pool-trait>)) (x-fees (list 120 uint)) (y-fees (list 120 uint))`
- `set-variable-fees-manager-multi`: Batch version of `set-variable-fees-manager` (120 max)
  - Parameters: `(pool-traits (list 120 <dlmm-pool-trait>)) (managers (list 120 principal))`
- `set-variable-fees-cooldown-multi`: Batch version of `set-variable-fees-cooldown` (120 max)
  - Parameters: `(pool-traits (list 120 <dlmm-pool-trait>)) (cooldowns (list 120 uint))`
- `set-freeze-variable-fees-manager-multi`: Batch version of `set-freeze-variable-fees-manager` (120 max)
  - Parameters: `(pool-traits (list 120 <dlmm-pool-trait>))`

## 3. dlmm-pool-trait-v-1-1

### Traits
- `sip-010-trait-ft-standard-v-1-1` (use)
- `dlmm-pool-trait` (define)

### Trait Definition
- `get-name`: () (response (string-ascii 32) uint)
- `get-symbol`: () (response (string-ascii 32) uint)
- `get-decimals`: (uint) (response uint uint)
- `get-token-uri`: (uint) (response (optional (string-ascii 256)) uint)
- `get-total-supply`: (uint) (response uint uint)
- `get-overall-supply`: () (response uint uint)
- `get-balance`: (uint principal) (response uint uint)
- `get-overall-balance`: (principal) (response uint uint)
- `get-pool`: () (response {pool-id: uint, pool-name: (string-ascii 32), pool-symbol: (string-ascii 32), pool-uri: (string-ascii 256), pool-created: bool, creation-height: uint, core-address: principal, variable-fees-manager: principal, fee-address: principal, x-token: principal, y-token: principal, pool-token: principal, bin-step: uint, initial-price: uint, active-bin-id: int, x-protocol-fee: uint, x-provider-fee: uint, x-variable-fee: uint, y-protocol-fee: uint, y-provider-fee: uint, y-variable-fee: uint, bin-change-count: uint, last-variable-fees-update: uint, variable-fees-cooldown: uint, freeze-variable-fees-manager: bool, dynamic-config: (buff 4096)} uint)
- `get-pool-for-swap`: (bool) (response {pool-id: uint, pool-name: (string-ascii 32), fee-address: principal, x-token: principal, y-token: principal, bin-step: uint, initial-price: uint, active-bin-id: int, protocol-fee: uint, provider-fee: uint, variable-fee: uint} uint)
- `get-pool-for-add`: () (response {pool-id: uint, pool-name: (string-ascii 32), x-token: principal, y-token: principal, bin-step: uint, initial-price: uint, active-bin-id: int, x-protocol-fee: uint, x-provider-fee: uint, x-variable-fee: uint, y-protocol-fee: uint, y-provider-fee: uint, y-variable-fee: uint} uint)
- `get-pool-for-withdraw`: () (response {pool-id: uint, pool-name: (string-ascii 32), x-token: principal, y-token: principal} uint)
- `get-active-bin-id`: () (response int uint)
- `get-bin-balances`: (uint) (response {x-balance: uint, y-balance: uint, bin-shares: uint} uint)
- `get-user-bins`: (principal) (response (list 1001 uint) uint)
- `set-pool-uri`: ((string-ascii 256)) (response bool uint)
- `set-variable-fees-manager`: (principal) (response bool uint)
- `set-fee-address`: (principal) (response bool uint)  
- `set-active-bin-id`: (int) (response bool uint)
- `set-x-fees`: (uint uint) (response bool uint)
- `set-y-fees`: (uint uint) (response bool uint)
- `set-variable-fees`: (uint uint) (response bool uint)
- `set-variable-fees-cooldown`: (uint) (response bool uint)
- `set-freeze-variable-fees-manager`: () (response bool uint)
- `set-dynamic-config`: ((buff 4096)) (response bool uint)
- `update-bin-balances`: (uint uint uint) (response bool uint)
- `update-bin-balances-on-withdraw`: (uint uint uint uint) (response bool uint)
- `transfer`: (uint uint principal principal) (response bool uint)
- `transfer-memo`: (uint uint principal principal (buff 34)) (response bool uint)
- `transfer-many`: ((list 200 {token-id: uint, amount: uint, sender: principal, recipient: principal})) (response bool uint)
- `transfer-many-memo`: ((list 200 {token-id: uint, amount: uint, sender: principal, recipient: principal, memo: (buff 34)})) (response bool uint)
- `pool-transfer`: (\<sip-010-trait> uint principal) (response bool uint)
- `pool-mint`: (uint uint principal) (response bool uint)
- `pool-burn`: (uint uint principal) (response bool uint)
- `create-pool`: (principal principal principal principal principal int uint uint uint (string-ascii 32) (string-ascii 32) (string-ascii 256)) (response bool uint)

## 4. dlmm-pool-sbtc-usdc-v-1-1

### Traits
- `dlmm-pool-trait-v-1-1` (implement)
- `sip-013-trait-sft-standard-v-1-1` (implement)
- `sip-013-transfer-many-trait-v-1-1` (implement)
- `sip-010-trait-ft-standard-v-1-1` (use)

### Token Definitions
- `define-fungible-token pool-token`
- `define-non-fungible-token pool-token-id {token-id: uint, owner: principal}`

### Constants
- Pool and SIP 013 error codes
- `CORE_ADDRESS` (`.dlmm-core-v-1-1`)
- `CONTRACT_DEPLOYER` (`tx-sender`)

### Data Variables

#### Pool Creation
Set via the core contract only at pool creation
- `pool-id` (`uint`): ID of pool (`(+ last-pool-id u1)`) [set within `pool-info` mapping]
- `pool-name` (`string-ascii 32`): Pool and `pool-token` name [set within `pool-info` mapping]
- `pool-symbol` (`string-ascii 32`): Pool and `pool-token` symbol [set within `pool-info` mapping]
- `pool-created` (`bool`): Pool creation status [set within `pool-info` mapping]
- `creation-height` (`uint`): Burn block height when the pool was created [set within `pool-info` mapping]
- `x-token` (`principal`): X token principal [set within `pool-addresses` mapping]
- `y-token` (`principal`): Y token principal [set within `pool-addresses` mapping]
- `bin-step` (`uint`): Pool bin step
- `initial-price` (`uint`): Price of pool at initial active bin

#### Admin-Configurable
Set via the core contract using admin functions
- `pool-uri` (`string-ascii 256`): Pool and `pool-token` URI [set within `pool-info` mapping]
- `variable-fees-manager` (`principal`): Principal authorized to set variable fees [set within `pool-addresses` mapping]
- `fee-address` (`principal`): Principal to send protocol fees to [set within `pool-addresses` mapping]
- `x-protocol-fee` (`uint`): Protocol fee charged for protocol when swapping X → Y [set within `pool-fees` mapping]
- `x-provider-fee` (`uint`): Provider fee charged for providers when swapping X → Y [set within `pool-fees` mapping]
- `x-variable-fee` (`uint`): Variable fee charged for providers when swapping X → Y [set within `pool-fees` mapping]
- `y-protocol-fee` (`uint`): Protocol fee charged for protocol when swapping Y → X [set within `pool-fees` mapping]
- `y-provider-fee` (`uint`): Protocol fee charged for providers when swapping Y → X [set within `pool-fees` mapping]
- `y-variable-fee` (`uint`): Variable fee charged for providers when swapping Y → X [set within `pool-fees` mapping]
- `variable-fees-cooldown` (`uint`): Variable fees can be reset after this cooldown (Stacks blocks) is reached
- `freeze-variable-fees-manager` (`bool`): If `true`, `variable-fees-manager` is permanently frozen
- `dynamic-config` (`buff 4096`): Dynamic configuration initially used to calculate variable fees

#### Indirectly Modified
Updated as a side-effect of other functions
- `active-bin-id` (`int`): ID of the active bin
- `bin-change-count` (`uint`): Number of bin changes since last variable fees reset
- `last-variable-fees-update` (`uint`): Latest variable fees update (Stacks block)

### Mappings
- `balances-at-bin` (`uint {x-balance: uint, y-balance: uint, bin-shares: uint}`)
- `user-balance-at-bin` (`{id: uint, user: principal} uint`)
- `user-bins` (`principal (list 1001 uint)`)

### SIP 013 Functions
Interact or retrieve data about the `pool-token` and `pool-token-id` (SIP 013-compliant)

#### Read-only
- `get-name`: Returns `pool-name` from `pool-info` mapping
- `get-symbol`: Returns `pool-symbol` from `pool-info` mapping
- `get-decimals`: Returns `pool-token` decimals
  - Parameters: `(token-id uint)`
- `get-token-uri`: Returns `pool-uri` from `pool-info` mapping
  - Parameters: `(token-id uint)`
- `get-total-supply`: Returns total `pool-token` supply
  - Parameters: `(token-id uint)`
- `get-overall-supply`: Returns overall total `pool-token` supply
- `get-balance`: Returns `pool-token` balance for a principal at a bin
  - Parameters: `(token-id uint) (user principal)`
- `get-overall-balance`: Returns overall `pool-token` balance for a principal
  - Parameters: `(user principal)`

#### Public
- `transfer`: Transfer `pool-token` (single bin)
  - Parameters: `(token-id uint) (amount uint) (sender principal) (recipient principal)`
- `transfer-memo`: Transfer `pool-token` (single bin) with memo
  - Parameters: `(token-id uint) (amount uint) (sender principal) (recipient principal) (memo (buff 34))`
- `transfer-many`: Transfer many `pool-token` (different bins)
  - Parameters: `(transfers (list 200 {token-id: uint, amount: uint, sender: principal, recipient: principal}))`
- `transfer-many-memo`: Transfer many `pool-token` (different bins) with memo
  - Parameters: `(transfers (list 200 {token-id: uint, amount: uint, sender: principal, recipient: principal, memo: (buff 34)}))`

#### Private
- `fold-transfer-many`: Helper function for transferring many `pool-token`
- `fold-transfer-many-memo`: Helper function for transferring many `pool-token` with memo
- `get-balance-or-default`: Helper function to get user balance at a bin from `user-balance-at-bin` mapping or default
- `update-user-balance`: Update the `user-balance-at-bin` and `user-bins` mappings via the mint, burn, and transfer functions in pool
  - Parameters: `(id uint) (user principal) (balance uint)`
- `tag-pool-token-id`: Burn `pool-token-id` from one principal and mint to another
  - Parameters: `(id {token-id: uint, owner: principal})`

### Pool Management Functions
Manage or retrieve data about the pool contract

#### Read-only
- `get-pool`: Returns base pool data
- `get-pool-for-swap`: Returns pool data for swap functions in core
  - Parameters: `(is-x-for-y bool)`
- `get-pool-for-add`: Returns pool data for add and move liquidity functions in core
- `get-pool-for-withdraw`: Returns pool data for withdraw liquidity function in core
- `get-bin-balances`: Returns data about a bin from `balances-at-bin` mapping
  - Parameters: `(id uint)`
- `get-user-bins`: Returns list of user bins from `user-bins` mapping
  - Parameters: `(user principal)`

#### Public (callable by core only)
- `set-pool-uri`: Called via `set-pool-uri` in core
  - Parameters: `(uri (string-ascii 256))`
- `set-variable-fees-manager`: Called via `set-variable-fees-manager` in core
  - Parameters: `(manager principal)`
- `set-fee-address`: Called via `set-fee-address` in core
  - Parameters: `(address principal)`
- `set-active-bin-id`: Set current active bin via pool creation, swap, and liquidity functions in core
  - Parameters: `(id int)`
- `set-x-fees`: Called via `set-x-fees` in core
  - Parameters: `(protocol-fee uint) (provider-fee uint)`
- `set-y-fees`: Called via `set-y-fees` in core
  - Parameters: `(protocol-fee uint) (provider-fee uint)`
- `set-variable-fees`: Called via `set-variable-fees` in core
  - Parameters: `(x-fee uint) (y-fee uint)`
- `set-variable-fees-cooldown`: Called via `set-variable-fees-cooldown` in core
  - Parameters: `(cooldown uint)`
- `set-freeze-variable-fees-manager`: Called via `set-freeze-variable-fees-manager` in core
- `set-dynamic-config`: Called via `set-dynamic-config` in core
  - Parameters: `(config (buff 4096))`
- `update-bin-balances`: Update the `balances-at-bin` mapping via pool creation, swap, add and move liquidity functions in core
  - Parameters: `(bin-id uint) (x-balance uint) (y-balance uint)`
- `update-bin-balances-on-withdraw`: Update the `balances-at-bin` mapping via withdraw liquidity function in core
  - Parameters: `(bin-id uint) (x-balance uint) (y-balance uint) (bin-shares uint)`
- `pool-transfer`: Transfer X / Y token from the pool via swap and withdraw liquidity functions in core
  - Parameters: `(token-trait <sip-010-trait>) (amount uint) (recipient principal)`
- `pool-mint`: Mint new `pool-token` via pool creation and add liquidity functions in core
  - Parameters: `(id uint) (amount uint) (user principal)`
- `pool-burn`: Burn existing `pool-token` via `withdraw-liquidity` in core
  - Parameters: `(id uint) (amount uint) (user principal)`
- `create-pool`: Called via `create-pool` in core
  - Parameters: `(x-token-contract principal) (y-token-contract principal) (variable-fees-mgr principal) (fee-addr principal) (core-caller principal) (active-bin int) (step uint) (price uint) (id uint) (name (string-ascii 32)) (symbol (string-ascii 32)) (uri (string-ascii 256))`
 
## 5. dlmm-swap-router-v-1-1

### Constants
- Router error codes

### Traits
- `dlmm-pool-trait-v-1-1` (use)
- `sip-010-trait-ft-standard-v-1-1` (use)

### Swap Functions
Swap using a single or multiple bins in a single or multiple pools

#### Public
- `swap-multi`: Swap tokens (350 max)
  - Parameters: `(swaps (list 350 {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, expected-bin-id: int, amount: uint, x-for-y: bool})) (min-received uint) (max-unfavorable-bins uint)`

#### Private
- `fold-swap-multi`: Used to batch swap calls via core
  - Parameters: `(swap {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, expected-bin-id: int, amount: uint, x-for-y: bool}) (result (response {received: uint, unfavorable: uint} uint))`
- `abs-int`: Returns absolute value of a signed int as uint
  - Parameters: `(value int)`

## 6. dlmm-liquidity-router-v-1-1

### Constants
- Router error codes

### Traits
- `dlmm-pool-trait-v-1-1` (use)
- `sip-010-trait-ft-standard-v-1-1` (use)

### Liquidity Functions
Add or withdraw liquidity using a single or multiple bins in a single or multiple pools

#### Public
- `add-liquidity-multi`: Add liquidity (single-sided for non-active bins) (350 max)
  - Parameters: `(positions (list 350 {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, bin-id: int, x-amount: uint, y-amount: uint})) (min-dlp uint)`
- `add-relative-liquidity-multi`: Add liquidity (single-sided for non-active bins) relative to the active bin (350 max)
  - Parameters: `(positions (list 350 {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, active-bin-id-offset: int, x-amount: uint, y-amount: uint})) (min-dlp uint)`
- `withdraw-liquidity-multi`: Withdraw proportional liquidity (350 max)
  - Parameters: `(positions (list 350 {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, bin-id: int, amount: uint})) (min-x-amount uint) (min-y-amount uint)`
- `withdraw-relative-liquidity-multi`: Withdraw proportional liquidity relative to the active bin (350 max)
  - Parameters: `(positions (list 350 {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, active-bin-id-offset: int, amount: uint})) (min-x-amount uint) (min-y-amount uint)`
- `move-liquidity-multi`: Move liquidity from one bin to another (350 max)
  - Parameters: `(positions (list 350 {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, from-bin-id: int, to-bin-id: int, amount: uint})) (min-dlp uint)`
- `move-relative-liquidity-multi`: Move liquidity from one bin to another relative to the active bin (350 max)
  - Parameters: `(positions (list 350 {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, from-bin-id: int, active-bin-id-offset: int, amount: uint})) (min-dlp uint)`

#### Private
- `fold-add-liquidity-multi`: Used to batch `add-liquidity` calls via core
  - Parameters: `(position {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, bin-id: int, x-amount: uint, y-amount: uint}) (result (response uint uint))`
- `fold-add-relative-liquidity-multi`: Used to batch `add-liquidity` calls via core
  - Parameters: `(position {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, active-bin-id-offset: int, x-amount: uint, y-amount: uint}) (result (response uint uint))`
- `fold-withdraw-liquidity-multi`: Used to batch `withdraw-liquidity` calls via core
  - Parameters: `(position {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, bin-id: int, amount: uint}) (result (response {x-amount: uint, y-amount: uint} uint))`
- `fold-withdraw-relative-liquidity-multi`: Used to batch `withdraw-liquidity` calls via core
  - Parameters: `(position {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, active-bin-id-offset: int, amount: uint}) (result (response {x-amount: uint, y-amount: uint} uint))`
- `fold-move-liquidity-multi`: Used to batch `move-liquidity` calls via core
  - Parameters: `(position {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, from-bin-id: int, to-bin-id: int, amount: uint}) (result (response uint uint))`
- `fold-move-relative-liquidity-multi`: Used to batch `move-liquidity` calls via core
  - Parameters: `(position {pool-trait: <dlmm-pool-trait>, x-token-trait: <sip-010-trait>, y-token-trait: <sip-010-trait>, from-bin-id: int, active-bin-id-offset: int, amount: uint}) (result (response uint uint))`

## 7. dlmm-staking-trait-v-1-1

### Trait Definition
- `get-helper-value`: () (response uint uint)
- `get-staking-status`: () (response bool uint)
- `get-early-unstake-status`: () (response bool uint)
- `get-early-unstake-fee-address`: () (response principal uint)
- `get-early-unstake-fee`: () (response uint uint)
- `get-minimum-staking-duration`: () (response uint uint)
- `get-total-lp-staked`: () (response uint uint)
- `get-total-rewards-per-block`: () (response uint uint)
- `get-total-rewards-claimed`: () (response uint uint)
- `get-total-rewards-accrued`: () (response uint uint)
- `get-last-total-rewards-accrued-update`: () (response uint uint)
- `get-bin`: (uint) (response (optional {lp-staked: uint, reward-per-block: uint, reward-index: uint, last-reward-index-update: uint}) uint)
- `get-user`: (principal) (response (optional {bins-staked: (list 1001 uint), lp-staked: uint}) uint)
- `get-user-data-at-bin`: (principal uint) (response (optional {lp-staked: uint, reward-index: uint, last-stake-height: uint}) uint)
- `get-updated-reward-index`: (uint) (response {reward-index: uint, rewards-to-distribute: uint} uint)
- `get-unclaimed-rewards`: (principal int) (response uint uint)
- `get-available-contract-balance`: () (response uint uint)
- `stake-lp-tokens`: (int uint) (response bool uint)
- `unstake-lp-tokens`: (int) (response bool uint)
- `early-unstake-lp-tokens`: (int) (response bool uint)
- `claim-rewards`: (int) (response uint uint)
- `update-reward-index`: (uint) (response bool uint)

## 8. dlmm-staking-sbtc-usdc-v-1-1

### Traits
- `dlmm-staking-trait-v-1-1` (implement)

### Constants
- Staking error codes
- `CONTRACT_DEPLOYER` (`tx-sender`)
- `NUM_OF_BINS` (`u1001`)
- `CENTER_BIN_ID` (`(/ NUM_OF_BINS u2)`)
- `MIN_REWARD_BUFFER_BLOCKS` (`u10000`)
- `FEE_SCALE_BPS` (`u10000`)
- `REWARD_SCALE_BPS` (`u1000000`)

### Data Variables

#### Admin-Configurable
Set via public admin functions
- `admins` (`(list 5 principal)`): List of principals with admin permissions
- `staking-status` (`bool`): Enable or disable staking
- `early-unstake-status` (`bool`): Enable or disable early unstaking
- `early-unstake-fee-address` (`principal`): Address that collects fees from early unstaking
- `early-unstake-fee` (`uint`): Fee charged when early unstaking
- `minimum-staking-duration` (`uint`): Minimum staking duration in blocks

#### Indirectly Modified
Updated as a side-effect of other functions
- `admin-helper` (`principal`): Helper variable for removing an admin
- `helper-value` (`uint`): Helper value used when unstaking
- `total-lp-staked` (`uint`): Total amount of LP tokens staked
- `total-rewards-per-block` (`uint`): Total amount of rewards per block
- `total-rewards-claimed` (`uint`): Total amount of rewards claimed
- `total-rewards-accrued` (`uint`): Total amount of rewards accrued
- `last-total-rewards-accrued-update` (`uint`): Block height when `total-rewards-accrued` was last updated

### Mappings
- `bin-data` (`uint {lp-staked: uint, reward-per-block: uint, reward-index: uint, last-reward-index-update: uint}`)
- `user-data` (`principal {bins-staked: (list 1001 uint), lp-staked: uint}`)
- `user-data-at-bin` (`{user: principal, bin-id: uint} {lp-staked: uint, reward-index: uint, last-stake-height: uint}`)

### Admin Functions
Follows the same design as XYK Core

#### Read-only
- `get-admins`: Returns `admins`
- `get-admin-helper`: Returns `admin-helper`

#### Public
- `add-admin`: Add principal to `admins` (admin-only)
  - Parameters: `(admin principal)`
- `remove-admin`: Remove principal from `admins` (admin-only)
  - Parameters: `(admin principal)`

#### Private
- `admin-not-removable`: Helper for removing a principal from `admins`
  - Parameters: `(admin principal)`

### Staking Management Functions
Manage or retrieve data about pools

#### Read-only
- `get-helper-value`: Returns `helper-value`
- `get-staking-status`: Returns `staking-status`
- `get-early-unstake-status`: Returns `early-unstake-status`
- `get-early-unstake-fee-address`: Returns `early-unstake-fee-address`
- `get-early-unstake-fee`: Returns `early-unstake-fee`
- `get-minimum-staking-duration`: Returns `minimum-staking-duration`
- `get-total-lp-staked`: Returns `total-lp-staked`
- `get-total-rewards-per-block`: Returns `total-rewards-per-block`
- `get-total-rewards-claimed`: Returns `total-rewards-claimed`
- `get-total-rewards-accrued`: Returns `total-rewards-accrued`
- `get-last-total-rewards-accrued-update`: Returns `last-total-rewards-accrued-update`
- `get-bin`: Returns data about a bin from the `bin-data` mapping
  - Parameters: `(bin-id uint)`
- `get-user`: Returns data about a user from the `user-data` mapping
  - Parameters: `(user principal)`
- `get-user-data-at-bin`: Returns data about a user at a bin from the `user-data-at-bin` mapping
  - Parameters: `(user principal) (bin-id uint)`
- `get-updated-reward-index`: Returns updated reward index at a bin
  - Parameters: `(bin-id uint)`
- `get-available-contract-balance`: Returns available contract balance after subtracting the reserved balance

#### Public
- `set-staking-status`: Set status for staking (admin-only)
  - Parameters: `(status bool)`
- `set-early-unstake-status`: Set status for early unstaking (admin-only)
  - Parameters: `(status bool)`
- `set-early-unstake-fee-address`: Set fee address for early unstaking fee (admin-only)
  - Parameters: `(address principal)`
- `set-early-unstake-fee`: Set fee taken when early unstaking (admin-only)
  - Parameters: `(fee uint)`
- `set-minimum-staking-duration`: Set minimum required staking duration in blocks (admin-only)
  - Parameters: `(duration uint)`
- `set-reward-per-block`: Set reward per block for a bin (admin-only)
  - Parameters: `(bin-id uint) (reward uint)`
- `withdraw-rewards`: Withdraw reward token from contract (admin-only)
  - Parameters: `(amount uint) (recipient principal)`
- `update-reward-index`: Update reward index for a bin
  - Parameters: `(bin-id uint)`
- `set-reward-per-block-multi`: Batch version of `set-reward-per-block` (350 max)
  - Parameters: `(bin-ids (list 350 uint)) (amounts (list 350 uint))`
- `update-reward-index-multi`: Batch version of `update-reward-index` (350 max)
  - Parameters: `(bin-ids (list 350 uint))`

#### Private
- `filter-values-eq-helper-value`: Filter function used when unstaking
  - Parameters: `(value uint)`
- `get-reward-token-balance`: Get reward token balance for contract
- `transfer-lp-token`: Transfer the LP token
  - Parameters: `(bin-id uint) (amount uint) (sender principal) (recipient principal)`
- `transfer-reward-token`: Transfer the reward token
  - Parameters: `(amount uint) (sender principal) (recipient principal)`

### Staking Functions

#### Read-only
- `get-unclaimed-rewards`: Returns unclaimed rewards for a user at a bin
  - Parameters: `(user principal) (bin-id int)`

#### Public
- `stake-lp-tokens`: Stake LP tokens for a bin
  - Parameters: `(bin-id int) (amount uint)`
- `unstake-lp-tokens`: Unstake LP tokens for a bin
  - Parameters: `(bin-id int)`
- `early-unstake-lp-tokens`: Early unstake LP tokens for a bin
  - Parameters: `(bin-id int)`
- `claim-rewards`: Claim any unclaimed rewards at a bin
  - Parameters: `(bin-id int)`
- `get-unclaimed-rewards-multi`: Batch version of `get-unclaimed-rewards` (350 max)
  - Parameters: `(users (list 350 principal)) (bin-ids (list 350 int))`
- `stake-lp-tokens-multi`: Batch version of `stake-lp-tokens` (350 max)
  - Parameters: `(bin-ids (list 350 int)) (amounts (list 350 uint))`
- `unstake-lp-tokens-multi`: Batch version of `unstake-lp-tokens` (350 max)
  - Parameters: `(bin-ids (list 350 int))`
- `early-unstake-lp-tokens-multi`: Batch version of `early-unstake-lp-tokens` (350 max)
  - Parameters: `(bin-ids (list 350 int))`
- `claim-rewards-multi`: Batch version of `claim-rewards` (350 max)
  - Parameters: `(bin-ids (list 350 int))`