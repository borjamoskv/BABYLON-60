//! Protocolo de comunicación inter-proceso (IPC) Zero-HTTP.
//! Acopla el `SharedManifest` canónico (64B) y las instantáneas sincronizadas de telemetría con el canal Unix Domain Socket (UDS).

use babylon60::manifest::SharedManifest;
use babylon60::seqlock::read as read_shared_manifest;
use std::io;
use std::os::unix::fs::{DirBuilderExt, FileTypeExt, MetadataExt, PermissionsExt};
use std::path::Path;
use std::sync::Arc;
use std::time::Duration;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{UnixListener, UnixStream};
use tokio::sync::{OwnedSemaphorePermit, Semaphore};

pub const DEFAULT_SOCKET_PATH: &str = "/tmp/eridu-infer/socket";

/// Consistent in-process snapshots. Lock acquisition may block; this is not a seqlock.
/// The canonical SharedManifest protocol remains separate.
pub struct TelemetrySnapshot<T: Copy> {
    data: std::sync::RwLock<T>,
}

impl<T: Copy> TelemetrySnapshot<T> {
    pub fn new(initial: T) -> Self {
        Self {
            data: std::sync::RwLock::new(initial),
        }
    }

    pub fn write(&self, value: T) {
        *self.data.write().expect("telemetry snapshot poisoned") = value;
    }

    pub fn read(&self) -> T {
        *self.data.read().expect("telemetry snapshot poisoned")
    }

    fn try_read(&self) -> Option<T> {
        self.data.try_read().ok().map(|guard| *guard)
    }

    /// Read-modify-write under one exclusive guard, preventing lost increments.
    pub fn update(&self, update: impl FnOnce(&mut T)) {
        let mut guard = self.data.write().expect("telemetry snapshot poisoned");
        update(&mut *guard);
    }
}

/// Instantánea coherente de telemetría de inferencia.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct InferenceTelemetryBlock {
    pub tokens_generated: u64,
    pub prompt_tokens: u64,
    pub last_latency_micros: u64,
    pub active_context_length: u32,
    pub is_generating: bool,
}

pub const MAX_UDS_CONNECTIONS: usize = 32;
const IO_DEADLINE: Duration = Duration::from_secs(2);

// A local socket pair obtains this process's OS-authenticated uid without
// environment variables, shell commands, or an additional libc dependency.
fn process_uid() -> io::Result<u32> {
    let (local, _peer) = UnixStream::pair()?;
    Ok(local.peer_cred()?.uid())
}

fn prepare_socket_path(path: &Path, owner: u32) -> io::Result<()> {
    let parent = path
        .parent()
        .filter(|p| !p.as_os_str().is_empty())
        .ok_or_else(|| {
            io::Error::new(
                io::ErrorKind::InvalidInput,
                "socket needs a private parent directory",
            )
        })?;
    match std::fs::DirBuilder::new().mode(0o700).create(parent) {
        Ok(()) => {}
        Err(error) if error.kind() == io::ErrorKind::AlreadyExists => {}
        Err(error) => return Err(error),
    }
    let metadata = std::fs::symlink_metadata(parent)?;
    if !metadata.is_dir() || metadata.uid() != owner || metadata.mode() & 0o077 != 0 {
        return Err(io::Error::new(
            io::ErrorKind::PermissionDenied,
            "socket parent must be owned by this user and private",
        ));
    }
    match std::fs::symlink_metadata(path) {
        Ok(_) => Err(io::Error::new(
            io::ErrorKind::AlreadyExists,
            "refusing to replace an existing socket path",
        )),
        Err(error) if error.kind() == io::ErrorKind::NotFound => Ok(()),
        Err(error) => Err(error),
    }
}

fn authorize_peer(stream: &UnixStream, owner: u32) -> io::Result<()> {
    if stream.peer_cred()?.uid() != owner {
        return Err(io::Error::new(
            io::ErrorKind::PermissionDenied,
            "foreign UDS peer",
        ));
    }
    Ok(())
}

