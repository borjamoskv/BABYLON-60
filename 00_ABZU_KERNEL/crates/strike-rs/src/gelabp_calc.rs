// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
/// Parámetros termodinámicos GELABP
#[derive(Debug, Clone)]
pub struct ExergyParams {
    pub g: f64,
    pub l: f64,
    pub a: f64,
    pub b: f64,
    pub p: f64,
    pub e_base: f64,
}

/// Evaluador GELABP — Implementa AX-EX-1 hasta AX-EX-7
pub fn compute_score(
    params: &ExergyParams,
    wall_ms: f64,
    node_sum_ms: f64,
    memory_capacity: usize,
    memory_entries: usize,
    has_high_latency_nodes: bool,
    has_placeholders: bool,
) -> f64 {
    // AX-EX-2: Cota inferior de entropía
    let mut e = wall_ms / 100.0;
    if e < params.e_base {
        e = params.e_base;
    }

    // AX-EX-3: Penalización Bottleneck
    let b = if has_high_latency_nodes {
        0.5
    } else {
        params.b
    };

    // AX-EX-4: Penalización de memoria
    let m_p = if memory_entries as f64 > 0.8 * memory_capacity as f64 {
        0.8
    } else {
        1.0
    };
    let effective_l = params.l * m_p;

    // AX-EX-7: Penalización PostHoc (Anti Green Theater)
    let p = if has_placeholders {
        0.2
    } else {
        params.p
    };

    // Speedup
    let speedup = if wall_ms > 0.0 {
        node_sum_ms / wall_ms
    } else {
        1.0
    };

    // AX-EX-1: Fórmula Canónica
    let raw = (params.g * effective_l * params.a * b * p) / e;
    let score = raw * speedup;

    // AX-EX-6: Cota Superior Cerrada
    score.clamp(0.0, 1000.0)
}

/// Escala de punto fijo F60 para determinismo bit-perfect en Ring-0 (1.0 = 1_000_000_u64)
pub const F60_SCALE: u64 = 1_000_000;

/// Parámetros termodinámicos GELABP en Punto Fijo F60 (sin punto flotante)
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ExergyParamsF60 {
    pub g: u64,
    pub l: u64,
    pub a: u64,
    pub b: u64,
    pub p: u64,
    pub e_base: u64,
}

impl From<&ExergyParams> for ExergyParamsF60 {
    fn from(p: &ExergyParams) -> Self {
        Self {
            g: (p.g * F60_SCALE as f64).round() as u64,
            l: (p.l * F60_SCALE as f64).round() as u64,
            a: (p.a * F60_SCALE as f64).round() as u64,
            b: (p.b * F60_SCALE as f64).round() as u64,
            p: (p.p * F60_SCALE as f64).round() as u64,
            e_base: (p.e_base * F60_SCALE as f64).round() as u64,
        }
    }
}

/// Evaluador GELABP determinista en Ring-0 (Punto Fijo F60, AX-EX-1 a AX-EX-7 sin IEEE 754)
pub fn compute_score_f60(
    params: &ExergyParamsF60,
    wall_ms_scaled: u64,
    node_sum_ms_scaled: u64,
    memory_capacity: usize,
    memory_entries: usize,
    has_high_latency_nodes: bool,
    has_placeholders: bool,
) -> u64 {
    // AX-EX-2: Cota inferior de entropía (e = max(wall_ms / 100, e_base))
    let mut e = wall_ms_scaled / 100;
    if e < params.e_base {
        e = params.e_base;
    }
    if e == 0 {
        e = 1;
    }

    // AX-EX-3: Penalización Bottleneck
    let b = if has_high_latency_nodes {
        F60_SCALE / 2
    } else {
        params.b
    };

    // AX-EX-4: Penalización de memoria (>80% capacidad -> factor 0.8)
    let effective_l = if (memory_entries as u64 * 10) > (memory_capacity as u64 * 8) {
        (params.l * 8) / 10
    } else {
        params.l
    };

    // AX-EX-7: Penalización PostHoc (Anti Green Theater -> factor 0.2)
    let p = if has_placeholders {
        F60_SCALE / 5
    } else {
        params.p
    };

    // Speedup en escala F60 (node_sum / wall_ms)
    let speedup = if wall_ms_scaled > 0 {
        (node_sum_ms_scaled as u128 * F60_SCALE as u128) / wall_ms_scaled as u128
    } else {
        F60_SCALE as u128
    };

    // AX-EX-1: Fórmula Canónica: raw = (g * l * a * b * p) / e
    let numer = (params.g as u128)
        * (effective_l as u128)
        * (params.a as u128)
        * (b as u128)
        * (p as u128);
    let scale_4 = (F60_SCALE as u128).pow(4);
    let normalized_numer = numer / scale_4;

    let raw = (normalized_numer * F60_SCALE as u128) / (e as u128);
    let score = (raw * speedup) / (F60_SCALE as u128);

    // AX-EX-6: Cota Superior Cerrada [0, 1000 * F60_SCALE]
    let max_score = 1000 * F60_SCALE as u128;
    score.min(max_score) as u64
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ax_ex_1_upper_bound() {
        let p = ExergyParams { g: 50.0, l: 50.0, a: 1.0, b: 1.0, p: 1.0, e_base: 0.01 };
        let score = compute_score(&p, 10.0, 100.0, 100, 10, false, false);
        assert!(score <= 1000.0);
    }

    #[test]
    fn test_ax_ex_7_green_theater() {
        let p = ExergyParams { g: 12.0, l: 12.0, a: 1.0, b: 1.0, p: 1.0, e_base: 0.04 };
        let score_clean = compute_score(&p, 10.0, 10.0, 100, 10, false, false);
        let score_dirty = compute_score(&p, 10.0, 10.0, 100, 10, false, true);
        assert!(score_dirty < score_clean);
        assert!(score_dirty < 700.0);
    }

    #[test]
    fn test_ax_ex_f60_determinism() {
        let p = ExergyParams { g: 12.0, l: 12.0, a: 1.0, b: 1.0, p: 1.0, e_base: 0.04 };
        let pf60 = ExergyParamsF60::from(&p);
        let score_f60_clean = compute_score_f60(&pf60, 10 * F60_SCALE, 10 * F60_SCALE, 100, 10, false, false);
        let score_f60_dirty = compute_score_f60(&pf60, 10 * F60_SCALE, 10 * F60_SCALE, 100, 10, false, true);
        assert!(score_f60_dirty < score_f60_clean);
        assert!(score_f60_clean <= 1000 * F60_SCALE);
    }
}
