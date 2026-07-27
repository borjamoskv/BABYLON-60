#![cfg(test)]

//! # Fork Budget Stress Tests
//!
//! Uses a real testnet ledger snapshot to measure CPU and memory consumption
//! for operations that are failing or near budget limits on testnet.
//!
//! ## Prerequisites
//!
//! 1. Create the snapshot:
//!    ```bash
//!    cd tests/integration-tests && bash create_snapshot.sh
//!    ```
//!
//! 2. Run the tests:
//!    ```bash
//!    cargo test --package k2-integration-tests --release test_fork -- --nocapture
//!    ```
//!
//! ## What This Tests
//!
//! - Swap collateral with 2-asset fast path (should pass)
//! - Swap collateral with 3-asset full HF path (the failing case)
//! - Borrow / Supply / Withdraw baselines

use crate::gas_tracking::{CPU_LIMIT, MEM_LIMIT};
use crate::{kinetic_router, a_token, debt_token, price_oracle};
use soroban_sdk::{Address, Env, BytesN, IntoVal};
use std::path::Path;

// ---------------------------------------------------------------------------
// Testnet contract addresses
// ---------------------------------------------------------------------------

const KINETIC_ROUTER: &str = "CAPQPFROYH3F7O5WHHYUMIZ5ZFNJS5A5TXTRAWKIYEFIUSZCXAGV5YVB";
const PRICE_ORACLE: &str = "CCXSDYSW6PTU66DPDNMG332N4AVCQNIZHZ6XGSZH73GJ4UPSWG6X6NSP";

// Underlying tokens
const USDC: &str = "CDDI7LMQ76LCQSXO36AEWAPYT4IZG6ANV54GSFN42ZYZ3QRI562T37E3";
const XLM: &str = "CDLZFC3SYJYDZT7K67VZ75HPJVIEUVNIXF47ZG2FB2RMQQVU2HHGCYSC";
const SOLVBTC: &str = "CCBIZHECM6MQIZMYZK7SX2VBO4E6N2MJ37NZIKSYIUCU5RYE6JWOU7K7";
const WBTC: &str = "CBWPLT4YJFXFNDCZFUMCZZQ7UBM2FDIAXQNCM24NZODJDSJNUNMQ63PF";
const WETH: &str = "CDQLK2TTUKTSQFELPJDN6IUXHQ4S374IBXWD7VLBFU6TP6NEX5QPPRQI";
const PYUSD: &str = "CACZL3MGXXP3O6ROMB4Q36ROFULRWD6QARPE3AKWPSWMYZVF2474CBXP";

// Soroswap DEX
const SOROSWAP_ROUTER: &str = "CCJUD55AG6W5HAI5LRVNKAE5WDP5XGZBUDS5WNTIVDU7O264UZZE7BRD";

// Test user that has positions on testnet (GA72QJ... has USDC+wBTC+wETH collateral, SolvBTC debt)
const TEST_USER: &str = "GA72QJA6RP7KW3KC57XG7RIU5RDPIJJRJP6TLDVNFCBR3FOWCLYWUE5U";

// Deployer / admin
const DEPLOYER: &str = "GCCY3QZAEMIADDQ2DPY7SVABK2JDTWA5AYAHOWSC63CPATIQOFPCVAR2";

// Snapshot file path (relative to the integration-tests crate root)
// Use _v23 suffix: the raw CLI output is v25 format, converted by convert_snapshot.py
const SNAPSHOT_FILE: &str = "testnet_snapshot_v23.json";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/// Load the testnet snapshot, returning an Env with real state.
/// Skips the test if the snapshot file doesn't exist.
fn load_snapshot() -> Env {
    let snapshot_path = Path::new(env!("CARGO_MANIFEST_DIR")).join(SNAPSHOT_FILE);
    if !snapshot_path.exists() {
        eprintln!(
            "SKIP: Snapshot file not found at {:?}.\n\
             Run `cd tests/integration-tests && bash create_snapshot.sh` first.",
            snapshot_path
        );
        // Use a special return that won't fail CI
        panic!("Snapshot file not found — run create_snapshot.sh first");
    }
    let env = Env::from_ledger_snapshot_file(&snapshot_path);
    env.mock_all_auths();
    // Set large budget so we can MEASURE usage even for operations that exceed
    // real network limits. The test logic reports pass/fail based on actual limits.
    env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);
    env
}

fn addr(env: &Env, s: &str) -> Address {
    Address::from_str(env, s)
}

/// Print budget usage with percentage of limits.
fn print_budget(env: &Env, label: &str) {
    let cost = env.cost_estimate();
    let cpu = cost.budget().cpu_instruction_cost();
    let mem = cost.budget().memory_bytes_cost();
    let resources = cost.resources();

    let cpu_pct = cpu as f64 / CPU_LIMIT as f64 * 100.0;
    let mem_pct = mem as f64 / MEM_LIMIT as f64 * 100.0;

    let cpu_icon = if cpu_pct > 90.0 {
        "CRIT"
    } else if cpu_pct > 75.0 {
        "WARN"
    } else {
        " OK "
    };
    let mem_icon = if mem_pct > 90.0 {
        "CRIT"
    } else if mem_pct > 75.0 {
        "WARN"
    } else {
        " OK "
    };

    println!("--- {} ---", label);
    println!(
        "  [{}] CPU: {:>12} / {:>12} ({:>5.1}%)",
        cpu_icon, cpu, CPU_LIMIT, cpu_pct
    );
    println!(
        "  [{}] MEM: {:>12} / {:>12} ({:>5.1}%)",
        mem_icon, mem, MEM_LIMIT, mem_pct
    );
    println!(
        "  write_entries: {}, write_bytes: {}, mem_bytes: {}",
        resources.write_entries, resources.write_bytes, resources.mem_bytes
    );
    println!();
}

