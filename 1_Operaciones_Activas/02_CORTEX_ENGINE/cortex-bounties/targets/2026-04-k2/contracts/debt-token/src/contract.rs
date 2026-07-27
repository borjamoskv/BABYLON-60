use crate::balance;
use crate::storage;
use crate::storage::DebtTokenState;
use k2_shared::*;
use soroban_sdk::{
    contract, contractimpl, panic_with_error, symbol_short, Address, BytesN, Env, IntoVal, String, Symbol, Vec,
};

use k2_shared::safe_u128_to_i128;

#[contract]
pub struct DebtTokenContract;

#[contractimpl]
impl DebtTokenContract {
    pub fn allowance(_env: Env, _from: Address, _spender: Address) -> i128 {
        0
    }

    pub fn approve(
        _env: Env,
        _from: Address,
        _spender: Address,
        _amount: i128,
        _expiration_ledger: u32,
    ) -> Result<(), TokenError> {
        Err(TokenError::UnsupportedOperation)
    }

    pub fn balance(env: Env, id: Address) -> i128 {
        balance::balance_of(&env, &id).unwrap_or_else(|e| panic_with_error!(&env, e))
    }

    pub fn balance_of(env: Env, id: Address) -> i128 {
        balance::balance_of(&env, &id).unwrap_or_else(|e| panic_with_error!(&env, e))
    }

    pub fn balance_of_with_index(env: Env, id: Address, borrow_index: u128) -> i128 {
        balance::balance_of_with_index(&env, &id, borrow_index)
    }

    pub fn balance_of_with_borrow_index(env: Env, id: Address, borrow_index: u128) -> i128 {
        balance::balance_of_with_index(&env, &id, borrow_index)
    }

    pub fn transfer(
        _env: Env,
        _from: Address,
        _to: Address,
        _amount: i128,
    ) -> Result<(), TokenError> {
        Err(TokenError::UnsupportedOperation)
    }

    pub fn transfer_from(
        _env: Env,
        _spender: Address,
        _from: Address,
        _to: Address,
        _amount: i128,
    ) -> Result<(), TokenError> {
        Err(TokenError::UnsupportedOperation)
    }

    pub fn burn(
        _env: Env,
        _from: Address,
        _amount: i128,
    ) -> Result<(), TokenError> {
        Err(TokenError::UnsupportedOperation)
    }

    pub fn burn_from(
        _env: Env,
        _spender: Address,
        _from: Address,
        _amount: i128,
    ) -> Result<(), TokenError> {
        Err(TokenError::UnsupportedOperation)
    }

    pub fn decimals(env: Env) -> u32 {
        storage::get_state(&env).map(|s| s.decimals).unwrap_or_else(|e| panic_with_error!(&env, e))
    }

    pub fn name(env: Env) -> String {
        storage::get_state(&env).map(|s| s.name).unwrap_or_else(|e| panic_with_error!(&env, e))
    }

    pub fn symbol(env: Env) -> String {
        storage::get_state(&env).map(|s| s.symbol).unwrap_or_else(|e| panic_with_error!(&env, e))
    }

    pub fn total_supply(env: Env) -> i128 {
        balance::total_supply(&env).unwrap_or_else(|e| panic_with_error!(&env, e))
    }

    pub fn total_supply_with_index(env: Env, borrow_index: u128) -> i128 {
        balance::total_supply_with_index(&env, borrow_index).unwrap_or_else(|e| panic_with_error!(&env, e))
    }

    pub fn mint(
        _env: Env,
        _to: Address,
        _amount: i128,
    ) -> Result<(), TokenError> {
        Err(TokenError::UnsupportedOperation)
    }

    pub fn __constructor(
        env: Env,
        admin: Address,
        borrowed_asset: Address,
        pool: Address,
        name: String,
        symbol: String,
        decimals: u32,
    ) {
        if storage::has_state(&env) {
            panic!("Already initialized");
        }

        crate::upgrade::initialize_admin(&env, &admin);

        let state = DebtTokenState {
            borrowed_asset,
            pool_address: pool,
            total_debt_scaled: 0,
            name,
            symbol,
            decimals,
        };
        storage::set_state(&env, &state);
    }

    pub fn initialize(
        _env: Env,
        _admin: Address,
        _borrowed_asset: Address,
        _pool: Address,
        _name: String,
        _symbol: String,
        _decimals: u32,
    ) -> Result<(), TokenError> {
        panic!("Initialization is atomic at deployment. Use __constructor.");
    }

