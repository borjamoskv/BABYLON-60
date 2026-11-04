//! Real filesystem witnesses for nonce ownership across independently opened brokers.
use babylon60::secure_fs::{
    AuthorityContext, EffectBudgetPolicy, EffectTxOrchestrator, EffectTxState, EffectType, NativeSecureFs,
    SecureFsBackend, SecureFsError,
};
use std::fs::{File, OpenOptions};
use std::io::Write;
use std::os::unix::fs::OpenOptionsExt;
use std::os::unix::io::AsRawFd;
use std::path::PathBuf;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Arc, Barrier};

static NEXT_ROOT: AtomicUsize = AtomicUsize::new(0);

struct Lab(PathBuf);

impl Lab {
    fn new() -> Self {
        let root = std::env::temp_dir().join(format!(
            "b60_nonce_instances_{}_{}",
            std::process::id(),
            NEXT_ROOT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&root).unwrap();
        Self(root)
    }

    fn open(&self) -> EffectTxOrchestrator<NativeSecureFs> {
        EffectTxOrchestrator::new(&self.0).unwrap()
    }

    fn directory(&self) -> File {
        OpenOptions::new()
            .read(true)
            .custom_flags(libc::O_DIRECTORY | libc::O_NOFOLLOW)
            .open(&self.0)
            .unwrap()
    }
}

impl Drop for Lab {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}

#[test]
fn already_open_instance_rejects_durably_consumed_nonce() {
    let lab = Lab::new();
    let first = lab.open();
    let second = lab.open();
    let nonce = [0x51; 32];

    first.consume_nonce_durable(&nonce).unwrap();
    let replay = second.consume_nonce_durable(&nonce);
    let ledger = std::fs::read(first.quarantine.dir_path.join(".consumed_nonces.bin")).unwrap();
    assert!(
        matches!(replay, Err(SecureFsError::NonceReplayDetected { .. })),
        "second live instance accepted a consumed nonce; durable_bytes={}",
        ledger.len()
    );
    assert_eq!(
        ledger.len(),
        32,
        "rejected replay must not append another record"
    );
    assert!(matches!(
        lab.open().consume_nonce_durable(&nonce),
        Err(SecureFsError::NonceReplayDetected { .. })
    ));
}

#[test]
fn replay_cannot_mutate_an_independent_file_through_a_second_instance() {
    let lab = Lab::new();
    let first = lab.open();
    let second = lab.open();
    let directory = lab.directory();
    std::fs::write(lab.0.join("first"), b"original-first").unwrap();
    std::fs::write(lab.0.join("witness"), b"original-witness").unwrap();
    let authority = [0x61; 32];
    let (first_fd, first_identity) =
        NativeSecureFs::pin_object(directory.as_raw_fd(), "first", authority).unwrap();
    let (witness_fd, witness_identity) =
        NativeSecureFs::pin_object(directory.as_raw_fd(), "witness", authority).unwrap();
    unsafe {
        libc::close(first_fd);
        libc::close(witness_fd);
    }
    for broker in [&first, &second] {
        broker.set_budget_policy(authority, EffectBudgetPolicy {
            max_effects: 2,
            max_total_bytes: 4096,
            allowed_targets: vec![
                (first_identity.locator.dev, first_identity.locator.ino),
                (witness_identity.locator.dev, witness_identity.locator.ino),
            ],
        }).unwrap();
    }
    let auth = AuthorityContext {
        authority_id: authority,
        epoch: first.get_epoch(),
        effect: EffectType::Mutate,
        nonce: [0x62; 32],
    };
    assert_eq!(
        first
            .secure_mutate_scoped(
                directory.as_raw_fd(),
                "first",
                &auth,
                &first_identity,
                b"committed-first"
            )
            .unwrap()
            .0,
        EffectTxState::Committed
    );
    assert_eq!(
        std::fs::read(lab.0.join("first")).unwrap(),
        b"committed-first"
    );

    let replay = second.secure_mutate_scoped(
        directory.as_raw_fd(),
        "witness",
        &auth,
        &witness_identity,
        b"replayed-effect",
    );
    // Observe the physical target independently of the broker's return value.
    let observed = std::fs::read(lab.0.join("witness")).unwrap();
    assert!(
        matches!(replay, Err(SecureFsError::NonceReplayDetected { .. }))
            && observed == b"original-witness",
        "replay result={replay:?}; independent_observation={observed:?}"
    );
}

#[test]
fn concurrent_instances_have_exactly_one_nonce_winner_after_warmup() {
    let lab = Lab::new();
    let first = lab.open();
    let second = lab.open();
    first.consume_nonce_durable(&[0x70; 32]).unwrap();
    let mut winner_counts = Vec::new();
    for round in 0..16u8 {
        let nonce = [round + 1; 32];
        let start = Arc::new(Barrier::new(2));
        let winners = std::thread::scope(|scope| {
            let first_start = Arc::clone(&start);
            let first_ref = &first;
            let one = scope.spawn(move || {
                first_start.wait();
                first_ref.consume_nonce_durable(&nonce).is_ok()
            });
            let two = scope.spawn(|| {
                start.wait();
                second.consume_nonce_durable(&nonce).is_ok()
            });
            usize::from(one.join().unwrap()) + usize::from(two.join().unwrap())
        });
        winner_counts.push(winners);
    }
    assert!(
        winner_counts.iter().all(|&count| count == 1),
        "each nonce requires one durable winner; observed={winner_counts:?}"
    );
}

#[test]
fn incomplete_nonce_record_blocks_another_live_instance_and_reopening() {
    let lab = Lab::new();
    let first = lab.open();
    let second = lab.open();
    first.consume_nonce_durable(&[0x81; 32]).unwrap();
    let path = first.quarantine.dir_path.join(".consumed_nonces.bin");
    let mut file = OpenOptions::new()
        .append(true)
        .custom_flags(libc::O_NOFOLLOW)
        .open(path)
        .unwrap();
    file.write_all(&[0x82]).unwrap();
    file.sync_all().unwrap();
    assert!(matches!(
        second.consume_nonce_durable(&[0x83; 32]),
        Err(SecureFsError::WalCorrupted(_))
    ));
    assert!(matches!(
        EffectTxOrchestrator::<NativeSecureFs>::new(&lab.0),
        Err(SecureFsError::WalCorrupted(_))
    ));
}

#[test]
fn nonce_refresh_rejects_symlinks_without_touching_the_target() {
    let lab = Lab::new();
    let first = lab.open();
    let second = lab.open();
    let target = lab.0.join("witness");
    std::fs::write(&target, b"independent-witness").unwrap();
    std::os::unix::fs::symlink(
        &target,
        first.quarantine.dir_path.join(".consumed_nonces.bin"),
    )
    .unwrap();
    assert!(second.consume_nonce_durable(&[0x91; 32]).is_err());
    assert_eq!(std::fs::read(target).unwrap(), b"independent-witness");
}

#[test]
fn separate_processes_have_exactly_one_durable_nonce_winner() {
    use std::os::unix::fs::PermissionsExt;
    use std::process::{Child, Command};
    use std::time::{Duration, Instant};
    const ROOT: &str = "BABYLON60_NONCE_PROCESS_REGRESSION_ROOT";
    const SLOT: &str = "BABYLON60_NONCE_PROCESS_REGRESSION_SLOT";
    const TEST: &str = "separate_processes_have_exactly_one_durable_nonce_winner";
    fn until(mut done: impl FnMut() -> bool) {
        let deadline = Instant::now() + Duration::from_secs(5);
        while !done() {
            assert!(
                Instant::now() < deadline,
                "nonce subprocess barrier timed out"
            );
            std::thread::sleep(Duration::from_millis(2));
        }
    }
    struct Children(Vec<Child>);
    impl Drop for Children {
        fn drop(&mut self) {
            for child in &mut self.0 {
                if matches!(child.try_wait(), Ok(None)) {
                    let _ = child.kill();
                }
                let _ = child.wait();
            }
        }
    }
    let nonce = [0xa1; 32];
    if let (Ok(root), Ok(slot)) = (std::env::var(ROOT), std::env::var(SLOT)) {
        assert!(slot == "0" || slot == "1");
        let root = PathBuf::from(root);
        let broker = EffectTxOrchestrator::<NativeSecureFs>::new(&root).unwrap();
        std::fs::write(root.join(format!("ready-{slot}")), b"ready").unwrap();
        until(|| root.join("start").is_file());
        let outcome = match broker.consume_nonce_durable(&nonce) {
            Ok(()) => "ok",
            Err(SecureFsError::NonceReplayDetected { .. }) => "replay",
            other => panic!("unexpected child outcome: {other:?}"),
        };
        std::fs::write(root.join(format!("result-{slot}")), outcome).unwrap();
        return;
    }
    let lab = Lab::new();
    std::fs::set_permissions(&lab.0, std::fs::Permissions::from_mode(0o700)).unwrap();
    // Provision the shared store before testing two already-open consumers.
    lab.open().consume_nonce_durable(&[0xa0; 32]).unwrap();
    let executable = std::env::current_exe().unwrap();
    let mut children = Children(Vec::new());
    for slot in ["0", "1"] {
        children.0.push(
            Command::new(&executable)
                .args(["--exact", TEST, "--nocapture"])
                .env(ROOT, &lab.0)
                .env(SLOT, slot)
                .spawn()
                .unwrap(),
        );
    }
    until(|| lab.0.join("ready-0").is_file() && lab.0.join("ready-1").is_file());
    std::fs::write(lab.0.join("start"), b"start").unwrap();
    for child in &mut children.0 {
        let mut status = None;
        until(|| {
            status = child.try_wait().unwrap();
            status.is_some()
        });
        assert!(status.unwrap().success(), "nonce subprocess failed");
    }
    let mut results: Vec<_> = ["0", "1"]
        .into_iter()
        .map(|slot| std::fs::read_to_string(lab.0.join(format!("result-{slot}"))).unwrap())
        .collect();
    results.sort();
    assert_eq!(results, ["ok", "replay"]);
    let ledger = std::fs::read(lab.0.join(".babylon/quarantine/.consumed_nonces.bin")).unwrap();
    assert_eq!(
        ledger, [[0xa0; 32], nonce].concat(),
        "warmup plus exactly one process must persist two 32-byte records"
    );
}
