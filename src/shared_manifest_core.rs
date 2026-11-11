use core::sync::atomic::{fence, AtomicU32, AtomicU64, Ordering};
/// Admission is open.
pub const RUNNING: u32 = 1;
/// Terminal admission state.
pub const POISONED: u32 = 0xDEAD_6060;
/// Maximum bounded snapshot/freeze attempts.
pub const MAX_RETRIES: usize = 10_000;

/// Shared C-ABI storage and protocol. All payload accesses are atomic.
#[repr(C, align(64))]
#[derive(Debug)]
pub struct SharedManifest {
    /// Admission flag at byte zero.
    pub status_flag: AtomicU32,
    /// Wrapping 32-bit sequence; odd denotes exclusive ownership.
    pub seq: AtomicU32,
    /// Caller-supplied logical epoch.
    pub epoch_id: AtomicU64,
    /// Atomic hash words.
    pub payload_hash: [AtomicU64; 4],
    /// Fixed C ABI padding.
    pub _padding: [u8; 16],
}
impl SharedManifest {
    /// Empty running manifest with logical epoch zero.
    pub const fn new() -> Self {
        Self {
            status_flag: AtomicU32::new(RUNNING),
            seq: AtomicU32::new(0),
            epoch_id: AtomicU64::new(0),
            payload_hash: [const { AtomicU64::new(0) }; 4],
            _padding: [0; 16],
        }
    }
    /// Compatibility alias for the empty running manifest.
    pub const fn zeroed() -> Self {
        Self::new()
    }

    /// Publish under exclusive CAS ownership; reject contention or poison.
    pub fn publish(&self, epoch: u64, hash: &[u64; 4]) -> Result<(), &'static str> {
        if self.status_flag.load(Ordering::Acquire) == POISONED {
            return Err("POISONED_STATE");
        }
        let seq = self.seq.load(Ordering::Acquire);
        if seq & 1 != 0
            || self
                .seq
                .compare_exchange(
                    seq,
                    seq.wrapping_add(1),
                    Ordering::Acquire,
                    Ordering::Relaxed,
                )
                .is_err()
        {
            return Err("WRITER_BUSY");
        }
        // The odd marker must precede every payload store. Matching reader
        // fence detects a later payload even when its initial seq was stale.
        fence(Ordering::Release);
        if self.status_flag.load(Ordering::Acquire) == POISONED {
            self.seq.store(seq.wrapping_add(2), Ordering::Release);
            return Err("POISONED_STATE");
        }
        self.epoch_id.store(epoch, Ordering::Relaxed);
        for (slot, value) in self.payload_hash.iter().zip(hash) {
            slot.store(*value, Ordering::Relaxed);
        }
        self.seq.store(seq.wrapping_add(2), Ordering::Release);
        Ok(())
    }
    /// Read a coherent snapshot only while admission remains open.
    pub fn read(&self) -> Option<(u64, [u64; 4])> {
        if self.status_flag.load(Ordering::Acquire) == POISONED {
            return None;
        }
        let snapshot = self.read_snapshot();
        if self.status_flag.load(Ordering::Acquire) == POISONED {
            None
        } else {
            snapshot
        }
    }
    /// Coherent forensic read, also available after admission is poisoned.
    /// This is not an authorization check. A frozen odd slot returns None.
    pub fn read_snapshot(&self) -> Option<(u64, [u64; 4])> {
        for _ in 0..MAX_RETRIES {
            let first = self.seq.load(Ordering::Acquire);
            if first & 1 != 0 {
                core::hint::spin_loop();
                continue;
            }
            let epoch = self.epoch_id.load(Ordering::Relaxed);
            let hash = core::array::from_fn(|i| self.payload_hash[i].load(Ordering::Relaxed));
            fence(Ordering::Acquire);
            if first == self.seq.load(Ordering::Acquire) {
                return Some((epoch, hash));
            }
            core::hint::spin_loop();
        }
        None
    }
    /// Freeze the payload before a terminal receipt. Never steal an active
    /// writer's odd sequence. Failure leaves poison set and emits no receipt.
    pub fn freeze(&self) -> Result<u64, &'static str> {
        self.status_flag.store(POISONED, Ordering::SeqCst);
        for _ in 0..MAX_RETRIES {
            let seq = self.seq.load(Ordering::Acquire);
            if seq & 1 == 0
                && self
                    .seq
                    .compare_exchange(
                        seq,
                        seq.wrapping_add(1),
                        Ordering::AcqRel,
                        Ordering::Relaxed,
                    )
                    .is_ok()
            {
                return Ok(self.epoch_id.load(Ordering::Acquire));
            }
            core::hint::spin_loop();
        }
        Err("TERMINAL_SNAPSHOT_UNAVAILABLE")
    }
}
impl Default for SharedManifest {
    fn default() -> Self {
        Self::new()
    }
}
const _: () = {
    assert!(core::mem::size_of::<SharedManifest>() == 64);
    assert!(core::mem::align_of::<SharedManifest>() == 64);
};