/// Collect a budget snapshot (cpu, mem) for comparison.
fn budget_snapshot(env: &Env) -> (u64, u64) {
    let cost = env.cost_estimate();
    (
        cost.budget().cpu_instruction_cost(),
        cost.budget().memory_bytes_cost(),
    )
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

/// Test 1: Baseline — read user account data (view function, cheap).
#[test]
fn test_fork_get_user_account_data() {
    let env = load_snapshot();
    let router_addr = addr(&env, KINETIC_ROUTER);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let user = addr(&env, TEST_USER);

    let account_data = router.get_user_account_data(&user);
    print_budget(&env, "get_user_account_data");

    println!("  total_collateral_base: {}", account_data.total_collateral_base);
    println!("  total_debt_base:       {}", account_data.total_debt_base);
    println!("  health_factor:         {}", account_data.health_factor);
    println!("  ltv:                   {}", account_data.ltv);
    println!();

    let (cpu, mem) = budget_snapshot(&env);
    assert!(
        cpu <= CPU_LIMIT,
        "get_user_account_data CPU exceeded: {} > {}",
        cpu,
        CPU_LIMIT
    );
    assert!(
        mem <= MEM_LIMIT,
        "get_user_account_data MEM exceeded: {} > {}",
        mem,
        MEM_LIMIT
    );
}

/// Test 2: Supply operation budget.
#[test]
fn test_fork_supply_budget() {
    let env = load_snapshot();
    let router_addr = addr(&env, KINETIC_ROUTER);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let user = addr(&env, TEST_USER);
    let usdc = addr(&env, USDC);

    // Supply 10 USDC (7 decimals)
    let amount = 100_000_000u128; // 10 USDC
    let result = router.try_supply(&user, &usdc, &amount, &user, &0u32);
    print_budget(&env, "supply (10 USDC)");

    match result {
        Ok(_) => println!("  Supply succeeded"),
        Err(e) => println!("  Supply failed: {:?}", e),
    }

    let (cpu, mem) = budget_snapshot(&env);
    println!(
        "  VERDICT: CPU {:.1}% | MEM {:.1}%\n",
        cpu as f64 / CPU_LIMIT as f64 * 100.0,
        mem as f64 / MEM_LIMIT as f64 * 100.0
    );
}

/// Test 3: Borrow operation budget (2 positions baseline).
#[test]
fn test_fork_borrow_budget() {
    let env = load_snapshot();
    let router_addr = addr(&env, KINETIC_ROUTER);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let user = addr(&env, TEST_USER);
    let xlm = addr(&env, XLM);

    // Borrow a small amount of XLM
    let amount = 10_000_000u128; // 1 XLM
    let result = router.try_borrow(&user, &xlm, &amount, &1u32, &0u32, &user);
    print_budget(&env, "borrow (1 XLM, ~2 positions)");

    match result {
        Ok(_) => println!("  Borrow succeeded"),
        Err(e) => println!("  Borrow failed: {:?}", e),
    }

    let (cpu, mem) = budget_snapshot(&env);
    println!(
        "  VERDICT: CPU {:.1}% | MEM {:.1}%\n",
        cpu as f64 / CPU_LIMIT as f64 * 100.0,
        mem as f64 / MEM_LIMIT as f64 * 100.0
    );
}

/// Test 4: Swap collateral — 2-asset fast path (USDC→XLM).
///
/// When the user only has positions in the swap pair, the router uses a
/// fast-path health-factor check that skips iterating all reserves.
#[test]
fn test_fork_swap_collateral_2_asset_fast_path() {
    let env = load_snapshot();
    let router_addr = addr(&env, KINETIC_ROUTER);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let user = addr(&env, TEST_USER);
    let usdc = addr(&env, USDC);
    let xlm = addr(&env, XLM);

    // Swap 5 USDC → XLM
    let amount = 50_000_000u128; // 5 USDC
    let min_out = 1u128; // Accept any output for budget measurement

    let result = router.try_swap_collateral(&user, &usdc, &xlm, &amount, &min_out, &None);
    print_budget(&env, "swap_collateral USDC->XLM (2-asset fast path)");

    match result {
        Ok(Ok(received)) => println!("  Swap succeeded, received: {}", received),
        Ok(Err(e)) => println!("  Swap contract error: {:?}", e),
        Err(e) => println!("  Swap invocation error: {:?}", e),
    }

    let (cpu, mem) = budget_snapshot(&env);
    println!(
        "  VERDICT: CPU {:.1}% | MEM {:.1}%\n",
        cpu as f64 / CPU_LIMIT as f64 * 100.0,
        mem as f64 / MEM_LIMIT as f64 * 100.0
    );
}

/// Test 5: Swap collateral — 3-asset full HF path (USDC→SolvBTC).
///
/// This is THE FAILING CASE on testnet. The user has USDC collateral +
/// XLM collateral + XLM debt, meaning a USDC→SolvBTC swap cannot use
/// the fast path and must calculate full health factor across all positions.
#[test]
fn test_fork_swap_collateral_3_asset_full_path() {
    let env = load_snapshot();
    let router_addr = addr(&env, KINETIC_ROUTER);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let user = addr(&env, TEST_USER);
    let usdc = addr(&env, USDC);
    let solvbtc = addr(&env, SOLVBTC);

    // Swap 5 USDC → SolvBTC
    let amount = 50_000_000u128; // 5 USDC
    let min_out = 1u128;

    let result =
        router.try_swap_collateral(&user, &usdc, &solvbtc, &amount, &min_out, &None);
    print_budget(&env, "swap_collateral USDC->SolvBTC (3-asset FULL HF path)");

    match &result {
        Ok(Ok(received)) => println!("  Swap succeeded, received: {}", received),
        Ok(Err(e)) => println!("  Swap contract error: {:?}", e),
        Err(e) => println!("  Swap invocation error (likely ExceededLimit): {:?}", e),
    }

    let (cpu, mem) = budget_snapshot(&env);
    println!(
        "  VERDICT: CPU {:.1}% | MEM {:.1}%",
        cpu as f64 / CPU_LIMIT as f64 * 100.0,
        mem as f64 / MEM_LIMIT as f64 * 100.0
    );

    // This test documents the failure — don't assert limits here.
    // After optimizations, uncomment to enforce:
    // assert!(cpu <= CPU_LIMIT, "swap 3-asset CPU: {}", cpu);
    // assert!(mem <= MEM_LIMIT, "swap 3-asset MEM: {}", mem);
    println!("  NOTE: This test documents current budget usage. See above for pass/fail.\n");
}

/// Upgrade the router, aToken, and debtToken contracts in the fork snapshot
/// to use locally-built WASMs. All three must be upgraded together since
/// burn_scaled/mint_scaled return types changed from bool to (bool, i128).
fn upgrade_router_in_snapshot(env: &Env) {
    let router_addr = addr(env, KINETIC_ROUTER);

    // Upload the locally-built optimized WASMs
    let router_wasm_hash: BytesN<32> = env.deployer().upload_contract_wasm(kinetic_router::WASM);
    let a_token_wasm_hash: BytesN<32> = env.deployer().upload_contract_wasm(a_token::WASM);
    let debt_token_wasm_hash: BytesN<32> = env.deployer().upload_contract_wasm(debt_token::WASM);

    // Upgrade the router contract (mock_all_auths handles admin auth)
    let router = kinetic_router::Client::new(env, &router_addr);
    router.upgrade(&router_wasm_hash);

    // Upgrade all aToken and debtToken contracts for assets involved in swap
    let assets = [USDC, XLM, SOLVBTC, WBTC, WETH, PYUSD];
    for asset_str in &assets {
        let asset = addr(env, asset_str);
        let reserve_data = router.get_reserve_data(&asset);
        // Upgrade aToken
        let a_token_client = a_token::Client::new(env, &reserve_data.a_token_address);
        a_token_client.upgrade(&a_token_wasm_hash);
        // Upgrade debtToken
        let debt_token_client = debt_token::Client::new(env, &reserve_data.debt_token_address);
        debt_token_client.upgrade(&debt_token_wasm_hash);
    }

    // Set DEX factory for direct pair swaps (inlined liquidation uses swap_exact_tokens_direct)
    let soroswap_router = addr(env, SOROSWAP_ROUTER);
    let factory: Address = env.invoke_contract(
        &soroswap_router,
        &soroban_sdk::Symbol::new(env, "get_factory"),
        soroban_sdk::vec![env],
    );
    router.set_dex_factory(&factory);

    // Reset budget counters so we only measure the swap itself
    env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);
    println!("  Router + aToken + debtToken upgraded to local WASMs (router: {} bytes)", kinetic_router::WASM.len());
    println!("  DEX factory set");
}

/// Test 5b: Swap collateral — 3-asset full HF path WITH optimized WASM.
///
/// Same as test 5, but upgrades the router to the locally-built WASM first.
/// This is the ground truth for whether our optimizations bring memory under limit.
#[test]
fn test_fork_swap_collateral_3_asset_full_path_optimized() {
    let env = load_snapshot();
    upgrade_router_in_snapshot(&env);

    let router_addr = addr(&env, KINETIC_ROUTER);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let user = addr(&env, TEST_USER);
    let usdc = addr(&env, USDC);
    let solvbtc = addr(&env, SOLVBTC);

    // Swap 5 USDC → SolvBTC
    let amount = 50_000_000u128; // 5 USDC
    let min_out = 1u128;

    let result =
        router.try_swap_collateral(&user, &usdc, &solvbtc, &amount, &min_out, &None);
    print_budget(&env, "swap_collateral USDC->SolvBTC (OPTIMIZED, 3-asset FULL HF path)");

    match &result {
        Ok(Ok(received)) => println!("  Swap succeeded, received: {}", received),
        Ok(Err(e)) => println!("  Swap contract error: {:?}", e),
        Err(e) => println!("  Swap invocation error: {:?}", e),
    }

    let (cpu, mem) = budget_snapshot(&env);
    let cpu_pct = cpu as f64 / CPU_LIMIT as f64 * 100.0;
    let mem_pct = mem as f64 / MEM_LIMIT as f64 * 100.0;
    println!(
        "  VERDICT: CPU {:.1}% | MEM {:.1}%",
        cpu_pct, mem_pct
    );

    if mem <= MEM_LIMIT && cpu <= CPU_LIMIT {
        println!("  PASS: Within budget limits!");
    } else {
        println!("  FAIL: Still exceeds budget (was 47.7MB / 113.8%)");
    }
    println!();

    // Uncomment to enforce:
    // assert!(cpu <= CPU_LIMIT, "swap 3-asset CPU: {} > {}", cpu, CPU_LIMIT);
    // assert!(mem <= MEM_LIMIT, "swap 3-asset MEM: {} > {}", mem, MEM_LIMIT);
}

// NOTE: test_fork_swap_collateral_quote removed — entry point extracted to reduce router WASM size.
// See docs/REMOVED_VIEW_FUNCTIONS.md for client-side alternatives.

/// Test 7: Withdraw operation budget.
#[test]
fn test_fork_withdraw_budget() {
    let env = load_snapshot();
    let router_addr = addr(&env, KINETIC_ROUTER);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let user = addr(&env, TEST_USER);
    let usdc = addr(&env, USDC);

    // Withdraw 1 USDC
    let amount = 10_000_000u128; // 1 USDC
    let result = router.try_withdraw(&user, &usdc, &amount, &user);
    print_budget(&env, "withdraw (1 USDC)");

    match result {
        Ok(_) => println!("  Withdraw succeeded"),
        Err(e) => println!("  Withdraw failed: {:?}", e),
    }

    let (cpu, mem) = budget_snapshot(&env);
    println!(
        "  VERDICT: CPU {:.1}% | MEM {:.1}%\n",
        cpu as f64 / CPU_LIMIT as f64 * 100.0,
        mem as f64 / MEM_LIMIT as f64 * 100.0
    );
}

