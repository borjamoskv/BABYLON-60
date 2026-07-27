#![no_std]
use soroban_sdk::{contract, contractimpl, contracttype, contracterror, symbol_short, token, Address, Env, IntoVal, Symbol, TryFromVal, U256, Val, Vec};
use soroban_sdk::auth::{ContractContext, InvokerContractAuthEntry, SubContractInvocation};

mod test;

// TTL constants: 1 year = 365 days * 17280 ledgers/day ≈ 6,307,200 ledgers
// Extend TTL when remaining time falls below 30 days
const TTL_THRESHOLD: u32 = 30 * 17280; // 30 days in ledgers
const TTL_EXTENSION: u32 = 365 * 17280; // 1 year in ledgers

#[derive(Clone)]
#[contracttype]
pub enum DataKey {
    Router,
    Factory,
    Admin,
    Initialized,
}

/// Safely convert u128 to i128 with bounds checking
fn safe_u128_to_i128(amount: u128) -> Result<i128, Error> {
    if amount > i128::MAX as u128 {
        return Err(Error::SwapFailed);
    }
    Ok(amount as i128)
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

#[contract]
pub struct SoroswapSwapAdapter;

/// Helper to safely invoke a Soroswap contract and decode its Result<T, Error> return type.
/// Soroswap contracts return Result<T, ContractError>, so we invoke and decode the Result.
fn call_soroswap<T: TryFromVal<Env, Val>>(
    env: &Env,
    contract: &Address,
    fn_name: &str,
    args: Vec<Val>,
) -> Result<T, Error> {
    let inner_result: Result<T, soroban_sdk::Error> = env.invoke_contract(
        contract,
        &Symbol::new(env, fn_name),
        args,
    );
    
    inner_result.map_err(|_| Error::SwapFailed)
}

#[contractimpl]
impl SoroswapSwapAdapter {
    pub fn __constructor(env: Env, admin: Address, router: Address, factory: Option<Address>) {
        env.storage().instance().set(&DataKey::Admin, &admin);
        env.storage().instance().set(&DataKey::Router, &router);
        if let Some(f) = factory {
            env.storage().instance().set(&DataKey::Factory, &f);
        }
        env.storage().instance().set(&DataKey::Initialized, &true);
        env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
    }

    /// Initialize adapter with Soroswap router and factory addresses
    /// 
    /// # Arguments
    /// * `admin` - Admin address (can update router/factory)
    /// * `router` - Soroswap router contract address
    /// * `factory` - Soroswap factory contract address (optional, for direct swaps)
    pub fn initialize(_env: Env, _admin: Address, _router: Address, _factory: Option<Address>) -> Result<(), Error> {
        panic!("SOROSWAP_ADAPTER_ALREADY_INITIALIZED_AT_CONSTRUCTOR");
    }
    
    /// Update Soroswap router address (admin only)
    pub fn set_router(env: Env, caller: Address, router: Address) -> Result<(), Error> {
        caller.require_auth();
        
        let admin: Address = env.storage().instance()
            .get(&DataKey::Admin)
            .ok_or(Error::NotInitialized)?;
        
        if caller != admin {
            return Err(Error::Unauthorized);
        }
        
        env.storage().instance().set(&DataKey::Router, &router);
        env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
        
        Ok(())
    }
    
    /// Update Soroswap factory address (admin only)
    pub fn set_factory(env: Env, caller: Address, factory: Option<Address>) -> Result<(), Error> {
        caller.require_auth();
        
        let admin: Address = env.storage().instance()
            .get(&DataKey::Admin)
            .ok_or(Error::NotInitialized)?;
        
        if caller != admin {
            return Err(Error::Unauthorized);
        }
        
        if let Some(f) = factory {
            env.storage().instance().set(&DataKey::Factory, &f);
            env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
        } else {
            env.storage().instance().remove(&DataKey::Factory);
        }
        
        Ok(())
    }
    
    /// Get current Soroswap router address
    pub fn get_router(env: Env) -> Result<Address, Error> {
        let result = env.storage().instance()
            .get(&DataKey::Router)
            .ok_or(Error::NotInitialized);
        if result.is_ok() {
            env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
        }
        result
    }
    
    fn get_factory(env: &Env) -> Option<Address> {
        let result = env.storage().instance().get(&DataKey::Factory);
        if result.is_some() {
            env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
        }
        result
    }
    
    fn sort_tokens(token_a: &Address, token_b: &Address) -> (Address, Address) {
        if token_a < token_b {
            (token_a.clone(), token_b.clone())
        } else {
            (token_b.clone(), token_a.clone())
        }
    }
    
    fn compute_pair_address(env: &Env, factory: &Address, token_a: &Address, token_b: &Address) -> Address {
        let (token_0, token_1) = Self::sort_tokens(token_a, token_b);
        use soroban_sdk::{Bytes, BytesN, xdr::ToXdr};
        let mut salt = Bytes::new(env);
        salt.append(&token_0.clone().to_xdr(env));
        salt.append(&token_1.clone().to_xdr(env));
        let salt_hash: BytesN<32> = env.crypto().sha256(&salt).into();
        env.deployer().with_address(factory.clone(), salt_hash).deployed_address()
    }
    
    /// AMM constant-product swap output: (amount_in_with_fee * reserve_out) / (reserve_in + amount_in_with_fee)
    /// Uses U256 for the intermediate multiplication to avoid i128 overflow with large reserves.
    fn calculate_amount_out(env: &Env, amount_in: i128, reserve_in: i128, reserve_out: i128) -> Option<i128> {
        if amount_in <= 0 || reserve_in <= 0 || reserve_out <= 0 {
            return None;
        }
        // Calculate fee with ceiling arithmetic: ceil(amount_in * 3 / 1000)
        let fee = amount_in
            .checked_mul(3)?
            .checked_add(1000 - 1)?
            .checked_div(1000)?;
        
        let amount_in_with_fee = amount_in.checked_sub(fee)?;
        if amount_in_with_fee <= 0 {
            return None;
        }
        let denominator = reserve_in.checked_add(amount_in_with_fee)?;
        if denominator <= 0 {
            return None;
        }

        // All three values are guaranteed > 0 by the guards above, so `as u128` is safe.
        let num = U256::from_u128(env, amount_in_with_fee as u128)
            .mul(&U256::from_u128(env, reserve_out as u128));
        let den = U256::from_u128(env, denominator as u128);
        let result = num.div(&den);
        
        // Convert back — result fits in i128 because it is <= reserve_out which was i128
        result.to_u128().and_then(|v| i128::try_from(v).ok())
    }
    
    /// Execute swap via Soroswap (K2 standard interface)
    /// 
    /// This is called by K2 contracts. It swaps via Soroswap router or direct pair.
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
        
        let adapter_address = env.current_contract_address();
        let router = Self::get_router(env.clone())?;
        
        // Try direct swap via factory if available, otherwise use router
        if let Some(factory) = Self::get_factory(&env) {
            // Direct pair swap (optimized)
            let pair_address = Self::compute_pair_address(&env, &factory, &from_token, &to_token);
            
            // Call get_reserves - Soroswap returns Result<(i128, i128), Error>
            let (reserve_0, reserve_1): (i128, i128) = call_soroswap(
                &env,
                &pair_address,
                "get_reserves",
                soroban_sdk::vec![&env],
            )?;
            
            let (token_0, _token_1) = Self::sort_tokens(&from_token, &to_token);
            let (reserve_in, reserve_out) = if from_token == token_0 {
                (reserve_0, reserve_1)
            } else {
                (reserve_1, reserve_0)
            };
            
            let amount_in_i128 = safe_u128_to_i128(amount_in)?;
            let min_amount_out_i128 = safe_u128_to_i128(min_amount_out)?;
            
            let amount_out = Self::calculate_amount_out(&env, amount_in_i128, reserve_in, reserve_out)
                .ok_or(Error::SwapFailed)?;
            
            if amount_out < min_amount_out_i128 {
                return Err(Error::SwapFailed);
            }
            
            // Authorize token transfer to pair
            env.authorize_as_current_contract(soroban_sdk::vec![
                &env,
                InvokerContractAuthEntry::Contract(SubContractInvocation {
                    context: ContractContext {
                        contract: from_token.clone(),
                        fn_name: symbol_short!("transfer"),
                        args: soroban_sdk::vec![
                            &env,
                            adapter_address.to_val(),
                            pair_address.to_val(),
                            amount_in_i128.into_val(&env),
                        ],
                    },
                    sub_invocations: Vec::new(&env),
                }),
            ]);
            
            // Transfer tokens to pair
            token::Client::new(&env, &from_token).transfer(
                &adapter_address,
                &pair_address,
                &amount_in_i128
            );
            
            // Execute swap
            let (amount_0_out, amount_1_out) = if from_token == token_0 {
                (0i128, amount_out)
            } else {
                (amount_out, 0i128)
            };
            
            // Call swap - Soroswap returns Result<(), Error>
            let _: () = call_soroswap(
                &env,
                &pair_address,
                "swap",
                soroban_sdk::vec![
                    &env,
                    amount_0_out.into_val(&env),
                    amount_1_out.into_val(&env),
                    recipient.to_val(),
                ],
            )?;
            
            u128::try_from(amount_out).map_err(|_| Error::InvalidAmount)
        } else {
            let mut path = Vec::new(&env);
            path.push_back(from_token.clone());
            path.push_back(to_token.clone());
            
            let deadline = env.ledger().timestamp() + 3600;
            
            let amount_in_i128 = safe_u128_to_i128(amount_in)?;
            let min_amount_out_i128 = safe_u128_to_i128(min_amount_out)?;
            
            let factory: Address = call_soroswap(
                &env,
                &router,
                "get_factory",
                soroban_sdk::vec![&env],
            )?;
            
            let pair_address: Address = call_soroswap(
                &env,
                &factory,
                "get_pair",
                soroban_sdk::vec![&env, from_token.to_val(), to_token.to_val()],
            )?;
            
            env.authorize_as_current_contract(soroban_sdk::vec![
                &env,
                InvokerContractAuthEntry::Contract(SubContractInvocation {
                    context: ContractContext {
                        contract: from_token.clone(),
                        fn_name: symbol_short!("transfer"),
                        args: soroban_sdk::vec![
                            &env,
                            adapter_address.to_val(),
                            pair_address.to_val(),
                            amount_in_i128.into_val(&env),
                        ],
                    },
                    sub_invocations: Vec::new(&env),
                }),
            ]);
            
            let amounts: Vec<i128> = call_soroswap(
                &env,
                &router,
                "swap_exact_tokens_for_tokens",
                soroban_sdk::vec![
                    &env,
                    amount_in_i128.into_val(&env),
                    min_amount_out_i128.into_val(&env),
                    path.to_val(),
                    adapter_address.to_val(),
                    deadline.into_val(&env),
                ],
            )?;
            
            if amounts.len() < 2 {
                return Err(Error::SwapFailed);
            }
            
            let amount_out = amounts.get(amounts.len() - 1).ok_or(Error::SwapFailed)?;
            
            if amount_out < min_amount_out_i128 {
                return Err(Error::SwapFailed);
            }
            
            // Transfer to recipient if different from adapter
            if recipient != adapter_address {
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
                                amount_out.into_val(&env),
                            ],
                        },
                        sub_invocations: Vec::new(&env),
                    }),
                ]);
                
                token::Client::new(&env, &to_token).transfer(
                    &adapter_address,
                    &recipient,
                    &amount_out
                );
            }
            
            u128::try_from(amount_out).map_err(|_| Error::InvalidAmount)
        }
    }
    
    /// Get swap quote from Soroswap (for view functions)
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
        
        let router = Self::get_router(env.clone())?;
        
        // Try direct quote if factory available
        if let Some(factory) = Self::get_factory(&env) {
            let pair_address = Self::compute_pair_address(&env, &factory, &from_token, &to_token);
            
            // Call get_reserves - Soroswap returns Result<(i128, i128), Error>
            let (reserve_0, reserve_1): (i128, i128) = call_soroswap(
                &env,
                &pair_address,
                "get_reserves",
                soroban_sdk::vec![&env],
            )?;
            
            let (token_0, _token_1) = Self::sort_tokens(&from_token, &to_token);
            let (reserve_in, reserve_out) = if from_token == token_0 {
                (reserve_0, reserve_1)
            } else {
                (reserve_1, reserve_0)
            };
            
            let amount_in_i128 = safe_u128_to_i128(amount_in)?;
            let amount_out = Self::calculate_amount_out(&env, amount_in_i128, reserve_in, reserve_out)
                .ok_or(Error::SwapFailed)?;
            
            u128::try_from(amount_out).map_err(|_| Error::InvalidAmount)
        } else {
            // Use router for quote - Soroswap returns Result<Vec<i128>, Error>
            let mut path = Vec::new(&env);
            path.push_back(from_token.clone());
            path.push_back(to_token.clone());
            
            let amount_in_i128 = safe_u128_to_i128(amount_in)?;
            let amounts: Vec<i128> = call_soroswap(
                &env,
                &router,
                "router_get_amounts_out",
                soroban_sdk::vec![&env, amount_in_i128.into_val(&env), path.to_val()],
            )?;
            
            if amounts.len() < 2 {
                return Err(Error::SwapFailed);
            }
            
            let out = amounts.get(amounts.len() - 1).ok_or(Error::SwapFailed)?;
            u128::try_from(out).map_err(|_| Error::InvalidAmount)
        }
    }
}
