use babylon60::executor::{
    EffectAdapter, SovereignExecutor, DurableExecutionStore, SecurityPolicy, SyntheticResource, ProposedIntent, SignedAuthorization,
    AuthorizationPayload, AuthorityAlgorithm, ExecutionError, SyntheticEffectAdapter, AdmittedAuthority, ReservationState
};
use babylon60::receipt::Ed25519Signer;
use ed25519_dalek::SigningKey;
use rand::rngs::OsRng;
use std::sync::{Arc, Mutex};
use std::thread;

const INST: [u8; 32] = [0x11; 32];
const EXEC: [u8; 32] = [0x22; 32];

fn tmp_db(tag: &str) -> String {
    let n = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos();
    let dir = std::env::temp_dir().join(format!("b60_exec_{}_{}_{}", tag, std::process::id(), n));
    std::fs::create_dir_all(&dir).unwrap();
    dir.join("ledger.sqlite").to_string_lossy().into_owned()
}

// 1. 100 targets independientes = 100 efectos COMPLETED.
#[test]
fn invariant_100_independent_targets() {
    let sk = SigningKey::generate(&mut OsRng);
    let pk = sk.verifying_key().to_bytes().to_vec();
    let signer = Ed25519Signer::from_signing_key(sk);

    let store = DurableExecutionStore::open(&tmp_db("inv1")).unwrap();
    let executor = SovereignExecutor::new(
        INST, EXEC, 1,
        vec![AdmittedAuthority { public_key: pk.clone(), algorithm: AuthorityAlgorithm::Ed25519 }],
        store,
        SyntheticEffectAdapter,
    );
    let shared_exec = Arc::new(Mutex::new(executor));
    
    let mut threads = vec![];
    for i in 0..100 {
        let exec_clone = Arc::clone(&shared_exec);
        let pk_clone = pk.clone();
        let signer_clone = signer.clone();
        
        threads.push(thread::spawn(move || {
            let mut resource = SyntheticResource::new(&format!("target_{}", i), 1000);
            let policy = SecurityPolicy {
                policy_id: [i; 32],
                allowed_action: "ADD".into(),
                max_allowed_uses: 1,
                admitted_authority_key: pk_clone,
            };
            let intent = ProposedIntent {
                intent_id: [i; 32],
                target_resource: format!("target_{}", i),
                action_name: "ADD".into(),
                parameters: 1u64.to_be_bytes().to_vec(),
            };
            let payload = AuthorizationPayload {
                protocol_version: 5,
                installation_id: INST,
                executor_id: EXEC,
                policy_digest: policy.compute_digest(),
                intent_digest: intent.compute_digest(),
                resource_precondition_digest: SyntheticEffectAdapter.compute_precondition(&resource).unwrap(),
                nonce: [i; 32],
                authority_epoch: 1,
                expires_at: 2_000_000_000,
                max_uses: 1,
            };
            let auth = SignedAuthorization::new_cose(&payload, &signer_clone).unwrap();
            
            let mut ex = exec_clone.lock().unwrap();
            let res = ex.execute_action(&auth, &intent, &policy, &mut resource, 1000);
            res.is_ok()
        }));
    }
    
    let mut successes = 0;
    for t in threads {
        if t.join().unwrap() {
            successes += 1;
        }
    }
    assert_eq!(successes, 100, "Todos los 100 targets independientes deben completarse.");
    
    let exec = shared_exec.lock().unwrap();
    assert_eq!(exec.store.count_by_state(ReservationState::Executed).unwrap(), 100);
}

