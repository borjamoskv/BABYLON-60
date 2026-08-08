// C5-REAL EXERGY CERTIFIED
// Motor Discriminador Termodinámico: Compuerta de Triple Verificación 100% Anergía
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum RiskLevel {
    Green,   // 100% Anergía Verificada: Seguro para purgar a papelera (Caché fría > 14 días)
    Yellow,  // Exergía Potencial / Requiere Confirmación Explícita del Usuario
    Red,     // INMUNIDAD ABSOLUTA: Datos de Usuario, Documentos, Credenciales, Sistema
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExergyScore {
    pub value: f64,
    pub risk: RiskLevel,
    pub is_100pct_anergy: bool,
    pub is_immune: bool,
    pub explanation: String,
}

pub struct ExergyEvaluator;

impl ExergyEvaluator {
    /// Lista de Inmunidad Absoluta: NUNCA se tocan estos archivos/directorios bajo ninguna circunstancia
    pub fn is_strictly_immune(path: &Path) -> bool {
        let path_str = path.to_string_lossy();
        let normalized = path_str.replace('\\', "/");

        // 1. Inmunidad de Credenciales y Llaves (macOS, Windows, Linux)
        if normalized.contains("/.ssh")
            || normalized.contains("/.gnupg")
            || normalized.contains("/.aws")
            || normalized.contains("/Keychains")
            || normalized.contains("/login.keychain")
            || normalized.contains("/Microsoft/Protect")
            || normalized.contains("/Microsoft/Credentials")
            || normalized.contains("/etc/shadow")
            || normalized.contains("/etc/sudoers")
        {
            return true;
        }

        // 2. Inmunidad de Documentos y Datos de Usuario Personales
        if normalized.contains("/Documents/")
            || normalized.contains("/Desktop/")
            || normalized.contains("/Pictures/")
            || normalized.contains("/Movies/")
            || normalized.contains("/Music/Logic")
            || normalized.contains("/Music/Ableton")
            || normalized.contains("/System Volume Information")
            || normalized.contains("/System32")
            || normalized.ends_with("/NTUSER.DAT")
            || normalized.starts_with("/boot")
            || normalized.starts_with("/proc")
            || normalized.starts_with("/sys")
        {
            // Solo se permite si es una subcarpeta explícita de cache interna
            if !normalized.contains("/Caches/") && !normalized.contains("/DerivedData/") && !normalized.contains("/Temp/") {
                return true;
            }
        }

        // 3. Inmunidad de Configuración del Sistema y Shells
        if normalized.ends_with("/.zshrc")
            || normalized.ends_with("/.bashrc")
            || normalized.ends_with("/.gitconfig")
            || normalized.contains("/.git/objects")
            || normalized.contains("/.git/refs")
        {
            return true;
        }

        // 4. Inmunidad de Bases de Datos de Sesión y Logins
        if normalized.ends_with("/Cookies")
            || normalized.ends_with("/Cookies.binarycookies")
            || normalized.contains("/Local Storage/")
            || normalized.contains("/Session Storage/")
            || normalized.contains("/IndexedDB/")
            || normalized.ends_with(".keychain-db")
        {
            return true;
        }

        // 5. Inmunidad de Paquetes Firmados / Ejecutables protegidos
        if normalized.contains("/_CodeSignature") || normalized.contains("/Contents/MacOS/") {
            return true;
        }

        false
    }

    /// Evalúa y certifica si un archivo es 100% ANERGÍA PURA.
    /// Si existe la menor duda o el archivo tiene inmunidad, se clasifica como Red o Yellow.
    pub fn evaluate_file(
        path: &Path,
        size_bytes: u64,
        access_epoch: u64,
        _modify_epoch: u64,
        is_known_cache_pattern: bool,
    ) -> ExergyScore {
        // Compuerta 1: Escudo de Inmunidad Absoluta
        if Self::is_strictly_immune(path) {
            return ExergyScore {
                value: 1000.0,
                risk: RiskLevel::Red,
                is_100pct_anergy: false,
                is_immune: true,
                explanation: "INMUNIDAD ABSOLUTA: Archivo personal, credencial o sistema protegido.".to_string(),
            };
        }

        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();

        let days_since_access = if now > access_epoch {
            ((now - access_epoch) / 86400).max(1) as f64
        } else {
            1.0
        };

        let size_mb = (size_bytes as f64 / (1024.0 * 1024.0)).max(0.001);

        // Compuerta 2: Verificación Rigurosa de Anergía
        // Solo es 100% Anergía si es un patrón de caché conocido Y lleva > 14 días sin acceso
        let is_100pct_anergy = is_known_cache_pattern && (days_since_access >= 14.0);

        if is_100pct_anergy {
            let e_file = (1.0 / days_since_access) * 0.05 / (size_mb.sqrt() + 1.0);
            ExergyScore {
                value: e_file,
                risk: RiskLevel::Green,
                is_100pct_anergy: true,
                is_immune: false,
                explanation: format!(
                    "100% ANERGÍA CERTIFICADA (E={:.5}): Caché fría inactiva por {} días.",
                    e_file, days_since_access as u64
                ),
            }
        } else if is_known_cache_pattern {
            // Caché reciente (< 14 días): Requiere revisión porque puede estar en uso caliente
            ExergyScore {
                value: 0.15,
                risk: RiskLevel::Yellow,
                is_100pct_anergy: false,
                is_immune: false,
                explanation: format!(
                    "Caché activa/reciente (accedida hace {} días): Requiere confirmación manual.",
                    days_since_access as u64
                ),
            }
        } else {
            // Archivo desconocido: Proteger por defecto
            ExergyScore {
                value: 1.0,
                risk: RiskLevel::Yellow,
                is_100pct_anergy: false,
                is_immune: false,
                explanation: "Tipo de archivo no catalogado como anergía: Preservado preventivamente.".to_string(),
            }
        }
    }

    /// Calcula la entropía de Shannon H(X) sobre una muestra de bytes [0.0 - 8.0]
    pub fn shannon_entropy(sample: &[u8]) -> f64 {
        if sample.is_empty() {
            return 0.0;
        }
        let mut counts = [0usize; 256];
        for &byte in sample {
            counts[byte as usize] += 1;
        }
        let len = sample.len() as f64;
        let mut entropy = 0.0;
        for &count in &counts {
            if count > 0 {
                let p = count as f64 / len;
                entropy -= p * p.log2();
            }
        }
        entropy
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    #[test]
    fn test_documents_and_ssh_are_strictly_immune() {
        let ssh_key = PathBuf::from("/Users/user/.ssh/id_ed25519");
        let doc = PathBuf::from("/Users/user/Documents/Tesis_Doctoral.pdf");
        let cookies = PathBuf::from("/Users/user/Library/Application Support/Slack/Cookies");

        assert!(ExergyEvaluator::is_strictly_immune(&ssh_key));
        assert!(ExergyEvaluator::is_strictly_immune(&doc));
        assert!(ExergyEvaluator::is_strictly_immune(&cookies));

        let score_ssh = ExergyEvaluator::evaluate_file(&ssh_key, 1024, 0, 0, true);
        assert_eq!(score_ssh.risk, RiskLevel::Red);
        assert!(!score_ssh.is_100pct_anergy);
        assert!(score_ssh.is_immune);
    }

    #[test]
    fn test_old_cache_is_100pct_anergy() {
        let cache = PathBuf::from("/Users/user/Library/Caches/com.adobe.Photoshop/temp_cache.bin");
        let old_time = 1_000_000; // Muchos días atrás
        let score = ExergyEvaluator::evaluate_file(&cache, 100 * 1024 * 1024, old_time, old_time, true);

        assert_eq!(score.risk, RiskLevel::Green);
        assert!(score.is_100pct_anergy);
        assert!(!score.is_immune);
    }
}
