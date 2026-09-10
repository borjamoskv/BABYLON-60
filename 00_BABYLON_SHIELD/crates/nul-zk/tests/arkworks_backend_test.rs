use ark_bls12_381::{Bls12_381, Fr as BlsFr};
use ark_groth16::Groth16;
use ark_snark::{CircuitSpecificSetupSNARK, SNARK};
use rand::thread_rng;
use nul_zk::compile_nul_source;
use ark_relations::r1cs::{ConstraintSynthesizer, ConstraintSystemRef, SynthesisError, Variable, LinearCombination};
use ark_ff::Field;

// Para testear dinámicamente sin generar el string de Rust y compilarlo on-the-fly 
// (lo cual es complejo en un test normal `cargo test`), idealmente deberíamos evaluar
// la estructura de las puertas de manera simbólica o usar un intérprete.
// Dado que la transpiliación de Arkworks genera código Rust estático (string), 
// el approach de test de integración se maneja mejor desde un paso de compilación build.rs.
