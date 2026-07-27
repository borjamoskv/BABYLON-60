use soroban_sdk::{
    auth::{ContractContext, InvokerContractAuthEntry, SubContractInvocation},
    xdr::ToXdr, symbol_short, Address, Bytes, BytesN, Env, IntoVal, Symbol, TryFromVal, Val, Vec,
};

use crate::KineticRouterError;
use crate::utils::{safe_i128_to_u128, safe_u128_to_i128};

/// Helper to invoke Soroswap contracts that return Result<T, Error>.
/// Decodes the return as Result<T, soroban_sdk::Error> to handle Soroswap's Result wrapper.
fn call_soroswap<T: TryFromVal<Env, Val>>(
    env: &Env,
    contract: &Address,
    fn_name: &str,
    args: Vec<Val>,
) -> Result<T, KineticRouterError> {
    let inner_result: Result<T, soroban_sdk::Error> = env.invoke_contract(
        contract,
        &Symbol::new(env, fn_name),
        args,
    );
    inner_result.map_err(|_| KineticRouterError::InsufficientSwapOut)
}

fn sort_tokens(token_a: &Address, token_b: &Address) -> (Address, Address) {
    if token_a < token_b {
        (token_a.clone(), token_b.clone())
    } else {
        (token_b.clone(), token_a.clone())
    }
}

fn pair_salt(env: &Env, token_0: &Address, token_1: &Address) -> BytesN<32> {
    let mut salt = Bytes::new(env);
    salt.append(&token_0.clone().to_xdr(env));
    salt.append(&token_1.clone().to_xdr(env));
    env.crypto().sha256(&salt).into()
}

/// Compute Soroswap pair address deterministically
pub fn compute_pair_address(
    env: &Env,
    factory: &Address,
    token_a: &Address,
    token_b: &Address,
) -> Address {
    let (token_0, token_1) = sort_tokens(token_a, token_b);
    let salt = pair_salt(env, &token_0, &token_1);
    env.deployer().with_address(factory.clone(), salt).deployed_address()
}

/// Calculate swap output (0.3% fee with ceiling arithmetic to match Soroswap)
/// Soroswap calculates fee as: fee = ceil(amount_in * 3 / 1000)
/// Then swaps on: amount_in_with_fee = amount_in - fee
fn calculate_amount_out(amount_in: i128, reserve_in: i128, reserve_out: i128) -> Option<i128> {
    if amount_in <= 0 || reserve_in <= 0 || reserve_out <= 0 {
        return None;
    }
    // Calculate fee with ceiling arithmetic: ceil(amount_in * 3 / 1000)
    // Ceiling division: (numerator + denominator - 1) / denominator
    let fee = amount_in
        .checked_mul(3)?
        .checked_add(1000 - 1)?
        .checked_div(1000)?;
    
    // Calculate amount_in_with_fee = amount_in - fee
    let amount_in_with_fee = amount_in.checked_sub(fee)?;
    
    // Apply AMM formula: amount_out = (amount_in_with_fee * reserve_out) / (reserve_in + amount_in_with_fee)
    let numerator = amount_in_with_fee.checked_mul(reserve_out)?;
    let denominator = reserve_in.checked_add(amount_in_with_fee)?;
    numerator.checked_div(denominator)
}

