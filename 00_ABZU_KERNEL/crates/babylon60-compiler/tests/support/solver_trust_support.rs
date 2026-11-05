//! Isolated test fixtures. Fixture-byte pinning here is not production trust discovery.
#![allow(dead_code)]
use babylon60_compiler::semantic_solver::{
    AdapterConfigError, SolverLimits, Z3Adapter, MAX_SOLVER_BINARY_BYTES,
};
use babylon60_compiler::solver_replay::ReplayJournal;
use kernel::semantic_entropy::solver_binary_digest;
use std::fs::OpenOptions;
use std::io::Read;
use std::ops::Deref;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

pub const NAMESPACE: [u8; 16] = [0x36; 16];

pub struct TempDir(pub PathBuf);
impl TempDir {
    pub fn new() -> Self {
        static NEXT: AtomicU64 = AtomicU64::new(1);
        let root = std::env::temp_dir().join(format!(
            "b60-solver-trust-test-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        let mut builder = std::fs::DirBuilder::new();
        #[cfg(unix)]
        {
            use std::os::unix::fs::DirBuilderExt;
            builder.mode(0o700);
        }
        builder.create(&root).unwrap();
        Self(root)
    }
    #[cfg(unix)]
    pub fn program(&self, name: &str, body: &str) -> PathBuf {
        use std::os::unix::fs::PermissionsExt;
        let path = self.0.join(name);
        std::fs::write(&path, format!("#!/usr/bin/python3\n{body}\n")).unwrap();
        std::fs::set_permissions(&path, std::fs::Permissions::from_mode(0o700)).unwrap();
        path
    }
    pub fn journal(&self) -> ReplayJournal {
        ReplayJournal::create(self.0.join("replay.bin"), NAMESPACE).unwrap()
    }
}
impl Drop for TempDir {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.0);
    }
}

pub fn z3_path() -> PathBuf {
    if let Some(path) = std::env::var_os("BABYLON_Z3_BIN") {
        // An explicit executable never falls back to another candidate. The
        // adapter must still authenticate it against the independently set pin.
        return std::fs::canonicalize(path).unwrap();
    }
    find_pinned_executable(
        std::env::split_paths(&std::env::var_os("PATH").unwrap_or_default()).map(|p| p.join("z3")),
        real_pin(),
    )
    .expect("Real tests require a Z3 on PATH matching the approved pin")
}

fn find_pinned_executable(
    paths: impl IntoIterator<Item = PathBuf>,
    expected: [u8; 32],
) -> Option<PathBuf> {
    paths
        .into_iter()
        .filter(|p| p.is_absolute())
        .find_map(|path| {
            let path = std::fs::canonicalize(path).ok()?;
            let mut options = OpenOptions::new();
            options.read(true);
            #[cfg(unix)]
            {
                use std::os::unix::fs::OpenOptionsExt;
                // Match the adapter's supported Unix descriptor flags: do not
                // block on a FIFO or follow a replacement leaf symlink.
                let flags = match std::env::consts::OS {
                    "macos" => 0x100 | 0x4,
                    "linux" => 0x20000 | 0x800,
                    _ => return None,
                };
                options.custom_flags(flags);
            }
            let file = options.open(&path).ok()?;
            let metadata = file.metadata().ok()?;
            if !metadata.is_file() || metadata.len() > MAX_SOLVER_BINARY_BYTES as u64 {
                return None;
            }
            let mut bytes = Vec::new();
            file.take(MAX_SOLVER_BINARY_BYTES as u64 + 1)
                .read_to_end(&mut bytes)
                .ok()?;
            (bytes.len() <= MAX_SOLVER_BINARY_BYTES && solver_binary_digest(&bytes) == expected)
                .then_some(path)
        })
}

