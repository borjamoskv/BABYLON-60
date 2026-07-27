//! # Resource Analyzer
//!
//! Utilities for analyzing Soroban transaction resource consumption.
//! Provides detailed attribution of CPU, memory, and storage costs.

use soroban_sdk::Env;

/// Resource breakdown for a single operation or checkpoint
#[derive(Debug, Clone)]
pub struct ResourceSnapshot {
    pub label: String,
    pub cpu_insns: u64,
    pub mem_bytes: u64,
    pub read_entries: u32,
    pub write_entries: u32,
    pub read_bytes: u32,
    pub write_bytes: u32,
}

impl ResourceSnapshot {
    /// Capture current resource usage from environment
    pub fn capture(env: &Env, label: impl Into<String>) -> Self {
        let cost_estimate = env.cost_estimate();
        let resources = cost_estimate.resources();
        
        Self {
            label: label.into(),
            cpu_insns: cost_estimate.budget().cpu_instruction_cost(),
            mem_bytes: cost_estimate.budget().memory_bytes_cost(),
            read_entries: 0, // Field removed in SDK 23.x
            write_entries: resources.write_entries,
            read_bytes: 0, // Field removed in SDK 23.x
            write_bytes: resources.write_bytes,
        }
    }
    
    /// Calculate the delta between two snapshots
    pub fn delta(&self, previous: &ResourceSnapshot) -> ResourceDelta {
        ResourceDelta {
            label: format!("{} -> {}", previous.label, self.label),
            cpu_insns_delta: self.cpu_insns.saturating_sub(previous.cpu_insns),
            mem_bytes_delta: self.mem_bytes.saturating_sub(previous.mem_bytes),
            read_entries_delta: self.read_entries.saturating_sub(previous.read_entries),
            write_entries_delta: self.write_entries.saturating_sub(previous.write_entries),
            read_bytes_delta: self.read_bytes.saturating_sub(previous.read_bytes),
            write_bytes_delta: self.write_bytes.saturating_sub(previous.write_bytes),
        }
    }
}

/// Resource delta between two snapshots
#[derive(Debug, Clone)]
pub struct ResourceDelta {
    pub label: String,
    pub cpu_insns_delta: u64,
    pub mem_bytes_delta: u64,
    pub read_entries_delta: u32,
    pub write_entries_delta: u32,
    pub read_bytes_delta: u32,
    pub write_bytes_delta: u32,
}

impl ResourceDelta {
    /// Print the delta in a human-readable format
    pub fn print(&self) {
        println!("📊 Resource Delta: {}", self.label);
        println!("   CPU Instructions: +{}", self.cpu_insns_delta);
        println!("   Memory Bytes:     +{}", self.mem_bytes_delta);
        println!("   Read Entries:     +{}", self.read_entries_delta);
        println!("   Write Entries:    +{}", self.write_entries_delta);
        println!("   Read Bytes:       +{}", self.read_bytes_delta);
        println!("   Write Bytes:      +{}", self.write_bytes_delta);
        println!();
    }
    
    /// Estimate the primary cost driver
    pub fn primary_cost_driver(&self) -> &'static str {
        // VM instantiation typically costs 10M+ CPU instructions
        if self.cpu_insns_delta > 10_000_000 {
            "VM instantiation (ContractCode)"
        } else if self.write_bytes_delta > 10_000 {
            "Large storage write"
        } else if self.write_entries_delta > 5 {
            "Multiple storage writes"
        } else if self.read_entries_delta > 10 {
            "Multiple storage reads"
        } else if self.cpu_insns_delta > 1_000_000 {
            "Computation (loops/iteration)"
        } else {
            "Minimal operation"
        }
    }
}

/// Resource analyzer for tracking operations across a test
pub struct ResourceAnalyzer {
    snapshots: Vec<ResourceSnapshot>,
}

impl ResourceAnalyzer {
    /// Create a new resource analyzer
    pub fn new() -> Self {
        Self {
            snapshots: Vec::new(),
        }
    }
    
    /// Capture a snapshot at a checkpoint
    pub fn checkpoint(&mut self, env: &Env, label: impl Into<String>) {
        self.snapshots.push(ResourceSnapshot::capture(env, label));
    }
    
    /// Get all snapshots
    pub fn snapshots(&self) -> &[ResourceSnapshot] {
        &self.snapshots
    }
    
