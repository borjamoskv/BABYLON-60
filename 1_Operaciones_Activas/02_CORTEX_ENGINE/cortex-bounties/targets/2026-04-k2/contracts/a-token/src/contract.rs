use crate::balance;
use crate::storage;
use crate::storage::{ATokenState, AllowanceData};
use k2_shared::*;
use soroban_sdk::auth::{ContractContext, InvokerContractAuthEntry, SubContractInvocation};
use soroban_sdk::{
    contract, contractimpl, panic_with_error, symbol_short, Address, BytesN, Env, IntoVal, String, Symbol, Vec,
};

use k2_shared::safe_u128_to_i128;

#[contract]
pub struct ATokenContract;

#[contractimpl]
impl ATokenContract {
    pub fn allowance(env: Env, from: Address, spender: Address) -> i128 {
        if let Some(data) = storage::get_allowance(&env, &from, &spender) {
            if data.expiration_ledger >= env.ledger().sequence() {
                return data.amount;
            }
        }
        0
    }

    pub fn approve(
        env: Env,
        from: Address,
        spender: Address,
        amount: i128,
        expiration_ledger: u32,
    ) -> Result<(), TokenError> {
        from.require_auth();

        if amount < 0 {
            return Err(TokenError::InvalidAmount);
        }

        if amount > 0 && expiration_ledger < env.ledger().sequence() {
            return Err(TokenError::InvalidAmount);
        }

        // LOW-001: Block blacklisted parties from setting up allowances
        let state = storage::get_state(&env)?;
        Self::validate_not_blacklisted(&env, &state.pool_address, &state.underlying_asset, &from)?;
        Self::validate_not_blacklisted(&env, &state.pool_address, &state.underlying_asset, &spender)?;

        let allowance_data = AllowanceData {
            amount,
            expiration_ledger,
        };
        storage::set_allowance(&env, &from, &spender, &allowance_data);

        env.events().publish(
            (symbol_short!("approve"), from, spender),
            (amount, expiration_ledger),
        );

        Ok(())
    }

    pub fn balance(env: Env, id: Address) -> i128 {
        balance::balance_of(&env, &id).unwrap_or_else(|e| panic_with_error!(&env, e))
    }

    pub fn balance_of(env: Env, id: Address) -> i128 {
        balance::balance_of(&env, &id).unwrap_or_else(|e| panic_with_error!(&env, e))
    }

    pub fn balance_of_with_index(env: Env, id: Address, liquidity_index: u128) -> i128 {
        balance::balance_of_with_index(&env, &id, liquidity_index)
    }

    pub fn balance_of_with_liquidity_index(env: Env, id: Address, liquidity_index: u128) -> i128 {
        balance::balance_of_with_index(&env, &id, liquidity_index)
    }

    pub fn transfer(env: Env, from: Address, to: Address, amount: i128) -> Result<(), TokenError> {
        from.require_auth();
        Self::transfer_internal(env, from, to, amount)
    }

    pub fn transfer_from(
        env: Env,
        spender: Address,
        from: Address,
        to: Address,
        amount: i128,
    ) -> Result<(), TokenError> {
        spender.require_auth();

        if amount <= 0 {
            return Err(TokenError::InvalidAmount);
        }

        // MEDIUM-001: Check spender blacklist before processing delegated transfer
        let state = storage::get_state(&env)?;
        Self::validate_not_blacklisted(&env, &state.pool_address, &state.underlying_asset, &spender)?;

        let current_allowance = Self::allowance(env.clone(), from.clone(), spender.clone());

        if current_allowance < amount {
            return Err(TokenError::InsufficientAllowance);
        }

        if let Some(mut allowance_data) = storage::get_allowance(&env, &from, &spender) {
            allowance_data.amount = current_allowance.checked_sub(amount)
                .ok_or(TokenError::InsufficientAllowance)?;
            storage::set_allowance(&env, &from, &spender, &allowance_data);
        }

        // WP-C6: self-transfer after allowance consumed — consistent with token::transfer_from
        // (SEP-41: transfer_from always costs allowance proportional to amount)
        if from == to {
            return Ok(());
        }

        // transfer_internal also checks from + to blacklist
        Self::transfer_internal(env, from, to, amount)
    }

