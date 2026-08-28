// C5-REAL EXERGY CERTIFIED
// Bytecode y OpCodes de ExergyScript
use serde::{Deserialize, Serialize};

#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum OpCode {
    Halt = 0x00,
    CheckImmunity = 0x01,
    LoadAgeDays = 0x02,
    LoadSizeBytes = 0x03,
    LoadEntropy = 0x04,
    CheckDevArtifact = 0x05,
    CheckElectronCache = 0x06,
    CheckLocked = 0x07,

    PushNumber = 0x10,
    PushBytes = 0x11,
    PushBool = 0x12,

    Gt = 0x20,
    Lt = 0x21,
    Eq = 0x22,
    And = 0x23,
    Or = 0x24,
    Not = 0x25,

    JumpIfFalse = 0x30,

    ActionSafeTrash = 0x40,
    ActionCloudEvict = 0x41,
    ActionImmune = 0x42,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompiledRule {
    pub name: String,
    pub target_pattern: String,
    pub instructions: Vec<OpCode>,
    pub constants_f64: Vec<f64>,
    pub constants_u64: Vec<u64>,
    pub attest_scitt: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompiledProgram {
    pub rules: Vec<CompiledRule>,
}
