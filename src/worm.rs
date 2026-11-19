use crate::receipt::Signer;
use core::sync::atomic::{compiler_fence, Ordering};
use sha2::{Digest, Sha256};
extern crate alloc;
use alloc::vec;
use alloc::vec::Vec;

const ANCHOR_DOMAIN: &[u8] = b"B60-WORM-ANCHOR-V1";
const ANCHOR_PAYLOAD_LEN: usize = 18 + 8 + 32;

#[derive(Clone, Debug)]
/// Entrada individual inmutable de la cadena WORM.
pub struct WormEntry {
    /// Índice monótono de la entrada.
    pub index: u64,
    /// Carga útil (Halt payload o SCITT receipt).
    pub payload: Vec<u8>,
    /// Firma asimétrica (EdDSA / Ed25519) del enclave.
    pub signature: Vec<u8>,
    /// Hash encadenado de la entrada.
    pub hash: [u8; 32],
}

/// Quotas exclude genesis; bytes count the exact encoded records on disk.
/// RAM is bounded by encoded bytes plus at most `max_entries` entry objects.
#[derive(Clone, Copy, Debug)]
pub struct WormLimits {
    /// Maximum committed entries, excluding genesis.
    pub max_entries: usize,
    /// Maximum sum of encoded record sizes.
    pub max_bytes: usize,
    /// Maximum encoded size of any single record.
    pub max_record_bytes: usize,
}

impl Default for WormLimits {
    fn default() -> Self {
        Self {
            max_entries: 100_000,
            max_bytes: 64 * 1024 * 1024,
            max_record_bytes: 1024 * 1024,
        }
    }
}

/// Registro HashChainedLedger (tamper-evident en memoria vía hash-chain SHA-256).
///
/// Proporciona detección criptográfica de alteración (*tamper detection*).
/// Nota de arquitectura: Al residir en RAM (`Vec<WormEntry>`), las garantías de
/// inmutabilidad física WORM o durabilidad ante colapsos de energía requieren
/// sincronización con almacenamiento persistente / WAL (como el provisto por CORTEX-Persist).
pub struct WormLedger {
    chain: Vec<WormEntry>,
    limits: WormLimits,
    encoded_bytes: usize,
    /// Archivo append-only opcional. Si existe, `append` hace `fsync` antes de confirmar.
    durable: Option<std::fs::File>,
    /// Clave pública del hardware enclave, utilizada para certificar la estructura (SCITT).
    #[allow(dead_code)]
    pub enclave_pubkey: Vec<u8>,
}

/// Alias formal riguroso de sistemas para `WormLedger`.
pub type HashChainedLedger = WormLedger;

impl WormLedger {
    /// Crea un nuevo WORM Ledger con su bloque génesis.
    pub fn new(enclave_pubkey: Vec<u8>) -> Self {
        Self::with_limits(enclave_pubkey, WormLimits::default())
    }

    /// Creates an in-memory ledger with explicit quotas; zero quotas reject appends.
    pub fn with_limits(enclave_pubkey: Vec<u8>, limits: WormLimits) -> Self {
        let genesis = WormEntry {
            index: 0,
            payload: b"BABYLON-60: GENESIS".to_vec(),
            signature: vec![],
            hash: [0u8; 32],
        };
        Self {
            chain: vec![genesis],
            limits,
            encoded_bytes: 0,
            durable: None,
            enclave_pubkey,
        }
    }

