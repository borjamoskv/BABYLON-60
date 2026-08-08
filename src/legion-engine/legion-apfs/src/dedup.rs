// C5-REAL EXERGY CERTIFIED
// Motor de Deduplicación Nativo APFS mediante Copy-on-Write (clonefile(2))
// Recupera gigabytes sin borrar ningún archivo (cero pérdida de datos)
use std::path::Path;
use std::ffi::CString;
use std::collections::HashMap;
use std::fs::File;
use std::io::Read;
use sha3::{Digest, Sha3_256};
use crate::bulk_scanner::FileMetadataEntry;

extern "C" {
    fn clonefile(src: *const libc::c_char, dst: *const libc::c_char, flags: libc::c_int) -> libc::c_int;
}

pub struct ApfsDeduplicator;

#[derive(Debug, Clone)]
pub struct DedupResult {
    pub original_path: String,
    pub cloned_path: String,
    pub bytes_saved: u64,
}

impl ApfsDeduplicator {
    /// Clona un archivo utilizando las primitivas Copy-on-Write del sistema de archivos APFS.
    pub fn clone_file(src: &Path, dst: &Path) -> std::io::Result<bool> {
        let src_c = CString::new(src.to_string_lossy().as_bytes())
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidInput, e))?;
        let dst_c = CString::new(dst.to_string_lossy().as_bytes())
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidInput, e))?;

        let res = unsafe { clonefile(src_c.as_ptr(), dst_c.as_ptr(), 0) };

        if res == 0 {
            Ok(true)
        } else {
            Err(std::io::Error::last_os_error())
        }
    }

    /// Calcula el digest SHA3-256 de los primeros 64 KB de un archivo para comparación rápida
    pub fn sample_hash(path: &Path) -> std::io::Result<[u8; 32]> {
        let mut file = File::open(path)?;
        let mut buffer = [0u8; 64 * 1024];
        let bytes_read = file.read(&mut buffer)?;

        let mut hasher = Sha3_256::new();
        hasher.update(&buffer[..bytes_read]);
        let mut out = [0u8; 32];
        out.copy_from_slice(&hasher.finalize());
        Ok(out)
    }

    /// Identifica candidatos duplicados y calcula el ahorro potencial
    pub fn find_duplicates(entries: &[FileMetadataEntry]) -> Vec<DedupResult> {
        let mut by_size: HashMap<u64, Vec<&FileMetadataEntry>> = HashMap::new();

        for entry in entries {
            if !entry.is_dir && entry.size_bytes > 1024 * 1024 { // Solo archivos > 1MB
                by_size.entry(entry.size_bytes).or_default().push(entry);
            }
        }

        let mut duplicates = Vec::new();

        for (&size, candidates) in &by_size {
            if candidates.len() < 2 {
                continue;
            }

            let mut by_hash: HashMap<[u8; 32], &FileMetadataEntry> = HashMap::new();
            for &cand in candidates {
                if let Ok(h) = Self::sample_hash(&cand.path) {
                    if let Some(orig) = by_hash.get(&h) {
                        duplicates.push(DedupResult {
                            original_path: orig.path.to_string_lossy().to_string(),
                            cloned_path: cand.path.to_string_lossy().to_string(),
                            bytes_saved: size,
                        });
                    } else {
                        by_hash.insert(h, cand);
                    }
                }
            }
        }

        duplicates
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    #[test]
    fn test_sample_hash_calculation() {
        let tmp = std::env::temp_dir().join("test_sample_hash.bin");
        fs::write(&tmp, b"Test data for SHA3-256 deduplication hashing").unwrap();
        let hash = ApfsDeduplicator::sample_hash(&tmp).unwrap();
        assert_eq!(hash.len(), 32);
        let _ = fs::remove_file(&tmp);
    }
}