// 2. Un nonce compartido (100 peticiones con el MISMO nonce) = 1 efecto, 99 rechazos de replay.
#[test]
fn invariant_shared_nonce_replay_rejection() {
    let sk = SigningKey::generate(&mut OsRng);
    let pk = sk.verifying_key().to_bytes().to_vec();
    let signer = Ed25519Signer::from_signing_key(sk);

    let store = DurableExecutionStore::open(&tmp_db("inv2")).unwrap();
    let executor = SovereignExecutor::new(
        INST, EXEC, 1,
        vec![AdmittedAuthority { public_key: pk.clone(), algorithm: AuthorityAlgorithm::Ed25519 }],
        store,
        SyntheticEffectAdapter,
    );
    let shared_exec = Arc::new(Mutex::new(executor));
    
    // Todos usan el mismo recurso, misma política, mismo nonce.
    let resource = SyntheticResource::new("shared_target", 1000);
    let policy = SecurityPolicy {
        policy_id: [0xBB; 32],
        allowed_action: "ADD".into(),
        max_allowed_uses: 1,
        admitted_authority_key: pk.clone(),
    };
    let intent = ProposedIntent {
        intent_id: [0xCC; 32],
        target_resource: "shared_target".into(),
        action_name: "ADD".into(),
        parameters: 1u64.to_be_bytes().to_vec(),
    };
    let payload = AuthorizationPayload {
        protocol_version: 5,
        installation_id: INST,
        executor_id: EXEC,
        policy_digest: policy.compute_digest(),
        intent_digest: intent.compute_digest(),
        resource_precondition_digest: SyntheticEffectAdapter.compute_precondition(&resource).unwrap(),
        nonce: [0xDD; 32],
        authority_epoch: 1,
        expires_at: 2_000_000_000,
        max_uses: 1,
    };
    let auth = SignedAuthorization::new_cose(&payload, &signer).unwrap();
    let shared_resource = Arc::new(Mutex::new(resource));
    
    let mut threads = vec![];
    for _ in 0..100 {
        let exec_clone = Arc::clone(&shared_exec);
        let auth_clone = auth.clone();
        let intent_clone = intent.clone();
        let policy_clone = policy.clone();
        let res_clone = Arc::clone(&shared_resource);
        
        threads.push(thread::spawn(move || {
            let mut ex = exec_clone.lock().unwrap();
            let mut r = res_clone.lock().unwrap();
            ex.execute_action(&auth_clone, &intent_clone, &policy_clone, &mut r, 1000)
        }));
    }
    
    let mut oks = 0;
    let mut replays = 0;
    for t in threads {
        match t.join().unwrap() {
            Ok(_) => oks += 1,
            Err(ExecutionError::NonceAlreadyConsumed(_)) => replays += 1,
            _ => panic!("Error inesperado"),
        }
    }
    
    assert_eq!(oks, 1, "Solo 1 despacho completado.");
    assert_eq!(replays, 99, "99 rechazos exactos por NonceConsumed.");
}

// 3. 100 nonces distintos, misma precondición CAS = 1 efecto COMPLETED, 99 REJECTED por PreconditionMismatch.
#[test]
fn invariant_100_nonces_same_cas() {
    let sk = SigningKey::generate(&mut OsRng);
    let pk = sk.verifying_key().to_bytes().to_vec();
    let signer = Ed25519Signer::from_signing_key(sk);

    let store = DurableExecutionStore::open(&tmp_db("inv3")).unwrap();
    let executor = SovereignExecutor::new(
        INST, EXEC, 1,
        vec![AdmittedAuthority { public_key: pk.clone(), algorithm: AuthorityAlgorithm::Ed25519 }],
        store,
        SyntheticEffectAdapter,
    );
    let shared_exec = Arc::new(Mutex::new(executor));
    
    let resource = SyntheticResource::new("cas_target", 1000);
    let policy = SecurityPolicy {
        policy_id: [0xEE; 32],
        allowed_action: "ADD".into(),
        max_allowed_uses: 1,
        admitted_authority_key: pk.clone(),
    };
    let intent = ProposedIntent {
        intent_id: [0xFF; 32],
        target_resource: "cas_target".into(),
        action_name: "ADD".into(),
        parameters: 1u64.to_be_bytes().to_vec(),
    };
    
    let shared_resource = Arc::new(Mutex::new(resource.clone()));
    
    let mut threads = vec![];
    for i in 0..100 {
        let exec_clone = Arc::clone(&shared_exec);
        let intent_clone = intent.clone();
        let policy_clone = policy.clone();
        let res_clone = Arc::clone(&shared_resource);
        let signer_clone = signer.clone();
        let resource_clone = resource.clone(); // The original state!
        
        threads.push(thread::spawn(move || {
            let payload = AuthorizationPayload {
                protocol_version: 5,
                installation_id: INST,
                executor_id: EXEC,
                policy_digest: policy_clone.compute_digest(),
                intent_digest: intent_clone.compute_digest(),
                resource_precondition_digest: SyntheticEffectAdapter.compute_precondition(&resource_clone).unwrap(),
                nonce: [i; 32],
                authority_epoch: 1,
                expires_at: 2_000_000_000,
                max_uses: 1,
            };
            let auth = SignedAuthorization::new_cose(&payload, &signer_clone).unwrap();
            
            let mut ex = exec_clone.lock().unwrap();
            let mut r = res_clone.lock().unwrap();
            ex.execute_action(&auth, &intent_clone, &policy_clone, &mut r, 1000)
        }));
    }
    
    let mut oks = 0;
    let mut cas_fails = 0;
    for t in threads {
        match t.join().unwrap() {
            Ok(_) => oks += 1,
            Err(ExecutionError::PreconditionMismatch) => cas_fails += 1,
            Err(e) => panic!("Error inesperado: {:?}", e),
        }
    }
    
    assert_eq!(oks, 1, "Solo 1 modificación CAS permitida.");
    assert_eq!(cas_fails, 99, "99 rechazos exactos por PreconditionMismatch (CAS).");
}

