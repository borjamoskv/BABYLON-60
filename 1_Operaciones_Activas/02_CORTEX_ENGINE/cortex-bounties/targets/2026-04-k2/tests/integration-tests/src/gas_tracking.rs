//! # Gas and Resource Tracking Utilities
//!
//! Utilities for tracking CPU, memory, and storage resource usage in integration tests.
//! Helps measure gas costs and identify optimization opportunities.
//!
//! ## Usage
//!
//! ```rust
//! use crate::gas_tracking::*;
//!
//! let env = Env::default();
//!
//! // Track resources at checkpoints
//! let checkpoint1 = capture_resources(&env, "After initialization");
//! // ... perform operations ...
//! let checkpoint2 = capture_resources(&env, "After supply");
//!
//! // Analyze the delta
//! let delta = calculate_delta(&checkpoint1, &checkpoint2);
//! print_resource_delta(&delta);
//!
//! // Attribute costs
//! let attribution = attribute_costs(&delta);
//! print_attribution(&attribution);
//! ```

use soroban_sdk::Env;

// Resource limits from https://developers.stellar.org/docs/networks/resource-limits-fees
pub const CPU_LIMIT: u64 = 100_000_000;
pub const MEM_LIMIT: u64 = 41_943_040;
pub const READ_ENTRIES_LIMIT: u32 = 40;
pub const WRITE_ENTRIES_LIMIT: u32 = 25;
pub const READ_BYTES_LIMIT: u32 = 204_800;
pub const WRITE_BYTES_LIMIT: u32 = 132_096;

/// Check resource limits and print usage information
pub fn check_limits(e: &Env, message: &str) {
    let cost_estimate = e.cost_estimate();
    let cpu_used = cost_estimate.budget().cpu_instruction_cost();
    let mem_used = cost_estimate.budget().memory_bytes_cost();

    println!("{} CPU Instructions: {:?}", message, cpu_used);
    println!("{} MEMORY: {:?}", message, mem_used);
    println!("===========================================");

    assert!(cpu_used <= CPU_LIMIT, "CPU instructions exceeded limit");
    assert!(mem_used <= MEM_LIMIT, "Memory usage exceeded limit");
}

/// Check resource limits and return detailed information
/// Returns: (message, cpu_used, mem_used, read_entries, write_entries, read_bytes, write_bytes)
pub fn check_limits_return_info(e: &Env, message: &str) -> (String, u64, u64, u32, u32, u32, u32) {
    let cost_estimate = e.cost_estimate();
    let cpu_used = cost_estimate.budget().cpu_instruction_cost();
    let mem_used = cost_estimate.budget().memory_bytes_cost();
    let resources = cost_estimate.resources();

    println!("{} CPU Instructions: {:?}", message, cpu_used);
    println!("{} MEMORY: {:?}", message, mem_used);
    // Note: read_entries and read_bytes fields removed in soroban-sdk 23.x
    println!("write_entries: {}", resources.write_entries);
    println!("mem_bytes: {}", resources.mem_bytes);
    println!("write_bytes: {}", resources.write_bytes);
    println!("===========================================");

    (
        message.to_string(),
        cpu_used,
        mem_used,
        0, // read_entries (removed in SDK 23.x)
        resources.write_entries,
        0, // read_bytes (removed in SDK 23.x)
        resources.write_bytes,
    )
}

/// Print resource usage information
pub fn print_resources(e: &Env, message: &str) {
    let resources = e.cost_estimate().resources();
    println!("{}", message);
    println!("{:?}", resources);
    println!("===========================================");
}