// ---------------------------------------------------------------------------
// SharedManifestRing0: Doble Buffer Ping-Pong Left-Right (Apple Silicon 128B)
// Con Apoptosis Asimétrica Externa (INV_C5_APPLE_128B_PING_PONG & INV_C5_ASYMMETRIC_APOPTOSIS)
// ---------------------------------------------------------------------------

use core::sync::atomic::AtomicBool;

/// Umbral máximo de ticks lógicos que un lector FFI puede retener un slot antes de apoptosis.
pub const MAX_FFI_HOLD_TICKS: u64 = 64;
/// Bit 63 reservado para la bandera ortogonal de veneno (evita colisión con la generación).
pub const POISON_BIT: u64 = 1 << 63;
/// Centinela de veneno con bit 63 activo.
pub const POISON_SENTINEL: u64 = POISON_BIT | 0x5EAD_6060_0000_0000;
/// Constante de compatibilidad heredada.
pub const BABYLON_POISONED_U64: u64 = POISON_SENTINEL;
/// Valor inactivo del pin de lectura FFI.
pub const UNPINNED: u64 = 0;

/// Línea 0 (128B): exclusiva de escritura del productor Ring-0.
#[repr(C, align(128))]
pub struct WriterControlLine {
    /// bit 0: active_idx | bits 1..62: monotonic_gen | bit 63: POISON_BIT
    pub control_word: AtomicU64,
    /// Bounded admission for publishers; occupies former padding, not a payload line.
    publishing: AtomicBool,
    /// Padding explícito para completar 128 bytes.
    pub _pad: [u8; 119],
}

impl WriterControlLine {
    /// Inicializa la línea de control del escritor.
    pub const fn new() -> Self {
        Self {
            control_word: AtomicU64::new(0),
            publishing: AtomicBool::new(false),
            _pad: [0; 119],
        }
    }
}

impl Default for WriterControlLine {
    fn default() -> Self {
        Self::new()
    }
}

/// Línea 1 (128B): exclusiva de escritura del consumidor FFI.
#[repr(C, align(128))]
pub struct ReaderPinLine {
    /// Escrito por el consumidor FFI; leído por el productor Ring-0.
    pub ffi_reader_pin_tick: AtomicU64,
    /// Padding explícito para completar 128 bytes.
    pub _pad: [u8; 120],
}

impl ReaderPinLine {
    /// Inicializa la línea de pin del lector FFI.
    pub const fn new() -> Self {
        Self {
            ffi_reader_pin_tick: AtomicU64::new(UNPINNED),
            _pad: [0; 120],
        }
    }
}

impl Default for ReaderPinLine {
    fn default() -> Self {
        Self::new()
    }
}

const _: () = {
    assert!(core::mem::size_of::<WriterControlLine>() == 128);
    assert!(core::mem::align_of::<WriterControlLine>() == 128);
    assert!(core::mem::size_of::<ReaderPinLine>() == 128);
    assert!(core::mem::align_of::<ReaderPinLine>() == 128);
};

/// Slot de datos atómicamente aislado a 128 bytes (tamaño de línea de coherencia en Apple Silicon M1-M4).
#[repr(C, align(128))]
pub struct PayloadSlot {
    /// Tick lógico causal de la transición.
    pub logical_tick: u64,
    /// Digest de estado o payload computado canónicamente.
    pub state_hash: [u8; 32],
    /// Telemetría y métricas operativas de transición (10 palabras u64).
    pub metrics: [u64; 10],
    /// Padding explícito a 128 bytes.
    pub _pad: [u8; 8],
}

impl PayloadSlot {
    /// Inicializa un slot vacío con ceros en memoria.
    pub const fn zeroed() -> Self {
        Self {
            logical_tick: 0,
            state_hash: [0; 32],
            metrics: [0; 10],
            _pad: [0; 8],
        }
    }
}

