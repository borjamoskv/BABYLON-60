// ============================================================================
// BABYLON-60 :: BLOQUE IX — TERMODINÁMICA DE LA INFORMACIÓN Y COTA DE LANDAUER
// ============================================================================
//! Implementación formal de las Iteraciones 81–90 de la Matriz Maestra (C5-REAL):
//! - [Iter 81] Medición de la Cota de Landauer en Silicio para Proyección de Leray.
//! - [Iter 82] Entropía de Kolmogorov-Sinai (h_KS) del Campo de Deformación.
//! - [Iter 83] Reducción Dimensional Geodésica sobre el Tensor de Fisher-Rao (Chentsov).
//! - [Iter 84] Monitoreo de Dimensionalidad Efectiva mediante RankMe.
//! - [Iter 85] Invariante de Transición de Aeón Conforme (INV_C5_AEON).
//! - [Iter 86] Balance Exergético de Watzlawick (Cambio 1 vs Cambio 2).
//! - [Iter 87] Cota Universal de Bekenstein sobre la Densidad de Vorticidad.
//! - [Iter 88] Manta de Markov Somática y Prevención de Burnout.
//! - [Iter 89] Purgado de Anergía Residual Sub-Kolmogorov.
//! - [Iter 90] Teorema de Compensación Calor-Información (Clausura Termodinámica).

use core::f64::consts::PI;

/// Constante de Boltzmann en Joules/Kelvin
pub const BOLTZMANN_K_B: f64 = 1.380649e-23;

/// Constante reducida de Planck en Joules*segundo
pub const H_BAR: f64 = 1.054571817e-34;

/// Velocidad de la luz en m/s
pub const SPEED_OF_LIGHT: f64 = 299792458.0;

/// Temperatura estándar de referencia del silicio (300 K)
pub const STANDARD_TEMP_K: f64 = 300.0;

/// Cota de Landauer elemental por bit a 300K: k_B * T * ln(2) ~ 2.87e-21 J
pub const LANDAUER_JOULES_PER_BIT_300K: f64 = 2.87049e-21;

// ---------------------------------------------------------------------------
// [Iter 81] Cota de Landauer para la Proyección de Leray-Helmholtz
// ---------------------------------------------------------------------------
/// Calcula el suelo teórico de disipación de Landauer al proyectar el campo
/// de velocidades sobre el subespacio solenoidal en una malla N x N x N.
/// La proyección borra N^3 grados de libertad longitudinales (compresibles),
/// cada uno de 64 bits (IEEE 754 f64).
#[inline]
pub fn leray_projection_landauer_floor_joules(mesh_n: usize, temperature_k: f64) -> f64 {
    let erased_modes = (mesh_n * mesh_n * mesh_n) as f64;
    let bits_erased = erased_modes * 64.0;
    let kb_t_ln2 = BOLTZMANN_K_B * temperature_k * core::f64::consts::LN_2;
    bits_erased * kb_t_ln2
}

// ---------------------------------------------------------------------------
// [Iter 82] Entropía de Kolmogorov-Sinai (h_KS)
// ---------------------------------------------------------------------------
/// Calcula la tasa de producción de información estocástica (caos determinista)
/// sumando los autovalores positivos del tensor de deformación local:
/// h_KS = \sum \max(0, \lambda_1(x)).
#[inline]
pub fn compute_kolmogorov_sinai_entropy(strain_max_eigenvalues: &[f64]) -> f64 {
    if strain_max_eigenvalues.is_empty() {
        return 0.0;
    }
    let mut sum_positive_lyapunov = 0.0;
    for &lambda in strain_max_eigenvalues {
        if lambda > 0.0 {
            sum_positive_lyapunov += lambda;
        }
    }
    sum_positive_lyapunov / (strain_max_eigenvalues.len() as f64)
}

