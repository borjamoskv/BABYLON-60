#![no_std]
use soroban_sdk::{contract, contractimpl, contracttype, contracterror, symbol_short, token, Address, Env, IntoVal, Symbol, Vec};
use soroban_sdk::auth::{ContractContext, InvokerContractAuthEntry, SubContractInvocation};
#[cfg(test)]
mod test;

// TTL constants: 1 year = 365 days * 17280 ledgers/day ≈ 6,307,200 ledgers
// Extend TTL when remaining time falls below 30 days
const TTL_THRESHOLD: u32 = 30 * 17280; // 30 days in ledgers
const TTL_EXTENSION: u32 = 365 * 17280; // 1 year in ledgers

#[derive(Clone)]
#[contracttype]
pub enum DataKey {
    Router,
    Admin,
    Initialized,
    /// Pool address for a token pair: PoolAddress(token0, token1) -> Address
    PoolAddress(Address, Address),
}

#[contracterror]
#[derive(Clone, Debug, Copy, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum Error {
    NotInitialized = 1,
    AlreadyInitialized = 2,
    Unauthorized = 3,
    InvalidAmount = 4,
    SwapFailed = 5,
}

/// Safely convert u128 to i128 with bounds checking
fn safe_u128_to_i128(env: &Env, amount: u128) -> Result<i128, Error> {
    if amount > i128::MAX as u128 {
        return Err(Error::InvalidAmount);
    }
    Ok(amount as i128)
}

#[contract]
pub struct AquariusSwapAdapter;

#[contractimpl]
impl AquariusSwapAdapter {
    pub fn __constructor(env: Env, admin: Address, aquarius_router: Address) {
        env.storage().instance().set(&DataKey::Admin, &admin);
        env.storage().instance().set(&DataKey::Router, &aquarius_router);
        env.storage().instance().set(&DataKey::Initialized, &true);
        env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    }

    /// Initialize adapter with Aquarius router address
    /// 
    /// # Arguments
    /// * `admin` - Admin address (can update router)
    /// * `aquarius_router` - Aquarius router contract address
    pub fn initialize(_env: Env, _admin: Address, _aquarius_router: Address) -> Result<(), Error> {
        panic!("AQUARIUS_ADAPTER_ALREADY_INITIALIZED_AT_CONSTRUCTOR");
    }
    
    /// Update Aquarius router address (admin only)
    pub fn set_router(env: Env, caller: Address, aquarius_router: Address) -> Result<(), Error> {
        caller.require_auth();
        
        let admin: Address = env.storage().instance()
            .get(&DataKey::Admin)
            .ok_or(Error::NotInitialized)?;
        
        if caller != admin {
            return Err(Error::Unauthorized);
        }
        
        env.storage().instance().set(&DataKey::Router, &aquarius_router);
        env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
        
        Ok(())
    }
    
    /// Get current Aquarius router address
    pub fn get_router(env: Env) -> Result<Address, Error> {
        let result = env.storage().instance()
            .get(&DataKey::Router)
            .ok_or(Error::NotInitialized);
        if result.is_ok() {
            env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
        }
        result
    }
    
    /// Register a pool for a token pair (admin only)
    /// 
    /// # Arguments
    /// * `caller` - Must be admin
    /// * `token_a` - First token
    /// * `token_b` - Second token  
    /// * `pool_address` - Pool contract address from Aquarius
    pub fn register_pool(
        env: Env,
        caller: Address,
        token_a: Address,
        token_b: Address,
        pool_address: Address,
    ) -> Result<(), Error> {
        caller.require_auth();
        
        let admin: Address = env.storage().instance()
            .get(&DataKey::Admin)
            .ok_or(Error::NotInitialized)?;
        
        env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
        
        if caller != admin {
            return Err(Error::Unauthorized);
        }
        
        // Store with sorted tokens
        let (token0, token1) = if token_a < token_b {
            (token_a, token_b)
        } else {
            (token_b, token_a)
        };
        
        let key = DataKey::PoolAddress(token0, token1);
        env.storage().persistent().set(&key, &pool_address);
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
        
        Ok(())
    }
    
