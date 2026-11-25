//! # BABYLON-60 — Ring-0 Causal Bridge
//!
//! Implementa el Puente de Anillo-0 en tres capas:
//!
//! 1. **`CausalEnvelope`** — serialización canónica libre de padding (Miri-safe, 107 B,
//!    big-endian) y digest BLAKE3 con separación de dominio `"BABYLON-60::RING0::CAUSAL_ENVELOPE::V1"`.
//! 2. **`HardwareSecurityGate`** — trait con tres implementaciones de silicio:
//!    - [`apple_se::AppleSecureEnclaveGate`] (macOS, Security.framework C-FFI)
//!    - [`linux_tpm2::LinuxTpm2Gate`] (Linux, `/dev/tpmrm0`, TPM 2.0)
//!    - [`aws_nitro::AwsNitroEnclaveGate`] (Linux, `/dev/nsm` ioctl, CBOR estático)
//! 3. **[`commit_ring0_transition`]** — linealización atómica en SQLite L0 con
//!    `BEGIN IMMEDIATE` + `compute_next_merkle_root`.
//!
//! ## Invariantes garantizadas
//! - `#![forbid(unsafe_op_in_unsafe_fn)]` heredado del crate.
//! - Ningún backend invoca `SystemTime`; la frescura se deriva de `logical_tick` y
//!   `prev_merkle_root`.
//! - El presupuesto de gramática ($\leq 150$ tokens) se verifica antes de adquirir el
//!   cerrojo de escritura SQLite.
//! - La raíz de Merkle se computa con BLAKE3 keyed-derive
//!   `"BABYLON-60::L0::MERKLE_NODE::V1"` cubriendo el envelope canónico, la firma
//!   hardware, el identificador de clave y la medición PCR/enclave.

use blake3::Hasher;

pub mod wire;

// ── Constantes públicas ──────────────────────────────────────────────────────

/// Código de parada de emergencia (Fail-Stop 0xDEAD_6060).
pub const FAIL_STOP_CODE: u64 = 0xDEAD_6060;

/// Máximo número de tokens de gramática permitidos (Cortafuegos 17).
pub const MAX_GRAMMAR_TOKENS: u16 = 150;

/// Longitud del buffer de serialización canónica de [`CausalEnvelope`] en bytes.
///
/// Descomposición:
/// - `logical_tick` (u64, 8 B)
/// - `prev_merkle_root` ([u8; 32], 32 B)
/// - `source_fact_hash` ([u8; 32], 32 B)
/// - `effect_payload_hash` ([u8; 32], 32 B)
/// - `token_count` (u16, 2 B)
/// - `attestation_tier` (u8, 1 B)
///
/// Total: 107 B (sin bytes de relleno).
pub const CANONICAL_ENVELOPE_LEN: usize = 107;

// ── Tipos públicos ───────────────────────────────────────────────────────────

/// Nivel de atestación requerido para el despacho de un efecto.
#[repr(u8)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum AttestationTier {
    /// El silicio de plataforma puede atestar de forma autónoma (sin presencia biométrica).
    PlatformAutonomous = 1,
    /// Se exige presencia biométrica del operador humano (Touch ID / PIN).
    HumanBiometricPresence = 2,
}

/// Envelope causal mínimo de 64 B (alineado a línea de caché L1).
///
/// **Miri-safe:** Nunca se pasa directamente al hasher; se serializa primero con
/// [`CausalEnvelope::to_canonical_bytes`], que proyecta campo a campo en orden
/// big-endian sobre un buffer de stack de tamaño fijo, evitando la lectura de
/// cualquier byte de relleno producido por `#[repr(C, align(64))]`.
#[repr(C, align(64))]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct CausalEnvelope {
    /// Reloj lógico monotónico estricto (Lamport).
    pub logical_tick: u64,
    /// Raíz de Merkle del estado anterior de L0.
    pub prev_merkle_root: [u8; 32],
    /// Hash canónico del hecho fuente verificado.
    pub source_fact_hash: [u8; 32],
    /// Hash del payload del efecto irreversible.
    pub effect_payload_hash: [u8; 32],
    /// Número de tokens de gramática consumidos (≤ 150).
    pub token_count: u16,
    /// Nivel de atestación de hardware requerido.
    pub attestation_tier: AttestationTier,
}