    /// WP-L8: Disabled — uses stale stored index. Router uses burn_scaled exclusively.
    pub fn burn(_env: Env, _from: Address, _amount: i128) -> Result<(), TokenError> {
        Err(TokenError::UnsupportedOperation)
    }

    /// WP-M4: Disabled — burn_from bypasses HF checks. Router uses burn_scaled exclusively.
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

    /// WP-L8: Disabled — uses stale stored index. Router uses mint_scaled exclusively.
    pub fn mint(_env: Env, _to: Address, _amount: i128) -> Result<(), TokenError> {
        Err(TokenError::UnsupportedOperation)
    }

    pub fn __constructor(
        env: Env,
        admin: Address,
        underlying_asset: Address,
        pool: Address,
        name: String,
        symbol: String,
        decimals: u32,
    ) {
        if storage::has_state(&env) {
            panic!("Already initialized");
        }

        crate::upgrade::initialize_admin(&env, &admin);

        let state = ATokenState {
            underlying_asset,
            pool_address: pool,
            total_supply_scaled: 0,
            name,
            symbol,
            decimals,
        };
        storage::set_state(&env, &state);
    }

    pub fn initialize(
        _env: Env,
        _admin: Address,
        _underlying_asset: Address,
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

    /// Mint scaled aTokens for a user.
    /// Returns (is_first_supply, user_new_scaled_balance, total_supply_scaled).
    /// The user_new_scaled_balance enables callers to compute the user's underlying
    /// balance via ray_mul(user_new_scaled_balance, index), avoiding an extra
    /// balance_of_with_index cross-contract call.
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
        let scaled_u128 = ray_div_down(&env, amount, index).map_err(|_| TokenError::InvalidIndex)?;
        let amount_scaled = safe_u128_to_i128(&env, scaled_u128);
        let current_scaled_balance = storage::get_scaled_balance(&env, &on_behalf_of);
        let is_first_supply = current_scaled_balance == 0;
        let new_scaled_balance = current_scaled_balance.checked_add(amount_scaled)
            .ok_or(TokenError::TransferFailed)?;
        storage::set_scaled_balance(&env, &on_behalf_of, &new_scaled_balance);

        // F-19
        state.total_supply_scaled = state
            .total_supply_scaled
            .checked_add(amount_scaled)
            .ok_or(TokenError::TransferFailed)?;
        let underlying_asset = state.underlying_asset.clone();
        let pool_address = state.pool_address.clone();
        storage::set_state(&env, &state);

        env.events().publish(
            (symbol_short!("mint"), on_behalf_of.clone()),
            (amount_scaled, safe_u128_to_i128(&env, amount)),
        );

        // Update incentives after minting (supply rewards)
        Self::handle_incentives_action(&env, &pool_address, &underlying_asset, &on_behalf_of, 0)?;

        Ok((is_first_supply, new_scaled_balance, state.total_supply_scaled))
    }

    pub fn burn_scaled(
        env: Env,
        caller: Address,
        on_behalf_of: Address,
        amount: u128,
        index: u128,
    ) -> Result<(bool, i128), TokenError> {
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

        // M-14 / OPT-M2: ray_div_up burns slightly more scaled units (protocol-favorable)
        let scaled_u128 = ray_div_up(&env, amount, index).map_err(|_| TokenError::InvalidIndex)?;
        let mut amount_scaled = safe_u128_to_i128(&env, scaled_u128);
        let current_scaled_balance = storage::get_scaled_balance(&env, &on_behalf_of);

        // Cap at actual scaled balance: ray_div_up(ray_mul_down(S,I),I) can exceed S by 1
        if amount_scaled > current_scaled_balance {
            amount_scaled = current_scaled_balance;
        }

        if amount_scaled == 0 {
            return Err(TokenError::InvalidAmount);
        }

        let new_scaled_balance = current_scaled_balance.checked_sub(amount_scaled)
            .ok_or(TokenError::InsufficientBalance)?;
        storage::set_scaled_balance(&env, &on_behalf_of, &new_scaled_balance);

        // F-19
        state.total_supply_scaled = state
            .total_supply_scaled
            .checked_sub(amount_scaled)
            .ok_or(TokenError::TransferFailed)?;
        let underlying_asset = state.underlying_asset.clone();
        let pool_address = state.pool_address.clone();
        storage::set_state(&env, &state);

        // WP-L4: Derive actual amount from capped scaled value, not raw `amount`
        let actual_amount = ray_mul(&env, safe_i128_to_u128(&env, amount_scaled), index)
            .map_err(|_| TokenError::InvalidIndex)?;
        env.events().publish(
            (symbol_short!("burn"), on_behalf_of.clone()),
            (amount_scaled, safe_u128_to_i128(&env, actual_amount)),
        );

        // Update incentives after burning (supply rewards)
        Self::handle_incentives_action(&env, &pool_address, &underlying_asset, &on_behalf_of, 0)?;

        Ok((new_scaled_balance == 0, state.total_supply_scaled))
    }