    /// Calculate deltas between consecutive snapshots
    pub fn deltas(&self) -> Vec<ResourceDelta> {
        self.snapshots
            .windows(2)
            .map(|window| window[1].delta(&window[0]))
            .collect()
    }
    
    /// Print a summary report
    pub fn print_report(&self) {
        println!("========================================");
        println!("📈 Resource Analysis Report");
        println!("========================================");
        println!();
        
        if self.snapshots.is_empty() {
            println!("⚠️  No snapshots captured");
            return;
        }
        
        // Print absolute values
        println!("📊 Absolute Resource Usage:");
        println!();
        for snapshot in &self.snapshots {
            println!("  {}", snapshot.label);
            println!("    CPU Instructions: {}", snapshot.cpu_insns);
            println!("    Memory Bytes:     {}", snapshot.mem_bytes);
            println!("    Read Entries:     {}", snapshot.read_entries);
            println!("    Write Entries:    {}", snapshot.write_entries);
            println!("    Read Bytes:       {}", snapshot.read_bytes);
            println!("    Write Bytes:      {}", snapshot.write_bytes);
            println!();
        }
        
        // Print deltas
        if self.snapshots.len() > 1 {
            println!("========================================");
            println!("📊 Resource Deltas (Operation Costs):");
            println!("========================================");
            println!();
            
            for delta in self.deltas() {
                delta.print();
                println!("   Primary driver: {}", delta.primary_cost_driver());
                println!();
            }
        }
        
        // Print summary
        if let (Some(first), Some(last)) = (self.snapshots.first(), self.snapshots.last()) {
            let total_delta = last.delta(first);
            println!("========================================");
            println!("📊 Total Resource Consumption:");
            println!("========================================");
            total_delta.print();
        }
    }
    
    /// Print a comparison between two analyzers (e.g., before/after optimization)
    pub fn print_comparison(before: &ResourceAnalyzer, after: &ResourceAnalyzer, label: &str) {
        println!("========================================");
        println!("📊 Resource Comparison: {}", label);
        println!("========================================");
        println!();
        
        if before.snapshots.is_empty() || after.snapshots.is_empty() {
            println!("⚠️  Insufficient data for comparison");
            return;
        }
        
        let before_total = before.snapshots.last().unwrap();
        let after_total = after.snapshots.last().unwrap();
        
        let cpu_diff = after_total.cpu_insns as i128 - before_total.cpu_insns as i128;
        let mem_diff = after_total.mem_bytes as i128 - before_total.mem_bytes as i128;
        
        println!("CPU Instructions:");
        println!("  Before: {}", before_total.cpu_insns);
        println!("  After:  {}", after_total.cpu_insns);
        println!("  Change: {} ({:.1}%)", 
            cpu_diff,
            (cpu_diff as f64 / before_total.cpu_insns as f64) * 100.0
        );
        println!();
        
        println!("Memory Bytes:");
        println!("  Before: {}", before_total.mem_bytes);
        println!("  After:  {}", after_total.mem_bytes);
        println!("  Change: {} ({:.1}%)", 
            mem_diff,
            (mem_diff as f64 / before_total.mem_bytes as f64) * 100.0
        );
        println!();
        
        if cpu_diff < 0 {
            println!("✅ Optimization successful: {} CPU instructions saved", -cpu_diff);
        } else if cpu_diff > 0 {
            println!("⚠️  Regression: {} CPU instructions added", cpu_diff);
        } else {
            println!("➡️  No change in CPU usage");
        }
    }
}

impl Default for ResourceAnalyzer {
    fn default() -> Self {
        Self::new()
    }
}

/// Estimate VM instantiation cost by comparing WASM vs Rust registration
/// 
/// This is a helper to demonstrate the difference between:
/// - env.register(Contract, ()) - Rust-only, no VM instantiation
/// - env.register(contract::WASM, ()) - WASM-backed, includes VM instantiation
pub fn estimate_vm_instantiation_cost(
    wasm_snapshot: &ResourceSnapshot,
    rust_snapshot: &ResourceSnapshot,
) -> u64 {
    wasm_snapshot.cpu_insns.saturating_sub(rust_snapshot.cpu_insns)
}