impl CausalEnvelope {
    /// Serialización canónica determinista sin exponer bytes de relleno (Miri-clean).
    ///
    /// El buffer de 107 bytes se construye campo a campo en big-endian sobre el stack.
    /// No se toca memoria no inicializada en ningún momento.
    #[inline]
    pub fn to_canonical_bytes(&self) -> [u8; CANONICAL_ENVELOPE_LEN] {
        let mut buf = [0u8; CANONICAL_ENVELOPE_LEN];
        buf[0..8].copy_from_slice(&self.logical_tick.to_be_bytes());
        buf[8..40].copy_from_slice(&self.prev_merkle_root);
        buf[40..72].copy_from_slice(&self.source_fact_hash);
        buf[72..104].copy_from_slice(&self.effect_payload_hash);
        buf[104..106].copy_from_slice(&self.token_count.to_be_bytes());
        buf[106] = self.attestation_tier as u8;
        buf
    }

    /// Digest criptográfico canónico con separación de dominio de Anillo-0.
    ///
    /// Usa `Hasher::new_derive_key` para aislar el espacio de claves de Ring-0
    /// de cualquier otro uso de BLAKE3 en el workspace.
    #[inline]
    pub fn canonical_digest(&self) -> [u8; 32] {
        let mut hasher = Hasher::new_derive_key("BABYLON-60::RING0::CAUSAL_ENVELOPE::V1");
        hasher.update(&self.to_canonical_bytes());
        *hasher.finalize().as_bytes()
    }
}

/// Recibo inmutable emitido por el silicio tras una atestación exitosa.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct HardwareReceipt {
    /// Firma hardware de 64 bytes (Ed25519 / ECDSA P-256 / COSE_Sign1).
    pub signature: [u8; 64],
    /// Identificador de la clave pública de atestación.
    pub public_key_id: [u8; 32],
    /// Medición PCR/Enclave en el momento de la atestación.
    pub pcr_or_enclave_measurement: [u8; 32],
}

/// Causas posibles de un fallo en la compuerta de Ring-0.
#[allow(missing_docs)] // Los campos de variantes de error son autodescriptivos.
#[derive(Debug, PartialEq, Eq)]
pub enum GateTrap {
    /// Persistencia ilegible o estado inválido; nunca se interpreta como génesis.
    PersistenceFailure { backend: &'static str, code: u64 },
    /// El número de tokens supera el presupuesto de gramática (Cortafuegos 17).
    GrammarBudgetExceeded { observed: u16, max: u16, code: u64 },
    /// El hecho fuente no existe o su tick no es estrictamente anterior al del efecto.
    UnanchoredCausalLineage { missing_fact: [u8; 32], code: u64 },
    /// El tick propuesto no es contiguo al estado actual de L0.
    NonMonotonicTick {
        proposed: u64,
        current: u64,
        code: u64,
    },
    /// El backend de silicio rechazó o no respondió a la solicitud de atestación.
    SiliconAttestationFailure {
        backend: &'static str,
        errno: i32,
        code: u64,
    },
}

/// Interfaz de silicio para atestar transiciones causales de Ring-0.
///
/// Cada implementación (Apple SE / Linux TPM 2.0 / AWS Nitro) firma el digest
/// canónico del envelope y devuelve un [`HardwareReceipt`] sellado.
#[allow(missing_docs)]
pub trait HardwareSecurityGate {
    fn attest_transition(&mut self, envelope: &CausalEnvelope)
        -> Result<HardwareReceipt, GateTrap>;
}

// ── Backend A: Apple Silicon Secure Enclave ──────────────────────────────────

/// Implementación del gate para Apple Silicon (macOS Security.framework).
#[cfg(target_os = "macos")]
pub mod apple_se {
    use super::*;

    /// Estructura de respuesta cruda del C-FFI de Security.framework.
    #[repr(C)]
    pub struct RawSeResponse {
        /// Código de estado: 0 = éxito.
        pub status: i32,
        /// Firma hardware de 64 bytes.
        pub signature: [u8; 64],
        /// Identificador de la clave en el Secure Enclave.
        pub key_id: [u8; 32],
        /// Medición del SEP en el momento de la firma.
        pub sep_measurement: [u8; 32],
    }

    // Puente C-ABI hacia el envoltorio nativo de Security.framework / LocalAuthentication.
    // La función real se enlaza desde `src/ffi.rs` o un archivo `.c` de la build.
    unsafe extern "C" {
        fn b60_apple_se_sign(
            digest_ptr: *const u8,
            digest_len: usize,
            require_biometrics: u8,
            out_resp: *mut RawSeResponse,
        ) -> i32;
    }

