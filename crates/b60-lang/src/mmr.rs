// ============================================================================
// B60 BARE-METAL MERKLE MOUNTAIN RANGE (MMR) ACCUMULATOR
// Standard: draft-bryce-cose-merkle-mountain-range-proofs-01 / EU AI Act Art. 12
// ============================================================================

use sha3::{Digest, Sha3_256};

pub const DOMAIN_MMR_NODE: u8 = 0x01;
pub const DOMAIN_MMR_PEAKS: u8 = 0x02;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MmrProofStep {
    pub sibling: [u8; 32],
    pub is_left: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MmrInclusionProof {
    pub leaf_index: usize,
    pub total_leaves: usize,
    pub peak_index: usize,
    pub inner_proof: Vec<MmrProofStep>,
    pub other_peaks: Vec<[u8; 32]>,
    pub mmr_root: [u8; 32],
}

pub struct MmrAccumulator {
    pub leaves: Vec<[u8; 32]>,
}

impl MmrAccumulator {
    pub fn new() -> Self {
        Self { leaves: Vec::new() }
    }

    pub fn append(&mut self, leaf_hash: [u8; 32]) -> usize {
        self.leaves.push(leaf_hash);
        self.leaves.len() - 1
    }

    pub fn len(&self) -> usize {
        self.leaves.len()
    }

    pub fn is_empty(&self) -> bool {
        self.leaves.is_empty()
    }

    fn get_peak_slices(&self) -> Vec<(usize, usize)> {
        let n = self.leaves.len();
        let mut slices = Vec::new();
        let mut start = 0;
        let mut bit = 1usize << 62;
        while bit > 0 {
            if (n & bit) != 0 {
                let size = bit;
                slices.push((start, start + size));
                start += size;
            }
            bit >>= 1;
        }
        slices
    }

    fn build_subtree_root_and_proof(
        leaf_slice: &[[u8; 32]],
        target_idx: Option<usize>,
    ) -> ([u8; 32], Vec<MmrProofStep>) {
        let mut layer: Vec<[u8; 32]> = leaf_slice.to_vec();
        let mut proof = Vec::new();
        let mut idx = target_idx;

        while layer.len() > 1 {
            if let Some(i) = idx {
                let is_right = i % 2 == 1;
                let sibling_idx = if is_right { i - 1 } else { i + 1 };
                proof.push(MmrProofStep {
                    sibling: layer[sibling_idx],
                    is_left: is_right,
                });
                idx = Some(i / 2);
            }

            let mut next_layer = Vec::with_capacity(layer.len() / 2);
            for chunk in layer.chunks_exact(2) {
                let mut hasher = Sha3_256::new();
                hasher.update([DOMAIN_MMR_NODE]);
                hasher.update(chunk[0]);
                hasher.update(chunk[1]);
                let result = hasher.finalize();
                let mut node = [0u8; 32];
                node.copy_from_slice(&result);
                next_layer.push(node);
            }
            layer = next_layer;
        }

        (layer[0], proof)
    }

    pub fn get_peaks(&self) -> Vec<[u8; 32]> {
        let slices = self.get_peak_slices();
        let mut peaks = Vec::with_capacity(slices.len());
        for (start, end) in slices {
            let (peak_root, _) = Self::build_subtree_root_and_proof(&self.leaves[start..end], None);
            peaks.push(peak_root);
        }
        peaks
    }

    pub fn get_root(&self) -> [u8; 32] {
        if self.leaves.is_empty() {
            return [0u8; 32];
        }
        let peaks = self.get_peaks();
        let mut hasher = Sha3_256::new();
        hasher.update([DOMAIN_MMR_PEAKS]);
        for p in &peaks {
            hasher.update(p);
        }
        hasher.update((self.leaves.len() as u64).to_le_bytes());
        let res = hasher.finalize();
        let mut root = [0u8; 32];
        root.copy_from_slice(&res);
        root
    }

    pub fn generate_proof(&self, target_index: usize) -> Result<MmrInclusionProof, &'static str> {
        if target_index >= self.leaves.len() {
            return Err("target_index fuera de rango");
        }
        let slices = self.get_peak_slices();
        let peaks = self.get_peaks();

        let mut peak_idx = 0;
        let mut rel_idx = 0;
        let mut found_start = 0;
        let mut found_end = 0;

        for (i, &(start, end)) in slices.iter().enumerate() {
            if target_index >= start && target_index < end {
                peak_idx = i;
                rel_idx = target_index - start;
                found_start = start;
                found_end = end;
                break;
            }
        }

        let (_, inner_proof) =
            Self::build_subtree_root_and_proof(&self.leaves[found_start..found_end], Some(rel_idx));

        let mut other_peaks = Vec::with_capacity(peaks.len().saturating_sub(1));
        for (j, p) in peaks.into_iter().enumerate() {
            if j != peak_idx {
                other_peaks.push(p);
            }
        }

        Ok(MmrInclusionProof {
            leaf_index: target_index,
            total_leaves: self.leaves.len(),
            peak_index: peak_idx,
            inner_proof,
            other_peaks,
            mmr_root: self.get_root(),
        })
    }

    pub fn verify_proof(
        leaf_hash: [u8; 32],
        proof: &MmrInclusionProof,
        expected_root: [u8; 32],
    ) -> bool {
        let mut curr = leaf_hash;
        for step in &proof.inner_proof {
            let mut hasher = Sha3_256::new();
            hasher.update([DOMAIN_MMR_NODE]);
            if step.is_left {
                hasher.update(step.sibling);
                hasher.update(curr);
            } else {
                hasher.update(curr);
                hasher.update(step.sibling);
            }
            let res = hasher.finalize();
            curr.copy_from_slice(&res);
        }

        let recomputed_peak = curr;
        let mut all_peaks = Vec::with_capacity(proof.other_peaks.len() + 1);
        all_peaks.extend_from_slice(&proof.other_peaks[..proof.peak_index]);
        all_peaks.push(recomputed_peak);
        all_peaks.extend_from_slice(&proof.other_peaks[proof.peak_index..]);

        let mut hasher = Sha3_256::new();
        hasher.update([DOMAIN_MMR_PEAKS]);
        for p in &all_peaks {
            hasher.update(p);
        }
        hasher.update((proof.total_leaves as u64).to_le_bytes());
        let res = hasher.finalize();
        let mut computed_root = [0u8; 32];
        computed_root.copy_from_slice(&res);

        computed_root == expected_root
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn dummy_hash(i: u64) -> [u8; 32] {
        let mut hasher = Sha3_256::new();
        hasher.update(i.to_le_bytes());
        let res = hasher.finalize();
        let mut h = [0u8; 32];
        h.copy_from_slice(&res);
        h
    }

    #[test]
    fn test_rust_mmr_arbitrary_sizes() {
        for &size in &[1, 2, 3, 5, 8, 13, 21, 60] {
            let mut mmr = MmrAccumulator::new();
            let mut leaves = Vec::new();
            for i in 0..size {
                let h = dummy_hash(i);
                mmr.append(h);
                leaves.push(h);
            }
            let root = mmr.get_root();
            for (i, &h) in leaves.iter().enumerate() {
                let proof = mmr.generate_proof(i).expect("proof generation");
                assert!(MmrAccumulator::verify_proof(h, &proof, root));
            }
        }
    }
}