/// Attribute resource costs to specific operation types
#[derive(Debug, Clone)]
pub struct ResourceAttribution {
    pub vm_instantiation_cost: u64,
    pub storage_read_cost: u64,
    pub storage_write_cost: u64,
    pub computation_cost: u64,
}

impl ResourceAttribution {
    /// Attempt to attribute costs based on heuristics
    /// 
    /// Note: This is approximate since Soroban doesn't provide per-operation traces
    pub fn from_delta(delta: &ResourceDelta) -> Self {
        // Heuristic: VM instantiation typically costs 10M+ CPU instructions
        let vm_cost = if delta.cpu_insns_delta > 10_000_000 {
            10_000_000.min(delta.cpu_insns_delta)
        } else {
            0
        };
        
        // Heuristic: Storage operations cost ~100k CPU per entry
        let storage_read_cost = (delta.read_entries_delta as u64) * 100_000;
        let storage_write_cost = (delta.write_entries_delta as u64) * 200_000;
        
        // Remaining is computation
        let computation_cost = delta.cpu_insns_delta
            .saturating_sub(vm_cost)
            .saturating_sub(storage_read_cost)
            .saturating_sub(storage_write_cost);
        
        Self {
            vm_instantiation_cost: vm_cost,
            storage_read_cost,
            storage_write_cost,
            computation_cost,
        }
    }
    
    /// Print the attribution breakdown
    pub fn print(&self) {
        let total = self.vm_instantiation_cost 
            + self.storage_read_cost 
            + self.storage_write_cost 
            + self.computation_cost;
        
        if total == 0 {
            println!("No resource usage to attribute");
            return;
        }
        
        println!("📊 Resource Attribution:");
        println!("   VM Instantiation: {} ({:.1}%)", 
            self.vm_instantiation_cost,
            (self.vm_instantiation_cost as f64 / total as f64) * 100.0
        );
        println!("   Storage Reads:    {} ({:.1}%)", 
            self.storage_read_cost,
            (self.storage_read_cost as f64 / total as f64) * 100.0
        );
        println!("   Storage Writes:   {} ({:.1}%)", 
            self.storage_write_cost,
            (self.storage_write_cost as f64 / total as f64) * 100.0
        );
        println!("   Computation:      {} ({:.1}%)", 
            self.computation_cost,
            (self.computation_cost as f64 / total as f64) * 100.0
        );
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use soroban_sdk::{contract, contractimpl};
    
    // Minimal contract stub for enabling cost metering in tests
    #[contract]
    struct TestStub;
    
    #[contractimpl]
    impl TestStub {
        pub fn noop(_env: soroban_sdk::Env) {}
    }
    
    #[test]
    fn test_resource_snapshot() {
        let env = Env::default();
        // Register a contract to enable cost metering
        // This is required for cost_estimate() to work
        let _contract_id = env.register(TestStub, ());
        
        let snapshot = ResourceSnapshot::capture(&env, "test");
        assert_eq!(snapshot.label, "test");
    }
    
    #[test]
    fn test_resource_delta() {
        let snap1 = ResourceSnapshot {
            label: "start".to_string(),
            cpu_insns: 1000,
            mem_bytes: 500,
            read_entries: 2,
            write_entries: 1,
            read_bytes: 100,
            write_bytes: 50,
        };
        
        let snap2 = ResourceSnapshot {
            label: "end".to_string(),
            cpu_insns: 2000,
            mem_bytes: 800,
            read_entries: 5,
            write_entries: 3,
            read_bytes: 300,
            write_bytes: 150,
        };
        
        let delta = snap2.delta(&snap1);
        assert_eq!(delta.cpu_insns_delta, 1000);
        assert_eq!(delta.mem_bytes_delta, 300);
        assert_eq!(delta.read_entries_delta, 3);
        assert_eq!(delta.write_entries_delta, 2);
    }
    
    #[test]
    fn test_primary_cost_driver() {
        let delta = ResourceDelta {
            label: "test".to_string(),
            cpu_insns_delta: 15_000_000,
            mem_bytes_delta: 1000,
            read_entries_delta: 1,
            write_entries_delta: 1,
            read_bytes_delta: 100,
            write_bytes_delta: 100,
        };
        
        assert_eq!(delta.primary_cost_driver(), "VM instantiation (ContractCode)");
    }
}