// ---------------------------------------------------------------------------
// [Iter 83] Distancia Geodésica de Fisher-Rao (Geometría de Chentsov)
// ---------------------------------------------------------------------------
/// Calcula la distancia termodinámica pura entre dos estados del fluido
/// representados como distribuciones de densidad espectral o enstrofía.
/// Conforme al Teorema de Unicidad de Chentsov, es la única métrica invariante
/// bajo morfismos estocásticos de Markov: d_F(p, q) = 2 * arccos(\sum \sqrt{p_i * q_i}).
#[inline]
pub fn fisher_rao_geodesic_distance(p: &[f64], q: &[f64]) -> f64 {
    assert_eq!(p.len(), q.len(), "Dimensiones incompatibles para distancia de Fisher-Rao");
    if p.is_empty() {
        return 0.0;
    }

    let mut bhattacharyya_coeff = 0.0;
    for (&p_i, &q_i) in p.iter().zip(q.iter()) {
        if p_i > 0.0 && q_i > 0.0 {
            bhattacharyya_coeff += (p_i * q_i).sqrt();
        }
    }

    // Clamp numérico para evitar NaNs en arccos si bhattacharyya > 1.0 por error flotante
    let clamped_bc = bhattacharyya_coeff.clamp(0.0, 1.0);
    2.0 * clamped_bc.acos()
}

// ---------------------------------------------------------------------------
// [Iter 84] Monitoreo de Dimensionalidad Efectiva mediante RankMe
// ---------------------------------------------------------------------------
/// Calcula la dimensión intrínseca efectiva del atractor del fluido:
/// RankMe(X) = \exp(H(p)), donde p_k = \sigma_k / \sum \sigma_i.
/// Si RankMe <= 1.5, el atractor ha colapsado a cuasi-1D/2D (depleción de no-linealidad).
#[inline]
pub fn compute_rankme_dimension(singular_values: &[f64]) -> f64 {
    let sum_sigma: f64 = singular_values.iter().filter(|&&s| s > 0.0).sum();
    if sum_sigma <= 0.0 {
        return 0.0;
    }

    let mut entropy = 0.0;
    for &s in singular_values {
        if s > 0.0 {
            let p_k = s / sum_sigma;
            entropy -= p_k * p_k.ln();
        }
    }

    entropy.exp()
}

// ---------------------------------------------------------------------------
// [Iter 85] Invariante de Transición de Aeón Conforme (INV_C5_AEON)
// ---------------------------------------------------------------------------
/// Determina si el sistema debe disparar la transición conforme de Aeón:
/// Ocurre si la dimensión efectiva colapsa (RankMe <= 1.5) o la entropía acumulada
/// satura el límite de disipación de la memoria caliente.
#[inline]
pub fn check_aeon_conformal_transition(rankme: f64, entropy: f64, max_entropy: f64) -> bool {
    rankme <= 1.5 || entropy >= max_entropy
}

// ---------------------------------------------------------------------------
// [Iter 86] Balance Exergético de Watzlawick (Cambio 1 vs Cambio 2)
// ---------------------------------------------------------------------------
/// Acción dictada por el balance exergético de Watzlawick (Aforismo 3).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum WatzlawickAction {
    /// Continuar refinamiento ordinario (Cambio 1)
    ContinueChange1,
    /// Ejecutar bifurcación topológica o salto de atractor (Cambio 2)
    BifurcateChange2,
}

/// Evalúa si el coste energético de continuar el refinamiento ordinario supera
/// la ganancia de información topológica (trampa de anergía de Watzlawick).
#[inline]
pub fn evaluate_watzlawick_balance(
    delta_info_bits: f64,
    dissipated_joules: f64,
    min_exergy_efficiency: f64,
) -> WatzlawickAction {
    if dissipated_joules <= 0.0 {
        return WatzlawickAction::ContinueChange1;
    }
    let efficiency = (delta_info_bits * LANDAUER_JOULES_PER_BIT_300K) / dissipated_joules;
    if efficiency < min_exergy_efficiency {
        WatzlawickAction::BifurcateChange2
    } else {
        WatzlawickAction::ContinueChange1
    }
}