    /// Get pool address for a token pair
    fn get_pool_address(env: &Env, token_a: &Address, token_b: &Address) -> Result<Address, Error> {
        let (token0, token1) = if token_a < token_b {
            (token_a.clone(), token_b.clone())
        } else {
            (token_b.clone(), token_a.clone())
        };
        
        let key = DataKey::PoolAddress(token0, token1);
        if env.storage().persistent().has(&key) {
            env.storage()
                .persistent()
                .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
        }
        env.storage()
            .persistent()
            .get(&key)
            .ok_or(Error::NotInitialized)
    }
    
    /// Get token indices for pool swap (0 or 1 based on pool's actual token order)
    /// 
    /// Queries the pool to get its actual token order, then calculates indices
    /// based on which token is at which position in the pool.
    fn get_token_indices(
        env: &Env,
        pool_address: &Address,
        from_token: &Address,
        to_token: &Address,
    ) -> Result<(u32, u32), Error> {
        // Query pool for actual token order (pool stores tokens as [token_a, token_b])
        let tokens_result = env.try_invoke_contract::<Vec<Address>, Error>(
            pool_address,
            &Symbol::new(env, "get_tokens"),
            soroban_sdk::vec![env],
        );
        
        let tokens = match tokens_result {
            Ok(Ok(t)) => t,
            Ok(Err(_)) | Err(_) => return Err(Error::SwapFailed),
        };
        
        if tokens.len() != 2 {
            return Err(Error::SwapFailed);
        }
        
        let token_a = tokens.get(0).ok_or(Error::InvalidAmount)?;
        let token_b = tokens.get(1).ok_or(Error::InvalidAmount)?;
        
        // Find indices based on pool's actual token order
        let in_idx = if *from_token == token_a {
            0
        } else if *from_token == token_b {
            1
        } else {
            return Err(Error::SwapFailed); // from_token not in pool
        };
        
        let out_idx = if *to_token == token_a {
            0
        } else if *to_token == token_b {
            1
        } else {
            return Err(Error::SwapFailed); // to_token not in pool
        };
        
        Ok((in_idx, out_idx))
    }
    
