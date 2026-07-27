use crate::storage;
use crate::types::AllowanceData;
use crate::error::TokenError;
use soroban_sdk::{contract, contractimpl, panic_with_error, symbol_short, Address, Env, String};

/// Standard SEP-41 compliant token contract for underlying assets (USDC, USDT, XLM)
/// Implements the SEP-41 token interface expected by the lending pool
#[contract]
pub struct TokenContract;

/// Standard SEP-41 token interface implementation
#[contractimpl]
impl TokenContract {
    /// Returns the allowance for `spender` to transfer from `from`.
    pub fn allowance(env: Env, from: Address, spender: Address) -> i128 {
        let allowance = storage::get_allowance(&env, &from, &spender);
        if env.ledger().sequence() < allowance.expiration_ledger {
            allowance.amount
        } else {
            0
        }
    }

    /// Set the allowance by `amount` for `spender` to transfer/burn from `from`.
    pub fn approve(
        env: Env,
        from: Address,
        spender: Address,
        amount: i128,
        expiration_ledger: u32,
    ) {
        from.require_auth();

        if amount < 0 {
            panic_with_error!(&env, TokenError::InvalidAmount);
        }

        let allowance_data = AllowanceData {
            amount,
            expiration_ledger,
        };

        storage::set_allowance(&env, &from, &spender, &allowance_data);

        env.events().publish(
            (symbol_short!("approve"), from, spender),
            (amount, expiration_ledger),
        );
    }

    /// Returns the balance of `id`.
    pub fn balance(env: Env, id: Address) -> i128 {
        storage::get_balance(&env, &id)
    }

    /// Transfer `amount` from `from` to `to`.
    pub fn transfer(env: Env, from: Address, to: Address, amount: i128) {
        from.require_auth();

        if amount < 0 {
            panic_with_error!(&env, TokenError::InvalidAmount);
        }

        // WP-C6: self-transfer would overwrite the debit with the credit, inflating balance
        if from == to {
            return;
        }

        let from_balance = Self::balance(env.clone(), from.clone());
        if from_balance < amount {
            panic_with_error!(&env, TokenError::InsufficientBalance);
        }

        let to_balance = Self::balance(env.clone(), to.clone());

        let new_from_balance = from_balance.checked_sub(amount)
            .unwrap_or_else(|| panic_with_error!(&env, TokenError::InsufficientBalance));
        let new_to_balance = to_balance.checked_add(amount)
            .unwrap_or_else(|| panic_with_error!(&env, TokenError::InvalidAmount));

        storage::set_balance(&env, &from, &new_from_balance);
        storage::set_balance(&env, &to, &new_to_balance);

        env.events()
            .publish((symbol_short!("transfer"), from, to), amount);
    }

    /// Transfer `amount` from `from` to `to`, consuming the allowance that `spender` has on `from`'s balance.
    pub fn transfer_from(env: Env, spender: Address, from: Address, to: Address, amount: i128) {
        spender.require_auth();

        if amount < 0 {
            panic_with_error!(&env, TokenError::InvalidAmount);
        }

        let mut allowance = storage::get_allowance(&env, &from, &spender);

        if env.ledger().sequence() >= allowance.expiration_ledger {
            panic_with_error!(&env, TokenError::InsufficientAllowance);
        }

        if allowance.amount < amount {
            panic_with_error!(&env, TokenError::InsufficientAllowance);
        }

        allowance.amount = allowance.amount.checked_sub(amount)
            .unwrap_or_else(|| panic_with_error!(&env, TokenError::InsufficientAllowance));
        storage::set_allowance(&env, &from, &spender, &allowance);

        // WP-C6: self-transfer would overwrite the debit with the credit, inflating balance.
        // Allowance already consumed above to prevent spender budget bypass.
        if from == to {
            return;
        }

        let from_balance = Self::balance(env.clone(), from.clone());
        if from_balance < amount {
            panic_with_error!(&env, TokenError::InsufficientBalance);
        }

        let to_balance = Self::balance(env.clone(), to.clone());

        let new_from_balance = from_balance.checked_sub(amount)
            .unwrap_or_else(|| panic_with_error!(&env, TokenError::InsufficientBalance));
        let new_to_balance = to_balance.checked_add(amount)
            .unwrap_or_else(|| panic_with_error!(&env, TokenError::InvalidAmount));

        storage::set_balance(&env, &from, &new_from_balance);
        storage::set_balance(&env, &to, &new_to_balance);

        env.events()
            .publish((symbol_short!("transfer"), from, to), amount);
    }