// ---------------------------------------------------------------------------
// [Iter 87] Cota Universal de Bekenstein sobre la Densidad de Vorticidad
// ---------------------------------------------------------------------------
/// Calcula la cota superior absoluta de información que puede residir
/// en una esfera de radio R con energía E: I <= (2 * \pi * R * E) / (\hbar * c * \ln 2).
/// Garantiza que la vorticidad no puede diverger a infinito en volumen cero.
#[inline]
pub fn bekenstein_vortex_information_bound(radius_meters: f64, mass_energy_joules: f64) -> f64 {
    let numerator = 2.0 * PI * radius_meters * mass_energy_joules;
    let denominator = H_BAR * SPEED_OF_LIGHT * core::f64::consts::LN_2;
    numerator / denominator
}

// ---------------------------------------------------------------------------
// [Iter 88] Manta de Markov Somática y Prevención de Burnout
// ---------------------------------------------------------------------------
/// Estado homeostático de la manta de Markov somática.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SomaticStatus {
    /// Régimen térmico óptimo
    OptimalThroughput,
    /// Se requiere dilatar ciclos para disipación térmica
    CoolingThrottleRequired,
    /// Apoptosis térmica para prevenir degradación física
    ThermalApoptosis,
}

/// Telemetría homeostática: protege el nodo de silicio y la atención biológica.
#[inline]
pub fn somatic_markov_blanket_telemetry(
    package_temp_celsius: f64,
    uninterrupted_duty_cycles: u64,
) -> SomaticStatus {
    if package_temp_celsius >= 100.0 || uninterrupted_duty_cycles >= 100_000_000 {
        SomaticStatus::ThermalApoptosis
    } else if package_temp_celsius >= 85.0 || uninterrupted_duty_cycles >= 50_000_000 {
        SomaticStatus::CoolingThrottleRequired
    } else {
        SomaticStatus::OptimalThroughput
    }
}

// ---------------------------------------------------------------------------
// [Iter 89] Purgado de Anergía Residual Sub-Kolmogorov
// ---------------------------------------------------------------------------
/// Aniquila los modos de alta frecuencia k > k_cutoff que residen más allá
/// de la escala de disipación viscosa de Kolmogorov, eliminando anergía estocástica.
#[inline]
pub fn purge_sub_kolmogorov_anergy(amplitudes: &mut [f64], k_cutoff: usize) -> usize {
    let mut purged_modes = 0;
    for (k, amp) in amplitudes.iter_mut().enumerate() {
        if k > k_cutoff && *amp != 0.0 {
            *amp = 0.0;
            purged_modes += 1;
        }
    }
    purged_modes
}

// ---------------------------------------------------------------------------
// [Iter 90] Teorema de Compensación de Calor-Información (Clausura Termodinámica)
// ---------------------------------------------------------------------------
/// Verifica formalmente que la disipación térmica acumulada satisface
/// la Segunda Ley Generalizada de la Termodinámica: Q >= T * \Delta S_info.
#[inline]
pub fn verify_heat_information_compensation(
    dissipated_joules: f64,
    entropy_delta_shannon_bits: f64,
    temperature_k: f64,
) -> bool {
    let min_heat = entropy_delta_shannon_bits * BOLTZMANN_K_B * temperature_k * core::f64::consts::LN_2;
    dissipated_joules >= min_heat
}

