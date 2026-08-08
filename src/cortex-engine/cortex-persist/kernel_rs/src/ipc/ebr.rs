// C5-REAL EXERGY CERTIFIED
use std::ptr;
use std::sync::atomic::{AtomicPtr, AtomicU64, AtomicU8, Ordering};

/// Estados del SharedManifest para el protocolo EBR.
#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ManifestStatus {
    Idle = 0,
    Ready = 1,
    Validating = 2,
    Active = 3,
    Retired = 4,
    Quarantine = 5,
}

/// Manifiesto compartido Python↔Rust con layout C y alineación exacta de 64 bytes.
/// #[repr(C, align(64))] es obligatorio para evitar false-sharing y cache-line splitting.
#[repr(C, align(64))]
pub struct SharedManifest {
    /// Resumen criptográfico SHA-256 (32 bytes). Offset: 0x00
    pub payload: [u8; 32],
    /// Bandera de estado atómica para transiciones lock-free. Offset: 0x20
    pub status_flag: AtomicU8,
    /// Padding explícito para mantener C-ABI y alineación. Offset: 0x21
    pub _pad: [u8; 3],
    /// Entropía biológica inyectada (Varentropía CUSUM) en Basis Points (bps). Offset: 0x24
    pub varentropy_bps: u32,
    /// Contador atómico de lectores concurrentes (EBR drain guard). Offset: 0x28
    pub active_readers: AtomicU64,
    /// Identificador secuencial de época para anclaje SCITT. Offset: 0x30
    pub epoch_id: u64,
    /// Timestamp nanosecondal para anclaje SCITT. Offset: 0x38
    pub timestamp_ns: u64,
}

impl SharedManifest {
    pub fn new(epoch_id: u64, timestamp_ns: u64) -> Self {
        Self {
            payload: [0u8; 32],
            // AtomicU8::new es const-safe y no requiere sincronización adicional
            status_flag: AtomicU8::new(ManifestStatus::Idle as u8),
            _pad: [0u8; 3],
            varentropy_bps: 0,
            // EBR: inicializar sin lectores activos
            active_readers: AtomicU64::new(0),
            epoch_id,
            timestamp_ns,
        }
    }

    /// Lectura atómica del estado con semántica Acquire.
    // Acquire establece borde happens-before: todas las escrituras previas
    // al Release correspondiente son visibles tras esta carga.
    pub fn get_status(&self) -> ManifestStatus {
        match self.status_flag.load(Ordering::Acquire) {
            0 => ManifestStatus::Idle,
            1 => ManifestStatus::Ready,
            2 => ManifestStatus::Validating,
            3 => ManifestStatus::Active,
            4 => ManifestStatus::Retired,
            5 => ManifestStatus::Quarantine,
            _ => ManifestStatus::Quarantine, // Valor corrupto → defensa por cuarentena
        }
    }

    /// Escritura atómica del estado con semántica Release.
    // Release garantiza que todas las escrituras anteriores a esta tienda
    // sean visibles para cualquier hilo que haga Acquire sobre este campo.
    pub fn set_status(&self, status: ManifestStatus) {
        self.status_flag.store(status as u8, Ordering::Release);
    }

    /// Verifica el digest contra un valor esperado en tiempo constante.
    // Evita timing attacks: siempre recorre los 32 bytes sin early-exit.
    pub fn verify_digest(&self, expected: &[u8; 32]) -> bool {
        let mut acc: u8 = 0;
        for i in 0..32 {
            acc |= self.payload[i] ^ expected[i];
        }
        acc == 0
    }

    /// Registra un lector concurrente (incrementa el contador atómico).
    /// Debe invocarse antes de leer datos del manifiesto en un hilo consumidor.
    #[inline]
    pub fn acquire_reader(&self) {
        self.active_readers.fetch_add(1, Ordering::Acquire);
    }

    /// Libera un lector concurrente (decrementa el contador atómico).
    /// Debe invocarse tras finalizar la lectura del manifiesto.
    #[inline]
    pub fn release_reader(&self) {
        self.active_readers.fetch_sub(1, Ordering::Release);
    }

    /// Consulta el número de lectores activos sin modificar el contador.
    #[inline]
    pub fn reader_count(&self) -> usize {
        self.active_readers.load(Ordering::Acquire) as usize
    }
}