async fn serve_peer(
    mut stream: UnixStream,
    owner: u32,
    manifest: Arc<SharedManifest>,
    telemetry: Arc<TelemetrySnapshot<InferenceTelemetryBlock>>,
    deadline: Duration,
    _permit: OwnedSemaphorePermit,
) -> io::Result<()> {
    authorize_peer(&stream, owner)?;
    tokio::time::timeout(deadline, async {
        let mut buf = [0u8; 4096];
        if stream.read(&mut buf).await? == 0 { return Ok(()); }
        let t = telemetry.try_read().ok_or_else(|| io::Error::other("telemetry unavailable"))?;
        let (epoch, hash) = read_shared_manifest(&manifest)
            .ok_or_else(|| io::Error::other("manifest unavailable"))?;
        let response = format!(
            "{{\"status\":\"ACK_ZERO_COPY_UMA\",\"rfo\":null,\"epoch\":{},\"hash_w0\":{},\"tokens_generated\":{},\"prompt_tokens\":{},\"last_latency_micros\":{}}}\n",
            epoch, hash[0], t.tokens_generated, t.prompt_tokens, t.last_latency_micros
        );
        stream.write_all(response.as_bytes()).await
    }).await.map_err(|_| io::Error::new(io::ErrorKind::TimedOut, "UDS I/O deadline exceeded"))?
}

struct OwnedSocketPath {
    path: std::path::PathBuf,
    device: u64,
    inode: u64,
}

impl OwnedSocketPath {
    fn capture(path: &Path) -> io::Result<Self> {
        let metadata = std::fs::symlink_metadata(path)?;
        if !metadata.file_type().is_socket() {
            return Err(io::Error::other("bound path is not a socket"));
        }
        Ok(Self {
            path: path.to_owned(),
            device: metadata.dev(),
            inode: metadata.ino(),
        })
    }
}

impl Drop for OwnedSocketPath {
    fn drop(&mut self) {
        // A replacement file, symlink, or different socket belongs to someone else.
        if let Ok(metadata) = std::fs::symlink_metadata(&self.path) {
            if metadata.file_type().is_socket()
                && metadata.dev() == self.device
                && metadata.ino() == self.inode
            {
                let _ = std::fs::remove_file(&self.path);
            }
        }
    }
}

/// Owns the listener task and its exact filesystem socket identity.
#[must_use = "retain the handle while the UDS endpoint is required"]
pub struct UdsListenerHandle {
    task: Option<tokio::task::JoinHandle<()>>,
    _socket: OwnedSocketPath,
}

impl UdsListenerHandle {
    /// Wait for listener cancellation before releasing its pathname.
    pub async fn shutdown(mut self) {
        if let Some(task) = self.task.take() {
            task.abort();
            let _ = task.await;
        }
    }
}

impl Drop for UdsListenerHandle {
    fn drop(&mut self) {
        if let Some(task) = self.task.take() {
            task.abort();
        }
    }
}

