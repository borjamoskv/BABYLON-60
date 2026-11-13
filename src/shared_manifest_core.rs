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

/// Umbral máximo de ticks lógicos que un lector FFI puede retener un slot antes de apoptosis.
pub const MAX_FFI_HOLD_TICKS: u64 = 64;
/// Bit 63 reservado para la bandera ortogonal de veneno (evita colisión con la generación).
pub const POISON_BIT: u64 = 1 << 63;
/// Centinela de veneno con bit 63 activo.
pub const POISON_SENTINEL: u64 = POISON_BIT | 0x5EAD_6060_0000_0000;
/// Constante de compatibilidad heredada.
pub const BABYLON_POISONED_U64: u64 = POISON_SENTINEL;
/// Inactive reader presence value; logical tick zero is not reserved.
pub const UNPINNED: u64 = 0;
// Writer ownership is separate from both terminal poison and the active index.
const WRITER_BUSY: u64 = 1 << 62;
const MAX_GENERATION: u64 = (WRITER_BUSY - 1) >> 1;

/// Control line shared by Ring-0 publishers and the terminal watchdog.
#[repr(C, align(128))]
pub struct WriterControlLine {
    // bit 0: active_idx; bits 1..61: generation; bit 62: writer; bit 63: poison.
    control_word: AtomicU64,
    /// Padding explícito para completar 128 bytes.
    pub _pad: [u8; 120],
}

impl WriterControlLine {
    /// Inicializa la línea de control del escritor.
    pub const fn new() -> Self {
        Self {
            control_word: AtomicU64::new(0),
            _pad: [0; 120],
        }
    }
}

impl Default for WriterControlLine {
    fn default() -> Self {
        Self::new()
    }
}

/// Monitoring line for one logical FFI reader lease.
#[repr(C, align(128))]
pub struct ReaderPinLine {
    // A separate presence word keeps every logical tick, including zero, valid.
    ffi_reader_pin_tick: AtomicU64,
    ffi_reader_active: AtomicU64,
    /// Padding explícito para completar 128 bytes.
    pub _pad: [u8; 112],
}