    /// Compuerta hardware para Apple Silicon Secure Enclave.
    pub struct AppleSecureEnclaveGate {
        enclave_key_tag: [u8; 32],
    }

    impl AppleSecureEnclaveGate {
        /// Crea una nueva instancia con la etiqueta de clave del Secure Enclave.
        pub const fn new(enclave_key_tag: [u8; 32]) -> Self {
            Self { enclave_key_tag }
        }
    }

    impl HardwareSecurityGate for AppleSecureEnclaveGate {
        fn attest_transition(
            &mut self,
            envelope: &CausalEnvelope,
        ) -> Result<HardwareReceipt, GateTrap> {
            let digest = envelope.canonical_digest();
            let require_bio = match envelope.attestation_tier {
                AttestationTier::PlatformAutonomous => 0u8,
                AttestationTier::HumanBiometricPresence => 1u8,
            };

            let mut raw = RawSeResponse {
                status: -1,
                signature: [0u8; 64],
                key_id: self.enclave_key_tag,
                sep_measurement: [0u8; 32],
            };

            // SAFETY: `digest` tiene longitud fija 32 B. `raw` vive en el stack del
            // llamador y está correctamente alineado. La función C no retiene el puntero.
            let rc = unsafe {
                b60_apple_se_sign(
                    digest.as_ptr(),
                    digest.len(),
                    require_bio,
                    &mut raw as *mut _,
                )
            };

            if rc != 0 || raw.status != 0 {
                return Err(GateTrap::SiliconAttestationFailure {
                    backend: "AppleSecureEnclave",
                    errno: if rc != 0 { rc } else { raw.status },
                    code: FAIL_STOP_CODE,
                });
            }

            Ok(HardwareReceipt {
                signature: raw.signature,
                public_key_id: raw.key_id,
                pcr_or_enclave_measurement: raw.sep_measurement,
            })
        }
    }
}

// ── Backend B: Linux TPM 2.0 (/dev/tpmrm0) ──────────────────────────────────

/// Implementación del gate para Linux con TPM 2.0 via KRM.
#[cfg(target_os = "linux")]
pub mod linux_tpm2 {
    use super::*;
    use std::fs::{File, OpenOptions};
    use std::io::{Read, Write};

    const TPM_RC_SUCCESS: u32 = 0x0000_0000;

    /// Compuerta hardware para Linux TPM 2.0 via Kernel Resource Manager.
    pub struct LinuxTpm2Gate {
        device: File,
        ak_handle: u32,
        ak_pubkey_id: [u8; 32],
        expected_pcr_composite: [u8; 32],
    }

    impl LinuxTpm2Gate {
        /// Abre `/dev/tpmrm0` y registra el handle de Attestation Key.
        pub fn open(
            ak_handle: u32,
            ak_pubkey_id: [u8; 32],
            expected_pcr_composite: [u8; 32],
        ) -> Result<Self, GateTrap> {
            let device = OpenOptions::new()
                .read(true)
                .write(true)
                .open("/dev/tpmrm0")
                .map_err(|e| GateTrap::SiliconAttestationFailure {
                    backend: "LinuxTPM2_Open",
                    errno: e.raw_os_error().unwrap_or(-1),
                    code: FAIL_STOP_CODE,
                })?;

            Ok(Self {
                device,
                ak_handle,
                ak_pubkey_id,
                expected_pcr_composite,
            })
        }

        /// Construye el paquete binario `TPM2_Quote` con `qualifyingData` = digest causal
        /// y selección de PCR 0, 7 y 14 en el banco SHA-256 (alg ID = 0x000B).
        ///
        /// Delegado en [`super::wire::build_quote_command`] (neutral de plataforma).
        fn build_quote_command(&self, qualifying_digest: &[u8; 32]) -> [u8; 73] {
            super::wire::build_quote_command(self.ak_handle, qualifying_digest)
        }
    }

    const TPM_ST_SESSIONS_RESP: u16 = 0x8002;
    const TPM_GENERATED_VALUE: u32 = 0xFF54_4347;
    const TPM_ST_ATTEST_QUOTE: u16 = 0x8018;
    const TPM_ALG_ECDSA: u16 = 0x0018;
    const TPM_ALG_SHA256: u16 = 0x000B;

    /// Cursor de lectura big-endian con límites; cualquier desbordamiento es `None`.
    struct Rd<'a>(&'a [u8]);

