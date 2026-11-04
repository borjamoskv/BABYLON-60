//! Two real processes start against a fresh store; barriers live outside it.
use babylon60::secure_fs::{EffectTxOrchestrator, NativeSecureFs, SecureFsError};
use std::os::unix::fs::DirBuilderExt;
use std::path::{Path, PathBuf};
use std::process::{Child, Command};
use std::time::{Duration, Instant};

const TEST: &str = "cold_start_processes_initialize_and_share_one_nonce";
const CONTROL_ENV: &str = "BABYLON60_COLD_START_CONTROL";
const SLOT_ENV: &str = "BABYLON60_COLD_START_SLOT";

fn publish(control: &Path, name: &str, contents: impl AsRef<[u8]>) {
    let temporary = control.join(format!("{name}.tmp"));
    std::fs::write(&temporary, contents).unwrap();
    std::fs::rename(temporary, control.join(name)).unwrap();
}

fn wait_for(mut condition: impl FnMut() -> bool) {
    let deadline = Instant::now() + Duration::from_secs(10);
    while !condition() {
        assert!(Instant::now() < deadline, "cold-start barrier timed out");
        std::thread::sleep(Duration::from_millis(1));
    }
}

struct Lab(PathBuf);
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

fn child(control: &Path, slot: &str) {
    assert!(slot == "0" || slot == "1");
    publish(control, &format!("ready-{slot}"), b"ready");
    wait_for(|| control.join("start").is_file());
    // Neither child constructs a broker until both have reached the start barrier.
    let broker = EffectTxOrchestrator::<NativeSecureFs>::new(&control.join("store"));
    let opened = match &broker {
        Ok(_) => "ok".to_owned(),
        Err(error) => format!("error: {error:?}"),
    };
    publish(control, &format!("opened-{slot}"), &opened);
    wait_for(|| control.join("opened-0").is_file() && control.join("opened-1").is_file());
    let peer_opened = std::fs::read_to_string(
        control.join(format!("opened-{}", 1 - slot.parse::<u8>().unwrap())),
    )
    .unwrap();
    let outcome = match broker {
        Ok(broker) if peer_opened == "ok" => match broker.consume_nonce_durable(&[0xb1; 32]) {
            Ok(()) => "ok".to_owned(),
            Err(SecureFsError::NonceReplayDetected { .. }) => "replay".to_owned(),
            other => format!("consume-error: {other:?}"),
        },
        _ => "startup-error".to_owned(),
    };
    publish(control, &format!("result-{slot}"), outcome);
}

#[test]
fn cold_start_processes_initialize_and_share_one_nonce() {
    if let (Ok(control), Ok(slot)) = (std::env::var(CONTROL_ENV), std::env::var(SLOT_ENV)) {
        child(Path::new(&control), &slot);
        return;
    }
    let executable = std::env::current_exe().unwrap();
    let mut failures = Vec::new();
    // Round zero warms the process/filesystem path in a separate empty store.
    for round in 0..=32 {
        let lab = Lab(std::env::temp_dir().join(format!(
            "b60_cold_start_{}_{}",
            std::process::id(),
            round
        )));
        std::fs::DirBuilder::new()
            .mode(0o700)
            .create(&lab.0)
            .unwrap();
        let store = lab.0.join("store");
        std::fs::DirBuilder::new()
            .mode(0o700)
            .create(&store)
            .unwrap();
        let mut children = Children(Vec::new());
        for slot in ["0", "1"] {
            children.0.push(
                Command::new(&executable)
                    .args(["--exact", TEST, "--nocapture", "--test-threads=1"])
                    .env(CONTROL_ENV, &lab.0)
                    .env(SLOT_ENV, slot)
                    .spawn()
                    .unwrap(),
            );
        }
        wait_for(|| lab.0.join("ready-0").is_file() && lab.0.join("ready-1").is_file());
        assert_eq!(
            std::fs::read_dir(&store).unwrap().count(),
            0,
            "store was provisioned before cold start"
        );
        publish(&lab.0, "start", b"start");
        for process in &mut children.0 {
            let mut status = None;
            wait_for(|| {
                status = process.try_wait().unwrap();
                status.is_some()
            });
            assert!(status.unwrap().success(), "cold-start child failed");
        }
        let opened: Vec<_> = ["0", "1"]
            .into_iter()
            .map(|slot| std::fs::read_to_string(lab.0.join(format!("opened-{slot}"))).unwrap())
            .collect();
        let mut results: Vec<_> = ["0", "1"]
            .into_iter()
            .map(|slot| std::fs::read_to_string(lab.0.join(format!("result-{slot}"))).unwrap())
            .collect();
        results.sort();
        // Observe persisted bytes independently of either child's return value.
        let durable = std::fs::read(store.join(".babylon/quarantine/.consumed_nonces.bin")).ok();
        eprintln!(
            "cold-start round={round} opened={opened:?} outcomes={results:?} durable_bytes={:?}",
            durable.as_ref().map(Vec::len)
        );
        if opened != ["ok", "ok"]
            || results != ["ok", "replay"]
            || durable.as_deref() != Some(&[0xb1; 32])
        {
            failures.push((round, opened, results, durable));
        }
    }
    assert!(failures.is_empty(), "cold-start failures: {failures:?}");
}

#[test]
fn existing_fence_symlink_is_rejected_without_touching_target() {
    let lab = Lab(std::env::temp_dir().join(format!("b60_fence_symlink_{}", std::process::id())));
    std::fs::DirBuilder::new()
        .mode(0o700)
        .create(&lab.0)
        .unwrap();
    let quarantine = lab.0.join(".babylon/quarantine");
    std::fs::create_dir_all(&quarantine).unwrap();
    let target = lab.0.join("outside-fence");
    let original = [0xa5; 8];
    std::fs::write(&target, original).unwrap();
    let fence = quarantine.join(".epoch_fence.bin");
    std::os::unix::fs::symlink(&target, &fence).unwrap();

    assert!(matches!(
        EffectTxOrchestrator::<NativeSecureFs>::new(&lab.0),
        Err(SecureFsError::IoError(error)) if error.raw_os_error() == Some(libc::ELOOP)
    ));
    assert_eq!(std::fs::read(target).unwrap(), original);
    assert!(std::fs::symlink_metadata(fence)
        .unwrap()
        .file_type()
        .is_symlink());
    assert!(!quarantine.join(".consumed_nonces.bin").exists());
}
