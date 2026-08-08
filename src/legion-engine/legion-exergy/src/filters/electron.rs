// C5-REAL EXERGY CERTIFIED
// Filtro Quirúrgico para aplicaciones Electron / Chromium
// Preserva sesiones, logins y bases de datos; purga GPUCache y blobs temporales
use std::path::Path;

pub struct ElectronFilter;

impl ElectronFilter {
    /// Devuelve true si la ruta es un archivo o directorio que DEBE ser preservado (Sesión/Login)
    pub fn is_protected_session_data(path: &Path) -> bool {
        let path_str = path.to_string_lossy();
        path_str.contains("/Cookies")
            || path_str.contains("/Local Storage")
            || path_str.contains("/Session Storage")
            || path_str.contains("/IndexedDB")
            || path_str.contains("/databases")
            || path_str.ends_with(".db")
            || path_str.ends_with(".sqlite")
    }

    /// Devuelve true si la ruta es anergía de renderizado purgable
    pub fn is_purgable_electron_cache(path: &Path) -> bool {
        if Self::is_protected_session_data(path) {
            return false;
        }
        let path_str = path.to_string_lossy();
        path_str.contains("/GPUCache")
            || path_str.contains("/Code Cache")
            || path_str.contains("/Cache_Data")
            || path_str.contains("/DawnCache")
            || path_str.contains("/blob_storage")
            || path_str.contains("/webrtc_event_logs")
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    #[test]
    fn test_electron_protects_cookies() {
        let p = PathBuf::from("/Users/user/Library/Application Support/Slack/Cookies");
        assert!(ElectronFilter::is_protected_session_data(&p));
        assert!(!ElectronFilter::is_purgable_electron_cache(&p));
    }

    #[test]
    fn test_electron_purges_gpucache() {
        let p = PathBuf::from("/Users/user/Library/Application Support/Slack/GPUCache/data_0");
        assert!(!ElectronFilter::is_protected_session_data(&p));
        assert!(ElectronFilter::is_purgable_electron_cache(&p));
    }
}
