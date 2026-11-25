//! Real short writes plus SIGKILL: replay safety must coexist with recovery.
#![cfg(target_os = "macos")]
use babylon60::secure_fs::{
    EffectTxOrchestrator, EffectType, NativeSecureFs, SecureFsError, WalRecord, WalRecordState,
};
use std::os::unix::fs::{DirBuilderExt, MetadataExt};
use std::os::unix::process::ExitStatusExt;
use std::path::{Path, PathBuf};
use std::process::{Child, Command};
use std::time::{Duration, Instant};
const TEST: &str = "partial_nonce_recovers_after_sigkill_without_replay";
const OLD: [u8; 32] = [0xe1; 32];
const INTERRUPTED: [u8; 32] = [0xe2; 32];
const NEXT: [u8; 32] = [0xe3; 32];
type Broker = EffectTxOrchestrator<NativeSecureFs>;
fn publish(root: &Path, name: &str, value: impl AsRef<[u8]>) {
    let temporary = root.join(format!("{name}.tmp"));
    std::fs::write(&temporary, value).unwrap();
    std::fs::rename(temporary, root.join(name)).unwrap();
}
fn wait_for(mut ready: impl FnMut() -> bool) {
    let deadline = Instant::now() + Duration::from_secs(10);
    while !ready() {
        assert!(Instant::now() < deadline, "partial nonce fixture timed out");
        std::thread::sleep(Duration::from_millis(1));
    }
}
struct Lab(PathBuf);
impl Lab {
    fn new(tag: &str) -> Self {
        let path = std::env::temp_dir().join(format!("b60_partial_{}_{tag}", std::process::id()));
        std::fs::DirBuilder::new()
            .mode(0o700)
            .create(&path)
            .unwrap();
        Self(path)
    }
}
impl Drop for Lab {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.0);
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
fn replay(broker: &Broker, nonce: &[u8; 32]) -> Result<(), String> {
    match broker.consume_nonce_durable(nonce) {
        Err(SecureFsError::NonceReplayDetected { nonce: actual }) if actual == *nonce => Ok(()),
        other => Err(format!("expected replay rejection; got {other:?}")),
    }
}
fn verify(root: &Path, seeded: bool) -> Result<(), String> {
    let broker = Broker::new(&root.join("store")).map_err(|error| format!("reopen: {error:?}"))?;
    for nonce in [&INTERRUPTED, &NEXT] {
        replay(&broker, nonce)?;
    }
    if seeded {
        replay(&broker, &OLD)?;
    }
    Ok(())
}
fn child(root: &Path, role: &str, seeded: bool) {
    if role == "verify" {
        publish(root, "verify-result", format!("{:?}", verify(root, seeded)));
        return;
    }
    let broker = Broker::new(&root.join("store")).unwrap();
    publish(root, &format!("ready-{role}"), b"ready");
    wait_for(|| root.join(format!("go-{role}")).is_file());
    if role == "writer" {
        if std::env::var("B60_PARTIAL_WRITER").unwrap() == "wal" {
            broker
                .append_wal_record(WalRecord::new(
                    WalRecordState::AttemptReserved,
                    EffectType::Mutate,
                    1,
                    INTERRUPTED,
                    0,
                    0,
                    [0; 32],
                    [0; 32],
                ))
                .unwrap();
        } else {
            broker.consume_nonce_durable(&INTERRUPTED).unwrap();
        }
        publish(root, "writer-returned", b"unexpected");
        panic!("writer escaped partial append boundary");
    }
    assert_eq!(role, "observer");
    let outcome = (|| {
        replay(&broker, &INTERRUPTED)?;
        if seeded {
            replay(&broker, &OLD)?;
        }
        broker
            .consume_nonce_durable(&NEXT)
            .map_err(|error| format!("new work: {error:?}"))?;
        Ok::<(), String>(())
    })();
    publish(root, "observer-result", format!("{outcome:?}"));
}
fn spawn(root: &Path, role: &str, length: usize, seeded: bool, mode: &str, shim: &Path) -> Child {
    let mut command = Command::new(std::env::current_exe().unwrap());
    command
        .args(["--exact", TEST, "--nocapture", "--test-threads=1"])
        .env("B60_PARTIAL_CONTROL", root)
        .env("B60_PARTIAL_ROLE", role)
        .env("B60_PARTIAL_BYTES", length.to_string())
        .env("B60_PARTIAL_WRITER", mode)
        .env("B60_PARTIAL_SEEDED", if seeded { "1" } else { "0" });
    if role == "verify" {
        command.env_remove("DYLD_INSERT_LIBRARIES");
    } else {
        command.env("DYLD_INSERT_LIBRARIES", shim);
    }
    command.spawn().unwrap()
}
fn wait_success(child: &mut Child) {
    let mut status = None;
    wait_for(|| {
        status = child.try_wait().unwrap();
        status.is_some()
    });
    assert!(status.unwrap().success());
}
#[test]
fn partial_nonce_recovers_after_sigkill_without_replay() {
    if let (Ok(root), Ok(role)) = (
        std::env::var("B60_PARTIAL_CONTROL"),
        std::env::var("B60_PARTIAL_ROLE"),
    ) {
        child(
            Path::new(&root),
            &role,
            std::env::var("B60_PARTIAL_SEEDED").unwrap() == "1",
        );
        return;
    }
    let build = Lab::new("shim");
    let source = build.0.join("observe.c");
    let shim = build.0.join("observe.dylib");
    std::fs::write(
        &source,
        include_str!("fixtures/partial_nonce_sigkill_interpose.c"),
    )
    .unwrap();
    let compiler = Command::new("cc")
        .args(["-dynamiclib", "-O2", "-Wall", "-Wextra", "-Werror"])
        .arg(&source)
        .arg("-o")
        .arg(&shim)
        .output()
        .unwrap();
    assert!(
        compiler.status.success(),
        "{}",
        String::from_utf8_lossy(&compiler.stderr)
    );
    let mut failures = Vec::new();
    for mode in ["direct", "wal"] {
        for length in [1, 16, 31] {
            for seeded in [false, true] {
                // One warmup and four measured fresh stores per scenario.
                for round in 0..=4 {
                    let lab = Lab::new(&format!("{mode}_{length}_{seeded}_{round}"));
                    let store = lab.0.join("store");
                    std::fs::DirBuilder::new()
                        .mode(0o700)
                        .create(&store)
                        .unwrap();
                    let broker = Broker::new(&store).unwrap();
                    if seeded {
                        broker.consume_nonce_durable(&OLD).unwrap();
                    }
                    drop(broker);
                    let ledger = store.join(".babylon/quarantine/.consumed_nonces.bin");
                    let mut children = Children(Vec::new());
                    children
                        .0
                        .push(spawn(&lab.0, "writer", length, seeded, mode, &shim));
                    children
                        .0
                        .push(spawn(&lab.0, "observer", length, seeded, mode, &shim));
                    wait_for(|| {
                        lab.0.join("ready-writer").is_file()
                            && lab.0.join("ready-observer").is_file()
                    });
                    publish(&lab.0, "go-writer", b"go");
                    wait_for(|| lab.0.join("writer-partial").is_file());
                    let writer = children.0[0].id();
                    let mut status = 0;
                    wait_for(|| {
                        let got = unsafe {
                            libc::waitpid(
                                writer as i32,
                                &mut status,
                                libc::WUNTRACED | libc::WNOHANG,
                            )
                        };
                        assert!(got >= 0);
                        got != 0
                    });
                    assert!(libc::WIFSTOPPED(status));
                    assert_eq!(libc::WSTOPSIG(status), libc::SIGSTOP);
                    assert!(!lab.0.join("writer-returned").exists());
                    let mut partial = if seeded { OLD.to_vec() } else { Vec::new() };
                    partial.extend_from_slice(&INTERRUPTED[..length]);
                    assert_eq!(std::fs::read(&ledger).unwrap(), partial);
                    let metadata = std::fs::metadata(&ledger).unwrap();
                    let record: Vec<u64> = std::fs::read_to_string(lab.0.join("writer-partial"))
                        .unwrap()
                        .split_whitespace()
                        .map(|value| value.parse().unwrap())
                        .collect();
                    assert_eq!(
                        record,
                        [
                            u64::from(writer),
                            metadata.dev(),
                            metadata.ino(),
                            partial.len() as u64
                        ]
                    );
                    children.0[0].kill().unwrap();
                    assert_eq!(children.0[0].wait().unwrap().signal(), Some(libc::SIGKILL));
                    publish(&lab.0, "go-observer", b"go");
                    wait_success(&mut children.0[1]);
                    children
                        .0
                        .push(spawn(&lab.0, "verify", length, seeded, mode, &shim));
                    wait_success(&mut children.0[2]);
                    let observer = std::fs::read_to_string(lab.0.join("observer-result")).unwrap();
                    let verify = std::fs::read_to_string(lab.0.join("verify-result")).unwrap();
                    let bytes = std::fs::read(&ledger).unwrap();
                    let expected = if seeded {
                        [OLD, INTERRUPTED, NEXT].concat()
                    } else {
                        [INTERRUPTED, NEXT].concat()
                    };
                    let ok = observer == "Ok(())" && verify == "Ok(())" && bytes == expected;
                    eprintln!("partial-nonce mode={mode} bytes={length} seeded={seeded} round={round} signal=9 ok={ok} observer={observer} verify={verify} ledger_bytes={}", bytes.len());
                    if !ok {
                        failures.push((length, seeded, round, observer, verify, bytes));
                    }
                }
            }
        }
    }
    assert!(
        failures.is_empty(),
        "partial nonce recovery failures: {failures:?}"
    );
}

