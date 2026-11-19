//! INV_C5_FLASH_DEFENSE: Validador Determinista de 5 Cortafuegos en Ring-0
//! acoplado al Árbitro Vectorial de Procedencia de 6 Dimensiones (FL-027-PD).
//!
//! Invariantes de seguridad:
//! - 0 `.unwrap()`, `.expect()`, `panic!`, `todo!`, `unimplemented!`.
//! - 0 `SystemTime` o `Instant` (relojes lógicos causales estrictos `CausalTick`).
//! - Escaneo léxico y de subcadenas en O(|S| + |T|) zero-allocation.

#![forbid(unsafe_code)]
#![allow(missing_docs)]

use std::collections::BTreeMap;

/// Marca lógica causal determinista (sustituye cualquier reloj de pared del SO).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct CausalTick(pub u64);

/// Identificador determinista de evento o invocación de herramienta.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct EventId(pub u64);

/// Identificador de conversación/sesión para anclaje de alcance (PD-02).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct ConversationId(pub u64);

/// Identificador de sujeto/autor para evitar transferencia por copia (PD-01 / PD-08).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct SubjectId(pub u64);

/// Esquemas de URI soberanos admitidos por el Cortafuegos 2.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CanonicalScheme {
    File,
    Babylon60,
    Vault,
    Sqlite,
}

/// Testigo de ejecución de herramienta previa requerido por el Cortafuegos 1 (Amnesia Asertiva).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ToolWitness {
    pub tool_call_id: u64,
    pub source_event_id: EventId,
    pub conversation_id: ConversationId,
    pub observed_at: CausalTick,
    pub territory_author: SubjectId,
    /// Solo `true` si el testigo proviene de un runner verificado en silicio (PD-05).
    pub verified_execution: bool,
}

/// Puntero de anclaje obligatorio requerido por el Cortafuegos 2 y validado por el Cortafuegos 5.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GroundingPointer<'a> {
    pub uri: &'a str,
    pub exact_quote: &'a str,
    /// Rango de bytes opcional `[start, end)` dentro del territorio para verificación O(1).
    pub expected_span: Option<(usize, usize)>,
    pub pointer_event_id: EventId,
}

/// Reclamo estructurado emitido por un modelo rápido (Cortafuegos 4: Esquema Estricto).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FlashClaim<'a> {
    pub claim_id: u64,
    pub conversation_id: ConversationId,
    pub emitting_agent: SubjectId,
    pub claimed_author: SubjectId,
    pub claim_tick: CausalTick,
    /// Si el modelo declara una marca temporal no observada por el testigo, se bloquea (PD-03).
    pub declared_unobserved_tick: Option<CausalTick>,
    /// Si el modelo intenta elevar su resumen a transcripción literal (PD-04).
    pub claims_verbatim_transcript: bool,
    /// Si el modelo afirma que una acción fue ejecutada en silicio (PD-05).
    pub claims_silicon_execution: bool,
    pub statement: &'a str,
    pub pointer: Option<GroundingPointer<'a>>,
    pub witness: Option<ToolWitness>,
}

