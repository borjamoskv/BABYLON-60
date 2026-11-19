// ============================================================================
// B60: SOVEREIGN BASE-60 PROGRAMMING LANGUAGE ENGINE
// Framework: C5-REAL | Substrate: BABYLON-60 / Teorema Robinson-Moskv
// ============================================================================

pub mod arithmetic;
pub mod isa;
pub mod reversible;
pub mod homotopy;
pub mod vm;
pub mod compiler;
pub mod mmr;
pub mod fisher;
pub mod transducer;
pub mod ffi;
pub mod repl;
pub mod dag;
pub mod lean_emitter;
mod bytecode_proof;
pub mod epistemic_types;
pub mod verified_plan;
pub mod consumer_gate;

pub use arithmetic::{Tick60, FRACTION_BASE};
pub use isa::SexaOpCode;
pub use reversible::{ReversibleRegister, SexaToffoliGate};
pub use homotopy::{HomotopyVerifier, HomotopyResult};
pub use vm::{F60VM, SexaRegister, SovereignManifest64};
pub use compiler::B60Compiler;
pub use mmr::{MmrAccumulator, MmrInclusionProof};
pub use fisher::FisherSimplex;
pub use transducer::{AgentActionIntent, EpistemicEvaluation, EpistemicGate};
pub use repl::B60Repl;
pub use dag::{CausalDag, CausalNode, CompiledCausalPlan, CausalParadoxError};
pub use lean_emitter::Lean4Emitter;
pub use epistemic_types::{Claim, Origin, Observed, EvidenceWitness, Verified, LinearCap, EpistemicError};
pub use verified_plan::{EvidenceLevel, CapabilityDescriptor, EvidenceRequirement, Operation, PlanError, VerifiedPlan, PlanBuilder};
pub use consumer_gate::{PlanConsumerGate, PlanGateError, PlanDispatchStatus, PlanExecutionReceipt};

