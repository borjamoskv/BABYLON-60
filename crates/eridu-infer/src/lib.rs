//! CORTEX/BABYLON-60 Sovereign Local Inference Engine (ERIDU-INFER).
//! Desacople en sala limpia de runtimes LLM (LM Studio / Ollama) hacia bare-metal en silicio:
//! - GGUF v3 zero-copy memory mapping (`gguf`)
//! - Apple Silicon Unified Memory Architecture allocator (`uma`)
//! - Zero-HTTP IPC via Seqlock SPMC KUDURRU-64 y Unix Domain Sockets (`ipc`)
//! - Causal Gate y WORM ledger bajo EU AI Act Arts. 12-14 (`gate`)
//! - Compatibilidad wire-format con LM Studio y OpenAI REST API (`auth`, `server`, `hud`)

pub mod auth;
pub mod gate;
pub mod gguf;
pub mod hud;
pub mod ipc;
pub mod server;
pub mod types;
pub mod uma;

#[cfg(test)]
mod tests {
    use super::gate::BabylonCausalGate;
    use super::gguf::{GgufModel, GGUF_MAGIC};
    use super::ipc::{InferenceTelemetryBlock, KudurruSeqlock};
    use super::uma::{UmaBufferPool, DARWIN_PAGE_SIZE};
    use byteorder::{ByteOrder, LittleEndian};
    use std::io::Write;

    #[test]
    fn test_causal_gate_logical_tick_and_shared_manifest_publish() {
        let mut gate1 = BabylonCausalGate::new();
        let mut gate2 = BabylonCausalGate::new();

        let r1 = gate1
            .evaluate_and_seal("deepseek-r1-distill-qwen-32b", "auditoria concursal")
            .unwrap();
        let r2 = gate2
            .evaluate_and_seal("deepseek-r1-distill-qwen-32b", "auditoria concursal")
            .unwrap();

        // Invariante INV_C5_CANONICAL_LOGICAL_TICK: mismo logical_tick + input => mismo hash y sello
        assert_eq!(r1.logical_tick, 1);
        assert_eq!(r1.prompt_hash, r2.prompt_hash);
        assert_eq!(r1.attestation_seal, r2.attestation_seal);

        // El SharedManifest de 64B refleja inmediatamente la publicación Seqlock (RFO = 0)
        let (epoch, hash_words) = gate1.read_manifest_snapshot().unwrap();
        assert_eq!(epoch, 1);
        assert_ne!(hash_words, [0; 4]);
    }

    #[test]
    fn test_uma_buffer_alignment_and_pool_reuse() {
        let mut pool = UmaBufferPool::new(2, 4096).unwrap();
        let mut buf = pool.acquire().unwrap();
        assert_eq!(buf.size, DARWIN_PAGE_SIZE);
        assert_eq!((buf.as_ptr() as usize) % DARWIN_PAGE_SIZE, 0);
        buf.as_mut_slice()[0..4].copy_from_slice(b"B60!");
        assert_eq!(&buf.as_slice()[0..4], b"B60!");
        pool.release(buf);
    }

    #[test]
    fn test_kudurru_seqlock_telemetry_roundtrip() {
        let lock = KudurruSeqlock::new(InferenceTelemetryBlock::default());
        assert_eq!(std::mem::align_of_val(&lock), 64);
        let next = InferenceTelemetryBlock {
            tokens_generated: 128,
            prompt_tokens: 32,
            last_latency_micros: 420,
            active_context_length: 160,
            is_generating: false,
        };
        lock.write(next);
        assert_eq!(lock.read(), next);
    }

    #[test]
    fn test_gguf_v3_mmap_zero_copy_parser() {
        let mut payload = Vec::new();
        let mut hdr = [0u8; 24];
        LittleEndian::write_u32(&mut hdr[0..4], GGUF_MAGIC);
        LittleEndian::write_u32(&mut hdr[4..8], 3); // version 3
        LittleEndian::write_u64(&mut hdr[8..16], 1); // 1 tensor
        LittleEndian::write_u64(&mut hdr[16..24], 0); // 0 metadata kv
        payload.extend_from_slice(&hdr);

        // Tensor descriptor: name="w0", n_dims=1, dim[0]=4, type=0 (F32), offset=0
        payload.extend_from_slice(&(2u64).to_le_bytes());
        payload.extend_from_slice(b"w0");
        payload.extend_from_slice(&(1u32).to_le_bytes());
        payload.extend_from_slice(&(4u64).to_le_bytes());
        payload.extend_from_slice(&(0u32).to_le_bytes());
        payload.extend_from_slice(&(0u64).to_le_bytes());

        // Align to 32 bytes + 16 bytes of F32 tensor data
        while payload.len() % 32 != 0 {
            payload.push(0);
        }
        payload.extend_from_slice(&[1u8; 16]);

        let tmp_path = std::env::temp_dir().join("eridu_test_model.gguf");
        {
            let mut f = std::fs::File::create(&tmp_path).unwrap();
            f.write_all(&payload).unwrap();
        }

        let model = GgufModel::load_mmap(&tmp_path).unwrap();
        assert_eq!(model.version, 3);
        assert_eq!(model.tensor_count, 1);
        assert_eq!(model.tensors[0].name, "w0");
        assert_eq!(model.get_tensor_data(0).unwrap(), &[1u8; 16]);
        let _ = std::fs::remove_file(&tmp_path);
    }
}
