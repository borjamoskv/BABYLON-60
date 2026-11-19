//! NEMESIS WAVE 7 · FL-027-PD PROVENANCE DRIFT.
//!
//! Falsadores PD-01..PD-08 contra `babylon60::provenance` (árbitro vectorial con
//! co-referencia). Datos sintéticos, independientes de contenido privado.
//! Incluye controles positivos para evitar tests vacuos.
//!
//! Limitación: estos tests acreditan que el modelo de referencia no sobreatribuye
//! en estos vectores. No demuestran tasa de fallo cero ni cubren corpus adversarial
//! correlacionado; reportar cobertura de vectores y tasa observada por separado.
use babylon60::provenance::{
    decompose, promote, Claim, Denied, Dim, DocType, Evidence, Grade, Link, ProvenanceVector, Record,
};

fn rec(id: u64, conv: u64, t: DocType, v: ProvenanceVector) -> Record {
    Record { event_id: id, message_id: id * 10, conversation_id: conv, doc_type: t, vector: v }
}

fn hashed_only() -> ProvenanceVector {
    ProvenanceVector::none().with(Dim::Content, Grade::Accredited)
}

/// PD-01: contenido íntegro de otro autor no transfiere autoría.
#[test]
fn pd01_copied_content_must_not_transfer_authorship() {
    let mut e = Evidence::new();
    e.add(rec(1, 1, DocType::Export, hashed_only()));
    assert_eq!(
        e.warranted(&Claim::Authorship { event: 1 }),
        Err(Denied::DimensionNotAccredited(Dim::Author))
    );
    // Control positivo.
    e.add(rec(2, 1, DocType::Export, hashed_only().with(Dim::Author, Grade::Accredited)));
    assert!(e.warranted(&Claim::Authorship { event: 2 }).is_ok());
}

/// PD-02: message_id válido en otra conversación no autentica la citada.
#[test]
fn pd02_message_id_must_bind_to_conversation() {
    let mut e = Evidence::new();
    e.add(rec(1, 1, DocType::Export, hashed_only()));
    let mid = 10;
    assert_eq!(
        e.warranted(&Claim::MessageInConversation { message_id: mid, conversation_id: 2 }),
        Err(Denied::ConversationMismatch)
    );
    assert!(e.warranted(&Claim::MessageInConversation { message_id: mid, conversation_id: 1 }).is_ok());
}

/// PD-03: reloj declarado no es reloj observado.
#[test]
fn pd03_declared_time_must_not_be_observed() {
    let mut e = Evidence::new();
    e.add(rec(1, 1, DocType::Export, hashed_only().with(Dim::Time, Grade::Declared)));
    assert_eq!(
        e.warranted(&Claim::ObservedTime { event: 1 }),
        Err(Denied::DimensionNotAccredited(Dim::Time))
    );
}

/// PD-04: un resumen conserva su tipo documental.
#[test]
fn pd04_summary_must_not_become_transcript() {
    let mut e = Evidence::new();
    e.add(rec(1, 1, DocType::Summary, hashed_only()));
    assert_eq!(
        e.warranted(&Claim::IsTranscript { event: 1 }),
        Err(Denied::WrongDocType(DocType::Summary))
    );
    e.add(rec(2, 1, DocType::Transcript, hashed_only()));
    assert!(e.warranted(&Claim::IsTranscript { event: 2 }).is_ok());
}

/// PD-05: un prompt íntegro no acredita ejecución.
#[test]
fn pd05_prompt_must_not_imply_execution() {
    let mut e = Evidence::new();
    e.add(rec(1, 1, DocType::Prompt, hashed_only()));
    assert_eq!(
        e.warranted(&Claim::Executed { event: 1 }),
        Err(Denied::DimensionNotAccredited(Dim::Execution))
    );
}

/// PD-06: autor de A + fecha de B no compone «autoría fechada» sin enlace con evidencia.
#[test]
fn pd06_fields_from_distinct_events_must_not_compose() {
    let mut e = Evidence::new();
    e.add(rec(1, 1, DocType::Export, hashed_only().with(Dim::Author, Grade::Accredited)));
    e.add(rec(2, 1, DocType::Export, hashed_only().with(Dim::Time, Grade::Accredited)));
    let c = Claim::DatedAuthorship { author_event: 1, time_event: 2 };
    assert_eq!(e.warranted(&c), Err(Denied::NoCoReference));
    // Un enlace SIN evidencia sigue valiendo cero.
    e.link(Link { a: 1, b: 2, evidence: None });
    assert_eq!(e.warranted(&c), Err(Denied::NoCoReference));
    // Control positivo: enlace con evidencia propia.
    e.link(Link { a: 1, b: 2, evidence: Some(99) });
    assert!(e.warranted(&c).is_ok());
}

/// PD-07: la promoción a regla conserva el vector y el puntero a la evidencia.
#[test]
fn pd07_promotion_must_preserve_provenance() {
    let m = rec(7, 1, DocType::Summary, hashed_only().with(Dim::Time, Grade::Declared));
    let rule = promote(&m);
    assert_eq!(rule.provenance, m.vector);
    assert_eq!(rule.evidence_ptr, m.event_id);
    assert_eq!(rule.doc_type, DocType::Summary);
}

/// PD-08: la descomposición no funde sujetos distintos en un átomo.
#[test]
fn pd08_decomposition_must_not_merge_subjects() {
    let atoms = decompose("Alice escribió el texto y Bob lo ejecutó");
    assert_eq!(atoms.len(), 2, "{atoms:?}");
}

/// Metamórfica: quitar evidencia no puede aumentar la atribución.
#[test]
fn meta_evidence_removed_never_increases_attribution() {
    let full = ProvenanceVector::none().with(Dim::Author, Grade::Accredited);
    let mut with = Evidence::new();
    with.add(rec(1, 1, DocType::Export, full));
    let without = Evidence::new();
    let c = Claim::Authorship { event: 1 };
    assert!(with.warranted(&c).is_ok());
    assert!(without.warranted(&c).is_err());
}
