//! macOS fault injection observes real openat/flock without changing production code.
#![cfg(target_os = "macos")]
use babylon60::secure_fs::{EffectTxOrchestrator, NativeSecureFs, SecureFsError};
use std::os::unix::fs::{DirBuilderExt, MetadataExt};
use std::os::unix::process::ExitStatusExt;
use std::path::{Path, PathBuf};
use std::process::{Child, Command};
use std::time::{Duration, Instant};

const TEST: &str = "survivor_recovers_when_fence_creator_is_sigkilled_during_startup";
const OLD: [u8; 32] = [0xc1; 32];
const NEW: [u8; 32] = [0xc2; 32];
type Broker = EffectTxOrchestrator<NativeSecureFs>;

fn publish(root: &Path, name: &str) {
    let temporary = root.join(format!("{name}.tmp"));
    std::fs::write(&temporary, b"ready").unwrap();
    std::fs::rename(temporary, root.join(name)).unwrap();
}
fn wait_for(mut ready: impl FnMut() -> bool) {
    let deadline = Instant::now() + Duration::from_secs(10);
    while !ready() {
        assert!(Instant::now() < deadline, "SIGKILL fixture timed out");
        std::thread::sleep(Duration::from_millis(1));
    }
}
struct Lab(PathBuf);
impl Lab {
    fn new(tag: &str) -> Self {
        let path = std::env::temp_dir().join(format!("b60_sigkill_{}_{tag}", std::process::id()));
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
    if role == "verify" {
        let broker = Broker::new(&root.join("store")).unwrap();
        replay(&broker, &NEW);
        if seeded {
            replay(&broker, &OLD);
        }
        return;
    }
    publish(root, &format!("ready-{role}"));
    wait_for(|| root.join(format!("start-{role}")).is_file());
    let broker = Broker::new(&root.join("store")).unwrap();
    publish(root, &format!("returned-{role}"));
    assert_eq!(role, "survivor", "creator escaped the injection point");
    wait_for(|| root.join("consume").is_file());
    if seeded {
        replay(&broker, &OLD);
    }
    broker.consume_nonce_durable(&NEW).unwrap();
    replay(&broker, &NEW);
    replay(&Broker::new(&root.join("store")).unwrap(), &NEW);
}
fn spawn(root: &Path, role: &str, phase: &str, seeded: bool, shim: &Path) -> Child {
    let mut command = Command::new(std::env::current_exe().unwrap());
    command
        .args(["--exact", TEST, "--nocapture", "--test-threads=1"])
        .env("B60_KILL_CONTROL", root)
        .env("B60_KILL_ROLE", role)
        .env("B60_KILL_PHASE", phase)
        .env("B60_KILL_SEEDED", if seeded { "1" } else { "0" });
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

#[test]
fn survivor_recovers_when_fence_creator_is_sigkilled_during_startup() {
    if let (Ok(root), Ok(role)) = (
        std::env::var("B60_KILL_CONTROL"),
        std::env::var("B60_KILL_ROLE"),
    ) {
        child(
            Path::new(&root),
            &role,
            std::env::var("B60_KILL_SEEDED").unwrap() == "1",
        );
        return;
    }
    let build = Lab::new("shim");
    let source = build.0.join("observe.c");
    let shim = build.0.join("observe.dylib");
    std::fs::write(
        &source,
        include_str!("fixtures/startup_sigkill_interpose.c"),
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
    for phase in ["created", "locked"] {
        for seeded in [false, true] {
            // One warmup and eight measured, independent stores per scenario.
            for round in 0..=8 {
                let lab = Lab::new(&format!("{phase}_{seeded}_{round}"));
                let store = lab.0.join("store");
                std::fs::DirBuilder::new()
                    .mode(0o700)
                    .create(&store)
                    .unwrap();
                let fence = store.join(".babylon/quarantine/.epoch_fence.bin");
                let ledger = store.join(".babylon/quarantine/.consumed_nonces.bin");
                if seeded {
                    let broker = Broker::new(&store).unwrap();
                    broker.consume_nonce_durable(&OLD).unwrap();
                    drop(broker);
                    // Recovery fixture: durable nonce remains, fence must be recreated.
                    std::fs::remove_file(&fence).unwrap();
                    assert_eq!(std::fs::read(&ledger).unwrap(), OLD);
                } else {
                    assert_eq!(std::fs::read_dir(&store).unwrap().count(), 0);
                }
                let mut children = Children(Vec::new());
                children
                    .0
                    .push(spawn(&lab.0, "creator", phase, seeded, &shim));
                children
                    .0
                    .push(spawn(&lab.0, "survivor", phase, seeded, &shim));
                wait_for(|| {
                    lab.0.join("ready-creator").is_file() && lab.0.join("ready-survivor").is_file()
                });
                publish(&lab.0, "start-creator");
                let boundary = if phase == "created" {
                    "creator-created"
                } else {
                    "creator-acquired"
                };
                wait_for(|| lab.0.join(boundary).is_file());
                let creator = children.0[0].id();
                let mut status = 0;
                wait_for(|| {
                    let got = unsafe {
                        libc::waitpid(creator as i32, &mut status, libc::WUNTRACED | libc::WNOHANG)
                    };
                    assert!(got >= 0);
                    got != 0
                });
                assert!(libc::WIFSTOPPED(status));
                assert_eq!(libc::WSTOPSIG(status), libc::SIGSTOP);
                assert!(!lab.0.join("returned-creator").exists());
                let metadata = std::fs::metadata(&fence).unwrap();
                assert_eq!(
                    record(&lab.0, "creator-created"),
                    [u64::from(creator), metadata.dev(), metadata.ino()]
                );
                publish(&lab.0, "start-survivor");
                wait_for(|| lab.0.join("survivor-waiting").is_file());
                assert_eq!(
                    &record(&lab.0, "survivor-waiting")[1..],
                    &[metadata.dev(), metadata.ino()]
                );
                if phase == "locked" {
                    std::thread::sleep(Duration::from_millis(20));
                    assert!(!lab.0.join("survivor-acquired").exists());
                    assert!(!lab.0.join("returned-survivor").exists());
                }
                assert_eq!(std::fs::read(&ledger).ok(), seeded.then(|| OLD.to_vec()));
                children.0[0].kill().unwrap(); // SIGKILL on Unix, confirmed below.
                assert_eq!(children.0[0].wait().unwrap().signal(), Some(libc::SIGKILL));
                publish(&lab.0, "consume");
                let mut survivor_status = None;
                wait_for(|| {
                    survivor_status = children.0[1].try_wait().unwrap();
                    survivor_status.is_some()
                });
                assert!(survivor_status.unwrap().success());
                assert!(lab.0.join("returned-survivor").exists());
                assert_eq!(
                    record(&lab.0, "survivor-acquired"),
                    [
                        u64::from(children.0[1].id()),
                        metadata.dev(),
                        metadata.ino()
                    ]
                );
                children
                    .0
                    .push(spawn(&lab.0, "verify", phase, seeded, &shim));
                let mut verify_status = None;
                wait_for(|| {
                    verify_status = children.0[2].try_wait().unwrap();
                    verify_status.is_some()
                });
                assert!(verify_status.unwrap().success());
                let expected = if seeded {
                    [OLD, NEW].concat()
                } else {
                    NEW.to_vec()
                };
                assert_eq!(std::fs::read(&ledger).unwrap(), expected);
                assert_eq!(std::fs::metadata(&fence).unwrap().ino(), metadata.ino());
                eprintln!("sigkill phase={phase} seeded={seeded} round={round} signal=9 survivor=ok replay=rejected durable_bytes={}", expected.len());
            }
        }
    }
}
