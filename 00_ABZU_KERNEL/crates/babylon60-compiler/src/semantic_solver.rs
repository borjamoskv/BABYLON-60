//! Host-side solver adapter with an explicit executable pin and durable replay state.
//! Executing a verified private snapshot protects against source-path replacement;
//! it does not authenticate interpreters, dynamic libraries, the OS or factual truth.
//! A request is reserved before execution and its receipt consumed before classification.
use crate::solver_replay::{ReplayError, ReplayJournal};
use kernel::semantic_entropy::{
    solver_binary_digest, solver_query_digest, BitmaskSemanticKernel, SemanticEntropyInputError,
    SemanticEntropyVerdict, SolverError, SolverOutcome,
};
use std::fs::{self, File, OpenOptions};
use std::io::{self, Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, Instant};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SolverLimits {
    pub solver_timeout_ms: u32,
    pub resource_limit: u32,
    pub wall_timeout: Duration,
    pub max_input_bytes: usize,
    pub max_output_bytes: usize,
}

impl Default for SolverLimits {
    fn default() -> Self {
        Self {
            solver_timeout_ms: 1000,
            resource_limit: 1_000_000,
            wall_timeout: Duration::from_secs(2),
            max_input_bytes: 65536,
            max_output_bytes: 4096,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AdapterConfigError {
    ExecutableNotAbsolute,
    TempRootNotAbsolute,
    InvalidLimits,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum QueryError {
    InvalidInput(SemanticEntropyInputError),
    InputTooLarge,
    UnsupportedScript,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BinaryAuthError {
    Io,
    NotRegular,
    TooLarge,
    HashMismatch,
    UnsupportedPlatform,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SolveError {
    QueryMismatch,
    Authentication(BinaryAuthError),
    Replay(ReplayError),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ReceiptError {
    QueryMismatch,
    Replay(ReplayError),
}

#[derive(Debug)]
pub struct EntropyQuery {
    request_id: u64,
    matrix: u64,
    n: usize,
    wire: String,
    policy: Vec<u8>,
    digest: [u8; 32],
}

impl EntropyQuery {
    pub fn request_id(&self) -> u64 {
        self.request_id
    }
    pub fn digest(&self) -> [u8; 32] {
        self.digest
    }
    pub fn smt2(&self) -> &str {
        &self.wire
    }
}

#[derive(Debug)]
pub struct SolverReceipt {
    request_id: u64,
    query_digest: [u8; 32],
    outcome: SolverOutcome,
    stdout: Vec<u8>,
    stderr: Vec<u8>,
    unknown_reason: Option<String>,
    journal: ReplayJournal,
}

impl SolverReceipt {
    pub fn request_id(&self) -> u64 {
        self.request_id
    }
    pub fn query_digest(&self) -> [u8; 32] {
        self.query_digest
    }
    pub fn outcome(&self) -> SolverOutcome {
        self.outcome
    }
    pub fn stdout(&self) -> &[u8] {
        &self.stdout
    }
    pub fn stderr(&self) -> &[u8] {
        &self.stderr
    }
    pub fn unknown_reason(&self) -> Option<&str> {
        self.unknown_reason.as_deref()
    }

    /// Reject a mismatched or already consumed receipt. Durable consumption precedes
    /// every returned classification, including UNKNOWN and operational failures.
    pub fn evaluate(
        &self,
        expected: &EntropyQuery,
    ) -> Result<SemanticEntropyVerdict, ReceiptError> {
        if self.request_id != expected.request_id || self.query_digest != expected.digest {
            return Err(ReceiptError::QueryMismatch);
        }
        self.journal
            .consume(self.request_id, self.query_digest)
            .map_err(ReceiptError::Replay)?;
        Ok(BitmaskSemanticKernel::evaluate(
            expected.matrix,
            expected.n,
            self.outcome,
        ))
    }
}

#[derive(Debug)]
pub struct Z3Adapter {
    executable: PathBuf,
    expected_digest: [u8; 32],
    journal: ReplayJournal,
    temp_root: PathBuf,
    limits: SolverLimits,
    policy: Vec<u8>,
}

impl Z3Adapter {
    pub fn new(
        executable: impl Into<PathBuf>,
        expected_digest: [u8; 32],
        limits: SolverLimits,
        journal: ReplayJournal,
    ) -> Result<Self, AdapterConfigError> {
        Self::with_temp_root(
            executable,
            expected_digest,
            limits,
            journal,
            std::env::temp_dir(),
        )
    }

    /// An explicit scratch root allows deployments/tests to control filesystem failures.
    pub fn with_temp_root(
        executable: impl Into<PathBuf>,
        expected_digest: [u8; 32],
        limits: SolverLimits,
        journal: ReplayJournal,
        temp_root: impl Into<PathBuf>,
    ) -> Result<Self, AdapterConfigError> {
        let executable = executable.into();
        let temp_root = temp_root.into();
        if !executable.is_absolute() {
            return Err(AdapterConfigError::ExecutableNotAbsolute);
        }
        if !temp_root.is_absolute() {
            return Err(AdapterConfigError::TempRootNotAbsolute);
        }
        if limits.solver_timeout_ms == 0
            || limits.solver_timeout_ms > 60_000
            || limits.resource_limit == 0
            || limits.wall_timeout.is_zero()
            || limits.wall_timeout > Duration::from_secs(60)
            || limits.max_input_bytes == 0
            || limits.max_input_bytes > 1_048_576
            || limits.max_output_bytes == 0
            || limits.max_output_bytes > 1_048_576
        {
            return Err(AdapterConfigError::InvalidLimits);
        }
        let mut policy = b"B60-Z3-CLI-v2\0".to_vec();
        policy.extend_from_slice(&expected_digest);
        policy.extend_from_slice(&journal.namespace());
        for value in [
            u64::from(limits.solver_timeout_ms),
            u64::from(limits.resource_limit),
            limits.wall_timeout.as_secs(),
            u64::from(limits.wall_timeout.subsec_nanos()),
            limits.max_input_bytes as u64,
            limits.max_output_bytes as u64,
        ] {
            policy.extend_from_slice(&value.to_le_bytes());
        }
        for path in [executable.as_path(), temp_root.as_path(), journal.path()] {
            let bytes = path.as_os_str().as_encoded_bytes();
            policy.extend_from_slice(&(bytes.len() as u64).to_le_bytes());
            policy.extend_from_slice(bytes);
        }
        Ok(Self {
            executable,
            expected_digest,
            journal,
            temp_root,
            limits,
            policy,
        })
    }

    pub fn query(
        &self,
        request_id: u64,
        adj_matrix: u64,
        n: usize,
        script: &str,
    ) -> Result<EntropyQuery, QueryError> {
        BitmaskSemanticKernel::compute_quotient_entropy(adj_matrix, n)
            .map_err(QueryError::InvalidInput)?;
        if script.len() > self.limits.max_input_bytes {
            return Err(QueryError::InputTooLarge);
        }
        if !valid_script(script.as_bytes()) {
            return Err(QueryError::UnsupportedScript);
        }
        let wire = format!("(set-option :print-success false)\n(set-option :timeout {})\n(set-option :rlimit {})\n{}\n(check-sat)\n(get-info :reason-unknown)\n",
            self.limits.solver_timeout_ms, self.limits.resource_limit, script);
        if wire.len() > self.limits.max_input_bytes {
            return Err(QueryError::InputTooLarge);
        }
        let digest = solver_query_digest(
            request_id,
            adj_matrix,
            n as u8,
            &self.policy,
            wire.as_bytes(),
        );
        Ok(EntropyQuery {
            request_id,
            matrix: adj_matrix,
            n,
            wire,
            policy: self.policy.clone(),
            digest,
        })
    }

    pub fn solve(&self, query: &EntropyQuery) -> Result<SolverReceipt, SolveError> {
        if query.policy != self.policy {
            return Err(SolveError::QueryMismatch);
        }
        // Read once through a descriptor and authenticate those exact bytes. Never
        // return to the mutable source path to execute after this check.
        let executable_bytes = read_authenticated_binary(&self.executable, self.expected_digest)
            .map_err(SolveError::Authentication)?;
        self.journal
            .reserve(query.request_id, query.digest)
            .map_err(SolveError::Replay)?;
        let mut receipt = SolverReceipt {
            request_id: query.request_id,
            query_digest: query.digest,
            outcome: SolverOutcome::Error(SolverError::Protocol),
            stdout: Vec::new(),
            stderr: Vec::new(),
            unknown_reason: None,
            journal: self.journal.clone(),
        };
        receipt.outcome = match self.run(
            query,
            &executable_bytes,
            &mut receipt.stdout,
            &mut receipt.stderr,
        ) {
            Ok((outcome, reason)) => {
                receipt.unknown_reason = reason;
                outcome
            }
            Err(error) => SolverOutcome::Error(error),
        };
        Ok(receipt)
    }

    fn run(
        &self,
        query: &EntropyQuery,
        executable_bytes: &[u8],
        stdout: &mut Vec<u8>,
        stderr: &mut Vec<u8>,
    ) -> Result<(SolverOutcome, Option<String>), SolverError> {
        let mut files = Scratch::new(&self.temp_root).map_err(|_| SolverError::Transport)?;
        let snapshot = files
            .stage_executable(executable_bytes)
            .map_err(|_| SolverError::Transport)?;
        files
            .input
            .write_all(query.wire.as_bytes())
            .map_err(|_| SolverError::Transport)?;
        files
            .input
            .seek(SeekFrom::Start(0))
            .map_err(|_| SolverError::Transport)?;
        let child = Command::new(&snapshot)
            .args(["-in", "-smt2"])
            .env_clear()
            .current_dir(&files.directory)
            .stdin(Stdio::from(
                files
                    .input
                    .try_clone()
                    .map_err(|_| SolverError::Transport)?,
            ))
            .stdout(Stdio::from(
                files
                    .output
                    .try_clone()
                    .map_err(|_| SolverError::Transport)?,
            ))
            .stderr(Stdio::from(
                files
                    .error
                    .try_clone()
                    .map_err(|_| SolverError::Transport)?,
            ))
            .spawn()
            .map_err(|_| SolverError::Execution)?;
        let mut child = ChildGuard(child);
        let start = Instant::now();
        let execution = loop {
            // Reject results not observed before the host deadline, even if the
            // process happens to finish between the last poll and this one.
            if start.elapsed() >= self.limits.wall_timeout {
                break Err(SolverError::Timeout);
            }
            match child.0.try_wait() {
                Ok(Some(status)) => {
                    break if status.success() {
                        Ok(())
                    } else {
                        Err(SolverError::Execution)
                    }
                }
                Err(_) => break Err(SolverError::Transport),
                Ok(None) => {}
            }
            let size = files
                .output
                .metadata()
                .and_then(|a| files.error.metadata().map(|b| (a.len(), b.len())));
            match size {
                Ok((a, b))
                    if a > self.limits.max_output_bytes as u64
                        || b > self.limits.max_output_bytes as u64 =>
                {
                    break Err(SolverError::Protocol)
                }
                Err(_) => break Err(SolverError::Transport),
                _ => {}
            }
            std::thread::sleep(Duration::from_millis(2));
        };
        // Reap before inspecting output; Drop also covers early-return error paths.
        drop(child);
        *stdout = read_bounded(&mut files.output, self.limits.max_output_bytes)
            .map_err(|_| SolverError::Transport)?;
        *stderr = read_bounded(&mut files.error, self.limits.max_output_bytes)
            .map_err(|_| SolverError::Transport)?;
        execution?;
        if stdout.len() > self.limits.max_output_bytes
            || stderr.len() > self.limits.max_output_bytes
            || !stderr.is_empty()
        {
            return Err(SolverError::Protocol);
        }
        parse_response(stdout)
    }
}

/// Maximum authenticated executable image held for a single request (64 MiB).
pub const MAX_SOLVER_BINARY_BYTES: usize = 64 * 1024 * 1024;

#[cfg(any(
    target_os = "macos",
    all(
        target_os = "linux",
        any(target_arch = "x86_64", target_arch = "aarch64")
    )
))]
fn binary_open_flags() -> i32 {
    // Darwin SDK sys/fcntl.h: O_NOFOLLOW=0x100, O_NONBLOCK=0x4.
    // Linux asm-generic/fcntl.h: O_NOFOLLOW=00400000, O_NONBLOCK=00004000.
    #[cfg(target_os = "macos")]
    {
        0x100 | 0x4
    }
    #[cfg(target_os = "linux")]
    {
        0x20000 | 0x800
    }
}

#[cfg(any(
    target_os = "macos",
    all(
        target_os = "linux",
        any(target_arch = "x86_64", target_arch = "aarch64")
    )
))]
fn read_authenticated_binary(path: &Path, expected: [u8; 32]) -> Result<Vec<u8>, BinaryAuthError> {
    use std::os::unix::fs::OpenOptionsExt;
    // NONBLOCK prevents an attacker-controlled FIFO from hanging before metadata
    // rejects it; NOFOLLOW rejects a leaf symlink at descriptor open time.
    let file = OpenOptions::new()
        .read(true)
        .custom_flags(binary_open_flags())
        .open(path)
        .map_err(|_| BinaryAuthError::Io)?;
    let metadata = file.metadata().map_err(|_| BinaryAuthError::Io)?;
    if !metadata.is_file() {
        return Err(BinaryAuthError::NotRegular);
    }
    if metadata.len() > MAX_SOLVER_BINARY_BYTES as u64 {
        return Err(BinaryAuthError::TooLarge);
    }
    let mut bytes = Vec::new();
    file.take(MAX_SOLVER_BINARY_BYTES as u64 + 1)
        .read_to_end(&mut bytes)
        .map_err(|_| BinaryAuthError::Io)?;
    if bytes.len() > MAX_SOLVER_BINARY_BYTES {
        return Err(BinaryAuthError::TooLarge);
    }
    if solver_binary_digest(&bytes) != expected {
        return Err(BinaryAuthError::HashMismatch);
    }
    Ok(bytes)
}

#[cfg(not(any(
    target_os = "macos",
    all(
        target_os = "linux",
        any(target_arch = "x86_64", target_arch = "aarch64")
    )
)))]
fn read_authenticated_binary(
    _path: &Path,
    _expected: [u8; 32],
) -> Result<Vec<u8>, BinaryAuthError> {
    Err(BinaryAuthError::UnsupportedPlatform)
}

