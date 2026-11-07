//! Kill around the real macOS syscall implementing File::sync_all; never fake success.
#![cfg(target_os = "macos")]
use babylon60::secure_fs::{EffectTxOrchestrator, NativeSecureFs, SecureFsError};
use std::os::unix::fs::{DirBuilderExt, MetadataExt};
use std::os::unix::process::ExitStatusExt;
use std::path::{Path, PathBuf};
use std::process::{Child, Command};
use std::time::{Duration, Instant};

const TEST: &str = "nonce_recovery_rejects_replay_across_sigkill_at_sync_all_boundaries";
const OLD: [u8; 32] = [0xd1; 32];
const INTERRUPTED: [u8; 32] = [0xd2; 32];
const NEXT: [u8; 32] = [0xd3; 32];
type Broker = EffectTxOrchestrator<NativeSecureFs>;

fn publish(root: &Path, name: &str) {
    let temporary = root.join(format!("{name}.tmp"));
    std::fs::write(&temporary, b"ready").unwrap();
    std::fs::rename(temporary, root.join(name)).unwrap();
}
fn wait_for(mut ready: impl FnMut() -> bool) {
    let deadline = Instant::now() + Duration::from_secs(10);
    while !ready() {
        assert!(
            Instant::now() < deadline,
            "nonce persistence fixture timed out"
        );
        std::thread::sleep(Duration::from_millis(1));
    }
}
struct Lab(PathBuf);
impl Lab {
    fn new(tag: &str) -> Self {
        let path =
            std::env::temp_dir().join(format!("b60_nonce_kill_{}_{tag}", std::process::id()));
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
fn replay(broker: &Broker, nonce: &[u8; 32]) {
    assert!(matches!(broker.consume_nonce_durable(nonce),
        Err(SecureFsError::NonceReplayDetected { nonce: rejected }) if rejected == *nonce));
}
fn child(root: &Path, role: &str, seeded: bool) {
    let broker = Broker::new(&root.join("store")).unwrap();
    if role == "verify" {
        for nonce in [&INTERRUPTED, &NEXT] {
            replay(&broker, nonce);
        }
        if seeded {
            replay(&broker, &OLD);
        }
        return;
    }
    publish(root, &format!("ready-{role}"));
    wait_for(|| root.join(format!("go-{role}")).is_file());
    if role == "writer" {
        broker.consume_nonce_durable(&INTERRUPTED).unwrap();
        publish(root, "writer-returned");
        panic!("writer escaped the requested persistence boundary");
    }
    assert_eq!(role, "observer");
    replay(&broker, &INTERRUPTED); // Instance predates the interrupted write.
    if seeded {
        replay(&broker, &OLD);
    }
    broker.consume_nonce_durable(&NEXT).unwrap(); // Recovery admits fresh work.
    replay(&Broker::new(&root.join("store")).unwrap(), &INTERRUPTED);
    publish(root, "observer-returned");
}
fn spawn(root: &Path, role: &str, phase: &str, seeded: bool, shim: &Path) -> Child {
    let mut command = Command::new(std::env::current_exe().unwrap());
    command
        .args(["--exact", TEST, "--nocapture", "--test-threads=1"])
        .env("B60_NONCE_CONTROL", root)
        .env("B60_NONCE_ROLE", role)
        .env("B60_NONCE_PHASE", phase)
        .env("B60_NONCE_SEEDED", if seeded { "1" } else { "0" });
    if role == "verify" {
        command.env_remove("DYLD_INSERT_LIBRARIES");
    } else {
        command.env("DYLD_INSERT_LIBRARIES", shim);
    }
    command.spawn().unwrap()
}
fn record(root: &Path, name: &str) -> Vec<u64> {
    std::fs::read_to_string(root.join(name))
        .unwrap()
        .split_whitespace()
        .map(|value| value.parse().unwrap())
        .collect()
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
fn nonce_recovery_rejects_replay_across_sigkill_at_sync_all_boundaries() {
    if let (Ok(root), Ok(role)) = (
        std::env::var("B60_NONCE_CONTROL"),
        std::env::var("B60_NONCE_ROLE"),
    ) {
        child(
            Path::new(&root),
            &role,
            std::env::var("B60_NONCE_SEEDED").unwrap() == "1",
        );
        return;
    }
    let build = Lab::new("shim");
    let source = build.0.join("observe.c");
    let shim = build.0.join("observe.dylib");
    std::fs::write(
        &source,
        include_str!("fixtures/nonce_sync_sigkill_interpose.c"),
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
    for phase in ["before-sync", "after-sync"] {
        for seeded in [false, true] {
            // Independent roots: one warmup plus eight measured rounds per scenario.
            for round in 0..=8 {
                let lab = Lab::new(&format!("{phase}_{seeded}_{round}"));
                let store = lab.0.join("store");
                std::fs::DirBuilder::new()
                    .mode(0o700)
                    .create(&store)
                    .unwrap();
                let prepared = Broker::new(&store).unwrap();
                if seeded {
                    prepared.consume_nonce_durable(&OLD).unwrap();
                }
                drop(prepared);
                let ledger = store.join(".babylon/quarantine/.consumed_nonces.bin");
                let mut children = Children(Vec::new());
                children
                    .0
                    .push(spawn(&lab.0, "writer", phase, seeded, &shim));
                children
                    .0
                    .push(spawn(&lab.0, "observer", phase, seeded, &shim));
                wait_for(|| {
                    lab.0.join("ready-writer").is_file() && lab.0.join("ready-observer").is_file()
                });
                assert_eq!(std::fs::read(&ledger).ok(), seeded.then(|| OLD.to_vec()));
                publish(&lab.0, "go-writer");
                wait_for(|| lab.0.join(format!("writer-{phase}")).is_file());
                let writer = children.0[0].id();
                let mut status = 0;
                wait_for(|| {
                    let got = unsafe {
                        libc::waitpid(writer as i32, &mut status, libc::WUNTRACED | libc::WNOHANG)
                    };
                    assert!(got >= 0);
                    got != 0
                });
                assert!(libc::WIFSTOPPED(status));
                assert_eq!(libc::WSTOPSIG(status), libc::SIGSTOP);
                assert!(!lab.0.join("writer-returned").exists());
                assert_eq!(
                    lab.0.join("writer-after-sync").is_file(),
                    phase == "after-sync"
                );
                let expected_written = if seeded {
                    [OLD, INTERRUPTED].concat()
                } else {
                    INTERRUPTED.to_vec()
                };
                let metadata = std::fs::metadata(&ledger).unwrap();
                assert_eq!(
                    record(&lab.0, &format!("writer-{phase}")),
                    [
                        u64::from(writer),
                        metadata.dev(),
                        metadata.ino(),
                        expected_written.len() as u64
                    ]
                );
                // This observes bytes only. Before-sync does not assert power-loss durability.
                assert_eq!(std::fs::read(&ledger).unwrap(), expected_written);
                publish(&lab.0, "go-observer");
                wait_for(|| lab.0.join("observer-waiting").is_file());
                std::thread::sleep(Duration::from_millis(20));
                assert!(!lab.0.join("observer-acquired").exists());
                assert!(!lab.0.join("observer-returned").exists());
                children.0[0].kill().unwrap();
                assert_eq!(children.0[0].wait().unwrap().signal(), Some(libc::SIGKILL));
                wait_success(&mut children.0[1]);
                assert!(lab.0.join("observer-acquired").is_file());
                assert!(lab.0.join("observer-returned").is_file());
                children
                    .0
                    .push(spawn(&lab.0, "verify", phase, seeded, &shim));
                wait_success(&mut children.0[2]);
                let expected = [expected_written, NEXT.to_vec()].concat();
                assert_eq!(std::fs::read(&ledger).unwrap(), expected);
                assert_eq!(std::fs::metadata(&ledger).unwrap().ino(), metadata.ino());
                eprintln!("nonce-kill phase={phase} seeded={seeded} round={round} signal=9 recovery=ok replay=rejected durable_bytes={}", expected.len());
            }
        }
    }
}
