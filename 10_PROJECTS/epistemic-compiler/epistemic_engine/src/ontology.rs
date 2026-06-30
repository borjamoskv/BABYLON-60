use logos::Logos;

#[derive(Debug, Clone)]
pub struct RawEvidence {
    pub source: String,
}

#[derive(Debug, Clone)]
pub struct Evidence {
    pub hash: String,
    pub extractor_confidence: f64,
}

#[derive(Debug, Clone)]
pub struct Observable {
    pub provenance_hash: String, // Regla: Rechazo si no hay hash
    pub value: String,
}

#[derive(Debug, Clone)]
pub struct Derived {
    pub value: String,
}

#[derive(Debug, Clone)]
pub enum Distribution {
    Beta(f64, f64),
    Normal(f64, f64),
    ConfidenceInterval(f64, f64),
}

#[derive(Debug, Clone)]
pub struct Latent {
    pub distribution: Distribution, // Regla: Rechazo si es escalar
}

#[derive(Debug, Clone)]
pub enum Quantifier {
    Universal,
    Existential,
    Eventually,
}

#[derive(Debug, Clone)]
pub struct Invariant {
    pub quantifier: Quantifier, // Regla: Contrato ambiguo sin cuantificador
    pub formula: String,
}

#[derive(Debug, Clone)]
pub struct Hypothesis {
    pub falsifiable_prediction: String,
}

#[derive(Debug, Clone)]
pub enum Reversibility {
    High,
    Medium,
    Low,
    Irreversible,
}

#[derive(Debug, Clone)]
pub struct Intervention {
    pub expected_delta: f64,
    pub cost: f64, // Regla: Acción ciega sin coste
    pub reversibility: Reversibility,
}

/// Epistemological kinds available to the parser.
pub trait EpistemicKind {}

impl EpistemicKind for RawEvidence {}
impl EpistemicKind for Evidence {}
impl EpistemicKind for Observable {}
impl EpistemicKind for Derived {}
impl EpistemicKind for Latent {}
impl EpistemicKind for Invariant {}
impl EpistemicKind for Hypothesis {}
impl EpistemicKind for Intervention {}

#[derive(Logos, Debug, PartialEq, Clone)]
#[logos(skip r"[ \t\n\f]+")]
pub enum OntologyToken {
    #[token("Entity")]
    Entity,

    #[token("Relation")]
    Relation,

    #[token("Attribute")]
    Attribute,

    #[token("Error")]
    Error,
}