// 4. Firma/intención alterada = Cero reservas y cero efectos.
#[test]
fn invariant_altered_intent_rejected() {
    let sk = SigningKey::generate(&mut OsRng);
    let pk = sk.verifying_key().to_bytes().to_vec();
    let signer = Ed25519Signer::from_signing_key(sk);

    let store = DurableExecutionStore::open(&tmp_db("inv4")).unwrap();
    let executor = SovereignExecutor::new(
        INST, EXEC, 1,
        vec![AdmittedAuthority { public_key: pk.clone(), algorithm: AuthorityAlgorithm::Ed25519 }],
        store,
        SyntheticEffectAdapter,
    );
    let shared_exec = Arc::new(Mutex::new(executor));
    
    let mut resource = SyntheticResource::new("hack_target", 1000);
    let policy = SecurityPolicy {
        policy_id: [0x12; 32],
        allowed_action: "ADD".into(),
        max_allowed_uses: 1,
        admitted_authority_key: pk.clone(),
    };
    
    let original_intent = ProposedIntent {
        intent_id: [0x34; 32],
        target_resource: "hack_target".into(),
        action_name: "ADD".into(),
        parameters: 1u64.to_be_bytes().to_vec(),
    };
    
    // Firma sobre el original
    let payload = AuthorizationPayload {
        protocol_version: 5,
        installation_id: INST,
        executor_id: EXEC,
        policy_digest: policy.compute_digest(),
        intent_digest: original_intent.compute_digest(),
        resource_precondition_digest: SyntheticEffectAdapter.compute_precondition(&resource).unwrap(),
        nonce: [0x56; 32],
        authority_epoch: 1,
        expires_at: 2_000_000_000,
        max_uses: 1,
    };
    let auth = SignedAuthorization::new_cose(&payload, &signer).unwrap();
    
    // Hacker altera la intención! Cambia el parámetro (roba más)
    let hacked_intent = ProposedIntent {
        intent_id: [0x34; 32],
        target_resource: "hack_target".into(),
        action_name: "ADD".into(),
        parameters: 1000000u64.to_be_bytes().to_vec(), // Modificado!
    };
    
    let mut ex = shared_exec.lock().unwrap();
    let res = ex.execute_action(&auth, &hacked_intent, &policy, &mut resource, 1000);
    
    assert!(matches!(res, Err(ExecutionError::IntentDigestMismatch)));
    
    // Comprobar que no hay reservas consumidas
    assert_eq!(ex.store.count_by_state(ReservationState::Executed).unwrap(), 0);
    assert_eq!(ex.store.count_by_state(ReservationState::Reserved).unwrap(), 0);
}