    pub fn set_incentives_contract(env: Env, caller: Address, incentives: Address) -> Result<(), TokenError> {
        caller.require_auth();
        let state = storage::get_state(&env)?;
        if caller != state.pool_address {
            return Err(TokenError::Unauthorized);
        }
        storage::set_incentives_contract(&env, &incentives);
        Ok(())
    }

    pub fn get_incentives_contract(env: Env) -> Option<Address> {
        storage::get_incentives_contract(&env)
    }

    /// Mint scaled debt tokens for a user.
    /// Returns (is_first_borrow, user_new_scaled_debt, total_debt_scaled).
    pub fn mint_scaled(
        env: Env,
        caller: Address,
        on_behalf_of: Address,
        amount: u128,
        index: u128,
    ) -> Result<(bool, i128, i128), TokenError> {
        caller.require_auth();
        let mut state = storage::get_state(&env)?;
        if caller != state.pool_address {
            return Err(TokenError::Unauthorized);
        }

        if amount == 0 {
            return Err(TokenError::InvalidAmount);
        }

        if index == 0 {
            return Err(TokenError::InvalidIndex);
        }

        // M-14
        let amount_scaled = ray_div_up(&env, amount, index).map_err(|_| TokenError::InvalidIndex)?;
        let current_scaled_debt = storage::get_scaled_debt(&env, &on_behalf_of);
        // WP-L3: Check actual debt before mint to determine if this is the first borrow
        let is_first_borrow = current_scaled_debt == 0;
        let new_scaled_debt = current_scaled_debt.checked_add(amount_scaled)
            .ok_or(TokenError::TransferFailed)?;
        storage::set_scaled_debt(&env, &on_behalf_of, new_scaled_debt);

        // F-19
        let amount_scaled_i128 = safe_u128_to_i128(&env, amount_scaled);
        let new_scaled_debt_i128 = safe_u128_to_i128(&env, new_scaled_debt);
        state.total_debt_scaled = state
            .total_debt_scaled
            .checked_add(amount_scaled_i128)
            .ok_or(TokenError::TransferFailed)?;
        let borrowed_asset = state.borrowed_asset.clone();
        let pool_address = state.pool_address.clone();
        storage::set_state(&env, &state);

        env.events().publish(
            (symbol_short!("mint"), on_behalf_of.clone()),
            (amount_scaled_i128, safe_u128_to_i128(&env, amount)),
        );

        // Update incentives after minting (borrow rewards)
        Self::handle_incentives_action(&env, &pool_address, &borrowed_asset, &on_behalf_of, 1)?;

        Ok((is_first_borrow, new_scaled_debt_i128, state.total_debt_scaled))
    }

    pub fn burn_scaled(
        env: Env,
        caller: Address,
        on_behalf_of: Address,
        amount: u128,
        index: u128,
    ) -> Result<(bool, i128, i128), TokenError> {
        caller.require_auth();
        let mut state = storage::get_state(&env)?;
        if !storage::is_authorized_caller(&env, &caller, &state.pool_address) {
            return Err(TokenError::Unauthorized);
        }

        if amount == 0 {
            return Err(TokenError::InvalidAmount);
        }

        if index == 0 {
            return Err(TokenError::InvalidIndex);
        }

        // M-14
        let mut amount_scaled = ray_div_down(&env, amount, index).map_err(|_| TokenError::InvalidIndex)?;
        let current_scaled_debt = storage::get_scaled_debt(&env, &on_behalf_of);

        if current_scaled_debt < amount_scaled {
            return Err(TokenError::InsufficientBalance);
        }

        let new_scaled_debt = current_scaled_debt.checked_sub(amount_scaled)
            .ok_or(TokenError::InsufficientBalance)?;

        // L-09
        // When ray_div_down(ray_mul(scaled, index), index) < scaled by 1 unit,
        // a tiny phantom debt remains. Force full burn if residual is dust (≤ 1).
        let final_user_scaled_debt;
        if new_scaled_debt <= 1 {
            amount_scaled = current_scaled_debt;
            storage::set_scaled_debt(&env, &on_behalf_of, 0);
            final_user_scaled_debt = 0i128;
        } else {
            storage::set_scaled_debt(&env, &on_behalf_of, new_scaled_debt);
            final_user_scaled_debt = safe_u128_to_i128(&env, new_scaled_debt);
        }

        // F-19
        let amount_scaled_i128 = safe_u128_to_i128(&env, amount_scaled);
        state.total_debt_scaled = state
            .total_debt_scaled
            .checked_sub(amount_scaled_i128)
            .ok_or(TokenError::TransferFailed)?;
        let borrowed_asset = state.borrowed_asset.clone();
        let pool_address = state.pool_address.clone();
        storage::set_state(&env, &state);

        // WP-L4: Derive actual amount from capped/adjusted scaled value, not raw `amount`
        let actual_amount = ray_mul(&env, amount_scaled, index)
            .map_err(|_| TokenError::InvalidIndex)?;
        env.events().publish(
            (symbol_short!("burn"), on_behalf_of.clone()),
            (amount_scaled_i128, safe_u128_to_i128(&env, actual_amount)),
        );

        // Update incentives after burning (borrow rewards)
        Self::handle_incentives_action(&env, &pool_address, &borrowed_asset, &on_behalf_of, 1)?;

        Ok((final_user_scaled_debt == 0, state.total_debt_scaled, final_user_scaled_debt))
    }

