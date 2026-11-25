//! # NEMESIS v2: Suite de Tortura Adversarial y Consenso LARSA
//!
//! Verifica empíricamente las invariantes de safety y resiliencia bizantina:
//! 1. `test_larsa_pure_happy_path`: Consenso unánime de quórum honesto 3/3.
//! 2. `test_adversarial_equivocation_eviction`: Evicción inmediata en O(1) de nodo bizantino equívoco.
//! 3. `test_adversarial_network_split_brain_prevention`: Resiliencia ante partición de red 2 vs 1.
//! 4. `test_adversarial_formal_veto_terminal`: Veto terminal irreversible de Lean 4 / Prover.
//! 5. `test_causal_replay_and_delta_debugging`: Minimizador de traza de contraejemplo.

use std::collections::BTreeMap;
use babylon60::larsa::VoteKind;
use babylon60::larsa_pure::{
    step, DeclarativeEffect, EpochStatus, LarsaPureState, LogicalEvent, NodeStatus,
};
use babylon60::nemesis_v2::faults::{AdversarialFault, FaultPlan, PartitionMatrix};
use babylon60::nemesis_v2::oracles::NemesisOracles;
use babylon60::nemesis_v2::replay::{CausalEvidenceBundle, DeltaDebugger};
use babylon60::nemesis_v2::NemesisScheduler;

fn create_3node_quorum() -> (LarsaPureState, PartitionMatrix) {
    let mut nodes = BTreeMap::new();
    nodes.insert(1, 10);
    nodes.insert(2, 10);
    nodes.insert(3, 10);

    let state = LarsaPureState::new(nodes, 20); // 20 de 30 requeridos (2/3 de peso)
    let topology = PartitionMatrix::fully_connected(&[1, 2, 3]);
    (state, topology)
}

#[test]
fn test_larsa_pure_happy_path() {
    let (state, topology) = create_3node_quorum();
    let mut scheduler = NemesisScheduler::new(state, topology, FaultPlan::new());

    let trace_hash = [0x42u8; 32];

    // Iniciar época 1
    scheduler.schedule_event(1, None, LogicalEvent::StartEpoch { epoch: 1 });

    // Voto nodo 1: Testigo formal verificado
    scheduler.schedule_event(
        2,
        None,
        LogicalEvent::VoteReceived {
            epoch: 1,
            view: 0,
            voter: 1,
            kind: VoteKind::FormalWitnessVerified { trace_hash },
        },
    );

    // Voto nodo 2: Aprobación heurística peso 10
    scheduler.schedule_event(
        3,
        None,
        LogicalEvent::VoteReceived {
            epoch: 1,
            view: 0,
            voter: 2,
            kind: VoteKind::HeuristicApprove { weight: 10 },
        },
    );

    // Voto nodo 3: Aprobación heurística peso 10 (alcanza 20 de peso requerido)
    scheduler.schedule_event(
        4,
        None,
        LogicalEvent::VoteReceived {
            epoch: 1,
            view: 0,
            voter: 3,
            kind: VoteKind::HeuristicApprove { weight: 10 },
        },
    );

    let executed = scheduler.run_until_quiescence(100).expect("Quiescencia sin violación");
    assert_eq!(executed, 4);

    // Verificar que la época 1 quedó en Committed
    match scheduler.state.epoch_statuses.get(&1) {
        Some(EpochStatus::Committed { trace_hash: h, heuristic_weight }) => {
            assert_eq!(*h, trace_hash);
            assert_eq!(*heuristic_weight, 20);
        }
        other => panic!("Esperado Committed, obtenido: {:?}", other),
    }
}