/// Summary test: runs all operations and prints a comparison table.
#[test]
fn test_fork_budget_summary_table() {
    let snapshot_path = Path::new(env!("CARGO_MANIFEST_DIR")).join(SNAPSHOT_FILE);
    if !snapshot_path.exists() {
        eprintln!("SKIP: Snapshot not found. Run create_snapshot.sh first.");
        return;
    }

    println!("\n{}", "=".repeat(80));
    println!("  K2 FORK BUDGET STRESS TEST — SUMMARY");
    println!("{}\n", "=".repeat(80));

    let operations: &[(&str, Box<dyn Fn() -> (u64, u64, &'static str)>)] = &[
        (
            "get_user_account_data",
            Box::new(|| {
                let env = Env::from_ledger_snapshot_file(&snapshot_path);
                env.mock_all_auths();
                env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);
                let r = kinetic_router::Client::new(&env, &addr(&env, KINETIC_ROUTER));
                let _ = r.try_get_user_account_data(&addr(&env, TEST_USER));
                let (cpu, mem) = budget_snapshot(&env);
                (cpu, mem, "view")
            }),
        ),
        (
            "supply (10 USDC)",
            Box::new(|| {
                let env = Env::from_ledger_snapshot_file(&snapshot_path);
                env.mock_all_auths();
                env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);
                let r = kinetic_router::Client::new(&env, &addr(&env, KINETIC_ROUTER));
                let _ = r.try_supply(
                    &addr(&env, TEST_USER),
                    &addr(&env, USDC),
                    &100_000_000u128,
                    &addr(&env, TEST_USER),
                    &0u32,
                );
                let (cpu, mem) = budget_snapshot(&env);
                (cpu, mem, "supply")
            }),
        ),
        (
            "borrow (1 XLM)",
            Box::new(|| {
                let env = Env::from_ledger_snapshot_file(&snapshot_path);
                env.mock_all_auths();
                env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);
                let r = kinetic_router::Client::new(&env, &addr(&env, KINETIC_ROUTER));
                let _ = r.try_borrow(
                    &addr(&env, TEST_USER),
                    &addr(&env, XLM),
                    &10_000_000u128,
                    &1u32,
                    &0u32,
                    &addr(&env, TEST_USER),
                );
                let (cpu, mem) = budget_snapshot(&env);
                (cpu, mem, "borrow")
            }),
        ),
        (
            "withdraw (1 USDC)",
            Box::new(|| {
                let env = Env::from_ledger_snapshot_file(&snapshot_path);
                env.mock_all_auths();
                env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);
                let r = kinetic_router::Client::new(&env, &addr(&env, KINETIC_ROUTER));
                let _ = r.try_withdraw(
                    &addr(&env, TEST_USER),
                    &addr(&env, USDC),
                    &10_000_000u128,
                    &addr(&env, TEST_USER),
                );
                let (cpu, mem) = budget_snapshot(&env);
                (cpu, mem, "withdraw")
            }),
        ),
        (
            "swap USDC->XLM (fast)",
            Box::new(|| {
                let env = Env::from_ledger_snapshot_file(&snapshot_path);
                env.mock_all_auths();
                env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);
                let r = kinetic_router::Client::new(&env, &addr(&env, KINETIC_ROUTER));
                let _ = r.try_swap_collateral(
                    &addr(&env, TEST_USER),
                    &addr(&env, USDC),
                    &addr(&env, XLM),
                    &50_000_000u128,
                    &1u128,
                    &None,
                );
                let (cpu, mem) = budget_snapshot(&env);
                (cpu, mem, "swap-fast")
            }),
        ),
        (
            "swap USDC->SolvBTC (full)",
            Box::new(|| {
                let env = Env::from_ledger_snapshot_file(&snapshot_path);
                env.mock_all_auths();
                env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);
                let r = kinetic_router::Client::new(&env, &addr(&env, KINETIC_ROUTER));
                let _ = r.try_swap_collateral(
                    &addr(&env, TEST_USER),
                    &addr(&env, USDC),
                    &addr(&env, SOLVBTC),
                    &50_000_000u128,
                    &1u128,
                    &None,
                );
                let (cpu, mem) = budget_snapshot(&env);
                (cpu, mem, "swap-full")
            }),
        ),
    ];

    // Header
    println!(
        "| {:<32} | {:>12} | {:>6} | {:>12} | {:>6} | {:>6} |",
        "Operation", "CPU", "CPU %", "Memory", "MEM %", "Status"
    );
    println!(
        "|{:-<34}|{:-<14}|{:-<8}|{:-<14}|{:-<8}|{:-<8}|",
        "", "", "", "", "", ""
    );

    for (name, run_fn) in operations {
        let (cpu, mem, _tag) = run_fn();
        let cpu_pct = cpu as f64 / CPU_LIMIT as f64 * 100.0;
        let mem_pct = mem as f64 / MEM_LIMIT as f64 * 100.0;
        let status = if cpu > CPU_LIMIT || mem > MEM_LIMIT {
            "FAIL"
        } else if cpu_pct > 90.0 || mem_pct > 90.0 {
            "CRIT"
        } else if cpu_pct > 75.0 || mem_pct > 75.0 {
            "WARN"
        } else {
            "OK"
        };
        println!(
            "| {:<32} | {:>12} | {:>5.1}% | {:>12} | {:>5.1}% | {:>6} |",
            name, cpu, cpu_pct, mem, mem_pct, status
        );
    }

    println!(
        "|{:-<34}|{:-<14}|{:-<8}|{:-<14}|{:-<8}|{:-<8}|",
        "", "", "", "", "", ""
    );
    println!(
        "| {:<32} | {:>12} |        | {:>12} |        |        |",
        "LIMITS", CPU_LIMIT, MEM_LIMIT
    );
    println!();
}

/// Summary test with OPTIMIZED local WASMs — the definitive budget numbers.
#[test]
fn test_fork_budget_summary_table_optimized() {
    let snapshot_path = Path::new(env!("CARGO_MANIFEST_DIR")).join(SNAPSHOT_FILE);
    if !snapshot_path.exists() {
        eprintln!("SKIP: Snapshot not found. Run create_snapshot.sh first.");
        return;
    }

    // Helper: load snapshot + upgrade to local WASMs, return env with reset budget
    let load_and_upgrade = || -> Env {
        let env = Env::from_ledger_snapshot_file(&snapshot_path);
        env.mock_all_auths();
        env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);
        upgrade_router_in_snapshot(&env);
        // Reset budget after upgrade so we only measure the operation
        env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);
        env
    };

    println!("\n{}", "=".repeat(80));
    println!("  K2 FORK BUDGET — OPTIMIZED WASMs (local build)");
    println!("{}\n", "=".repeat(80));

    let operations: Vec<(&str, Box<dyn Fn() -> (u64, u64)>)> = vec![
        (
            "get_user_account_data (4 pos)",
            Box::new(|| {
                let env = load_and_upgrade();
                let r = kinetic_router::Client::new(&env, &addr(&env, KINETIC_ROUTER));
                let _ = r.try_get_user_account_data(&addr(&env, TEST_USER));
                budget_snapshot(&env)
            }),
        ),
        (
            "supply (10 USDC, 4 pos)",
            Box::new(|| {
                let env = load_and_upgrade();
                let r = kinetic_router::Client::new(&env, &addr(&env, KINETIC_ROUTER));
                let _ = r.try_supply(
                    &addr(&env, TEST_USER), &addr(&env, USDC),
                    &100_000_000u128, &addr(&env, TEST_USER), &0u32,
                );
                budget_snapshot(&env)
            }),
        ),
        (
            "borrow (1 XLM, 4 pos)",
            Box::new(|| {
                let env = load_and_upgrade();
                let r = kinetic_router::Client::new(&env, &addr(&env, KINETIC_ROUTER));
                let _ = r.try_borrow(
                    &addr(&env, TEST_USER), &addr(&env, XLM),
                    &10_000_000u128, &1u32, &0u32, &addr(&env, TEST_USER),
                );
                budget_snapshot(&env)
            }),
        ),
        (
            "withdraw (1 USDC, 4 pos)",
            Box::new(|| {
                let env = load_and_upgrade();
                let r = kinetic_router::Client::new(&env, &addr(&env, KINETIC_ROUTER));
                let _ = r.try_withdraw(
                    &addr(&env, TEST_USER), &addr(&env, USDC),
                    &10_000_000u128, &addr(&env, TEST_USER),
                );
                budget_snapshot(&env)
            }),
        ),
        (
            "swap USDC->XLM (fast, 4 pos)",
            Box::new(|| {
                let env = load_and_upgrade();
                let r = kinetic_router::Client::new(&env, &addr(&env, KINETIC_ROUTER));
                let _ = r.try_swap_collateral(
                    &addr(&env, TEST_USER), &addr(&env, USDC), &addr(&env, XLM),
                    &50_000_000u128, &1u128, &None,
                );
                budget_snapshot(&env)
            }),
        ),
        (
            "swap USDC->SolvBTC (full, 4 pos)",
            Box::new(|| {
                let env = load_and_upgrade();
                let r = kinetic_router::Client::new(&env, &addr(&env, KINETIC_ROUTER));
                let _ = r.try_swap_collateral(
                    &addr(&env, TEST_USER), &addr(&env, USDC), &addr(&env, SOLVBTC),
                    &50_000_000u128, &1u128, &None,
                );
                budget_snapshot(&env)
            }),
        ),
    ];

    // Header
    println!(
        "| {:<35} | {:>12} | {:>6} | {:>12} | {:>6} | {:>6} |",
        "Operation", "CPU", "CPU %", "Memory", "MEM %", "Status"
    );
    println!(
        "|{:-<37}|{:-<14}|{:-<8}|{:-<14}|{:-<8}|{:-<8}|",
        "", "", "", "", "", ""
    );

    for (name, run_fn) in &operations {
        let (cpu, mem) = run_fn();
        let cpu_pct = cpu as f64 / CPU_LIMIT as f64 * 100.0;
        let mem_pct = mem as f64 / MEM_LIMIT as f64 * 100.0;
        let status = if cpu > CPU_LIMIT || mem > MEM_LIMIT {
            "FAIL"
        } else if cpu_pct > 90.0 || mem_pct > 90.0 {
            "CRIT"
        } else if cpu_pct > 75.0 || mem_pct > 75.0 {
            "WARN"
        } else {
            "OK"
        };
        println!(
            "| {:<35} | {:>12} | {:>5.1}% | {:>12} | {:>5.1}% | {:>6} |",
            name, cpu, cpu_pct, mem, mem_pct, status
        );
    }

    println!(
        "|{:-<37}|{:-<14}|{:-<8}|{:-<14}|{:-<8}|{:-<8}|",
        "", "", "", "", "", ""
    );
    println!(
        "| {:<35} | {:>12} |        | {:>12} |        |        |",
        "LIMITS", CPU_LIMIT, MEM_LIMIT
    );
    println!();
    println!("  All operations use OPTIMIZED local WASMs (router: {} bytes)", kinetic_router::WASM.len());
    println!("  TEST_USER has 4 positions: USDC+XLM supplied, wBTC+SolvBTC borrowed");
    println!();
}

// ---------------------------------------------------------------------------
// Flash Liquidation Budget Tests (Two-Step: prepare + execute)
// ---------------------------------------------------------------------------