impl Clone for PayloadSlot {
    fn clone(&self) -> Self {
        *self
    }
}

impl Copy for PayloadSlot {}

const _: () = {
    assert!(core::mem::size_of::<PayloadSlot>() == 128);
    assert!(core::mem::align_of::<PayloadSlot>() == 128);
};

/// Atomic storage has the same size as the caller-facing copied payload.
/// Consumers must use read_snapshot rather than non-atomic raw slot copies.
#[repr(C, align(128))]
pub struct AtomicPayloadSlot {
    words: [AtomicU64; 16],
}

impl AtomicPayloadSlot {
    const fn new() -> Self {
        Self {
            words: [const { AtomicU64::new(0) }; 16],
        }
    }

    fn store(&self, payload: &PayloadSlot) {
        self.words[0].store(payload.logical_tick, Ordering::Relaxed);
        for (word, bytes) in self.words[1..5]
            .iter()
            .zip(payload.state_hash.as_chunks::<8>().0)
        {
            word.store(u64::from_ne_bytes(*bytes), Ordering::Relaxed);
        }
        for (word, value) in self.words[5..15].iter().zip(payload.metrics) {
            word.store(value, Ordering::Relaxed);
        }
        self.words[15].store(u64::from_ne_bytes(payload._pad), Ordering::Relaxed);
    }

    fn load(&self) -> PayloadSlot {
        let mut payload = PayloadSlot::zeroed();
        payload.logical_tick = self.words[0].load(Ordering::Relaxed);
        for (bytes, word) in payload
            .state_hash
            .as_chunks_mut::<8>()
            .0
            .iter_mut()
            .zip(&self.words[1..5])
        {
            *bytes = word.load(Ordering::Relaxed).to_ne_bytes();
        }
        for (value, word) in payload.metrics.iter_mut().zip(&self.words[5..15]) {
            *value = word.load(Ordering::Relaxed);
        }
        payload._pad = self.words[15].load(Ordering::Relaxed).to_ne_bytes();
        payload
    }
}

struct PublicationGuard<'a>(&'a AtomicBool);

impl Drop for PublicationGuard<'_> {
    fn drop(&mut self) {
        self.0.store(false, Ordering::Release);
    }
}

const _: () = {
    assert!(core::mem::size_of::<AtomicPayloadSlot>() == 128);
    assert!(core::mem::align_of::<AtomicPayloadSlot>() == 128);
};

/// Registro Ping-Pong Left-Right con cuádruple aislamiento de línea de caché de 128B (512B total):
/// 1. Línea 0 (128B): Exclusiva de escritura del productor Ring-0 (control_word).
/// 2. Línea 1 (128B): Exclusiva de escritura del consumidor FFI (ffi_reader_pin_tick).
/// 3. Línea 2 (128B): Slot A Payload.
/// 4. Línea 3 (128B): Slot B Payload.
#[repr(C, align(128))]
pub struct SharedManifestRing0 {
    /// Línea 0 (128B): exclusiva de escritura Ring-0.
    pub writer_ctl: WriterControlLine,
    /// Línea 1 (128B): exclusiva de escritura FFI.
    pub reader_pin: ReaderPinLine,
    /// Líneas 2 y 3 (256B): Ping-Pong A/B.
    pub slots: [AtomicPayloadSlot; 2],
}

impl SharedManifestRing0 {
    /// Crea un nuevo manifiesto Ring-0 con 512 bytes de aislamiento.
    pub const fn new() -> Self {
        Self {
            writer_ctl: WriterControlLine::new(),
            reader_pin: ReaderPinLine::new(),
            slots: [AtomicPayloadSlot::new(), AtomicPayloadSlot::new()],
        }
    }

    /// Comprueba o dispara apoptosis asimétrica externa en silicio.
    #[inline(always)]
    pub fn check_or_trigger_apoptosis(&self, current_tick: u64) -> Result<u64, u64> {
        let ctl = self.writer_ctl.control_word.load(Ordering::Acquire);
        if (ctl & POISON_BIT) != 0 {
            return Err(ctl);
        }
        let pinned_tick = self.reader_pin.ffi_reader_pin_tick.load(Ordering::Acquire);
        if pinned_tick != UNPINNED && current_tick.saturating_sub(pinned_tick) > MAX_FFI_HOLD_TICKS
        {
            self.writer_ctl
                .control_word
                .store(POISON_SENTINEL, Ordering::Release);
            return Err(POISON_SENTINEL);
        }
        Ok(ctl)
    }

