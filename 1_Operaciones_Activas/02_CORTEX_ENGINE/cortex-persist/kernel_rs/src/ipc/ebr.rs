// C5-REAL EXERGY CERTIFIED
use std::ptr;
use std::sync::atomic::{AtomicPtr, AtomicU64, AtomicU8, Ordering};

/// Estados posibles del SharedManifest para EBR.
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

/// Manifiesto compartido entre Python y Rust con layout C garantizado.
/// #[repr(C, align(8))] asegura compatibilidad ABI y alineación para atomics en 64-bit.
#[repr(C, align(8))]
pub struct SharedManifest {
    /// Resumen criptográfico SHA-256 (32 bytes).
    pub payload: [u8; 32],
    /// Bandera de estado atómica para transiciones lock-free.
    pub status_flag: AtomicU8,
    /// Identificador secuencial de época para anclaje SCITT.
    pub epoch_id: u64,
    /// Timestamp nanosecondal para anclaje SCITT.
    pub timestamp_ns: u64,
}

impl SharedManifest {
    /// Crea un nuevo manifiesto en estado Idle.
    pub fn new(epoch_id: u64, timestamp_ns: u64) -> Self {
        Self {
            payload: [0u8; 32],
            // Inicialización atómica sin bloqueos
            status_flag: AtomicU8::new(ManifestStatus::Idle as u8),
            epoch_id,
            timestamp_ns,
        }
    }

    /// Lectura atómica del estado con semántica Acquire.
    // Acquire: garantiza que lecturas subsiguientes no se reordenen antes de esta carga,
    // estableciendo un borde happens-before con el Release del escritor.
    pub fn get_status(&self) -> ManifestStatus {
        match self.status_flag.load(Ordering::Acquire) {
            0 => ManifestStatus::Idle,
            1 => ManifestStatus::Ready,
            2 => ManifestStatus::Validating,
            3 => ManifestStatus::Active,
            4 => ManifestStatus::Retired,
            5 => ManifestStatus::Quarantine,
            _ => ManifestStatus::Quarantine, // Defensa: valor corrupto → cuarentena
        }
    }

    /// Escritura atómica del estado con semántica Release.
    // Release: garantiza que escrituras previas a esta tienda sean visibles
    // para cualquier hilo que posteriormente haga Acquire sobre este campo.
    pub fn set_status(&self, status: ManifestStatus) {
        self.status_flag.store(status as u8, Ordering::Release);
    }
}

/// Error epistémico: violación de consistencia detectada durante transición.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct EpistemicHalt {
    /// Epoch ID del manifiesto que causó el halt.
    pub failed_epoch: u64,
    /// Razón codificada del fallo.
    pub reason: HaltReason,
}

/// Razones específicas para EpistemicHalt.
#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum HaltReason {
    /// Digest SHA-256 no coincide con el esperado.
    DigestMismatch = 0,
    /// CAS falló por contención concurrente.
    CasContention = 1,
    /// Puntero nulo proporcionado.
    NullPointer = 2,
}

/// Estado global de épocas con punteros atómicos para EBR lock-free.
pub struct EpochState {
    /// Puntero al manifiesto actualmente activo.
    // AtomicPtr<SharedManifest>: operaciones atómicas de puntero nativas en 64-bit.
    pub active_epoch_ptr: AtomicPtr<SharedManifest>,
    /// Puntero al manifiesto estable de respaldo para rollback inmediato.
    pub stable_fallback_ptr: AtomicPtr<SharedManifest>,
    /// Contador global de épocas para asignación monotónica.
    // AtomicU64: contador lock-free para generación de epoch_id.
    pub global_epoch_counter: AtomicU64,
}

impl EpochState {
    /// Crea un nuevo EpochState con punteros nulos y contador en cero.
    pub fn new() -> Self {
        Self {
            active_epoch_ptr: AtomicPtr::new(ptr::null_mut()),
            stable_fallback_ptr: AtomicPtr::new(ptr::null_mut()),
            global_epoch_counter: AtomicU64::new(0),
        }
    }

    /// Inicializa los punteros con manifiestos preexistentes.
    /// # Safety
    /// Los punteros deben ser válidos, alineados a 8 bytes, y residir en
    /// memoria compartida mapeada correctamente entre Python y Rust via mmap.
    pub unsafe fn init(
        &self,
        active: *mut SharedManifest,
        fallback: *mut SharedManifest,
        initial_epoch: u64,
    ) {
        // Release: publica los punteros después de que la memoria esté lista
        self.active_epoch_ptr.store(active, Ordering::Release);
        self.stable_fallback_ptr.store(fallback, Ordering::Release);
        self.global_epoch_counter.store(initial_epoch, Ordering::Release);
    }