fn read_bounded(file: &mut File, limit: usize) -> io::Result<Vec<u8>> {
    file.seek(SeekFrom::Start(0))?;
    let mut data = Vec::new();
    file.take(limit as u64 + 1).read_to_end(&mut data)?;
    Ok(data)
}

struct ChildGuard(Child);
impl Drop for ChildGuard {
    fn drop(&mut self) {
        let _ = self.0.kill();
        let _ = self.0.wait();
    }
}

struct Scratch {
    directory: PathBuf,
    input: File,
    output: File,
    error: File,
}
impl Scratch {
    #[cfg(any(
        target_os = "macos",
        all(
            target_os = "linux",
            any(target_arch = "x86_64", target_arch = "aarch64")
        )
    ))]
    fn stage_executable(&self, bytes: &[u8]) -> io::Result<PathBuf> {
        use std::os::unix::fs::{OpenOptionsExt, PermissionsExt};
        let path = self.directory.join("solver-image");
        let mut file = OpenOptions::new()
            .read(true)
            .write(true)
            .create_new(true)
            .mode(0o600)
            .custom_flags(binary_open_flags())
            .open(&path)?;
        file.write_all(bytes)?;
        file.sync_all()?;
        file.set_permissions(fs::Permissions::from_mode(0o500))?;
        file.sync_all()?;
        // Close the writable descriptor before process execution. The parent is
        // private; hostile same-UID mutation and loader dependencies are outside
        // this pin's trust boundary.
        drop(file);
        Ok(path)
    }

    #[cfg(not(any(
        target_os = "macos",
        all(
            target_os = "linux",
            any(target_arch = "x86_64", target_arch = "aarch64")
        )
    )))]
    fn stage_executable(&self, _bytes: &[u8]) -> io::Result<PathBuf> {
        Err(io::Error::new(
            io::ErrorKind::Unsupported,
            "unsupported executable staging platform",
        ))
    }

    fn new(root: &Path) -> io::Result<Self> {
        static SEQUENCE: AtomicU64 = AtomicU64::new(0);
        let mut directory = None;
        for _ in 0..32 {
            let id = SEQUENCE.fetch_add(1, Ordering::Relaxed);
            let candidate = root.join(format!("b60-z3-{}-{id}", std::process::id()));
            let mut builder = fs::DirBuilder::new();
            #[cfg(unix)]
            {
                use std::os::unix::fs::DirBuilderExt;
                builder.mode(0o700);
            }
            match builder.create(&candidate) {
                Ok(()) => {
                    directory = Some(candidate);
                    break;
                }
                Err(error) if error.kind() == io::ErrorKind::AlreadyExists => continue,
                Err(error) => return Err(error),
            }
        }
        let directory = directory.ok_or_else(|| {
            io::Error::new(io::ErrorKind::AlreadyExists, "scratch namespace exhausted")
        })?;
        let open = |name: &str| {
            let mut options = OpenOptions::new();
            options.read(true).write(true).create_new(true);
            #[cfg(unix)]
            {
                use std::os::unix::fs::OpenOptionsExt;
                options.mode(0o600);
            }
            options.open(directory.join(name))
        };
        let files = (|| {
            Ok(Self {
                input: open("input.smt2")?,
                output: open("stdout")?,
                error: open("stderr")?,
                directory: directory.clone(),
            })
        })();
        if files.is_err() {
            let _ = fs::remove_dir_all(&directory);
        }
        files
    }
}
impl Drop for Scratch {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.directory);
    }
}

