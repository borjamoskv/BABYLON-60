use crate::receipt::Signer;
use sha2::{Digest, Sha256};
use core::sync::atomic::{compiler_fence, Ordering};
extern crate alloc;
use alloc::vec::Vec;
use alloc::vec;

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

/// Registro HashChainedLedger (tamper-evident en memoria vía hash-chain SHA-256).
///
/// Proporciona detección criptográfica de alteración (*tamper detection*).
/// Nota de arquitectura: Al residir en RAM (`Vec<WormEntry>`), las garantías de
/// inmutabilidad física WORM o durabilidad ante colapsos de energía requieren
/// sincronización con almacenamiento persistente / WAL (como el provisto por CORTEX-Persist).
pub struct WormLedger {
    chain: Vec<WormEntry>,
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
        let genesis = WormEntry {
            index: 0,
            payload: b"BABYLON-60: GENESIS".to_vec(),
            signature: vec![],
            hash: [0u8; 32],
        };
        Self {
            chain: vec![genesis],
            durable: None,
            enclave_pubkey,
        }
    }

    /// Añade un nuevo recibo al WORM. Falla si la firma es inválida según el Signer (TEE).
    pub fn append<S: Signer>(&mut self, payload: &[u8], signature: &[u8], signer: &S) -> Result<[u8; 32], &'static str> {
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
            let rec = encode_record(&entry);
            f.write_all(&rec).map_err(|_| "Rechazo WORM: fallo de escritura durable")?;
            f.sync_all().map_err(|_| "Rechazo WORM: fallo de fsync")?;
        }

        self.chain.push(entry);
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
        use std::io::{Read, Seek, SeekFrom};
        let mut file = std::fs::OpenOptions::new()
            .read(true)
            .append(true)
            .create(true)
            .open(path)
            .map_err(|e| alloc::format!("open: {e}"))?;
        let mut raw = Vec::new();
        file.read_to_end(&mut raw).map_err(|e| alloc::format!("read: {e}"))?;

        let mut ledger = WormLedger::new(signer.get_public_key());
        let mut off = 0usize;
        while off < raw.len() {
            match decode_record(&raw[off..]) {
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
                    off += used;
                }
            }
        }
        if off < raw.len() {
            // Cola rota: truncar a la última entrada completa.
            file.set_len(off as u64).map_err(|e| alloc::format!("truncate: {e}"))?;
            file.sync_all().map_err(|e| alloc::format!("fsync: {e}"))?;
        }
        file.seek(SeekFrom::End(0)).map_err(|e| alloc::format!("seek: {e}"))?;
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
        WormEntry { index, payload: b[p0..s0].to_vec(), signature: b[s0..h0].to_vec(), hash },
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
        assert!(!ledger.audit_integrity(), "Tampered block must fail audit integrity check");
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
        assert!(ledger.audit_integrity(), "cadena reescrita es internamente consistente");
        assert!(!ledger.audit_against_anchor(anchor), "el ancla externa la delata");
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
        assert!(!ledger.verify_anchor_receipt(&receipt, &other), "otra clave no verifica");
    }

    fn tmp_path(tag: &str) -> std::path::PathBuf {
        let mut p = std::env::temp_dir();
        p.push(alloc::format!("b60_worm_{tag}_{}_{}.log", std::process::id(),
            std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos()));
        p
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
            let mut f = std::fs::OpenOptions::new().append(true).open(&path).unwrap();
            f.write_all(&[0, 0, 0, 0, 0, 0, 0, 9, 0, 0]).unwrap(); // registro roto
        }
        let l = WormLedger::open_durable(&path, &signer).unwrap();
        assert_eq!(l.head_anchor(), anchor, "las entradas confirmadas se conservan");
        assert_eq!(std::fs::metadata(&path).unwrap().len(), good_len, "cola rota truncada");
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
        assert!(WormLedger::open_durable(&path, &signer).is_err(), "longitud corrupta no es cola rota");
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
        assert_eq!(std::fs::metadata(&path).unwrap().len(), len_before, "no se trunca ante corrupción");
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
            let e = WormEntry { index: 2, payload: b"B".to_vec(), signature: vec![0u8; 64], hash: [7u8; 32] };
            let rec = encode_record(&e);
            let mut f = std::fs::OpenOptions::new().append(true).open(&path).unwrap();
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
