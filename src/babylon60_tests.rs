use super::*;

const SOURCE: &str = include_str!("../tools/examples/counter_sync.b60");

#[test]
fn sexagesimal_whitespace_separates_positions() {
    assert_eq!(parse_b60_number("[ <<<<<YYYYYYYYY ]"), 59);
    assert_eq!(parse_b60_number("[ Y - ]"), 60);
    assert_eq!(parse_b60_number("[ <<<<< YYYYYYYYY ]"), 3009);
}

#[test]
fn fixture_encodes_threshold_59() {
    let assignment = SOURCE
        .lines()
        .find(|line| line.starts_with("NIG R0 "))
        .unwrap();
    let literal = assignment
        .split_once('[')
        .unwrap()
        .1
        .split_once(']')
        .unwrap()
        .0;
    assert_eq!(parse_b60_number(literal), 59);
}

#[test]
fn peak_tracks_executed_register_values() {
    let result =
        run("ALLOC F60 R10\nNIG R10 [ YY ]\nDAH R10 [ YYY ]\nNIG R10 [ Y ]\nHALT").unwrap();
    assert_eq!(result.r10_peak, Some(5));
}

#[test]
fn canonical_hash_changes_when_only_opcode_changes() {
    let mut ledger = DAGLedger::new();
    ledger.append(
        "EV_0_0".into(),
        "NIG".into(),
        "same payload".into(),
        LogicalClock(0),
    );
    let before = ledger.canonical_hash();
    ledger.events.get_mut("EV_0_0").unwrap().opcode = "DAH".into();
    assert_ne!(before, ledger.canonical_hash());
}

#[test]
fn unfulfilled_wait_terminates() {
    let (sender, receiver) = std::sync::mpsc::channel();
    std::thread::spawn(move || {
        let result = run("AWAIT \"NEVER\" DONE\nMUB DONE\nHALT");
        sender.send(result).unwrap();
    });
    let result = receiver
        .recv_timeout(std::time::Duration::from_secs(3))
        .expect("El intérprete debe terminar aunque ninguna corrutina emita la señal");
    assert_eq!(
        result,
        Err(ExecutionError::StepLimitExceeded {
            max_steps: MAX_STEPS
        })
    );
}

#[test]
fn fixture_reaches_threshold_and_repeats_the_same_result() {
    let mut ring = babylon60::spsc_ring::SpscRingBuffer::<String, 1024>::new();
    let (_producer, mut consumer) = ring.split();
    let execution = execute_program(SOURCE, &mut consumer, MAX_STEPS);
    for payload in ["R10=59", "R20=59"] {
        assert!(execution
            .ledger
            .events
            .values()
            .any(|event| event.opcode == "SAR" && event.payload == payload));
    }
    let first = run(SOURCE).unwrap();
    assert!(!first.quarantined);
    assert_eq!(first.r10_peak, Some(59));
    for _ in 0..100 {
        assert_eq!(run(SOURCE).unwrap(), first);
    }
}

#[test]
fn changing_threshold_changes_the_observed_peak() {
    let modified = SOURCE.replace("[ <<<<<YYYYYYYYY ]", "[ YYYY ]");
    assert_ne!(modified, SOURCE);
    let result = run(&modified).unwrap();
    assert!(!result.quarantined);
    assert_eq!(result.r10_peak, Some(4));
    assert_ne!(result.canonical_hash, run(SOURCE).unwrap().canonical_hash);
}

#[test]
fn absent_counter_is_not_reported_as_a_peak() {
    let result = run("HALT").unwrap();
    assert_eq!(result.r10_peak, None);
    assert!(!result.quarantined);
}

#[test]
fn peak_includes_child_coroutines() {
    let result = run("FORK CHILD\nALLOC F60 R10\nNIG R10 [ YY ]\nHALT\n\
         MUB CHILD\nALLOC F60 R10\nNIG R10 [ YYYYYYY ]\nHALT")
    .unwrap();
    assert_eq!(result.r10_peak, Some(7));
}

#[test]
fn all_scheduler_paths_respect_the_step_budget() {
    let programs = [
        // Todas las corrutinas esperando una señal ausente.
        "FORK CHILD\nAWAIT \"NEVER\" DONE\nMUB CHILD\nAWAIT \"NEVER\" DONE\nMUB DONE\nHALT",
        // El temporizador vence después del presupuesto.
        "ALLOC TIME R1\nNIG R1 [ Y - ]\nAFTER R1 DONE\nMUB DONE\nHALT",
        // Bucle de instrucciones sin espera.
        "MUB LOOP\nNU R0 LOOP",
    ];
    for source in programs {
        let (sender, receiver) = std::sync::mpsc::channel();
        std::thread::spawn(move || {
            sender.send(run_bounded(source, 8)).unwrap();
        });
        let result = receiver
            .recv_timeout(std::time::Duration::from_secs(3))
            .expect("El límite debe cubrir cada ruta del planificador");
        assert_eq!(
            result,
            Err(ExecutionError::StepLimitExceeded { max_steps: 8 })
        );
    }
}

#[test]
fn step_budget_allows_exactly_the_requested_number_of_dispatches() {
    assert!(run_bounded("HALT", 1).is_ok());
    assert_eq!(
        run_bounded("HALT", 0),
        Err(ExecutionError::StepLimitExceeded { max_steps: 0 })
    );
    assert_eq!(
        run_bounded("NIG R0 [ Y ]\nHALT", 1),
        Err(ExecutionError::StepLimitExceeded { max_steps: 1 })
    );
}

