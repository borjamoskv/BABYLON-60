//! Protocolo de comunicación inter-proceso (IPC) Zero-HTTP.
//! Acopla el `SharedManifest` canónico (64B) y el Seqlock SPMC de telemetría con el canal Unix Domain Socket (UDS).

use std::path::Path;
use std::sync::atomic::{fence, AtomicU64, Ordering};
use std::sync::Arc;
use babylon60::manifest::SharedManifest;
use babylon60::seqlock::read as read_shared_manifest;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::UnixListener;

pub const DEFAULT_SOCKET_PATH: &str = "/tmp/eridu-infer.sock";

#[inline(always)]
fn armv9_acquire_read_barrier() {
    #[cfg(target_arch = "aarch64")]
    unsafe {
        core::arch::asm!("dmb ishld", options(nostack, preserves_flags));
    }
    #[cfg(not(target_arch = "aarch64"))]
    {
        fence(Ordering::Acquire);
    }
}

/// Seqlock Single-Producer Multi-Consumer alineado a 64 bytes con barrera `dmb ishld` (ARMv9).
#[repr(align(64))]
pub struct KudurruSeqlock<T: Copy> {
    sequence: AtomicU64,
    data: std::cell::UnsafeCell<T>,
}

unsafe impl<T: Copy + Send> Send for KudurruSeqlock<T> {}
unsafe impl<T: Copy + Sync> Sync for KudurruSeqlock<T> {}

impl<T: Copy> KudurruSeqlock<T> {
    pub fn new(initial: T) -> Self {
        Self {
            sequence: AtomicU64::new(0),
            data: std::cell::UnsafeCell::new(initial),
        }
    }

    /// Escritura atómica (solo un productor a la vez).
    pub fn write(&self, value: T) {
        let seq = self.sequence.load(Ordering::Acquire);
        self.sequence.store(seq.wrapping_add(1), Ordering::Relaxed);
        fence(Ordering::Release);

        unsafe {
            *self.data.get() = value;
        }

        fence(Ordering::Release);
        self.sequence.store(seq.wrapping_add(2), Ordering::Release);
    }

    /// Lectura optimista lock-free con barrera de hardware `dmb ishld` (RFO = 0).
    pub fn read(&self) -> T {
        loop {
            let seq0 = self.sequence.load(Ordering::Acquire);
            if seq0 & 1 != 0 {
                std::hint::spin_loop();
                continue;
            }

            armv9_acquire_read_barrier();
            let val = unsafe { *self.data.get() };
            armv9_acquire_read_barrier();

            let seq1 = self.sequence.load(Ordering::Acquire);
            if seq0 == seq1 {
                return val;
            }
            std::hint::spin_loop();
        }
    }
}

/// Estado atómico de telemetría de inferencia transmitido por Seqlock KUDURRU-64.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct InferenceTelemetryBlock {
    pub tokens_generated: u64,
    pub prompt_tokens: u64,
    pub last_latency_micros: u64,
    pub active_context_length: u32,
    pub is_generating: bool,
}

/// Inicia el listener de Unix Domain Socket acoplado al `SharedManifest` (64B) y al `KudurruSeqlock`.
pub async fn start_uds_listener<P: AsRef<Path>>(
    socket_path: P,
    manifest: Arc<SharedManifest>,
    telemetry: Arc<KudurruSeqlock<InferenceTelemetryBlock>>,
) -> Result<(), String> {
    let p = socket_path.as_ref();
    if p.exists() {
        let _ = std::fs::remove_file(p);
    }

    let listener = UnixListener::bind(p)
        .map_err(|e| format!("Error enlazando Unix Domain Socket en {}: {}", p.display(), e))?;

    tokio::spawn(async move {
        while let Ok((mut stream, _)) = listener.accept().await {
            let manifest_ref = Arc::clone(&manifest);
            let telemetry_ref = Arc::clone(&telemetry);
            tokio::spawn(async move {
                let mut buf = vec![0u8; 4096];
                if let Ok(n) = stream.read(&mut buf).await {
                    if n > 0 {
                        let t = telemetry_ref.read();
                        let (epoch, hash) = read_shared_manifest(&manifest_ref).unwrap_or((0, [0; 4]));
                        let response = format!(
                            "{{\"status\":\"ACK_ZERO_COPY_UMA\",\"rfo\":0,\"epoch\":{},\"hash_w0\":{},\"tokens_generated\":{},\"prompt_tokens\":{},\"last_latency_micros\":{}}}\n",
                            epoch, hash[0], t.tokens_generated, t.prompt_tokens, t.last_latency_micros
                        );
                        let _ = stream.write_all(response.as_bytes()).await;
                    }
                }
            });
        }
    });

    Ok(())
}