// ─── ITERACIÓN 2: concurrencia REAL (sin Mutex global) ──────────────────────
// Un executor + una conexión SQLite por hilo sobre el MISMO fichero WAL.
// El único punto de serialización es la transacción IMMEDIATE del ledger.
// Métrica fiable: efectos realmente aplicados (mutación observable del recurso),
// no el número de Ok devueltos.
#[test]
fn invariant_shared_nonce_true_concurrency_multi_connection() {
    use std::sync::Barrier;
    let sk = SigningKey::generate(&mut OsRng);
    let pk = sk.verifying_key().to_bytes().to_vec();
    let signer = Ed25519Signer::from_signing_key(sk);
    let db = tmp_db("inv2b");

    let policy = SecurityPolicy {
        policy_id: [0xBB; 32],
        allowed_action: "ADD".into(),
        max_allowed_uses: 1,
        admitted_authority_key: pk.clone(),
    };
    let intent = ProposedIntent {
        intent_id: [0xCC; 32],
        target_resource: "shared_target".into(),
        action_name: "ADD".into(),
        parameters: 1u64.to_be_bytes().to_vec(),
    };
    let base = SyntheticResource::new("shared_target", 1000);
    let payload = AuthorizationPayload {
        protocol_version: 5,
        installation_id: INST,
        executor_id: EXEC,
        policy_digest: policy.compute_digest(),
        intent_digest: intent.compute_digest(),
        resource_precondition_digest: SyntheticEffectAdapter.compute_precondition(&base).unwrap(),
        nonce: [0xDD; 32],
        authority_epoch: 1,
        expires_at: 2_000_000_000,
        max_uses: 1,
    };
    let auth = SignedAuthorization::new_cose(&payload, &signer).unwrap();

    // Pre-inicializar el esquema del ledger antes de lanzar los hilos para evitar carrera DDL
    {
        let _init = DurableExecutionStore::open(&db).unwrap();
    }

    const N: usize = 100;
    let barrier = Arc::new(Barrier::new(N));
    let mut threads = vec![];
    for _ in 0..N {
        let (db, pk, auth, intent, policy, base, barrier) =
            (db.clone(), pk.clone(), auth.clone(), intent.clone(), policy.clone(), base.clone(), Arc::clone(&barrier));
        threads.push(thread::spawn(move || {
            let store_res = DurableExecutionStore::open(&db);
            barrier.wait();
            let store = store_res.unwrap();
            let mut ex = SovereignExecutor::new(
                INST, EXEC, 1,
                vec![AdmittedAuthority { public_key: pk, algorithm: AuthorityAlgorithm::Ed25519 }],
                store, SyntheticEffectAdapter,
            );
            let mut r = base.clone(); // recurso privado: sin serialización en memoria
            let res = ex.execute_action(&auth, &intent, &policy, &mut r, 1000);
            (res.map(|_| ()).map_err(|e| format!("{:?}", e)), r != base)
        }));
    }

    let (mut oks, mut applied) = (0usize, 0usize);
    let mut errs: std::collections::BTreeMap<String, usize> = Default::default();
    for t in threads {
        let (res, mutated) = t.join().unwrap();
        if mutated { applied += 1; }
        match res {
            Ok(()) => oks += 1,
            Err(e) => *errs.entry(e.split('(').next().unwrap().to_string()).or_default() += 1,
        }
    }
    eprintln!("oks={oks} efectos_aplicados={applied} errores={errs:?}");
    assert_eq!(applied, 1, "AX-0 violado: efectos aplicados = {applied}, esperado 1");
}