/// Start a same-user telemetry endpoint in a private directory.
/// Existing files are never removed; stale endpoints require explicit cleanup.
pub async fn start_uds_listener<P: AsRef<Path>>(
    socket_path: P,
    manifest: Arc<SharedManifest>,
    telemetry: Arc<TelemetrySnapshot<InferenceTelemetryBlock>>,
) -> Result<UdsListenerHandle, String> {
    let owner = process_uid().map_err(|e| e.to_string())?;
    let p = socket_path.as_ref();
    prepare_socket_path(p, owner).map_err(|e| e.to_string())?;
    let listener = UnixListener::bind(p).map_err(|e| e.to_string())?;
    let owned_socket = OwnedSocketPath::capture(p).map_err(|e| e.to_string())?;
    std::fs::set_permissions(p, std::fs::Permissions::from_mode(0o600))
        .map_err(|e| e.to_string())?;
    let permits = Arc::new(Semaphore::new(MAX_UDS_CONNECTIONS));
    let task = tokio::spawn(async move {
        let mut peers = tokio::task::JoinSet::new();
        loop {
            while peers.try_join_next().is_some() {}
            // Acquire before accepting/spawning: no unbounded queue of waiting tasks.
            let Ok(permit) = Arc::clone(&permits).acquire_owned().await else {
                break;
            };
            let Ok((stream, _)) = listener.accept().await else {
                break;
            };
            let manifest = Arc::clone(&manifest);
            let telemetry = Arc::clone(&telemetry);
            peers.spawn(async move {
                let _ = serve_peer(stream, owner, manifest, telemetry, IO_DEADLINE, permit).await;
            });
        }
    });
    Ok(UdsListenerHandle {
        task: Some(task),
        _socket: owned_socket,
    })
}

#[cfg(test)]
mod security_tests {
    use super::*;
    use std::os::unix::fs::symlink;
    use std::sync::atomic::{AtomicUsize, Ordering};

    static NEXT_TEMP: AtomicUsize = AtomicUsize::new(0);
    struct TempDirectory(std::path::PathBuf);
    impl TempDirectory {
        fn new() -> Self {
            let path = std::env::temp_dir().join(format!(
                "eridu-uds-test-{}-{}",
                std::process::id(),
                NEXT_TEMP.fetch_add(1, Ordering::Relaxed)
            ));
            std::fs::DirBuilder::new()
                .mode(0o700)
                .create(&path)
                .unwrap();
            Self(path)
        }
    }
    impl Drop for TempDirectory {
        fn drop(&mut self) {
            let _ = std::fs::remove_dir_all(&self.0);
        }
    }

    async fn start_test_socket(path: &Path) -> UdsListenerHandle {
        start_uds_listener(
            path,
            Arc::new(SharedManifest::new()),
            Arc::new(TelemetrySnapshot::new(InferenceTelemetryBlock::default())),
        )
        .await
        .unwrap()
    }

    #[tokio::test]
    async fn listener_shutdown_allows_restart_and_refuses_duplicate_start() {
        let temp = TempDirectory::new();
        let path = temp.0.join("socket");
        for _ in 0..3 {
            let handle = start_test_socket(&path).await;
            assert_eq!(std::fs::metadata(&path).unwrap().mode() & 0o777, 0o600);
            assert!(start_uds_listener(
                &path,
                Arc::new(SharedManifest::new()),
                Arc::new(TelemetrySnapshot::new(InferenceTelemetryBlock::default()))
            )
            .await
            .is_err());
            let mut client = UnixStream::connect(&path).await.unwrap();
            client.write_all(b"snapshot").await.unwrap();
            let mut response = Vec::new();
            client.read_to_end(&mut response).await.unwrap();
            assert!(!response.is_empty());
            handle.shutdown().await;
            assert!(!path.exists());
        }
    }

    #[tokio::test]
    async fn cleanup_preserves_replacement_file_symlink_and_socket() {
        let temp = TempDirectory::new();
        for kind in 0..3 {
            let path = temp.0.join(format!("socket-{kind}"));
            let handle = start_test_socket(&path).await;
            std::fs::rename(&path, temp.0.join(format!("original-{kind}"))).unwrap();
            let replacement = match kind {
                0 => {
                    std::fs::write(&path, b"preserve").unwrap();
                    None
                }
                1 => {
                    symlink("unrelated", &path).unwrap();
                    None
                }
                _ => Some(UnixListener::bind(&path).unwrap()),
            };
            let identity = std::fs::symlink_metadata(&path).unwrap().ino();
            handle.shutdown().await;
            assert_eq!(std::fs::symlink_metadata(&path).unwrap().ino(), identity);
            drop(replacement);
        }
    }