    // WP-L3: burn_with_index removed — zero callers, dead code.

    pub fn scaled_balance_of(env: Env, id: Address) -> u128 {
        storage::get_scaled_debt(&env, &id)
    }

    pub fn scaled_total_supply(env: Env) -> i128 {
        storage::get_state(&env).map(|s| s.total_debt_scaled).unwrap_or_else(|e| panic_with_error!(&env, e))
    }

    pub fn get_borrow_index(env: Env) -> u128 {
        let state = storage::get_state(&env).unwrap_or_else(|e| panic_with_error!(&env, e));
        let mut args = Vec::new(&env);
        args.push_back(state.borrowed_asset.to_val());

        // Call kinetic-router to get current variable borrow index (always up-to-date)
        let result = env.try_invoke_contract::<u128, KineticRouterError>(
            &state.pool_address,
            &Symbol::new(&env, "get_current_var_borrow_idx"),
            args,
        );

        match result {
            Ok(Ok(index)) => index,
            Ok(Err(_)) | Err(_) => panic_with_error!(&env, TokenError::InvalidIndex),
        }
    }

    pub fn get_borrowed_asset(env: Env) -> Address {
        storage::get_state(&env).map(|s| s.borrowed_asset).unwrap_or_else(|e| panic_with_error!(&env, e))
    }

    pub fn get_pool_address(env: Env) -> Address {
        storage::get_state(&env).map(|s| s.pool_address).unwrap_or_else(|e| panic_with_error!(&env, e))
    }

    /// Upgrade contract WASM (admin only)
    pub fn upgrade(env: Env, new_wasm_hash: BytesN<32>) -> Result<(), TokenError> {
        crate::upgrade::upgrade(env, new_wasm_hash).map_err(|_| TokenError::Unauthorized)
    }

    pub fn version(_env: Env) -> u32 {
        crate::upgrade::version()
    }

    pub fn get_admin(env: Env) -> Result<Address, TokenError> {
        crate::upgrade::get_admin(&env).map_err(|_| TokenError::Unauthorized)
    }

    fn handle_incentives_action(
        env: &Env,
        _pool_address: &Address,
        _borrowed_asset: &Address,
        user: &Address,
        reward_type: u32,
    ) -> Result<(), TokenError> {
        let incentives_contract = match storage::get_incentives_contract(env) {
            Some(addr) => addr,
            None => return Ok(()),
        };

        // Get scaled balances
        let user_balance = storage::get_scaled_debt(env, user);
        let state = storage::get_state(env)?;
        // S-04
        let total_supply = safe_i128_to_u128(env, state.total_debt_scaled);

        // Call incentives.handle_action
        // Asset is determined by token_address (this token contract), following Aave's pattern
        // If this token is not registered, the call is a no-op (safe for anyone to call)
        let mut args = Vec::new(env);
        args.push_back(env.current_contract_address().into_val(env)); // token_address (asset identifier)
        args.push_back(user.clone().into_val(env)); // user
        args.push_back(total_supply.into_val(env)); // total_supply
        args.push_back(user_balance.into_val(env)); // user_balance
        args.push_back(reward_type.into_val(env)); // reward_type

        // Try to call incentives contract, but ignore any errors
        // Rewards are optional and should not block core operations
        let result = env.try_invoke_contract::<(), TokenError>(
            &incentives_contract,
            &Symbol::new(env, "handle_action"),
            args,
        );
        
        // Emit event on failure for monitoring
        if result.is_err() {
            env.events().publish(
                (symbol_short!("inc_fail"), user.clone()),
                incentives_contract,
            );
        }
        Ok(())
    }
}
