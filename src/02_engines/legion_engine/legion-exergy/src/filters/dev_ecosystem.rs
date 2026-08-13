// C5-REAL EXERGY CERTIFIED
// Filtro para artefactos de compilación y dependencias de desarrollo
use std::path::Path;

pub struct DevEcosystemFilter;

impl DevEcosystemFilter {
    /// Detecta si una ruta corresponde a artefactos de desarrollo purubles
    pub fn is_dev_artifact(path: &Path) -> bool {
        let path_str = path.to_string_lossy();
        path_str.contains("/target/debug/")
            || path_str.contains("/target/release/")
            || path_str.ends_with("/node_modules")
            || path_str.contains("/node_modules/")
            || path_str.ends_with("/DerivedData")
            || path_str.contains("/DerivedData/")
            || path_str.ends_with("/.venv")
            || path_str.contains("/.venv/")
            || path_str.ends_with("/Pods")
            || path_str.contains("/Pods/")
    }

    /// Nombre de la categoría de desarrollo
    pub fn classify_artifact(path: &Path) -> Option<&'static str> {
        let path_str = path.to_string_lossy();
        if path_str.contains("/target/") {
            Some("Rust Target Build")
        } else if path_str.contains("node_modules") {
            Some("Node.js Dependencies")
        } else if path_str.contains("DerivedData") {
            Some("Xcode DerivedData")
        } else if path_str.contains(".venv") {
            Some("Python VirtualEnv")
        } else if path_str.contains("Pods") {
            Some("CocoaPods Cache")
        } else {
            None
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    #[test]
    fn test_detect_node_modules() {
        let p = PathBuf::from("/Users/dev/project/node_modules/express");
        assert!(DevEcosystemFilter::is_dev_artifact(&p));
        assert_eq!(DevEcosystemFilter::classify_artifact(&p), Some("Node.js Dependencies"));
    }

    #[test]
    fn test_detect_rust_target() {
        let p = PathBuf::from("/Users/dev/rust-app/target/debug/incremental");
        assert!(DevEcosystemFilter::is_dev_artifact(&p));
        assert_eq!(DevEcosystemFilter::classify_artifact(&p), Some("Rust Target Build"));
    }
}
