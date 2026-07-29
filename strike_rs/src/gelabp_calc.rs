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
    score.min(1000.0).max(0.0)
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
}