    pub fn transfer_underlying_to(
        env: Env,
        caller: Address,
        target: Address,
        amount: u128,
    ) -> Result<bool, TokenError> {
        caller.require_auth();
        let state = storage::get_state(&env)?;
        if caller != state.pool_address {
            return Err(TokenError::Unauthorized);
        }

        if amount == 0 {
            return Err(TokenError::InvalidAmount);
        }

        let balance_args =
            soroban_sdk::vec![&env, env.current_contract_address().into_val(&env)];
        let balance_sym = Symbol::new(&env, "balance");
        let underlying_balance: i128 = match env.try_invoke_contract::<i128, TokenError>(
            &state.underlying_asset,
            &balance_sym,
            balance_args,
        ) {
            Ok(Ok(bal)) => bal,
            Ok(Err(_)) | Err(_) => return Err(TokenError::TransferFailed),
        };

        let amount_i128 = safe_u128_to_i128(&env, amount);
        if underlying_balance < amount_i128 {
            return Err(TokenError::InsufficientBalance);
        }

        let mut transfer_args = Vec::new(&env);
        transfer_args.push_back(env.current_contract_address().into_val(&env));
        transfer_args.push_back(target.into_val(&env));
        transfer_args.push_back(amount_i128.into_val(&env));

        let transfer_auth = InvokerContractAuthEntry::Contract(SubContractInvocation {
            context: ContractContext {
                contract: state.underlying_asset.clone(),
                fn_name: Symbol::new(&env, "transfer"),
                args: transfer_args.clone(),
            },
            sub_invocations: soroban_sdk::vec![&env],
        });

        env.authorize_as_current_contract(soroban_sdk::vec![&env, transfer_auth]);

        let _: () = env.invoke_contract(
            &state.underlying_asset,
            &Symbol::new(&env, "transfer"),
            transfer_args,
        );

        Ok(true)
    }
    
    /// Burns scaled aTokens and transfers underlying to target in a single call.
    /// Returns (new_user_scaled_balance, new_total_supply_scaled, actual_amount_transferred).
    /// The actual_amount is capped at `amount` to prevent rounding overshoot (WP-C1).
    pub fn burn_scaled_and_transfer_to(
        env: Env,
        caller: Address,
        on_behalf_of: Address,
        amount: u128,
        index: u128,
        transfer_target: Address,
    ) -> Result<(i128, i128, u128), TokenError> {
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

        // M-14 / OPT-M2: ray_div_up burns slightly more scaled units (protocol-favorable)
        let scaled_u128 = ray_div_up(&env, amount, index).map_err(|_| TokenError::InvalidIndex)?;
        let mut amount_scaled = safe_u128_to_i128(&env, scaled_u128);
        let current_scaled_balance = storage::get_scaled_balance(&env, &on_behalf_of);

        // Cap at actual scaled balance: ray_div_up(ray_mul_down(S,I),I) can exceed S by 1
        if amount_scaled > current_scaled_balance {
            amount_scaled = current_scaled_balance;
        }

        if amount_scaled == 0 {
            return Err(TokenError::InvalidAmount);
        }

        let new_scaled_balance = current_scaled_balance.checked_sub(amount_scaled)
            .ok_or(TokenError::InsufficientBalance)?;
        storage::set_scaled_balance(&env, &on_behalf_of, &new_scaled_balance);

        // F-19
        state.total_supply_scaled = state
            .total_supply_scaled
            .checked_sub(amount_scaled)
            .ok_or(TokenError::TransferFailed)?;
        let underlying_asset = state.underlying_asset.clone();
        let pool_address = state.pool_address.clone();
        storage::set_state(&env, &state);

        // WP-C1: Floor-round actual_amount so protocol never overpays when amount_scaled is capped.
        // ray_mul (half-up) after ray_div_up can exceed the true value of burned shares.
        let actual_amount = ray_mul_down(&env, safe_i128_to_u128(&env, amount_scaled), index)
            .map_err(|_| TokenError::InvalidIndex)?;
        let actual_amount = actual_amount.min(amount);
        let actual_amount_i128 = safe_u128_to_i128(&env, actual_amount);
        env.events().publish(
            (symbol_short!("burn"), on_behalf_of.clone()),
            (amount_scaled, actual_amount_i128),
        );

        // Update incentives after burning (supply rewards)
        Self::handle_incentives_action(&env, &pool_address, &underlying_asset, &on_behalf_of, 0)?;

        // Transfer underlying to target (same logic as transfer_underlying_to)
        let mut transfer_args = Vec::new(&env);
        transfer_args.push_back(env.current_contract_address().into_val(&env));
        transfer_args.push_back(transfer_target.into_val(&env));
        transfer_args.push_back(actual_amount_i128.into_val(&env));

        // Authorize aToken contract to transfer underlying token
        // Note: authorize_as_current_contract only authorizes the contract itself, not the EOA caller
        let transfer_auth = InvokerContractAuthEntry::Contract(SubContractInvocation {
            context: ContractContext {
                contract: underlying_asset.clone(),
                fn_name: Symbol::new(&env, "transfer"),
                args: transfer_args.clone(),
            },
            sub_invocations: soroban_sdk::vec![&env],
        });

        env.authorize_as_current_contract(soroban_sdk::vec![&env, transfer_auth]);

        let _: () = env.invoke_contract(
            &underlying_asset,
            &Symbol::new(&env, "transfer"),
            transfer_args,
        );

        Ok((new_scaled_balance, state.total_supply_scaled, actual_amount))
    }

