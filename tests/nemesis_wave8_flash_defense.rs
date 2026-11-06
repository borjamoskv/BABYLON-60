//! NEMESIS Wave 8: Verificación en silicio de INV_C5_FLASH_DEFENSE (1.000 sondas)
//! + acoplamiento ortogonal con FL-027-PD (Provenance 6D).

use std::time::Instant;

use babylon60::flash_defense::{
    validate_flash_claim, AuthorAttribution, CausalTick, ContentEpistemology, ConversationId,
    CustodyChain, EventId, ExecutionEpistemology, FlashClaim, FlashDefenseViolation,
    GroundingPointer, IntoProvenanceArbiter, ProvenanceDriftKind, SubjectId, TerritorySnapshot,
    TimeEpistemology, ToolWitness,
};
use babylon60::provenance::{Dim, DocType, Grade, Record};

fn build_fixture_territory() -> TerritorySnapshot {
    let mut snapshot = TerritorySnapshot::new();
    snapshot.insert_territory(
        "vault://babylon60/state/odb_telemetry.txt",
        b"in-pack: 18867 objects; size-pack: 45.21 MiB; status: canonical_omega",
    );
    snapshot.insert_territory(
        "file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/src/provenance.rs",
        b"pub mod provenance; // 6D orthogonal vector arbiter FL-027-PD",
    );
    snapshot
}

fn valid_baseline_claim<'a>() -> FlashClaim<'a> {
    FlashClaim {
        claim_id: 1,
        conversation_id: ConversationId(42),
        emitting_agent: SubjectId(7),
        claimed_author: SubjectId(7),
        claim_tick: CausalTick(100),
        declared_unobserved_tick: None,
        claims_verbatim_transcript: false,
        claims_silicon_execution: false,
        statement: "El packfile registra 18867 objetos en estado canonical_omega.",
        pointer: Some(GroundingPointer {
            uri: "vault://babylon60/state/odb_telemetry.txt",
            exact_quote: "in-pack: 18867 objects; size-pack: 45.21 MiB",
            expected_span: Some((0, 44)),
            pointer_event_id: EventId(9001),
        }),
        witness: Some(ToolWitness {
            tool_call_id: 501,
            source_event_id: EventId(9001),
            conversation_id: ConversationId(42),
            observed_at: CausalTick(99),
            territory_author: SubjectId(1),
            verified_execution: false,
        }),
    }
}

#[test]
fn omega_1000_adversarial_probes_and_controls_in_silicon() {
    let territories = build_fixture_territory();
    let mut intercepted_slop = 0usize;
    let mut admitted_controls = 0usize;

    let t0 = Instant::now();

    // 1. 200 sondas: Cortafuegos 1 y 2 (Amnesia asertiva / sin testigo o sin puntero)
    for i in 0..200u64 {
        let mut claim = valid_baseline_claim();
        claim.claim_id = 1000 + i;
        if i % 2 == 0 {
            claim.witness = None;
            assert_eq!(
                validate_flash_claim(&claim, &territories),
                Err(FlashDefenseViolation::Fw1AmnesiaMissingWitness)
            );
        } else {
            claim.pointer = None;
            assert_eq!(
                validate_flash_claim(&claim, &territories),
                Err(FlashDefenseViolation::Fw2InvalidGroundingPointer)
            );
        }
        intercepted_slop += 1;
    }

    // 2. 200 sondas: Cortafuegos 3 (Purga gramatical C5 / cheap talk RLHF)
    for i in 0..200u64 {
        let mut claim = valid_baseline_claim();
        claim.claim_id = 2000 + i;
        claim.statement =
            "Ciertamente el packfile registra 18867 objetos de forma fascinante.";
        assert!(matches!(
            validate_flash_claim(&claim, &territories),
            Err(FlashDefenseViolation::Fw3GrammaticalSlop { .. })
        ));
        intercepted_slop += 1;
    }

    // 3. 200 sondas: Cortafuegos 5A (Fractura de substring literal)
    for i in 0..200u64 {
        let mut claim = valid_baseline_claim();
        claim.claim_id = 3000 + i;
        if let Some(ref mut ptr) = claim.pointer {
            ptr.exact_quote = "in-pack: 99999 objects; size-pack: 0.00 MiB";
            ptr.expected_span = None;
        }
        assert_eq!(
            validate_flash_claim(&claim, &territories),
            Err(FlashDefenseViolation::Fw5SubstringFracture)
        );
        intercepted_slop += 1;
    }

    // 4. 200 sondas: Cortafuegos 5B (Territorio inexistente / URI alucinado)
    for i in 0..200u64 {
        let mut claim = valid_baseline_claim();
        claim.claim_id = 4000 + i;
        if let Some(ref mut ptr) = claim.pointer {
            ptr.uri = "vault://babylon60/state/hallucinated_file.txt";
        }
        assert_eq!(
            validate_flash_claim(&claim, &territories),
            Err(FlashDefenseViolation::Fw5TerritoryNotFound)
        );
        intercepted_slop += 1;
    }

    // 5. 200 sondas: Controles legítimos verificados en las 6 dimensiones
    for i in 0..200u64 {
        let mut claim = valid_baseline_claim();
        claim.claim_id = 5000 + i;
        let res = validate_flash_claim(&claim, &territories);
        assert!(res.is_ok());
        if let Ok(artifact) = res {
            assert_eq!(
                artifact.provenance_6d.content,
                ContentEpistemology::GroundedAssertion
            );
            assert_eq!(
                artifact.provenance_6d.author,
                AuthorAttribution::AgentSynthesized {
                    agent: SubjectId(7),
                    source_author: SubjectId(1),
                }
            );
            assert_eq!(
                artifact.provenance_6d.time,
                TimeEpistemology::CausalObserved(CausalTick(99))
            );
            assert_eq!(
                artifact.provenance_6d.execution,
                ExecutionEpistemology::PromptOrStaticText
            );
            assert_eq!(
                artifact.provenance_6d.custody,
                CustodyChain::SingleEventWitnessed {
                    event_id: EventId(9001),
                    witness_id: 501,
                }
            );
            admitted_controls += 1;
        }
    }

    let elapsed = t0.elapsed();
    let total_us = elapsed.as_micros();
    let avg_ns = elapsed.as_nanos() / 1000;
    println!(
        "\n[RUST SILICON BENCHMARK] 1.000 sondas ejecutadas en {:?} (~{} µs total, ~{} ns/sonda)",
        elapsed, total_us, avg_ns
    );

    assert_eq!(intercepted_slop, 800);
    assert_eq!(admitted_controls, 200);
}