// ─── ITERACIÓN 3: campaña mixta de 100 workers, concurrencia real ───────────
// 60 legítimos (nonces y targets distintos) + 10 replay del mismo nonce
// + 20 intención alterada + 10 clave no admitida. Sin Mutex global; una
// conexión WAL por worker. Auditoría final del ledger con conexión nueva.
#[test]
fn invariant_mixed_campaign_100_workers_true_concurrency() {
    use std::sync::Barrier;
    let sk = SigningKey::generate(&mut OsRng);
    let pk = sk.verifying_key().to_bytes().to_vec();
    let signer = Ed25519Signer::from_signing_key(sk);
    let rogue_signer = Ed25519Signer::from_signing_key(SigningKey::generate(&mut OsRng));
    let db = tmp_db("mixed");

    let policy = SecurityPolicy {
        policy_id: [0xAA; 32], allowed_action: "ADD".into(),
        max_allowed_uses: 1, admitted_authority_key: pk.clone(),
    };
    let mk_intent = |id: u8, target: &str, delta: u64| ProposedIntent {
        intent_id: [id; 32], target_resource: target.into(), action_name: "ADD".into(),
        parameters: delta.to_be_bytes().to_vec(),
    };
    let mk_auth = |s: &Ed25519Signer, intent: &ProposedIntent, res: &SyntheticResource, nonce: u8| {
        let p = AuthorizationPayload {
            protocol_version: 5, installation_id: INST, executor_id: EXEC,
            policy_digest: policy.compute_digest(), intent_digest: intent.compute_digest(),
            resource_precondition_digest: SyntheticEffectAdapter.compute_precondition(res).unwrap(),
            nonce: [nonce; 32], authority_epoch: 1, expires_at: 2_000_000_000, max_uses: 1,
        };
        SignedAuthorization::new_cose(&p, s).unwrap()
    };

    // (rol, auth, intent_a_ejecutar, recurso_base)
    let mut jobs = vec![];
    for i in 0..60u8 {
        let r = SyntheticResource::new(&format!("t{i}"), 1000);
        let it = mk_intent(i, &format!("t{i}"), 1);
        jobs.push(("legit", mk_auth(&signer, &it, &r, i), it, r));
    }
    let shared_r = SyntheticResource::new("shared", 1000);
    let shared_it = mk_intent(0xE0, "shared", 1);
    let shared_auth = mk_auth(&signer, &shared_it, &shared_r, 0xEE);
    for _ in 0..10 {
        jobs.push(("replay", shared_auth.clone(), shared_it.clone(), shared_r.clone()));
    }
    for i in 0..20u8 {
        let r = SyntheticResource::new(&format!("a{i}"), 1000);
        let signed = mk_intent(100 + i, &format!("a{i}"), 1);
        let hacked = mk_intent(100 + i, &format!("a{i}"), 1_000_000);
        jobs.push(("altered", mk_auth(&signer, &signed, &r, 100 + i), hacked, r));
    }
    for i in 0..10u8 {
        let r = SyntheticResource::new(&format!("r{i}"), 1000);
        let it = mk_intent(200 + i, &format!("r{i}"), 1);
        jobs.push(("rogue", mk_auth(&rogue_signer, &it, &r, 200 + i), it, r));
    }
    assert_eq!(jobs.len(), 100);

    // Pre-inicializar el esquema del ledger antes de lanzar los 100 workers concurrentes
    {
        let _init = DurableExecutionStore::open(&db).unwrap();
    }

    let barrier = Arc::new(Barrier::new(100));
    let mut threads = vec![];
    for (role, auth, intent, base) in jobs {
        let (db, pk, policy, barrier) = (db.clone(), pk.clone(), policy.clone(), Arc::clone(&barrier));
        threads.push(thread::spawn(move || {
            let store_res = DurableExecutionStore::open(&db);
            barrier.wait();
            let store = store_res.unwrap();
            let mut ex = SovereignExecutor::new(
                INST, EXEC, 1,
                vec![AdmittedAuthority { public_key: pk, algorithm: AuthorityAlgorithm::Ed25519 }],
                store, SyntheticEffectAdapter,
            );
            let mut r = base.clone();
            let _delta = u64::from_be_bytes(intent.parameters.clone().try_into().unwrap());
            let t0 = std::time::Instant::now();
            let res = ex.execute_action(&auth, &intent, &policy, &mut r, 1000);
            let us = t0.elapsed().as_micros() as u64;
            (role, res.map(|_| ()).map_err(|e| format!("{:?}", e)), r != base, us)
        }));
    }

    let mut by_role: std::collections::BTreeMap<(&str, String), usize> = Default::default();
    let (mut applied, mut lat) = (0usize, vec![]);
    for t in threads {
        let (role, res, mutated, us) = t.join().unwrap();
        lat.push(us);
        if mutated { applied += 1; }
        let k = match res { Ok(()) => "Ok".to_string(), Err(e) => e.split('(').next().unwrap().to_string() };
        *by_role.entry((role, k)).or_default() += 1;
    }
    lat.sort();
    eprintln!("applied={applied} p50={}us p99={}us max={}us\n{by_role:#?}",
              lat[50], lat[98], lat[99]);

    // Auditoría independiente del ledger (conexión nueva).
    let audit = DurableExecutionStore::open(&db).unwrap();
    let c = |s| audit.count_by_state(s).unwrap();
    eprintln!("ledger: executed={} reserved={} dispatched={} failed={} unknown={}",
              c(ReservationState::Executed), c(ReservationState::Reserved),
              c(ReservationState::Dispatched), c(ReservationState::Failed), c(ReservationState::Unknown));

    assert_eq!(applied, 61, "60 legítimos + 1 del nonce compartido");
    assert_eq!(c(ReservationState::Executed), 61);
    assert_eq!(c(ReservationState::Reserved) + c(ReservationState::Dispatched)
             + c(ReservationState::Failed) + c(ReservationState::Unknown), 0,
               "rechazos pre-reserva no deben dejar filas; nada atascado");
    assert_eq!(by_role.get(&("altered", "IntentDigestMismatch".into())), Some(&20));
    assert_eq!(by_role.get(&("rogue", "InvalidAuthorityKey".into())), Some(&10));
}