    /// WP-M3: Transfer aTokens from borrower to liquidator without moving underlying.
    /// Used when _receive_a_token=true. Returns true if this is the liquidator's first balance.
    /// Uses single ray_div for both debit and credit to prevent total_supply_scaled drift.
    pub fn transfer_on_liquidation(
        env: Env,
        caller: Address,
        from: Address,
        to: Address,
        amount: u128,
        index: u128,
    ) -> Result<bool, TokenError> {
        caller.require_auth();
        let state = storage::get_state(&env)?;
        if caller != state.pool_address {
            return Err(TokenError::Unauthorized);
        }

        if amount == 0 {
            return Err(TokenError::InvalidAmount);
        }

        if index == 0 {
            return Err(TokenError::InvalidIndex);
        }

        // Single ray_div_down for both debit and credit (prevents total_supply_scaled drift)
        // M-1: Use ray_div_down to match burn_scaled rounding and avoid protocol fee revert
        let scaled_u128 = ray_div_down(&env, amount, index).map_err(|_| TokenError::InvalidIndex)?;
        let amount_scaled = safe_u128_to_i128(&env, scaled_u128);

        if amount_scaled == 0 {
            return Err(TokenError::InvalidAmount);
        }

        // Debit from sender
        let from_balance = storage::get_scaled_balance(&env, &from);
        if from_balance < amount_scaled {
            return Err(TokenError::InsufficientBalance);
        }
        storage::set_scaled_balance(&env, &from, &(from_balance - amount_scaled));

        // Credit to receiver
        let to_balance = storage::get_scaled_balance(&env, &to);
        let is_first = to_balance == 0;
        let new_to_balance = to_balance.checked_add(amount_scaled)
            .ok_or(TokenError::TransferFailed)?;
        storage::set_scaled_balance(&env, &to, &new_to_balance);

        // total_supply_scaled unchanged (transfer, not mint/burn)

        // Update incentives for both parties
        Self::handle_incentives_action(&env, &state.pool_address, &state.underlying_asset, &from, 0)?;
        Self::handle_incentives_action(&env, &state.pool_address, &state.underlying_asset, &to, 0)?;

        env.events().publish(
            (symbol_short!("liq_xfer"), from, to),
            (amount_scaled, safe_u128_to_i128(&env, amount)),
        );

        Ok(is_first)
    }

    pub fn scaled_balance_of(env: Env, id: Address) -> i128 {
        storage::get_scaled_balance(&env, &id)
    }

    pub fn scaled_total_supply(env: Env) -> i128 {
        storage::get_state(&env).map(|s| s.total_supply_scaled).unwrap_or_else(|e| panic_with_error!(&env, e))
    }

