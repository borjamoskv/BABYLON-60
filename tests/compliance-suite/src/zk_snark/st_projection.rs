// C5-REAL EXERGY CERTIFIED
//! Standard part map projection st(x) dissipating infinitesimal noise \epsilon \in \mu(0).
//!
//! In Robinson's Nonstandard Analysis, standard part projection maps hyperreal
//! quantities x = x_0 + \epsilon to their standard part x_0 \in \mathbb{R},
//! dissipating nonstandard infinitesimal noise \epsilon \in \mu(0).

use ark_bn254::Fr;
use ark_ff::PrimeField;

/// Dissipate infinitesimal noise from a floating-point scalar value.
/// If |x| <= eps, returns 0.0; otherwise returns x.
#[inline]
pub fn dissipate_noise_scalar(x: f32, eps: f32) -> f32 {
    if x.abs() <= eps {
        0.0
    } else {
        x
    }
}

/// Apply standard part projection across a float vector, zeroing out infinitesimal noise.
/// Writes standard parts into `output` buffer and returns the squared Euclidean norm of the standard part.
pub fn dissipate_noise_vector(input: &[f32], eps: f32, output: &mut [f32]) -> f32 {
    assert_eq!(input.len(), output.len(), "Input and output slice lengths must match");

    let mut sum_sq = 0.0f32;
    for (i, &val) in input.iter().enumerate() {
        let st_val = dissipate_noise_scalar(val, eps);
        output[i] = st_val;
        sum_sq += st_val * st_val;
    }
    sum_sq
}

/// Determines if a scalar float lies within the infinitesimal halo \mu(0) given threshold \epsilon.
#[inline]
pub fn is_infinitesimal(x: f32, eps: f32) -> bool {
    x.abs() <= eps
}

/// Project a BN254 scalar field element to standard part by clearing noise bits
/// below specified bit threshold (infinitesimal field dissipation).
pub fn st_project_bn254(val: &Fr, noise_bits: u32) -> Fr {
    if noise_bits == 0 {
        return *val;
    }
    let mut bigint = val.into_bigint();
    let limbs = bigint.as_mut();

    let mut bits_cleared = 0;
    for limb in limbs.iter_mut() {
        if bits_cleared >= noise_bits {
            break;
        }
        let remaining = noise_bits - bits_cleared;
        if remaining >= 64 {
            *limb = 0;
            bits_cleared += 64;
        } else {
            let mask = !((1u64 << remaining) - 1);
            *limb &= mask;
            bits_cleared += remaining;
        }
    }
    Fr::from_bigint(bigint).unwrap_or(*val)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dissipate_noise_scalar() {
        let eps = 1e-6f32;
        assert_eq!(dissipate_noise_scalar(1e-7f32, eps), 0.0);
        assert_eq!(dissipate_noise_scalar(-1e-8f32, eps), 0.0);
        assert_eq!(dissipate_noise_scalar(0.005f32, eps), 0.005f32);
    }

    #[test]
    fn test_dissipate_noise_vector() {
        let input = vec![1.0f32, 1e-7f32, -0.5f32, 2e-8f32];
        let mut output = vec![0.0f32; 4];
        let norm_sq = dissipate_noise_vector(&input, 1e-6f32, &mut output);

        assert_eq!(output, vec![1.0f32, 0.0f32, -0.5f32, 0.0f32]);
        assert!((norm_sq - 1.25f32).abs() < 1e-6);
    }

    #[test]
    fn test_st_project_bn254() {
        let val = Fr::from(1000000u64);
        let projected = st_project_bn254(&val, 8);
        assert_ne!(val, projected);

        let exact_val = Fr::from(256u64);
        let projected_exact = st_project_bn254(&exact_val, 8);
        assert_eq!(projected_exact, Fr::from(256u64));
    }
}
