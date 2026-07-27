//! Seed generator for K2 lending operations fuzzer
//!
//! This tool generates hand-crafted seed corpus files that help the fuzzer
//! achieve better initial coverage by providing targeted starting points.
//!
//! Run: cargo run --bin generate_seeds
//!
//! The seeds are written to: corpus/fuzz_lending_operations/

use std::fs;
use std::io::Write;
use std::path::Path;

/// User discriminants
const USER1: u8 = 0;
const USER2: u8 = 1;

/// Operation discriminants
const OP_SUPPLY: u8 = 0;
const OP_BORROW: u8 = 1;
const OP_REPAY: u8 = 2;
const OP_WITHDRAW: u8 = 3;
const OP_ADVANCE_TIME: u8 = 4;
const OP_SUPPLY_MORE: u8 = 5;
const OP_PARTIAL_WITHDRAW: u8 = 6;
const OP_REPAY_ALL: u8 = 7;
const OP_WITHDRAW_ALL: u8 = 8;
const OP_SET_PRICE: u8 = 9;
const OP_LIQUIDATE: u8 = 10;
const OP_SET_COLLATERAL: u8 = 11;

/// Amount hint discriminants
const HINT_RAW: u8 = 0;
const HINT_MAX: u8 = 1;
const HINT_MIN: u8 = 2;
const HINT_POWER_OF_TWO: u8 = 3;
const HINT_LTV_BOUNDARY: u8 = 4;

/// Writes bytes representing a LendingInput to corpus
///
/// The byte format approximates what libfuzzer/Arbitrary will consume:
/// - initial_supply_user1: 8 bytes (u64 little-endian)
/// - initial_supply_user2: 8 bytes (u64 little-endian)
/// - initial_supply_hint: 1 byte (enum discriminant 0-4)
/// - operations[16]: for each:
///   - 1 byte for Option discriminant (0=None, 1=Some)
///   - if Some: 1 byte for Operation discriminant + payload bytes
struct SeedBuilder {
    bytes: Vec<u8>,
    op_count: usize,
}

impl SeedBuilder {
    fn new() -> Self {
        Self {
            bytes: Vec::new(),
            op_count: 0,
        }
    }

    fn initial_supplies(mut self, user1_amount: u64, user2_amount: u64, hint: u8) -> Self {
        // u64 little-endian for user1
        self.bytes.extend_from_slice(&user1_amount.to_le_bytes());
        // u64 little-endian for user2
        self.bytes.extend_from_slice(&user2_amount.to_le_bytes());
        // AmountHint discriminant
        self.bytes.push(hint % 5);
        self
    }

    fn none_op(mut self) -> Self {
        // Option::None discriminant
        self.bytes.push(0);
        self.op_count += 1;
        self
    }

    fn supply(mut self, user: u8, amount: u64) -> Self {
        self.bytes.push(1); // Some
        self.bytes.push(OP_SUPPLY);
        self.bytes.push(user);
        self.bytes.extend_from_slice(&amount.to_le_bytes());
        self.op_count += 1;
        self
    }

    fn borrow(mut self, user: u8, amount: u64) -> Self {
        self.bytes.push(1); // Some
        self.bytes.push(OP_BORROW);
        self.bytes.push(user);
        self.bytes.extend_from_slice(&amount.to_le_bytes());
        self.op_count += 1;
        self
    }

    fn repay(mut self, user: u8, amount: u64) -> Self {
        self.bytes.push(1); // Some
        self.bytes.push(OP_REPAY);
        self.bytes.push(user);
        self.bytes.extend_from_slice(&amount.to_le_bytes());
        self.op_count += 1;
        self
    }

    fn withdraw(mut self, user: u8, amount: u64) -> Self {
        self.bytes.push(1); // Some
        self.bytes.push(OP_WITHDRAW);
        self.bytes.push(user);
        self.bytes.extend_from_slice(&amount.to_le_bytes());
        self.op_count += 1;
        self
    }

    fn advance_time(mut self, seconds: u32) -> Self {
        self.bytes.push(1); // Some
        self.bytes.push(OP_ADVANCE_TIME);
        self.bytes.extend_from_slice(&seconds.to_le_bytes());
        self.op_count += 1;
        self
    }

    fn supply_more(mut self, user: u8, amount: u64) -> Self {
        self.bytes.push(1); // Some
        self.bytes.push(OP_SUPPLY_MORE);
        self.bytes.push(user);
        self.bytes.extend_from_slice(&amount.to_le_bytes());
        self.op_count += 1;
        self
    }