    pub fn get_liquidity_index(env: Env) -> u128 {
        let state = storage::get_state(&env).unwrap_or_else(|e| panic_with_error!(&env, e));
        let mut args = Vec::new(&env);
        args.push_back(state.underlying_asset.to_val());

        // Call kinetic-router to get current liquidity index (always up-to-date)
        let result = env.try_invoke_contract::<u128, KineticRouterError>(
            &state.pool_address,
            &Symbol::new(&env, "get_current_liquidity_index"),
            args,
        );

        match result {
            Ok(Ok(index)) => index,
            Ok(Err(_)) | Err(_) => {
                panic_with_error!(&env, TokenError::InvalidIndex)
            }
        }
    }

    pub fn get_underlying_asset(env: Env) -> Address {
        storage::get_state(&env).map(|s| s.underlying_asset).unwrap_or_else(|e| panic_with_error!(&env, e))
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

    fn transfer_internal(env: Env, from: Address, to: Address, amount: i128) -> Result<(), TokenError> {
        if amount <= 0 {
            return Err(TokenError::InvalidAmount);
        }

        // WP-C6: self-transfer would overwrite the debit with the credit, inflating balance
        if from == to {
            return Ok(());
        }

        let state = storage::get_state(&env)?;

        // Enforce whitelist on recipient to prevent bypass via aToken transfers
        Self::validate_recipient_whitelist(
            &env,
            &state.pool_address,
            &state.underlying_asset,
            &to,
        )?;

        // HIGH-003: Enforce blacklist on both sender and recipient
        Self::validate_not_blacklisted(
            &env,
            &state.pool_address,
            &state.underlying_asset,
            &from,
        )?;
        Self::validate_not_blacklisted(
            &env,
            &state.pool_address,
            &state.underlying_asset,
            &to,
        )?;

        // M-04 + WP-L5: Fail-closed — reject transfer if fresh index unavailable
        let liquidity_index = {
            let mut args = soroban_sdk::Vec::new(&env);
            args.push_back(state.underlying_asset.to_val());
            match env.try_invoke_contract::<u128, k2_shared::KineticRouterError>(
                &state.pool_address,
                &soroban_sdk::Symbol::new(&env, "get_current_liquidity_index"),
                args,
            ) {
                Ok(Ok(index)) if index > 0 => index,
                _ => return Err(TokenError::InvalidIndex),
            }
        };

        // S-04: Compute scaled amounts and post-transfer balances
        let amount_u128 = safe_i128_to_u128(&env, amount);
        let scaled_u128 = ray_div_up(&env, amount_u128, liquidity_index).map_err(|_| TokenError::InvalidIndex)?;
        let scaled_amount = safe_u128_to_i128(&env, scaled_u128);
        let from_scaled_balance = storage::get_scaled_balance(&env, &from);

        if from_scaled_balance < scaled_amount {
            return Err(TokenError::InsufficientBalance);
        }

        let new_from_balance = from_scaled_balance.checked_sub(scaled_amount)
            .ok_or(TokenError::InsufficientBalance)?;
        let to_scaled_balance = storage::get_scaled_balance(&env, &to);
        let new_to_balance = to_scaled_balance.checked_add(scaled_amount)
            .ok_or(TokenError::TransferFailed)?;

        // WP-C1 + MEDIUM-1: Single call to validate sender HF + update bitmaps.
        // Balances are computed but not yet written — if HF check fails, transfer reverts cleanly.
        {
            let from_balance_u128 = k2_shared::safe_i128_to_u128(&env, new_from_balance);
            let to_balance_u128 = k2_shared::safe_i128_to_u128(&env, new_to_balance);
            let mut args = Vec::new(&env);
            args.push_back(state.underlying_asset.clone().into_val(&env));
            args.push_back(from.clone().into_val(&env));
            args.push_back(to.clone().into_val(&env));
            args.push_back(amount_u128.into_val(&env));
            args.push_back(from_balance_u128.into_val(&env));
            args.push_back(to_balance_u128.into_val(&env));

            let result = env.try_invoke_contract::<(), k2_shared::KineticRouterError>(
                &state.pool_address,
                &Symbol::new(&env, "validate_and_finalize_transfer"),
                args,
            );

            match result {
                Ok(Ok(())) => {} // HF valid + bitmaps updated
                _ => return Err(TokenError::TransferFailed), // Fail-closed
            }
        }

        // Write balances after validation passed
        storage::set_scaled_balance(&env, &from, &new_from_balance);
        storage::set_scaled_balance(&env, &to, &new_to_balance);

        // N-03
        Self::handle_incentives_action(&env, &state.pool_address, &state.underlying_asset, &from, 0)?;
        Self::handle_incentives_action(&env, &state.pool_address, &state.underlying_asset, &to, 0)?;

        env.events().publish(
            (symbol_short!("transfer"), from, to),
            (scaled_amount, amount),
        );

        Ok(())
    }

    /// Prevents whitelist bypass via aToken transfers
    ///
    /// Validates that the recipient address is whitelisted for the reserve.
    /// If the pool contract call fails (e.g., contract not initialized),
    /// we fail-closed for security: transfers are blocked until whitelist is properly configured.
    fn validate_recipient_whitelist(
        env: &Env,
        pool_address: &Address,
        underlying_asset: &Address,
        recipient: &Address,
    ) -> Result<(), TokenError> {
        let mut args = Vec::new(env);
        args.push_back(underlying_asset.clone().into_val(env));
        args.push_back(recipient.clone().into_val(env));

        let is_whitelisted: bool = match env.try_invoke_contract::<bool, TokenError>(
            pool_address,
            &Symbol::new(env, "is_whitelisted_for_reserve"),
            args,
        ) {
            Ok(Ok(result)) => result,
            // F-11: Fail-closed design - if pool contract call fails, block transfer for security.
            // This is a deliberate security-first choice: we prefer to block legitimate transfers
            // during transient failures (pool temporarily unavailable, gas limit, etc.) rather
            // than risk allowing unauthorized transfers if the whitelist check cannot be verified.
            // This ensures whitelist is properly configured before allowing transfers.
            _ => return Err(TokenError::TransferFailed),
        };

        if !is_whitelisted {
            return Err(TokenError::TransferFailed);
        }

        Ok(())
    }

    /// HIGH-003: Validates that an address is not blacklisted for the reserve.
    /// Fail-closed: if the pool contract call fails, transfers are blocked.
    fn validate_not_blacklisted(
        env: &Env,
        pool_address: &Address,
        underlying_asset: &Address,
        account: &Address,
    ) -> Result<(), TokenError> {
        let mut args = Vec::new(env);
        args.push_back(underlying_asset.clone().into_val(env));
        args.push_back(account.clone().into_val(env));

        let is_blacklisted: bool = match env.try_invoke_contract::<bool, TokenError>(
            pool_address,
            &Symbol::new(env, "is_blacklisted_for_reserve"),
            args,
        ) {
            Ok(Ok(result)) => result,
            // Fail-closed: if pool call fails, block transfer
            _ => return Err(TokenError::TransferFailed),
        };

        if is_blacklisted {
            return Err(TokenError::TransferFailed);
        }

        Ok(())
    }

    /// Handle incentives action - calls incentives contract to update reward indices
    /// This is called after mint/burn operations to update rewards
    /// Following Aave's pattern: asset is determined by msg.sender (this token contract)
    fn handle_incentives_action(
        env: &Env,
        _pool_address: &Address,
        _underlying_asset: &Address,
        user: &Address,
        reward_type: u32,
    ) -> Result<(), TokenError> {
        // Get incentives contract address from local cache only
        // Pool sets this during initialization/updates to avoid re-entry
        let incentives_contract = match storage::get_incentives_contract(env) {
            Some(addr) => addr,
            None => return Ok(()), // No incentives contract set, skip silently
        };

        // S-04
        let user_balance = safe_i128_to_u128(env, storage::get_scaled_balance(env, user));
        let state = storage::get_state(env)?;
        let total_supply = safe_i128_to_u128(env, state.total_supply_scaled);

        // Asset determined by token_address (this contract), following Aave's pattern
        // If token not registered, call is a no-op (safe for anyone to call)
        let mut args = Vec::new(env);
        args.push_back(env.current_contract_address().into_val(env));
        args.push_back(user.clone().into_val(env));
        args.push_back(total_supply.into_val(env));
        args.push_back(user_balance.into_val(env));
        args.push_back(reward_type.into_val(env));

        // L-05
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