    impl<'a> Rd<'a> {
        fn take(&mut self, n: usize) -> Option<&'a [u8]> {
            if self.0.len() < n {
                return None;
            }
            let (h, t) = self.0.split_at(n);
            self.0 = t;
            Some(h)
        }
        fn u16(&mut self) -> Option<u16> {
            self.take(2).map(|b| u16::from_be_bytes([b[0], b[1]]))
        }
        fn u32(&mut self) -> Option<u32> {
            self.take(4)
                .map(|b| u32::from_be_bytes([b[0], b[1], b[2], b[3]]))
        }
        fn tpm2b(&mut self) -> Option<&'a [u8]> {
            let n = self.u16()? as usize;
            self.take(n)
        }
    }

    /// Parsea una respuesta `TPM2_Quote` (TPM_ST_SESSIONS) y falla cerrado ante cualquier
    /// desviación estructural. Devuelve `(r || s, pcrDigest atestado)`.
    ///
    /// Comprueba: tamaño declarado == longitud leída; `TPM_RC_SUCCESS`; `TPM_GENERATED`;
    /// tipo `TPM_ST_ATTEST_QUOTE`; `extraData` == `expected_digest` (enlace causal);
    /// `pcrDigest` == `expected_pcr`; firma ECDSA-SHA256 con `r` y `s` de 32 B no nulos.
    ///
    /// **Límite:** no verifica criptográficamente la firma; el gate no conoce la clave pública
    /// del AK (solo un identificador). La verificación ECDSA corresponde al verificador externo.
    pub(crate) fn parse_quote_response(
        resp: &[u8],
        expected_digest: &[u8; 32],
        expected_pcr: &[u8; 32],
    ) -> Result<([u8; 64], [u8; 32]), &'static str> {
        let mut r = Rd(resp);
        let tag = r.u16().ok_or("LinuxTPM2_ShortRead")?;
        let size = r.u32().ok_or("LinuxTPM2_ShortRead")? as usize;
        let rc = r.u32().ok_or("LinuxTPM2_ShortRead")?;
        if size != resp.len() {
            return Err("LinuxTPM2_SizeMismatch");
        }
        if rc != TPM_RC_SUCCESS {
            return Err("LinuxTPM2_ResponseCode");
        }
        if tag != TPM_ST_SESSIONS_RESP {
            return Err("LinuxTPM2_BadTag");
        }
        let param_size = r.u32().ok_or("LinuxTPM2_Malformed")? as usize;
        let params = r.take(param_size).ok_or("LinuxTPM2_Malformed")?;
        let mut p = Rd(params);

        let attest_raw = p.tpm2b().ok_or("LinuxTPM2_Malformed")?;
        let mut a = Rd(attest_raw);
        if a.u32().ok_or("LinuxTPM2_Malformed")? != TPM_GENERATED_VALUE {
            return Err("LinuxTPM2_NotTpmGenerated");
        }
        if a.u16().ok_or("LinuxTPM2_Malformed")? != TPM_ST_ATTEST_QUOTE {
            return Err("LinuxTPM2_NotQuote");
        }
        a.tpm2b().ok_or("LinuxTPM2_Malformed")?; // qualifiedSigner
        if a.tpm2b().ok_or("LinuxTPM2_Malformed")? != expected_digest {
            return Err("LinuxTPM2_ExtraDataMismatch");
        }
        a.take(17 + 8).ok_or("LinuxTPM2_Malformed")?; // clockInfo + firmwareVersion
        let banks = a.u32().ok_or("LinuxTPM2_Malformed")?;
        if banks == 0 || banks > 16 {
            return Err("LinuxTPM2_Malformed");
        }
        for _ in 0..banks {
            a.u16().ok_or("LinuxTPM2_Malformed")?;
            let sz = a.take(1).ok_or("LinuxTPM2_Malformed")?[0] as usize;
            a.take(sz).ok_or("LinuxTPM2_Malformed")?;
        }
        let pcr_digest = a.tpm2b().ok_or("LinuxTPM2_Malformed")?;
        if pcr_digest != expected_pcr {
            return Err("LinuxTPM2_PcrMismatch");
        }
        if !a.0.is_empty() {
            return Err("LinuxTPM2_Malformed");
        }

        if p.u16().ok_or("LinuxTPM2_Malformed")? != TPM_ALG_ECDSA {
            return Err("LinuxTPM2_UnsupportedSigAlg");
        }
        if p.u16().ok_or("LinuxTPM2_Malformed")? != TPM_ALG_SHA256 {
            return Err("LinuxTPM2_UnsupportedSigHash");
        }
        let sig_r = p.tpm2b().ok_or("LinuxTPM2_Malformed")?;
        let sig_s = p.tpm2b().ok_or("LinuxTPM2_Malformed")?;
        if sig_r.len() != 32 || sig_s.len() != 32 {
            return Err("LinuxTPM2_BadSigLen");
        }
        if sig_r.iter().all(|&b| b == 0) || sig_s.iter().all(|&b| b == 0) {
            return Err("LinuxTPM2_ZeroSignature");
        }
        let mut signature = [0u8; 64];
        signature[..32].copy_from_slice(sig_r);
        signature[32..].copy_from_slice(sig_s);
        let mut pcr = [0u8; 32];
        pcr.copy_from_slice(pcr_digest);
        Ok((signature, pcr))
    }

    impl HardwareSecurityGate for LinuxTpm2Gate {
        fn attest_transition(
            &mut self,
            envelope: &CausalEnvelope,
        ) -> Result<HardwareReceipt, GateTrap> {
            let digest = envelope.canonical_digest();
            let cmd = self.build_quote_command(&digest);

            self.device
                .write_all(&cmd)
                .map_err(|e| GateTrap::SiliconAttestationFailure {
                    backend: "LinuxTPM2_Write",
                    errno: e.raw_os_error().unwrap_or(-2),
                    code: FAIL_STOP_CODE,
                })?;

            let mut resp = [0u8; 512];
            let n =
                self.device
                    .read(&mut resp)
                    .map_err(|e| GateTrap::SiliconAttestationFailure {
                        backend: "LinuxTPM2_Read",
                        errno: e.raw_os_error().unwrap_or(-3),
                        code: FAIL_STOP_CODE,
                    })?;

            if n < 10 {
                return Err(GateTrap::SiliconAttestationFailure {
                    backend: "LinuxTPM2_ShortRead",
                    errno: n as i32,
                    code: FAIL_STOP_CODE,
                });
            }

            let rc = u32::from_be_bytes([resp[6], resp[7], resp[8], resp[9]]);
            if rc != TPM_RC_SUCCESS {
                return Err(GateTrap::SiliconAttestationFailure {
                    backend: "LinuxTPM2_ResponseCode",
                    errno: rc as i32,
                    code: FAIL_STOP_CODE,
                });
            }

            let (signature, attested_pcr) =
                parse_quote_response(&resp[..n], &digest, &self.expected_pcr_composite).map_err(
                    |backend| GateTrap::SiliconAttestationFailure {
                        backend,
                        errno: n as i32,
                        code: FAIL_STOP_CODE,
                    },
                )?;

            Ok(HardwareReceipt {
                signature,
                public_key_id: self.ak_pubkey_id,
                pcr_or_enclave_measurement: attested_pcr,
            })
        }
    }
}

