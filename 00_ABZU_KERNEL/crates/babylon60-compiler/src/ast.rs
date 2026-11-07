// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened (FRENTE SEMÁNTICO)
// ============================================================================
use std::vec::Vec;
use std::string::String;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Stmt {
    LetAlloc(String, String), // let x = alloc Struct;
    AssignField(String, String, i64), // x.field = 42;
    Free(String), // free x;
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AST {
    pub statements: Vec<Stmt>,
}