// ─── ITERACIÓN 4: techo de contención del ledger (SWARM_N workers) ──────────
// Sólo workers legítimos, nonce/target distintos, conexión WAL propia.
// Mide dónde aparece el primer StorageError (busy_timeout = 5000 ms).
#[test]
fn ceiling_ledger_contention() {
    use std::sync::Barrier;
    let n: usize = std::env::var("SWARM_N").ok().and_then(|v| v.parse().ok()).unwrap_or(100);
    let sk = SigningKey::generate(&mut OsRng);
    let pk = sk.verifying_key().to_bytes().to_vec();
    let signer = Ed25519Signer::from_signing_key(sk);
    let db = tmp_db("ceiling");
    // Pre-inicializar el esquema para evitar carreras de DDL entre los 100 hilos
    let _init = DurableExecutionStore::open(&db).unwrap();
    drop(_init);

    let policy = SecurityPolicy {
        policy_id: [0xAA; 32], allowed_action: "ADD".into(),
        max_allowed_uses: 1, admitted_authority_key: pk.clone(),
    };
    let id32 = |i: usize| { let mut b = [0u8; 32]; b[..8].copy_from_slice(&(i as u64).to_be_bytes()); b };

    let barrier = Arc::new(Barrier::new(n));
    let mut threads = vec![];
    for i in 0..n {
        let r = SyntheticResource::new(&format!("t{i}"), 1000);
        let it = ProposedIntent {
            intent_id: id32(i), target_resource: format!("t{i}"), action_name: "ADD".into(),
            parameters: 1u64.to_be_bytes().to_vec(),
        };
        let p = AuthorizationPayload {
            protocol_version: 5, installation_id: INST, executor_id: EXEC,
            policy_digest: policy.compute_digest(), intent_digest: it.compute_digest(),
            resource_precondition_digest: SyntheticEffectAdapter.compute_precondition(&r).unwrap(),
            nonce: id32(i), authority_epoch: 1, expires_at: 2_000_000_000, max_uses: 1,
        };
        let auth = SignedAuthorization::new_cose(&p, &signer).unwrap();
        let (db, pk, policy, barrier) = (db.clone(), pk.clone(), policy.clone(), Arc::clone(&barrier));
        threads.push(thread::spawn(move || {
            let store = match DurableExecutionStore::open(&db) {
                Ok(s) => s,
                Err(e) => {
                    barrier.wait();
                    return Err(format!("open:{e:?}"));
                }
            };
            let mut ex = SovereignExecutor::new(
                INST, EXEC, 1,
                vec![AdmittedAuthority { public_key: pk, algorithm: AuthorityAlgorithm::Ed25519 }],
                store, SyntheticEffectAdapter,
            );
            let mut rr = r.clone();
            barrier.wait();
            let t0 = std::time::Instant::now();
            let res = ex.execute_action(&auth, &it, &policy, &mut rr, 1000);
            let us = t0.elapsed().as_micros() as u64;
            res.map(|_| us).map_err(|e| format!("{e:?}"))
        }));
    }
    let (mut ok, mut lat) = (0usize, vec![]);
    let mut errs: std::collections::BTreeMap<String, usize> = Default::default();
    for t in threads {
        match t.join().unwrap() {
            Ok(us) => { ok += 1; lat.push(us); }
            Err(e) => *errs.entry(e.chars().take(60).collect()).or_default() += 1,
        }
    }
    lat.sort();
    let q = |p: usize| lat.get(((lat.len().saturating_sub(1)) * p) / 100).copied().unwrap_or(0);
    eprintln!("N={n} ok={ok} p50={}ms p99={}ms max={}ms errs={errs:?}",
              q(50) / 1000, q(99) / 1000, lat.last().copied().unwrap_or(0) / 1000);
    let audit = DurableExecutionStore::open(&db).unwrap();
    let ex = audit.count_by_state(ReservationState::Executed).unwrap();
    eprintln!("ledger executed={ex}");
    assert_eq!(ex as usize, ok, "ledger y resultados deben coincidir");
}