    fn partial_withdraw(mut self, user: u8, percent: u8) -> Self {
        self.bytes.push(1); // Some
        self.bytes.push(OP_PARTIAL_WITHDRAW);
        self.bytes.push(user);
        self.bytes.push(percent);
        self.op_count += 1;
        self
    }

    fn repay_all(mut self, user: u8) -> Self {
        self.bytes.push(1); // Some
        self.bytes.push(OP_REPAY_ALL);
        self.bytes.push(user);
        self.op_count += 1;
        self
    }

    fn withdraw_all(mut self, user: u8) -> Self {
        self.bytes.push(1); // Some
        self.bytes.push(OP_WITHDRAW_ALL);
        self.bytes.push(user);
        self.op_count += 1;
        self
    }

    fn set_price(mut self, price_bps: u16) -> Self {
        self.bytes.push(1); // Some
        self.bytes.push(OP_SET_PRICE);
        self.bytes.extend_from_slice(&price_bps.to_le_bytes());
        self.op_count += 1;
        self
    }

    fn liquidate(mut self, liquidator: u8, borrower: u8, amount: u64) -> Self {
        self.bytes.push(1); // Some
        self.bytes.push(OP_LIQUIDATE);
        self.bytes.push(liquidator);
        self.bytes.push(borrower);
        self.bytes.extend_from_slice(&amount.to_le_bytes());
        self.op_count += 1;
        self
    }

    fn set_collateral_enabled(mut self, user: u8, enabled: bool) -> Self {
        self.bytes.push(1); // Some
        self.bytes.push(OP_SET_COLLATERAL);
        self.bytes.push(user);
        self.bytes.push(if enabled { 1 } else { 0 });
        self.op_count += 1;
        self
    }

    /// Pad remaining operation slots with None (up to 16)
    fn fill_nones(mut self) -> Self {
        while self.op_count < 16 {
            self = self.none_op();
        }
        self
    }

    fn build(self) -> Vec<u8> {
        self.bytes
    }
}

