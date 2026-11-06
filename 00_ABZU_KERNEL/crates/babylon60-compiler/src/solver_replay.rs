//! Durable local request reservation and one-time receipt consumption.
//!
//! The caller must protect the private parent and retain this journal. Locks are
//! advisory; checksums do not authenticate an owner who rewrites or rolls back
//! valid state. Successful syncs rely on the filesystem/storage durability contract.
use kernel::semantic_entropy::solver_replay_record_digest;
use std::collections::BTreeMap;
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};

const MAGIC: &[u8; 16] = b"B60-Z3-JOURNAL1\0";
const HEADER_SIZE: usize = 64;
const RECORD_SIZE: usize = 80;
const RESERVE: u8 = 1;
const CONSUME: u8 = 2;
pub const MAX_JOURNAL_RECORDS: usize = 100_000;
pub const MAX_JOURNAL_BYTES: usize = HEADER_SIZE + RECORD_SIZE * MAX_JOURNAL_RECORDS;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ReplayError {
    InvalidConfig,
    Replay,
    MissingReservation,
    QueryMismatch,
    Corrupt,
    Io,
    Capacity,
    UnsupportedPlatform,
}

#[derive(Debug, Clone)]
pub struct ReplayJournal {
    path: PathBuf,
    namespace: [u8; 16],
}

#[derive(Clone, Copy)]
struct RequestState {
    digest: [u8; 32],
    consumed: bool,
}

struct JournalState {
    requests: BTreeMap<u64, RequestState>,
    last_hash: [u8; 32],
    records: usize,
}

impl ReplayJournal {
    /// Explicit initialization only: an existing pathname is never overwritten.
    /// The parent must already exist with mode 0700 on supported Unix platforms.
    pub fn create(path: impl Into<PathBuf>, namespace: [u8; 16]) -> Result<Self, ReplayError> {
        let journal = Self::configured(path.into(), namespace)?;
        let parent = journal.open_parent()?;
        let mut options = secure_options()?;
        options.read(true).write(true).create_new(true);
        let mut file = options.open(&journal.path).map_err(|_| ReplayError::Io)?;
        file.lock().map_err(|_| ReplayError::Io)?;
        journal.validate_file(&file, &parent)?;
        let mut header = [0u8; HEADER_SIZE];
        header[..16].copy_from_slice(MAGIC);
        header[16..32].copy_from_slice(&namespace);
        let checksum = solver_replay_record_digest(&header[..32]);
        header[32..].copy_from_slice(&checksum);
        file.write_all(&header).map_err(|_| ReplayError::Io)?;
        file.sync_all().map_err(|_| ReplayError::Io)?;
        parent.sync_all().map_err(|_| ReplayError::Io)?;
        Ok(journal)
    }

    /// Open retained state, refusing absent, malformed or incompatible journals.
    /// No missing/truncated state is recreated, repaired or discarded.
    pub fn open(path: impl Into<PathBuf>, namespace: [u8; 16]) -> Result<Self, ReplayError> {
        let journal = Self::configured(path.into(), namespace)?;
        let mut file = journal.locked_file()?;
        journal.load(&mut file)?;
        Ok(journal)
    }

    pub fn path(&self) -> &Path {
        &self.path
    }

    pub fn namespace(&self) -> [u8; 16] {
        self.namespace
    }

    /// Reserve durably before executing a solver. Any existing ID is a replay,
    /// even if its former query had a different digest or never completed.
    pub fn reserve(&self, request_id: u64, digest: [u8; 32]) -> Result<(), ReplayError> {
        self.transition(RESERVE, request_id, digest)
    }

    /// Consume the matching reserved receipt durably before returning a verdict.
    /// Failed/inconclusive solver results are also consumed, not retried by ID.
    pub fn consume(&self, request_id: u64, digest: [u8; 32]) -> Result<(), ReplayError> {
        self.transition(CONSUME, request_id, digest)
    }

