// C5-REAL EXERGY CERTIFIED
// APFS Snapshots & Spaceman Reclamation Auditor
use std::process::Command;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApfsSnapshotInfo {
    pub name: String,
    pub date_tag: String,
}

pub struct SnapshotAuditor;

impl SnapshotAuditor {
    /// Lista los snapshots locales de Time Machine anclados al disco raíz
    pub fn list_local_snapshots() -> Vec<ApfsSnapshotInfo> {
        let output = Command::new("tmutil")
            .arg("listlocalsnapshots")
            .arg("/")
            .output();

        let mut snapshots = Vec::new();
        if let Ok(out) = output {
            let stdout = String::from_utf8_lossy(&out.stdout);
            for line in stdout.lines() {
                let trimmed = line.trim();
                // Formato típico: com.apple.TimeMachine.2024-03-24-150000.local
                if trimmed.starts_with("com.apple.TimeMachine.") {
                    let date_part = trimmed
                        .strip_prefix("com.apple.TimeMachine.")
                        .and_then(|s| s.strip_suffix(".local"))
                        .unwrap_or(trimmed);

                    snapshots.push(ApfsSnapshotInfo {
                        name: trimmed.to_string(),
                        date_tag: date_part.to_string(),
                    });
                }
            }
        }
        snapshots
    }

    /// Genera la orden de purga para snapshots locales antiguos
    pub fn purge_snapshot_command(date_tag: &str) -> String {
        format!("tmutil deletelocalsnapshots {}", date_tag)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_purge_command_generation() {
        let cmd = SnapshotAuditor::purge_snapshot_command("2024-03-24-150000");
        assert_eq!(cmd, "tmutil deletelocalsnapshots 2024-03-24-150000");
    }
}
