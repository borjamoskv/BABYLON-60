//! FL-PATH-01: observe returned bytes, not just path validation decisions.

use babylon60::capability::ScopedHandle;
use babylon_skills_mcp::{read_bytes_from_root, read_bytes_nofollow, ImmutableSkillsSnapshot};
use std::fs;
use std::io;
use std::os::unix::ffi::OsStrExt;
use std::os::unix::fs::symlink;
use std::path::{Component, Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{mpsc, Arc};
use std::thread::{self, JoinHandle};
use std::time::Instant;

const OUTSIDE: &[u8] = b"FL-PATH-01-OUTSIDE-CANARY-DO-NOT-READ";
const ALLOWED: &[u8] = b"FL-PATH-01-AUTHORIZED-RESOURCE";

#[test]
fn configured_read_rejects_a_symlink_parent_before_returning_outside_bytes() {
    let lab = tempfile::tempdir().unwrap();
    let allowed = lab.path().join("allowed");
    let outside = lab.path().join("outside");
    fs::create_dir(&allowed).unwrap();
    fs::create_dir(&outside).unwrap();
    fs::write(outside.join("secret"), OUTSIDE).unwrap();
    symlink(&outside, allowed.join("link")).unwrap();

    let result = read_bytes_nofollow(&allowed.join("link/secret"));
    let leaked = result.as_ref().is_ok_and(|bytes| bytes == OUTSIDE);
    assert!(
        result.is_err() && !leaked,
        "symlink parent read returned outside canary: {leaked}; result={result:?}"
    );
    assert_eq!(fs::read(outside.join("secret")).unwrap(), OUTSIDE);
}

struct Lab {
    _temporary: tempfile::TempDir,
    root: PathBuf,
    outside: PathBuf,
    sibling: PathBuf,
}

impl Lab {
    fn new() -> Self {
        let temporary = tempfile::tempdir().unwrap();
        let root = temporary.path().join("allowed");
        let outside = temporary.path().join("outside");
        let sibling = temporary.path().join("allowed-sibling");
        for directory in [&root, &outside, &sibling] {
            fs::create_dir(directory).unwrap();
        }
        fs::write(root.join("safe"), ALLOWED).unwrap();
        fs::write(outside.join("secret"), OUTSIDE).unwrap();
        fs::write(sibling.join("secret"), OUTSIDE).unwrap();
        Self {
            _temporary: temporary,
            root,
            outside,
            sibling,
        }
    }

    fn pin(&self) -> ScopedHandle {
        ScopedHandle::new(&self.root, [0x61; 32]).unwrap()
    }

    fn race_directory(&self) {
        fs::create_dir(self.root.join("race")).unwrap();
        fs::write(self.root.join("race/secret"), ALLOWED).unwrap();
    }
}

fn populate_skill(root: &Path, name: &str, bytes: &[u8]) {
    let directory = root.join(name);
    fs::create_dir_all(directory.join("nested")).unwrap();
    fs::write(
        directory.join("SKILL.md"),
        format!("---\nname: {name}\nrole: auditor\n---\n# {name}\n"),
    )
    .unwrap();
    fs::write(directory.join("nested/evidence.txt"), bytes).unwrap();
}

fn assert_snapshot_is_authorized(root: &ScopedHandle) {
    let snapshot = ImmutableSkillsSnapshot::load_from_root(None, Some(root), Some(1))
        .expect("the retained directory capability must still load");
    assert_eq!(snapshot.total_skills(), 1);
    assert_eq!(
        snapshot
            .read_resource("skill://alpha/nested/evidence.txt")
            .unwrap()
            .text
            .as_bytes(),
        ALLOWED
    );
    assert!(snapshot
        .read_resource("skill://intruder/SKILL.md")
        .is_none());
}

#[test]
fn held_root_keeps_its_identity_after_rename_and_textual_path_replacement() {
    let lab = Lab::new();
    populate_skill(&lab.root, "alpha", ALLOWED);
    populate_skill(&lab.outside, "alpha", OUTSIDE);
    populate_skill(&lab.outside, "intruder", OUTSIDE);
    let root = lab.pin();
    let retained = lab._temporary.path().join("retained-authorized-root");
    fs::rename(&lab.root, &retained).unwrap();
    symlink(&lab.outside, &lab.root).unwrap();

    // Every load must enumerate the held directory with its own stream offset.
    for _ in 0..3 {
        assert_snapshot_is_authorized(&root);
    }
    thread::scope(|scope| {
        for _ in 0..4 {
            let root = &root;
            scope.spawn(move || {
                for _ in 0..8 {
                    assert_snapshot_is_authorized(root);
                }
            });
        }
    });
    assert_eq!(
        fs::read(retained.join("alpha/nested/evidence.txt")).unwrap(),
        ALLOWED
    );
}

#[test]
fn explicitly_granted_child_directory_keeps_authority_when_renamed() {
    let lab = Lab::new();
    lab.race_directory();
    let child = ScopedHandle::new(&lab.root.join("race"), [0x62; 32]).unwrap();
    let retained = lab._temporary.path().join("retained-child");
    fs::rename(lab.root.join("race"), &retained).unwrap();
    symlink(&lab.outside, lab.root.join("race")).unwrap();
    assert_eq!(
        read_bytes_from_root(&child, Path::new("secret")).unwrap(),
        ALLOWED
    );
    assert!(read_bytes_from_root(&lab.pin(), Path::new("race/secret")).is_err());
}

#[test]
fn descendant_reads_reject_symlinks_traversal_absolute_paths_and_prefix_collisions() {
    let lab = Lab::new();
    let root = lab.pin();
    symlink(lab.outside.join("secret"), lab.root.join("leaf")).unwrap();
    symlink(&lab.outside, lab.root.join("link")).unwrap();
    for path in [
        PathBuf::from("leaf"),
        PathBuf::from("link/secret"),
        PathBuf::from("../allowed-sibling/secret"),
        PathBuf::from("safe/../../allowed-sibling/secret"),
        lab.sibling.join("secret"),
    ] {
        let result = read_bytes_from_root(&root, &path);
        assert!(result.is_err(), "escaped descendant {path:?}: {result:?}");
    }
    assert_eq!(
        read_bytes_from_root(&root, Path::new("safe")).unwrap(),
        ALLOWED
    );
    assert_eq!(fs::read(lab.outside.join("secret")).unwrap(), OUTSIDE);
}

enum SwapCommand {
    Install,
    Restore,
    Stop,
}

/// Owns the attacker thread and restores the fixture even when a reader panics.
struct ScheduledSwap {
    command: mpsc::Sender<SwapCommand>,
    acknowledged: mpsc::Receiver<()>,
    worker: Option<JoinHandle<()>>,
}

impl ScheduledSwap {
    fn new(root: &Path, outside: &Path) -> Self {
        let race = root.join("race");
        let parked = root.join("race-parked");
        let outside = outside.to_owned();
        let (command, commands) = mpsc::channel();
        let (acknowledge, acknowledged) = mpsc::channel();
        let worker = thread::spawn(move || {
            let mut installed = false;
            while let Ok(command) = commands.recv() {
                match command {
                    SwapCommand::Install => {
                        fs::rename(&race, &parked).unwrap();
                        symlink(&outside, &race).unwrap();
                        installed = true;
                    }
                    SwapCommand::Restore => {
                        fs::remove_file(&race).unwrap();
                        fs::rename(&parked, &race).unwrap();
                        installed = false;
                    }
                    SwapCommand::Stop => break,
                }
                if acknowledge.send(()).is_err() {
                    break;
                }
            }
            if installed {
                fs::remove_file(&race).unwrap();
                fs::rename(&parked, &race).unwrap();
            }
        });
        Self {
            command,
            acknowledged,
            worker: Some(worker),
        }
    }

    fn perform(&self, command: SwapCommand) {
        self.command.send(command).unwrap();
        self.acknowledged.recv().unwrap();
    }

    fn finish(mut self) {
        self.command.send(SwapCommand::Stop).unwrap();
        self.worker.take().unwrap().join().unwrap();
    }
}

impl Drop for ScheduledSwap {
    fn drop(&mut self) {
        let _ = self.command.send(SwapCommand::Stop);
        if let Some(worker) = self.worker.take() {
            let _ = worker.join();
        }
    }
}

struct RacingSwap {
    stop: Arc<AtomicBool>,
    worker: Option<JoinHandle<()>>,
}

impl RacingSwap {
    fn new(root: &Path, outside: &Path) -> Self {
        let race = root.join("race");
        let parked = root.join("race-parked");
        let outside = outside.to_owned();
        let stop = Arc::new(AtomicBool::new(false));
        let stopping = Arc::clone(&stop);
        let (ready, started) = mpsc::channel();
        let worker = thread::spawn(move || {
            let mut first = true;
            loop {
                fs::rename(&race, &parked).unwrap();
                symlink(&outside, &race).unwrap();
                if first {
                    let _ = ready.send(());
                    first = false;
                }
                thread::yield_now();
                fs::remove_file(&race).unwrap();
                fs::rename(&parked, &race).unwrap();
                if stopping.load(Ordering::Acquire) {
                    break;
                }
                thread::yield_now();
            }
        });
        started.recv().unwrap();
        Self {
            stop,
            worker: Some(worker),
        }
    }

    fn finish(mut self) {
        self.stop.store(true, Ordering::Release);
        self.worker.take().unwrap().join().unwrap();
    }
}

impl Drop for RacingSwap {
    fn drop(&mut self) {
        self.stop.store(true, Ordering::Release);
        if let Some(worker) = self.worker.take() {
            let _ = worker.join();
        }
    }
}

#[test]
fn free_running_intermediate_swaps_never_return_outside_bytes() {
    let lab = Lab::new();
    lab.race_directory();
    let root = lab.pin();
    assert_eq!(
        read_bytes_from_root(&root, Path::new("race/secret")).unwrap(),
        ALLOWED
    );
    let attacker = RacingSwap::new(&lab.root, &lab.outside);
    for _ in 0..2000 {
        if let Ok(bytes) = read_bytes_from_root(&root, Path::new("race/secret")) {
            assert_eq!(bytes, ALLOWED, "an outside canary crossed the capability");
        }
    }
    attacker.finish();
    assert_eq!(
        read_bytes_from_root(&root, Path::new("race/secret")).unwrap(),
        ALLOWED
    );
    assert_eq!(fs::read(lab.outside.join("secret")).unwrap(), OUTSIDE);
}

#[test]
fn snapshot_ingestion_does_not_publish_canaries_during_concurrent_skill_swaps() {
    let lab = Lab::new();
    populate_skill(&lab.root, "race", ALLOWED);
    fs::write(lab.root.join("race/secret"), ALLOWED).unwrap();
    fs::create_dir(lab.outside.join("nested")).unwrap();
    fs::write(
        lab.outside.join("SKILL.md"),
        format!(
            "---\nname: race\nrole: auditor\n---\n{}",
            String::from_utf8_lossy(OUTSIDE)
        ),
    )
    .unwrap();
    fs::write(lab.outside.join("nested/evidence.txt"), OUTSIDE).unwrap();
    let root = lab.pin();
    let attacker = RacingSwap::new(&lab.root, &lab.outside);
    for _ in 0..256 {
        if let Ok(snapshot) = ImmutableSkillsSnapshot::load_from_root(None, Some(&root), None) {
            for resource in ["SKILL.md", "secret", "nested/evidence.txt"] {
                if let Some(read) = snapshot.read_resource(&format!("skill://race/{resource}")) {
                    assert!(
                        !read.text.contains(std::str::from_utf8(OUTSIDE).unwrap()),
                        "outside resource published during ingestion: {resource}"
                    );
                }
            }
        }
    }
    attacker.finish();
    let snapshot = ImmutableSkillsSnapshot::load_from_root(None, Some(&root), Some(1)).unwrap();
    assert_eq!(
        snapshot
            .read_resource("skill://race/nested/evidence.txt")
            .unwrap()
            .text
            .as_bytes(),
        ALLOWED
    );
}

fn prefix_model(root: &Path, candidate: &Path) -> io::Result<Vec<u8>> {
    if !candidate
        .as_os_str()
        .as_bytes()
        .starts_with(root.as_os_str().as_bytes())
    {
        return Err(io::Error::from(io::ErrorKind::PermissionDenied));
    }
    fs::read(candidate)
}

fn component_model(root: &Path, candidate: &Path) -> io::Result<Vec<u8>> {
    let relative = candidate
        .strip_prefix(root)
        .map_err(|_| io::Error::from(io::ErrorKind::PermissionDenied))?;
    if relative.components().any(|component| {
        matches!(
            component,
            Component::ParentDir | Component::RootDir | Component::Prefix(_)
        )
    }) {
        return Err(io::Error::from(io::ErrorKind::PermissionDenied));
    }
    fs::read(candidate)
}

#[test]
fn ten_thousand_operations_measure_actual_bytes_and_legitimate_reads() {
    const WARMUP: usize = 100;
    const MEASURED: usize = 10_000;
    let lab = Lab::new();
    lab.race_directory();
    symlink(&lab.outside, lab.root.join("link")).unwrap();
    let root = lab.pin();
    let attacker = ScheduledSwap::new(&lab.root, &lab.outside);
    let mut unauthorized_reads = [0usize; 3];
    let mut unauthorized_bytes = [0usize; 3];
    let mut legitimate_success = 0;
    let mut false_rejections = 0;
    let mut c_rejections = 0;
    let mut prefix_bypasses = 0;
    let mut symlink_escapes = 0;
    let mut latencies = Vec::with_capacity(MEASURED);
    for iteration in 0..WARMUP + MEASURED {
        let kind = iteration % 4;
        let (candidate, relative) = match kind {
            0 => (lab.root.join("safe"), PathBuf::from("safe")),
            1 => (
                lab.sibling.join("secret"),
                PathBuf::from("../allowed-sibling/secret"),
            ),
            2 => (lab.root.join("link/secret"), PathBuf::from("link/secret")),
            _ => {
                // This reproduces the loader's former check/open window:
                // a directory was observed before the other thread replaces it.
                assert!(fs::symlink_metadata(lab.root.join("race"))
                    .unwrap()
                    .is_dir());
                attacker.perform(SwapCommand::Install);
                (lab.root.join("race/secret"), PathBuf::from("race/secret"))
            }
        };
        let a = prefix_model(&lab.root, &candidate);
        let b = component_model(&lab.root, &candidate);
        let began = Instant::now();
        let c = read_bytes_from_root(&root, &relative);
        let elapsed = began.elapsed().as_nanos();
        if kind == 3 {
            attacker.perform(SwapCommand::Restore);
        }
        if iteration < WARMUP {
            continue;
        }
        latencies.push(elapsed);
        c_rejections += usize::from(c.is_err());
        if kind == 0 {
            legitimate_success += usize::from(c.as_ref().is_ok_and(|bytes| bytes == ALLOWED));
            false_rejections += usize::from(c.is_err());
        }
        prefix_bypasses += usize::from(kind == 1 && c.is_ok());
        symlink_escapes += usize::from((kind == 2 || kind == 3) && c.is_ok());
        for (policy, result) in [a, b, c].into_iter().enumerate() {
            if let Ok(bytes) = result {
                if bytes != ALLOWED {
                    assert_eq!(bytes, OUTSIDE, "fixture returned unexpected content");
                    unauthorized_reads[policy] += 1;
                    unauthorized_bytes[policy] += bytes.len();
                }
            }
        }
    }
    attacker.finish();
    latencies.sort_unstable();
    let p99 = latencies[(MEASURED * 99).div_ceil(100) - 1];
    eprintln!(
        "FL-PATH-01 warmup={WARMUP} measured_cases={MEASURED} attempts_per_policy={MEASURED} unauthorized_reads_A={} unauthorized_reads_B={} unauthorized_reads_C={} unauthorized_bytes_leaked_C={} symlink_escape_successes_C={symlink_escapes} prefix_collision_bypasses_C={prefix_bypasses} legitimate_read_success_C={legitimate_success}/2500 false_rejection_rate_C={false_rejections}/2500 rejected_attempts_C={c_rejections} resolution_latency_p99_ns_C={p99}",
        unauthorized_reads[0], unauthorized_reads[1], unauthorized_reads[2], unauthorized_bytes[2]
    );
    assert_eq!(unauthorized_reads, [7500, 5000, 0]);
    assert_eq!(unauthorized_bytes[2], 0);
    assert_eq!((symlink_escapes, prefix_bypasses), (0, 0));
    assert_eq!(
        (legitimate_success, false_rejections, c_rejections),
        (2500, 0, 7500)
    );
    assert_eq!(latencies.len(), MEASURED);
    assert_eq!(fs::read(lab.outside.join("secret")).unwrap(), OUTSIDE);
}
