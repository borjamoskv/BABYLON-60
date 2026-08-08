// C5-REAL EXERGY CERTIFIED
// Purga atómica de DNS Cache en macOS
use std::process::Command;

pub struct DnsHealer;

impl DnsHealer {
    pub fn flush_cache() -> std::io::Result<bool> {
        let status1 = Command::new("dscacheutil")
            .arg("-flushcache")
            .status()?;

        let status2 = Command::new("killall")
            .args(["-HUP", "mDNSResponder"])
            .status()?;

        Ok(status1.success() && status2.success())
    }
}