#[test]
fn nonce_intent_recovers_before_append_and_after_complete_append() {
    use std::io::Write;
    for length in [0, 32] {
        let lab = Lab::new(&format!("intent_{length}"));
        let broker = Broker::new(&lab.0).unwrap();
        broker.consume_nonce_durable(&OLD).unwrap();
        let quarantine = broker.quarantine.dir_path.clone();
        drop(broker);
        let ledger = quarantine.join(".consumed_nonces.bin");
        let mut file = std::fs::OpenOptions::new()
            .append(true)
            .open(&ledger)
            .unwrap();
        file.write_all(&INTERRUPTED[..length]).unwrap();
        file.sync_all().unwrap();
        let intent = quarantine.join(format!(".nonce_intent_{}", hex::encode(INTERRUPTED)));
        std::fs::File::create(&intent).unwrap().sync_all().unwrap();
        let recovered = Broker::new(&lab.0).unwrap();
        replay(&recovered, &INTERRUPTED).unwrap();
        replay(&recovered, &OLD).unwrap();
        assert_eq!(std::fs::read(ledger).unwrap(), [OLD, INTERRUPTED].concat());
        assert!(!intent.exists());
        replay(&Broker::new(&lab.0).unwrap(), &INTERRUPTED).unwrap();
    }
}