#[test]
fn test_adversarial_equivocation_eviction() {
    let (state, topology) = create_3node_quorum();
    let mut scheduler = NemesisScheduler::new(state, topology, FaultPlan::new());

    scheduler.schedule_event(1, None, LogicalEvent::StartEpoch { epoch: 1 });

    let hash_a = [0xAAu8; 32];
    let hash_b = [0xBBu8; 32];

    // Nodo 1 emite voto A
    scheduler.schedule_event(
        2,
        None,
        LogicalEvent::VoteReceived {
            epoch: 1,
            view: 0,
            voter: 1,
            kind: VoteKind::FormalWitnessVerified { trace_hash: hash_a },
        },
    );

    // Nodo 1 (bizantino) emite voto conflictivo B para la misma época y vista
    scheduler.schedule_event(
        3,
        None,
        LogicalEvent::VoteReceived {
            epoch: 1,
            view: 0,
            voter: 1,
            kind: VoteKind::FormalWitnessVerified { trace_hash: hash_b },
        },
    );

    let executed = scheduler.run_until_quiescence(100).expect("Quiescencia sin violación");
    assert_eq!(executed, 3);

    // Comprobar que el nodo 1 fue expulsado inmediatamente
    assert_eq!(
        scheduler.state.nodes.get(&1),
        Some(&NodeStatus::EvictedByEquivocation)
    );

    // Comprobar que se emitió el efecto declarativo EvictNode
    let evicted_effects: Vec<_> = scheduler
        .emitted_effects
        .iter()
        .filter(|(_, eff)| matches!(eff, DeclarativeEffect::EvictNode { node: 1, .. }))
        .collect();
    assert_eq!(evicted_effects.len(), 1);
}

#[test]
fn test_adversarial_network_split_brain_prevention() {
    let (state, _) = create_3node_quorum();

    // Partición de red en tick 2: Nodo 3 queda aislado ({1, 2} vs {3})
    let partition = PartitionMatrix::split(&[1, 2], &[3]);
    let mut fault_plan = FaultPlan::new();
    fault_plan.add_fault(AdversarialFault::InjectPartition {
        at_tick: 2,
        matrix: partition,
    });

    let mut scheduler = NemesisScheduler::new(state, PartitionMatrix::fully_connected(&[1, 2, 3]), fault_plan);

    scheduler.schedule_event(1, None, LogicalEvent::StartEpoch { epoch: 1 });

    // Nodo 3 aislado intenta votar con destino a nodo 1 (bloqueado por partición)
    scheduler.schedule_event(
        3,
        Some(1),
        LogicalEvent::VoteReceived {
            epoch: 1,
            view: 0,
            voter: 3,
            kind: VoteKind::HeuristicApprove { weight: 10 },
        },
    );

    // Solo los nodos 1 y 2 logran comunicarse
    scheduler.schedule_event(
        4,
        Some(2),
        LogicalEvent::VoteReceived {
            epoch: 1,
            view: 0,
            voter: 1,
            kind: VoteKind::FormalWitnessVerified { trace_hash: [0x55u8; 32] },
        },
    );

    scheduler.schedule_event(
        5,
        Some(1),
        LogicalEvent::VoteReceived {
            epoch: 1,
            view: 0,
            voter: 2,
            kind: VoteKind::HeuristicApprove { weight: 10 },
        },
    );

    let _ = scheduler.run_until_quiescence(100).expect("Ejecución bajo partición segura");

    // Quórum {1, 2} tiene 20 de peso y 2/3 de nodos activos -> Safety preservado, commit alcanzado
    assert!(matches!(
        scheduler.state.epoch_statuses.get(&1),
        Some(EpochStatus::Committed { .. })
    ));
}