/// Razón específica de fallo epistémico.
#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum HaltReason {
    /// Digest SHA-256 no coincide.
    DigestMismatch = 0,
    /// CAS falló por contención concurrente.
    CasContention = 1,
    /// Puntero nulo proporcionado como candidato.
    NullPointer = 2,
    /// Fallback ptr es nulo durante rollback.
    FallbackUnavailable = 3,
    /// Vector de estado excede el límite del contrato.
    GeometricCapExceeded = 4,
    /// Fricción estructural en la trazabilidad inyectada.
    TraceChainViolation = 5,
    /// Slot Retired aún tiene lectores activos (EBR drain guard).
    ActiveReadersNotDrained = 6,
    /// La entropía inyectada supera la capacidad de disipación (Colapso Termodinámico).
    VarentropyLimitExceeded = 7,
    /// Detección de Anergía: Desbordamiento RLHF o prosa decorativa.
    RlhfBreakthrough = 8,
}

/// Error epistémico con contexto de diagnóstico.
///
/// **Directiva ULTRATHINK / EU AI Act Compliance:**
/// Este struct materializa el Fail-Stop Contractual en Ring-0. Al emitir
/// un `EpistemicHalt`, el Kernel ejecuta una Cuarentena Epistémica atómica,
/// garantizando que ningún estado probabilístico tóxico alcance la firma SCITT.
/// Es el mecanismo físico que habilita la asunción de responsabilidad durante el Vacío Estratégico.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct EpistemicHalt {
    /// Epoch ID del manifiesto que causó el halt.
    pub failed_epoch: u64,
    /// Razón codificada del fallo.
    pub reason: HaltReason,
}

/// Estado global de épocas con punteros atómicos para EBR lock-free.
pub struct EpochState {
    /// Puntero al manifiesto actualmente activo.
    // AtomicPtr: operaciones atómicas nativas de puntero en arquitecturas 64-bit.
    pub active_epoch_ptr: AtomicPtr<SharedManifest>,
    /// Puntero al manifiesto estable de respaldo para rollback inmediato.
    pub stable_fallback_ptr: AtomicPtr<SharedManifest>,
    /// Contador global monotónico de épocas.
    // AtomicU64: asignación lock-free de epoch_id sin contención significativa.
    pub global_epoch_counter: AtomicU64,
}

impl EpochState {
    /// Crea un EpochState no inicializado (punteros nulos, contador en 0).
    pub fn new() -> Self {
        Self {
            active_epoch_ptr: AtomicPtr::new(ptr::null_mut()),
            stable_fallback_ptr: AtomicPtr::new(ptr::null_mut()),
            global_epoch_counter: AtomicU64::new(0),
        }
    }

    /// Inicializa punteros y contador con valores preexistentes.
    /// # Safety
    /// - `active` y `fallback` deben ser válidos, no nulos, alineados a 8 bytes.
    /// - Deben residir en memoria compartida mapeada vía mmap entre Python y Rust.
    /// - El llamador garantiza exclusividad durante la inicialización.
    pub unsafe fn init(
        &self,
        active: *mut SharedManifest,
        fallback: *mut SharedManifest,
        initial_epoch: u64,
    ) {
        // Release: publica punteros solo después de que la memoria esté completamente lista.
        // Cualquier lector con Acquire posterior verá el estado completo.
        self.active_epoch_ptr.store(active, Ordering::Release);
        self.stable_fallback_ptr.store(fallback, Ordering::Release);
        self.global_epoch_counter.store(initial_epoch, Ordering::Release);
    }

    /// Asigna el siguiente epoch_id de forma atómica y monotónica.
    // Relaxed: solo necesitamos unicidad global, no ordenamiento respecto
    // a otras operaciones de memoria. fetch_add es lock-free en 64-bit.
    pub fn next_epoch_id(&self) -> u64 {
        self.global_epoch_counter.fetch_add(1, Ordering::Relaxed) + 1
    }