impl ReaderPinLine {
    /// Inicializa la línea de pin del lector FFI.
    pub const fn new() -> Self {
        Self {
            ffi_reader_pin_tick: AtomicU64::new(UNPINNED),
            ffi_reader_active: AtomicU64::new(UNPINNED),
            _pad: [0; 112],
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

/// Owned payload copied into or out of the shared atomic storage.
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

// The representation has the same size, alignment and byte offsets as PayloadSlot.
// Atomics, rather than post-copy validation alone, make slot reuse data-race-free.
#[repr(C, align(128))]
struct AtomicPayloadSlot {
    logical_tick: AtomicU64,
    state_hash: [AtomicU64; 4],
    metrics: [AtomicU64; 10],
    padding: AtomicU64,
}

impl AtomicPayloadSlot {
    const fn new() -> Self {
        Self {
            logical_tick: AtomicU64::new(0),
            state_hash: [const { AtomicU64::new(0) }; 4],
            metrics: [const { AtomicU64::new(0) }; 10],
            padding: AtomicU64::new(0),
        }
    }

    fn store(&self, payload: &PayloadSlot) {
        self.logical_tick
            .store(payload.logical_tick, Ordering::Relaxed);
        for (word, bytes) in self
            .state_hash
            .iter()
            .zip(payload.state_hash.chunks_exact(8))
        {
            word.store(
                u64::from_ne_bytes(bytes.try_into().unwrap()),
                Ordering::Relaxed,
            );
        }
        for (word, value) in self.metrics.iter().zip(payload.metrics) {
            word.store(value, Ordering::Relaxed);
        }
        self.padding
            .store(u64::from_ne_bytes(payload._pad), Ordering::Relaxed);
    }

    fn load(&self) -> PayloadSlot {
        let mut state_hash = [0; 32];
        for (bytes, word) in state_hash.chunks_exact_mut(8).zip(&self.state_hash) {
            bytes.copy_from_slice(&word.load(Ordering::Relaxed).to_ne_bytes());
        }
        PayloadSlot {
            logical_tick: self.logical_tick.load(Ordering::Relaxed),
            state_hash,
            metrics: core::array::from_fn(|i| self.metrics[i].load(Ordering::Relaxed)),
            _pad: self.padding.load(Ordering::Relaxed).to_ne_bytes(),
        }
    }
}

/// Two atomic payload slots in four 128-byte lines (512 bytes total).
/// Writers claim control with CAS and reject contention. Readers use only loads
/// and bounded retries; this protocol does not claim wait-free publication.
/// The offsets are retained, but this protocol requires atomic slot accesses by
/// every participant; do not share it with clients using the earlier raw-copy ABI.
#[repr(C, align(128))]
pub struct SharedManifestRing0 {
    /// Writer ownership, generation and terminal poison (first 128 bytes).
    pub writer_ctl: WriterControlLine,
    /// Línea 1 (128B): exclusiva de escritura FFI.
    pub reader_pin: ReaderPinLine,
    /// Líneas 2 y 3 (256B): Ping-Pong A/B.
    slots: [AtomicPayloadSlot; 2],
}

impl SharedManifestRing0 {
    /// Crea un nuevo manifiesto Ring-0 con 512 bytes de aislamiento.
    pub const fn new() -> Self {
        Self {
            writer_ctl: WriterControlLine::new(),
            reader_pin: ReaderPinLine::new(),
            slots: [const { AtomicPayloadSlot::new() }; 2],
        }
    }

    /// Check the single-reader watchdog using wrapping logical elapsed ticks.
    /// A backward clock is treated as an expired lease and fails closed.
    #[inline(always)]
    pub fn check_or_trigger_apoptosis(&self, current_tick: u64) -> Result<u64, u64> {
        let ctl = self.writer_ctl.control_word.load(Ordering::Acquire);
        if (ctl & POISON_BIT) != 0 {
            return Err(ctl);
        }
        if self.reader_pin.ffi_reader_active.load(Ordering::Acquire) != UNPINNED {
            let pinned_tick = self.reader_pin.ffi_reader_pin_tick.load(Ordering::Relaxed);
            if current_tick.wrapping_sub(pinned_tick) > MAX_FFI_HOLD_TICKS {
                self.writer_ctl
                    .control_word
                    .store(POISON_SENTINEL, Ordering::Release);
                return Err(POISON_SENTINEL);
            }
        }
        Ok(ctl)
    }

    /// Publish a coherent payload, rejecting a concurrent writer or terminal poison.
    /// An error with bit 62 set is transient writer contention; bit 63 is terminal.
    pub fn publish_and_audit(&self, next_data: &PayloadSlot, current_tick: u64) -> Result<(), u64> {
        let ctl = self.check_or_trigger_apoptosis(current_tick)?;
        if ctl & WRITER_BUSY != 0 {
            return Err(ctl);
        }
        let owned = ctl | WRITER_BUSY;
        self.writer_ctl
            .control_word
            .compare_exchange(ctl, owned, Ordering::Acquire, Ordering::Acquire)
            .map_err(|actual| actual | WRITER_BUSY)?;
        // Pair with the reader's acquire fence: observing any later payload word
        // requires its final control load to observe ownership or a later commit.
        fence(Ordering::Release);
        let current_gen = (ctl >> 1) & MAX_GENERATION;
        if current_gen == MAX_GENERATION {
            // Never wrap the generation: that would permit an ABA snapshot.
            let _ = self.writer_ctl.control_word.compare_exchange(
                owned,
                POISON_SENTINEL,
                Ordering::Release,
                Ordering::Acquire,
            );
            return Err(self.writer_ctl.control_word.load(Ordering::Acquire));
        }
        let active_idx = (ctl & 1) as usize;
        let write_idx = active_idx ^ 1;
        self.slots[write_idx].store(next_data);
        let next_ctrl = ((current_gen + 1) << 1) | (write_idx as u64);
        // Poison prevents committing the in-flight copy; it does not physically
        // freeze every slot store already in progress. The CAS cannot erase it.
        self.writer_ctl.control_word.compare_exchange(
            owned,
            next_ctrl,
            Ordering::Release,
            Ordering::Acquire,
        )?;
        Ok(())
    }

    /// Lectura consistente con validación post-copia del control_word.
    pub fn read_snapshot(&self, out_buf: &mut PayloadSlot) -> Result<(), u64> {
        for _ in 0..MAX_RETRIES {
            let ctrl_before = self.writer_ctl.control_word.load(Ordering::Acquire);
            if (ctrl_before & POISON_BIT) != 0 {
                return Err(ctrl_before);
            }
            if ctrl_before & WRITER_BUSY != 0 {
                core::hint::spin_loop();
                continue;
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

    /// Pin one logical FFI reader for the watchdog, including at tick zero.
    /// This single-reader lease is monitoring, not payload memory synchronization.
    #[inline(always)]
    pub fn ffi_pin(&self, tick: u64) {
        self.reader_pin
            .ffi_reader_pin_tick
            .store(tick, Ordering::Relaxed);
        self.reader_pin
            .ffi_reader_active
            .store(1, Ordering::Release);
        fence(Ordering::SeqCst);
    }

    /// Libera el pin de lectura de la C-FFI.
    #[inline(always)]
    pub fn ffi_unpin(&self) {
        self.reader_pin
            .ffi_reader_active
            .store(UNPINNED, Ordering::Release);
    }
}

impl Default for SharedManifestRing0 {
    fn default() -> Self {
        Self::new()
    }
}

const _: () = {
    assert!(core::mem::size_of::<AtomicPayloadSlot>() == 128);
    assert!(core::mem::align_of::<AtomicPayloadSlot>() == 128);
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
    fn ring0_atomic_payload_roundtrip() {
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
    fn ring0_asymmetric_external_apoptosis_on_stalled_reader() {
        let manifest = SharedManifestRing0::new();
        let mut slot = PayloadSlot::zeroed();

        // 1. Simular lector FFI anclado en tick 100
        manifest.ffi_pin(100);

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

    #[test]
    fn ring0_layout_remains_four_128_byte_lines() {
        use core::mem::{align_of, offset_of, size_of};
        assert_eq!(size_of::<SharedManifestRing0>(), 512);
        assert_eq!(align_of::<SharedManifestRing0>(), 128);
        assert_eq!(offset_of!(SharedManifestRing0, writer_ctl), 0);
        assert_eq!(offset_of!(SharedManifestRing0, reader_pin), 128);
        assert_eq!(offset_of!(SharedManifestRing0, slots), 256);
        assert_eq!(size_of::<AtomicPayloadSlot>(), size_of::<PayloadSlot>());
        assert_eq!(
            offset_of!(AtomicPayloadSlot, state_hash),
            offset_of!(PayloadSlot, state_hash)
        );
        assert_eq!(
            offset_of!(AtomicPayloadSlot, metrics),
            offset_of!(PayloadSlot, metrics)
        );
    }

    #[test]
    fn ring0_tick_zero_and_wrapping_clock_obey_the_64_tick_budget() {
        for pinned_at in [0, 1, u64::MAX - 10, u64::MAX] {
            let manifest = SharedManifestRing0::new();
            manifest.ffi_pin(pinned_at);
            assert!(manifest
                .check_or_trigger_apoptosis(pinned_at.wrapping_add(64))
                .is_ok());
            assert_eq!(
                manifest.check_or_trigger_apoptosis(pinned_at.wrapping_add(65)),
                Err(POISON_SENTINEL)
            );
            manifest.ffi_unpin();
            assert_eq!(
                manifest.publish_and_audit(&PayloadSlot::zeroed(), 0),
                Err(POISON_SENTINEL)
            );
        }
        let manifest = SharedManifestRing0::new();
        manifest.ffi_pin(0);
        manifest.ffi_unpin();
        assert!(manifest.check_or_trigger_apoptosis(65).is_ok());
    }

    #[test]
    fn ring0_rejects_busy_writers_and_never_wraps_the_generation() {
        let manifest = SharedManifestRing0::new();
        manifest
            .writer_ctl
            .control_word
            .store(WRITER_BUSY, Ordering::Release);
        assert_eq!(
            manifest.publish_and_audit(&PayloadSlot::zeroed(), 0),
            Err(WRITER_BUSY)
        );
        let mut unchanged = PayloadSlot::zeroed();
        unchanged.logical_tick = 999;
        assert!(manifest.read_snapshot(&mut unchanged).is_err());
        assert_eq!(unchanged.logical_tick, 999);
        manifest
            .writer_ctl
            .control_word
            .store(MAX_GENERATION << 1, Ordering::Release);
        assert_eq!(
            manifest.publish_and_audit(&PayloadSlot::zeroed(), 0),
            Err(POISON_SENTINEL)
        );
        assert_eq!(manifest.read_snapshot(&mut unchanged), Err(POISON_SENTINEL));
    }

    #[test]
    fn ring0_concurrent_writers_publish_only_coherent_snapshots() {
        let manifest = SharedManifestRing0::new();
        let done = AtomicU32::new(0);
        let iterations = if cfg!(miri) { 4 } else { 512 };
        thread::scope(|scope| {
            for writer in 1..=2 {
                let manifest = &manifest;
                let done = &done;
                scope.spawn(move || {
                    for index in 1..=iterations {
                        let tick = (writer << 32) | index;
                        let mut payload = PayloadSlot::zeroed();
                        payload.logical_tick = tick;
                        payload.metrics = [tick; 10];
                        payload.state_hash = tick.to_ne_bytes().repeat(4).try_into().unwrap();
                        payload._pad = tick.to_ne_bytes();
                        while let Err(control) = manifest.publish_and_audit(&payload, 0) {
                            assert_eq!(control & POISON_BIT, 0);
                            thread::yield_now();
                        }
                    }
                    done.fetch_add(1, Ordering::Release);
                });
            }
            let mut output = PayloadSlot::zeroed();
            while done.load(Ordering::Acquire) != 2 {
                if manifest.read_snapshot(&mut output).is_ok() {
                    let tick = output.logical_tick;
                    assert_eq!(output.metrics, [tick; 10]);
                    assert_eq!(output.state_hash, tick.to_ne_bytes().repeat(4).as_slice());
                    assert_eq!(output._pad, tick.to_ne_bytes());
                }
                thread::yield_now();
            }
        });
    }

    #[test]
    fn ring0_watchdog_poison_survives_an_in_flight_writer() {
        let manifest = SharedManifestRing0::new();
        manifest.ffi_pin(0);
        thread::scope(|scope| {
            scope.spawn(|| {
                let _ = manifest.publish_and_audit(&PayloadSlot::zeroed(), 0);
            });
            scope.spawn(|| {
                assert_eq!(
                    manifest.check_or_trigger_apoptosis(65),
                    Err(POISON_SENTINEL)
                );
            });
        });
        assert_eq!(
            manifest.publish_and_audit(&PayloadSlot::zeroed(), 0),
            Err(POISON_SENTINEL)
        );
        assert_eq!(
            manifest.read_snapshot(&mut PayloadSlot::zeroed()),
            Err(POISON_SENTINEL)
        );
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
            .control_word
            .store(WRITER_BUSY, Ordering::Release);
        assert_eq!(
            manifest.publish_and_audit(&PayloadSlot::zeroed(), 1),
            Err(WRITER_BUSY)
        );
        assert_eq!(manifest.writer_ctl.control_word.load(Ordering::Acquire), WRITER_BUSY);
        manifest
            .writer_ctl
            .control_word
            .store(0, Ordering::Release);
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
            .store(MAX_GENERATION << 1, Ordering::Release);
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

}
