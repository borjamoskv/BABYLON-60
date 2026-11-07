//! Canonical mathematical scoring functions for CORTEX Archaeology.
//! Law O3 & Blueprint §7: S, R_pres, C_rec, T_tens.

/// Computes the pure Surprise metric S = (1 - exp(-d / tau)) * R_pres * (1 - C_rec).
/// Returns an error if any parameter is out of bounds or NaN.
pub fn compute_surprise(d_days: f32, tau: f32, r_pres: f32, c_rec: f32) -> Result<f32, &'static str> {
    if d_days < 0.0 || tau <= 0.0 {
        return Err("d_days >= 0.0 and tau > 0.0 required");
    }
    if !(0.0..=1.0).contains(&r_pres) || !(0.0..=1.0).contains(&c_rec) {
        return Err("r_pres and c_rec must lie within [0.0, 1.0]");
    }
    if d_days.is_nan() || tau.is_nan() || r_pres.is_nan() || c_rec.is_nan() {
        return Err("NaN values are strictly rejected");
    }

    let temporal_tension = 1.0 - (-d_days / tau).exp();
    let s = temporal_tension * r_pres * (1.0 - c_rec);
    Ok(s.clamp(0.0, 1.0))
}

/// Packs up to 32 bytes/tokens into a single `u64` word using 2 bits per symbol
/// (`(b & 0b11) as u64` shifted by `2 * i` bit positions, for `i < 32`).
pub fn pack_2bit_shingle(bytes: &[u8]) -> u64 {
    let mut packed = 0u64;
    for (i, &b) in bytes.iter().take(32).enumerate() {
        packed |= ((b & 0b11) as u64) << (2 * i);
    }
    packed
}

/// Computes in branchless $O(1)$ time the number of 2-bit symbol positions (out of 32)
/// that differ between `sig_a` and `sig_b`.
pub fn hamming_distance_2bit(sig_a: u64, sig_b: u64) -> u32 {
    let diff = sig_a ^ sig_b;
    let pair_diff = (diff | (diff >> 1)) & 0x5555_5555_5555_5555u64;
    pair_diff.count_ones()
}