/// Create a formatted results table comparing resource usage across multiple checkpoints
pub fn create_results_table(e: &Env, data: Vec<(String, u64, u64, u32, u32, u32, u32)>) {
    let header = vec![
        "Message".to_string(),
        "CPU Instructions".to_string(),
        "Memory".to_string(),
        "Read Entries".to_string(),
        "Write Entries".to_string(),
        "Read Bytes".to_string(),
        "Write Bytes".to_string(),
    ];

    println!(
        "|{:-<27}+{:-<21}+{:-<13}+{:-<15}+{:-<16}+{:-<14}+{:-<15}|",
        "", "", "", "", "", "", ""
    );
    println!(
        "| {:<26}| {:<20}| {:<12}| {:<14}| {:<15}| {:<13}| {:<14}|",
        header[0], header[1], header[2], header[3], header[4], header[5], header[6]
    );
    println!(
        "|{:-<27}+{:-<21}+{:-<13}+{:-<15}+{:-<16}+{:-<14}+{:-<15}|",
        "", "", "", "", "", "", ""
    );

    // Print the limits header
    println!(
        "| {:<26}| {:<20}| {:<12}| {:<14}| {:<15}| {:<13}| {:<14}|",
        "Limits",
        CPU_LIMIT,
        MEM_LIMIT,
        READ_ENTRIES_LIMIT,
        WRITE_ENTRIES_LIMIT,
        READ_BYTES_LIMIT,
        WRITE_BYTES_LIMIT
    );
    println!(
        "|{:-<27}+{:-<21}+{:-<13}+{:-<15}+{:-<16}+{:-<14}+{:-<15}|",
        "", "", "", "", "", "", ""
    );

    for row in &data {
        let (message, cpu_used, mem_used, _, _, _, _) =
            (&row.0, &row.1, &row.2, &row.3, &row.4, &row.5, &row.6);
        if (cpu_used >= &CPU_LIMIT) || (mem_used >= &MEM_LIMIT) {
            println!(
                "|🟥{:<25}| {:<20}| {:<12}| {:<14}| {:<15}| {:<13}| {:<14}|",
                row.0, row.1, row.2, row.3, row.4, row.5, row.6
            );
        } else {
            println!(
                "|{:<27}| {:<20}| {:<12}| {:<14}| {:<15}| {:<13}| {:<14}|",
                row.0, row.1, row.2, row.3, row.4, row.5, row.6
            );
        }
    }
    println!(
        "|{:-<27}-{:-<21}-{:-<13}-{:-<15}-{:-<16}-{:-<14}-{:-<15}|",
        "", "", "", "", "", "", ""
    );

    // Assert all limits
    for (message, cpu_used, mem_used, read_entries, write_entries, read_bytes, write_bytes) in data
    {
        assert!(
            cpu_used <= CPU_LIMIT,
            "🟥 {} CPU instructions exceeded limit",
            message
        );
        assert!(
            mem_used <= MEM_LIMIT,
            "🟥 {} Memory usage exceeded limit",
            message
        );
        assert!(
            read_entries <= READ_ENTRIES_LIMIT,
            "🟥 {} Read entries exceeded limit",
            message
        );
        assert!(
            write_entries <= WRITE_ENTRIES_LIMIT,
            "🟥 {} Write entries exceeded limit",
            message
        );
        assert!(
            read_bytes <= READ_BYTES_LIMIT,
            "🟥 {} Read bytes exceeded limit",
            message
        );
        assert!(
            write_bytes <= WRITE_BYTES_LIMIT,
            "🟥 {} Write bytes exceeded limit",
            message
        );
    }
}

// =============================================================================
// Footprint Analysis and Resource Attribution
// =============================================================================

/// Captured resource snapshot at a point in time
#[derive(Debug, Clone)]
pub struct ResourceCheckpoint {
    pub label: String,
    pub cpu_insns: u64,
    pub mem_bytes: u64,
    pub read_entries: u32,
    pub write_entries: u32,
    pub read_bytes: u32,
    pub write_bytes: u32,
}

/// Resource delta between two checkpoints
#[derive(Debug, Clone)]
pub struct ResourceDelta {
    pub from_label: String,
    pub to_label: String,
    pub cpu_insns_delta: u64,
    pub mem_bytes_delta: u64,
    pub read_entries_delta: u32,
    pub write_entries_delta: u32,
    pub read_bytes_delta: u32,
    pub write_bytes_delta: u32,
}

/// Resource cost attribution
#[derive(Debug, Clone)]
pub struct ResourceAttribution {
    pub vm_instantiation_cost: u64,
    pub storage_read_cost: u64,
    pub storage_write_cost: u64,
    pub computation_cost: u64,
}

/// Capture current resource state
/// Returns a zero checkpoint if cost_estimate is not available (no invocation yet)
pub fn capture_resources(env: &Env, label: &str) -> ResourceCheckpoint {
    // Try to get cost estimate, but handle the case where no invocation has happened yet
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        let cost_estimate = env.cost_estimate();
        let resources = cost_estimate.resources();
        
        ResourceCheckpoint {
            label: label.to_string(),
            cpu_insns: cost_estimate.budget().cpu_instruction_cost(),
            mem_bytes: cost_estimate.budget().memory_bytes_cost(),
            read_entries: 0, // Field removed in SDK 23.x
            write_entries: resources.write_entries,
            read_bytes: 0, // Field removed in SDK 23.x
            write_bytes: resources.write_bytes,
        }
    }));
    
    match result {
        Ok(checkpoint) => checkpoint,
        Err(_) => {
            // No invocation has happened yet, return zero checkpoint
            ResourceCheckpoint {
                label: label.to_string(),
                cpu_insns: 0,
                mem_bytes: 0,
                read_entries: 0,
                write_entries: 0,
                read_bytes: 0,
                write_bytes: 0,
            }
        }
    }
}

