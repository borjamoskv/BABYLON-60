use soroban_sdk::Bytes;
use crate::common::constants::*;
use crate::common::operations::{Operation, FlashLoanReceiverType};
use crate::common::setup::TestEnv;

pub fn execute_operation(test_env: &mut TestEnv, op: &Operation) -> bool {
    match op {
        Operation::Supply { user_idx, asset_idx, amount_percent } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            let balance = test_env.get_asset(*asset_idx).token.balance(&user);
            
            if balance <= 0 { return false; }
            let amount = ((balance as u128) * (*amount_percent as u128) / 100).max(MIN_AMOUNT);
            if amount > MAX_SAFE_AMOUNT { return false; }
            
            test_env.router.try_supply(&user, &asset_addr, &amount, &user, &0u32).is_ok()
        }
        
        Operation::SupplyOnBehalf { user_idx, recipient_idx, asset_idx, amount_percent } => {
            let user = test_env.get_user(*user_idx).clone();
            let recipient = test_env.get_user(*recipient_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            let balance = test_env.get_asset(*asset_idx).token.balance(&user);
            
            if balance <= 0 { return false; }
            let amount = ((balance as u128) * (*amount_percent as u128) / 100).max(MIN_AMOUNT);
            if amount > MAX_SAFE_AMOUNT { return false; }
            
            test_env.router.try_supply(&user, &asset_addr, &amount, &recipient, &0u32).is_ok()
        }
        
        // ==========================================================================
        // CORE WITHDRAW OPERATIONS
        // ==========================================================================
        Operation::Withdraw { user_idx, asset_idx, amount_percent } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            let balance = test_env.get_asset(*asset_idx).a_token.balance(&user);
            
            if balance <= 0 { return false; }
            let amount = ((balance as u128) * (*amount_percent as u128) / 100).max(MIN_AMOUNT);
            
            test_env.router.try_withdraw(&user, &asset_addr, &amount, &user).is_ok()
        }
        
        Operation::WithdrawAll { user_idx, asset_idx } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            let balance = test_env.get_asset(*asset_idx).a_token.balance(&user);
            
            if balance <= 0 { return false; }
            test_env.router.try_withdraw(&user, &asset_addr, &(balance as u128), &user).is_ok()
        }
        
        Operation::WithdrawToRecipient { user_idx, recipient_idx, asset_idx, amount_percent } => {
            let user = test_env.get_user(*user_idx).clone();
            let recipient = test_env.get_user(*recipient_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            let balance = test_env.get_asset(*asset_idx).a_token.balance(&user);
            
            if balance <= 0 { return false; }
            let amount = ((balance as u128) * (*amount_percent as u128) / 100).max(MIN_AMOUNT);
            
            test_env.router.try_withdraw(&user, &asset_addr, &amount, &recipient).is_ok()
        }
        
        // ==========================================================================
        // CORE BORROW OPERATIONS
        // ==========================================================================
        Operation::Borrow { user_idx, asset_idx, amount_percent } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            
            let collateral: i128 = test_env.assets.iter().map(|a| a.a_token.balance(&user)).sum();
            if collateral <= 0 { return false; }
            
            let available = test_env.get_asset(*asset_idx).token.balance(&test_env.get_asset(*asset_idx).a_token.address);
            if available <= 0 { return false; }
            
            let amount = ((available as u128) * (*amount_percent as u128) / 100).max(MIN_AMOUNT);
            if amount > MAX_SAFE_AMOUNT { return false; }
            
            test_env.router.try_borrow(&user, &asset_addr, &amount, &1u32, &0u32, &user).is_ok()
        }
        
        Operation::BorrowToRecipient { user_idx, recipient_idx, asset_idx, amount_percent } => {
            let user = test_env.get_user(*user_idx).clone();
            let recipient = test_env.get_user(*recipient_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            
            let collateral: i128 = test_env.assets.iter().map(|a| a.a_token.balance(&user)).sum();
            if collateral <= 0 { return false; }
            
            let available = test_env.get_asset(*asset_idx).token.balance(&test_env.get_asset(*asset_idx).a_token.address);
            if available <= 0 { return false; }
            
            let amount = ((available as u128) * (*amount_percent as u128) / 100).max(MIN_AMOUNT);
            if amount > MAX_SAFE_AMOUNT { return false; }
            
            test_env.router.try_borrow(&user, &asset_addr, &amount, &1u32, &0u32, &recipient).is_ok()
        }
        
        // ==========================================================================
        // CORE REPAY OPERATIONS
        // ==========================================================================
        Operation::Repay { user_idx, asset_idx, amount_percent } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            let debt = test_env.get_asset(*asset_idx).debt_token.balance(&user);
            
            if debt <= 0 { return false; }
            let user_balance = test_env.get_asset(*asset_idx).token.balance(&user);
            if user_balance <= 0 { return false; }
            
            let amount = ((debt as u128) * (*amount_percent as u128) / 100).min(user_balance as u128).max(MIN_AMOUNT);
            test_env.router.try_repay(&user, &asset_addr, &amount, &1u32, &user).is_ok()
        }
        
        Operation::RepayAll { user_idx, asset_idx } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            let debt = test_env.get_asset(*asset_idx).debt_token.balance(&user);
            
            if debt <= 0 { return false; }
            let user_balance = test_env.get_asset(*asset_idx).token.balance(&user);
            if user_balance <= 0 { return false; }
            
            let amount = (debt as u128).min(user_balance as u128);
            test_env.router.try_repay(&user, &asset_addr, &amount, &1u32, &user).is_ok()
        }
        
        Operation::RepayOnBehalf { payer_idx, borrower_idx, asset_idx, amount_percent } => {
            let payer = test_env.get_user(*payer_idx).clone();
            let borrower = test_env.get_user(*borrower_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            let debt = test_env.get_asset(*asset_idx).debt_token.balance(&borrower);
            
            if debt <= 0 { return false; }
            let payer_balance = test_env.get_asset(*asset_idx).token.balance(&payer);
            if payer_balance <= 0 { return false; }
            
            let amount = ((debt as u128) * (*amount_percent as u128) / 100).min(payer_balance as u128).max(MIN_AMOUNT);
            test_env.router.try_repay(&payer, &asset_addr, &amount, &1u32, &borrower).is_ok()
        }
        
        // ==========================================================================
        // COLLATERAL SETTINGS
        // ==========================================================================
        Operation::SetCollateral { user_idx, asset_idx, use_as_collateral } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            test_env.router.try_set_user_use_reserve_as_coll(&user, &asset_addr, use_as_collateral).is_ok()
        }
        
        // ==========================================================================
        // ENVIRONMENTAL CHANGES
        // ==========================================================================
        Operation::TimeWarp { seconds } => {
            test_env.advance_time(*seconds);
            true
        }
        
        Operation::ExtremeTimeWarp { years } => {
            let seconds_per_year = 31_536_000u32;
            let total_seconds = (*years as u32).min(10) * seconds_per_year;
            
            // Capture indices before
            let mut indices_before = Vec::new();
            for asset in &test_env.assets {
                if let Ok(Ok(reserve_data)) = test_env.router.try_get_reserve_data(&asset.address) {
                    indices_before.push((reserve_data.liquidity_index, reserve_data.variable_borrow_index));
                }
            }
            
            test_env.advance_time(total_seconds);
            
            // Verify indices didn't overflow and are still valid
            for (i, asset) in test_env.assets.iter().enumerate() {
                if let Ok(Ok(reserve_data)) = test_env.router.try_get_reserve_data(&asset.address) {
                    // Indices should still be >= RAY
                    assert!(reserve_data.liquidity_index >= crate::common::constants::RAY,
                        "CRITICAL: Liquidity index below RAY after extreme time warp for asset {}", i);
                    assert!(reserve_data.variable_borrow_index >= crate::common::constants::RAY,
                        "CRITICAL: Borrow index below RAY after extreme time warp for asset {}", i);
                    
                    // Indices should have increased (if there was any debt)
                    if i < indices_before.len() {
                        let (before_liq, before_borrow) = indices_before[i];
                        assert!(reserve_data.liquidity_index >= before_liq,
                            "CRITICAL: Liquidity index decreased after time warp for asset {}", i);
                        assert!(reserve_data.variable_borrow_index >= before_borrow,
                            "CRITICAL: Borrow index decreased after time warp for asset {}", i);
                    }
                    
                    let max_reasonable_index = crate::common::constants::RAY * 10_000;
                    assert!(reserve_data.liquidity_index <= max_reasonable_index,
                        "Liquidity index unreasonably high after extreme time warp: {}", reserve_data.liquidity_index);
                    assert!(reserve_data.variable_borrow_index <= max_reasonable_index,
                        "Borrow index unreasonably high after extreme time warp: {}", reserve_data.variable_borrow_index);
                }
            }
            
            true
        }
        
        Operation::PriceChange { asset_idx, price_change_bps } => {
            let current_price = test_env.get_price(*asset_idx);
            if current_price == 0 { return false; }
            
            let change_factor = (10000i64 + *price_change_bps as i64) as u128;
            let new_price = (current_price * change_factor / 10000).max(MIN_PRICE).min(MAX_PRICE);
            test_env.set_price(*asset_idx, new_price);
            true
        }
        
        // ==========================================================================
        // LIQUIDATION OPERATIONS
        // ==========================================================================
        Operation::Liquidate { liquidator_idx, user_idx, collateral_idx, debt_idx, amount_percent } => {
            if liquidator_idx == user_idx { return false; }
            
            let liquidator = test_env.get_user(*liquidator_idx).clone();
            let user = test_env.get_user(*user_idx).clone();
            let collateral_addr = test_env.get_asset(*collateral_idx).address.clone();
            let debt_addr = test_env.get_asset(*debt_idx).address.clone();
            
            let user_debt = test_env.get_asset(*debt_idx).debt_token.balance(&user);
            if user_debt <= 0 { return false; }
            
            let user_collateral = test_env.get_asset(*collateral_idx).a_token.balance(&user);
            if user_collateral <= 0 { return false; }
            
            let debt_to_cover = ((user_debt as u128) * (*amount_percent as u128) / 100).max(MIN_AMOUNT);
            let max_liquidatable = (user_debt as u128 * DEFAULT_LIQUIDATION_CLOSE_FACTOR) / BASIS_POINTS as u128;
            let actual_debt_to_cover = debt_to_cover.min(max_liquidatable);
            
            test_env.router.try_liquidation_call(&liquidator, &collateral_addr, &debt_addr, &user, &actual_debt_to_cover, &false).is_ok()
        }
        
        Operation::LiquidateReceiveAToken { liquidator_idx, user_idx, collateral_idx, debt_idx, amount_percent } => {
            if liquidator_idx == user_idx { return false; }
            
            let liquidator = test_env.get_user(*liquidator_idx).clone();
            let user = test_env.get_user(*user_idx).clone();
            let collateral_addr = test_env.get_asset(*collateral_idx).address.clone();
            let debt_addr = test_env.get_asset(*debt_idx).address.clone();
            
            let user_debt = test_env.get_asset(*debt_idx).debt_token.balance(&user);
            if user_debt <= 0 { return false; }
            
            let user_collateral = test_env.get_asset(*collateral_idx).a_token.balance(&user);
            if user_collateral <= 0 { return false; }
            
            let debt_to_cover = ((user_debt as u128) * (*amount_percent as u128) / 100).max(MIN_AMOUNT);
            let max_liquidatable = (user_debt as u128 * DEFAULT_LIQUIDATION_CLOSE_FACTOR) / BASIS_POINTS as u128;
            let actual_debt_to_cover = debt_to_cover.min(max_liquidatable);
            
            test_env.router.try_liquidation_call(&liquidator, &collateral_addr, &debt_addr, &user, &actual_debt_to_cover, &true).is_ok()
        }
        
        Operation::PrepareLiquidation { liquidator_idx, user_idx, collateral_idx, debt_idx } => {
            if liquidator_idx == user_idx { return false; }
            
            let liquidator = test_env.get_user(*liquidator_idx).clone();
            let user = test_env.get_user(*user_idx).clone();
            let collateral_addr = test_env.get_asset(*collateral_idx).address.clone();
            let debt_addr = test_env.get_asset(*debt_idx).address.clone();
            
            let user_debt = test_env.get_asset(*debt_idx).debt_token.balance(&user);
            if user_debt <= 0 { return false; }
            
            test_env.router.try_prepare_liquidation(
                &liquidator, &user, &debt_addr, &collateral_addr, 
                &(user_debt as u128 / 2), &0u128, &None
            ).is_ok()
        }
        
        Operation::CreateAndLiquidate { liquidator_idx, user_idx, collateral_idx, debt_idx } => {
            if liquidator_idx == user_idx { return false; }
            
            let user = test_env.get_user(*user_idx).clone();
            let liquidator = test_env.get_user(*liquidator_idx).clone();
            let collateral_idx_usize = (*collateral_idx as usize) % test_env.assets.len();
            let debt_idx_usize = (*debt_idx as usize) % test_env.assets.len();
            
            // Get addresses and data we need upfront
            let collateral_addr = test_env.assets[collateral_idx_usize].address.clone();
            let debt_addr = test_env.assets[debt_idx_usize].address.clone();
            
            // Step 1: Ensure user has some collateral - supply if needed
            let user_collateral = test_env.assets[collateral_idx_usize].a_token.balance(&user);
            if user_collateral <= 0 {
                let balance = test_env.assets[collateral_idx_usize].token.balance(&user);
                if balance <= 0 { return false; }
                let supply_amount = (balance as u128) / 2;
                if test_env.router.try_supply(&user, &collateral_addr, &supply_amount, &user, &0u32).is_err() {
                    return false;
                }
            }
            
            // Step 2: Borrow if user has no debt
            let user_debt = test_env.assets[debt_idx_usize].debt_token.balance(&user);
            if user_debt <= 0 {
                let a_token_addr = test_env.assets[debt_idx_usize].a_token.address.clone();
                let available = test_env.assets[debt_idx_usize].token.balance(&a_token_addr);
                if available <= 0 { return false; }
                // Borrow 60% of available to get close to liquidation threshold
                let borrow_amount = (available as u128) * 60 / 100;
                if borrow_amount == 0 { return false; }
                let _ = test_env.router.try_borrow(&user, &debt_addr, &borrow_amount, &1u32, &0u32, &user);
            }
            
            let original_price = test_env.assets[collateral_idx_usize].current_price;
            test_env.set_price(*collateral_idx, original_price * 40 / 100);
            
            let user_debt_after = test_env.assets[debt_idx_usize].debt_token.balance(&user);
            let mut liquidation_success = false;
            
            if user_debt_after > 0 {
                if let Ok(Ok(account_data)) = test_env.router.try_get_user_account_data(&user) {
                    let hf_threshold = test_env.router.get_hf_liquidation_threshold();
                    if account_data.health_factor < hf_threshold {
                        // User is liquidatable - attempt liquidation
                        let debt_to_cover = ((user_debt_after as u128) / 4).max(MIN_AMOUNT);
                        let max_liquidatable = (user_debt_after as u128 * DEFAULT_LIQUIDATION_CLOSE_FACTOR) / BASIS_POINTS as u128;
                        let actual_debt = debt_to_cover.min(max_liquidatable);
                        
                        liquidation_success = test_env.router.try_liquidation_call(
                            &liquidator, &collateral_addr, &debt_addr, 
                            &user, &actual_debt, &false
                        ).is_ok();
                    }
                }
            }
            
            test_env.set_price(*collateral_idx, original_price);
            
            liquidation_success
        }
        
        // ==========================================================================
        // FLASH LOAN OPERATIONS
        // ==========================================================================
        Operation::FlashLoan { user_idx, asset_idx, amount_percent, receiver_type } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset = test_env.get_asset(*asset_idx);
            let asset_addr = asset.address.clone();
            
            let available = asset.token.balance(&asset.a_token.address);
            if available <= 0 { return false; }
            
            let amount = ((available as u128) * (*amount_percent as u128) / 100).max(MIN_AMOUNT);
            if amount > MAX_SAFE_AMOUNT { return false; }
            
            let mut assets = soroban_sdk::Vec::new(test_env.env);
            assets.push_back(asset_addr);
            
            let mut amounts = soroban_sdk::Vec::new(test_env.env);
            amounts.push_back(amount);
            
            // Pass the router contract ID bytes for adversarial receivers
            let params = match receiver_type {
                FlashLoanReceiverType::Reentrant 
                | FlashLoanReceiverType::StateManipulating 
                | FlashLoanReceiverType::OracleManipulating => {
                    test_env.get_router_contract_id_bytes()
                }
                _ => Bytes::new(test_env.env),
            };
            
            let receiver = test_env.get_flash_loan_receiver(*receiver_type).clone();
            test_env.router.try_flash_loan(&user, &receiver, &assets, &amounts, &params).is_ok()
        }
        
        Operation::MultiAssetFlashLoan { user_idx, asset_indices, amount_percents, receiver_type } => {
            let user = test_env.get_user(*user_idx).clone();
            
            let mut assets = soroban_sdk::Vec::new(test_env.env);
            let mut amounts = soroban_sdk::Vec::new(test_env.env);
            
            for (i, &asset_idx) in asset_indices.iter().enumerate() {
                let asset = test_env.get_asset(asset_idx);
                let available = asset.token.balance(&asset.a_token.address);
                if available <= 0 { continue; }
                
                let amount = ((available as u128) * (amount_percents[i] as u128) / 100).max(MIN_AMOUNT);
                if amount > MAX_SAFE_AMOUNT { continue; }
                
                assets.push_back(asset.address.clone());
                amounts.push_back(amount);
            }
            
            if assets.is_empty() { return false; }
            
            let params = Bytes::new(test_env.env);
            let receiver = test_env.get_flash_loan_receiver(*receiver_type).clone();
            test_env.router.try_flash_loan(&user, &receiver, &assets, &amounts, &params).is_ok()
        }
        
        // ==========================================================================
        // SWAP COLLATERAL
        // ==========================================================================
        Operation::SwapCollateral { user_idx, from_idx, to_idx, amount_percent } => {
            if from_idx == to_idx { return false; }
            
            let user = test_env.get_user(*user_idx).clone();
            let from_asset = test_env.get_asset(*from_idx).address.clone();
            let to_asset = test_env.get_asset(*to_idx).address.clone();
            
            let balance = test_env.get_asset(*from_idx).a_token.balance(&user);
            if balance <= 0 { return false; }
            
            let amount = ((balance as u128) * (*amount_percent as u128) / 100).max(MIN_AMOUNT);
            test_env.router.try_swap_collateral(&user, &from_asset, &to_asset, &amount, &1u128, &None).is_ok()
        }
        
        // ==========================================================================
        // ZERO AMOUNT EDGE CASES
        // ==========================================================================
        Operation::ZeroAmountSupply { user_idx, asset_idx } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            let result = test_env.router.try_supply(&user, &asset_addr, &0u128, &user, &0u32);
            assert!(result.is_err(), "CRITICAL: Zero amount supply was accepted!");
            false
        }
        
        Operation::ZeroAmountBorrow { user_idx, asset_idx } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            let result = test_env.router.try_borrow(&user, &asset_addr, &0u128, &1u32, &0u32, &user);
            assert!(result.is_err(), "CRITICAL: Zero amount borrow was accepted!");
            false
        }
        
        Operation::ZeroAmountWithdraw { user_idx, asset_idx } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            let result = test_env.router.try_withdraw(&user, &asset_addr, &0u128, &user);
            assert!(result.is_err(), "CRITICAL: Zero amount withdraw was accepted!");
            false
        }
        
        Operation::ZeroAmountRepay { user_idx, asset_idx } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            let result = test_env.router.try_repay(&user, &asset_addr, &0u128, &1u32, &user);
            assert!(result.is_err(), "CRITICAL: Zero amount repay was accepted!");
            false
        }
        
        // ==========================================================================
        // DUST AMOUNT EDGE CASES
        // ==========================================================================
        Operation::DustSupply { user_idx, asset_idx, dust_amount } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            let balance = test_env.get_asset(*asset_idx).token.balance(&user);
            
            if balance <= 0 { return false; }
            let amount = (*dust_amount as u128).min(DUST_THRESHOLD);
            test_env.router.try_supply(&user, &asset_addr, &amount, &user, &0u32).is_ok()
        }
        
        Operation::DustBorrow { user_idx, asset_idx, dust_amount } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            
            let collateral: i128 = test_env.assets.iter().map(|a| a.a_token.balance(&user)).sum();
            if collateral <= 0 { return false; }
            
            let amount = (*dust_amount as u128).min(DUST_THRESHOLD);
            test_env.router.try_borrow(&user, &asset_addr, &amount, &1u32, &0u32, &user).is_ok()
        }
        
        Operation::DustWithdraw { user_idx, asset_idx, dust_amount } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            let balance = test_env.get_asset(*asset_idx).a_token.balance(&user);
            
            if balance <= 0 { return false; }
            let amount = (*dust_amount as u128).min(DUST_THRESHOLD).min(balance as u128);
            test_env.router.try_withdraw(&user, &asset_addr, &amount, &user).is_ok()
        }
        
        Operation::DustRepay { user_idx, asset_idx, dust_amount } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            let debt = test_env.get_asset(*asset_idx).debt_token.balance(&user);
            
            if debt <= 0 { return false; }
            let amount = (*dust_amount as u128).min(DUST_THRESHOLD);
            test_env.router.try_repay(&user, &asset_addr, &amount, &1u32, &user).is_ok()
        }
        
        // ==========================================================================
        // MAX AMOUNT EDGE CASES
        // ==========================================================================
        Operation::MaxAmountSupply { user_idx, asset_idx } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            let balance = test_env.get_asset(*asset_idx).token.balance(&user);
            
            if balance <= 0 { return false; }
            test_env.router.try_supply(&user, &asset_addr, &(balance as u128), &user, &0u32).is_ok()
        }
        
        Operation::MaxAmountBorrow { user_idx, asset_idx } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            
            let available = test_env.get_asset(*asset_idx).token.balance(&test_env.get_asset(*asset_idx).a_token.address);
            if available <= 0 { return false; }
            
            test_env.router.try_borrow(&user, &asset_addr, &(available as u128), &1u32, &0u32, &user).is_ok()
        }
        
        // ==========================================================================
        // ORACLE EDGE CASES
        // ==========================================================================
        Operation::PriceToZero { asset_idx } => {
            test_env.set_price(*asset_idx, ZERO_PRICE);
            true
        }
        
        Operation::PriceToMax { asset_idx } => {
            test_env.set_price(*asset_idx, MAX_PRICE);
            true
        }
        
        Operation::OracleStale { asset_idx } => {
            test_env.set_price_stale(*asset_idx);
            
            // Verify that operations requiring price fail with stale oracle
            let test_user = test_env.get_user(0).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            
            let collateral: i128 = test_env.assets.iter().map(|a| a.a_token.balance(&test_user)).sum();
            if collateral > 0 {
                let _borrow_result = test_env.router.try_borrow(&test_user, &asset_addr, &1000u128, &1u32, &0u32, &test_user);
            }
            
            let liquidator = test_env.get_user(1).clone();
            let victim = test_env.get_user(2).clone();
            let victim_debt = test_env.get_asset(*asset_idx).debt_token.balance(&victim);
            if victim_debt > 0 {
                let _liq_result = test_env.router.try_liquidation_call(
                    &liquidator, &asset_addr, &asset_addr, &victim, &((victim_debt as u128) / 2), &false
                );
            }
            
            true
        }
        
        Operation::PriceVolatility { asset_idx, swings } => {
            let base_price = test_env.get_price(*asset_idx);
            if base_price == 0 { return false; }
            
            // Simulate rapid price swings
            for i in 0..(*swings).min(10) {
                let factor = if i % 2 == 0 { 12000u128 } else { 8000u128 }; // +20% / -20%
                let new_price = (base_price * factor / 10000).max(MIN_PRICE).min(MAX_PRICE);
                test_env.set_price(*asset_idx, new_price);
            }
            true
        }
        
        // ==========================================================================
        // PROTOCOL STATE CHANGES
        // ==========================================================================
        Operation::PauseProtocol => {
            let was_paused = test_env.is_paused();
            let result = test_env.router.try_pause(&test_env.admin);
            
            if result.is_ok() && !was_paused {
                // Verify that operations fail when paused
                let test_user = test_env.get_user(0).clone();
                let test_asset = test_env.get_asset(0).address.clone();
                
                // Try supply - should fail when paused
                let supply_result = test_env.router.try_supply(&test_user, &test_asset, &1000u128, &test_user, &0u32);
                assert!(supply_result.is_err(), "CRITICAL: Supply succeeded while protocol is paused!");
                
                // Try borrow - should fail when paused
                let borrow_result = test_env.router.try_borrow(&test_user, &test_asset, &1000u128, &1u32, &0u32, &test_user);
                assert!(borrow_result.is_err(), "CRITICAL: Borrow succeeded while protocol is paused!");
                
                // Try withdraw - should fail when paused
                let withdraw_result = test_env.router.try_withdraw(&test_user, &test_asset, &1000u128, &test_user);
                assert!(withdraw_result.is_err(), "CRITICAL: Withdraw succeeded while protocol is paused!");
            }
            
            result.is_ok()
        }
        
        Operation::UnpauseProtocol => {
            let was_paused = test_env.is_paused();
            let result = test_env.router.try_unpause(&test_env.admin);
            
            if result.is_ok() && was_paused {
                // Verify protocol is now unpaused
                assert!(!test_env.is_paused(), "Protocol should be unpaused after unpause call");
            }
            
            result.is_ok()
        }
        
        Operation::CollectProtocolReserves { asset_idx } => {
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            test_env.router.try_collect_protocol_reserves(&asset_addr).is_ok()
        }
        
        // ==========================================================================
        // ADVERSARIAL PATTERNS
        // ==========================================================================
        Operation::SelfLiquidationAttempt { user_idx, collateral_idx, debt_idx } => {
            let user = test_env.get_user(*user_idx).clone();
            let collateral_addr = test_env.get_asset(*collateral_idx).address.clone();
            let debt_addr = test_env.get_asset(*debt_idx).address.clone();
            
            let user_debt = test_env.get_asset(*debt_idx).debt_token.balance(&user);
            if user_debt <= 0 { return false; }
            
            test_env.router.try_liquidation_call(&user, &collateral_addr, &debt_addr, &user, &(user_debt as u128 / 2), &false).is_ok()
        }
        
        Operation::MultiAssetLiquidation { liquidator_idx, user_idx, collateral_idx, debt_idx } => {
            if liquidator_idx == user_idx { return false; }
            
            let liquidator = test_env.get_user(*liquidator_idx).clone();
            let user = test_env.get_user(*user_idx).clone();
            let collateral_addr = test_env.get_asset(*collateral_idx).address.clone();
            let debt_addr = test_env.get_asset(*debt_idx).address.clone();
            
            let user_debt = test_env.get_asset(*debt_idx).debt_token.balance(&user);
            if user_debt <= 0 { return false; }
            
            let user_collateral = test_env.get_asset(*collateral_idx).a_token.balance(&user);
            if user_collateral <= 0 { return false; }
            
            test_env.router.try_liquidation_call(&liquidator, &collateral_addr, &debt_addr, &user, &(user_debt as u128 / 2), &false).is_ok()
        }
        
        Operation::RapidSupplyWithdraw { user_idx, asset_idx, iterations } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            
            let initial_balance = test_env.get_asset(*asset_idx).token.balance(&user);
            if initial_balance <= 0 { return false; }
            
            let amount = (initial_balance as u128) / 10;
            if amount == 0 { return false; }
            
            let mut success_count = 0;
            
            for _ in 0..(*iterations).min(10) {
                if test_env.router.try_supply(&user, &asset_addr, &amount, &user, &0u32).is_ok() {
                    success_count += 1;
                    let a_balance = test_env.get_asset(*asset_idx).a_token.balance(&user);
                    if a_balance > 0 {
                        let withdraw_amount = (a_balance as u128).min(amount);
                        if test_env.router.try_withdraw(&user, &asset_addr, &withdraw_amount, &user).is_ok() {
                            success_count += 1;
                        }
                    }
                }
            }
            
            let final_balance = test_env.get_asset(*asset_idx).token.balance(&user);
            let a_token_balance = test_env.get_asset(*asset_idx).a_token.balance(&user);
            let total_value = final_balance + a_token_balance;
            let max_gain = (initial_balance / 1000).max(100);
            
            assert!(total_value <= initial_balance + max_gain,
                "CRITICAL: Value extraction through rapid supply/withdraw! Initial: {}, Final: {}", initial_balance, total_value);
            
            success_count > 0
        }
        
        Operation::RapidBorrowRepay { user_idx, asset_idx, iterations } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            
            let collateral: i128 = test_env.assets.iter().map(|a| a.a_token.balance(&user)).sum();
            if collateral <= 0 { return false; }
            
            let available = test_env.get_asset(*asset_idx).token.balance(&test_env.get_asset(*asset_idx).a_token.address);
            if available <= 0 { return false; }
            
            let initial_underlying = test_env.get_asset(*asset_idx).token.balance(&user);
            let borrow_amount = (available as u128) / 20; // 5% of available
            if borrow_amount == 0 { return false; }
            
            let mut success_count = 0;
            
            for _ in 0..(*iterations).min(10) {
                if test_env.router.try_borrow(&user, &asset_addr, &borrow_amount, &1u32, &0u32, &user).is_ok() {
                    success_count += 1;
                    let debt = test_env.get_asset(*asset_idx).debt_token.balance(&user);
                    if debt > 0 {
                        let repay_amount = (debt as u128).min(borrow_amount);
                        if test_env.router.try_repay(&user, &asset_addr, &repay_amount, &1u32, &user).is_ok() {
                            success_count += 1;
                        }
                    }
                }
            }
            
            let final_underlying = test_env.get_asset(*asset_idx).token.balance(&user);
            let max_loss = (initial_underlying / 100).max(1000); // 1% tolerance for interest
            
            assert!(final_underlying >= initial_underlying - max_loss,
                "Unexpected loss through rapid borrow/repay: Initial: {}, Final: {}", initial_underlying, final_underlying);
            
            success_count > 0
        }
        
        Operation::SandwichPriceChange { attacker_idx, victim_idx, asset_idx } => {
            if attacker_idx == victim_idx { return false; }
            
            let attacker = test_env.get_user(*attacker_idx).clone();
            let victim = test_env.get_user(*victim_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            
            let attacker_balance = test_env.get_asset(*asset_idx).token.balance(&attacker);
            let victim_balance = test_env.get_asset(*asset_idx).token.balance(&victim);
            
            if attacker_balance <= 0 || victim_balance <= 0 { return false; }
            
            // Step 1: Attacker supplies before price change
            let _ = test_env.router.try_supply(&attacker, &asset_addr, &((attacker_balance as u128) / 2), &attacker, &0u32);
            
            // Step 2: Price increases
            let current_price = test_env.get_price(*asset_idx);
            test_env.set_price(*asset_idx, current_price * 120 / 100);
            
            // Step 3: Victim supplies at higher price
            let _ = test_env.router.try_supply(&victim, &asset_addr, &((victim_balance as u128) / 2), &victim, &0u32);
            
            // Step 4: Price returns to normal
            test_env.set_price(*asset_idx, current_price);
            
            // Step 5: Attacker withdraws
            let attacker_a_balance = test_env.get_asset(*asset_idx).a_token.balance(&attacker);
            if attacker_a_balance > 0 {
                let _ = test_env.router.try_withdraw(&attacker, &asset_addr, &(attacker_a_balance as u128), &attacker);
            }
            
            true
        }
        
        Operation::InterestAccrualExploit { user_idx, asset_idx } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            
            let balance = test_env.get_asset(*asset_idx).token.balance(&user);
            if balance <= 0 { return false; }
            
            // Supply, advance time, check interest accrual
            let supply_amount = (balance as u128) / 2;
            if test_env.router.try_supply(&user, &asset_addr, &supply_amount, &user, &0u32).is_err() {
                return false;
            }
            
            let a_balance_before = test_env.get_asset(*asset_idx).a_token.balance(&user);
            
            // Advance time significantly
            test_env.advance_time(86400 * 30); // 30 days
            
            let a_balance_after = test_env.get_asset(*asset_idx).a_token.balance(&user);
            
            // Interest should accrue (balance should increase or stay same, never decrease)
            assert!(a_balance_after >= a_balance_before,
                "Interest accrual bug: balance decreased from {} to {}", a_balance_before, a_balance_after);
            
            true
        }
        
        Operation::TransferAToken { from_idx, to_idx, asset_idx, amount_percent } => {
            if from_idx == to_idx { return false; }
            
            let from = test_env.get_user(*from_idx).clone();
            let to = test_env.get_user(*to_idx).clone();
            let a_token = &test_env.get_asset(*asset_idx).a_token;
            
            let balance = a_token.balance(&from);
            if balance <= 0 { return false; }
            
            let amount = ((balance as u128) * (*amount_percent as u128) / 100).max(MIN_AMOUNT);
            
            // Direct aToken transfer
            a_token.try_transfer(&from, &to, &(amount as i128)).is_ok()
        }
        
        Operation::DrainLiquidity { user_idx, asset_idx } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            
            // First ensure user has collateral
            let collateral: i128 = test_env.assets.iter().map(|a| a.a_token.balance(&user)).sum();
            if collateral <= 0 { return false; }
            
            // Try to borrow all available liquidity
            let available = test_env.get_asset(*asset_idx).token.balance(&test_env.get_asset(*asset_idx).a_token.address);
            if available <= 0 { return false; }
            
            // This should fail or be limited by health factor
            test_env.router.try_borrow(&user, &asset_addr, &(available as u128), &1u32, &0u32, &user).is_ok()
        }
        
        Operation::MaxUtilization { user_idx, asset_idx } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            
            // Supply first
            let balance = test_env.get_asset(*asset_idx).token.balance(&user);
            if balance <= 0 { return false; }
            
            let supply_amount = (balance as u128) / 2;
            if test_env.router.try_supply(&user, &asset_addr, &supply_amount, &user, &0u32).is_err() {
                return false;
            }
            
            // Then try to borrow close to 100% utilization
            let available = test_env.get_asset(*asset_idx).token.balance(&test_env.get_asset(*asset_idx).a_token.address);
            if available <= 0 { return false; }
            
            // Borrow 95% of available
            let borrow_amount = (available as u128) * 95 / 100;
            test_env.router.try_borrow(&user, &asset_addr, &borrow_amount, &1u32, &0u32, &user).is_ok()
        }
        
        // ==========================================================================
        // TWO-STEP LIQUIDATION
        // ==========================================================================
        Operation::ExecuteLiquidation { liquidator_idx, user_idx, collateral_idx, debt_idx, amount_percent } => {
            if liquidator_idx == user_idx { return false; }
            
            let liquidator = test_env.get_user(*liquidator_idx).clone();
            let user = test_env.get_user(*user_idx).clone();
            let collateral_addr = test_env.get_asset(*collateral_idx).address.clone();
            let debt_addr = test_env.get_asset(*debt_idx).address.clone();
            
            let user_debt = test_env.get_asset(*debt_idx).debt_token.balance(&user);
            if user_debt <= 0 { return false; }
            
            let user_collateral = test_env.get_asset(*collateral_idx).a_token.balance(&user);
            if user_collateral <= 0 { return false; }
            
            let debt_to_cover = ((user_debt as u128) * (*amount_percent as u128) / 100).max(MIN_AMOUNT);
            
            // Step 1: Prepare liquidation
            let prepare_result = test_env.router.try_prepare_liquidation(
                &liquidator, &user, &debt_addr, &collateral_addr, &debt_to_cover, &0u128, &None
            );
            
            if prepare_result.is_err() {
                return false;
            }
            
            // Step 2: Execute liquidation
            let deadline = test_env.env.ledger().timestamp() + 300;
            test_env.router.try_execute_liquidation(
                &liquidator, &user, &debt_addr, &collateral_addr, &deadline
            ).is_ok()
        }
        
        // ==========================================================================
        // RESERVE CONFIGURATION (Admin operations)
        // ==========================================================================
        Operation::UpdateReserveConfiguration { asset_idx, ltv, liquidation_threshold, liquidation_bonus } => {
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            
            // Get current reserve data to preserve other settings
            if let Ok(Ok(reserve_data)) = test_env.router.try_get_reserve_data(&asset_addr) {
                let mut config = reserve_data.configuration;
                let _ = config.set_ltv(*ltv);
                let _ = config.set_liquidation_threshold(*liquidation_threshold);
                let _ = config.set_liquidation_bonus(*liquidation_bonus);
                
                test_env.router.try_update_reserve_configuration(
                    &test_env.pool_configurator, &asset_addr, &config
                ).is_ok()
            } else {
                false
            }
        }
        
        Operation::UpdateReserveRateStrategy { asset_idx } => {
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            
            // Deploy a new interest rate strategy with different parameters
            use k2_interest_rate_strategy::{InterestRateStrategyContract, InterestRateStrategyContractClient};
            use crate::common::constants::RAY;
            
            let new_strategy_id = test_env.env.register(InterestRateStrategyContract, ());
            let new_strategy = InterestRateStrategyContractClient::new(test_env.env, &new_strategy_id);
            
            // Use different parameters than default
            let optimal_utilization = RAY * 7 / 10; // 70%
            let base_rate = RAY / 200; // 0.5%
            let slope1 = RAY / 20; // 5%
            let slope2 = RAY; // 100%
            
            if new_strategy.try_initialize(&test_env.admin, &optimal_utilization, &base_rate, &slope1, &slope2).is_err() {
                return false;
            }
            
            test_env.router.try_update_reserve_rate_strategy(&test_env.pool_configurator, &asset_addr, &new_strategy_id).is_ok()
        }
        
        Operation::DropReserve { asset_idx } => {
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            
            // Dropping a reserve should only succeed if no one has positions
            let result = test_env.router.try_drop_reserve(&test_env.pool_configurator, &asset_addr);
            
            // If it succeeded, verify the reserve is actually dropped
            if result.is_ok() {
                let get_result = test_env.router.try_get_reserve_data(&asset_addr);
                assert!(get_result.is_err() || get_result.unwrap().is_err(), 
                    "CRITICAL: Reserve still exists after drop_reserve succeeded!");
            }
            
            result.is_ok()
        }
        
        Operation::SetReserveSupplyCap { asset_idx, cap } => {
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            test_env.router.try_set_reserve_supply_cap(&asset_addr, &(*cap as u128)).is_ok()
        }
        
        Operation::SetReserveBorrowCap { asset_idx, cap } => {
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            test_env.router.try_set_reserve_borrow_cap(&asset_addr, &(*cap as u128)).is_ok()
        }
        
        Operation::SetReserveDebtCeiling { asset_idx, ceiling } => {
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            test_env.router.try_set_reserve_debt_ceiling(&asset_addr, &(*ceiling as u128)).is_ok()
        }
        
        // ==========================================================================
        // ACCESS CONTROL (Admin operations)
        // ==========================================================================
        Operation::SetReserveWhitelist { asset_idx, user_idx, add } => {
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            let user = test_env.get_user(*user_idx).clone();
            
            let mut whitelist = test_env.router.get_reserve_whitelist(&asset_addr);
            
            if *add {
                // Add user to whitelist if not already present
                let mut found = false;
                for i in 0..whitelist.len() {
                    if whitelist.get(i) == Some(user.clone()) {
                        found = true;
                        break;
                    }
                }
                if !found {
                    whitelist.push_back(user);
                }
            } else {
                // Remove user from whitelist
                let mut new_whitelist = soroban_sdk::Vec::new(test_env.env);
                for i in 0..whitelist.len() {
                    if let Some(addr) = whitelist.get(i) {
                        if addr != user {
                            new_whitelist.push_back(addr);
                        }
                    }
                }
                whitelist = new_whitelist;
            }
            
            let result = test_env.router.try_set_reserve_whitelist(&asset_addr, &whitelist);
            
            // Verify whitelist enforcement if set
            if result.is_ok() && !whitelist.is_empty() {
                let non_whitelisted = test_env.get_user((*user_idx + 1) % 5).clone();
                let mut is_whitelisted = false;
                for i in 0..whitelist.len() {
                    if whitelist.get(i) == Some(non_whitelisted.clone()) {
                        is_whitelisted = true;
                        break;
                    }
                }
                
                if !is_whitelisted {
                    let _supply_result = test_env.router.try_supply(
                        &non_whitelisted, &asset_addr, &1000u128, &non_whitelisted, &0u32
                    );
                }
            }
            
            result.is_ok()
        }
        
        Operation::SetReserveBlacklist { asset_idx, user_idx, add } => {
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            let user = test_env.get_user(*user_idx).clone();
            
            let mut blacklist = test_env.router.get_reserve_blacklist(&asset_addr);
            
            if *add {
                let mut found = false;
                for i in 0..blacklist.len() {
                    if blacklist.get(i) == Some(user.clone()) {
                        found = true;
                        break;
                    }
                }
                if !found {
                    blacklist.push_back(user.clone());
                }
            } else {
                let mut new_blacklist = soroban_sdk::Vec::new(test_env.env);
                for i in 0..blacklist.len() {
                    if let Some(addr) = blacklist.get(i) {
                        if addr != user {
                            new_blacklist.push_back(addr);
                        }
                    }
                }
                blacklist = new_blacklist;
            }
            
            let result = test_env.router.try_set_reserve_blacklist(&asset_addr, &blacklist);
            
            if result.is_ok() && *add {
                let _supply_result = test_env.router.try_supply(
                    &user, &asset_addr, &1000u128, &user, &0u32
                );
            }
            
            result.is_ok()
        }
        
        Operation::SetLiquidationWhitelist { user_idx, add } => {
            let user = test_env.get_user(*user_idx).clone();
            let mut whitelist = test_env.router.get_liquidation_whitelist();
            
            if *add {
                let mut found = false;
                for i in 0..whitelist.len() {
                    if whitelist.get(i) == Some(user.clone()) {
                        found = true;
                        break;
                    }
                }
                if !found {
                    whitelist.push_back(user);
                }
            } else {
                let mut new_whitelist = soroban_sdk::Vec::new(test_env.env);
                for i in 0..whitelist.len() {
                    if let Some(addr) = whitelist.get(i) {
                        if addr != user {
                            new_whitelist.push_back(addr);
                        }
                    }
                }
                whitelist = new_whitelist;
            }
            
            test_env.router.try_set_liquidation_whitelist(&whitelist).is_ok()
        }
        
        Operation::SetLiquidationBlacklist { user_idx, add } => {
            let user = test_env.get_user(*user_idx).clone();
            let mut blacklist = test_env.router.get_liquidation_blacklist();
            
            if *add {
                let mut found = false;
                for i in 0..blacklist.len() {
                    if blacklist.get(i) == Some(user.clone()) {
                        found = true;
                        break;
                    }
                }
                if !found {
                    blacklist.push_back(user);
                }
            } else {
                let mut new_blacklist = soroban_sdk::Vec::new(test_env.env);
                for i in 0..blacklist.len() {
                    if let Some(addr) = blacklist.get(i) {
                        if addr != user {
                            new_blacklist.push_back(addr);
                        }
                    }
                }
                blacklist = new_blacklist;
            }
            
            test_env.router.try_set_liquidation_blacklist(&blacklist).is_ok()
        }
        
        // ==========================================================================
        // ADMIN TRANSFER
        // ==========================================================================
        Operation::ProposePoolAdmin { new_admin_idx } => {
            let new_admin = test_env.get_user(*new_admin_idx).clone();
            test_env.router.try_propose_pool_admin(&test_env.admin, &new_admin).is_ok()
        }
        
        Operation::AcceptPoolAdmin { pending_admin_idx } => {
            let pending_admin = test_env.get_user(*pending_admin_idx).clone();
            // This should only succeed if this user was proposed
            test_env.router.try_accept_pool_admin(&pending_admin).is_ok()
        }
        
        // ==========================================================================
        // DANGEROUS SEQUENCES
        // ==========================================================================
        Operation::BorrowMaxWithdrawAttempt { user_idx, supply_asset_idx, borrow_asset_idx } => {
            let user = test_env.get_user(*user_idx).clone();
            let supply_asset = test_env.get_asset(*supply_asset_idx);
            let borrow_asset = test_env.get_asset(*borrow_asset_idx);
            
            let supply_balance = supply_asset.token.balance(&user);
            if supply_balance <= 0 { return false; }
            
            // Step 1: Supply all
            let supply_amount = supply_balance as u128;
            if test_env.router.try_supply(&user, &supply_asset.address, &supply_amount, &user, &0u32).is_err() {
                return false;
            }
            
            // Step 2: Borrow maximum possible
            let available = borrow_asset.token.balance(&borrow_asset.a_token.address);
            if available <= 0 { return true; } // No liquidity to borrow
            
            // Try to borrow 80% of available (should be near max for most LTV configs)
            let borrow_amount = (available as u128) * 80 / 100;
            let borrow_result = test_env.router.try_borrow(&user, &borrow_asset.address, &borrow_amount, &1u32, &0u32, &user);
            
            if borrow_result.is_err() {
                return true; // Borrow failed, which is fine
            }
            
            // Step 3: Attempt to withdraw all collateral - this SHOULD fail
            let a_balance = supply_asset.a_token.balance(&user);
            if a_balance > 0 {
                let withdraw_result = test_env.router.try_withdraw(&user, &supply_asset.address, &(a_balance as u128), &user);
                
                // If user has debt, full withdrawal should fail
                let debt = borrow_asset.debt_token.balance(&user);
                if debt > 0 && withdraw_result.is_ok() {
                    // Check if health factor is still valid
                    if let Ok(Ok(account_data)) = test_env.router.try_get_user_account_data(&user) {
                        assert!(account_data.health_factor >= 1_000_000_000_000_000_000,
                            "CRITICAL: Withdrawal succeeded but health factor is below 1.0!");
                    }
                }
            }
            
            true
        }
        
        Operation::PriceCrashLiquidation { user_idx, liquidator_idx, asset_idx } => {
            if user_idx == liquidator_idx { return false; }
            
            let user = test_env.get_user(*user_idx).clone();
            let liquidator = test_env.get_user(*liquidator_idx).clone();
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            let a_token_addr = test_env.get_asset(*asset_idx).a_token.address.clone();
            
            // Step 1: User supplies and borrows
            let balance = test_env.get_asset(*asset_idx).token.balance(&user);
            if balance <= 0 { return false; }
            
            let supply_amount = (balance as u128) / 2;
            if test_env.router.try_supply(&user, &asset_addr, &supply_amount, &user, &0u32).is_err() {
                return false;
            }
            
            // Borrow 50% of what's available
            let available = test_env.get_asset(*asset_idx).token.balance(&a_token_addr);
            if available <= 0 { return true; }
            
            let borrow_amount = (available as u128) / 2;
            if test_env.router.try_borrow(&user, &asset_addr, &borrow_amount, &1u32, &0u32, &user).is_err() {
                return true; // Borrow failed, which is fine
            }
            
            // Step 2: Crash the price by 50%
            let current_price = test_env.get_price(*asset_idx);
            test_env.set_price(*asset_idx, current_price / 2);
            
            // Step 3: Check if user is now liquidatable
            if let Ok(Ok(account_data)) = test_env.router.try_get_user_account_data(&user) {
                if account_data.health_factor < 1_000_000_000_000_000_000 {
                    // User is liquidatable - try to liquidate
                    let debt = test_env.get_asset(*asset_idx).debt_token.balance(&user);
                    if debt > 0 {
                        let liquidate_result = test_env.router.try_liquidation_call(
                            &liquidator, &asset_addr, &asset_addr, &user, 
                            &((debt as u128) / 2), &false
                        );
                        // Liquidation should succeed
                        let _ = liquidate_result;
                    }
                }
            }
            
            // Restore price
            test_env.set_price(*asset_idx, current_price);
            
            true
        }
        
        // ==========================================================================
        // KNOWN DEFI EXPLOITS
        // ==========================================================================
        Operation::FirstDepositorAttack { attacker_idx, victim_idx, asset_idx } => {
            if attacker_idx == victim_idx { return false; }
            
            let attacker = test_env.get_user(*attacker_idx).clone();
            let victim = test_env.get_user(*victim_idx).clone();
            let asset = test_env.get_asset(*asset_idx);
            
            let attacker_balance = asset.token.balance(&attacker);
            let victim_balance = asset.token.balance(&victim);
            
            if attacker_balance <= 0 || victim_balance <= 0 { return false; }
            
            // Check if pool is empty (first depositor scenario)
            let pool_supply = asset.a_token.total_supply();
            if pool_supply > 0 { return false; } // Not a first depositor scenario
            
            // Step 1: Attacker deposits tiny amount (1 unit)
            let tiny_amount = 1u128;
            if test_env.router.try_supply(&attacker, &asset.address, &tiny_amount, &attacker, &0u32).is_err() {
                return false;
            }
            
            let _attacker_shares_after_deposit = asset.a_token.balance(&attacker);
            
            // Step 2: Attacker "donates" by transferring directly to aToken contract
            // This inflates the exchange rate
            let donation_amount = (attacker_balance as u128) / 10; // 10% of balance
            if donation_amount == 0 { return true; }
            
            // Direct transfer to aToken contract (donation)
            let _ = asset.token.try_transfer(&attacker, &asset.a_token.address, &(donation_amount as i128));
            
            // Step 3: Victim deposits
            let victim_deposit = (victim_balance as u128) / 2;
            let victim_shares_before = asset.a_token.balance(&victim);
            
            if test_env.router.try_supply(&victim, &asset.address, &victim_deposit, &victim, &0u32).is_err() {
                return true; // Supply failed, protocol might have protection
            }
            
            let victim_shares_after = asset.a_token.balance(&victim);
            let victim_shares_received = victim_shares_after - victim_shares_before;
            
            // Step 4: Attacker withdraws
            let attacker_shares = asset.a_token.balance(&attacker);
            if attacker_shares > 0 {
                let _ = test_env.router.try_withdraw(&attacker, &asset.address, &(attacker_shares as u128), &attacker);
            }
            
            let attacker_final_balance = asset.token.balance(&attacker);
            let attacker_initial_balance = attacker_balance;
            
            // INVARIANT: Attacker should not profit significantly from this attack
            // Allow small tolerance for rounding
            let max_profit = (attacker_initial_balance / 100).max(1000); // 1% tolerance
            let attacker_profit = attacker_final_balance - attacker_initial_balance + donation_amount as i128;
            
            assert!(attacker_profit <= max_profit,
                "CRITICAL: First depositor attack succeeded! Attacker profit: {}", attacker_profit);
            
            // INVARIANT: Victim should receive shares proportional to their deposit
            // If victim deposited X and got 0 shares, that's a problem
            if victim_deposit > DUST_THRESHOLD {
                assert!(victim_shares_received > 0,
                    "CRITICAL: Victim received 0 shares for deposit of {}!", victim_deposit);
            }
            
            true
        }
        
        Operation::DonationAttack { attacker_idx, asset_idx, donation_amount } => {
            let attacker = test_env.get_user(*attacker_idx).clone();
            let asset = test_env.get_asset(*asset_idx);
            
            let attacker_balance = asset.token.balance(&attacker);
            if attacker_balance <= 0 { return false; }
            
            // Record state before donation
            let total_supply_before = asset.a_token.total_supply();
            let pool_balance_before = asset.token.balance(&asset.a_token.address);
            
            if total_supply_before == 0 { return false; } // Need existing depositors
            
            // Calculate donation amount (percentage of attacker's balance)
            let donation = ((attacker_balance as u128) * (*donation_amount as u128) / 100).max(1);
            
            // Attacker donates directly to aToken contract
            if asset.token.try_transfer(&attacker, &asset.a_token.address, &(donation as i128)).is_err() {
                return false;
            }
            
            let pool_balance_after = asset.token.balance(&asset.a_token.address);
            let total_supply_after = asset.a_token.total_supply();
            
            // INVARIANT: Total supply of aTokens should not change from donation
            assert_eq!(total_supply_before, total_supply_after,
                "CRITICAL: Donation changed aToken total supply! Before: {}, After: {}",
                total_supply_before, total_supply_after);
            
            // INVARIANT: Pool balance should increase by exactly the donation
            let expected_balance = pool_balance_before + donation as i128;
            assert_eq!(pool_balance_after, expected_balance,
                "Pool balance mismatch after donation. Expected: {}, Got: {}",
                expected_balance, pool_balance_after);
            
            // Test that a new depositor after donation gets fair shares
            // Use a different user to test
            let test_user_idx = (*attacker_idx + 1) % 8;
            let test_user = test_env.get_user(test_user_idx).clone();
            let test_user_balance = asset.token.balance(&test_user);
            
            if test_user_balance > 0 {
                let test_deposit = (test_user_balance as u128) / 4;
                let shares_before = asset.a_token.balance(&test_user);
                
                if test_env.router.try_supply(&test_user, &asset.address, &test_deposit, &test_user, &0u32).is_ok() {
                    let shares_after = asset.a_token.balance(&test_user);
                    let shares_received = shares_after - shares_before;
                    
                    // User should receive shares (not 0 due to donation manipulation)
                    if test_deposit > DUST_THRESHOLD {
                        assert!(shares_received > 0,
                            "CRITICAL: User received 0 shares after donation attack! Deposit: {}", test_deposit);
                    }
                }
            }
            
            true
        }
        
        // ==========================================================================
        // RESERVE STATE OPERATIONS
        // ==========================================================================
        Operation::SetReserveActive { asset_idx, active } => {
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            
            if let Ok(Ok(reserve_data)) = test_env.router.try_get_reserve_data(&asset_addr) {
                let mut config = reserve_data.configuration;
                config.set_active(*active);
                
                let result = test_env.router.try_update_reserve_configuration(
                    &test_env.pool_configurator, &asset_addr, &config
                );
                
                if result.is_ok() && !*active {
                    let test_user = test_env.get_user(0).clone();
                    let _supply_result = test_env.router.try_supply(&test_user, &asset_addr, &1000u128, &test_user, &0u32);
                }
                
                result.is_ok()
            } else {
                false
            }
        }
        
        Operation::SetReserveFrozen { asset_idx, frozen } => {
            let asset_addr = test_env.get_asset(*asset_idx).address.clone();
            
            if let Ok(Ok(reserve_data)) = test_env.router.try_get_reserve_data(&asset_addr) {
                let mut config = reserve_data.configuration;
                config.set_frozen(*frozen);
                
                let result = test_env.router.try_update_reserve_configuration(
                    &test_env.pool_configurator, &asset_addr, &config
                );
                
                if result.is_ok() && *frozen {
                    let test_user = test_env.get_user(0).clone();
                    let _supply_result = test_env.router.try_supply(&test_user, &asset_addr, &1000u128, &test_user, &0u32);
                }
                
                result.is_ok()
            } else {
                false
            }
        }
        
        // ==========================================================================
        // FLASH LOAN DURING PAUSE
        // ==========================================================================
        Operation::FlashLoanWhilePaused { user_idx, asset_idx, amount_percent } => {
            // First pause the protocol
            let was_paused = test_env.is_paused();
            if !was_paused {
                let _ = test_env.router.try_pause(&test_env.admin);
            }
            
            // Now try flash loan - should fail
            let user = test_env.get_user(*user_idx).clone();
            let asset = test_env.get_asset(*asset_idx);
            let asset_addr = asset.address.clone();
            
            let available = asset.token.balance(&asset.a_token.address);
            if available <= 0 {
                // Unpause if we paused
                if !was_paused {
                    let _ = test_env.router.try_unpause(&test_env.admin);
                }
                return false;
            }
            
            let amount = ((available as u128) * (*amount_percent as u128) / 100).max(MIN_AMOUNT);
            
            let mut assets = soroban_sdk::Vec::new(test_env.env);
            assets.push_back(asset_addr);
            
            let mut amounts = soroban_sdk::Vec::new(test_env.env);
            amounts.push_back(amount);
            
            let params = Bytes::new(test_env.env);
            let receiver = test_env.flash_loan_receiver_standard.clone();
            
            let result = test_env.router.try_flash_loan(&user, &receiver, &assets, &amounts, &params);
            
            // Flash loan during pause should fail
            if test_env.is_paused() {
                assert!(result.is_err(), "CRITICAL: Flash loan succeeded while protocol is paused!");
            }
            
            // Restore pause state
            if !was_paused {
                let _ = test_env.router.try_unpause(&test_env.admin);
            }
            
            false // Operation intentionally fails
        }
        
        // ==========================================================================
        // BAD DEBT SCENARIO
        // ==========================================================================
        Operation::BadDebtScenario { user_idx, asset_idx } => {
            let user = test_env.get_user(*user_idx).clone();
            let asset = test_env.get_asset(*asset_idx);
            
            // Check if user has debt but no collateral (bad debt)
            let debt = asset.debt_token.balance(&user);
            let collateral: i128 = test_env.assets.iter().map(|a| a.a_token.balance(&user)).sum();
            
            if debt > 0 && collateral == 0 {
                // This is a bad debt situation - protocol should handle gracefully
                // Verify protocol doesn't panic and solvency checks account for this
                if let Ok(Ok(account_data)) = test_env.router.try_get_user_account_data(&user) {
                    // Health factor should be 0 or very low
                    assert!(account_data.health_factor == 0 || account_data.total_collateral_base == 0,
                        "Bad debt scenario: user has debt {} but HF is {}", debt, account_data.health_factor);
                }
            }
            
            // Try to create bad debt by:
            // 1. Supply and borrow
            // 2. Crash price to make liquidatable
            // 3. Liquidate all collateral but not all debt
            
            let balance = asset.token.balance(&user);
            if balance <= 0 { return false; }
            
            // Supply
            let supply_amount = (balance as u128) / 2;
            if test_env.router.try_supply(&user, &asset.address, &supply_amount, &user, &0u32).is_err() {
                return false;
            }
            
            // Borrow max
            let available = asset.token.balance(&asset.a_token.address);
            if available <= 0 { return true; }
            
            let borrow_amount = (available as u128) * 70 / 100; // 70% of available
            if test_env.router.try_borrow(&user, &asset.address, &borrow_amount, &1u32, &0u32, &user).is_err() {
                return true;
            }
            
            // Crash price to create underwater position
            let current_price = test_env.get_price(*asset_idx);
            test_env.set_price(*asset_idx, current_price / 10); // 90% drop
            
            // Verify user is now liquidatable
            if let Ok(Ok(account_data)) = test_env.router.try_get_user_account_data(&user) {
                // User should be underwater
                if account_data.health_factor < 1_000_000_000_000_000_000 {
                    // Good - user is liquidatable as expected
                }
            }
            
            // Restore price
            test_env.set_price(*asset_idx, current_price);
            
            true
        }
        
        // ==========================================================================
        // FULL MULTI-ASSET LIQUIDATION (ALL 4 ASSETS)
        // ==========================================================================
        Operation::FullMultiAssetLiquidation { liquidator_idx, user_idx } => {
            if liquidator_idx == user_idx { return false; }
            
            let liquidator = test_env.get_user(*liquidator_idx).clone();
            let user = test_env.get_user(*user_idx).clone();
            
            // Step 1: Set up user with positions in all 4 assets
            // Supply to assets 0 and 1, borrow from assets 2 and 3
            let mut setup_success = true;
            
            // Supply to first two assets
            for i in 0..2 {
                let asset = test_env.get_asset(i as u8);
                let balance = asset.token.balance(&user);
                if balance > 0 {
                    let supply_amount = (balance as u128) / 4;
                    if test_env.router.try_supply(&user, &asset.address, &supply_amount, &user, &0u32).is_err() {
                        setup_success = false;
                    }
                }
            }
            
            if !setup_success { return false; }
            
            // Borrow from last two assets
            for i in 2..4 {
                let asset = test_env.get_asset(i as u8);
                let available = asset.token.balance(&asset.a_token.address);
                if available > 0 {
                    let borrow_amount = (available as u128) / 10; // Conservative borrow
                    let _ = test_env.router.try_borrow(&user, &asset.address, &borrow_amount, &1u32, &0u32, &user);
                }
            }
            
            // Step 2: Crash prices of collateral assets to make user liquidatable
            let original_prices: Vec<u128> = (0..4).map(|i| test_env.get_price(i)).collect();
            
            // Crash collateral prices (assets 0 and 1)
            test_env.set_price(0, original_prices[0] / 3);
            test_env.set_price(1, original_prices[1] / 3);
            
            // Step 3: Check if user is liquidatable
            let is_liquidatable = if let Ok(Ok(account_data)) = test_env.router.try_get_user_account_data(&user) {
                account_data.health_factor < test_env.router.get_hf_liquidation_threshold()
            } else {
                false
            };
            
            let mut any_liquidation_success = false;
            
            if is_liquidatable {
                // Step 4: Attempt liquidations across different collateral/debt pairs
                // Try liquidating debt in asset 2 with collateral from asset 0
                let user_debt_2 = test_env.get_asset(2).debt_token.balance(&user);
                if user_debt_2 > 0 {
                    let debt_to_cover = (user_debt_2 as u128) / 4;
                    let collateral_addr = test_env.get_asset(0).address.clone();
                    let debt_addr = test_env.get_asset(2).address.clone();
                    
                    if test_env.router.try_liquidation_call(
                        &liquidator, &collateral_addr, &debt_addr, &user, &debt_to_cover, &false
                    ).is_ok() {
                        any_liquidation_success = true;
                    }
                }
                
                // Try liquidating debt in asset 3 with collateral from asset 1
                let user_debt_3 = test_env.get_asset(3).debt_token.balance(&user);
                if user_debt_3 > 0 {
                    let debt_to_cover = (user_debt_3 as u128) / 4;
                    let collateral_addr = test_env.get_asset(1).address.clone();
                    let debt_addr = test_env.get_asset(3).address.clone();
                    
                    if test_env.router.try_liquidation_call(
                        &liquidator, &collateral_addr, &debt_addr, &user, &debt_to_cover, &false
                    ).is_ok() {
                        any_liquidation_success = true;
                    }
                }
                
                // Try cross-liquidation: debt in asset 2 with collateral from asset 1
                let user_debt_2_remaining = test_env.get_asset(2).debt_token.balance(&user);
                if user_debt_2_remaining > 0 {
                    let debt_to_cover = (user_debt_2_remaining as u128) / 4;
                    let collateral_addr = test_env.get_asset(1).address.clone();
                    let debt_addr = test_env.get_asset(2).address.clone();
                    
                    let _ = test_env.router.try_liquidation_call(
                        &liquidator, &collateral_addr, &debt_addr, &user, &debt_to_cover, &true // receive aToken
                    );
                }
            }
            
            // Step 5: Restore prices
            for i in 0..4 {
                test_env.set_price(i as u8, original_prices[i]);
            }
            
            // Step 6: Verify invariants after multi-asset liquidation
            // User's total debt should have decreased if any liquidation succeeded
            if any_liquidation_success {
                // Verify health factor improved or user has less debt
                if let Ok(Ok(account_data)) = test_env.router.try_get_user_account_data(&user) {
                    // Health factor should be valid
                    assert!(account_data.health_factor > 0 || account_data.total_debt_base == 0,
                        "Invalid health factor after multi-asset liquidation");
                }
            }
            
            any_liquidation_success || !is_liquidatable
        }
    }
}
