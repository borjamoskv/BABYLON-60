// C5-REAL EXERGY CERTIFIED
// ExergyScript AST (Abstract Syntax Tree)
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum ActionType {
    SafeTrash,   // Mover a ~/.Trash (permite deshacer)
    CloudEvict,  // brctl evict (desalojo local de iCloud)
    Immune,      // Proteger formalmente / Inmunidad
    HealDNS,     // Purga de DNS y mDNSResponder
    HealLS,      // Reconstrucción de LaunchServices
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Expr {
    // Predicados de Silicio y FileSystem
    AgeDays(f64),
    SizeBytes(u64),
    EntropyMax(f64),
    IsDevArtifact,
    IsElectronCache,
    IsLocked,

    // Operaciones Booleanas
    Gt(Box<Expr>, Box<Expr>),
    Lt(Box<Expr>, Box<Expr>),
    Eq(Box<Expr>, Box<Expr>),
    And(Box<Expr>, Box<Expr>),
    Or(Box<Expr>, Box<Expr>),
    Not(Box<Expr>),
    BoolLiteral(bool),

    // Identificadores de campo
    FieldAge,
    FieldSize,
    FieldEntropy,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Rule {
    pub name: String,
    pub target_pattern: String,
    pub guard: Expr,
    pub action: ActionType,
    pub attest_scitt: bool,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Program {
    pub rules: Vec<Rule>,
}