    /// Asigna el siguiente epoch_id de forma atómica y monotónica.
    // Relaxed es suficiente aquí: solo necesitamos unicidad, no ordenamiento
    // respecto a otras operaciones de memoria.
    pub fn next_epoch_id(&self) -> u64 {
        self.global_epoch_counter.fetch_add(1, Ordering::Relaxed) + 1
    }

    /// Ejecuta una transición atómica de época con validación, CAS y rollback.
    ///
    /// Retorna Ok(new_epoch_id) si el CAS tiene éxito.
    /// Retorna Err(EpistemicHalt) con razón específica si falla,
    /// ejecutando rollback instantáneo al fallback y marcando cuarentena.
    pub fn commit_transition(
        &self,
        new_manifest: *mut SharedManifest,
        expected_digest: &[u8; 32],
    ) -> Result<u64, EpistemicHalt> {
        // Validación de puntero nulo antes de cualquier acceso
        if new_manifest.is_null() {
            return Err(EpistemicHalt {
                failed_epoch: 0,
                reason: HaltReason::NullPointer,
            });
        }

        // SAFETY: El llamador garantiza que new_manifest apunta a memoria válida
        // dentro del segmento compartido y está correctamente alineado.
        let manifest = unsafe { &*new_manifest };
        let candidate_epoch = manifest.epoch_id;

        // Paso 1: Validación criptográfica del digest SHA-256.
        // Comparación constante en tiempo para evitar timing attacks.
        let mut mismatch = false;
        for i in 0..32 {
            if manifest.payload[i] != expected_digest[i] {
                mismatch = true;
            }
        }
        if mismatch {
            // Digest inválido → cuarentena inmediata, sin intentar CAS
            manifest.set_status(ManifestStatus::Quarantine);
            return Err(EpistemicHalt {
                failed_epoch: candidate_epoch,
                reason: HaltReason::DigestMismatch,
            });
        }

        // Paso 2: Transicionar a estado Validating antes del CAS.
        // Esto señala a observadores que este manifiesto está siendo evaluado.
        manifest.set_status(ManifestStatus::Validating);

        // Paso 3: Leer el puntero activo actual.
        // Acquire: sincroniza con el Release del último writer exitoso,
        // asegurando que vemos el estado completo del manifiesto activo.
        let current_active = self.active_epoch_ptr.load(Ordering::Acquire);

        // Paso 4: Compare-Exchange estricto para rotar la época.
        // Success ordering = AcqRel:
        //   - Release: publica todas las escrituras al nuevo manifiesto
        //     (payload, epoch_id, timestamp_ns, status=Validating)
        //     ANTES de que el puntero sea visible globalmente.
        //   - Acquire: tras éxito, adquiere visibilidad completa del nuevo estado.
        // Failure ordering = Acquire:
        //   - En fallo, necesitamos leer consistentemente el valor real
        //     para diagnóstico o reintento futuro.
        match self.active_epoch_ptr.compare_exchange(
            current_active,
            new_manifest,
            Ordering::AcqRel,
            Ordering::Acquire,
        ) {
            Ok(_) => {
                // CAS exitoso: promover a Active
                manifest.set_status(ManifestStatus::Active);

                // Marcar el manifiesto anterior como Retired (EBR: no liberar aún)
                if !current_active.is_null() {
                    let old = unsafe { &*current_active };
                    old.set_status(ManifestStatus::Retired);
                }

                Ok(candidate_epoch)
            }
            Err(_actual) => {
                // CAS falló: contención concurrente detectada.
                // Rollback estricto al STABLE_FALLBACK_PTR.

                // Cargar fallback con Acquire para asegurar consistencia
                let fallback = self.stable_fallback_ptr.load(Ordering::Acquire);

                // Restaurar puntero activo al fallback estable.
                // Release: garantiza que el fallback sea visible antes de
                // que cualquier lector posterior observe este cambio.
                self.active_epoch_ptr.store(fallback, Ordering::Release);

                // Cuarentena del manifiesto candidato fallido
                manifest.set_status(ManifestStatus::Quarantine);

                Err(EpistemicHalt {
                    failed_epoch: candidate_epoch,
                    reason: HaltReason::CasContention,
                })
            }
        }
    }

    /// Lee el epoch_id del manifiesto activo actual de forma segura.
    /// Retorna None si no hay manifiesto activo.
    // Acquire en la carga del puntero + Acquire en la lectura del campo
    // establece cadena happens-before completa hasta el escritor original.
    pub fn current_epoch_id(&self) -> Option<u64> {
        let ptr = self.active_epoch_ptr.load(Ordering::Acquire);
        if ptr.is_null() {
            None
        } else {
            // SAFETY: puntero no nulo obtenido vía Acquire es válido
            Some(unsafe { (*ptr).epoch_id })
        }
    }
}