fn main() -> std::io::Result<()> {
    let corpus_dir = Path::new("corpus/fuzz_lending_operations");

    // Create corpus directory if it doesn't exist
    fs::create_dir_all(corpus_dir)?;

    // Collection of seeds with descriptions
    let seeds: Vec<(&str, Vec<u8>)> = vec![
        // === Basic Edge Cases ===
        (
            "max_supply_u1",
            SeedBuilder::new()
                .initial_supplies(u64::MAX, 0, HINT_MAX)
                .fill_nones()
                .build(),
        ),
        (
            "min_supply_both",
            SeedBuilder::new()
                .initial_supplies(1, 1, HINT_MIN)
                .fill_nones()
                .build(),
        ),
        (
            "zero_supply",
            SeedBuilder::new()
                .initial_supplies(0, 0, HINT_RAW)
                .fill_nones()
                .build(),
        ),
        // === LTV Boundary Testing ===
        (
            "borrow_at_ltv_boundary_u1",
            SeedBuilder::new()
                .initial_supplies(1_000_000_000, 0, HINT_LTV_BOUNDARY)
                .borrow(USER1, 800_000_000) // Exactly 80% LTV
                .fill_nones()
                .build(),
        ),
        (
            "borrow_max_ltv_u2",
            SeedBuilder::new()
                .initial_supplies(0, 10_000_000_000, HINT_RAW)
                .borrow(USER2, 8_000_000_000) // 80% = max LTV
                .fill_nones()
                .build(),
        ),
        // === Interest Accrual Testing ===
        (
            "borrow_with_time_advance",
            SeedBuilder::new()
                .initial_supplies(1_000_000_000, 0, HINT_RAW)
                .borrow(USER1, 500_000_000)
                .advance_time(86400) // 1 day
                .fill_nones()
                .build(),
        ),
        (
            "max_time_advance",
            SeedBuilder::new()
                .initial_supplies(1_000_000_000, 0, HINT_RAW)
                .borrow(USER1, 500_000_000)
                .advance_time(31_536_000) // 1 year
                .repay(USER1, u64::MAX) // Repay all with interest
                .fill_nones()
                .build(),
        ),
        // === Full Cycles ===
        (
            "full_borrow_repay_cycle",
            SeedBuilder::new()
                .initial_supplies(1_000_000_000, 0, HINT_RAW)
                .borrow(USER1, 500_000_000)
                .advance_time(3600) // 1 hour
                .repay_all(USER1)
                .fill_nones()
                .build(),
        ),
        (
            "full_supply_withdraw_cycle",
            SeedBuilder::new()
                .initial_supplies(1_000_000_000, 0, HINT_RAW)
                .withdraw_all(USER1)
                .fill_nones()
                .build(),
        ),
        // === Multi-User Scenarios ===
        (
            "two_users_supply",
            SeedBuilder::new()
                .initial_supplies(1_000_000_000, 500_000_000, HINT_RAW)
                .supply(USER1, 200_000_000)
                .supply(USER2, 300_000_000)
                .fill_nones()
                .build(),
        ),
        (
            "two_users_borrow",
            SeedBuilder::new()
                .initial_supplies(2_000_000_000, 1_000_000_000, HINT_RAW)
                .borrow(USER1, 800_000_000)
                .borrow(USER2, 400_000_000)
                .advance_time(86400)
                .fill_nones()
                .build(),
        ),
        (
            "user2_liquidates_user1",
            SeedBuilder::new()
                .initial_supplies(1_000_000_000, 500_000_000, HINT_RAW)
                .borrow(USER1, 750_000_000) // Near max LTV
                .set_price(5000) // Drop price to 50%
                .liquidate(USER2, USER1, 100_000_000)
                .fill_nones()
                .build(),
        ),
        (
            "user1_liquidates_user2",
            SeedBuilder::new()
                .initial_supplies(500_000_000, 1_000_000_000, HINT_RAW)
                .borrow(USER2, 750_000_000) // Near max LTV
                .set_price(5000) // Drop price to 50%
                .liquidate(USER1, USER2, 100_000_000)
                .fill_nones()
                .build(),
        ),
        // === Price Manipulation Scenarios ===
        (
            "price_crash_scenario",
            SeedBuilder::new()
                .initial_supplies(1_000_000_000, 0, HINT_RAW)
                .borrow(USER1, 700_000_000)
                .set_price(5000) // 50% price drop
                .set_price(2500) // Further drop to 25%
                .fill_nones()
                .build(),
        ),
        (
            "price_pump_scenario",
            SeedBuilder::new()
                .initial_supplies(1_000_000_000, 0, HINT_RAW)
                .borrow(USER1, 700_000_000)
                .set_price(20000) // 200% price
                .borrow(USER1, 500_000_000) // Can borrow more now
                .fill_nones()
                .build(),
        ),
        (
            "volatile_price",
            SeedBuilder::new()
                .initial_supplies(1_000_000_000, 1_000_000_000, HINT_RAW)
                .borrow(USER1, 500_000_000)
                .set_price(15000) // +50%
                .set_price(7000) // -30% from base
                .set_price(12000) // +20%
                .advance_time(3600)
                .set_price(5000) // -50%
                .fill_nones()
                .build(),
        ),
        // === Complex Sequences ===
        (
            "multiple_supplies_u1",
            SeedBuilder::new()
                .initial_supplies(100_000_000, 0, HINT_RAW)
                .supply(USER1, 200_000_000)
                .supply_more(USER1, 300_000_000)
                .supply(USER1, 400_000_000)
                .fill_nones()
                .build(),
        ),
        (
            "supply_borrow_supply_borrow",
            SeedBuilder::new()
                .initial_supplies(500_000_000, 0, HINT_RAW)
                .borrow(USER1, 200_000_000)
                .supply_more(USER1, 500_000_000)
                .borrow(USER1, 200_000_000)
                .fill_nones()
                .build(),
        ),
        (
            "partial_withdrawals",
            SeedBuilder::new()
                .initial_supplies(1_000_000_000, 0, HINT_RAW)
                .partial_withdraw(USER1, 10) // 10%
                .partial_withdraw(USER1, 25) // 25%
                .partial_withdraw(USER1, 50) // 50%
                .fill_nones()
                .build(),
        ),
        // === Rapid Operations ===
        (
            "rapid_small_operations",
            SeedBuilder::new()
                .initial_supplies(1_000_000_000, 0, HINT_RAW)
                .borrow(USER1, 1000)
                .repay(USER1, 500)
                .borrow(USER1, 1000)
                .repay(USER1, 500)
                .withdraw(USER1, 1000)
                .supply(USER1, 1000)
                .withdraw(USER1, 1000)
                .fill_nones()
                .build(),
        ),
        // === Power of 2 Testing ===
        (
            "power_of_two_supply",
            SeedBuilder::new()
                .initial_supplies(1 << 30, 0, HINT_POWER_OF_TWO) // 2^30
                .fill_nones()
                .build(),
        ),
        (
            "power_of_two_borrow",
            SeedBuilder::new()
                .initial_supplies(1 << 32, 0, HINT_RAW)
                .borrow(USER1, 1 << 31) // 2^31 borrow
                .fill_nones()
                .build(),
        ),
        // === Edge Case Amounts ===
        (
            "one_wei_amounts",
            SeedBuilder::new()
                .initial_supplies(1, 1, HINT_RAW)
                .supply(USER1, 1)
                .borrow(USER1, 1)
                .repay(USER1, 1)
                .withdraw(USER1, 1)
                .fill_nones()
                .build(),
        ),
        (
            "near_max_borrow",
            SeedBuilder::new()
                .initial_supplies(u64::MAX / 2, 0, HINT_RAW)
                .borrow(USER1, (u64::MAX / 2) / 10 * 8) // ~80% of supply
                .fill_nones()
                .build(),
        ),
        // === Time-Heavy Sequences ===
        (
            "multi_time_advance",
            SeedBuilder::new()
                .initial_supplies(1_000_000_000, 0, HINT_RAW)
                .borrow(USER1, 500_000_000)
                .advance_time(3600)    // 1 hour
                .advance_time(86400)   // 1 day
                .advance_time(604800)  // 1 week
                .advance_time(2592000) // 30 days
                .fill_nones()
                .build(),
        ),
        // === Stress Test Sequences ===
        (
            "all_operations_sequence",
            SeedBuilder::new()
                .initial_supplies(10_000_000_000, 5_000_000_000, HINT_RAW)
                .borrow(USER1, 4_000_000_000)
                .advance_time(86400)
                .supply_more(USER1, 5_000_000_000)
                .partial_withdraw(USER1, 10)
                .repay(USER1, 1_000_000_000)
                .withdraw(USER1, 500_000_000)
                .repay_all(USER1)
                .borrow(USER2, 2_000_000_000)
                .set_price(8000)
                .liquidate(USER1, USER2, 500_000_000)
                .fill_nones()
                .build(),
        ),
        // === Collateral Toggle Scenarios ===
        (
            "toggle_collateral",
            SeedBuilder::new()
                .initial_supplies(1_000_000_000, 0, HINT_RAW)
                .set_collateral_enabled(USER1, false)
                .set_collateral_enabled(USER1, true)
                .borrow(USER1, 500_000_000)
                .fill_nones()
                .build(),
        ),
        (
            "disable_collateral_with_debt",
            SeedBuilder::new()
                .initial_supplies(1_000_000_000, 0, HINT_RAW)
                .borrow(USER1, 500_000_000)
                .set_collateral_enabled(USER1, false) // Should fail
                .fill_nones()
                .build(),
        ),
        // === Long Operation Sequences ===
        (
            "max_length_sequence",
            SeedBuilder::new()
                .initial_supplies(10_000_000_000, 10_000_000_000, HINT_RAW)
                .supply(USER1, 100_000_000)
                .supply(USER2, 100_000_000)
                .borrow(USER1, 50_000_000)
                .borrow(USER2, 50_000_000)
                .advance_time(3600)
                .set_price(9000)
                .repay(USER1, 10_000_000)
                .repay(USER2, 10_000_000)
                .partial_withdraw(USER1, 5)
                .partial_withdraw(USER2, 5)
                .set_price(10000)
                .advance_time(86400)
                .supply_more(USER1, 50_000_000)
                .supply_more(USER2, 50_000_000)
                .repay_all(USER1)
                .repay_all(USER2)
                .build(), // Uses all 16 slots
        ),
    ];

    // Write all seeds
    let mut count = 0;
    for (name, bytes) in &seeds {
        let path = corpus_dir.join(name);
        let mut file = fs::File::create(&path)?;
        file.write_all(bytes)?;
        println!("Created: {} ({} bytes)", name, bytes.len());
        count += 1;
    }

    println!("\nGenerated {} seed files in {:?}", count, corpus_dir);
    println!("\nRun the fuzzer with:");
    println!("  cargo +nightly fuzz run fuzz_lending_operations --sanitizer=none");
    println!("\nWith dictionary:");
    println!("  cargo +nightly fuzz run fuzz_lending_operations --sanitizer=none -- -dict=dict.txt");
    println!("\nFor parallel execution:");
    println!("  cargo +nightly fuzz run fuzz_lending_operations --sanitizer=none -- -jobs=4 -workers=4 -dict=dict.txt");

    Ok(())
}