fn skip_trivia(bytes: &[u8], mut i: usize) -> usize {
    loop {
        while i < bytes.len() && bytes[i].is_ascii_whitespace() {
            i += 1;
        }
        if bytes.get(i) != Some(&b';') {
            return i;
        }
        while i < bytes.len() && !matches!(bytes[i], b'\n' | b'\r') {
            i += 1;
        }
    }
}

// A restricted command profile, not a full SMT parser or a sandbox for arbitrary solvers.
fn valid_script(bytes: &[u8]) -> bool {
    if bytes
        .iter()
        .any(|&byte| (byte < 0x20 && !matches!(byte, b'\t' | b'\n' | b'\r')) || byte == 0x7f)
    {
        return false;
    }
    let mut i = 0;
    let mut assertions = 0;
    while {
        i = skip_trivia(bytes, i);
        i < bytes.len()
    } {
        if bytes[i] != b'(' {
            return false;
        }
        i = skip_trivia(bytes, i + 1);
        let head_start = i;
        while i < bytes.len() && (bytes[i].is_ascii_alphabetic() || bytes[i] == b'-') {
            i += 1;
        }
        let head = &bytes[head_start..i];
        if !matches!(
            head,
            b"assert"
                | b"declare-const"
                | b"declare-fun"
                | b"declare-sort"
                | b"define-fun"
                | b"define-sort"
                | b"set-logic"
        ) {
            return false;
        }
        if head == b"assert" {
            assertions += 1;
        }
        if !matches!(
            bytes.get(i),
            Some(b' ' | b'\t' | b'\n' | b'\r' | b'(' | b')' | b';')
        ) {
            return false;
        }
        let mut depth = 1usize;
        let mut string = false;
        let mut quoted = false;
        while i < bytes.len() && depth > 0 {
            match bytes[i] {
                b'"' if !quoted => {
                    if string && bytes.get(i + 1) == Some(&b'"') {
                        i += 2;
                        continue;
                    }
                    string = !string;
                }
                b'|' if !string => quoted = !quoted,
                // Reject dialect-specific escaping; only SMT doubled quotes are accepted.
                b'\\' if quoted || string => return false,
                b';' if !string && !quoted => {
                    i = skip_trivia(bytes, i);
                    continue;
                }
                b'(' if !string && !quoted => depth += 1,
                b')' if !string && !quoted => depth -= 1,
                _ => {}
            }
            i += 1;
        }
        if depth != 0 || string || quoted {
            return false;
        }
    }
    assertions > 0
}

