use serde::{Deserialize, Serialize};
use std::fmt;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Domain {
    Source = 0,
    Matrix = 1,
    Pulse = 2,
    Kinetic = 3,
    Logic = 4,
    Vector = 5,
    Storage = 6,
    Osint = 7,
    Clock = 8,
    Compiler = 9,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Primitive {
    Init = 0,
    Mutate = 1,
    Bind = 2,
    Query = 3,
    Stream = 4,
    Commit = 5,
    Sync = 6,
    Halt = 7,
    Fork = 8,
    Join = 9,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Modifier {
    Raw = 0,
    Atomic = 1,
    Persist = 2,
    Ephemeral = 3,
    Async = 4,
    Sync = 5,
    Quantized = 6,
    Mapped = 7,
    Wrapped = 8,
    Locked = 9,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct VectorPath {
    pub domain: Domain,
    pub primitive: Primitive,
    pub modifier: Modifier,
}

impl VectorPath {
    pub fn new(domain: Domain, primitive: Primitive, modifier: Modifier) -> Self {
        Self { domain, primitive, modifier }
    }

    pub fn index(&self) -> usize {
        (self.domain as usize * 100) + (self.primitive as usize * 10) + (self.modifier as usize)
    }
}

impl fmt::Display for VectorPath {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:?}.{:?}.{:?}", self.domain, self.primitive, self.modifier)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct VectorPath4D {
    pub domain: Domain,
    pub primitive: Primitive,
    pub modifier: Modifier,
    pub temporal: u8,
}

impl VectorPath4D {
    pub fn new(d: u8, p: u8, m: u8, t: u8) -> Result<Self, String> {
        let domain = match d {
            0 => Domain::Source,
            1 => Domain::Matrix,
            2 => Domain::Pulse,
            3 => Domain::Kinetic,
            4 => Domain::Logic,
            5 => Domain::Vector,
            6 => Domain::Storage,
            7 => Domain::Osint,
            8 => Domain::Clock,
            9 => Domain::Compiler,
            _ => return Err(format!("Invalid domain: {}", d)),
        };
        let primitive = match p {
            0 => Primitive::Init,
            1 => Primitive::Mutate,
            2 => Primitive::Bind,
            3 => Primitive::Query,
            4 => Primitive::Stream,
            5 => Primitive::Commit,
            6 => Primitive::Sync,
            7 => Primitive::Halt,
            8 => Primitive::Fork,
            9 => Primitive::Join,
            _ => return Err(format!("Invalid primitive: {}", p)),
        };
        let modifier = match m {
            0 => Modifier::Raw,
            1 => Modifier::Atomic,
            2 => Modifier::Persist,
            3 => Modifier::Ephemeral,
            4 => Modifier::Async,
            5 => Modifier::Sync,
            6 => Modifier::Quantized,
            7 => Modifier::Mapped,
            8 => Modifier::Wrapped,
            9 => Modifier::Locked,
            _ => return Err(format!("Invalid modifier: {}", m)),
        };
        Ok(Self {
            domain,
            primitive,
            modifier,
            temporal: t % 10,
        })
    }

    pub fn index(&self) -> usize {
        (self.domain as usize * 1000)
            + (self.primitive as usize * 100)
            + (self.modifier as usize * 10)
            + (self.temporal as usize)
    }

    pub fn to_3d(&self) -> VectorPath {
        VectorPath::new(self.domain, self.primitive, self.modifier)
    }
}

impl fmt::Display for VectorPath4D {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{:?}.{:?}.{:?}.T{}",
            self.domain, self.primitive, self.modifier, self.temporal
        )
    }
}