    /// Burn `amount` from `from`.
    pub fn burn(env: Env, from: Address, amount: i128) {
        from.require_auth();

        if amount < 0 {
            panic_with_error!(&env, TokenError::InvalidAmount);
        }

        let from_balance = Self::balance(env.clone(), from.clone());
        if from_balance < amount {
            panic_with_error!(&env, TokenError::InsufficientBalance);
        }

        let new_balance = from_balance - amount;
        storage::set_balance(&env, &from, &new_balance);

        env.events().publish((symbol_short!("burn"), from), amount);
    }

    /// Burn `amount` from `from`, consuming the allowance of `spender`.
    pub fn burn_from(env: Env, spender: Address, from: Address, amount: i128) {
        spender.require_auth();

        if amount < 0 {
            panic_with_error!(&env, TokenError::InvalidAmount);
        }

        let mut allowance = storage::get_allowance(&env, &from, &spender);

        if env.ledger().sequence() >= allowance.expiration_ledger {
            panic_with_error!(&env, TokenError::InsufficientAllowance);
        }

        if allowance.amount < amount {
            panic_with_error!(&env, TokenError::InsufficientAllowance);
        }

        allowance.amount = allowance.amount.checked_sub(amount)
            .unwrap_or_else(|| panic_with_error!(&env, TokenError::InsufficientAllowance));
        storage::set_allowance(&env, &from, &spender, &allowance);

        let from_balance = Self::balance(env.clone(), from.clone());
        if from_balance < amount {
            panic_with_error!(&env, TokenError::InsufficientBalance);
        }

        let new_balance = from_balance.checked_sub(amount)
            .unwrap_or_else(|| panic_with_error!(&env, TokenError::InsufficientBalance));
        storage::set_balance(&env, &from, &new_balance);

        env.events().publish((symbol_short!("burn"), from), amount);
    }

    /// Returns the number of decimals used to represent amounts of this token.
    pub fn decimals(env: Env) -> u32 {
        storage::get_decimals(&env).unwrap_or_else(|e| panic_with_error!(&env, e))
    }

    /// Returns the name for this token.
    pub fn name(env: Env) -> String {
        storage::get_name(&env).unwrap_or_else(|e| panic_with_error!(&env, e))
    }

    /// Returns the symbol for this token.
    pub fn symbol(env: Env) -> String {
        storage::get_symbol(&env).unwrap_or_else(|e| panic_with_error!(&env, e))
    }

    /// Atomic constructor to bind admin and metadata at deployment time.
    /// This prevents the first-caller takeover vulnerability (#44834).
    pub fn __constructor(env: Env, admin: Address, name: String, symbol: String, decimals: u32) {
        if storage::has_admin(&env) {
            panic_with_error!(&env, TokenError::AlreadyInitialized);
        }
        storage::set_admin(&env, &admin);
        storage::set_name(&env, &name);
        storage::set_symbol(&env, &symbol);
        storage::set_decimals(&env, decimals);
    }

    /// Legacy initialize function, now disabled to enforce constructor-based binding.
    pub fn initialize(env: Env, _admin: Address, _name: String, _symbol: String, _decimals: u32) {
        panic_with_error!(&env, TokenError::AlreadyInitialized);
    }

    /// Mint tokens (admin only)
    pub fn mint(env: Env, to: Address, amount: i128) {
        // Admin authorization required for minting
        let admin = storage::get_admin(&env).unwrap_or_else(|_| {
            panic_with_error!(&env, TokenError::Unauthorized)
        });
        admin.require_auth();

        if amount <= 0 {
            panic_with_error!(&env, TokenError::InvalidAmount);
        }

        let current_balance = Self::balance(env.clone(), to.clone());
        let new_balance = current_balance.checked_add(amount)
            .unwrap_or_else(|| panic_with_error!(&env, TokenError::InvalidAmount));

        storage::set_balance(&env, &to, &new_balance);

        env.events().publish((symbol_short!("mint"), to), amount);
    }

    /// Get admin address
    pub fn admin(env: Env) -> Address {
        storage::get_admin(&env).unwrap_or_else(|e| panic_with_error!(&env, e))
    }

    /// Set admin address (admin only)
    pub fn set_admin(env: Env, new_admin: Address) {
        let admin = storage::get_admin(&env).unwrap_or_else(|e| panic_with_error!(&env, e));
        admin.require_auth();

        storage::set_admin(&env, &new_admin);
    }
}