/// Calculate delta between two checkpoints
pub fn calculate_delta(from: &ResourceCheckpoint, to: &ResourceCheckpoint) -> ResourceDelta {
    ResourceDelta {
        from_label: from.label.clone(),
        to_label: to.label.clone(),
        cpu_insns_delta: to.cpu_insns.saturating_sub(from.cpu_insns),
        mem_bytes_delta: to.mem_bytes.saturating_sub(from.mem_bytes),
        read_entries_delta: to.read_entries.saturating_sub(from.read_entries),
        write_entries_delta: to.write_entries.saturating_sub(from.write_entries),
        read_bytes_delta: to.read_bytes.saturating_sub(from.read_bytes),
        write_bytes_delta: to.write_bytes.saturating_sub(from.write_bytes),
    }
}

/// Print resource delta in a readable format
pub fn print_resource_delta(delta: &ResourceDelta) {
    println!("📊 Resource Delta: {} -> {}", delta.from_label, delta.to_label);
    println!("   CPU Instructions: +{}", delta.cpu_insns_delta);
    println!("   Memory Bytes:     +{}", delta.mem_bytes_delta);
    println!("   Read Entries:     +{}", delta.read_entries_delta);
    println!("   Write Entries:    +{}", delta.write_entries_delta);
    println!("   Read Bytes:       +{}", delta.read_bytes_delta);
    println!("   Write Bytes:      +{}", delta.write_bytes_delta);
    println!();
}

/// Attribute costs to specific operation types
/// 
/// Uses heuristics since Soroban doesn't provide per-operation traces:
/// - VM instantiation: ~10M+ CPU instructions
/// - Storage reads: ~100k CPU per entry
/// - Storage writes: ~200k CPU per entry
/// - Remaining: computation
pub fn attribute_costs(delta: &ResourceDelta) -> ResourceAttribution {
    // Heuristic: VM instantiation typically costs 10M+ CPU instructions
    let vm_cost = if delta.cpu_insns_delta > 10_000_000 {
        10_000_000.min(delta.cpu_insns_delta)
    } else {
        0
    };
    
    // Heuristic: Storage operations cost ~100-200k CPU per entry
    let storage_read_cost = (delta.read_entries_delta as u64) * 100_000;
    let storage_write_cost = (delta.write_entries_delta as u64) * 200_000;
    
    // Remaining is computation
    let computation_cost = delta.cpu_insns_delta
        .saturating_sub(vm_cost)
        .saturating_sub(storage_read_cost)
        .saturating_sub(storage_write_cost);
    
    ResourceAttribution {
        vm_instantiation_cost: vm_cost,
        storage_read_cost,
        storage_write_cost,
        computation_cost,
    }
}

/// Print resource attribution breakdown
pub fn print_attribution(attribution: &ResourceAttribution) {
    let total = attribution.vm_instantiation_cost 
        + attribution.storage_read_cost 
        + attribution.storage_write_cost 
        + attribution.computation_cost;
    
    if total == 0 {
        println!("No resource usage to attribute");
        return;
    }
    
    println!("📊 Resource Attribution:");
    println!("   VM Instantiation: {:>12} ({:>5.1}%)", 
        attribution.vm_instantiation_cost,
        (attribution.vm_instantiation_cost as f64 / total as f64) * 100.0
    );
    println!("   Storage Reads:    {:>12} ({:>5.1}%)", 
        attribution.storage_read_cost,
        (attribution.storage_read_cost as f64 / total as f64) * 100.0
    );
    println!("   Storage Writes:   {:>12} ({:>5.1}%)", 
        attribution.storage_write_cost,
        (attribution.storage_write_cost as f64 / total as f64) * 100.0
    );
    println!("   Computation:      {:>12} ({:>5.1}%)", 
        attribution.computation_cost,
        (attribution.computation_cost as f64 / total as f64) * 100.0
    );
    println!();
}

/// Identify the primary cost driver
pub fn identify_primary_cost_driver(delta: &ResourceDelta) -> &'static str {
    // VM instantiation typically costs 10M+ CPU instructions
    if delta.cpu_insns_delta > 10_000_000 {
        "VM instantiation (ContractCode)"
    } else if delta.write_bytes_delta > 10_000 {
        "Large storage write"
    } else if delta.write_entries_delta > 5 {
        "Multiple storage writes"
    } else if delta.read_entries_delta > 10 {
        "Multiple storage reads"
    } else if delta.cpu_insns_delta > 1_000_000 {
        "Computation (loops/iteration)"
    } else {
        "Minimal operation"
    }
}