    /// Execute swap via Aquarius (K2 standard interface)
    /// 
    /// This is called by K2 contracts. It translates K2's simple interface
    /// to Aquarius's specific requirements (sorted tokens, pool_index, etc.)
    /// 
    /// # Arguments
    /// * `from_token` - Token to swap from
    /// * `to_token` - Token to swap to
    /// * `amount_in` - Amount to swap
    /// * `min_amount_out` - Minimum acceptable output (slippage protection)
    /// * `recipient` - Address to receive output tokens
    /// 
    /// # Returns
    /// * Actual amount of tokens received
    pub fn execute_swap(
        env: Env,
        from_token: Address,
        to_token: Address,
        amount_in: u128,
        min_amount_out: u128,
        recipient: Address,
    ) -> Result<u128, Error> {
        if amount_in == 0 {
            return Err(Error::InvalidAmount);
        }
        
        // Get pool address directly (no router needed)
        let pool_address = Self::get_pool_address(&env, &from_token, &to_token)?;
        let adapter_address = env.current_contract_address();
        
        // Get token indices based on pool's actual token order (pool expects 0 or 1)
        let (in_idx, out_idx) = Self::get_token_indices(&env, &pool_address, &from_token, &to_token)?;
        
        // Pre-authorize the pool swap call and token transfer
        // Pool.swap() calls user.require_auth(), so we need to authorize the adapter
        // Pool will also call: token.transfer(adapter, pool, amount_in)
        let mut auth_entries = soroban_sdk::vec![&env];
        
        // Authorize pool swap call (pool checks adapter_address.require_auth())
        auth_entries.push_back(InvokerContractAuthEntry::Contract(SubContractInvocation {
            context: ContractContext {
                contract: pool_address.clone(),
                fn_name: symbol_short!("swap"),
                args: soroban_sdk::vec![
                    &env,
                    adapter_address.to_val(),
                    in_idx.into_val(&env),
                    out_idx.into_val(&env),
                    amount_in.into_val(&env),
                    min_amount_out.into_val(&env),
                ],
            },
            sub_invocations: Vec::new(&env),
        }));
        
        // Authorize token transfer that pool.swap() will initiate
        auth_entries.push_back(InvokerContractAuthEntry::Contract(SubContractInvocation {
            context: ContractContext {
                contract: from_token.clone(),
                fn_name: symbol_short!("transfer"),
                args: soroban_sdk::vec![
                    &env,
                    adapter_address.to_val(),
                    pool_address.to_val(),
                    safe_u128_to_i128(&env, amount_in)?.into_val(&env),
                ],
            },
            sub_invocations: Vec::new(&env),
        }));
        
        env.authorize_as_current_contract(auth_entries);
        
        // Call pool directly (not router) - avoids nested require_auth() issues
        // Pool signature: swap(user, in_idx, out_idx, in_amount, out_min)
        let swap_result = env.try_invoke_contract::<u128, Error>(
            &pool_address,
            &symbol_short!("swap"),
            soroban_sdk::vec![
                &env,
                adapter_address.to_val(),
                in_idx.into_val(&env),
                out_idx.into_val(&env),
                amount_in.into_val(&env),
                min_amount_out.into_val(&env),
            ],
        );
        
        let amount_out = match swap_result {
            Ok(Ok(amt)) => amt,
            Ok(Err(_)) | Err(_) => return Err(Error::SwapFailed),
        };
        
        if amount_out < min_amount_out {
            return Err(Error::SwapFailed);
        }
        
        // Transfer output tokens from adapter to recipient
        // Flow: K2 -> adapter (input) -> Pool swap -> adapter (output) -> K2 (output)
        env.authorize_as_current_contract(soroban_sdk::vec![
            &env,
            InvokerContractAuthEntry::Contract(SubContractInvocation {
                context: ContractContext {
                    contract: to_token.clone(),
                    fn_name: symbol_short!("transfer"),
                    args: soroban_sdk::vec![
                        &env,
                        adapter_address.to_val(),
                        recipient.to_val(),
                        safe_u128_to_i128(&env, amount_out)?.into_val(&env),
                    ],
                },
                sub_invocations: Vec::new(&env),
            }),
        ]);
        
        token::Client::new(&env, &to_token).transfer(
            &adapter_address,
            &recipient,
            &safe_u128_to_i128(&env, amount_out)?
        );
        
        Ok(amount_out)
    }
    
    /// Get swap quote from Aquarius (for view functions)
    /// 
    /// # Arguments
    /// * `from_token` - Token to swap from
    /// * `to_token` - Token to swap to
    /// * `amount_in` - Amount to get quote for
    /// 
    /// # Returns
    /// * Expected output amount
    pub fn get_quote(
        env: Env,
        from_token: Address,
        to_token: Address,
        amount_in: u128,
    ) -> Result<u128, Error> {
        if amount_in == 0 {
            return Err(Error::InvalidAmount);
        }
        
        // Get pool address directly
        let pool_address = Self::get_pool_address(&env, &from_token, &to_token)?;
        
        // Get token indices based on pool's actual token order
        let (in_idx, out_idx) = Self::get_token_indices(&env, &pool_address, &from_token, &to_token)?;
        
        // Call pool's estimate_swap directly
        // Pool signature: estimate_swap(in_idx, out_idx, in_amount)
        let quote_result = env.try_invoke_contract::<u128, Error>(
            &pool_address,
            &Symbol::new(&env, "estimate_swap"),
            soroban_sdk::vec![
                &env,
                in_idx.into_val(&env),
                out_idx.into_val(&env),
                amount_in.into_val(&env),
            ],
        );
        
        let amount_out = match quote_result {
            Ok(Ok(amt)) => amt,
            Ok(Err(_)) | Err(_) => return Err(Error::SwapFailed),
        };
        
        Ok(amount_out)
    }
}
