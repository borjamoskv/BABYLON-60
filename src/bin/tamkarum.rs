//! TAMKARUM-60 · Sovereign Arbitrage & KudurruBudgetGate CLI (Ring-1)
//! Author: Borja Fernández Angulo (borjamoskv)

use babylon60::tamkarum::{BudgetVerdict, KudurruBudgetGate};
use std::env;

fn main() {
    let args: Vec<String> = env::args().collect();
    let cmd = args.get(1).map(|s| s.as_str()).unwrap_or("status");

    println!("====================================================================");
    println!("  TAMKARUM-60 · SOVEREIGN TRANSDUCER & KUDURRU BUDGET GATE (64B)   ");
    println!("====================================================================");

    let mut gate = KudurruBudgetGate::new(
        100_000, // 1,000.00 EUR max daily
        2_500,   // 25.00 EUR max bid
        250,     // 2.50x min ROAS
        [0x42; 32],
    );

    match cmd {
        "status" => {
            println!("Memory Layout:      64 Bytes (align 64) — L1 Cache-Line Resident");
            println!("Max Daily Budget:   {:>10.2} EUR", gate.max_daily_budget_cents as f64 / 100.0);
            println!("Spent Today:        {:>10.2} EUR", gate.spent_today_cents as f64 / 100.0);
            println!("Max Bid Cap:        {:>10.2} EUR", gate.max_bid_cents as f64 / 100.0);
            println!("Min Target ROAS:    {:>10.2}x", gate.min_roas_basis_points as f64 / 100.0);
            println!("Current ROAS:       {:>10.2}x", gate.current_roas_basis_points as f64 / 100.0);
            println!("Apoptosis Trigger:  MUSHUSHU-0 (0xDEAD_6060 on breach or 60 epochs bad ROAS)");
            println!("Biometric Lock:     Active (Touch ID P-256 bound)");
        }
        "evaluate" => {
            let bid = args.get(2).and_then(|s| s.parse::<u32>().ok()).unwrap_or(500);
            println!("Evaluating bid of {:.2} EUR under Kelly Criterion...", bid as f64 / 100.0);
            let verdict = gate.evaluate_bid(bid, 6000, 250);
            match verdict {
                BudgetVerdict::Allowed { approved_bid_cents } => {
                    println!("VERDICT: [ALLOWED] Approved Bid: {:.2} EUR", approved_bid_cents as f64 / 100.0);
                    println!("Cumulative Daily Spend: {:.2} EUR", gate.spent_today_cents as f64 / 100.0);
                }
                BudgetVerdict::ExceedsBidCap { attempted_bid_cents, bid_cap_cents } => {
                    println!("VERDICT: [DENIED] Attempted {:.2} EUR exceeds cap of {:.2} EUR", attempted_bid_cents as f64 / 100.0, bid_cap_cents as f64 / 100.0);
                }
                BudgetVerdict::ExceedsDailyBudget { attempted_total_cents, limit_cents } => {
                    println!("VERDICT: [DENIED] Total {:.2} EUR exceeds daily budget of {:.2} EUR", attempted_total_cents as f64 / 100.0, limit_cents as f64 / 100.0);
                }
                BudgetVerdict::ApoptosisHalt { signal } => {
                    println!("VERDICT: [APOPTOSIS HALT] 0x{:08X}", signal);
                }
            }
        }
        _ => {
            println!("Usage: cargo run --bin tamkarum -- [status | evaluate <bid_cents>]");
        }
    }
    println!("====================================================================");
}