#[test]
fn test_adversarial_formal_veto_terminal() {
    let (state, topology) = create_3node_quorum();
    let mut scheduler = NemesisScheduler::new(state, topology, FaultPlan::new());

    scheduler.schedule_event(1, None, LogicalEvent::StartEpoch { epoch: 1 });

    // Nodo 2 y 3 aprueban con suficiente peso heurístico (20)
    scheduler.schedule_event(
        2,
        None,
        LogicalEvent::VoteReceived {
            epoch: 1,
            view: 0,
            voter: 2,
            kind: VoteKind::HeuristicApprove { weight: 10 },
        },
    );
    scheduler.schedule_event(
        3,
        None,
        LogicalEvent::VoteReceived {
            epoch: 1,
            view: 0,
            voter: 3,
            kind: VoteKind::HeuristicApprove { weight: 10 },
        },
    );

    // Vértice formal emite refutación irreversible de teorema 101
    scheduler.schedule_event(
        4,
        None,
        LogicalEvent::VoteReceived {
            epoch: 1,
            view: 0,
            voter: 1,
            kind: VoteKind::FormalRefutation { theorem_id: 101 },
        },
    );

    // Posteriormente llega un testigo formal tardío
    scheduler.schedule_event(
        5,
        None,
        LogicalEvent::VoteReceived {
            epoch: 1,
            view: 0,
            voter: 1,
            kind: VoteKind::FormalWitnessVerified { trace_hash: [0x99u8; 32] },
        },
    );

    let _ = scheduler.run_until_quiescence(100).expect("Ejecución con veto");

    // La época DEBE quedar en Vetoed permanentemente
    assert_eq!(
        scheduler.state.epoch_statuses.get(&1),
        Some(&EpochStatus::Vetoed { theorem_id: 101 })
    );

    // Oráculo ratifica que no hubo commit tras veto
    assert!(NemesisOracles::verify_all(&scheduler.state, &scheduler.committed_history).is_ok());
}

#[test]
fn test_causal_replay_and_delta_debugging() {
    let trace_hash = [0x11u8; 32];

    // Predicado de interés: alcanzar Commit en época 1
    let check_commit = |subset: &[(u64, LogicalEvent)]| -> bool {
        let mut nodes = BTreeMap::new();
        nodes.insert(1, 10);
        nodes.insert(2, 10);
        nodes.insert(3, 10);
        let mut st = LarsaPureState::new(nodes, 20);

        for (_, ev) in subset {
            let (next, _) = step(st, ev.clone());
            st = next;
        }

        matches!(st.epoch_statuses.get(&1), Some(EpochStatus::Committed { .. }))
    };

    // La traza contiene los 4 eventos mínimos para el commit (StartEpoch, FormalWitness, Vote2, Vote3)
    // más un evento superfluo en época 2 emitido por el nodo 3.
    let base_events = vec![
        (1, LogicalEvent::StartEpoch { epoch: 1 }),
        (2, LogicalEvent::VoteReceived { epoch: 1, view: 0, voter: 1, kind: VoteKind::FormalWitnessVerified { trace_hash } }),
        (3, LogicalEvent::VoteReceived { epoch: 1, view: 0, voter: 2, kind: VoteKind::HeuristicApprove { weight: 10 } }),
        (4, LogicalEvent::VoteReceived { epoch: 1, view: 0, voter: 3, kind: VoteKind::HeuristicApprove { weight: 10 } }),
        (5, LogicalEvent::VoteReceived { epoch: 2, view: 0, voter: 3, kind: VoteKind::HeuristicApprove { weight: 10 } }),
    ];

    assert!(check_commit(&base_events));

    // Ejecutar minimizador (Delta-Debugging)
    let minimal = DeltaDebugger::minimize(&base_events, check_commit);

    // El evento 5 (época 2) es ruido no relacionado y debe ser podado;
    // mientras que los eventos 1, 2, 3 y 4 son todos estrictamente indispensables.
    assert_eq!(minimal.len(), 4);
    assert!(!minimal.iter().any(|(_, ev)| matches!(ev, LogicalEvent::VoteReceived { epoch: 2, .. })));

    // Empaquetar CausalEvidenceBundle
    let bundle = CausalEvidenceBundle::new(
        42,
        "causal_sha_test",
        "rustc-1.85-nightly",
        [0xAA; 32],
        vec![],
        minimal,
    );
    assert_eq!(bundle.events.len(), 4);
    assert_eq!(bundle.seed, 42);
}
