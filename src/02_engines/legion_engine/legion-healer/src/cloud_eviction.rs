// C5-REAL EXERGY CERTIFIED
// Desalojo Local de iCloud Drive (brctl evict)
use std::process::Command;
use std::path::Path;

pub struct CloudEviction;

impl CloudEviction {
    /// Desaloja la copia local del archivo en iCloud Drive sin borrarlo de la nube
    pub fn evict_local_copy(path: &Path) -> std::io::Result<bool> {
        let status = Command::new("brctl")
            .arg("evict")
            .arg(path)
            .status()?;

        Ok(status.success())
    }
}