#[test]
fn invalid_nonce_intents_do_not_repair_or_erase_corrupt_evidence() {
    use std::io::Write;
    for case in [
        "mismatch",
        "multiple",
        "malformed",
        "symlink",
        "nonempty",
        "wal",
    ] {
        let lab = Lab::new(case);
        let broker = Broker::new(&lab.0).unwrap();
        broker.consume_nonce_durable(&OLD).unwrap();
        let quarantine = broker.quarantine.dir_path.clone();
        drop(broker);
        let ledger = quarantine.join(".consumed_nonces.bin");
        let tail = if case == "mismatch" {
            [0xff; 16]
        } else {
            [0xe2; 16]
        };
        let mut file = std::fs::OpenOptions::new()
            .append(true)
            .open(&ledger)
            .unwrap();
        file.write_all(&tail).unwrap();
        file.sync_all().unwrap();
        let before = std::fs::read(&ledger).unwrap();
        if case == "wal" {
            std::fs::write(quarantine.join(".effect_wal.bin"), [0; 154]).unwrap();
        }
        let intent = quarantine.join(format!(".nonce_intent_{}", hex::encode(INTERRUPTED)));
        let witness = lab.0.join("independent-witness");
        std::fs::write(&witness, b"untouched").unwrap();
        match case {
            "malformed" => {
                std::fs::write(quarantine.join(".nonce_intent_bad"), []).unwrap();
            }
            "symlink" => {
                std::os::unix::fs::symlink(&witness, &intent).unwrap();
            }
            "nonempty" => {
                std::fs::write(&intent, b"untrusted").unwrap();
            }
            _ => {
                std::fs::write(&intent, []).unwrap();
                if case == "multiple" {
                    std::fs::write(
                        quarantine.join(format!(".nonce_intent_{}", hex::encode(NEXT))),
                        [],
                    )
                    .unwrap();
                }
            }
        }
        assert!(Broker::new(&lab.0).is_err(), "accepted {case}");
        assert_eq!(std::fs::read(&ledger).unwrap(), before);
        assert_eq!(std::fs::read(witness).unwrap(), b"untouched");
        assert_eq!(
            std::fs::read_dir(&quarantine)
                .unwrap()
                .filter(|entry| entry
                    .as_ref()
                    .unwrap()
                    .file_name()
                    .to_string_lossy()
                    .starts_with(".nonce_intent_"))
                .count(),
            if case == "multiple" { 2 } else { 1 }
        );
    }
}