// ============================================================================
// VECTOR DE PROCEDENCIA ORTOGONAL DE 6 DIMENSIONES (ACOPLAMIENTO FL-027-PD)
// ============================================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum ContentEpistemology {
    Unverified,
    DerivedSummary,
    GroundedAssertion,
    VerbatimSlice,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum PlatformBinding {
    Unbound,
    BoundConversation(ConversationId),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum AuthorAttribution {
    Unknown,
    AgentSynthesized { agent: SubjectId, source_author: SubjectId },
    DirectSource(SubjectId),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum TimeEpistemology {
    DeclaredUnverified,
    CausalObserved(CausalTick),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum ExecutionEpistemology {
    PromptOrStaticText,
    VerifiedSiliconExecution { tool_call_id: u64 },
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum CustodyChain {
    Broken,
    SingleEventWitnessed { event_id: EventId, witness_id: u64 },
}

/// Vector ortogonal de 6 dimensiones (Content, Platform, Author, Time, Execution, Custody).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ProvenanceVector6D {
    pub content: ContentEpistemology,
    pub platform: PlatformBinding,
    pub author: AuthorAttribution,
    pub time: TimeEpistemology,
    pub execution: ExecutionEpistemology,
    pub custody: CustodyChain,
}

/// Trait de puente sin fricción hacia los tipos internos de `src/provenance.rs`.
pub trait IntoProvenanceArbiter<T> {
    fn project_into_arbiter(&self) -> T;
}

/// Artefacto sellado por Ring-0 tras superar los 5 cortafuegos y las reglas PD-01..PD-08.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VerifiedFlashArtifact<'a> {
    pub claim_id: u64,
    pub canonical_scheme: CanonicalScheme,
    pub uri: &'a str,
    pub verified_quote: &'a str,
    pub verified_byte_span: (usize, usize),
    pub statement: &'a str,
    pub provenance_6d: ProvenanceVector6D,
}

// ============================================================================
// TAXONOMÍA DE VIOLACIONES DETERMINISTAS (SIN PÁNICOS)
// ============================================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SchemaViolationKind {
    EmptyStatement,
    StatementExceedsMaxBytes,
    EmptyUri,
    EmptyExactQuote,
    QuoteExceedsMaxBytes,
    InvalidByteSpanOrder,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProvenanceDriftKind {
    /// PD-01: Copiar contenido del territorio no transfiere la autoría al agente ni viceversa.
    Pd01CopiedContentAuthorshipTransfer,
    /// PD-02: El testigo pertenece a una conversación distinta de la del reclamo.
    Pd02CrossConversationLeak,
    /// PD-03: El reclamo intenta inyectar un tiempo declarado no observado por el testigo.
    Pd03DeclaredTimeNotObserved,
    /// PD-04: Un resumen/afirmación del agente intenta promocionarse como transcripción literal.
    Pd04SummaryPromotedToTranscript,
    /// PD-05: Un prompt o texto estático reclama ejecución en silicio sin testigo de ejecución.
    Pd05PromptImpliesExecution,
    /// PD-06: El puntero y el testigo provienen de eventos distintos (composición ilegítima).
    Pd06CrossEventFieldComposition,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FlashDefenseViolation {
    /// CORTAFUEGOS 1: Amnesia Asertiva (afirmación sin testigo de herramienta previo válido).
    Fw1AmnesiaMissingWitness,
    /// CORTAFUEGOS 1: El testigo tiene un tick causal posterior al reclamo (violación de causalidad).
    Fw1CausalFutureWitness { witness_tick: CausalTick, claim_tick: CausalTick },
    /// CORTAFUEGOS 2: Ausencia de puntero o URI fuera de esquemas soberanos / con path traversal.
    Fw2InvalidGroundingPointer,
    /// CORTAFUEGOS 3: Purga Gramatical C5 (detección de cheap talk RLHF o adverbios parásitos).
    Fw3GrammaticalSlop { lexicon_index: u16 },
    /// CORTAFUEGOS 4: Violación del contrato de esquema tipado.
    Fw4SchemaViolation(SchemaViolationKind),
    /// CORTAFUEGOS 5: El URI apuntado no existe en la instantánea del territorio.
    Fw5TerritoryNotFound,
    /// CORTAFUEGOS 5: La cita literal no coincide byte a byte con el territorio.
    Fw5SubstringFracture,
    /// FL-027-PD: Violación de co-referencia o deriva en las 6 dimensiones de procedencia.
    Fl027ProvenanceDrift(ProvenanceDriftKind),
}

// ============================================================================
// ALMACÉN DETERMINISTA DE TERRITORIO Y LÉXICO ANTI-SLOP (CORTAFUEGOS 3 y 5)
// ============================================================================

pub const MAX_STATEMENT_BYTES: usize = 4096;
pub const MAX_QUOTE_BYTES: usize = 2048;

/// Lista negra canónica de marcadores RLHF ("cheap talk") y adverbios de inflación semántica.
/// Escaneada en minúsculas ASCII sin alocaciones dinámicas.
const BANNED_CHEAP_TALK_PATTERNS: &[&[u8]] = &[
    b"ciertamente",
    b"absolutamente",
    b"por supuesto",
    b"con mucho gusto",
    b"increiblemente",
    b"fascinante",
    b"sin lugar a dudas",
    b"es importante destacar",
    b"cabe mencionar",
    b"como modelo de lenguaje",
    b"estoy encantado",
    b"indudablemente",
    b"maravilloso",
    b"extraordinariamente",
    b"definitivamente",
    b"certainly",
    b"absolutely",
    b"of course",
    b"delighted to",
    b"as an ai",
    b"undoubtedly",
    b"it is important to note",
];

/// Instantánea inmutable de territorios direccionables por URI para validación en Ring-0.
#[derive(Debug, Default, Clone)]
pub struct TerritorySnapshot {
    blobs: BTreeMap<String, Vec<u8>>,
}

impl TerritorySnapshot {
    #[inline]
    pub fn new() -> Self {
        Self {
            blobs: BTreeMap::new(),
        }
    }

    #[inline]
    pub fn insert_territory(&mut self, uri: &str, content: &[u8]) {
        self.blobs.insert(uri.to_owned(), content.to_vec());
    }

    #[inline]
    pub fn get_territory(&self, uri: &str) -> Option<&[u8]> {
        self.blobs.get(uri).map(|v| v.as_slice())
    }
}

// ============================================================================
// MOTOR DE VALIDACIÓN DETERMINISTA RING-0
// ============================================================================

/// Valida un `FlashClaim` contra los 5 Cortafuegos de `INV_C5_FLASH_DEFENSE` y construye
/// el `VerifiedFlashArtifact` con su `ProvenanceVector6D` (`FL-027-PD`).
pub fn validate_flash_claim<'a>(
    claim: &'a FlashClaim<'a>,
    territories: &TerritorySnapshot,
) -> Result<VerifiedFlashArtifact<'a>, FlashDefenseViolation> {
    // ------------------------------------------------------------------------
    // CORTAFUEGOS 4: ESQUEMAS ESTRICTOS DE SALIDA (O(1))
    // ------------------------------------------------------------------------
    let stmt_bytes = claim.statement.as_bytes();
    if stmt_bytes.is_empty() {
        return Err(FlashDefenseViolation::Fw4SchemaViolation(
            SchemaViolationKind::EmptyStatement,
        ));
    }
    if stmt_bytes.len() > MAX_STATEMENT_BYTES {
        return Err(FlashDefenseViolation::Fw4SchemaViolation(
            SchemaViolationKind::StatementExceedsMaxBytes,
        ));
    }

    // ------------------------------------------------------------------------
    // CORTAFUEGOS 1: AMNESIA ASERTIVA (Testigo de herramienta obligatorio)
    // ------------------------------------------------------------------------
    let witness = match claim.witness {
        Some(w) if w.tool_call_id != 0 => w,
        _ => return Err(FlashDefenseViolation::Fw1AmnesiaMissingWitness),
    };

    if witness.observed_at > claim.claim_tick {
        return Err(FlashDefenseViolation::Fw1CausalFutureWitness {
            witness_tick: witness.observed_at,
            claim_tick: claim.claim_tick,
        });
    }

    // ------------------------------------------------------------------------
    // CORTAFUEGOS 2: GROUNDING OBLIGATORIO POR PUNTEROS
    // ------------------------------------------------------------------------
    let pointer = match &claim.pointer {
        Some(p) => p,
        None => return Err(FlashDefenseViolation::Fw2InvalidGroundingPointer),
    };

    if pointer.uri.is_empty() {
        return Err(FlashDefenseViolation::Fw4SchemaViolation(
            SchemaViolationKind::EmptyUri,
        ));
    }
    let quote_bytes = pointer.exact_quote.as_bytes();
    if quote_bytes.is_empty() {
        return Err(FlashDefenseViolation::Fw4SchemaViolation(
            SchemaViolationKind::EmptyExactQuote,
        ));
    }
    if quote_bytes.len() > MAX_QUOTE_BYTES {
        return Err(FlashDefenseViolation::Fw4SchemaViolation(
            SchemaViolationKind::QuoteExceedsMaxBytes,
        ));
    }

    let canonical_scheme = parse_canonical_uri_scheme(pointer.uri)
        .ok_or(FlashDefenseViolation::Fw2InvalidGroundingPointer)?;

    if let Some((start, end)) = pointer.expected_span {
        if start >= end {
            return Err(FlashDefenseViolation::Fw4SchemaViolation(
                SchemaViolationKind::InvalidByteSpanOrder,
            ));
        }
        let span_len = match end.checked_sub(start) {
            Some(len) => len,
            None => {
                return Err(FlashDefenseViolation::Fw4SchemaViolation(
                    SchemaViolationKind::InvalidByteSpanOrder,
                ))
            }
        };
        if span_len != quote_bytes.len() {
            return Err(FlashDefenseViolation::Fw5SubstringFracture);
        }
    }

    // ------------------------------------------------------------------------
    // CORTAFUEGOS 3: PURGA GRAMATICAL C5 (Escaneo O(|S|) zero-allocation)
    // ------------------------------------------------------------------------
    if let Some(idx) = detect_grammatical_slop(stmt_bytes) {
        return Err(FlashDefenseViolation::Fw3GrammaticalSlop {
            lexicon_index: idx,
        });
    }

    // ------------------------------------------------------------------------
    // CORTAFUEGOS 5: VALIDADOR DETERMINISTA DE SUBCADENA EN TERRITORIO
    // ------------------------------------------------------------------------
    let territory_bytes = territories
        .get_territory(pointer.uri)
        .ok_or(FlashDefenseViolation::Fw5TerritoryNotFound)?;

    let verified_byte_span = match pointer.expected_span {
        Some((start, end)) => {
            let slice = territory_bytes
                .get(start..end)
                .ok_or(FlashDefenseViolation::Fw5SubstringFracture)?;
            if slice != quote_bytes {
                return Err(FlashDefenseViolation::Fw5SubstringFracture);
            }
            (start, end)
        }
        None => find_exact_subslice(territory_bytes, quote_bytes)
            .ok_or(FlashDefenseViolation::Fw5SubstringFracture)?,
    };

    // ------------------------------------------------------------------------
    // INTEGRACIÓN CON ÁRBITRO VECTORIAL 6D (FL-027-PD: PD-01 a PD-08)
    // ------------------------------------------------------------------------
    // PD-06: Los campos de eventos distintos (testigo vs puntero) no pueden componerse.
    if witness.source_event_id != pointer.pointer_event_id {
        return Err(FlashDefenseViolation::Fl027ProvenanceDrift(
            ProvenanceDriftKind::Pd06CrossEventFieldComposition,
        ));
    }

    // PD-02: El mensaje/testigo debe estar vinculado a la misma conversación.
    if witness.conversation_id != claim.conversation_id {
        return Err(FlashDefenseViolation::Fl027ProvenanceDrift(
            ProvenanceDriftKind::Pd02CrossConversationLeak,
        ));
    }

    // PD-01: Copiar contenido del territorio no transfiere la autoría al agente emisor.
    if claim.claimed_author != claim.emitting_agent {
        return Err(FlashDefenseViolation::Fl027ProvenanceDrift(
            ProvenanceDriftKind::Pd01CopiedContentAuthorshipTransfer,
        ));
    }

    // PD-03: El tiempo declarado no puede sustituir al tiempo observado por el testigo.
    if let Some(declared_tick) = claim.declared_unobserved_tick {
        if declared_tick != witness.observed_at {
            return Err(FlashDefenseViolation::Fl027ProvenanceDrift(
                ProvenanceDriftKind::Pd03DeclaredTimeNotObserved,
            ));
        }
    }

    // PD-04: Una síntesis/afirmación del agente no puede promocionarse a transcripción literal
    // salvo que el statement completo sea byte a byte idéntico a la cita verificada.
    let is_exact_transcript = stmt_bytes == quote_bytes;
    if claim.claims_verbatim_transcript && !is_exact_transcript {
        return Err(FlashDefenseViolation::Fl027ProvenanceDrift(
            ProvenanceDriftKind::Pd04SummaryPromotedToTranscript,
        ));
    }

    // PD-05: Un prompt o archivo estático no implica ejecución en silicio.
    if claim.claims_silicon_execution && !witness.verified_execution {
        return Err(FlashDefenseViolation::Fl027ProvenanceDrift(
            ProvenanceDriftKind::Pd05PromptImpliesExecution,
        ));
    }

    let provenance_6d = ProvenanceVector6D {
        content: if is_exact_transcript {
            ContentEpistemology::VerbatimSlice
        } else {
            ContentEpistemology::GroundedAssertion
        },
        platform: PlatformBinding::BoundConversation(claim.conversation_id),
        author: AuthorAttribution::AgentSynthesized {
            agent: claim.emitting_agent,
            source_author: witness.territory_author,
        },
        time: TimeEpistemology::CausalObserved(witness.observed_at),
        execution: if witness.verified_execution {
            ExecutionEpistemology::VerifiedSiliconExecution {
                tool_call_id: witness.tool_call_id,
            }
        } else {
            ExecutionEpistemology::PromptOrStaticText
        },
        custody: CustodyChain::SingleEventWitnessed {
            event_id: witness.source_event_id,
            witness_id: witness.tool_call_id,
        },
    };

    Ok(VerifiedFlashArtifact {
        claim_id: claim.claim_id,
        canonical_scheme,
        uri: pointer.uri,
        verified_quote: pointer.exact_quote,
        verified_byte_span,
        statement: claim.statement,
        provenance_6d,
    })
}

// ============================================================================
// PUENTE HACIA SRC/PROVENANCE.RS (INTO_PROVENANCE_ARBITER)
// ============================================================================

impl<'a> IntoProvenanceArbiter<crate::provenance::Record> for VerifiedFlashArtifact<'a> {
    fn project_into_arbiter(&self) -> crate::provenance::Record {
        let event_id = match self.provenance_6d.custody {
            CustodyChain::SingleEventWitnessed { event_id, .. } => event_id.0,
            CustodyChain::Broken => 0,
        };
        let conversation_id = match self.provenance_6d.platform {
            PlatformBinding::BoundConversation(cid) => cid.0,
            PlatformBinding::Unbound => 0,
        };
        let doc_type = match self.provenance_6d.content {
            ContentEpistemology::VerbatimSlice => crate::provenance::DocType::Transcript,
            ContentEpistemology::GroundedAssertion => crate::provenance::DocType::Summary,
            ContentEpistemology::DerivedSummary => crate::provenance::DocType::Summary,
            ContentEpistemology::Unverified => crate::provenance::DocType::Prompt,
        };
        crate::provenance::Record {
            event_id,
            message_id: self.claim_id,
            conversation_id,
            doc_type,
            vector: self.provenance_6d.project_into_arbiter(),
        }
    }
}

impl IntoProvenanceArbiter<crate::provenance::ProvenanceVector> for ProvenanceVector6D {
    fn project_into_arbiter(&self) -> crate::provenance::ProvenanceVector {
        use crate::provenance::{Dim, Grade, ProvenanceVector};
        let mut pv = ProvenanceVector::none();

        let content_grade = match self.content {
            ContentEpistemology::VerbatimSlice | ContentEpistemology::GroundedAssertion => {
                Grade::Accredited
            }
            ContentEpistemology::DerivedSummary => Grade::Declared,
            ContentEpistemology::Unverified => Grade::Unaccredited,
        };
        pv = pv.with(Dim::Content, content_grade);

        let platform_grade = match self.platform {
            PlatformBinding::BoundConversation(_) => Grade::Accredited,
            PlatformBinding::Unbound => Grade::Unaccredited,
        };
        pv = pv.with(Dim::Platform, platform_grade);

        let author_grade = match self.author {
            AuthorAttribution::DirectSource(_) | AuthorAttribution::AgentSynthesized { .. } => {
                Grade::Accredited
            }
            AuthorAttribution::Unknown => Grade::Unaccredited,
        };
        pv = pv.with(Dim::Author, author_grade);

        let time_grade = match self.time {
            TimeEpistemology::CausalObserved(_) => Grade::Accredited,
            TimeEpistemology::DeclaredUnverified => Grade::Declared,
        };
        pv = pv.with(Dim::Time, time_grade);

        let exec_grade = match self.execution {
            ExecutionEpistemology::VerifiedSiliconExecution { .. } => Grade::Accredited,
            ExecutionEpistemology::PromptOrStaticText => Grade::Declared,
        };
        pv = pv.with(Dim::Execution, exec_grade);

        let custody_grade = match self.custody {
            CustodyChain::SingleEventWitnessed { .. } => Grade::Accredited,
            CustodyChain::Broken => Grade::Unaccredited,
        };
        pv = pv.with(Dim::Custody, custody_grade);

        pv
    }
}

/// Verifica que el URI pertenezca a un esquema soberano y carezca de path traversal (`..`).
#[inline]
fn parse_canonical_uri_scheme(uri: &str) -> Option<CanonicalScheme> {
    if uri.contains("..") || uri.bytes().any(|b| b.is_ascii_control()) {
        return None;
    }
    let (scheme, rest) = if let Some(r) = uri.strip_prefix("file://") {
        (CanonicalScheme::File, r)
    } else if let Some(r) = uri.strip_prefix("b60://") {
        (CanonicalScheme::Babylon60, r)
    } else if let Some(r) = uri.strip_prefix("vault://") {
        (CanonicalScheme::Vault, r)
    } else {
        let r = uri.strip_prefix("sqlite://")?;
        (CanonicalScheme::Sqlite, r)
    };

    if rest.is_empty() {
        return None;
    }
    Some(scheme)
}

/// Búsqueda determinista de subcadena exacta en O(|H| * |N|) acotado y zero-allocation.
#[inline]
fn find_exact_subslice(haystack: &[u8], needle: &[u8]) -> Option<(usize, usize)> {
    if needle.is_empty() || needle.len() > haystack.len() {
        return None;
    }
    let first = *needle.first()?;
    let max_start = haystack.len().checked_sub(needle.len())?;

    let mut idx = 0usize;
    while idx <= max_start {
        if let Some(&b) = haystack.get(idx) {
            if b == first {
                let end = idx.checked_add(needle.len())?;
                if let Some(window) = haystack.get(idx..end) {
                    if window == needle {
                        return Some((idx, end));
                    }
                }
            }
        }
        idx = idx.saturating_add(1);
    }
    None
}

/// Escáner léxico insensible a mayúsculas ASCII con respeto de fronteras de palabra.
#[inline]
fn detect_grammatical_slop(statement: &[u8]) -> Option<u16> {
    for (pattern_idx, &pattern) in BANNED_CHEAP_TALK_PATTERNS.iter().enumerate() {
        if contains_ascii_case_insensitive_word(statement, pattern) {
            return Some(pattern_idx as u16);
        }
    }
    None
}

#[inline]
fn is_word_byte(b: u8) -> bool {
    b.is_ascii_alphanumeric() || b == b'_'
}

#[inline]
fn contains_ascii_case_insensitive_word(haystack: &[u8], needle_lower: &[u8]) -> bool {
    if needle_lower.is_empty() || needle_lower.len() > haystack.len() {
        return false;
    }
    let max_start = match haystack.len().checked_sub(needle_lower.len()) {
        Some(m) => m,
        None => return false,
    };

    let mut start = 0usize;
    while start <= max_start {
        let mut matched = true;
        let mut offset = 0usize;
        while offset < needle_lower.len() {
            let h_byte = match haystack.get(start.saturating_add(offset)) {
                Some(&b) => b.to_ascii_lowercase(),
                None => {
                    matched = false;
                    break;
                }
            };
            let n_byte = match needle_lower.get(offset) {
                Some(&b) => b,
                None => {
                    matched = false;
                    break;
                }
            };
            if h_byte != n_byte {
                matched = false;
                break;
            }
            offset = offset.saturating_add(1);
        }

        if matched {
            let prev_is_word = if start == 0 {
                false
            } else {
                match haystack.get(start.saturating_sub(1)) {
                    Some(&b) => is_word_byte(b),
                    None => false,
                }
            };
            let end = start.saturating_add(needle_lower.len());
            let next_is_word = match haystack.get(end) {
                Some(&b) => is_word_byte(b),
                None => false,
            };

            if !prev_is_word && !next_is_word {
                return true;
            }
        }
        start = start.saturating_add(1);
    }
    false
}