// ── Backend C: AWS Nitro Enclaves (/dev/nsm ioctl) ──────────────────────────

/// Implementación del gate para AWS Nitro Enclaves.
#[cfg(target_os = "linux")]
pub mod aws_nitro {
    use super::*;
    use std::fs::OpenOptions;
    use std::os::fd::AsRawFd;

    // _IOWR(0x0A, 0, struct nsm_message) en el driver /dev/nsm de Linux.
    const NSM_IOCTL_REQUEST: libc::c_ulong = 0xC020_0A00;

    #[repr(C)]
    struct Iovec {
        iov_base: *mut u8,
        iov_len: usize,
    }

    #[repr(C)]
    struct NsmMessage {
        request: Iovec,
        response: Iovec,
    }

    struct FileDesc(std::fs::File);

    /// Compuerta hardware para AWS Nitro Enclaves.
    pub struct AwsNitroEnclaveGate {
        fd: FileDesc,
        enclave_key_id: [u8; 32],
        pcr0_measurement: [u8; 32],
    }

    impl AwsNitroEnclaveGate {
        /// Abre `/dev/nsm` y registra la clave de identificación del enclave.
        pub fn open(
            enclave_key_id: [u8; 32],
            pcr0_measurement: [u8; 32],
        ) -> Result<Self, GateTrap> {
            let file = OpenOptions::new()
                .read(true)
                .write(true)
                .open("/dev/nsm")
                .map_err(|e| GateTrap::SiliconAttestationFailure {
                    backend: "AwsNitroNsm_Open",
                    errno: e.raw_os_error().unwrap_or(-1),
                    code: FAIL_STOP_CODE,
                })?;
            Ok(Self {
                fd: FileDesc(file),
                enclave_key_id,
                pcr0_measurement,
            })
        }

