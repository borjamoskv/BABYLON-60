//! Isolated test fixtures. Fixture-byte pinning here is not production trust discovery.
#![allow(dead_code)]
use babylon60_compiler::semantic_solver::{AdapterConfigError, SolverLimits, Z3Adapter};
use babylon60_compiler::solver_replay::ReplayJournal;
use kernel::semantic_entropy::solver_binary_digest;
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
    let path = if let Some(path) = std::env::var_os("BABYLON_Z3_BIN") {
        PathBuf::from(path)
    } else {
        std::env::split_paths(&std::env::var_os("PATH").unwrap_or_default())
            .map(|p| p.join("z3"))
            .find(|p| p.is_absolute() && p.is_file())
            .expect("Real tests require Z3 and an approved pin")
    };
    std::fs::canonicalize(path).unwrap()
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
