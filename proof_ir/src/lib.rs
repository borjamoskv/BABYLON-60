// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
#![no_std]

extern crate alloc;

use alloc::string::String;
use alloc::vec::Vec;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProofObligation {
    pub name: String,
    pub hypotheses: Vec<String>,
    pub goal: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Invariant {
    pub name: String,
    pub condition: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AbstractState {
    pub variables: Vec<(String, String)>, // name, type
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProofIR {
    pub state: AbstractState,
    pub invariants: Vec<Invariant>,
    pub obligations: Vec<ProofObligation>,
}
