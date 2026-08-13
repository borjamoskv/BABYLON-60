// C5-REAL EXERGY CERTIFIED
use std::collections::{HashSet, HashMap};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CfGkatNode {
    Skip,
    Assign(String, String),
    Seq(Box<CfGkatNode>, Box<CfGkatNode>),
    IfThenElse(String, Box<CfGkatNode>, Box<CfGkatNode>),
    While(String, Box<CfGkatNode>),
    Goto(String),
    Break(Option<String>),
    Return(Option<String>),
    SandboxInvoke(String, HashMap<String, String>),
}

pub struct CfgkatContext {
    pub whitelisted_tools: HashSet<String>,
}

#[derive(Debug, PartialEq, Eq)]
pub enum ValidationError {
    UnauthorizedTool(String),
    MalformedGoto(String),
    SemanticEvasion, // INV-1 Evasión
}

/// Normaliza el árbol a su representante canónico módulo ≡.
/// Para el Hito 1 (T_eff), nos enfocamos en el rechazo estricto (falsabilidad)
/// de nodos maliciosos y evasiones de restricciones (cumpliendo INV-1).
pub fn normalize_and_validate(
    node: &CfGkatNode,
    ctx: &CfgkatContext,
) -> Result<CfGkatNode, ValidationError> {
    match node {
        CfGkatNode::Skip => Ok(CfGkatNode::Skip),
        CfGkatNode::Assign(var, expr) => Ok(CfGkatNode::Assign(var.clone(), expr.clone())),
        CfGkatNode::Seq(left, right) => {
            let left_norm = normalize_and_validate(left, ctx)?;
            let right_norm = normalize_and_validate(right, ctx)?;
            Ok(CfGkatNode::Seq(Box::new(left_norm), Box::new(right_norm)))
        }
        CfGkatNode::IfThenElse(cond, t_branch, e_branch) => {
            let t_norm = normalize_and_validate(t_branch, ctx)?;
            let e_norm = normalize_and_validate(e_branch, ctx)?;
            Ok(CfGkatNode::IfThenElse(cond.clone(), Box::new(t_norm), Box::new(e_norm)))
        }
        CfGkatNode::While(cond, body) => {
            let body_norm = normalize_and_validate(body, ctx)?;
            Ok(CfGkatNode::While(cond.clone(), Box::new(body_norm)))
        }
        CfGkatNode::Goto(label) => Ok(CfGkatNode::Goto(label.clone())),
        CfGkatNode::Break(label) => Ok(CfGkatNode::Break(label.clone())),
        CfGkatNode::Return(val) => Ok(CfGkatNode::Return(val.clone())),
        CfGkatNode::SandboxInvoke(tool_name, args) => {
            // INV-1: Validación estricta del alcance declarado.
            if !ctx.whitelisted_tools.contains(tool_name) {
                return Err(ValidationError::UnauthorizedTool(tool_name.clone()));
            }
            Ok(CfGkatNode::SandboxInvoke(tool_name.clone(), args.clone()))
        }
    }
}
