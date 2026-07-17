#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Domain { SOURCE, MATRIX, PULSE, KINETIC, LOGIC, VECTOR, STORAGE, OSINT, CLOCK, COMPILER }

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Primitive { INIT, MUTATE, BIND, QUERY, STREAM, COMMIT, SYNC, HALT, FORK, JOIN }

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Modifier { RAW, ATOMIC, PERSIST, EPHEMERAL, ASYNC, SYNC, QUANTIZED, MAPPED, WRAPPED, LOCKED }

pub struct VectorPath(pub Domain, pub Primitive, pub Modifier);