/// Make the deployer's position liquidatable by borrowing USDC then dropping SolvBTC price.
///
/// Strategy:
///   1. Borrow USDC against SolvBTC collateral (~$69,635 at original price, LTV 70%)
///   2. Drop SolvBTC price so HF falls below 1.0 but stays above ~0.85
///      (too deep underwater causes post-HF check to fail since liquidation bonus
///       removes more collateral value than debt covered)
///
/// For HF to IMPROVE after liquidation: collateral_value must be > 1.1 × debt
/// (where 1.1 = 1 + liquidation_bonus of 10%). This requires HF > ~0.825.
/// We target HF ≈ 0.85-0.90 for reliable liquidation.
fn make_user_liquidatable(env: &Env) {
    let oracle_addr = addr(env, PRICE_ORACLE);
    let oracle = price_oracle::Client::new(env, &oracle_addr);
    let router_addr = addr(env, KINETIC_ROUTER);
    let router = kinetic_router::Client::new(env, &router_addr);
    let deployer = addr(env, DEPLOYER);

    // Step 1: Borrow USDC against SolvBTC collateral (XLM pool is empty on testnet)
    let usdc = addr(env, USDC);
    let usdc_borrow_amounts = [
        40_000_0000000u128,  // 40,000 USDC
        10_000_0000000u128,  // 10,000 USDC
        1_000_0000000u128,   // 1,000 USDC
        100_0000000u128,     // 100 USDC
    ];
    let mut usdc_borrowed = 0u128;
    for amount in usdc_borrow_amounts {
        let r = router.try_borrow(&deployer, &usdc, &amount, &1u32, &0u32, &deployer);
        match r {
            Ok(Ok(_)) => {
                usdc_borrowed = amount;
                println!("  USDC borrow succeeded: {} USDC", amount / 10_000_000);
                break;
            }
            Ok(Err(e)) => println!("  USDC borrow {} failed: {:?}", amount / 10_000_000, e),
            Err(e) => println!("  USDC borrow {} invoke error: {:?}", amount / 10_000_000, e),
        }
    }
    if usdc_borrowed == 0 {
        println!("  ERROR: Could not borrow any USDC — liquidation tests will fail");
        return;
    }

    // Step 2: Read current HF and original SolvBTC price, then compute target price
    // for HF ≈ 0.88 (deep enough for 100% close factor, but not so deep that
    // liquidation bonus makes HF worse — HF must be > ~0.825 for improvement).
    let account_data = router.get_user_account_data(&deployer);
    let current_hf = account_data.health_factor;
    println!("  After borrow — HF: {}, collateral_base: {}, debt_base: {}",
        current_hf, account_data.total_collateral_base, account_data.total_debt_base);

    let solvbtc_asset = price_oracle::Asset::Stellar(addr(env, SOLVBTC));
    let original_price = oracle.get_asset_price(&solvbtc_asset);
    println!("  Original SolvBTC price (14 dec): {}", original_price);

    // HF scales linearly with collateral price:
    //   target_HF / current_HF = target_price / original_price
    //   target_price = original_price * target_HF / current_HF
    // WAD = 10^18
    let target_hf_wad = 880_000_000_000_000_000u128; // 0.88 WAD
    // target_price = original_price * target_hf_wad / current_hf
    let target_price = original_price
        .checked_mul(target_hf_wad).expect("mul overflow")
        .checked_div(current_hf).expect("div zero");

    println!("  Target SolvBTC price (14 dec): {} (ratio: {}x drop)",
        target_price, original_price / target_price.max(1));

    // Step 3: Set SolvBTC price (reset circuit breaker first)
    oracle.reset_circuit_breaker(&deployer, &solvbtc_asset);
    let expiry = env.ledger().timestamp() + 86400;
    oracle.set_manual_override(&deployer, &solvbtc_asset, &Some(target_price), &Some(expiry));

    // Verify HF
    let account_data = router.get_user_account_data(&deployer);
    println!("  After price drop — Deployer HF: {}, collateral: {}, debt: {}",
        account_data.health_factor, account_data.total_collateral_base, account_data.total_debt_base);
}

/// Returns the address to liquidate (deployer, since we create position with deployer).
fn get_liquidatable_user(env: &Env) -> Address {
    addr(env, DEPLOYER)
}

/// Test 9a: Debug - check oracle config and prices.
#[test]
fn test_fork_debug_oracle_prices() {
    let env = load_snapshot();
    let router_addr = addr(&env, KINETIC_ROUTER);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let oracle_addr = addr(&env, PRICE_ORACLE);
    let oracle = price_oracle::Client::new(&env, &oracle_addr);
    let user = addr(&env, TEST_USER);
    let deployer = addr(&env, DEPLOYER);

    let account_data = router.get_user_account_data(&user);
    println!("  TEST_USER account data:");
    println!("    total_collateral_base: {}", account_data.total_collateral_base);
    println!("    total_debt_base: {}", account_data.total_debt_base);
    println!("    health_factor: {}", account_data.health_factor);
    println!("    ltv: {}", account_data.ltv);

    let deployer_data = router.get_user_account_data(&deployer);
    println!("  DEPLOYER account data:");
    println!("    total_collateral_base: {}", deployer_data.total_collateral_base);
    println!("    total_debt_base: {}", deployer_data.total_debt_base);
    println!("    health_factor: {}", deployer_data.health_factor);
    println!("    ltv: {}", deployer_data.ltv);

    let oracle_config = oracle.get_oracle_config();
    println!("  Oracle config:");
    println!("    price_precision: {}", oracle_config.price_precision);
    println!("    wad_precision: {}", oracle_config.wad_precision);
    println!("    conversion_factor: {}", oracle_config.conversion_factor);

    let usdc_asset = price_oracle::Asset::Stellar(addr(&env, USDC));
    let xlm_asset = price_oracle::Asset::Stellar(addr(&env, XLM));
    let solvbtc_asset = price_oracle::Asset::Stellar(addr(&env, SOLVBTC));

    match oracle.try_get_asset_price(&usdc_asset) {
        Ok(Ok(p)) => println!("  USDC price: {}", p),
        Ok(Err(e)) => println!("  USDC price error: {:?}", e),
        Err(e) => println!("  USDC price invoke error: {:?}", e),
    }
    match oracle.try_get_asset_price(&xlm_asset) {
        Ok(Ok(p)) => println!("  XLM price: {}", p),
        Ok(Err(e)) => println!("  XLM price error: {:?}", e),
        Err(e) => println!("  XLM price invoke error: {:?}", e),
    }
    match oracle.try_get_asset_price(&solvbtc_asset) {
        Ok(Ok(p)) => println!("  SolvBTC price: {}", p),
        Ok(Err(e)) => println!("  SolvBTC price error: {:?}", e),
        Err(e) => println!("  SolvBTC price invoke error: {:?}", e),
    }
    println!();
}

/// Test 9: prepare_liquidation budget (TX1 of two-step flash liquidation).
///
/// This is the validation step: oracle price fetch, HF calculation, close factor check.
#[test]
fn test_fork_prepare_liquidation_budget() {
    let env = load_snapshot();
    upgrade_router_in_snapshot(&env);
    make_user_liquidatable(&env);

    let router_addr = addr(&env, KINETIC_ROUTER);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let user = get_liquidatable_user(&env); // deployer (has USDC collateral + XLM debt)
    let liquidator = addr(&env, TEST_USER); // use test_user as liquidator

    // Verify user is liquidatable
    let account_data = router.get_user_account_data(&user);
    println!("  User (deployer) HF: {}", account_data.health_factor);
    println!("  Total collateral base: {}", account_data.total_collateral_base);
    println!("  Total debt base: {}", account_data.total_debt_base);

    if account_data.health_factor >= 1_000_000_000_000_000_000u128 {
        println!("  SKIP: User is not liquidatable (HF >= 1.0)");
        return;
    }

    // Reset budget to only measure prepare_liquidation
    env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);

    let solvbtc = addr(&env, SOLVBTC);
    let usdc = addr(&env, USDC);
    let debt_to_cover = 10_0000000u128; // 10 USDC (7 decimals) // 50 USDC (7 decimals)
    let min_swap_out = 1u128;

    let result = router.try_prepare_liquidation(
        &liquidator,
        &user,
        &usdc,     // debt asset (deployer borrowed USDC)
        &solvbtc,  // collateral asset (deployer has SolvBTC)
        &debt_to_cover,
        &min_swap_out,
        &None::<Address>,
    );
    print_budget(&env, "prepare_liquidation (SolvBTC collateral, USDC debt)");

    match &result {
        Ok(Ok(auth)) => {
            println!("  prepare_liquidation succeeded");
            println!("    nonce: {}", auth.nonce);
            println!("    debt_to_cover: {}", auth.debt_to_cover);
            println!("    collateral_to_seize: {}", auth.collateral_to_seize);
            println!("    expires_at: {}", auth.expires_at);
        }
        Ok(Err(e)) => println!("  prepare_liquidation contract error: {:?}", e),
        Err(e) => println!("  prepare_liquidation invocation error: {:?}", e),
    }

    let (cpu, mem) = budget_snapshot(&env);
    let cpu_pct = cpu as f64 / CPU_LIMIT as f64 * 100.0;
    let mem_pct = mem as f64 / MEM_LIMIT as f64 * 100.0;
    println!(
        "  VERDICT: CPU {:.1}% | MEM {:.1}%\n",
        cpu_pct, mem_pct
    );
}

/// Test 10: execute_liquidation budget (TX2 of two-step flash liquidation).
///
/// This is the atomic execution: flash loan, DEX swap, debt repayment, collateral seizure.
/// This is THE expensive operation — includes the flash loan callback with ~10+ cross-contract calls.
#[test]
fn test_fork_execute_liquidation_budget() {
    let env = load_snapshot();
    upgrade_router_in_snapshot(&env);
    make_user_liquidatable(&env);

    let router_addr = addr(&env, KINETIC_ROUTER);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let user = get_liquidatable_user(&env);
    let liquidator = addr(&env, TEST_USER);

    // Verify user is liquidatable
    let account_data = router.get_user_account_data(&user);
    println!("  User HF: {}", account_data.health_factor);

    if account_data.health_factor >= 1_000_000_000_000_000_000u128 {
        println!("  SKIP: User is not liquidatable");
        return;
    }

    let solvbtc = addr(&env, SOLVBTC);
    let usdc = addr(&env, USDC);
    let debt_to_cover = 10_0000000u128; // 10 USDC (7 decimals) // 50 USDC
    let min_swap_out = 1u128;

    // Step 1: Prepare liquidation (budget not measured)
    let auth_result = router.try_prepare_liquidation(
        &liquidator,
        &user,
        &usdc,    // debt asset
        &solvbtc, // collateral asset
        &debt_to_cover,
        &min_swap_out,
        &None::<Address>,
    );

    match &auth_result {
        Ok(Ok(auth)) => {
            println!("  prepare_liquidation succeeded (nonce: {})", auth.nonce);
        }
        Ok(Err(e)) => {
            println!("  prepare_liquidation failed: {:?}", e);
            return;
        }
        Err(e) => {
            println!("  prepare_liquidation invocation error: {:?}", e);
            return;
        }
    }

    // Reset budget to only measure execute_liquidation
    env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);

    let deadline = env.ledger().timestamp() + 300;

    let result = router.try_execute_liquidation(
        &liquidator,
        &user,
        &usdc,    // debt asset
        &solvbtc, // collateral asset
        &deadline,
    );
    print_budget(&env, "execute_liquidation (SolvBTC collateral, USDC debt, Soroswap swap)");

    match &result {
        Ok(Ok(_)) => println!("  execute_liquidation succeeded"),
        Ok(Err(e)) => println!("  execute_liquidation contract error: {:?}", e),
        Err(e) => println!("  execute_liquidation invocation error: {:?}", e),
    }

    let (cpu, mem) = budget_snapshot(&env);
    let cpu_pct = cpu as f64 / CPU_LIMIT as f64 * 100.0;
    let mem_pct = mem as f64 / MEM_LIMIT as f64 * 100.0;
    println!(
        "  VERDICT: CPU {:.1}% | MEM {:.1}%",
        cpu_pct, mem_pct
    );

    if mem <= MEM_LIMIT && cpu <= CPU_LIMIT {
        println!("  PASS: Within budget limits!");
    } else {
        println!("  FAIL: Exceeds budget limits");
    }
    println!();
}