#[test]
fn short_timer_and_matching_signal_resume_execution() {
    let timer = "ALLOC TIME R1\nNIG R1 [ YY ]\nAFTER R1 DONE\n\
                 MUB DONE\nALLOC F60 R10\nNIG R10 [ YYY ]\nHALT";
    assert_eq!(run_bounded(timer, 8).unwrap().r10_peak, Some(3));

    let signal = "FORK CHILD\nEXECUTE \"READY\"\nHALT\n\
                  MUB CHILD\nAWAIT \"READY\" DONE\nMUB DONE\n\
                  ALLOC F60 R10\nNIG R10 [ YYYY ]\nHALT";
    assert_eq!(run_bounded(signal, 8).unwrap().r10_peak, Some(4));
}

#[test]
fn invalid_timer_is_rejected() {
    let negative = "NIG R2 [ Y ]\nLAL R1 R2\nAFTER R1 DONE\nMUB DONE\nHALT";
    assert_eq!(run(negative), Err(ExecutionError::InvalidTimer));
}

#[test]
fn halts_in_different_coroutines_preserve_each_event() {
    let result = run("FORK CHILD\nHALT\nMUB CHILD\nHALT").unwrap();
    assert_eq!(result.total_events, 3);
}

#[test]
fn canonical_hash_covers_every_event_field() {
    let mut ledger = DAGLedger::new();
    ledger.append(
        "EV_0_0".into(),
        "NIG".into(),
        "R0=1".into(),
        LogicalClock(0),
    );
    let original = ledger.events["EV_0_0"].clone();
    let hash = ledger.canonical_hash();
    for field in 0..6 {
        let mut event = original.clone();
        match field {
            0 => event.id = "EV_other".into(),
            1 => event.parents.push("EV_parent".into()),
            2 => event.logical_timestamp.0 += 1,
            3 => event.opcode = "DAH".into(),
            4 => event.payload = "R0=2".into(),
            5 => event.signature = "changed".into(),
            _ => unreachable!(),
        }
        ledger.events.insert("EV_0_0".into(), event);
        assert_ne!(hash, ledger.canonical_hash(), "Campo omitido: {}", field);
    }
}

#[test]
fn canonical_hash_ignores_map_and_parent_order() {
    let mut first = DAGLedger::new();
    first.append(
        "EV_0_0".into(),
        "FORK".into(),
        "CHILD".into(),
        LogicalClock(0),
    );
    first.append(
        "EV_1_1".into(),
        "HALT".into(),
        "CO_1".into(),
        LogicalClock(1),
    );
    first.events.get_mut("EV_1_1").unwrap().parents = vec!["P1".into(), "P2".into()];
    let mut second = DAGLedger::new();
    for id in ["EV_1_1", "EV_0_0"] {
        let mut event = first.events[id].clone();
        event.parents.reverse();
        second.events.insert(id.into(), event);
    }
    assert_eq!(first.canonical_hash(), second.canonical_hash());
}

#[test]
fn canonical_hash_preserves_field_and_parent_boundaries() {
    let mut ledger = DAGLedger::new();
    ledger.append(
        "EV_0_0".into(),
        "A|B".into(),
        "C\nD".into(),
        LogicalClock(0),
    );
    let hash = ledger.canonical_hash();
    let event = ledger.events.get_mut("EV_0_0").unwrap();
    event.opcode = "A".into();
    event.payload = "B|C\nD".into();
    assert_ne!(hash, ledger.canonical_hash());

    ledger.events.get_mut("EV_0_0").unwrap().parents = vec!["A,B".into()];
    let hash = ledger.canonical_hash();
    ledger.events.get_mut("EV_0_0").unwrap().parents = vec!["A".into(), "B".into()];
    assert_ne!(hash, ledger.canonical_hash());
}

// These helpers call the same engine as the CLI, with an empty input channel.
#[derive(Debug, PartialEq, Eq)]
struct Summary {
    quarantined: bool,
    canonical_hash: String,
    total_events: usize,
    r10_peak: Option<i128>,
}

fn run(source: &str) -> Result<Summary, ExecutionError> {
    run_bounded(source, MAX_STEPS)
}

fn run_bounded(source: &str, max_steps: u64) -> Result<Summary, ExecutionError> {
    let mut ring = babylon60::spsc_ring::SpscRingBuffer::<String, 1024>::new();
    let (_producer, mut consumer) = ring.split();
    let execution = execute_program(source, &mut consumer, max_steps);
    if let Some(error) = execution.error {
        return Err(error);
    }
    Ok(Summary {
        quarantined: execution.quarantined,
        canonical_hash: execution.ledger.canonical_hash(),
        total_events: execution.ledger.events.len(),
        r10_peak: execution.r10_peak,
    })
}

#[test]
fn unknown_opcodes_and_critical_halt_remain_fail_closed() {
    assert!(run("UNKNOWN").unwrap().quarantined);
    assert!(run("EXECUTE \"CRITICAL_HALT\"").unwrap().quarantined);
    assert!(matches!(
        run("GIN MISSING"),
        Err(ExecutionError::StaticRejected(_))
    ));
}

#[test]
fn input_events_and_instructions_keep_distinct_ids_at_the_same_tick() {
    let mut ring = babylon60::spsc_ring::SpscRingBuffer::<String, 1024>::new();
    let (mut producer, mut consumer) = ring.split();
    assert!(producer
        .push("externally supplied message".to_string())
        .is_ok());
    let execution = execute_program("NIG R0 [ Y ]\nHALT", &mut consumer, 2);
    assert!(!execution.quarantined);
    assert_eq!(execution.ledger.events.len(), 3);
    let first_tick: Vec<_> = execution
        .ledger
        .events
        .values()
        .filter(|event| event.logical_timestamp == LogicalClock(1))
        .collect();
    assert_eq!(first_tick.len(), 2);
    assert_ne!(first_tick[0].id, first_tick[1].id);
}