    /// Bounded publication: reject competing publishers or a terminal control state.
    pub fn publish_and_audit(&self, next_data: &PayloadSlot, current_tick: u64) -> Result<(), u64> {
        if self
            .writer_ctl
            .publishing
            .compare_exchange(false, true, Ordering::Acquire, Ordering::Relaxed)
            .is_err()
        {
            return Err(self.writer_ctl.control_word.load(Ordering::Acquire));
        }
        let _publication = PublicationGuard(&self.writer_ctl.publishing);
        let ctl = self.check_or_trigger_apoptosis(current_tick)?;
        let current_gen = ctl >> 1;
        if current_gen == (1 << 62) - 1 {
            // Never wrap the generation and allow a snapshot's control value to repeat.
            self.writer_ctl
                .control_word
                .store(POISON_SENTINEL, Ordering::Release);
            return Err(POISON_SENTINEL);
        }

        let active_idx = (ctl & 1) as usize;
        let write_idx = active_idx ^ 1;
        // If a reader sees a later overwrite, its acquire fence must also observe
        // the preceding control publication, so it cannot accept a stale generation.
        fence(Ordering::Release);
        self.slots[write_idx].store(next_data);
        let next_gen = current_gen + 1;
        let next_ctrl = (next_gen << 1) | (write_idx as u64);
        // Another thread may poison the channel while the payload is being stored.
        // A failed CAS must not resurrect admission.
        self.writer_ctl
            .control_word
            .compare_exchange(ctl, next_ctrl, Ordering::Release, Ordering::Relaxed)
            .map(|_| ())
    }

    /// Lectura consistente con validación post-copia del control_word.
    pub fn read_snapshot(&self, out_buf: &mut PayloadSlot) -> Result<(), u64> {
        for _ in 0..MAX_RETRIES {
            let ctrl_before = self.writer_ctl.control_word.load(Ordering::Acquire);
            if (ctrl_before & POISON_BIT) != 0 {
                return Err(ctrl_before);
            }

            let active_idx = (ctrl_before & 1) as usize;
            let snapshot = self.slots[active_idx].load();

            fence(Ordering::Acquire);
            let ctrl_after = self.writer_ctl.control_word.load(Ordering::Acquire);
            if ctrl_before == ctrl_after {
                *out_buf = snapshot;
                return Ok(());
            }
            core::hint::spin_loop();
        }
        Err(self.writer_ctl.control_word.load(Ordering::Acquire))
    }

    /// Fija el pin de lectura de la C-FFI para el centinela de apoptosis.
    #[inline(always)]
    pub fn ffi_pin(&self, tick: u64) {
        self.reader_pin
            .ffi_reader_pin_tick
            .store(tick, Ordering::Release);
        fence(Ordering::SeqCst);
    }

    /// Libera el pin de lectura de la C-FFI.
    #[inline(always)]
    pub fn ffi_unpin(&self) {
        self.reader_pin
            .ffi_reader_pin_tick
            .store(UNPINNED, Ordering::Release);
    }
}

impl Default for SharedManifestRing0 {
    fn default() -> Self {
        Self::new()
    }
}

const _: () = {
    assert!(core::mem::size_of::<SharedManifestRing0>() == 512);
    assert!(core::mem::align_of::<SharedManifestRing0>() == 128);
};

#[cfg(test)]
mod protocol_regressions {
    extern crate std;
    use super::*;
    use std::sync::Arc;
    use std::thread;

    #[test]
    fn halt_does_not_unlock_an_active_writer() {
        let m = SharedManifest::new();
        m.seq.store(1, Ordering::Release); // paused writer owns the odd marker
        assert_eq!(m.freeze(), Err("TERMINAL_SNAPSHOT_UNAVAILABLE"));
        assert_eq!(m.seq.load(Ordering::Acquire), 1);
        assert!(m.publish(99, &[99; 4]).is_err());
        // Writer finishes; a subsequent freeze may now seal its final epoch.
        m.epoch_id.store(7, Ordering::Relaxed);
        m.seq.store(2, Ordering::Release);
        assert_eq!(m.freeze(), Ok(7));
        assert!(m.publish(8, &[8; 4]).is_err());
        assert_eq!(m.epoch_id.load(Ordering::Acquire), 7);
    }