/// Seed Soroswap USDC/SolvBTC pair with liquidity for DEX swap during execute_liquidation.
///
/// The execute_liquidation callback swaps collateral (USDC) → debt (SolvBTC) via Soroswap.
/// The testnet snapshot may not have this pair or may have insufficient liquidity.
/// This function creates the pair and adds liquidity using the Soroswap router.
fn seed_soroswap_liquidity(env: &Env) {
    use soroban_sdk::Symbol;
    let soroswap_router = addr(env, SOROSWAP_ROUTER);
    let deployer = addr(env, DEPLOYER);
    let usdc = addr(env, USDC);
    let solvbtc = addr(env, SOLVBTC);

    // Mint generous amounts of both tokens to deployer
    // SolvBTC: 8 decimals, USDC: 7 decimals
    // Price ratio: ~100,000 USDC per BTC (but BTC is inflated 27x, so use base ratio)
    let usdc_amount = 100_000_0000000i128;    // 100,000 USDC (7 decimals)
    let solvbtc_amount = 1_00000000i128;       // 1 SolvBTC (8 decimals)

    let usdc_sac = soroban_sdk::token::StellarAssetClient::new(env, &usdc);
    let solvbtc_sac = soroban_sdk::token::StellarAssetClient::new(env, &solvbtc);
    usdc_sac.mint(&deployer, &usdc_amount);
    solvbtc_sac.mint(&deployer, &solvbtc_amount);

    // Approve Soroswap router to spend tokens
    let usdc_token = soroban_sdk::token::Client::new(env, &usdc);
    let solvbtc_token = soroban_sdk::token::Client::new(env, &solvbtc);
    let seq = env.ledger().sequence();
    usdc_token.approve(&deployer, &soroswap_router, &usdc_amount, &(seq + 10000));
    solvbtc_token.approve(&deployer, &soroswap_router, &solvbtc_amount, &(seq + 10000));

    // Call Soroswap router.add_liquidity(token_a, token_b, amount_a_desired, amount_b_desired,
    //   amount_a_min, amount_b_min, to, deadline)
    let deadline = env.ledger().timestamp() + 3600u64;
    let add_liq_result = env.try_invoke_contract::<(i128, i128, i128), soroban_sdk::Error>(
        &soroswap_router,
        &Symbol::new(env, "add_liquidity"),
        soroban_sdk::vec![
            env,
            usdc.to_val(),
            solvbtc.to_val(),
            usdc_amount.into_val(env),
            solvbtc_amount.into_val(env),
            0i128.into_val(env),       // amount_a_min
            0i128.into_val(env),       // amount_b_min
            deployer.to_val(),         // to (LP recipient)
            deadline.into_val(env),    // deadline
        ],
    );
    match add_liq_result {
        Ok(Ok((a, b, lp))) => println!("  Soroswap liquidity seeded: USDC={}, SolvBTC={}, LP={}", a, b, lp),
        Ok(Err(e)) => println!("  Soroswap add_liquidity contract error: {:?}", e),
        Err(e) => println!("  Soroswap add_liquidity invoke error: {:?}", e),
    }
}

/// Test 10b: Two-step execute_liquidation budget with 4 positions.
///
/// TEST_USER has 4 real testnet positions: USDC supplied, XLM supplied, wBTC borrowed, SolvBTC borrowed.
/// Inflate BTC prices to make debt exceed collateral (HF < 1.0).
/// Cover FULL SolvBTC debt to avoid min_remaining_debt violations.
/// Uses USDC collateral + SolvBTC debt (Soroswap has USDC/SolvBTC liquidity).
#[test]
fn test_fork_execute_liquidation_budget_4_positions() {
    let env = load_snapshot();
    upgrade_router_in_snapshot(&env);

    let router_addr = addr(&env, KINETIC_ROUTER);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let oracle_addr = addr(&env, PRICE_ORACLE);
    let oracle = price_oracle::Client::new(&env, &oracle_addr);
    let user = addr(&env, TEST_USER);
    let liquidator = addr(&env, DEPLOYER);

    // Check TEST_USER's current positions (4 positions on testnet)
    let account_data = router.get_user_account_data(&user);
    println!("  TEST_USER before price change:");
    println!("    HF: {}", account_data.health_factor);
    println!("    collateral_base: {}", account_data.total_collateral_base);
    println!("    debt_base: {}", account_data.total_debt_base);

    // Inflate BTC prices 27x to push HF below 0.5 (enables 100% close factor).
    // Needed because SolvBTC debt is tiny (~50_000 units) and min_remaining_debt
    // prevents partial liquidation. With 100% close factor, we cover all debt.
    // M=14 → HF=0.934, M=27 → HF≈0.48 (below 0.5 threshold)
    let solvbtc_asset = price_oracle::Asset::Stellar(addr(&env, SOLVBTC));
    let wbtc_asset = price_oracle::Asset::Stellar(addr(&env, WBTC));
    let expiry = env.ledger().timestamp() + 86400;

    let original_solvbtc_price = oracle.get_asset_price(&solvbtc_asset);
    let original_wbtc_price = oracle.get_asset_price(&wbtc_asset);

    oracle.reset_circuit_breaker(&liquidator, &solvbtc_asset);
    oracle.set_manual_override(&liquidator, &solvbtc_asset, &Some(original_solvbtc_price * 27), &Some(expiry));
    oracle.reset_circuit_breaker(&liquidator, &wbtc_asset);
    oracle.set_manual_override(&liquidator, &wbtc_asset, &Some(original_wbtc_price * 27), &Some(expiry));

    let account_data = router.get_user_account_data(&user);
    println!("  TEST_USER after BTC price 27x inflation:");
    println!("    HF: {}", account_data.health_factor);
    println!("    collateral_base: {}", account_data.total_collateral_base);
    println!("    debt_base: {}", account_data.total_debt_base);

    if account_data.health_factor >= 1_000_000_000_000_000_000u128 {
        println!("  SKIP: User is not liquidatable");
        return;
    }

    // Seed Soroswap USDC/SolvBTC liquidity for DEX swap during execute_liquidation
    seed_soroswap_liquidity(&env);

    // Cover FULL SolvBTC debt (avoid min_remaining_debt violation).
    // User has ~0.0005 SolvBTC debt = 50_000 units at 8 decimals.
    let solvbtc = addr(&env, SOLVBTC);
    let usdc = addr(&env, USDC);
    let debt_to_cover = 50_000u128; // ~0.0005 SolvBTC (full debt, 100% close factor)
    let min_swap_out = 1u128;

    // Reset budget before prepare+execute
    env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);

    // Step 1: prepare_liquidation (USDC collateral, SolvBTC debt)
    let auth_result = router.try_prepare_liquidation(
        &liquidator, &user, &solvbtc, &usdc,
        &debt_to_cover, &min_swap_out, &None::<Address>,
    );
    match &auth_result {
        Ok(Ok(auth)) => println!("  prepare_liquidation succeeded (nonce: {}, debt: {}, collateral: {})",
            auth.nonce, auth.debt_to_cover, auth.collateral_to_seize),
        Ok(Err(e)) => { println!("  prepare_liquidation contract error: {:?}", e); return; }
        Err(e) => { println!("  prepare_liquidation invoke error: {:?}", e); return; }
    }

    // Pre-fund the USDC aToken with enough USDC for the collateral transfer.
    // Real aToken's burn_scaled_and_transfer_to (or burn_scaled + transfer_underlying_to)
    // needs the aToken contract to hold enough underlying to cover the seized collateral.
    let collateral_to_seize = match &auth_result {
        Ok(Ok(auth)) => auth.collateral_to_seize,
        _ => 0,
    };
    let usdc_sac = soroban_sdk::token::StellarAssetClient::new(&env, &usdc);
    // Fund the USDC aToken so it can transfer collateral to the pool
    let usdc_reserve = router.get_reserve_data(&usdc);
    usdc_sac.mint(&usdc_reserve.a_token_address, &((collateral_to_seize as i128) * 2));

    // Reset budget to only measure execute_liquidation
    env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);

    // Step 2: execute_liquidation
    let deadline = env.ledger().timestamp() + 300;
    let result = router.try_execute_liquidation(
        &liquidator, &user, &solvbtc, &usdc, &deadline,
    );
    print_budget(&env, "execute_liquidation (4 positions: USDC+XLM coll, wBTC+SolvBTC debt)");

    match &result {
        Ok(Ok(_)) => println!("  execute_liquidation succeeded"),
        Ok(Err(e)) => println!("  execute_liquidation contract error: {:?}", e),
        Err(e) => println!("  execute_liquidation invocation error: {:?}", e),
    }

    let (cpu, mem) = budget_snapshot(&env);
    let cpu_pct = cpu as f64 / CPU_LIMIT as f64 * 100.0;
    let mem_pct = mem as f64 / MEM_LIMIT as f64 * 100.0;
    println!(
        "  VERDICT: CPU {:.1}% | MEM {:.1}%",
        cpu_pct, mem_pct
    );

    if mem <= MEM_LIMIT && cpu <= CPU_LIMIT {
        println!("  PASS: Within budget limits!");
    } else {
        println!("  FAIL: Exceeds budget limits");
    }
    println!();
}