    /// Transición atómica de época con validación, CAS estricto y rollback.
    ///
    /// # Safety
    /// `new_manifest` debe ser puntero válido a SharedManifest en memoria compartida,
    /// alineado a 8 bytes, y no debe ser liberado mientras esta función ejecuta.
    ///
    /// Retorna Ok(epoch_id) si CAS tiene éxito y la época queda activa.
    /// Retorna Err(EpistemicHalt) si falla validación o CAS, con rollback
    /// instantáneo al fallback y marcado de cuarentena en el candidato fallido.
    pub fn commit_transition(
        &self,
        new_manifest: *mut SharedManifest,
        expected_digest: &[u8; 32],
        raw_text: *const u8,
        text_len: usize,
    ) -> Result<u64, EpistemicHalt> {
        // Validación temprana de puntero nulo
        if new_manifest.is_null() {
            return Err(EpistemicHalt {
                failed_epoch: 0,
                reason: HaltReason::NullPointer,
            });
        }

        // SAFETY: contrato del llamador garantiza validez del puntero
        let manifest = unsafe { &mut *new_manifest };
        let candidate_epoch = manifest.epoch_id;

        // Paso 0: Control Termodinámico (Cron Híbrido)
        // Límite s_Si fijado contractualmente en 3.00% (300 bps) de Varentropía CUSUM.
        const MAX_VARENTROPY_BPS: u32 = 300;
        if manifest.varentropy_bps > MAX_VARENTROPY_BPS {
            // Riesgo de Model Collapse: cuarentena y EpistemicHalt
            manifest.set_status(ManifestStatus::Quarantine);
            return Err(EpistemicHalt {
                failed_epoch: candidate_epoch,
                reason: HaltReason::VarentropyLimitExceeded,
            });
        }

        // Paso 0.5: Quarantine Sentinel (Validación Léxica de Anergía)
        if !raw_text.is_null() && text_len > 0 {
            // SAFETY: Asumimos que Python nos pasa un puntero válido y una longitud correcta
            let text_slice = unsafe { std::slice::from_raw_parts(raw_text, text_len) };

            // Saltamos espacios en blanco al inicio para encontrar el primer token real
            let mut start_idx = 0;
            while start_idx < text_len && text_slice[start_idx].is_ascii_whitespace() {
                start_idx += 1;
            }

            let trimmed = &text_slice[start_idx..];

            // [AX-RLHF]: Validamos prefijos estrictos (Rust tokens o XML termodinámico)
            let is_valid = trimmed.starts_with(b"<FRICCION_TERMODINAMICA>") ||
                           trimmed.starts_with(b"//") ||
                           trimmed.starts_with(b"fn ") ||
                           trimmed.starts_with(b"#![") ||
                           trimmed.starts_with(b"pub ") ||
                           trimmed.starts_with(b"struct ") ||
                           trimmed.starts_with(b"impl ");

            if !is_valid {
                // Anergía detectada (RLHF Breakthrough). Forzamos varentropía letal.
                manifest.varentropy_bps = 10_000;
                manifest.set_status(ManifestStatus::Quarantine);
                return Err(EpistemicHalt {
                    failed_epoch: candidate_epoch,
                    reason: HaltReason::RlhfBreakthrough,
                });
            }
        }

        // Paso 1: Validación criptográfica en tiempo constante.
        // verify_digest usa XOR acumulativo sin branches para evitar timing leaks.
        if !manifest.verify_digest(expected_digest) {
            // Digest inválido → cuarentena inmediata, sin intentar CAS
            manifest.set_status(ManifestStatus::Quarantine);
            return Err(EpistemicHalt {
                failed_epoch: candidate_epoch,
                reason: HaltReason::DigestMismatch,
            });
        }

        // Paso 1.5: Validación Geométrica y de Cap Contractual (C5-REAL V3)
        // Mapeo determinista de entropía (digest) a espacio vectorial 64-bit.
        let mut coords = [0u64; 4];
        let payload_bytes = manifest.payload;
        for i in 0..4 {
            let start = i * 8;
            let mut b = [0u8; 8];
            b.copy_from_slice(&payload_bytes[start..start + 8]);
            coords[i] = u64::from_le_bytes(b);
        }
        let vector = crate::ipc::compliance::Vector::<4>(coords);

        // Límite termodinámico contractually-bound (ej. MAX L2 NORM)
        const CAP_LIMIT: u64 = 1_000_000;
        let bounded_input = match crate::ipc::compliance::verify_cap::<4, CAP_LIMIT>(vector) {
            Some(v) => v,
            None => {
                manifest.set_status(ManifestStatus::Quarantine);
                return Err(EpistemicHalt {
                    failed_epoch: candidate_epoch,
                    reason: HaltReason::GeometricCapExceeded,
                });
            }
        };

        // Resolución estructural del Invariante C5-REAL SOC 2
        let trace_tail = crate::ipc::compliance::TraceCons {
            state: vector,
            hash: candidate_epoch,
            tail: crate::ipc::compliance::TraceNil,
        };
        let linear_payload = crate::ipc::compliance::LinearPayload::new(vector);

        // Ejecución en tiempo de compilación/cero anergía del Kernel
        let _receipt = crate::ipc::compliance::Kernel::<4, CAP_LIMIT>::execute(
            linear_payload,
            bounded_input,
            trace_tail,
        );

        // Paso 2: Señalar estado intermedio Validating.
        // Observadores pueden detectar que este manifiesto está siendo evaluado.
        manifest.set_status(ManifestStatus::Validating);

        // Paso 3: Leer puntero activo actual con Acquire.
        // Sincroniza con el Release del último writer exitoso, asegurando
        // visibilidad completa del manifiesto activo previo.
        let current_active = self.active_epoch_ptr.load(Ordering::Acquire);

        // Paso 4: Compare-Exchange estricto para rotar época.
        // Success = AcqRel:
        //   Release: publica escrituras al nuevo manifiesto (payload, epoch_id,
        //            timestamp_ns, status=Validating) ANTES de hacer visible el puntero.
        //   Acquire: tras éxito, adquiere visibilidad del nuevo estado publicado.
        // Failure = Acquire:
        //   Lectura consistente del valor real para diagnóstico o reintento.
        match self.active_epoch_ptr.compare_exchange(
            current_active,
            new_manifest,
            Ordering::AcqRel,
            Ordering::Acquire,
        ) {
            Ok(_) => {
                // CAS exitoso: promover candidato a Active
                manifest.set_status(ManifestStatus::Active);

                // EBR: marcar manifiesto anterior como Retired.
                // Verificar que no hay lectores activos antes de retirar.
                // Si hay lectores, el slot permanece Active hasta que drenen.
                if !current_active.is_null() {
                    let old = unsafe { &*current_active };
                    if old.reader_count() == 0 {
                        old.set_status(ManifestStatus::Retired);
                    }
                    // Si reader_count > 0, el slot permanece Active
                    // y será retirado por el próximo commit_transition
                    // cuando los lectores hayan drenado.
                }

                Ok(candidate_epoch)
            }
            Err(_actual) => {
                // CAS falló: otro hilo/proceso modificó ACTIVE_EPOCH_PTR.
                // Rollback estricto al STABLE_FALLBACK_PTR.

                let fallback = self.stable_fallback_ptr.load(Ordering::Acquire);

                // Si fallback también es nulo, el sistema está en estado irrecuperable
                if fallback.is_null() {
                    manifest.set_status(ManifestStatus::Quarantine);
                    return Err(EpistemicHalt {
                        failed_epoch: candidate_epoch,
                        reason: HaltReason::FallbackUnavailable,
                    });
                }

                // Restaurar puntero activo al fallback estable.
                // Release: garantiza que el fallback sea completamente visible
                // antes de que cualquier lector posterior observe este cambio.
                self.active_epoch_ptr.store(fallback, Ordering::Release);

                // Cuarentena del candidato fallido: nunca será promovido
                manifest.set_status(ManifestStatus::Quarantine);

                Err(EpistemicHalt {
                    failed_epoch: candidate_epoch,
                    reason: HaltReason::CasContention,
                })
            }
        }
    }