        /// Codifica en CBOR estático (sin heap) una petición `Attestation` con
        /// `user_data` (32 B del digest causal) y `nonce` (8 B del `logical_tick`).
        ///
        /// Delegado en [`super::wire::encode_cbor_attestation_req`] (neutral de plataforma).
        fn encode_cbor_attestation_req(digest: &[u8; 32], tick: u64) -> [u8; 73] {
            super::wire::encode_cbor_attestation_req(digest, tick)
        }
    }

    impl HardwareSecurityGate for AwsNitroEnclaveGate {
        fn attest_transition(
            &mut self,
            envelope: &CausalEnvelope,
        ) -> Result<HardwareReceipt, GateTrap> {
            let digest = envelope.canonical_digest();
            let mut req_buf = Self::encode_cbor_attestation_req(&digest, envelope.logical_tick);
            let mut resp_buf = [0u8; 4096];

            let mut msg = NsmMessage {
                request: Iovec {
                    iov_base: req_buf.as_mut_ptr(),
                    iov_len: req_buf.len(),
                },
                response: Iovec {
                    iov_base: resp_buf.as_mut_ptr(),
                    iov_len: resp_buf.len(),
                },
            };

            // SAFETY: `req_buf` y `resp_buf` viven en el stack del llamador y sus
            // longitudes son exactas. El ioctl no retiene los punteros.
            let rc = unsafe {
                libc::ioctl(
                    self.fd.0.as_raw_fd(),
                    NSM_IOCTL_REQUEST,
                    &mut msg as *mut NsmMessage,
                )
            };

            if rc != 0 || msg.response.iov_len < 96 {
                return Err(GateTrap::SiliconAttestationFailure {
                    backend: "AwsNitroNsm_Ioctl",
                    errno: rc as i32,
                    code: FAIL_STOP_CODE,
                });
            }

            let len = msg.response.iov_len;
            // Fail-closed: una longitud mayor que el búfer provocaría un pánico al trocear.
            if len > resp_buf.len() {
                return Err(GateTrap::SiliconAttestationFailure {
                    backend: "AwsNitroNsm_ResponseOverflow",
                    errno: 0,
                    code: FAIL_STOP_CODE,
                });
            }
            // NO_VERIFICADO (auditoría 2026-11-25): no se parsea el documento COSE_Sign1 de
            // NSM; estos 64 B no son una firma verificada y la medición devuelta es la
            // configurada, no la leída del documento. Ver CLAIMS antes de citar este gate.
            let mut signature = [0u8; 64];
            signature.copy_from_slice(&resp_buf[len - 64..len]);

            Ok(HardwareReceipt {
                signature,
                public_key_id: self.enclave_key_id,
                pcr_or_enclave_measurement: self.pcr0_measurement,
            })
        }
    }
}

// ── Implementación mock para tests (feature = "test_mock_hardware") ──────────

/// Backend de pruebas que firma con BLAKE3 (cero syscalls de silicio).
///
/// Habilitado únicamente bajo `cfg(feature = "test_mock_hardware")`.
#[cfg(feature = "test_mock_hardware")]
pub mod mock_gate {
    use super::*;

    /// Compuerta de prueba determinista — **nunca usar en producción**.
    pub struct MockHardwareGate {
        /// Número de veces que se ha invocado `attest_transition`.
        pub call_count: u32,
    }

    impl MockHardwareGate {
        /// Crea una nueva instancia con contador a cero.
        pub fn new() -> Self {
            Self { call_count: 0 }
        }
    }

    impl HardwareSecurityGate for MockHardwareGate {
        fn attest_transition(
            &mut self,
            envelope: &CausalEnvelope,
        ) -> Result<HardwareReceipt, GateTrap> {
            self.call_count += 1;
            let digest = envelope.canonical_digest();

            let mut sig = [0u8; 64];
            sig[..32].copy_from_slice(&digest);
            // El segundo bloque de 32 bytes invierte el digest (distinguibilidad de test)
            for (i, &b) in digest.iter().enumerate() {
                sig[32 + i] = !b;
            }

            let mut key_id = [0u8; 32];
            key_id[0..4].copy_from_slice(b"MOCK");

            Ok(HardwareReceipt {
                signature: sig,
                public_key_id: key_id,
                pcr_or_enclave_measurement: [0xABu8; 32],
            })
        }
    }
}