pub fn real_pin() -> [u8; 32] {
    // Test anchor matches the binary in the preceding audit, not a vendor signature.
    let text = std::env::var("BABYLON_Z3_BLAKE3").unwrap_or_else(|_| {
        "e4f6b1564a1ddbf849c676f33cc33a0b2d35159e1dc62d38d3bd6be587fcfec3".into()
    });
    assert_eq!(text.len(), 64);
    let mut pin = [0; 32];
    for (i, value) in pin.iter_mut().enumerate() {
        *value = u8::from_str_radix(&text[2 * i..2 * i + 2], 16).unwrap();
    }
    pin
}

fn fixture_pin(executable: &Path) -> [u8; 32] {
    if executable == z3_path() {
        return real_pin();
    }
    std::fs::read(executable)
        .map(|bytes| solver_binary_digest(&bytes))
        .unwrap_or([0; 32])
}

pub struct TestAdapter {
    pub inner: Z3Adapter,
    pub journal: ReplayJournal,
    _root: TempDir,
}
impl Deref for TestAdapter {
    type Target = Z3Adapter;
    fn deref(&self) -> &Self::Target {
        &self.inner
    }
}

pub fn secure_new(
    executable: impl Into<PathBuf>,
    limits: SolverLimits,
) -> Result<TestAdapter, AdapterConfigError> {
    let root = TempDir::new();
    let journal = root.journal();
    let executable = executable.into();
    let inner = Z3Adapter::new(
        &executable,
        fixture_pin(&executable),
        limits,
        journal.clone(),
    )?;
    Ok(TestAdapter {
        inner,
        journal,
        _root: root,
    })
}

pub fn secure_temp(
    executable: impl Into<PathBuf>,
    limits: SolverLimits,
    scratch: impl Into<PathBuf>,
) -> Result<TestAdapter, AdapterConfigError> {
    let root = TempDir::new();
    let journal = root.journal();
    let executable = executable.into();
    let inner = Z3Adapter::with_temp_root(
        &executable,
        fixture_pin(&executable),
        limits,
        journal.clone(),
        scratch,
    )?;
    Ok(TestAdapter {
        inner,
        journal,
        _root: root,
    })
}

#[cfg(test)]
mod discovery_tests {
    use super::*;

    #[test]
    fn discovery_skips_an_unapproved_first_candidate() {
        let root = TempDir::new();
        let foreign = root.0.join("foreign-z3");
        let approved = root.0.join("approved-z3");
        std::fs::write(&foreign, b"unapproved isolated fixture").unwrap();
        let approved_bytes = b"approved isolated fixture";
        std::fs::write(&approved, approved_bytes).unwrap();
        assert_eq!(
            find_pinned_executable(
                [foreign, approved.clone()],
                solver_binary_digest(approved_bytes),
            ),
            Some(std::fs::canonicalize(approved).unwrap()),
        );
    }

    #[test]
    fn discovery_returns_none_without_an_approved_candidate() {
        let root = TempDir::new();
        let foreign = root.0.join("foreign-z3");
        std::fs::write(&foreign, b"unapproved isolated fixture").unwrap();
        assert_eq!(
            find_pinned_executable(
                [foreign],
                solver_binary_digest(b"approved isolated fixture")
            ),
            None,
        );
    }

    #[test]
    fn discovery_rejects_a_changed_expected_pin() {
        let root = TempDir::new();
        let candidate = root.0.join("isolated-z3");
        let bytes = b"isolated fixture";
        std::fs::write(&candidate, bytes).unwrap();
        let mut pin = solver_binary_digest(bytes);
        pin[0] ^= 1;
        assert_eq!(find_pinned_executable([candidate], pin), None);
    }

    #[test]
    fn discovery_rejects_missing_directory_and_oversize_candidates() {
        let root = TempDir::new();
        let oversize = root.0.join("oversize-z3");
        std::fs::File::create(&oversize)
            .unwrap()
            .set_len(MAX_SOLVER_BINARY_BYTES as u64 + 1)
            .unwrap();
        assert_eq!(
            find_pinned_executable(
                [root.0.join("absent-z3"), root.0.clone(), oversize],
                solver_binary_digest(b""),
            ),
            None,
        );
    }
}
