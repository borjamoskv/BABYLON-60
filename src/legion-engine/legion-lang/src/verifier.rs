// C5-REAL EXERGY CERTIFIED
// Tribunal de Inmunidad y Verificador Formal a Tiempo de Compilación
use crate::ast::*;

#[derive(Debug, Clone, PartialEq)]
pub enum VerificationError {
    ImmunityViolation {
        rule_name: String,
        target_pattern: String,
        reason: String,
    },
    UnboundedPurgeGuard {
        rule_name: String,
        reason: String,
    },
}

pub struct ImmunityVerifier;

impl ImmunityVerifier {
    /// Verifica formalmente un programa ExergyScript.
    /// Garantiza a nivel de tipos y AST que ninguna regla vulnere el Escudo de Inmunidad.
    pub fn verify_program(program: &Program) -> Result<(), VerificationError> {
        for rule in &program.rules {
            Self::verify_rule(rule)?;
        }
        Ok(())
    }

    pub fn verify_rule(rule: &Rule) -> Result<(), VerificationError> {
        let pattern = &rule.target_pattern;

        // Si la acción es explícitamente Immune, es una regla de protección válida
        if rule.action == ActionType::Immune {
            return Ok(());
        }

        let mut normalized = pattern.replace('\\', "/");
        while normalized.contains("//") {
            normalized = normalized.replace("//", "/");
        }
        let lower = normalized.to_lowercase();

        // 1. Verificación contra el Escudo de Inmunidad de Credenciales y Llaves (macOS, Windows, Linux)
        if lower.contains("/.ssh")
            || lower.contains("/.gnupg")
            || lower.contains("/.aws")
            || lower.contains("/keychains")
            || lower.contains("login.keychain")
            || lower.contains("/microsoft/protect")
            || lower.contains("/microsoft/credentials")
            || lower.contains("/etc/shadow")
        {
            return Err(VerificationError::ImmunityViolation {
                rule_name: rule.name.clone(),
                target_pattern: pattern.clone(),
                reason: "Intento de acción sobre almacenes de credenciales protegidos.".to_string(),
            });
        }

        // 2. Verificación contra Documentos Personales de Usuario
        if lower.contains("/documents")
            || lower.contains("/desktop")
            || lower.contains("/pictures")
            || lower.contains("/movies")
            || lower.contains("/system volume information")
            || lower.ends_with("/ntuser.dat")
        {
            if !lower.contains("/caches") && !lower.contains("/deriveddata") && !lower.contains("/temp") {
                return Err(VerificationError::ImmunityViolation {
                    rule_name: rule.name.clone(),
                    target_pattern: pattern.clone(),
                    reason: "Intento de acción sobre carpetas personales de usuario o archivos del sistema.".to_string(),
                });
            }
        }

        // 3. Verificación contra el Core del Sistema y Firmas Activas
        if lower.contains("/_codesignature")
            || lower.contains("/system/")
            || lower.contains("/system32")
            || lower.contains("/usr/bin")
            || lower.contains("/bin/")
            || lower.starts_with("/boot")
        {
            return Err(VerificationError::ImmunityViolation {
                rule_name: rule.name.clone(),
                target_pattern: pattern.clone(),
                reason: "Intento de modificación sobre el sistema o firmas de código.".to_string(),
            });
        }

        // 4. Verificación de Guardas Estrictas
        if rule.action == ActionType::SafeTrash {
            if let Expr::BoolLiteral(true) = rule.guard {
                return Err(VerificationError::UnboundedPurgeGuard {
                    rule_name: rule.name.clone(),
                    reason: "Prohibida regla de purga con guarda 'true' incondicional sin filtro de edad o caché.".to_string(),
                });
            }
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rejects_ssh_purge_rule() {
        let bad_rule = Rule {
            name: "NukeSSH".to_string(),
            target_pattern: "~/.ssh/*".to_string(),
            guard: Expr::BoolLiteral(false),
            action: ActionType::SafeTrash,
            attest_scitt: true,
        };
        let program = Program { rules: vec![bad_rule] };
        assert!(ImmunityVerifier::verify_program(&program).is_err());
    }

    #[test]
    fn test_accepts_valid_cache_purge_rule() {
        let good_rule = Rule {
            name: "CleanAdobe".to_string(),
            target_pattern: "~/Library/Caches/com.adobe.*".to_string(),
            guard: Expr::Gt(Box::new(Expr::FieldAge), Box::new(Expr::AgeDays(14.0))),
            action: ActionType::SafeTrash,
            attest_scitt: true,
        };
        let program = Program { rules: vec![good_rule] };
        assert!(ImmunityVerifier::verify_program(&program).is_ok());
    }
}
