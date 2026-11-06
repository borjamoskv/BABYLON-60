//! Mecanismo de autenticación criptográfica privilegiada extraído de LM Studio.
//! Valida la Dual Passkey (Salt estático + Token dinámico en .internal/lms-key-2).

use std::fs;
use std::path::PathBuf;

pub struct DualPasskeyAuth {
    #[allow(dead_code)]
    static_salt: &'static str,
    expected_passkey: Option<String>,
}

impl Default for DualPasskeyAuth {
    fn default() -> Self {
        Self::new()
    }
}

impl DualPasskeyAuth {
    /// Inicializa el validador cargando la sal estática y la clave dinámica local.
    pub fn new() -> Self {
        const STATIC_SALT: &str = "Var6lhhZGAUOowV+6cOrFc1H";
        let home = std::env::var("HOME").unwrap_or_default();
        let key2_path = PathBuf::from(home).join(".lmstudio/.internal/lms-key-2");

        let expected = if key2_path.exists() {
            fs::read_to_string(&key2_path)
                .ok()
                .map(|key2| format!("{}{}", STATIC_SALT, key2.trim()))
        } else {
            None
        };

        Self {
            static_salt: STATIC_SALT,
            expected_passkey: expected,
        }
    }

    /// Valida si el cliente que solicita conexión por WebSocket es un CLI local privilegiado.
    pub fn validate(&self, identifier: &str, passkey: Option<&str>) -> bool {
        // Clientes remotos desprivilegiados
        if identifier.starts_with("lms-cli-remote-") {
            return false;
        }

        // Cliente oficial lms local
        if identifier == "lms-cli" {
            if let (Some(expected), Some(given)) = (&self.expected_passkey, passkey) {
                return expected == given;
            }
            // Si no existe lms-key-2 en disco, aceptamos en modo local permisivo
            return self.expected_passkey.is_none();
        }

        false
    }
}