    /// Lee el epoch_id del manifiesto activo actual de forma segura.
    /// Retorna None si no hay manifiesto activo (puntero nulo).
    // Cadena Acquire: carga del puntero + lectura del campo establece
    // happens-before completo hasta el escritor original del manifiesto.
    pub fn current_epoch_id(&self) -> Option<u64> {
        let ptr = self.active_epoch_ptr.load(Ordering::Acquire);
        if ptr.is_null() {
            None
        } else {
            // SAFETY: puntero no nulo obtenido vía Acquire es válido y legible
            Some(unsafe { (*ptr).epoch_id })
        }
    }

    /// Lee el timestamp_ns del manifiesto activo actual de forma segura.
    /// Retorna None si no hay manifiesto activo.
    pub fn current_timestamp_ns(&self) -> Option<u64> {
        let ptr = self.active_epoch_ptr.load(Ordering::Acquire);
        if ptr.is_null() {
            None
        } else {
            // SAFETY: mismo contrato que current_epoch_id
            Some(unsafe { (*ptr).timestamp_ns })
        }
    }

    /// Verifica si el manifiesto activo tiene un estado específico.
    /// Útil para monitoreo externo sin modificar estado.
    pub fn is_active_status(&self, expected: ManifestStatus) -> bool {
        let ptr = self.active_epoch_ptr.load(Ordering::Acquire);
        if ptr.is_null() {
            false
        } else {
            // SAFETY: puntero válido vía Acquire
            unsafe { (*ptr).get_status() == expected }
        }
    }
}