    fn admit_record(&self, payload: usize, signature: usize) -> Result<usize, &'static str> {
        let size = payload
            .checked_add(signature)
            .and_then(|n| n.checked_add(HDR_LEN + 32))
            .ok_or("WORM quota: record size overflow")?;
        if payload > u32::MAX as usize
            || signature > u16::MAX as usize
            || size > self.limits.max_record_bytes
            || self.chain.len() > self.limits.max_entries
            || size > self.limits.max_bytes.saturating_sub(self.encoded_bytes)
        {
            return Err("WORM quota exceeded");
        }
        Ok(size)
    }

    /// Añade un nuevo recibo al WORM. Falla si la firma es inválida según el Signer (TEE).
    pub fn append<S: Signer>(
        &mut self,
        payload: &[u8],
        signature: &[u8],
        signer: &S,
    ) -> Result<[u8; 32], &'static str> {
        let record_bytes = self.admit_record(payload.len(), signature.len())?;
        // Validar la firma utilizando el hardware signer (Enclave)
        if !signer.verify(payload, signature) {
            return Err("Rechazo WORM: Firma del TEE invalida");
        }

        // Hash-Chaining: H(prev_hash || payload || signature)
        let prev_hash = self.chain.last().unwrap().hash;
        let mut hasher = Sha256::new();
        hasher.update(prev_hash);
        hasher.update(payload);
        hasher.update(signature);
        let new_hash: [u8; 32] = hasher.finalize().into();

        let entry = WormEntry {
            index: self.chain.len() as u64,
            payload: payload.to_vec(),
            signature: signature.to_vec(),
            hash: new_hash,
        };

        // Durabilidad: la entrada solo se confirma tras `fsync`. Si falla, no se encadena.
        if let Some(f) = self.durable.as_mut() {
            use std::io::Write;
            let physical_bytes = f.metadata().map_err(|_| "WORM metadata failed")?.len();
            if physical_bytes != self.encoded_bytes as u64 {
                return Err("WORM file changed: reopen required");
            }
            let rec = encode_record(&entry);
            f.write_all(&rec)
                .map_err(|_| "Rechazo WORM: fallo de escritura durable")?;
            f.sync_all().map_err(|_| "Rechazo WORM: fallo de fsync")?;
        }

        self.chain.push(entry);
        self.encoded_bytes += record_bytes;
        compiler_fence(Ordering::SeqCst);

        Ok(new_hash)
    }

    /// Abre (o crea) un WORM durable en `path`. Recupera la cadena existente verificando
    /// firma y encadenado de cada registro. Un registro final incompleto (escritura rota
    /// por caída antes de `fsync`, nunca confirmada) se descarta y el archivo se trunca.
    /// Cualquier otra corrupción devuelve `Err` (fail-closed).
    pub fn open_durable<S: Signer>(
        path: &std::path::Path,
        signer: &S,
    ) -> Result<Self, alloc::string::String> {
        Self::open_durable_with_limits(path, signer, WormLimits::default())
    }

    /// Oversized history is rejected without deleting or truncating evidence.
    /// A single owner is required, as with the append-only ledger API.
    pub fn open_durable_with_limits<S: Signer>(
        path: &std::path::Path,
        signer: &S,
        limits: WormLimits,
    ) -> Result<Self, alloc::string::String> {
        use std::io::{Read, Seek, SeekFrom};
        let mut options = std::fs::OpenOptions::new();
        options.read(true).append(true).create(true);
        #[cfg(unix)]
        {
            use std::os::unix::fs::OpenOptionsExt;
            options
                .mode(0o600)
                .custom_flags(libc::O_NOFOLLOW | libc::O_CLOEXEC);
        }
        let mut file = options
            .open(path)
            .map_err(|e| alloc::format!("open: {e}"))?;
        let metadata = file
            .metadata()
            .map_err(|e| alloc::format!("metadata: {e}"))?;
        if !metadata.is_file() {
            return Err("WORM requires a regular file".into());
        }
        let file_len = metadata.len();
        if file_len > limits.max_bytes as u64 {
            return Err("WORM quota exceeded: existing history".into());
        }
        let mut ledger = WormLedger::with_limits(signer.get_public_key(), limits);
        let mut off = 0usize;
        while (off as u64) < file_len {
            if file_len - (off as u64) < HDR_LEN as u64 {
                break;
            }
            let mut header = [0u8; HDR_LEN];
            file.read_exact(&mut header)
                .map_err(|e| alloc::format!("read: {e}"))?;
            let index = u64::from_be_bytes(header[..8].try_into().unwrap());
            let plen = u32::from_be_bytes(header[8..12].try_into().unwrap());
            let slen = u16::from_be_bytes(header[12..14].try_into().unwrap());
            if header[14..18] != header_check(index, plen, slen) {
                return Err("WORM corrupto: cabecera invalida".into());
            }
            let size = ledger
                .admit_record(plen as usize, slen as usize)
                .map_err(alloc::string::String::from)?;
            if size as u64 > file_len - off as u64 {
                break;
            }
            let mut raw = vec![0u8; size];
            raw[..HDR_LEN].copy_from_slice(&header);
            file.read_exact(&mut raw[HDR_LEN..])
                .map_err(|e| alloc::format!("read: {e}"))?;
            match decode_record(&raw) {
                Decoded::Incomplete => break,
                Decoded::Corrupt => return Err("WORM corrupto: cabecera invalida".into()),
                Decoded::Record(entry, used) => {
                    let prev = ledger.chain.last().unwrap().hash;
                    if entry.index != ledger.chain.len() as u64 {
                        return Err("WORM corrupto: indice no monotono".into());
                    }
                    if !signer.verify(&entry.payload, &entry.signature) {
                        return Err("WORM corrupto: firma invalida".into());
                    }
                    let mut h = Sha256::new();
                    h.update(prev);
                    h.update(&entry.payload);
                    h.update(&entry.signature);
                    let expect: [u8; 32] = h.finalize().into();
                    if expect != entry.hash {
                        return Err("WORM corrupto: hash encadenado invalido".into());
                    }
                    ledger.chain.push(entry);
                    ledger.encoded_bytes += used;
                    off += used;
                }
            }
        }
        if (off as u64) < file_len {
            // Cola rota: truncar a la última entrada completa.
            file.set_len(off as u64)
                .map_err(|e| alloc::format!("truncate: {e}"))?;
            file.sync_all().map_err(|e| alloc::format!("fsync: {e}"))?;
        }
        file.seek(SeekFrom::End(0))
            .map_err(|e| alloc::format!("seek: {e}"))?;
        ledger.durable = Some(file);
        Ok(ledger)
    }

    /// Ancla de cabeza `(len, head_hash)`. Debe publicarse fuera del proceso
    /// (recibo firmado, SCITT/OTS) para detectar truncado de cola.
    pub fn head_anchor(&self) -> (u64, [u8; 32]) {
        (self.chain.len() as u64, self.chain.last().unwrap().hash)
    }

    /// Audita la cadena y verifica que contiene el ancla externa: misma entrada
    /// en la posición `len-1` con el mismo hash. Detecta truncado de cola y
    /// reescritura de historia posterior al ancla.
    pub fn audit_against_anchor(&self, anchor: (u64, [u8; 32])) -> bool {
        let (len, hash) = anchor;
        if len == 0 || (self.chain.len() as u64) < len {
            return false;
        }
        self.audit_integrity() && self.chain[(len - 1) as usize].hash == hash
    }

    /// Emite un recibo firmado del ancla de cabeza: `payload(58 B) || firma`.
    /// payload = `B60-WORM-ANCHOR-V1` || len (u64 BE) || head_hash (32 B).
    /// Separación de dominio: la firma no es reutilizable como recibo HALT.
    pub fn signed_anchor<S: Signer>(&self, signer: &S) -> Result<Vec<u8>, alloc::string::String> {
        let (len, hash) = self.head_anchor();
        let mut payload = Vec::with_capacity(ANCHOR_PAYLOAD_LEN);
        payload.extend_from_slice(ANCHOR_DOMAIN);
        payload.extend_from_slice(&len.to_be_bytes());
        payload.extend_from_slice(&hash);
        let sig = signer.sign(&payload)?;
        payload.extend_from_slice(&sig);
        Ok(payload)
    }

    /// Verifica un recibo de ancla y lo contrasta con esta cadena.
    /// `false` si el recibo está malformado, mal firmado, o la cadena no lo contiene.
    pub fn verify_anchor_receipt<S: Signer>(&self, receipt: &[u8], signer: &S) -> bool {
        if receipt.len() <= ANCHOR_PAYLOAD_LEN {
            return false;
        }
        let (payload, sig) = receipt.split_at(ANCHOR_PAYLOAD_LEN);
        if &payload[..ANCHOR_DOMAIN.len()] != ANCHOR_DOMAIN || !signer.verify(payload, sig) {
            return false;
        }
        let d = ANCHOR_DOMAIN.len();
        let mut len_b = [0u8; 8];
        len_b.copy_from_slice(&payload[d..d + 8]);
        let mut hash = [0u8; 32];
        hash.copy_from_slice(&payload[d + 8..d + 40]);
        self.audit_against_anchor((u64::from_be_bytes(len_b), hash))
    }

    /// Audita toda la cadena criptográfica
    pub fn audit_integrity(&self) -> bool {
        for window in self.chain.windows(2) {
            let prev = &window[0];
            let curr = &window[1];

            let mut hasher = Sha256::new();
            hasher.update(prev.hash);
            hasher.update(&curr.payload);
            hasher.update(&curr.signature);
            let expected_hash: [u8; 32] = hasher.finalize().into();

            if curr.hash != expected_hash {
                return false;
            }
        }
        true
    }
}

