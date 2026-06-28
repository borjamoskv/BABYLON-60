pub use epistemic_macros::epistemic;
use std::marker::PhantomData;
use std::collections::{HashMap, BinaryHeap};
use std::cmp::Ordering;

pub mod ontology;
pub use ontology::*;

/// El runtime mínimo de C5-REAL.
#[derive(Debug)]
pub struct Inference<S> {
    pub value: String,
    pub confidence: f64,
    pub _state: PhantomData<S>,
}

impl<S> Clone for Inference<S> {
    fn clone(&self) -> Self {
        Inference {
            value: self.value.clone(),
            confidence: self.confidence,
            _state: PhantomData,
        }
    }
}

/// El trait que representa un enlace (edge) en el DAG epistémico.
pub trait Transition<S> {
    type To;
    fn apply(self) -> Inference<Self::To>;
}