    fn configured(path: PathBuf, namespace: [u8; 16]) -> Result<Self, ReplayError> {
        if !path.is_absolute() || path.file_name().is_none() {
            return Err(ReplayError::InvalidConfig);
        }
        // Check support without opening a path on unsupported platforms.
        secure_options()?;
        Ok(Self { path, namespace })
    }

    fn locked_file(&self) -> Result<File, ReplayError> {
        let parent = self.open_parent()?;
        let mut options = secure_options()?;
        options.read(true).write(true);
        let file = options.open(&self.path).map_err(|_| ReplayError::Io)?;
        // Reject non-regular descriptors before attempting an advisory lock.
        self.validate_file(&file, &parent)?;
        // Every operation owns a fresh descriptor and takes this lock only once.
        // Closing that descriptor releases the lock, including process termination.
        file.lock().map_err(|_| ReplayError::Io)?;
        self.validate_file(&file, &parent)?;
        Ok(file)
    }

    fn open_parent(&self) -> Result<File, ReplayError> {
        let path = self.path.parent().ok_or(ReplayError::InvalidConfig)?;
        let mut options = secure_options()?;
        options.read(true);
        let parent = options.open(path).map_err(|_| ReplayError::Io)?;
        let metadata = parent.metadata().map_err(|_| ReplayError::Io)?;
        if !metadata.is_dir() {
            return Err(ReplayError::InvalidConfig);
        }
        #[cfg(unix)]
        {
            use std::os::unix::fs::MetadataExt;
            if metadata.mode() & 0o777 != 0o700 {
                return Err(ReplayError::InvalidConfig);
            }
        }
        Ok(parent)
    }

    fn validate_file(&self, file: &File, parent: &File) -> Result<(), ReplayError> {
        let metadata = file.metadata().map_err(|_| ReplayError::Io)?;
        if !metadata.is_file() {
            return Err(ReplayError::Corrupt);
        }
        #[cfg(unix)]
        {
            use std::os::unix::fs::MetadataExt;
            let directory = parent.metadata().map_err(|_| ReplayError::Io)?;
            let named = fs::symlink_metadata(&self.path).map_err(|_| ReplayError::Io)?;
            if metadata.mode() & 0o777 != 0o600
                || metadata.nlink() != 1
                || metadata.uid() != directory.uid()
                || metadata.dev() != named.dev()
                || metadata.ino() != named.ino()
            {
                return Err(ReplayError::Corrupt);
            }
        }
        Ok(())
    }

    fn load(&self, file: &mut File) -> Result<JournalState, ReplayError> {
        let length = file.metadata().map_err(|_| ReplayError::Io)?.len();
        if length > MAX_JOURNAL_BYTES as u64 {
            return Err(ReplayError::Capacity);
        }
        if length < HEADER_SIZE as u64 || (length as usize - HEADER_SIZE) % RECORD_SIZE != 0 {
            return Err(ReplayError::Corrupt);
        }
        file.seek(SeekFrom::Start(0)).map_err(|_| ReplayError::Io)?;
        let mut bytes = Vec::new();
        file.take(MAX_JOURNAL_BYTES as u64 + 1)
            .read_to_end(&mut bytes)
            .map_err(|_| ReplayError::Io)?;
        if bytes.len() > MAX_JOURNAL_BYTES {
            return Err(ReplayError::Capacity);
        }
        if bytes.len() as u64 != length || &bytes[..16] != MAGIC || bytes[16..32] != self.namespace
        {
            return Err(ReplayError::Corrupt);
        }
        let mut last_hash = solver_replay_record_digest(&bytes[..32]);
        if bytes[32..HEADER_SIZE] != last_hash {
            return Err(ReplayError::Corrupt);
        }
        let mut requests = BTreeMap::new();
        for record in bytes[HEADER_SIZE..].chunks_exact(RECORD_SIZE) {
            if record[..4] != (RECORD_SIZE as u32).to_le_bytes()
                || record[5..8] != [0; 3]
                || !matches!(record[4], RESERVE | CONSUME)
            {
                return Err(ReplayError::Corrupt);
            }
            let mut chained = [0u8; 80];
            chained[..32].copy_from_slice(&last_hash);
            chained[32..].copy_from_slice(&record[..48]);
            last_hash = solver_replay_record_digest(&chained);
            if record[48..] != last_hash {
                return Err(ReplayError::Corrupt);
            }
            let mut id = [0u8; 8];
            id.copy_from_slice(&record[8..16]);
            let request_id = u64::from_le_bytes(id);
            let mut digest = [0u8; 32];
            digest.copy_from_slice(&record[16..48]);
            match record[4] {
                RESERVE => {
                    if requests
                        .insert(
                            request_id,
                            RequestState {
                                digest,
                                consumed: false,
                            },
                        )
                        .is_some()
                    {
                        return Err(ReplayError::Corrupt);
                    }
                }
                CONSUME => {
                    let state = requests.get_mut(&request_id).ok_or(ReplayError::Corrupt)?;
                    if state.consumed || state.digest != digest {
                        return Err(ReplayError::Corrupt);
                    }
                    state.consumed = true;
                }
                _ => return Err(ReplayError::Corrupt),
            }
        }
        Ok(JournalState {
            requests,
            last_hash,
            records: (bytes.len() - HEADER_SIZE) / RECORD_SIZE,
        })
    }

