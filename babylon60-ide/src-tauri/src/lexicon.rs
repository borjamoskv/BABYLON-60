use serde::{Deserialize, Serialize};
use std::fmt;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum Domain {
    Source, Matrix, Pulse, Kinetic, Logic, Vector, Storage, Osint, Clock, Compiler,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum Primitive {
    Init, Mutate, Bind, Query, Stream, Commit, Sync, Halt, Fork, Join,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum Modifier {
    Raw, Atomic, Persist, Ephemeral, Async, Sync, Quantized, Mapped, Wrapped, Locked,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct VectorPath {
    pub domain: Domain,
    pub primitive: Primitive,
    pub modifier: Modifier,
}

impl VectorPath {
    pub const fn new(domain: Domain, primitive: Primitive, modifier: Modifier) -> Self {
        Self { domain, primitive, modifier }
    }

    /// Deterministic numeric index: D*100 + P*10 + M
    pub fn index(&self) -> usize {
        (self.domain as usize * 100) + (self.primitive as usize * 10) + self.modifier as usize
    }
}

impl fmt::Display for VectorPath {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[{:?}][{:?}][{:?}]", self.domain, self.primitive, self.modifier)
    }
}

impl fmt::Display for Domain {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { write!(f, "{:?}", self) }
}
impl fmt::Display for Primitive {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { write!(f, "{:?}", self) }
}
impl fmt::Display for Modifier {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { write!(f, "{:?}", self) }
}