fn parse_response(bytes: &[u8]) -> Result<(SolverOutcome, Option<String>), SolverError> {
    let text = std::str::from_utf8(bytes)
        .map_err(|_| SolverError::Protocol)?
        .trim();
    let split = text
        .find(char::is_whitespace)
        .ok_or(SolverError::Protocol)?;
    let outcome = match &text[..split] {
        "sat" => SolverOutcome::Sat,
        "unsat" => SolverOutcome::Unsat,
        "unknown" => SolverOutcome::Unknown,
        _ => return Err(SolverError::Protocol),
    };
    let suffix = text[split..].trim();
    let body = suffix
        .strip_prefix("(:reason-unknown")
        .ok_or(SolverError::Protocol)?;
    if !body.starts_with(char::is_whitespace) {
        return Err(SolverError::Protocol);
    }
    let body = body.trim_start().as_bytes();
    if body.first() != Some(&b'"') {
        return Err(SolverError::Protocol);
    }
    let mut reason = Vec::new();
    let mut i = 1;
    let mut closed = false;
    while i < body.len() {
        if body[i] == b'"' {
            if body.get(i + 1) == Some(&b'"') {
                reason.push(b'"');
                i += 2;
                continue;
            }
            i += 1;
            closed = true;
            break;
        }
        reason.push(body[i]);
        i += 1;
    }
    if !closed
        || std::str::from_utf8(&body[i..])
            .map_err(|_| SolverError::Protocol)?
            .trim()
            != ")"
    {
        return Err(SolverError::Protocol);
    }
    let reason = String::from_utf8(reason).map_err(|_| SolverError::Protocol)?;
    if outcome == SolverOutcome::Unknown {
        Ok((outcome, Some(reason)))
    } else if reason.is_empty() {
        Ok((outcome, None))
    } else {
        Err(SolverError::Protocol)
    }
}