// ── Raíz de Merkle L0 y linealización atómica ────────────────────────────────

/// Computa determinísticamente la siguiente raíz de Merkle de L0.
///
/// `R_n = BLAKE3("BABYLON-60::L0::MERKLE_NODE::V1", canonical_bytes || hw_sig || pubkey || pcr)`
#[inline]
pub fn compute_next_merkle_root(envelope: &CausalEnvelope, receipt: &HardwareReceipt) -> [u8; 32] {
    let mut hasher = Hasher::new_derive_key("BABYLON-60::L0::MERKLE_NODE::V1");
    hasher.update(&envelope.to_canonical_bytes());
    hasher.update(&receipt.signature);
    hasher.update(&receipt.public_key_id);
    hasher.update(&receipt.pcr_or_enclave_measurement);
    *hasher.finalize().as_bytes()
}

/// Recibo de una transición de Ring-0 comprometida en SQLite L0.
#[derive(Debug)]
pub struct L0CommittedTransition {
    /// Tick lógico sellado.
    pub logical_tick: u64,
    /// Nueva raíz de Merkle tras la transición.
    pub curr_merkle_root: [u8; 32],
    /// Recibo hardware emitido por el silicio.
    pub receipt: HardwareReceipt,
}

/// Linealiza atómicamente una transición verificada en SQLite L0.
///
/// Protocolo:
/// 1. Comprueba `token_count ≤ MAX_GRAMMAR_TOKENS` (fail-closed antes del lock).
/// 2. Adquiere `BEGIN IMMEDIATE` (single-writer lock de WAL).
/// 3. Lee el estado actual de L0: `(current_tick, current_root)`.
/// 4. Verifica monotonía de tick y enlace Merkle en Rust (doble barrera antes del trigger).
/// 5. Verifica precedencia causal del hecho fuente.
/// 6. Solicita firma al backend de silicio (Apple SE / TPM 2.0 / Nitro).
/// 7. Computa `curr_merkle_root` = [`compute_next_merkle_root`].
/// 8. Ejecuta el `INSERT`; los triggers SQL verifican las invariantes por segunda vez.
/// 9. Hace `COMMIT` y devuelve [`L0CommittedTransition`].
///
/// Requiere feature `cortex-persist`.
#[cfg(feature = "cortex-persist")]
pub fn commit_ring0_transition<G: HardwareSecurityGate>(
    conn: &mut rusqlite::Connection,
    gate: &mut G,
    envelope: &CausalEnvelope,
) -> Result<L0CommittedTransition, GateTrap> {
    use rusqlite::{params, TransactionBehavior};

    // Cortafuegos 17: verificación del presupuesto de gramática antes del lock
    if envelope.token_count > MAX_GRAMMAR_TOKENS {
        return Err(GateTrap::GrammarBudgetExceeded {
            observed: envelope.token_count,
            max: MAX_GRAMMAR_TOKENS,
            code: FAIL_STOP_CODE,
        });
    }

    // Adquiere el cerrojo de escritura inmediato de SQLite WAL (single-writer)
    let tx = conn
        .transaction_with_behavior(TransactionBehavior::Immediate)
        .map_err(|_| GateTrap::SiliconAttestationFailure {
            backend: "SQLite_BeginImmediate",
            errno: -10,
            code: FAIL_STOP_CODE,
        })?;

    let (current_tick, current_root) = read_l0_tip(&tx)?;
    let proposed_tick =
        i64::try_from(envelope.logical_tick).map_err(|_| GateTrap::NonMonotonicTick {
            proposed: envelope.logical_tick,
            current: current_tick,
            code: FAIL_STOP_CODE,
        })?;

    // Barrera Rust — monotonía contigua dentro del dominio INTEGER de SQLite.
    if current_tick >= i64::MAX as u64 || envelope.logical_tick != current_tick + 1 {
        return Err(GateTrap::NonMonotonicTick {
            proposed: envelope.logical_tick,
            current: current_tick,
            code: FAIL_STOP_CODE,
        });
    }

    // Barrera Rust — enlace criptográfico con la raíz anterior
    if envelope.prev_merkle_root != current_root {
        return Err(GateTrap::UnanchoredCausalLineage {
            missing_fact: envelope.prev_merkle_root,
            code: FAIL_STOP_CODE,
        });
    }

    // Barrera Rust — precedencia temporal del hecho fuente
    let fact_valid: bool = tx
        .query_row(
            "SELECT EXISTS(
                SELECT 1 FROM l0_anchored_facts
                WHERE fact_hash = ?1 AND anchored_tick >= 0 AND anchored_tick < ?2
             )",
            params![&envelope.source_fact_hash[..], proposed_tick],
            |row| row.get(0),
        )
        .map_err(|_| GateTrap::PersistenceFailure {
            backend: "SQLite_FactRead",
            code: FAIL_STOP_CODE,
        })?;

    if !fact_valid {
        return Err(GateTrap::UnanchoredCausalLineage {
            missing_fact: envelope.source_fact_hash,
            code: FAIL_STOP_CODE,
        });
    }

    // Atestación en silicio (Apple SE / TPM 2.0 / Nitro / Mock)
    let receipt = gate.attest_transition(envelope)?;
    let curr_merkle_root = compute_next_merkle_root(envelope, &receipt);

    // INSERT: los triggers SQL actúan como barrera defensiva secundaria
    tx.execute(
        "INSERT INTO l0_causal_ledger (
            logical_tick, prev_merkle_root, source_fact_hash, effect_payload_hash,
            curr_merkle_root, token_count, attestation_tier,
            hw_signature, hw_pubkey_id, hw_measurement
         ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)",
        params![
            proposed_tick,
            &envelope.prev_merkle_root[..],
            &envelope.source_fact_hash[..],
            &envelope.effect_payload_hash[..],
            &curr_merkle_root[..],
            envelope.token_count as i64,
            envelope.attestation_tier as i64,
            &receipt.signature[..],
            &receipt.public_key_id[..],
            &receipt.pcr_or_enclave_measurement[..],
        ],
    )
    .map_err(|_| GateTrap::SiliconAttestationFailure {
        backend: "SQLite_L0TriggerAbort",
        errno: -20,
        code: FAIL_STOP_CODE,
    })?;

    tx.commit()
        .map_err(|_| GateTrap::SiliconAttestationFailure {
            backend: "SQLite_Commit",
            errno: -30,
            code: FAIL_STOP_CODE,
        })?;

    Ok(L0CommittedTransition {
        logical_tick: envelope.logical_tick,
        curr_merkle_root,
        receipt,
    })
}

