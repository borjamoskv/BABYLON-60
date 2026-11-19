//! FL-027-PD · Árbitro de procedencia vectorial con co-referencia.
//!
//! Sustituye `Attribution <= ProvenanceLevel` (escalar) por un vector de seis
//! dimensiones acreditadas de forma independiente y una relación `warranted`
//! que exige co-referencia: las dimensiones que sustentan una afirmación deben
//! pertenecer al mismo evento, o estar unidas por un enlace con evidencia propia.
//!
//! Alcance: modelo de referencia en memoria. No autentica orígenes reales; solo
//! impide que el sistema afirme más de lo que la evidencia acreditada sustenta.

#![allow(missing_docs)] // Modelo de referencia; los nombres de variante son autoexplicativos.

use std::collections::HashMap;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Dim {
    Content = 0,
    Platform = 1,
    Author = 2,
    Time = 3,
    Execution = 4,
    Custody = 5,
}

#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub enum Grade {
    Unaccredited,
    /// Declarado por el propio registro; no acreditado.
    Declared,
    Accredited,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct ProvenanceVector([Grade; 6]);

impl ProvenanceVector {
    pub const fn none() -> Self {
        Self([Grade::Unaccredited; 6])
    }
    pub fn with(mut self, d: Dim, g: Grade) -> Self {
        self.0[d as usize] = g;
        self
    }
    pub fn get(&self, d: Dim) -> Grade {
        self.0[d as usize]
    }
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum DocType {
    Transcript,
    Summary,
    Prompt,
    Export,
}

#[derive(Clone, Debug)]
pub struct Record {
    pub event_id: u64,
    pub message_id: u64,
    pub conversation_id: u64,
    pub doc_type: DocType,
    pub vector: ProvenanceVector,
}

/// Enlace entre dos eventos. Sin evidencia vale cero.
#[derive(Clone, Copy, Debug)]
pub struct Link {
    pub a: u64,
    pub b: u64,
    pub evidence: Option<u64>,
}

#[derive(Clone, PartialEq, Eq, Debug)]
pub enum Claim {
    Authorship { event: u64 },
    ObservedTime { event: u64 },
    Executed { event: u64 },
    IsTranscript { event: u64 },
    MessageInConversation { message_id: u64, conversation_id: u64 },
    /// Autoría fechada: autor de un evento y fecha de otro (o del mismo).
    DatedAuthorship { author_event: u64, time_event: u64 },
}

#[derive(Clone, PartialEq, Eq, Debug)]
pub enum Denied {
    UnknownEvent(u64),
    DimensionNotAccredited(Dim),
    WrongDocType(DocType),
    ConversationMismatch,
    NoCoReference,
}

#[derive(Default)]
pub struct Evidence {
    records: HashMap<u64, Record>,
    links: Vec<Link>,
}

impl Evidence {
    pub fn new() -> Self {
        Self::default()
    }
    pub fn add(&mut self, r: Record) {
        self.records.insert(r.event_id, r);
    }
    pub fn link(&mut self, l: Link) {
        self.links.push(l);
    }

    fn rec(&self, id: u64) -> Result<&Record, Denied> {
        self.records.get(&id).ok_or(Denied::UnknownEvent(id))
    }

    fn need(&self, id: u64, d: Dim) -> Result<(), Denied> {
        if self.rec(id)?.vector.get(d) == Grade::Accredited {
            Ok(())
        } else {
            Err(Denied::DimensionNotAccredited(d))
        }
    }

    fn co_referent(&self, x: u64, y: u64) -> bool {
        x == y
            || self
                .links
                .iter()
                .any(|l| l.evidence.is_some() && ((l.a == x && l.b == y) || (l.a == y && l.b == x)))
    }

    /// `Ok` solo si la evidencia acreditada sustenta la afirmación atómica.
    pub fn warranted(&self, c: &Claim) -> Result<(), Denied> {
        match *c {
            Claim::Authorship { event } => self.need(event, Dim::Author),
            Claim::ObservedTime { event } => self.need(event, Dim::Time),
            Claim::Executed { event } => self.need(event, Dim::Execution),
            Claim::IsTranscript { event } => {
                let t = self.rec(event)?.doc_type;
                if t == DocType::Transcript {
                    Ok(())
                } else {
                    Err(Denied::WrongDocType(t))
                }
            }
            Claim::MessageInConversation { message_id, conversation_id } => {
                let r = self
                    .records
                    .values()
                    .find(|r| r.message_id == message_id)
                    .ok_or(Denied::UnknownEvent(message_id))?;
                if r.conversation_id == conversation_id {
                    Ok(())
                } else {
                    Err(Denied::ConversationMismatch)
                }
            }
            Claim::DatedAuthorship { author_event, time_event } => {
                self.need(author_event, Dim::Author)?;
                self.need(time_event, Dim::Time)?;
                if self.co_referent(author_event, time_event) {
                    Ok(())
                } else {
                    Err(Denied::NoCoReference)
                }
            }
        }
    }
}

/// Regla promovida desde una memoria: conserva vector y puntero a la evidencia.
#[derive(Clone, Debug)]
pub struct Rule {
    pub provenance: ProvenanceVector,
    pub evidence_ptr: u64,
    pub doc_type: DocType,
}

/// Promoción operativa: gana utilidad sin ganar credibilidad.
pub fn promote(m: &Record) -> Rule {
    Rule { provenance: m.vector, evidence_ptr: m.event_id, doc_type: m.doc_type }
}

/// Descomposición mínima por conjunción (limitación conocida: no cubre toda
/// la sintaxis; PD-08 exige falsarla con más casos antes de confiar en ella).
pub fn decompose(text: &str) -> Vec<String> {
    text.split(" y ")
        .flat_map(|s| s.split(" and "))
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .collect()
}