    #[test]
    fn multiple_writers_never_publish_mixed_payloads() {
        let m = Arc::new(SharedManifest::new());
        let mut writers = std::vec::Vec::new();
        for producer in 0..2 {
            let shared = Arc::clone(&m);
            writers.push(thread::spawn(move || {
                for step in 1..20_000 {
                    let value = step * 2 + producer;
                    while shared.publish(value, &[value; 4]).is_err() {
                        thread::yield_now();
                    }
                }
            }));
        }
        for _ in 0..20_000 {
            if let Some((epoch, hash)) = m.read() {
                assert_eq!(hash, [epoch; 4]);
            }
        }
        for writer in writers {
            writer.join().unwrap();
        }
    }

    #[test]
    fn concurrent_snapshots_and_terminal_freeze_after_warmup() {
        let m = Arc::new(SharedManifest::new());
        for epoch in 0..1_000 {
            m.publish(epoch, &[epoch; 4]).unwrap();
        }
        let writer = Arc::clone(&m);
        let h = thread::spawn(move || {
            for epoch in 1_000..101_000 {
                if writer.publish(epoch, &[epoch; 4]).is_err() {
                    break;
                }
            }
        });
        for _ in 0..20_000 {
            if let Some((epoch, hash)) = m.read() {
                assert_eq!(hash, [epoch; 4]);
            }
        }
        // Bounded freeze may report contention; joining the writer permits a retry.
        let first = m.freeze();
        h.join().unwrap();
        let frozen = match first {
            Ok(epoch) => epoch,
            Err(_) => m.freeze().unwrap(),
        };
        assert_eq!(m.epoch_id.load(Ordering::Acquire), frozen);
        assert!(m.publish(frozen + 1, &[0; 4]).is_err());
        assert!(m.read().is_none());
    }

    #[test]
    fn ring0_ping_pong_wait_free_roundtrip() {
        let manifest = SharedManifestRing0::new();
        let mut slot = PayloadSlot::zeroed();
        slot.logical_tick = 42;
        slot.state_hash = [0xAA; 32];
        slot.metrics[0] = 1000;

        assert!(manifest.publish_and_audit(&slot, 42).is_ok());

        let mut read_buf = PayloadSlot::zeroed();
        assert!(manifest.read_snapshot(&mut read_buf).is_ok());
        assert_eq!(read_buf.logical_tick, 42);
        assert_eq!(read_buf.state_hash, [0xAA; 32]);
        assert_eq!(read_buf.metrics[0], 1000);
    }

    #[test]
    fn ring0_atomic_storage_preserves_layout_and_every_payload_word() {
        assert_eq!(core::mem::size_of::<SharedManifestRing0>(), 512);
        assert_eq!(core::mem::align_of::<SharedManifestRing0>(), 128);
        assert_eq!(core::mem::offset_of!(SharedManifestRing0, writer_ctl), 0);
        assert_eq!(core::mem::offset_of!(SharedManifestRing0, reader_pin), 128);
        assert_eq!(core::mem::offset_of!(SharedManifestRing0, slots), 256);
        let manifest = SharedManifestRing0::new();
        let mut payload = PayloadSlot::zeroed();
        payload.logical_tick = 7;
        payload.state_hash = core::array::from_fn(|i| i as u8);
        payload.metrics = core::array::from_fn(|i| i as u64 + 90);
        payload._pad = [0xAB; 8];
        manifest.publish_and_audit(&payload, 7).unwrap();
        let mut snapshot = PayloadSlot::zeroed();
        manifest.read_snapshot(&mut snapshot).unwrap();
        assert_eq!(snapshot.logical_tick, payload.logical_tick);
        assert_eq!(snapshot.state_hash, payload.state_hash);
        assert_eq!(snapshot.metrics, payload.metrics);
        assert_eq!(snapshot._pad, payload._pad);
    }

    #[test]
    fn ring0_competing_publisher_is_rejected_without_changing_control() {
        let manifest = SharedManifestRing0::new();
        manifest
            .writer_ctl
            .publishing
            .store(true, Ordering::Release);
        assert_eq!(
            manifest.publish_and_audit(&PayloadSlot::zeroed(), 1),
            Err(0)
        );
        assert_eq!(manifest.writer_ctl.control_word.load(Ordering::Acquire), 0);
        manifest
            .writer_ctl
            .publishing
            .store(false, Ordering::Release);
        assert!(manifest
            .publish_and_audit(&PayloadSlot::zeroed(), 1)
            .is_ok());
    }