    #[tokio::test]
    async fn dropping_handle_before_first_poll_releases_owned_path() {
        let temp = TempDirectory::new();
        let path = temp.0.join("socket");
        let handle = start_test_socket(&path).await;
        drop(handle);
        assert!(!path.exists());
    }

    #[tokio::test]
    async fn rejects_foreign_uid_and_preserves_existing_paths() {
        let uid = process_uid().unwrap();
        let (peer, _other) = UnixStream::pair().unwrap();
        authorize_peer(&peer, uid).unwrap();
        assert_eq!(
            authorize_peer(&peer, uid.wrapping_add(1))
                .unwrap_err()
                .kind(),
            io::ErrorKind::PermissionDenied
        );
        let temp = TempDirectory::new();
        let socket = temp.0.join("private/socket");
        prepare_socket_path(&socket, uid).unwrap();
        assert_eq!(
            std::fs::metadata(socket.parent().unwrap()).unwrap().mode() & 0o777,
            0o700
        );
        std::fs::write(&socket, b"retain").unwrap();
        assert_eq!(
            prepare_socket_path(&socket, uid).unwrap_err().kind(),
            io::ErrorKind::AlreadyExists
        );
        assert_eq!(std::fs::read(&socket).unwrap(), b"retain");
        let link = temp.0.join("private/link");
        symlink(&socket, &link).unwrap();
        assert!(prepare_socket_path(&link, uid).is_err());
        let parent_link = temp.0.join("linked-parent");
        symlink(socket.parent().unwrap(), &parent_link).unwrap();
        assert!(prepare_socket_path(&parent_link.join("socket"), uid).is_err());
        std::fs::set_permissions(
            socket.parent().unwrap(),
            std::fs::Permissions::from_mode(0o755),
        )
        .unwrap();
        assert_eq!(
            prepare_socket_path(&socket, uid).unwrap_err().kind(),
            io::ErrorKind::PermissionDenied
        );
    }

    #[tokio::test]
    async fn socket_pairs_timeout_release_all_slots_and_warm_success_path() {
        let uid = process_uid().unwrap();
        let manifest = Arc::new(SharedManifest::new());
        let telemetry = Arc::new(TelemetrySnapshot::new(InferenceTelemetryBlock::default()));
        let permits = Arc::new(Semaphore::new(MAX_UDS_CONNECTIONS));
        // Warm the same authenticated read/write path using unnamed sockets.
        for _ in 0..4 {
            let (server, mut client) = UnixStream::pair().unwrap();
            client.write_all(b"snapshot").await.unwrap();
            let permit = Arc::clone(&permits).acquire_owned().await.unwrap();
            serve_peer(
                server,
                uid,
                Arc::clone(&manifest),
                Arc::clone(&telemetry),
                IO_DEADLINE,
                permit,
            )
            .await
            .unwrap();
            let mut response = Vec::new();
            client.read_to_end(&mut response).await.unwrap();
            assert!(String::from_utf8(response)
                .unwrap()
                .contains("tokens_generated"));
        }
        let mut tasks = Vec::new();
        let mut idle_clients = Vec::new();
        for _ in 0..MAX_UDS_CONNECTIONS {
            let (server, client) = UnixStream::pair().unwrap();
            idle_clients.push(client);
            let permit = Arc::clone(&permits).try_acquire_owned().unwrap();
            tasks.push(tokio::spawn(serve_peer(
                server,
                uid,
                Arc::clone(&manifest),
                Arc::clone(&telemetry),
                Duration::from_millis(20),
                permit,
            )));
        }
        assert!(Arc::clone(&permits).try_acquire_owned().is_err());
        for task in tasks {
            assert_eq!(
                task.await.unwrap().unwrap_err().kind(),
                io::ErrorKind::TimedOut
            );
        }
        assert_eq!(permits.available_permits(), MAX_UDS_CONNECTIONS);
        drop(idle_clients);
    }
}