/// Test 10c: Direct liquidation_call with 4 positions (TEST_USER).
/// No DEX swap needed — measures full HF calculation with balance cache.
#[test]
fn test_fork_liquidation_call_budget_4_positions() {
    let env = load_snapshot();
    upgrade_router_in_snapshot(&env);

    let router_addr = addr(&env, KINETIC_ROUTER);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let oracle_addr = addr(&env, PRICE_ORACLE);
    let oracle = price_oracle::Client::new(&env, &oracle_addr);
    let user = addr(&env, TEST_USER);
    let deployer = addr(&env, DEPLOYER);
    let liquidator = addr(&env, DEPLOYER);

    let account_data = router.get_user_account_data(&user);
    println!("  TEST_USER positions (4): USDC+XLM supplied, wBTC+SolvBTC borrowed");
    println!("    HF: {}, coll: {}, debt: {}", account_data.health_factor,
        account_data.total_collateral_base, account_data.total_debt_base);

    // Inflate BTC prices 27x to push HF below 0.5 (100% close factor)
    let solvbtc_asset = price_oracle::Asset::Stellar(addr(&env, SOLVBTC));
    let wbtc_asset = price_oracle::Asset::Stellar(addr(&env, WBTC));
    let expiry = env.ledger().timestamp() + 86400;
    let orig_solvbtc = oracle.get_asset_price(&solvbtc_asset);
    let orig_wbtc = oracle.get_asset_price(&wbtc_asset);

    oracle.reset_circuit_breaker(&deployer, &solvbtc_asset);
    oracle.set_manual_override(&deployer, &solvbtc_asset, &Some(orig_solvbtc * 27), &Some(expiry));
    oracle.reset_circuit_breaker(&deployer, &wbtc_asset);
    oracle.set_manual_override(&deployer, &wbtc_asset, &Some(orig_wbtc * 27), &Some(expiry));

    let account_data = router.get_user_account_data(&user);
    println!("    After 27x BTC inflation: HF={}, coll={}, debt={}",
        account_data.health_factor, account_data.total_collateral_base, account_data.total_debt_base);

    if account_data.health_factor >= 1_000_000_000_000_000_000u128 {
        println!("  SKIP: Not liquidatable");
        return;
    }

    // Give liquidator SolvBTC to repay the debt
    let solvbtc = addr(&env, SOLVBTC);
    let usdc = addr(&env, USDC);
    let solvbtc_token = soroban_sdk::token::Client::new(&env, &solvbtc);

    // Mint SolvBTC and approve router to spend it
    let solvbtc_sac = soroban_sdk::token::StellarAssetClient::new(&env, &solvbtc);
    solvbtc_sac.mint(&liquidator, &1_000_000_000i128);
    solvbtc_token.approve(&liquidator, &addr(&env, KINETIC_ROUTER), &1_000_000_000i128, &(env.ledger().sequence() + 1000));
    // Reset budget
    env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);

    // Direct liquidation: cover full SolvBTC debt, seize USDC collateral
    let result = router.try_liquidation_call(
        &liquidator,
        &usdc,      // collateral to seize
        &solvbtc,   // debt to cover
        &user,
        &50_000u128, // full SolvBTC debt (~0.0005 SolvBTC)
        &false,
    );
    print_budget(&env, "liquidation_call (4 positions, direct, no flash loan)");

    match &result {
        Ok(Ok(_)) => println!("  liquidation_call succeeded"),
        Ok(Err(e)) => println!("  liquidation_call contract error: {:?}", e),
        Err(e) => println!("  liquidation_call invocation error: {:?}", e),
    }

    let (cpu, mem) = budget_snapshot(&env);
    let cpu_pct = cpu as f64 / CPU_LIMIT as f64 * 100.0;
    let mem_pct = mem as f64 / MEM_LIMIT as f64 * 100.0;
    println!("  VERDICT: CPU {:.1}% | MEM {:.1}%", cpu_pct, mem_pct);

    if mem <= MEM_LIMIT && cpu <= CPU_LIMIT {
        println!("  PASS: Within budget limits!");
    } else {
        println!("  FAIL: Exceeds budget limits");
    }
    println!();
}

/// Test 11: Combined prepare + execute budget (total cost of a full 2-step liquidation).
#[test]
fn test_fork_full_liquidation_budget() {
    let env = load_snapshot();
    upgrade_router_in_snapshot(&env);
    make_user_liquidatable(&env);

    let router_addr = addr(&env, KINETIC_ROUTER);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let user = get_liquidatable_user(&env);
    let liquidator = addr(&env, TEST_USER);

    let account_data = router.get_user_account_data(&user);
    if account_data.health_factor >= 1_000_000_000_000_000_000u128 {
        println!("  SKIP: User is not liquidatable");
        return;
    }

    // Reset budget to measure both steps combined
    env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);

    let solvbtc = addr(&env, SOLVBTC);
    let usdc = addr(&env, USDC);
    let debt_to_cover = 10_0000000u128; // 10 USDC (7 decimals) // 50 USDC
    let min_swap_out = 1u128;

    // Measure prepare
    let prepare_result = router.try_prepare_liquidation(
        &liquidator, &user, &usdc, &solvbtc,
        &debt_to_cover, &min_swap_out, &None::<Address>,
    );
    let (prepare_cpu, prepare_mem) = budget_snapshot(&env);
    print_budget(&env, "prepare_liquidation (measured individually)");

    match &prepare_result {
        Ok(Ok(_)) => {}
        Ok(Err(e)) => { println!("  prepare failed: {:?}", e); return; }
        Err(e) => { println!("  prepare invoke error: {:?}", e); return; }
    }

    // Reset and measure execute
    env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);

    let deadline = env.ledger().timestamp() + 300;
    let execute_result = router.try_execute_liquidation(
        &liquidator, &user, &usdc, &solvbtc, &deadline,
    );
    let (execute_cpu, execute_mem) = budget_snapshot(&env);
    print_budget(&env, "execute_liquidation (measured individually)");

    match &execute_result {
        Ok(Ok(_)) => println!("  Full liquidation succeeded"),
        Ok(Err(e)) => println!("  execute failed: {:?}", e),
        Err(e) => println!("  execute invoke error: {:?}", e),
    }

    // Summary
    println!("--- LIQUIDATION BUDGET SUMMARY ---");
    println!(
        "  prepare:  CPU {:>5.1}% | MEM {:>5.1}%",
        prepare_cpu as f64 / CPU_LIMIT as f64 * 100.0,
        prepare_mem as f64 / MEM_LIMIT as f64 * 100.0
    );
    println!(
        "  execute:  CPU {:>5.1}% | MEM {:>5.1}%",
        execute_cpu as f64 / CPU_LIMIT as f64 * 100.0,
        execute_mem as f64 / MEM_LIMIT as f64 * 100.0
    );
    println!(
        "  combined: CPU {:>5.1}% | MEM {:>5.1}% (individual TXs, not summed)",
        (prepare_cpu.max(execute_cpu)) as f64 / CPU_LIMIT as f64 * 100.0,
        (prepare_mem.max(execute_mem)) as f64 / MEM_LIMIT as f64 * 100.0
    );
    println!(
        "  BOTTLENECK: {} (CPU: {} | MEM: {})",
        if execute_mem > prepare_mem { "execute" } else { "prepare" },
        if execute_cpu > prepare_cpu { "execute" } else { "prepare" },
        if execute_mem > prepare_mem { "execute" } else { "prepare" },
    );
    println!();
}

/// Test 12: Direct liquidation_call budget (single-TX liquidation, no flash loan).
///
/// For comparison: this is the legacy one-step liquidation where the liquidator
/// provides the debt asset upfront (no DEX swap needed).
#[test]
fn test_fork_direct_liquidation_call_budget() {
    let env = load_snapshot();
    upgrade_router_in_snapshot(&env);
    make_user_liquidatable(&env);

    let router_addr = addr(&env, KINETIC_ROUTER);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let user = get_liquidatable_user(&env);
    let liquidator = addr(&env, TEST_USER);

    let account_data = router.get_user_account_data(&user);
    if account_data.health_factor >= 1_000_000_000_000_000_000u128 {
        println!("  SKIP: User is not liquidatable");
        return;
    }

    // Reset budget
    env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);

    let solvbtc = addr(&env, SOLVBTC);
    let usdc = addr(&env, USDC);
    let debt_to_cover = 10_0000000u128; // 10 USDC (7 decimals) // 50 USDC

    let result = router.try_liquidation_call(
        &liquidator,
        &solvbtc, // collateral
        &usdc,    // debt
        &user,
        &debt_to_cover,
        &false,   // receive_a_token
    );
    print_budget(&env, "liquidation_call (direct, no flash loan)");

    match &result {
        Ok(Ok(_)) => println!("  liquidation_call succeeded"),
        Ok(Err(e)) => println!("  liquidation_call contract error: {:?}", e),
        Err(e) => println!("  liquidation_call invocation error: {:?}", e),
    }

    let (cpu, mem) = budget_snapshot(&env);
    let cpu_pct = cpu as f64 / CPU_LIMIT as f64 * 100.0;
    let mem_pct = mem as f64 / MEM_LIMIT as f64 * 100.0;
    println!(
        "  VERDICT: CPU {:.1}% | MEM {:.1}%\n",
        cpu_pct, mem_pct
    );
}

// ---------------------------------------------------------------------------
// Cross-Contract Call Cost Measurement
// ---------------------------------------------------------------------------

