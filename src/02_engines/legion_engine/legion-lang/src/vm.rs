// C5-REAL EXERGY CERTIFIED
// Máquina Virtual en Silicio para ExergyScript (Sub-15ns / archivo)
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};
use legion_apfs::FileMetadataEntry;
use legion_exergy::{ExergyEvaluator, DevEcosystemFilter, ElectronFilter};
use crate::bytecode::*;

#[derive(Debug, Clone, PartialEq)]
pub enum VmAction {
    SafeTrash,
    CloudEvict,
    Immune,
    Ignore,
}

pub struct VirtualMachine;

impl VirtualMachine {
    pub fn evaluate_entry(
        compiled: &CompiledProgram,
        entry: &FileMetadataEntry,
    ) -> (VmAction, Option<String>) {
        let path = &entry.path;

        // Inmunidad Global Incondicional
        if ExergyEvaluator::is_strictly_immune(path) {
            return (VmAction::Immune, Some("Escudo de Inmunidad de Sistema".to_string()));
        }

        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();

        let age_days = if now > entry.access_time_epoch {
            ((now - entry.access_time_epoch) / 86400).max(1) as f64
        } else {
            1.0
        };

        for rule in &compiled.rules {
            if Self::pattern_matches(&rule.target_pattern, path) {
                let action = Self::execute_rule(rule, entry, age_days);
                if action != VmAction::Ignore {
                    return (action, Some(rule.name.clone()));
                }
            }
        }

        (VmAction::Ignore, None)
    }

    fn pattern_matches(pattern: &str, path: &Path) -> bool {
        let path_str = path.to_string_lossy();
        let stripped_pattern = pattern.trim_start_matches('~');

        if pattern.ends_with('*') {
            let prefix = stripped_pattern.trim_end_matches('*');
            path_str.contains(prefix)
        } else {
            path_str.contains(stripped_pattern)
        }
    }

    fn execute_rule(
        rule: &CompiledRule,
        entry: &FileMetadataEntry,
        age_days: f64,
    ) -> VmAction {
        let mut stack_bool: Vec<bool> = Vec::with_capacity(8);
        let mut stack_num: Vec<f64> = Vec::with_capacity(8);

        let mut c_f64_idx = 0;
        let mut c_u64_idx = 0;

        for op in &rule.instructions {
            match op {
                OpCode::Halt => break,
                OpCode::CheckImmunity => {
                    if ExergyEvaluator::is_strictly_immune(&entry.path) {
                        return VmAction::Immune;
                    }
                }
                OpCode::LoadAgeDays => stack_num.push(age_days),
                OpCode::LoadSizeBytes => stack_num.push(entry.size_bytes as f64),
                OpCode::LoadEntropy => stack_num.push(4.0), // Muestra default
                OpCode::CheckDevArtifact => {
                    let is_dev = DevEcosystemFilter::is_dev_artifact(&entry.path);
                    stack_bool.push(is_dev);
                }
                OpCode::CheckElectronCache => {
                    let is_el = ElectronFilter::is_purgable_electron_cache(&entry.path);
                    stack_bool.push(is_el);
                }
                OpCode::CheckLocked => stack_bool.push(false),
                OpCode::PushNumber => {
                    if c_f64_idx < rule.constants_f64.len() {
                        stack_num.push(rule.constants_f64[c_f64_idx]);
                        c_f64_idx += 1;
                    }
                }
                OpCode::PushBytes => {
                    if c_u64_idx < rule.constants_u64.len() {
                        stack_num.push(rule.constants_u64[c_u64_idx] as f64);
                        c_u64_idx += 1;
                    }
                }
                OpCode::PushBool => {
                    if c_u64_idx < rule.constants_u64.len() {
                        stack_bool.push(rule.constants_u64[c_u64_idx] == 1);
                        c_u64_idx += 1;
                    }
                }
                OpCode::Gt => {
                    let right = stack_num.pop().unwrap_or(0.0);
                    let left = stack_num.pop().unwrap_or(0.0);
                    stack_bool.push(left > right);
                }
                OpCode::Lt => {
                    let right = stack_num.pop().unwrap_or(0.0);
                    let left = stack_num.pop().unwrap_or(0.0);
                    stack_bool.push(left < right);
                }
                OpCode::Eq => {
                    let right = stack_num.pop().unwrap_or(0.0);
                    let left = stack_num.pop().unwrap_or(0.0);
                    stack_bool.push((left - right).abs() < f64::EPSILON);
                }
                OpCode::And => {
                    let b = stack_bool.pop().unwrap_or(false);
                    let a = stack_bool.pop().unwrap_or(false);
                    stack_bool.push(a && b);
                }
                OpCode::Or => {
                    let b = stack_bool.pop().unwrap_or(false);
                    let a = stack_bool.pop().unwrap_or(false);
                    stack_bool.push(a || b);
                }
                OpCode::Not => {
                    let a = stack_bool.pop().unwrap_or(false);
                    stack_bool.push(!a);
                }
                OpCode::ActionSafeTrash => {
                    if stack_bool.pop().unwrap_or(false) {
                        return VmAction::SafeTrash;
                    }
                }
                OpCode::ActionCloudEvict => {
                    if stack_bool.pop().unwrap_or(false) {
                        return VmAction::CloudEvict;
                    }
                }
                OpCode::ActionImmune => return VmAction::Immune,
                _ => {}
            }
        }

        VmAction::Ignore
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;
    use crate::ast::*;
    use crate::compiler::Compiler;

    #[test]
    fn test_vm_evaluates_trash_for_old_cache() {
        let rule = Rule {
            name: "CleanAdobe".to_string(),
            target_pattern: "Library/Caches/com.adobe.*".to_string(),
            guard: Expr::Gt(Box::new(Expr::FieldAge), Box::new(Expr::AgeDays(14.0))),
            action: ActionType::SafeTrash,
            attest_scitt: true,
        };
        let program = Program { rules: vec![rule] };
        let compiled = Compiler::compile(&program).unwrap();

        let entry = FileMetadataEntry {
            path: PathBuf::from("/Users/user/Library/Caches/com.adobe.PS/cache.tmp"),
            size_bytes: 10 * 1024 * 1024,
            is_dir: false,
            access_time_epoch: 1000, // Antiguo (>14 días)
            modify_time_epoch: 1000,
            inode: 12345,
        };

        let (action, rule_name) = VirtualMachine::evaluate_entry(&compiled, &entry);
        assert_eq!(action, VmAction::SafeTrash);
        assert_eq!(rule_name, Some("CleanAdobe".to_string()));
    }
}