/// Direct pair swap - bypasses router for fewer cross-contract calls
pub fn swap_exact_tokens_direct(
    env: &Env,
    factory: &Address,
    from_token: &Address,
    to_token: &Address,
    amount_in: i128,
    min_out: i128,
    recipient: &Address,
) -> Result<i128, KineticRouterError> {
    let caller = env.current_contract_address();
    let pair_address = compute_pair_address(env, factory, from_token, to_token);
    
    // Soroswap returns Result<(i128, i128), Error>
    let (reserve_0, reserve_1): (i128, i128) = call_soroswap(
        env,
        &pair_address,
        "get_reserves",
        soroban_sdk::vec![env],
    )?;
    
    let (token_0, _token_1) = sort_tokens(from_token, to_token);
    let (reserve_in, reserve_out) = if from_token == &token_0 {
        (reserve_0, reserve_1)
    } else {
        (reserve_1, reserve_0)
    };
    
    let amount_out = calculate_amount_out(amount_in, reserve_in, reserve_out)
        .ok_or(KineticRouterError::InsufficientSwapOut)?;
    
    if amount_out < min_out {
        return Err(KineticRouterError::InsufficientSwapOut);
    }
    
    // Authorize current contract to transfer tokens to pair
    // Note: authorize_as_current_contract only authorizes the contract itself, not the EOA caller
    env.authorize_as_current_contract(soroban_sdk::vec![
        env,
        InvokerContractAuthEntry::Contract(SubContractInvocation {
            context: ContractContext {
                contract: from_token.clone(),
                fn_name: symbol_short!("transfer"),
                args: soroban_sdk::vec![
                    env,
                    caller.to_val(),
                    pair_address.to_val(),
                    amount_in.into_val(env),
                ],
            },
            sub_invocations: Vec::<InvokerContractAuthEntry>::new(env),
        }),
    ]);
    
    let _: () = env.invoke_contract(
        from_token,
        &symbol_short!("transfer"),
        soroban_sdk::vec![
            env,
            caller.to_val(),
            pair_address.to_val(),
            amount_in.into_val(env),
        ],
    );
    
    let (amount_0_out, amount_1_out) = if from_token == &token_0 {
        (0i128, amount_out)
    } else {
        (amount_out, 0i128)
    };
    
    // Soroswap returns Result<(), Error>
    let _: () = call_soroswap(
        env,
        &pair_address,
        "swap",
        soroban_sdk::vec![
            env,
            amount_0_out.into_val(env),
            amount_1_out.into_val(env),
            recipient.to_val(),
        ],
    )?;
    
    Ok(amount_out)
}

/// Swap via router (fallback)
pub fn swap_exact_tokens(
    env: &Env,
    router: &Address,
    from_token: &Address,
    to_token: &Address,
    amount_in: i128,
    min_out: i128,
    recipient: &Address,
    pair_address: Option<Address>,
) -> Result<i128, KineticRouterError> {
    let caller = env.current_contract_address();

    let mut path = Vec::new(env);
    path.push_back(from_token.clone());
    path.push_back(to_token.clone());

    let deadline = env.ledger().timestamp()
        .checked_add(3600)
        .ok_or(crate::KineticRouterError::MathOverflow)?;

    // Use cached pair address if provided, otherwise fetch from factory
    let pair_address = if let Some(pair) = pair_address {
        pair
    } else {
        // Get factory and pair addresses - Soroswap returns Result<Address, Error>
        let factory: Address = call_soroswap(
            env,
            router,
            "get_factory",
            soroban_sdk::vec![env],
        ).map_err(|_| KineticRouterError::UnauthorizedAMM)?;

        // Soroswap factory returns Result<Address, Error>
        call_soroswap(
            env,
            &factory,
            "get_pair",
            soroban_sdk::vec![env, from_token.to_val(), to_token.to_val()],
        )?
    };

    // Authorize current contract to transfer tokens to pair
    // Note: authorize_as_current_contract only authorizes the contract itself, not the EOA caller
    env.authorize_as_current_contract(soroban_sdk::vec![
        env,
        InvokerContractAuthEntry::Contract(SubContractInvocation {
            context: ContractContext {
                contract: from_token.clone(),
                fn_name: symbol_short!("transfer"),
                args: soroban_sdk::vec![
                    env,
                    caller.to_val(),
                    pair_address.to_val(),
                    amount_in.into_val(env),
                ],
            },
            sub_invocations: Vec::<InvokerContractAuthEntry>::new(env),
        }),
    ]);

    // Execute swap - Soroswap returns Result<Vec<i128>, Error>
    let amounts: Vec<i128> = call_soroswap(
        env,
        router,
        "swap_exact_tokens_for_tokens",
        soroban_sdk::vec![
            env,
            amount_in.into_val(env),
            min_out.into_val(env),
            path.to_val(),
            caller.to_val(),
            deadline.into_val(env),
        ],
    )?;

    if amounts.len() < 2 {
        return Err(KineticRouterError::InsufficientSwapOut);
    }

    let amount_out = amounts
        .get(amounts.len() - 1)
        .ok_or(KineticRouterError::InsufficientSwapOut)?;

    if amount_out < min_out {
        return Err(KineticRouterError::InsufficientSwapOut);
    }

    // Transfer to recipient if different from caller
    if recipient != &caller {
        // Authorize current contract to transfer tokens to recipient
        // Note: authorize_as_current_contract only authorizes the contract itself, not the EOA caller
        env.authorize_as_current_contract(soroban_sdk::vec![
            env,
            InvokerContractAuthEntry::Contract(SubContractInvocation {
                context: ContractContext {
                    contract: to_token.clone(),
                    fn_name: symbol_short!("transfer"),
                    args: soroban_sdk::vec![
                        env,
                        caller.to_val(),
                        recipient.to_val(),
                        amount_out.into_val(env),
                    ],
                },
                sub_invocations: Vec::<InvokerContractAuthEntry>::new(env),
            }),
        ]);

        let _: () = env.invoke_contract(
            to_token,
            &Symbol::new(env, "transfer"),
            soroban_sdk::vec![
                env,
                caller.to_val(),
                recipient.to_val(),
                amount_out.into_val(env),
            ],
        );
    }

    Ok(amount_out)
}