// ---------------------------------------------------------------------------
// TESTS UNITARIOS DEL BLOQUE IX
// ---------------------------------------------------------------------------
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_leray_projection_landauer_floor() {
        // Malla 8x8x8: 512 celdas * 64 bits = 32.768 bits borrados
        let q = leray_projection_landauer_floor_joules(8, 300.0);
        assert!(q > 9.0e-17, "La cota de Landauer debe ser positiva y proporcional");
        assert!(q < 1.0e-15);
    }

    #[test]
    fn test_kolmogorov_sinai_entropy() {
        let lambdas = vec![2.5, -1.0, -1.5, 3.0, 0.0, -0.5];
        let h_ks = compute_kolmogorov_sinai_entropy(&lambdas);
        // Positivos: 2.5 + 3.0 = 5.5 / 6.0 = 0.91666...
        assert!((h_ks - 5.5 / 6.0).abs() < 1e-12);
    }

    #[test]
    fn test_fisher_rao_geodesic_distance() {
        // Distribuciones idénticas -> d_F = 0
        let p = vec![0.5, 0.5];
        let q = vec![0.5, 0.5];
        assert_eq!(fisher_rao_geodesic_distance(&p, &q), 0.0);

        // Distribuciones ortogonales (soporte disjunto) -> d_F = 2 * arccos(0) = \pi
        let p_orth = vec![1.0, 0.0];
        let q_orth = vec![0.0, 1.0];
        let d_orth = fisher_rao_geodesic_distance(&p_orth, &q_orth);
        assert!((d_orth - PI).abs() < 1e-12);
    }

    #[test]
    fn test_rankme_effective_dimension() {
        // Espectro uniforme de 4 valores singulares -> RankMe = 4.0
        let uniform = vec![1.0, 1.0, 1.0, 1.0];
        let r_unif = compute_rankme_dimension(&uniform);
        assert!((r_unif - 4.0).abs() < 1e-12);

        // Espectro con colapso a un único autovalor -> RankMe = 1.0 <= 1.5
        let collapsed = vec![100.0, 0.0, 0.0, 0.0];
        let r_col = compute_rankme_dimension(&collapsed);
        assert!((r_col - 1.0).abs() < 1e-12);
        assert!(check_aeon_conformal_transition(r_col, 10.0, 100.0));
    }

    #[test]
    fn test_watzlawick_exergy_balance() {
        // Alta eficiencia (1e9 bits = 2.87e-12 J vs 1e-12 J disipados -> eficiencia ~ 2.87 > 0.01) -> continuar Cambio 1
        let act1 = evaluate_watzlawick_balance(1_000_000_000.0, 1e-12, 0.01);
        assert_eq!(act1, WatzlawickAction::ContinueChange1);

        // Pésima eficiencia (anergía masiva) -> Cambio 2
        let act2 = evaluate_watzlawick_balance(1.0, 10.0, 0.01);
        assert_eq!(act2, WatzlawickAction::BifurcateChange2);
    }

    #[test]
    fn test_bekenstein_bound() {
        let r = 0.01; // 1 cm
        let e = 1.0;  // 1 Joule
        let max_bits = bekenstein_vortex_information_bound(r, e);
        assert!(max_bits > 1e24, "La cota de Bekenstein debe ser astronómicamente amplia en escala macro (~2.87e24 bits)");
    }

    #[test]
    fn test_somatic_markov_telemetry() {
        assert_eq!(somatic_markov_blanket_telemetry(45.0, 1000), SomaticStatus::OptimalThroughput);
        assert_eq!(somatic_markov_blanket_telemetry(88.0, 1000), SomaticStatus::CoolingThrottleRequired);
        assert_eq!(somatic_markov_blanket_telemetry(102.0, 1000), SomaticStatus::ThermalApoptosis);
    }

    #[test]
    fn test_kolmogorov_anergy_purge() {
        let mut modes = vec![1.0, 0.8, 0.5, 0.2, 0.1, 0.05];
        let purged = purge_sub_kolmogorov_anergy(&mut modes, 3);
        assert_eq!(purged, 2);
        assert_eq!(modes[4], 0.0);
        assert_eq!(modes[5], 0.0);
        assert_eq!(modes[3], 0.2);
    }

    #[test]
    fn test_heat_information_compensation() {
        let bits = 1000.0;
        let min_heat = bits * LANDAUER_JOULES_PER_BIT_300K;
        assert!(verify_heat_information_compensation(min_heat * 1.1, bits, 300.0));
        assert!(!verify_heat_information_compensation(min_heat * 0.9, bits, 300.0));
    }
}