/// Cabecera fija (18 B): index u64 BE | plen u32 BE | slen u16 BE | chk 4 B.
/// `chk` = primeros 4 B de SHA-256(index||plen||slen): detecta corrupción de longitudes
/// y la distingue de una escritura rota (cabecera incompleta o cuerpo corto con cabecera válida).
/// Cuerpo: payload | firma | hash 32 B.
const HDR_LEN: usize = 18;

fn header_check(index: u64, plen: u32, slen: u16) -> [u8; 4] {
    let mut h = Sha256::new();
    h.update(index.to_be_bytes());
    h.update(plen.to_be_bytes());
    h.update(slen.to_be_bytes());
    let d: [u8; 32] = h.finalize().into();
    [d[0], d[1], d[2], d[3]]
}

fn encode_record(e: &WormEntry) -> Vec<u8> {
    let plen = e.payload.len() as u32;
    let slen = e.signature.len() as u16;
    let mut v = Vec::with_capacity(HDR_LEN + e.payload.len() + e.signature.len() + 32);
    v.extend_from_slice(&e.index.to_be_bytes());
    v.extend_from_slice(&plen.to_be_bytes());
    v.extend_from_slice(&slen.to_be_bytes());
    v.extend_from_slice(&header_check(e.index, plen, slen));
    v.extend_from_slice(&e.payload);
    v.extend_from_slice(&e.signature);
    v.extend_from_slice(&e.hash);
    v
}

