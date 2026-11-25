// Shared source keeps the C ABI and memory ordering identical in both crates.
include!("../../../../src/shared_manifest_core.rs");
impl SharedManifest {
    pub fn epistemic_halt(&self, secret_key_bytes: &[u8; 32]) -> Result<crate::scitt::ScittReceipt, &'static str> {
        let epoch = self.freeze()?;
        Ok(crate::scitt::ScittReceipt::new(epoch, secret_key_bytes))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_shared_manifest_layout_invariants() {
        // [AX-2] TOPOLOGY: Garantizar isomorfismo estricto de caché L1
        assert_eq!(
            core::mem::size_of::<SharedManifest>(),
            64,
            "SharedManifest debe pesar exactamente 64 bytes para evitar False Sharing"
        );
        assert_eq!(
            core::mem::align_of::<SharedManifest>(),
            64,
            "SharedManifest debe estar alineado a 64 bytes"
        );
    }

    #[test]
    fn test_seqlock_publish_and_read() {
        let manifest = SharedManifest::new();
        
        // Estado inicial
        assert_eq!(manifest.status_flag.load(Ordering::SeqCst), RUNNING);
        
        // Publicar dato
        let test_hash = [0xAAAA, 0xBBBB, 0xCCCC, 0xDDDD];
        let epoch = 42;
        assert!(manifest.publish(epoch, &test_hash).is_ok());
        
        // Leer dato
        let read_result = manifest.read();
        assert!(read_result.is_some());
        let (read_epoch, read_hash) = read_result.expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
        
        assert_eq!(read_epoch, 42);
        assert_eq!(read_hash, test_hash);
    }

    #[test]
    fn test_epistemic_halt() {
        let manifest = SharedManifest::new();
        let secret_bytes = [0u8; 32];
        
        let receipt = manifest.epistemic_halt(&secret_bytes).expect("stable terminal snapshot");
        assert_eq!(receipt.epoch_halted, 0); // Initial logical epoch is shared with the root crate.
        
        // No se puede publicar
        assert!(manifest.publish(1, &[0; 4]).is_err());
        
        // Las lecturas devuelven None
        assert!(manifest.read().is_none());
        assert_eq!(manifest.status_flag.load(Ordering::SeqCst), POISONED);
    }
}
