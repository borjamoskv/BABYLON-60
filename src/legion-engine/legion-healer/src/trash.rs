// C5-REAL EXERGY CERTIFIED
// Eliminación Segura hacia la Papelera de macOS (~/.Trash)
use std::path::{Path, PathBuf};
use std::fs;
use std::env;

pub struct SafeTrash;

impl SafeTrash {
    /// Mueve un archivo o directorio a la papelera del sistema con sufijo de timestamp (soporte de Deshacer)
    pub fn move_to_trash(path: &Path) -> std::io::Result<PathBuf> {
        let trash_dir = Self::get_system_trash_dir()?;

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

    fn get_system_trash_dir() -> std::io::Result<PathBuf> {
        if cfg!(target_os = "macos") {
            let home = env::var("HOME").map_err(|e| std::io::Error::new(std::io::ErrorKind::NotFound, e))?;
            Ok(Path::new(&home).join(".Trash"))
        } else if cfg!(target_os = "windows") {
            if let Ok(profile) = env::var("USERPROFILE") {
                Ok(Path::new(&profile).join(".Trash"))
            } else {
                let temp = env::var("TEMP").unwrap_or_else(|_| "C:\\Temp".to_string());
                Ok(Path::new(&temp).join("Trash"))
            }
        } else {
            // Linux / FreeDesktop.org Trash Specification
            let home = env::var("HOME").map_err(|e| std::io::Error::new(std::io::ErrorKind::NotFound, e))?;
            Ok(Path::new(&home).join(".local/share/Trash/files"))
        }
    }
}
