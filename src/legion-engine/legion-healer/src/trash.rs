// C5-REAL EXERGY CERTIFIED
// Eliminación Segura hacia la Papelera de macOS (~/.Trash)
use std::path::{Path, PathBuf};
use std::fs;
use std::env;

pub struct SafeTrash;

impl SafeTrash {
    /// Mueve un archivo o directorio a ~/.Trash con un sufijo de timestamp para evitar colisiones
    pub fn move_to_trash(path: &Path) -> std::io::Result<PathBuf> {
        let home = env::var("HOME").map_err(|e| std::io::Error::new(std::io::ErrorKind::NotFound, e))?;
        let trash_dir = Path::new(&home).join(".Trash");

        if !trash_dir.exists() {
            fs::create_dir_all(&trash_dir)?;
        }

        let file_name = path.file_name().unwrap_or_default().to_string_lossy();
        let timestamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();

        let destination = trash_dir.join(format!("{}_{}", file_name, timestamp));
        fs::rename(path, &destination)?;

        Ok(destination)
    }
}