/// Check if resources are approaching limits and warn
/// Returns early if cost_estimate is not available (no invocation yet)
pub fn check_resource_limits_with_warnings(e: &Env, message: &str) {
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        let cost_estimate = e.cost_estimate();
        let cpu_used = cost_estimate.budget().cpu_instruction_cost();
        let mem_used = cost_estimate.budget().memory_bytes_cost();
        let resources = cost_estimate.resources();
        
        (cpu_used, mem_used, resources)
    }));
    
    let (cpu_used, mem_used, resources) = match result {
        Ok((cpu, mem, res)) => (cpu, mem, res),
        Err(_) => {
            // No invocation has happened yet, just print message and return
            println!("{}", message);
            println!("⚠️  Cost estimate not available (no invocation yet)");
            println!("===========================================");
            return;
        }
    };
    
    println!("{}", message);
    
    // CPU check with warning levels
    let cpu_pct = (cpu_used as f64 / CPU_LIMIT as f64) * 100.0;
    if cpu_pct > 90.0 {
        println!("🔴 CPU: {} / {} ({:.1}%) - CRITICAL", cpu_used, CPU_LIMIT, cpu_pct);
    } else if cpu_pct > 75.0 {
        println!("🟡 CPU: {} / {} ({:.1}%) - WARNING", cpu_used, CPU_LIMIT, cpu_pct);
    } else {
        println!("✅ CPU: {} / {} ({:.1}%)", cpu_used, CPU_LIMIT, cpu_pct);
    }
    
    // Memory check
    let mem_pct = (mem_used as f64 / MEM_LIMIT as f64) * 100.0;
    if mem_pct > 90.0 {
        println!("🔴 MEM: {} / {} ({:.1}%) - CRITICAL", mem_used, MEM_LIMIT, mem_pct);
    } else if mem_pct > 75.0 {
        println!("🟡 MEM: {} / {} ({:.1}%) - WARNING", mem_used, MEM_LIMIT, mem_pct);
    } else {
        println!("✅ MEM: {} / {} ({:.1}%)", mem_used, MEM_LIMIT, mem_pct);
    }
    
    // Storage checks
    // Note: read_entries field removed in SDK 23.x
    if resources.write_entries > (WRITE_ENTRIES_LIMIT * 3 / 4) {
        println!("🟡 Write Entries: {} / {} - WARNING", resources.write_entries, WRITE_ENTRIES_LIMIT);
    }
    
    println!("===========================================");
}

/// Compare resources before and after optimization
pub fn compare_optimization(
    before_label: &str,
    before: &ResourceCheckpoint,
    after_label: &str,
    after: &ResourceCheckpoint,
) {
    println!("========================================");
    println!("📊 Optimization Comparison");
    println!("========================================");
    println!();
    
    let cpu_diff = after.cpu_insns as i128 - before.cpu_insns as i128;
    let mem_diff = after.mem_bytes as i128 - before.mem_bytes as i128;
    
    println!("Before: {}", before_label);
    println!("After:  {}", after_label);
    println!();
    
    println!("CPU Instructions:");
    println!("  Before: {}", before.cpu_insns);
    println!("  After:  {}", after.cpu_insns);
    if cpu_diff != 0 {
        println!("  Change: {} ({:.1}%)", 
            cpu_diff,
            (cpu_diff as f64 / before.cpu_insns as f64) * 100.0
        );
    }
    println!();
    
    println!("Memory Bytes:");
    println!("  Before: {}", before.mem_bytes);
    println!("  After:  {}", after.mem_bytes);
    if mem_diff != 0 {
        println!("  Change: {} ({:.1}%)", 
            mem_diff,
            (mem_diff as f64 / before.mem_bytes as f64) * 100.0
        );
    }
    println!();
    
    if cpu_diff < 0 {
        println!("✅ Optimization successful: {} CPU instructions saved ({:.1}%)", 
            -cpu_diff,
            (-cpu_diff as f64 / before.cpu_insns as f64) * 100.0
        );
    } else if cpu_diff > 0 {
        println!("⚠️  Regression: {} CPU instructions added ({:.1}%)", 
            cpu_diff,
            (cpu_diff as f64 / before.cpu_insns as f64) * 100.0
        );
    } else {
        println!("➡️  No change in CPU usage");
    }
    println!("========================================");
}
