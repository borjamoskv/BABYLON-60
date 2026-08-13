// C5-REAL EXERGY CERTIFIED
// Reconstrucción determinista de LaunchServices sin AppleScript
use std::process::Command;
use std::path::Path;

pub const LSREGISTER_PATH: &str = "/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister";

pub struct LaunchServicesHealer;

impl LaunchServicesHealer {
    pub fn rebuild_database() -> std::io::Result<bool> {
        if !Path::new(LSREGISTER_PATH).exists() {
            return Ok(false);
        }

        let status = Command::new(LSREGISTER_PATH)
            .args(["-kill", "-r", "-domain", "local", "-domain", "system", "-domain", "user"])
            .status()?;

        Ok(status.success())
    }
}