    fn transition(&self, kind: u8, request_id: u64, digest: [u8; 32]) -> Result<(), ReplayError> {
        let mut file = self.locked_file()?;
        let state = self.load(&mut file)?;
        match (kind, state.requests.get(&request_id)) {
            (RESERVE, Some(_)) => return Err(ReplayError::Replay),
            (CONSUME, None) => return Err(ReplayError::MissingReservation),
            (CONSUME, Some(prior)) if prior.consumed => return Err(ReplayError::Replay),
            (CONSUME, Some(prior)) if prior.digest != digest => {
                return Err(ReplayError::QueryMismatch)
            }
            _ => {}
        }
        if state.records >= MAX_JOURNAL_RECORDS {
            return Err(ReplayError::Capacity);
        }
        let mut record = [0u8; RECORD_SIZE];
        record[..4].copy_from_slice(&(RECORD_SIZE as u32).to_le_bytes());
        record[4] = kind;
        record[8..16].copy_from_slice(&request_id.to_le_bytes());
        record[16..48].copy_from_slice(&digest);
        let mut chained = [0u8; 80];
        chained[..32].copy_from_slice(&state.last_hash);
        chained[32..].copy_from_slice(&record[..48]);
        record[48..].copy_from_slice(&solver_replay_record_digest(&chained));
        file.seek(SeekFrom::End(0)).map_err(|_| ReplayError::Io)?;
        file.write_all(&record).map_err(|_| ReplayError::Io)?;
        file.sync_all().map_err(|_| ReplayError::Io)?;
        Ok(())
    }
}

fn secure_options() -> Result<OpenOptions, ReplayError> {
    #[cfg(any(
        target_os = "macos",
        all(
            target_os = "linux",
            any(target_arch = "x86_64", target_arch = "aarch64")
        )
    ))]
    {
        use std::os::unix::fs::OpenOptionsExt;
        // Darwin SDK sys/fcntl.h:123; Linux asm-generic/fcntl.h:54-56.
        #[cfg(target_os = "macos")]
        const NOFOLLOW: i32 = 0x100;
        #[cfg(target_os = "macos")]
        const NONBLOCK: i32 = 0x4;
        #[cfg(target_os = "linux")]
        const NOFOLLOW: i32 = 0x20000;
        #[cfg(target_os = "linux")]
        const NONBLOCK: i32 = 0x800;
        let mut options = OpenOptions::new();
        options.mode(0o600).custom_flags(NOFOLLOW | NONBLOCK);
        Ok(options)
    }
    #[cfg(not(any(
        target_os = "macos",
        all(
            target_os = "linux",
            any(target_arch = "x86_64", target_arch = "aarch64")
        )
    )))]
    {
        Err(ReplayError::UnsupportedPlatform)
    }
}