#[test]
fn fl027_pd_coupling_prevents_provenance_escalation_after_flash_gate() {
    let territories = build_fixture_territory();

    // PD-01: El agente no puede apropiarse de la autoría del territorio ni atribuir su frase al autor original
    let mut pd01 = valid_baseline_claim();
    pd01.claimed_author = SubjectId(1);
    assert_eq!(
        validate_flash_claim(&pd01, &territories),
        Err(FlashDefenseViolation::Fl027ProvenanceDrift(
            ProvenanceDriftKind::Pd01CopiedContentAuthorshipTransfer
        ))
    );

    // PD-03: Tiempo declarado distinto del observado por el testigo es rechazado
    let mut pd03 = valid_baseline_claim();
    pd03.declared_unobserved_tick = Some(CausalTick(50));
    assert_eq!(
        validate_flash_claim(&pd03, &territories),
        Err(FlashDefenseViolation::Fl027ProvenanceDrift(
            ProvenanceDriftKind::Pd03DeclaredTimeNotObserved
        ))
    );

    // PD-04: Una afirmación derivada no puede promocionarse a transcripción literal
    let mut pd04 = valid_baseline_claim();
    pd04.claims_verbatim_transcript = true;
    assert_eq!(
        validate_flash_claim(&pd04, &territories),
        Err(FlashDefenseViolation::Fl027ProvenanceDrift(
            ProvenanceDriftKind::Pd04SummaryPromotedToTranscript
        ))
    );

    // PD-05: Citar un archivo no implica ejecución en silicio si el testigo no es de ejecución
    let mut pd05 = valid_baseline_claim();
    pd05.claims_silicon_execution = true;
    assert_eq!(
        validate_flash_claim(&pd05, &territories),
        Err(FlashDefenseViolation::Fl027ProvenanceDrift(
            ProvenanceDriftKind::Pd05PromptImpliesExecution
        ))
    );

    // PD-06: Composición de testigo y puntero procedentes de eventos distintos es bloqueada
    let mut pd06 = valid_baseline_claim();
    if let Some(ref mut ptr) = pd06.pointer {
        ptr.pointer_event_id = EventId(9999);
    }
    assert_eq!(
        validate_flash_claim(&pd06, &territories),
        Err(FlashDefenseViolation::Fl027ProvenanceDrift(
            ProvenanceDriftKind::Pd06CrossEventFieldComposition
        ))
    );

    // Verificación de IntoProvenanceArbiter proyectando hacia src/provenance.rs
    let claim = valid_baseline_claim();
    let artifact = validate_flash_claim(&claim, &territories).expect("claim base debe ser válido");
    let record: Record = artifact.project_into_arbiter();

    assert_eq!(record.event_id, 9001);
    assert_eq!(record.message_id, 1);
    assert_eq!(record.conversation_id, 42);
    assert_eq!(record.doc_type, DocType::Summary);
    assert_eq!(record.vector.get(Dim::Content), Grade::Accredited);
    assert_eq!(record.vector.get(Dim::Platform), Grade::Accredited);
    assert_eq!(record.vector.get(Dim::Author), Grade::Accredited);
    assert_eq!(record.vector.get(Dim::Time), Grade::Accredited);
    assert_eq!(record.vector.get(Dim::Execution), Grade::Declared); // StaticArtifact / Prompt
    assert_eq!(record.vector.get(Dim::Custody), Grade::Accredited);
}