    #[test]
    fn ring0_generation_exhaustion_does_not_wrap_or_reopen_admission() {
        let manifest = SharedManifestRing0::new();
        manifest
            .writer_ctl
            .control_word
            .store(((1u64 << 62) - 1) << 1, Ordering::Release);
        assert_eq!(
            manifest.publish_and_audit(&PayloadSlot::zeroed(), 1),
            Err(POISON_SENTINEL)
        );
        assert_eq!(
            manifest.publish_and_audit(&PayloadSlot::zeroed(), 2),
            Err(POISON_SENTINEL)
        );
        assert_eq!(
            manifest.read_snapshot(&mut PayloadSlot::zeroed()),
            Err(POISON_SENTINEL)
        );
    }

    #[test]
    fn ring0_multiple_publishers_and_readers_never_accept_mixed_words() {
        let manifest = Arc::new(SharedManifestRing0::new());
        let start = Arc::new(std::sync::Barrier::new(5));
        let mut handles = std::vec::Vec::new();
        for producer in 0..2 {
            let shared = Arc::clone(&manifest);
            let start = Arc::clone(&start);
            handles.push(thread::spawn(move || {
                start.wait();
                for step in 1..2_000 {
                    let value = step * 2 + producer;
                    let mut payload = PayloadSlot::zeroed();
                    payload.logical_tick = value;
                    payload.state_hash = [value as u8; 32];
                    payload.metrics = [value; 10];
                    while shared.publish_and_audit(&payload, value).is_err() {
                        thread::yield_now();
                    }
                }
            }));
        }
        for _ in 0..2 {
            let shared = Arc::clone(&manifest);
            let start = Arc::clone(&start);
            handles.push(thread::spawn(move || {
                start.wait();
                for _ in 0..4_000 {
                    let mut snapshot = PayloadSlot::zeroed();
                    if shared.read_snapshot(&mut snapshot).is_ok() {
                        assert_eq!(snapshot.state_hash, [snapshot.logical_tick as u8; 32]);
                        assert_eq!(snapshot.metrics, [snapshot.logical_tick; 10]);
                    }
                }
            }));
        }
        start.wait();
        for handle in handles {
            handle.join().unwrap();
        }
    }

    #[test]
    fn ring0_concurrent_poison_remains_terminal_after_publisher_finishes() {
        let manifest = Arc::new(SharedManifestRing0::new());
        let start = Arc::new(std::sync::Barrier::new(2));
        let shared = Arc::clone(&manifest);
        let ready = Arc::clone(&start);
        let publisher = thread::spawn(move || {
            ready.wait();
            for tick in 1..10_000 {
                if shared
                    .publish_and_audit(&PayloadSlot::zeroed(), tick)
                    .is_err()
                {
                    break;
                }
            }
        });
        start.wait();
        manifest
            .writer_ctl
            .control_word
            .store(POISON_SENTINEL, Ordering::Release);
        publisher.join().unwrap();
        assert_eq!(
            manifest.writer_ctl.control_word.load(Ordering::Acquire),
            POISON_SENTINEL
        );
        assert!(manifest.read_snapshot(&mut PayloadSlot::zeroed()).is_err());
    }

    #[test]
    fn ring0_asymmetric_external_apoptosis_on_stalled_reader() {
        let manifest = SharedManifestRing0::new();
        let mut slot = PayloadSlot::zeroed();

        // 1. Simular lector FFI anclado en tick 100
        manifest
            .reader_pin
            .ffi_reader_pin_tick
            .store(100, Ordering::Release);

        // 2. Productor avanza dentro del presupuesto permitido (delta = 50 <= 64)
        slot.logical_tick = 150;
        assert!(manifest.publish_and_audit(&slot, 150).is_ok());

        // 3. Productor avanza más allá de MAX_FFI_HOLD_TICKS (delta = 70 > 64)
        // El productor dispara apoptosis asimétrica en silicio
        slot.logical_tick = 170;
        let res = manifest.publish_and_audit(&slot, 170);
        assert_eq!(res, Err(BABYLON_POISONED_U64));
        assert_eq!(
            manifest.writer_ctl.control_word.load(Ordering::Acquire),
            BABYLON_POISONED_U64
        );

        // 4. Posteriores lecturas fallan por estado POISONED
        let mut read_buf = PayloadSlot::zeroed();
        assert_eq!(
            manifest.read_snapshot(&mut read_buf),
            Err(BABYLON_POISONED_U64)
        );
    }
}