/// Get swap quote from Soroswap router
///
/// # Arguments
/// * `env` - Soroban environment
/// * `router` - Soroswap router contract address
/// * `from_token` - Token to swap from
/// * `to_token` - Token to swap to
/// * `amount_in` - Amount to get quote for
///
/// # Returns
/// * Expected output amount
pub fn get_swap_quote(
    env: &Env,
    router: &Address,
    from_token: &Address,
    to_token: &Address,
    amount_in: i128,
) -> Result<i128, KineticRouterError> {
    let mut path = Vec::new(env);
    path.push_back(from_token.clone());
    path.push_back(to_token.clone());

    // Soroswap returns Result<Vec<i128>, Error>
    let amounts: Vec<i128> = call_soroswap(
        env,
        router,
        "router_get_amounts_out",
        soroban_sdk::vec![env, amount_in.into_val(env), path.to_val()],
    )?;

    if amounts.len() < 2 {
        return Err(KineticRouterError::InsufficientSwapOut);
    }

    amounts
        .get(amounts.len() - 1)
        .ok_or(KineticRouterError::InsufficientSwapOut)
}

/// Check if a pair exists on Soroswap
pub fn pair_exists(env: &Env, router: &Address, token_a: &Address, token_b: &Address) -> bool {
    // Soroswap returns Result<Address, Error>
    let factory: Address = match call_soroswap(
        env,
        router,
        "get_factory",
        soroban_sdk::vec![env],
    ) {
        Ok(f) => f,
        Err(_) => return false,
    };

    // Soroswap factory returns Result<bool, Error>
    match call_soroswap::<bool>(
        env,
        &factory,
        "pair_exists",
        soroban_sdk::vec![env, token_a.to_val(), token_b.to_val()],
    ) {
        Ok(exists) => exists,
        Err(_) => false,
    }
}