/// Test 13: Measure exact memory cost of individual balance_of_with_index calls.
///
/// Isolates per-call overhead by calling balance_of_with_index on each
/// token contract individually and measuring the delta between calls.
/// TEST_USER has 4 positions: USDC supplied, XLM supplied, wBTC borrowed, SolvBTC borrowed.
#[test]
fn test_fork_measure_balance_call_costs() {
    let env = load_snapshot();
    upgrade_router_in_snapshot(&env);

    let router_addr = addr(&env, KINETIC_ROUTER);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let user = addr(&env, TEST_USER);

    let assets = [
        ("USDC", USDC),
        ("XLM", XLM),
        ("SolvBTC", SOLVBTC),
        ("wBTC", WBTC),
    ];

    let sym_balance = soroban_sdk::Symbol::new(&env, "balance_of_with_index");

    println!("\n--- ISOLATED balance_of_with_index CALL COSTS ---\n");
    println!("| {:>10} | {:>8} | {:>12} | {:>12} | {:>10} | {:>10} |",
        "Asset", "Token", "CPU delta", "MEM delta", "CPU total", "MEM total");
    println!("|{:-<12}|{:-<10}|{:-<14}|{:-<14}|{:-<12}|{:-<12}|",
        "", "", "", "", "", "");

    // Warm up: first cross-contract call has extra WASM instantiation cost.
    // Do one throwaway call so subsequent measurements reflect steady-state.
    {
        let reserve = router.get_reserve_data(&addr(&env, USDC));
        let args = soroban_sdk::vec![
            &env,
            user.to_val(),
            IntoVal::into_val(&reserve.liquidity_index, &env)
        ];
        let _ = env.try_invoke_contract::<i128, soroban_sdk::Error>(
            &reserve.a_token_address,
            &sym_balance,
            args,
        );
    }

    // Reset after warmup
    env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);

    let mut prev_cpu = 0u64;
    let mut prev_mem = 0u64;

    // Pre-fetch all reserve data BEFORE measurement loop (avoid polluting deltas)
    let mut reserves = std::vec::Vec::new();
    for (_name, asset_str) in &assets {
        reserves.push(router.get_reserve_data(&addr(&env, asset_str)));
    }

    // Reset after reserve data fetches
    env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);

    for (i, (name, _asset_str)) in assets.iter().enumerate() {
        let reserve = &reserves[i];

        // Measure aToken balance_of_with_index
        let (pre_cpu, pre_mem) = budget_snapshot(&env);
        let args = soroban_sdk::vec![
            &env,
            user.to_val(),
            IntoVal::into_val(&reserve.liquidity_index, &env)
        ];
        let _ = env.try_invoke_contract::<i128, soroban_sdk::Error>(
            &reserve.a_token_address,
            &sym_balance,
            args,
        );
        let (cpu, mem) = budget_snapshot(&env);
        let cpu_delta = cpu.saturating_sub(pre_cpu);
        let mem_delta = mem.saturating_sub(pre_mem);
        println!("| {:>10} | {:>8} | {:>12} | {:>12} | {:>10} | {:>10} |",
            name, "aToken", cpu_delta, mem_delta, cpu, mem);

        // Measure debtToken balance_of_with_index
        let (pre_cpu, pre_mem) = budget_snapshot(&env);
        let args = soroban_sdk::vec![
            &env,
            user.to_val(),
            IntoVal::into_val(&reserve.variable_borrow_index, &env)
        ];
        let _ = env.try_invoke_contract::<i128, soroban_sdk::Error>(
            &reserve.debt_token_address,
            &sym_balance,
            args,
        );
        let (cpu, mem) = budget_snapshot(&env);
        let cpu_delta = cpu.saturating_sub(pre_cpu);
        let mem_delta = mem.saturating_sub(pre_mem);
        println!("| {:>10} | {:>8} | {:>12} | {:>12} | {:>10} | {:>10} |",
            name, "debtTkn", cpu_delta, mem_delta, cpu, mem);
    }

    let (total_cpu, total_mem) = budget_snapshot(&env);
    println!("|{:-<12}|{:-<10}|{:-<14}|{:-<14}|{:-<12}|{:-<12}|",
        "", "", "", "", "", "");
    println!("| {:>10} | {:>8} | {:>12} | {:>12} | {:>10} | {:>10} |",
        "TOTAL", "8 calls", "", "", total_cpu, total_mem);
    println!("| {:>10} | {:>8} | {:>12} | {:>12} |",
        "AVERAGE", "per call",
        total_cpu / 8,
        total_mem / 8);
    println!();

    let mem_pct = total_mem as f64 / MEM_LIMIT as f64 * 100.0;
    println!("  8 balance calls = {:.1}% of MEM limit ({} bytes = {:.1} MB)",
        mem_pct, total_mem, total_mem as f64 / 1_048_576.0);
    println!("  Per call average: {} bytes = {:.2} MB\n",
        total_mem / 8, (total_mem / 8) as f64 / 1_048_576.0);
}

/// Test 14: Measure HF computation cost with vs without cached balances.
///
/// Calls get_user_account_data twice — once cold, once warm.
/// Shows whether Soroban reuses WASM instances or allocates fresh frames.
#[test]
fn test_fork_measure_hf_cached_vs_uncached() {
    let env = load_snapshot();
    upgrade_router_in_snapshot(&env);

    let router_addr = addr(&env, KINETIC_ROUTER);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let user = addr(&env, TEST_USER);

    println!("\n--- HF COMPUTATION: COLD vs WARM ---\n");

    // Cold call (first HF computation — all balance queries are fresh)
    env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);
    let _ = router.try_get_user_account_data(&user);
    let (cold_cpu, cold_mem) = budget_snapshot(&env);

    // Warm call (second HF — Soroban may cache WASM instances)
    env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);
    let _ = router.try_get_user_account_data(&user);
    let (warm_cpu, warm_mem) = budget_snapshot(&env);

    println!("| {:>15} | {:>12} | {:>6} | {:>12} | {:>6} |",
        "", "CPU", "CPU %", "Memory", "MEM %");
    println!("|{:-<17}|{:-<14}|{:-<8}|{:-<14}|{:-<8}|",
        "", "", "", "", "");
    println!("| {:>15} | {:>12} | {:>5.1}% | {:>12} | {:>5.1}% |",
        "Cold (1st call)", cold_cpu,
        cold_cpu as f64 / CPU_LIMIT as f64 * 100.0,
        cold_mem,
        cold_mem as f64 / MEM_LIMIT as f64 * 100.0);
    println!("| {:>15} | {:>12} | {:>5.1}% | {:>12} | {:>5.1}% |",
        "Warm (2nd call)", warm_cpu,
        warm_cpu as f64 / CPU_LIMIT as f64 * 100.0,
        warm_mem,
        warm_mem as f64 / MEM_LIMIT as f64 * 100.0);

    let cpu_savings = if cold_cpu > warm_cpu { cold_cpu - warm_cpu } else { 0 };
    let mem_savings = if cold_mem > warm_mem { cold_mem - warm_mem } else { 0 };
    println!("| {:>15} | {:>12} |        | {:>12} |        |",
        "Delta (savings)", cpu_savings, mem_savings);
    println!();

    println!("  Cold = fresh invocation frames for all balance queries");
    println!("  Warm = WASM instance cache may be populated from cold call");
    println!("  If delta is ~0, Soroban allocates fresh frames regardless (bump allocator)\n");
}

/// Test 15: Measure WASM instantiation costs end-to-end.
///
/// Strategy: Make successive router calls that trigger different sets of WASMs.
/// 1. get_reserve_data (router WASM only — no token/oracle calls)
/// 2. get_current_reserve_data (router + debtToken WASM for borrow index)
/// 3. get_user_account_data (router + aToken + debtToken + oracle WASMs)
///
/// By measuring deltas, we isolate what each WASM instantiation adds.
#[test]
fn test_fork_measure_wasm_instantiation_costs() {
    let env = load_snapshot();
    upgrade_router_in_snapshot(&env);

    let router_addr = addr(&env, KINETIC_ROUTER);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let user = addr(&env, TEST_USER);
    let usdc = addr(&env, USDC);

    println!("\n--- WASM INSTANTIATION COST BREAKDOWN ---\n");
    println!("Each call is measured independently (budget reset between calls).\n");

    // 1. get_reserve_data — reads from router storage, no cross-contract calls
    env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);
    let _ = router.try_get_reserve_data(&usdc);
    let (cpu_1, mem_1) = budget_snapshot(&env);

    // 2. get_current_reserve_data — calls update_state which computes current
    //    borrow index (may call debtToken for total_supply, or compute in-memory)
    env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);
    let _ = router.try_get_current_reserve_data(&usdc);
    let (cpu_2, mem_2) = budget_snapshot(&env);

    // 3. get_user_account_data — full HF: router + oracle + N×(aToken + debtToken)
    env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);
    let _ = router.try_get_user_account_data(&user);
    let (cpu_3, mem_3) = budget_snapshot(&env);

    // 4. get_user_account_data AGAIN — all WASMs should be cached from call 3
    env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);
    let _ = router.try_get_user_account_data(&user);
    let (cpu_4, mem_4) = budget_snapshot(&env);

    println!("| {:>35} | {:>12} | {:>6} | {:>12} | {:>6} |",
        "Operation", "CPU", "CPU %", "Memory", "MEM %");
    println!("|{:-<37}|{:-<14}|{:-<8}|{:-<14}|{:-<8}|",
        "", "", "", "", "");

    let rows: &[(&str, u64, u64)] = &[
        ("get_reserve_data (storage only)", cpu_1, mem_1),
        ("get_current_reserve_data", cpu_2, mem_2),
        ("get_user_account_data (1st, cold)", cpu_3, mem_3),
        ("get_user_account_data (2nd, warm)", cpu_4, mem_4),
    ];

    for (name, cpu, mem) in rows {
        println!("| {:>35} | {:>12} | {:>5.1}% | {:>12} | {:>5.1}% |",
            name, cpu,
            *cpu as f64 / CPU_LIMIT as f64 * 100.0,
            mem,
            *mem as f64 / MEM_LIMIT as f64 * 100.0);
    }

    println!();
    println!("  Interpretation:");
    println!("  - Row 1: Router WASM instantiation + storage read");
    println!("  - Row 2 - Row 1: debtToken/interest calculation overhead");
    println!("  - Row 3 - Row 2: oracle + aToken + debtToken balance queries");
    println!("  - Row 4 vs Row 3: WASM cache effect (should be ~same if independent txs)");
    println!("  - Row 3 = total cost of HF computation for 4 positions");

    // Deltas
    println!();
    println!("  Deltas:");
    println!("    Router WASM + storage:     {:>8} CPU | {:>8} MEM ({:.1} MB)",
        cpu_1, mem_1, mem_1 as f64 / 1_048_576.0);
    println!("    + interest calc:           {:>8} CPU | {:>8} MEM ({:.1} MB)",
        cpu_2.saturating_sub(cpu_1), mem_2.saturating_sub(mem_1),
        mem_2.saturating_sub(mem_1) as f64 / 1_048_576.0);
    println!("    + oracle + balance queries:{:>8} CPU | {:>8} MEM ({:.1} MB)",
        cpu_3.saturating_sub(cpu_2), mem_3.saturating_sub(mem_2),
        mem_3.saturating_sub(mem_2) as f64 / 1_048_576.0);
    println!("    WASM cache savings (4-3):  {:>8} CPU | {:>8} MEM ({:.1} MB)",
        cpu_3.saturating_sub(cpu_4), mem_3.saturating_sub(mem_4),
        mem_3.saturating_sub(mem_4) as f64 / 1_048_576.0);
    println!();
}

