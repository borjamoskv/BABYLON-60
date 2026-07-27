use crate::babylon_kernel::{AuditLogger, AuditEntry};
use std::io::Write;

pub struct Ledger {
    pub log_path: String,
}

impl AuditLogger for Ledger {
    fn log_cycle(&self, entry: AuditEntry) {
        let serialized = serde_json::to_string(&entry).unwrap();
        let mut file = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.log_path)
            .unwrap();
            
        writeln!(file, "{}", serialized).unwrap();
    }
}