/// Computes the exact unit-cost edit distance (insertions, deletions, substitutions of weight 1)
/// between two episodic event sequences `trace_a` and `trace_b` operating over wavefronts
/// in bounded linear space $O(s)$ (retaining only the current and next wavefronts of size
/// `2 * max_score + 1` instead of a quadratic $O(N \times M)$ matrix).
///
/// Extends each diagonal $k = i - j$ along exact matches (longest common prefix / snake).
/// Returns `Some(s)` if the main target diagonal `k = n as isize - m as isize` reaches
/// `i == n && j == m` within `s <= max_score` steps, or `None` if the distance exceeds `max_score`.
pub fn biwfa_trace_distance(trace_a: &[u32], trace_b: &[u32], max_score: usize) -> Option<usize> {
    let n = trace_a.len();
    let m = trace_b.len();
    let target_k = n as isize - m as isize;

    if target_k.unsigned_abs() > max_score {
        return None;
    }

    let wf_len = 2 * max_score + 1;
    let offset = max_score as isize;
    let mut curr_wf = vec![-1isize; wf_len];
    let mut next_wf = vec![-1isize; wf_len];

    // Score s = 0: extend initial snake along diagonal k = 0
    let mut i0 = 0usize;
    while i0 < n && i0 < m && trace_a[i0] == trace_b[i0] {
        i0 += 1;
    }
    if target_k == 0 && i0 == n && i0 == m {
        return Some(0);
    }
    curr_wf[offset as usize] = i0 as isize;

    for s in 1..=max_score {
        next_wf.fill(-1);
        let s_isize = s as isize;

        for k in -s_isize..=s_isize {
            let idx = (k + offset) as usize;
            let mut best_i = curr_wf[idx];

            // Insertion into trace_a / advance in trace_b from diagonal k + 1: (i, j - 1) -> (i, j)
            if k < offset {
                let prev_i = curr_wf[(k + 1 + offset) as usize];
                if prev_i >= 0 {
                    let cand_i = prev_i;
                    let cand_j = cand_i - k;
                    if cand_i <= n as isize && cand_j >= 0 && cand_j <= m as isize {
                        best_i = best_i.max(cand_i);
                    }
                }
            }

            // Deletion from trace_a / advance in trace_a from diagonal k - 1: (i - 1, j) -> (i, j)
            if k > -offset {
                let prev_i = curr_wf[(k - 1 + offset) as usize];
                if prev_i >= 0 {
                    let cand_i = prev_i + 1;
                    let cand_j = cand_i - k;
                    if cand_i <= n as isize && cand_j >= 0 && cand_j <= m as isize {
                        best_i = best_i.max(cand_i);
                    }
                }
            }

            // Substitution from diagonal k: (i - 1, j - 1) -> (i, j)
            let prev_i = curr_wf[idx];
            if prev_i >= 0 {
                let cand_i = prev_i + 1;
                let cand_j = cand_i - k;
                if cand_i <= n as isize && cand_j >= 0 && cand_j <= m as isize {
                    best_i = best_i.max(cand_i);
                }
            }

            if best_i >= 0 {
                let mut i = best_i as usize;
                let mut j = (best_i - k) as usize;
                while i < n && j < m && trace_a[i] == trace_b[j] {
                    i += 1;
                    j += 1;
                }
                if k == target_k && i == n && j == m {
                    return Some(s);
                }
                next_wf[idx] = i as isize;
            }
        }

        std::mem::swap(&mut curr_wf, &mut next_wf);
    }

    None
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_surprise_bounds_and_saturation() {
        // d = 0 => S = 0
        assert_eq!(compute_surprise(0.0, 180.0, 1.0, 0.0).unwrap(), 0.0);
        // r_pres = 0 => S = 0
        assert_eq!(compute_surprise(100.0, 180.0, 0.0, 0.0).unwrap(), 0.0);
        // c_rec = 1 => S = 0
        assert_eq!(compute_surprise(100.0, 180.0, 1.0, 1.0).unwrap(), 0.0);

        // tau = 180, d = 180 => 1 - exp(-1) ~= 0.63212056
        let s_180 = compute_surprise(180.0, 180.0, 1.0, 0.0).unwrap();
        assert!((s_180 - 0.63212056).abs() < 1e-4);

        // Boundary rejects
        assert!(compute_surprise(-1.0, 180.0, 1.0, 0.0).is_err());
        assert!(compute_surprise(10.0, 0.0, 1.0, 0.0).is_err());
        assert!(compute_surprise(10.0, 180.0, 1.5, 0.0).is_err());
    }

    #[test]
    fn test_2bit_shingle_packing_and_branchless_hamming() {
        let base_seq: [u8; 32] = [
            0, 1, 2, 3, 0, 1, 2, 3, 1, 1, 2, 2, 3, 3, 0, 0,
            3, 2, 1, 0, 3, 2, 1, 0, 2, 3, 0, 1, 2, 3, 0, 1,
        ];
        let sig_a = pack_2bit_shingle(&base_seq);
        let sig_same = pack_2bit_shingle(&base_seq);
        assert_eq!(hamming_distance_2bit(sig_a, sig_same), 0);

        // 1-symbol mutation (both bits flipped in symbol 0: 0b00 -> 0b11)
        let mut seq_mut1 = base_seq;
        seq_mut1[0] = 3;
        let sig_mut1 = pack_2bit_shingle(&seq_mut1);
        assert_eq!(hamming_distance_2bit(sig_a, sig_mut1), 1);

        // 2-symbol mutation (symbol 0: 0b00 -> 0b11, symbol 15: 0b00 -> 0b01)
        let mut seq_mut2 = seq_mut1;
        seq_mut2[15] = 1;
        let sig_mut2 = pack_2bit_shingle(&seq_mut2);
        assert_eq!(hamming_distance_2bit(sig_a, sig_mut2), 2);

        // All 32 symbols mutated
        let mut seq_mut32 = base_seq;
        for b in &mut seq_mut32 {
            *b = (*b + 1) & 0b11;
        }
        let sig_mut32 = pack_2bit_shingle(&seq_mut32);
        assert_eq!(hamming_distance_2bit(sig_a, sig_mut32), 32);
    }

    #[test]
    fn test_biwfa_trace_distance_linear_space() {
        let trace_a = [101u32, 102, 103, 104, 105, 106];
        // Distance 0 on identical traces
        assert_eq!(biwfa_trace_distance(&trace_a, &trace_a, 4), Some(0));
        assert_eq!(biwfa_trace_distance(&[], &[], 0), Some(0));

        // 1 insertion
        let trace_ins = [101u32, 102, 999, 103, 104, 105, 106];
        assert_eq!(biwfa_trace_distance(&trace_a, &trace_ins, 4), Some(1));

        // 1 deletion
        let trace_del = [101u32, 102, 104, 105, 106];
        assert_eq!(biwfa_trace_distance(&trace_a, &trace_del, 4), Some(1));

        // Combined: 1 substitution + 1 deletion + 1 insertion = distance 3
        let trace_mixed = [101u32, 888, 103, 105, 106, 777];
        assert_eq!(biwfa_trace_distance(&trace_a, &trace_mixed, 5), Some(3));
        assert_eq!(biwfa_trace_distance(&trace_a, &trace_mixed, 3), Some(3));

        // Exceeds max_score -> None
        assert_eq!(biwfa_trace_distance(&trace_a, &trace_mixed, 2), None);
    }
}