// ---------------------------------------------------------------------------
// Test 13: Current testnet scenario — GA72QJ... user liquidation
//
// User: GA72QJA6RP7KW3KC57XG7RIU5RDPIJJRJP6TLDVNFCBR3FOWCLYWUE5U
// Positions: USDC + wBTC + wETH collateral, SolvBTC debt (~0.0146 SolvBTC)
// HF ~0.943 after SolvBTC price bump to $72,000
// This tests the exact liquidation that's failing on testnet with Budget Exceeded.
// ---------------------------------------------------------------------------

/// Test 13a: Direct liquidation_call for current testnet user (3 collateral + 1 debt).
/// Covers the full SolvBTC debt using USDC as collateral.
#[test]
fn test_fork_liquidation_current_user() {
    let env = load_snapshot();
    upgrade_router_in_snapshot(&env);

    let router_addr = addr(&env, KINETIC_ROUTER);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let oracle_addr = addr(&env, PRICE_ORACLE);
    let oracle = price_oracle::Client::new(&env, &oracle_addr);
    let user = addr(&env, TEST_USER);
    let liquidator = addr(&env, DEPLOYER);

    // Read current account state
    let account_data = router.get_user_account_data(&user);
    println!("  TEST_USER current state:");
    println!("    HF: {}", account_data.health_factor);
    println!("    collateral_base: {}", account_data.total_collateral_base);
    println!("    debt_base: {}", account_data.total_debt_base);

    // If user is not already liquidatable, bump SolvBTC price
    if account_data.health_factor >= 1_000_000_000_000_000_000u128 {
        println!("  User not liquidatable, bumping SolvBTC price...");
        let solvbtc_asset = price_oracle::Asset::Stellar(addr(&env, SOLVBTC));
        let original_price = oracle.get_asset_price(&solvbtc_asset);
        let target_price = original_price
            .checked_mul(account_data.health_factor).expect("mul overflow")
            .checked_div(940_000_000_000_000_000u128).expect("div overflow");
        oracle.reset_circuit_breaker(&liquidator, &solvbtc_asset);
        let expiry = env.ledger().timestamp() + 86400;
        oracle.set_manual_override(&liquidator, &solvbtc_asset, &Some(target_price), &Some(expiry));
        let updated = router.get_user_account_data(&user);
        println!("    After price bump: HF={}", updated.health_factor);
    }

    // Ensure partial_liq_hf_threshold is 0.95 so HF=0.943 gives 100% close factor
    router.set_partial_liq_hf_threshold(&950_000_000_000_000_000u128);
    println!("  partial_liq_hf_threshold set to 0.95");

    // Give liquidator SolvBTC to repay the debt
    let solvbtc = addr(&env, SOLVBTC);
    let usdc = addr(&env, USDC);
    let solvbtc_sac = soroban_sdk::token::StellarAssetClient::new(&env, &solvbtc);
    let solvbtc_token = soroban_sdk::token::Client::new(&env, &solvbtc);
    solvbtc_sac.mint(&liquidator, &100_000_000i128); // 1 SolvBTC
    solvbtc_token.approve(&liquidator, &router_addr, &100_000_000i128, &(env.ledger().sequence() + 1000));

    // Get actual debt
    let solvbtc_reserve = router.get_reserve_data(&solvbtc);
    let debt_token = soroban_sdk::token::Client::new(&env, &solvbtc_reserve.debt_token_address);
    let user_debt = debt_token.balance(&user);
    println!("  User SolvBTC debt balance: {} (raw units)", user_debt);

    // Reset budget before liquidation
    env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);

    // Full liquidation — use exact debt balance (100% close factor since HF < 0.95)
    let debt_to_cover = user_debt as u128;
    let result = router.try_liquidation_call(
        &liquidator,
        &usdc,      // collateral to seize
        &solvbtc,   // debt to cover
        &user,
        &debt_to_cover,
        &false,
    );
    print_budget(&env, "liquidation_call (3 coll + 1 debt, full cover, USDC collateral)");

    match &result {
        Ok(Ok(_)) => println!("  liquidation_call SUCCEEDED"),
        Ok(Err(e)) => println!("  liquidation_call contract error: {:?}", e),
        Err(e) => println!("  liquidation_call invocation error: {:?}", e),
    }

    let (cpu, mem) = budget_snapshot(&env);
    let cpu_pct = cpu as f64 / CPU_LIMIT as f64 * 100.0;
    let mem_pct = mem as f64 / MEM_LIMIT as f64 * 100.0;
    println!("  VERDICT: CPU {:.1}% | MEM {:.1}%", cpu_pct, mem_pct);
    if mem <= MEM_LIMIT && cpu <= CPU_LIMIT {
        println!("  PASS: Within budget limits!");
    } else {
        println!("  FAIL: Exceeds budget (CPU limit: {}, MEM limit: {})", CPU_LIMIT, MEM_LIMIT);
    }
    println!();
}

/// Test 13b: Same as 13a but using wBTC as collateral (higher value, avoids collateral cap).
#[test]
fn test_fork_liquidation_current_user_wbtc_collateral() {
    let env = load_snapshot();
    upgrade_router_in_snapshot(&env);

    let router_addr = addr(&env, KINETIC_ROUTER);
    let router = kinetic_router::Client::new(&env, &router_addr);
    let oracle_addr = addr(&env, PRICE_ORACLE);
    let oracle = price_oracle::Client::new(&env, &oracle_addr);
    let user = addr(&env, TEST_USER);
    let liquidator = addr(&env, DEPLOYER);

    let account_data = router.get_user_account_data(&user);
    if account_data.health_factor >= 1_000_000_000_000_000_000u128 {
        let solvbtc_asset = price_oracle::Asset::Stellar(addr(&env, SOLVBTC));
        let original_price = oracle.get_asset_price(&solvbtc_asset);
        let target_price = original_price
            .checked_mul(account_data.health_factor).expect("mul overflow")
            .checked_div(940_000_000_000_000_000u128).expect("div overflow");
        oracle.reset_circuit_breaker(&liquidator, &solvbtc_asset);
        let expiry = env.ledger().timestamp() + 86400;
        oracle.set_manual_override(&liquidator, &solvbtc_asset, &Some(target_price), &Some(expiry));
    }

    // Ensure 100% close factor
    router.set_partial_liq_hf_threshold(&950_000_000_000_000_000u128);

    let solvbtc = addr(&env, SOLVBTC);
    let wbtc = addr(&env, WBTC);
    let solvbtc_sac = soroban_sdk::token::StellarAssetClient::new(&env, &solvbtc);
    let solvbtc_token = soroban_sdk::token::Client::new(&env, &solvbtc);
    solvbtc_sac.mint(&liquidator, &100_000_000i128);
    solvbtc_token.approve(&liquidator, &router_addr, &100_000_000i128, &(env.ledger().sequence() + 1000));

    let solvbtc_reserve = router.get_reserve_data(&solvbtc);
    let debt_token = soroban_sdk::token::Client::new(&env, &solvbtc_reserve.debt_token_address);
    let user_debt = debt_token.balance(&user);
    println!("  User SolvBTC debt: {} units", user_debt);

    env.cost_estimate().budget().reset_limits(500_000_000, 200_000_000);

    let debt_to_cover = user_debt as u128;
    let result = router.try_liquidation_call(
        &liquidator,
        &wbtc,      // collateral to seize (wBTC)
        &solvbtc,   // debt to cover
        &user,
        &debt_to_cover,
        &false,
    );
    print_budget(&env, "liquidation_call (3 coll + 1 debt, full cover, wBTC collateral)");

    match &result {
        Ok(Ok(_)) => println!("  liquidation_call SUCCEEDED"),
        Ok(Err(e)) => println!("  liquidation_call contract error: {:?}", e),
        Err(e) => println!("  liquidation_call invocation error: {:?}", e),
    }

    let (cpu, mem) = budget_snapshot(&env);
    let cpu_pct = cpu as f64 / CPU_LIMIT as f64 * 100.0;
    let mem_pct = mem as f64 / MEM_LIMIT as f64 * 100.0;
    println!("  VERDICT: CPU {:.1}% | MEM {:.1}%", cpu_pct, mem_pct);
    if mem <= MEM_LIMIT && cpu <= CPU_LIMIT {
        println!("  PASS: Within budget limits!");
    } else {
        println!("  FAIL: Exceeds budget");
    }
    println!();
}
