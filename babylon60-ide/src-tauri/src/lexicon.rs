use serde::{Deserialize, Serialize};
use std::convert::TryFrom;
use std::fmt;


#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Domain {
    Source   = 0,
    Matrix   = 1,
    Pulse    = 2,
    Kinetic  = 3,
    Logic    = 4,
    Vector   = 5,
    Storage  = 6,
    Osint    = 7,
    Clock    = 8,
    Compiler = 9,
}

impl TryFrom<u8> for Domain {
    type Error = &'static str;
    fn try_from(v: u8) -> Result<Self, Self::Error> {
        match v {
            0 => Ok(Domain::Source),   1 => Ok(Domain::Matrix),
            2 => Ok(Domain::Pulse),    3 => Ok(Domain::Kinetic),
            4 => Ok(Domain::Logic),    5 => Ok(Domain::Vector),
            6 => Ok(Domain::Storage),  7 => Ok(Domain::Osint),
            8 => Ok(Domain::Clock),    9 => Ok(Domain::Compiler),
            _ => Err("Invalid Domain index"),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Primitive {
    Init   = 0, Mutate = 1, Bind   = 2, Query  = 3, Stream = 4,
    Commit = 5, Sync   = 6, Halt   = 7, Fork   = 8, Join   = 9,
}

impl TryFrom<u8> for Primitive {
    type Error = &'static str;
    fn try_from(v: u8) -> Result<Self, Self::Error> {
        match v {
            0 => Ok(Primitive::Init),   1 => Ok(Primitive::Mutate),
            2 => Ok(Primitive::Bind),   3 => Ok(Primitive::Query),
            4 => Ok(Primitive::Stream), 5 => Ok(Primitive::Commit),
            6 => Ok(Primitive::Sync),   7 => Ok(Primitive::Halt),
            8 => Ok(Primitive::Fork),   9 => Ok(Primitive::Join),
            _ => Err("Invalid Primitive index"),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Modifier {
    Raw       = 0, Atomic    = 1, Persist   = 2, Ephemeral = 3, Async     = 4,
    Sync      = 5, Quantized = 6, Mapped    = 7, Wrapped   = 8, Locked    = 9,
}

impl TryFrom<u8> for Modifier {
    type Error = &'static str;
    fn try_from(v: u8) -> Result<Self, Self::Error> {
        match v {
            0 => Ok(Modifier::Raw),       1 => Ok(Modifier::Atomic),
            2 => Ok(Modifier::Persist),   3 => Ok(Modifier::Ephemeral),
            4 => Ok(Modifier::Async),     5 => Ok(Modifier::Sync),
            6 => Ok(Modifier::Quantized), 7 => Ok(Modifier::Mapped),
            8 => Ok(Modifier::Wrapped),   9 => Ok(Modifier::Locked),
            _ => Err("Invalid Modifier index"),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Target {
    Local    = 0, Network  = 1, Swarm    = 2, Ledger   = 3, Memory   = 4,
    Dispatch = 5, Ui       = 6, System   = 7, Bft      = 8, Core     = 9,
}

impl TryFrom<u8> for Target {
    type Error = &'static str;
    fn try_from(v: u8) -> Result<Self, Self::Error> {
        match v {
            0 => Ok(Target::Local),    1 => Ok(Target::Network),
            2 => Ok(Target::Swarm),    3 => Ok(Target::Ledger),
            4 => Ok(Target::Memory),   5 => Ok(Target::Dispatch),
            6 => Ok(Target::Ui),       7 => Ok(Target::System),
            8 => Ok(Target::Bft),      9 => Ok(Target::Core),
            _ => Err("Invalid Target index"),
        }
    }
}


#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct VectorPath {
    pub domain:    Domain,
    pub primitive: Primitive,
    pub modifier:  Modifier,
}

impl VectorPath {
    pub const fn new(domain: Domain, primitive: Primitive, modifier: Modifier) -> Self {
        Self { domain, primitive, modifier }
    }
    pub fn index(&self) -> usize {
        (self.domain as usize * 100) + (self.primitive as usize * 10) + self.modifier as usize
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct VectorPath4D {
    pub domain:    Domain,
    pub primitive: Primitive,
    pub modifier:  Modifier,
    pub target:    Target,
}

impl VectorPath4D {
    pub fn new(d: u8, p: u8, m: u8, t: u8) -> Result<Self, &'static str> {
        Ok(Self {
            domain:    Domain::try_from(d)?,
            primitive: Primitive::try_from(p)?,
            modifier:  Modifier::try_from(m)?,
            target:    Target::try_from(t)?,
        })
    }
    pub fn index(&self) -> usize {
        (self.domain as usize * 1000)
            + (self.primitive as usize * 100)
            + (self.modifier as usize * 10)
            + self.target as usize
    }
    pub fn to_3d(&self) -> VectorPath {
        VectorPath::new(self.domain, self.primitive, self.modifier)
    }
}


impl fmt::Display for VectorPath {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[{:?}][{:?}][{:?}]", self.domain, self.primitive, self.modifier)
    }
}
impl fmt::Display for VectorPath4D {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[{:?}][{:?}][{:?}][{:?}]",
            self.domain, self.primitive, self.modifier, self.target)
    }
}
impl fmt::Display for Domain    { fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { write!(f, "{:?}", self) } }
impl fmt::Display for Primitive { fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { write!(f, "{:?}", self) } }
impl fmt::Display for Modifier  { fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { write!(f, "{:?}", self) } }
impl fmt::Display for Target    { fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { write!(f, "{:?}", self) } }