/// Lee un tip validado; únicamente la ausencia real de filas es génesis.
#[cfg(feature = "cortex-persist")]
pub fn read_l0_tip(conn: &rusqlite::Connection) -> Result<(u64, [u8; 32]), GateTrap> {
    use rusqlite::OptionalExtension;
    let row: Option<(i64, Vec<u8>)> = conn.query_row(
        "SELECT logical_tick, curr_merkle_root FROM l0_causal_ledger ORDER BY logical_tick DESC LIMIT 1",
        [], |row| Ok((row.get(0)?, row.get(1)?)),
    ).optional().map_err(|_| GateTrap::PersistenceFailure { backend: "SQLite_TipRead", code: FAIL_STOP_CODE })?;
    match row {
        None => Ok((0, [0; 32])),
        Some((tick, root)) if tick > 0 && root.len() == 32 => {
            let mut bytes = [0; 32];
            bytes.copy_from_slice(&root);
            Ok((tick as u64, bytes))
        }
        _ => Err(GateTrap::PersistenceFailure {
            backend: "SQLite_InvalidTip",
            code: FAIL_STOP_CODE,
        }),
    }
}

/// Inicializa el esquema L0 de SQLite en la conexión proporcionada.
///
/// Idempotente (usa `CREATE TABLE IF NOT EXISTS` y `CREATE TRIGGER IF NOT EXISTS`).
/// Debe llamarse una vez antes de invocar [`commit_ring0_transition`].
#[cfg(feature = "cortex-persist")]
pub fn init_l0_schema(conn: &rusqlite::Connection) -> rusqlite::Result<()> {
    conn.execute_batch(include_str!("../scripts/ring0_l0_schema.sql"))?;
    let legacy_unique_tick: bool = conn.query_row(
        "SELECT EXISTS(SELECT 1 FROM pragma_index_list('l0_anchored_facts') i \
         JOIN pragma_index_info(i.name) c WHERE i.[unique]=1 AND c.name='anchored_tick')",
        [],
        |row| row.get(0),
    )?;
    if legacy_unique_tick {
        if let Err(error) =
            conn.execute_batch(include_str!("../scripts/ring0_l0_fact_tick_migration.sql"))
        {
            let _ = conn.execute_batch("ROLLBACK; PRAGMA legacy_alter_table = OFF;");
            return Err(error);
        }
    }
    Ok(())
}