/// Swap via external handler contract
/// 
/// This allows using any DEX by providing an adapter contract that implements
/// the execute_swap interface. The handler receives tokens, swaps via any DEX,
/// and returns the output tokens to the recipient.
///
/// # Arguments
/// * `env` - Soroban environment
/// * `handler` - Address of the swap handler contract
/// * `from_token` - Token to swap from
/// * `to_token` - Token to swap to
/// * `amount_in` - Amount to swap
/// * `min_out` - Minimum acceptable output
/// * `recipient` - Address to receive output tokens
///
/// # Returns
/// * Amount of tokens received
pub fn swap_via_handler(
    env: &Env,
    handler: &Address,
    from_token: &Address,
    to_token: &Address,
    amount_in: i128,
    min_out: i128,
    recipient: &Address,
) -> Result<i128, KineticRouterError> {
    let caller = env.current_contract_address();
    
    // Authorize current contract to transfer tokens to handler
    env.authorize_as_current_contract(soroban_sdk::vec![
        env,
        InvokerContractAuthEntry::Contract(SubContractInvocation {
            context: ContractContext {
                contract: from_token.clone(),
                fn_name: symbol_short!("transfer"),
                args: soroban_sdk::vec![
                    env,
                    caller.to_val(),
                    handler.to_val(),
                    amount_in.into_val(env),
                ],
            },
            sub_invocations: Vec::<InvokerContractAuthEntry>::new(env),
        }),
    ]);
    
    // Transfer tokens to handler
    let _: () = env.invoke_contract(
        from_token,
        &symbol_short!("transfer"),
        soroban_sdk::vec![
            env,
            caller.to_val(),
            handler.to_val(),
            amount_in.into_val(env),
        ],
    );
    
    // L-01
    let balance_before: i128 = env.invoke_contract(
        to_token,
        &symbol_short!("balance"),
        soroban_sdk::vec![env, recipient.to_val()],
    );
    
    // Call handler's execute_swap - handlers return Result<u128, Error>
    let reported_amount_out: u128 = call_soroswap(
        env,
        handler,
        "execute_swap",
        soroban_sdk::vec![
            env, 
            from_token.to_val(), 
            to_token.to_val(),
            safe_i128_to_u128(env, amount_in).into_val(env),
            safe_i128_to_u128(env, min_out).into_val(env),
            recipient.to_val()
        ],
    )?;
    
    // Verify actual balance increase matches or exceeds reported amount
    let balance_after: i128 = env.invoke_contract(
        to_token,
        &symbol_short!("balance"),
        soroban_sdk::vec![env, recipient.to_val()],
    );
    
    let actual_amount_out = balance_after
        .checked_sub(balance_before)
        .ok_or(KineticRouterError::MathOverflow)?;
    
    if actual_amount_out < 0 {
        return Err(KineticRouterError::InsufficientSwapOut);
    }
    
    let actual_amount_out_u128 = safe_i128_to_u128(env, actual_amount_out);
    
    // Use actual balance change, not handler-reported amount
    if actual_amount_out_u128 < safe_i128_to_u128(env, min_out) {
        return Err(KineticRouterError::InsufficientSwapOut);
    }
    
    Ok(actual_amount_out)
}

/// Get swap quote from external handler contract
/// 
/// This allows getting quotes from any DEX via an adapter contract.
/// The handler must implement a get_quote function.
///
/// # Arguments
/// * `env` - Soroban environment
/// * `handler` - Address of the swap handler contract
/// * `from_token` - Token to swap from
/// * `to_token` - Token to swap to
/// * `amount_in` - Amount to get quote for
///
/// # Returns
/// * Expected output amount
pub fn get_quote_from_handler(
    env: &Env,
    handler: &Address,
    from_token: &Address,
    to_token: &Address,
    amount_in: i128,
) -> Result<i128, KineticRouterError> {
    // Handlers return Result<u128, Error>
    let quote: u128 = call_soroswap(
        env,
        handler,
        "get_quote",
        soroban_sdk::vec![
            env, 
            from_token.to_val(), 
            to_token.to_val(),
            safe_i128_to_u128(env, amount_in).into_val(env),
        ],
    )?;
    
    Ok(safe_u128_to_i128(env, quote))
}
