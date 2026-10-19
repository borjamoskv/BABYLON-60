// ============================================================================
// B60 FISHER INFORMATION GEOMETRY & MINIMAL ACTION SIMPLEX ENGINE
// Reference: Physics of Information Geometry Part I & II (arXiv:2609.08285/11187)
// ============================================================================

pub struct FisherSimplex;

impl FisherSimplex {
    /// Coeficiente de Bhattacharyya: BC(p, q) = \sum_x \sqrt{p(x) * q(x)}
    pub fn bhattacharyya_coefficient(p: &[f64], q: &[f64]) -> f64 {
        assert_eq!(p.len(), q.len(), "Dimensiones deben coincidir en el símplex");
        let mut bc = 0.0;
        for (&pi, &qi) in p.iter().zip(q.iter()) {
            bc += (pi * qi).sqrt();
        }
        bc.clamp(0.0, 1.0)
    }

    /// Distancia Geodésica de Fisher-Rao: d_F(p, q) = 2 * arccos(BC(p, q))
    pub fn fisher_rao_distance(p: &[f64], q: &[f64]) -> f64 {
        let bc = Self::bhattacharyya_coefficient(p, q);
        2.0 * bc.acos()
    }

    /// Acción Cinética de Mínima Acción Informacional: A_kin = 0.5 * (d_F^2 / T)
    pub fn kinetic_action(p: &[f64], q: &[f64], duration_secs: f64) -> f64 {
        assert!(duration_secs > 0.0, "Duración debe ser positiva");
        let dist = Self::fisher_rao_distance(p, q);
        0.5 * (dist * dist) / duration_secs
    }

    /// Divergencia de Kullback-Leibler (Entropía Relativa): D_KL(p || q) = \sum_x p(x) * ln(p(x) / q(x))
    pub fn relative_entropy_kl(p: &[f64], q: &[f64]) -> f64 {
        assert_eq!(p.len(), q.len());
        let mut d_kl = 0.0;
        for (&pi, &qi) in p.iter().zip(q.iter()) {
            if pi > 1e-12 {
                assert!(qi > 1e-12, "Soporte violado: q(x) = 0 con p(x) > 0");
                d_kl += pi * (pi / qi).ln();
            }
        }
        d_kl
    }

    /// Teorema Pitagórico de la Información: D_KL(p || r) = D_KL(p || q) + D_KL(q || r)
    /// Retorna: (es_valido, residual_error)
    pub fn verify_pythagorean_identity(p: &[f64], q_proj: &[f64], r: &[f64]) -> (bool, f64) {
        let d_pr = Self::relative_entropy_kl(p, r);
        let d_pq = Self::relative_entropy_kl(p, q_proj);
        let d_qr = Self::relative_entropy_kl(q_proj, r);

        let residual = (d_pr - (d_pq + d_qr)).abs();
        (residual < 1e-7, residual)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fisher_rao_geodesic_properties() {
        let p = [0.5, 0.5];
        let q = [0.5, 0.5];
        assert_eq!(FisherSimplex::fisher_rao_distance(&p, &q), 0.0);

        let p_ortho = [1.0, 0.0];
        let q_ortho = [0.0, 1.0];
        let dist = FisherSimplex::fisher_rao_distance(&p_ortho, &q_ortho);
        // arccos(0) = pi / 2 -> 2 * (pi / 2) = pi
        assert!((dist - std::f64::consts::PI).abs() < 1e-10);
    }

    #[test]
    fn test_pythagorean_identity_information_projection() {
        // Distribución prior r uniforme
        let r = [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0];
        // Familia lineal E: distribuciones con p[0] = 0.5
        // Proyección de información I-projection de r sobre E:
        // q_proj = [0.5, 0.25, 0.25]
        let q_proj = [0.5, 0.25, 0.25];
        // Cualquier otro p en E: ej. [0.5, 0.4, 0.1]
        let p = [0.5, 0.4, 0.1];

        let (valid, residual) = FisherSimplex::verify_pythagorean_identity(&p, &q_proj, &r);
        assert!(valid, "Fallo en Teorema Pitagórico: residual = {}", residual);
    }
}