enum Decoded {
    Record(WormEntry, usize),
    /// Escritura rota al final (cabecera corta o cuerpo corto bajo cabecera válida).
    Incomplete,
    /// Cabecera completa con comprobación inválida: corrupción, no escritura rota.
    Corrupt,
}

fn decode_record(b: &[u8]) -> Decoded {
    if b.len() < HDR_LEN {
        return Decoded::Incomplete;
    }
    let index = u64::from_be_bytes(b[0..8].try_into().unwrap());
    let plen = u32::from_be_bytes(b[8..12].try_into().unwrap());
    let slen = u16::from_be_bytes(b[12..14].try_into().unwrap());
    if b[14..18] != header_check(index, plen, slen) {
        return Decoded::Corrupt;
    }
    let total = HDR_LEN + plen as usize + slen as usize + 32;
    if b.len() < total {
        return Decoded::Incomplete;
    }
    let p0 = HDR_LEN;
    let s0 = p0 + plen as usize;
    let h0 = s0 + slen as usize;
    let hash: [u8; 32] = b[h0..h0 + 32].try_into().unwrap();
    Decoded::Record(
        WormEntry {
            index,
            payload: b[p0..s0].to_vec(),
            signature: b[s0..h0].to_vec(),
            hash,
        },
        total,
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::receipt::NullSigner;

    fn ledger_with(n: usize) -> (WormLedger, NullSigner) {
        let signer = NullSigner;
        let mut ledger = WormLedger::new(signer.get_public_key());
        for i in 0..n {
            let payload = alloc::format!("EVENT_{i:02}").into_bytes();
            let sig = signer.sign(&payload).unwrap();
            ledger.append(&payload, &sig, &signer).unwrap();
        }
        (ledger, signer)
    }

    #[test]
    fn test_worm_ledger_append_and_tamper_detection() {
        let (mut ledger, _) = ledger_with(1);
        assert!(ledger.audit_integrity());
        ledger.chain[1].payload = b"TAMPERED_STATE".to_vec();
        assert!(
            !ledger.audit_integrity(),
            "Tampered block must fail audit integrity check"
        );
    }

    #[test]
    fn invalid_signature_is_rejected_and_chain_unchanged() {
        let (mut ledger, signer) = ledger_with(2);
        let before = ledger.chain.len();
        let bad_sig = vec![1u8; 64];
        assert!(ledger.append(b"X", &bad_sig, &signer).is_err());
        assert_eq!(ledger.chain.len(), before);
        assert!(ledger.audit_integrity());
    }

    #[test]
    fn indices_are_monotonic_and_hashes_chain() {
        let (ledger, _) = ledger_with(5);
        for (i, e) in ledger.chain.iter().enumerate() {
            assert_eq!(e.index, i as u64);
        }
        for w in ledger.chain.windows(2) {
            assert_ne!(w[0].hash, w[1].hash);
        }
        assert!(ledger.audit_integrity());
    }

    #[test]
    fn tampering_any_middle_entry_is_detected() {
        for target in 1..=4 {
            let (mut ledger, _) = ledger_with(4);
            ledger.chain[target].payload.push(0xFF);
            assert!(!ledger.audit_integrity(), "tamper at {target} undetected");
        }
    }

    #[test]
    fn reordering_entries_is_detected() {
        let (mut ledger, _) = ledger_with(3);
        ledger.chain.swap(1, 2);
        assert!(!ledger.audit_integrity());
    }

    #[test]
    fn signature_tamper_is_detected() {
        let (mut ledger, _) = ledger_with(2);
        ledger.chain[1].signature[0] ^= 0x01;
        assert!(!ledger.audit_integrity());
    }

    /// Sin ancla externa el truncado de cola no es detectable (límite de audit_integrity).
    #[test]
    fn tail_truncation_is_not_detected_without_external_anchor() {
        let (mut ledger, _) = ledger_with(4);
        ledger.chain.pop();
        assert!(ledger.audit_integrity());
    }

    #[test]
    fn anchor_detects_tail_truncation() {
        let (mut ledger, _) = ledger_with(4);
        let anchor = ledger.head_anchor();
        assert!(ledger.audit_against_anchor(anchor));
        ledger.chain.pop();
        assert!(!ledger.audit_against_anchor(anchor));
    }

    #[test]
    fn anchor_survives_legitimate_growth() {
        let (mut ledger, signer) = ledger_with(3);
        let anchor = ledger.head_anchor();
        let sig = signer.sign(b"MORE").unwrap();
        ledger.append(b"MORE", &sig, &signer).unwrap();
        assert!(ledger.audit_against_anchor(anchor));
    }

    #[test]
    fn anchor_detects_history_rewrite_with_recomputed_hashes() {
        let (mut ledger, _) = ledger_with(4);
        let anchor = ledger.head_anchor();
        // Atacante reescribe la entrada 2 y recalcula toda la cadena posterior.
        let mut prev = ledger.chain[1].hash;
        for i in 2..ledger.chain.len() {
            if i == 2 {
                ledger.chain[i].payload = b"FORGED".to_vec();
            }
            let mut h = Sha256::new();
            h.update(prev);
            h.update(&ledger.chain[i].payload);
            h.update(&ledger.chain[i].signature);
            let nh: [u8; 32] = h.finalize().into();
            ledger.chain[i].hash = nh;
            prev = nh;
        }
        assert!(
            ledger.audit_integrity(),
            "cadena reescrita es internamente consistente"
        );
        assert!(
            !ledger.audit_against_anchor(anchor),
            "el ancla externa la delata"
        );
    }

    #[test]
    fn anchor_with_zero_len_or_future_len_is_rejected() {
        let (ledger, _) = ledger_with(2);
        assert!(!ledger.audit_against_anchor((0, [0u8; 32])));
        assert!(!ledger.audit_against_anchor((99, [0u8; 32])));
    }

    #[test]
    fn signed_anchor_roundtrip_and_truncation_detected() {
        let (mut ledger, signer) = ledger_with(4);
        let receipt = ledger.signed_anchor(&signer).unwrap();
        assert!(ledger.verify_anchor_receipt(&receipt, &signer));
        ledger.chain.pop();
        assert!(!ledger.verify_anchor_receipt(&receipt, &signer));
    }

    #[test]
    fn signed_anchor_tamper_and_malformed_rejected() {
        let (ledger, signer) = ledger_with(3);
        let mut r = ledger.signed_anchor(&signer).unwrap();
        assert!(!ledger.verify_anchor_receipt(&r[..ANCHOR_PAYLOAD_LEN], &signer));
        assert!(!ledger.verify_anchor_receipt(&[], &signer));
        let last = r.len() - 1;
        r[last] ^= 1;
        assert!(!ledger.verify_anchor_receipt(&r, &signer));
        let mut r2 = ledger.signed_anchor(&signer).unwrap();
        r2[0] ^= 1;
        assert!(!ledger.verify_anchor_receipt(&r2, &signer));
    }

    #[test]
    fn signed_anchor_with_real_p256_signature() {
        let signer = crate::receipt::P256Signer::new();
        let mut ledger = WormLedger::new(signer.get_public_key());
        let sig = signer.sign(b"E1").unwrap();
        ledger.append(b"E1", &sig, &signer).unwrap();
        let receipt = ledger.signed_anchor(&signer).unwrap();
        assert!(ledger.verify_anchor_receipt(&receipt, &signer));
        let other = crate::receipt::P256Signer::new();
        assert!(
            !ledger.verify_anchor_receipt(&receipt, &other),
            "otra clave no verifica"
        );
    }

    fn tmp_path(tag: &str) -> std::path::PathBuf {
        let mut p = std::env::temp_dir();
        p.push(alloc::format!(
            "b60_worm_{tag}_{}_{}.log",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        p
    }

    #[test]
    fn quotas_reject_append_and_history_without_mutation() {
        let path = tmp_path("quotas");
        let signer = NullSigner;
        let payload = b"bounded";
        let signature = signer.sign(payload).unwrap();
        let size = HDR_LEN + 32 + payload.len() + signature.len();
        let limits = WormLimits {
            max_entries: 1,
            max_bytes: size,
            max_record_bytes: size,
        };
        let mut ledger = WormLedger::open_durable_with_limits(&path, &signer, limits).unwrap();
        ledger.append(payload, &signature, &signer).unwrap();
        let anchor = ledger.head_anchor();
        let bytes = std::fs::read(&path).unwrap();
        assert!(ledger.append(payload, &signature, &signer).is_err());
        assert_eq!(ledger.head_anchor(), anchor);
        assert_eq!(std::fs::read(&path).unwrap(), bytes);
        drop(ledger);
        let reopened = WormLedger::open_durable_with_limits(&path, &signer, limits).unwrap();
        assert_eq!(reopened.head_anchor(), anchor);
        drop(reopened);
        for lower in [
            WormLimits {
                max_entries: 0,
                ..limits
            },
            WormLimits {
                max_bytes: size - 1,
                ..limits
            },
            WormLimits {
                max_record_bytes: size - 1,
                ..limits
            },
        ] {
            assert!(WormLedger::open_durable_with_limits(&path, &signer, lower).is_err());
            assert_eq!(std::fs::read(&path).unwrap(), bytes);
        }
        std::fs::remove_file(path).unwrap();
    }

    #[cfg(unix)]
    #[test]
    fn durable_open_rejects_symlink_without_touching_target() {
        let target = tmp_path("symlink_target");
        let link = tmp_path("symlink_ledger");
        // Warm up a real private ledger, then use its bytes as the independent witness.
        let mut warmup = WormLedger::open_durable(&target, &NullSigner).unwrap();
        let signature = NullSigner.sign(b"warmup").unwrap();
        warmup.append(b"warmup", &signature, &NullSigner).unwrap();
        drop(warmup);
        let before = std::fs::read(&target).unwrap();
        std::os::unix::fs::symlink(&target, &link).unwrap();
        let all_rejected = (0..256).all(|_| WormLedger::open_durable(&link, &NullSigner).is_err());
        let witness = std::fs::read(&target).unwrap();
        std::fs::remove_file(link).unwrap();
        std::fs::remove_file(target).unwrap();
        assert!(all_rejected, "symlink must not become a durable ledger");
        assert_eq!(witness, before, "the independent target must remain intact");
    }

    #[test]
    fn memory_quotas_and_wire_lengths_reject_before_append() {
        let signer = NullSigner;
        let sig = signer.sign(b"x").unwrap();
        let size = HDR_LEN + 32 + 1 + sig.len();
        for limits in [
            WormLimits {
                max_entries: 0,
                ..WormLimits::default()
            },
            WormLimits {
                max_bytes: size - 1,
                ..WormLimits::default()
            },
            WormLimits {
                max_record_bytes: size - 1,
                ..WormLimits::default()
            },
        ] {
            let mut ledger = WormLedger::with_limits(vec![], limits);
            let anchor = ledger.head_anchor();
            assert!(ledger.append(b"x", &sig, &signer).is_err());
            assert_eq!(ledger.head_anchor(), anchor);
        }
        let ledger = WormLedger::new(vec![]);
        assert!(ledger.admit_record(1, u16::MAX as usize + 1).is_err());
        assert!(ledger.admit_record(usize::MAX, 1).is_err());
    }

    #[test]
    fn oversized_valid_header_is_rejected_without_truncation() {
        use std::io::Write;
        let path = tmp_path("oversized_header");
        let mut file = std::fs::File::create(&path).unwrap();
        let plen = u32::MAX;
        let mut header = Vec::new();
        header.extend_from_slice(&1u64.to_be_bytes());
        header.extend_from_slice(&plen.to_be_bytes());
        header.extend_from_slice(&0u16.to_be_bytes());
        header.extend_from_slice(&header_check(1, plen, 0));
        file.write_all(&header).unwrap();
        drop(file);
        assert!(WormLedger::open_durable(&path, &NullSigner).is_err());
        assert_eq!(std::fs::read(&path).unwrap(), header);
        std::fs::remove_file(path).unwrap();
    }

    #[test]
    fn durable_roundtrip_survives_reopen() {
        let path = tmp_path("rt");
        let signer = NullSigner;
        let anchor;
        {
            let mut l = WormLedger::open_durable(&path, &signer).unwrap();
            for i in 0..5 {
                let pl = alloc::format!("E{i}").into_bytes();
                let sig = signer.sign(&pl).unwrap();
                l.append(&pl, &sig, &signer).unwrap();
            }
            anchor = l.head_anchor();
        }
        let l2 = WormLedger::open_durable(&path, &signer).unwrap();
        assert_eq!(l2.head_anchor(), anchor);
        assert!(l2.audit_against_anchor(anchor));
        let _ = std::fs::remove_file(&path);
    }

    #[test]
    fn durable_torn_tail_is_discarded_and_file_truncated() {
        let path = tmp_path("torn");
        let signer = NullSigner;
        let anchor;
        {
            let mut l = WormLedger::open_durable(&path, &signer).unwrap();
            for i in 0..3 {
                let pl = alloc::format!("E{i}").into_bytes();
                let sig = signer.sign(&pl).unwrap();
                l.append(&pl, &sig, &signer).unwrap();
            }
            anchor = l.head_anchor();
        }
        let good_len = std::fs::metadata(&path).unwrap().len();
        {
            use std::io::Write;
            let mut f = std::fs::OpenOptions::new()
                .append(true)
                .open(&path)
                .unwrap();
            f.write_all(&[0, 0, 0, 0, 0, 0, 0, 9, 0, 0]).unwrap(); // registro roto
        }
        let l = WormLedger::open_durable(&path, &signer).unwrap();
        assert_eq!(
            l.head_anchor(),
            anchor,
            "las entradas confirmadas se conservan"
        );
        assert_eq!(
            std::fs::metadata(&path).unwrap().len(),
            good_len,
            "cola rota truncada"
        );
        let _ = std::fs::remove_file(&path);
    }

    #[test]
    fn durable_corruption_in_middle_fails_closed() {
        let path = tmp_path("corrupt");
        let signer = NullSigner;
        {
            let mut l = WormLedger::open_durable(&path, &signer).unwrap();
            for i in 0..3 {
                let pl = alloc::format!("E{i}").into_bytes();
                let sig = signer.sign(&pl).unwrap();
                l.append(&pl, &sig, &signer).unwrap();
            }
        }
        let mut bytes = std::fs::read(&path).unwrap();
        bytes[12] ^= 0xFF; // longitud de firma del primer registro
        std::fs::write(&path, &bytes).unwrap();
        assert!(
            WormLedger::open_durable(&path, &signer).is_err(),
            "longitud corrupta no es cola rota"
        );
        let _ = std::fs::remove_file(&path);
    }

    #[test]
    fn durable_payload_bitflip_in_middle_fails_closed_and_keeps_file() {
        let path = tmp_path("bitflip");
        let signer = NullSigner;
        {
            let mut l = WormLedger::open_durable(&path, &signer).unwrap();
            for i in 0..3 {
                let pl = alloc::format!("E{i}").into_bytes();
                let sig = signer.sign(&pl).unwrap();
                l.append(&pl, &sig, &signer).unwrap();
            }
        }
        let mut bytes = std::fs::read(&path).unwrap();
        bytes[HDR_LEN] ^= 0x01; // primer byte del payload del primer registro
        std::fs::write(&path, &bytes).unwrap();
        let len_before = std::fs::metadata(&path).unwrap().len();
        assert!(WormLedger::open_durable(&path, &signer).is_err());
        assert_eq!(
            std::fs::metadata(&path).unwrap().len(),
            len_before,
            "no se trunca ante corrupción"
        );
        let _ = std::fs::remove_file(&path);
    }

    #[test]
    fn durable_torn_body_with_valid_header_is_discarded() {
        let path = tmp_path("tornbody");
        let signer = NullSigner;
        let anchor;
        {
            let mut l = WormLedger::open_durable(&path, &signer).unwrap();
            let sig = signer.sign(b"A").unwrap();
            l.append(b"A", &sig, &signer).unwrap();
            anchor = l.head_anchor();
        }
        let good_len = std::fs::metadata(&path).unwrap().len();
        {
            use std::io::Write;
            let e = WormEntry {
                index: 2,
                payload: b"B".to_vec(),
                signature: vec![0u8; 64],
                hash: [7u8; 32],
            };
            let rec = encode_record(&e);
            let mut f = std::fs::OpenOptions::new()
                .append(true)
                .open(&path)
                .unwrap();
            f.write_all(&rec[..rec.len() - 20]).unwrap(); // cabecera válida, cuerpo corto
        }
        let l = WormLedger::open_durable(&path, &signer).unwrap();
        assert_eq!(l.head_anchor(), anchor);
        assert_eq!(std::fs::metadata(&path).unwrap().len(), good_len);
        let _ = std::fs::remove_file(&path);
    }

    #[test]
    fn durable_reopened_ledger_keeps_appending_consistently() {
        let path = tmp_path("grow");
        let signer = NullSigner;
        for round in 0..3 {
            let mut l = WormLedger::open_durable(&path, &signer).unwrap();
            let pl = alloc::format!("R{round}").into_bytes();
            let sig = signer.sign(&pl).unwrap();
            l.append(&pl, &sig, &signer).unwrap();
        }
        let l = WormLedger::open_durable(&path, &signer).unwrap();
        assert_eq!(l.head_anchor().0, 4); // génesis + 3
        assert!(l.audit_integrity());
        let _ = std::fs::remove_file(&path);
    }
}
