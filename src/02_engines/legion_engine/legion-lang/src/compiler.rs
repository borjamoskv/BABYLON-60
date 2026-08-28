// C5-REAL EXERGY CERTIFIED
// Compilador AST -> Bytecode para ExergyScript
use crate::ast::*;
use crate::bytecode::*;
use crate::verifier::ImmunityVerifier;

pub struct Compiler;

impl Compiler {
    pub fn compile(program: &Program) -> Result<CompiledProgram, String> {
        // Paso 1: Tribunal de Inmunidad
        ImmunityVerifier::verify_program(program)
            .map_err(|e| format!("Error de Verificación de Inmunidad: {:?}", e))?;

        let mut compiled_rules = Vec::new();
        for rule in &program.rules {
            compiled_rules.push(Self::compile_rule(rule)?);
        }

        Ok(CompiledProgram { rules: compiled_rules })
    }

    fn compile_rule(rule: &Rule) -> Result<CompiledRule, String> {
        let mut instructions = Vec::new();
        let mut constants_f64 = Vec::new();
        let mut constants_u64 = Vec::new();

        // 1. Inyectar siempre verificación de inmunidad previa
        instructions.push(OpCode::CheckImmunity);

        // 2. Compilar la guarda booleana
        Self::compile_expr(&rule.guard, &mut instructions, &mut constants_f64, &mut constants_u64)?;

        // 3. Instrucción de acción final
        match rule.action {
            ActionType::SafeTrash => instructions.push(OpCode::ActionSafeTrash),
            ActionType::CloudEvict => instructions.push(OpCode::ActionCloudEvict),
            ActionType::Immune => instructions.push(OpCode::ActionImmune),
            _ => instructions.push(OpCode::Halt),
        }

        instructions.push(OpCode::Halt);

        Ok(CompiledRule {
            name: rule.name.clone(),
            target_pattern: rule.target_pattern.clone(),
            instructions,
            constants_f64,
            constants_u64,
            attest_scitt: rule.attest_scitt,
        })
    }

    fn compile_expr(
        expr: &Expr,
        insts: &mut Vec<OpCode>,
        c_f64: &mut Vec<f64>,
        c_u64: &mut Vec<u64>,
    ) -> Result<(), String> {
        match expr {
            Expr::FieldAge => insts.push(OpCode::LoadAgeDays),
            Expr::FieldSize => insts.push(OpCode::LoadSizeBytes),
            Expr::FieldEntropy => insts.push(OpCode::LoadEntropy),
            Expr::IsDevArtifact => insts.push(OpCode::CheckDevArtifact),
            Expr::IsElectronCache => insts.push(OpCode::CheckElectronCache),
            Expr::IsLocked => insts.push(OpCode::CheckLocked),
            Expr::AgeDays(d) => {
                c_f64.push(*d);
                insts.push(OpCode::PushNumber);
            }
            Expr::SizeBytes(b) => {
                c_u64.push(*b);
                insts.push(OpCode::PushBytes);
            }
            Expr::EntropyMax(e) => {
                c_f64.push(*e);
                insts.push(OpCode::PushNumber);
            }
            Expr::BoolLiteral(b) => {
                insts.push(OpCode::PushBool);
                c_u64.push(if *b { 1 } else { 0 });
            }
            Expr::Gt(l, r) => {
                Self::compile_expr(l, insts, c_f64, c_u64)?;
                Self::compile_expr(r, insts, c_f64, c_u64)?;
                insts.push(OpCode::Gt);
            }
            Expr::Lt(l, r) => {
                Self::compile_expr(l, insts, c_f64, c_u64)?;
                Self::compile_expr(r, insts, c_f64, c_u64)?;
                insts.push(OpCode::Lt);
            }
            Expr::Eq(l, r) => {
                Self::compile_expr(l, insts, c_f64, c_u64)?;
                Self::compile_expr(r, insts, c_f64, c_u64)?;
                insts.push(OpCode::Eq);
            }
            Expr::And(l, r) => {
                Self::compile_expr(l, insts, c_f64, c_u64)?;
                Self::compile_expr(r, insts, c_f64, c_u64)?;
                insts.push(OpCode::And);
            }
            Expr::Or(l, r) => {
                Self::compile_expr(l, insts, c_f64, c_u64)?;
                Self::compile_expr(r, insts, c_f64, c_u64)?;
                insts.push(OpCode::Or);
            }
            Expr::Not(inner) => {
                Self::compile_expr(inner, insts, c_f64, c_u64)?;
                insts.push(OpCode::Not);
            }
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_compile_valid_rule() {
        let rule = Rule {
            name: "CleanAdobe".to_string(),
            target_pattern: "~/Library/Caches/com.adobe.*".to_string(),
            guard: Expr::Gt(Box::new(Expr::FieldAge), Box::new(Expr::AgeDays(14.0))),
            action: ActionType::SafeTrash,
            attest_scitt: true,
        };
        let program = Program { rules: vec![rule] };
        let compiled = Compiler::compile(&program).unwrap();
        assert_eq!(compiled.rules.len(), 1);
        assert_eq!(compiled.rules[0].instructions[0], OpCode::CheckImmunity);
    }
}
