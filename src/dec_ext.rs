//! Diagnósticos avanzados de Constantin-Fefferman, radio de vórtice y verificación de nilpotencia DEC.

use super::*;

impl MimeticNavierStokes {
    /// Calcula la constante de suavidad direccional Lipschitz de Constantin-Fefferman con regularización $\epsilon$-suave.
    pub fn compute_regularized_cf_smoothness(&self, omega: &[f64]) -> f64 {
        let mut xi = vec![[0.0f64; 3]; self.mesh.num_vertices];

        for z in 0..self.mesh.n {
            for y in 0..self.mesh.n {
                for x in 0..self.mesh.n {
                    let prev_x = if x == 0 { self.mesh.n - 1 } else { x - 1 };
                    let prev_y = if y == 0 { self.mesh.n - 1 } else { y - 1 };
                    let prev_z = if z == 0 { self.mesh.n - 1 } else { z - 1 };

                    let wx = 0.5 * (omega[self.mesh.face_idx(x, y, z, 0)] + omega[self.mesh.face_idx(prev_x, y, z, 0)]);
                    let wy = 0.5 * (omega[self.mesh.face_idx(x, y, z, 1)] + omega[self.mesh.face_idx(x, prev_y, z, 1)]);
                    let wz = 0.5 * (omega[self.mesh.face_idx(x, y, z, 2)] + omega[self.mesh.face_idx(x, y, prev_z, 2)]);

                    let norm_sq = wx * wx + wy * wy + wz * wz + self.epsilon_reg * self.epsilon_reg;
                    let norm = norm_sq.sqrt();
                    let v = self.mesh.vertex_idx(x, y, z);
                    xi[v] = [wx / norm, wy / norm, wz / norm];
                }
            }
        }

        let mut max_lip = 0.0f64;
        let h = self.grid_spacing_h;
        for z in 0..self.mesh.n {
            for y in 0..self.mesh.n {
                for x in 0..self.mesh.n {
                    let v = self.mesh.vertex_idx(x, y, z);
                    let vx_next = self.mesh.vertex_idx(x + 1, y, z);
                    let vy_next = self.mesh.vertex_idx(x, y + 1, z);
                    let vz_next = self.mesh.vertex_idx(x, y, z + 1);

                    for &nbr in &[vx_next, vy_next, vz_next] {
                        let d_xi = (
                            (xi[v][0] - xi[nbr][0]).powi(2) +
                            (xi[v][1] - xi[nbr][1]).powi(2) +
                            (xi[v][2] - xi[nbr][2]).powi(2)
                        ).sqrt();
                        let lip = d_xi / h;
                        if lip > max_lip {
                            max_lip = lip;
                        }
                    }
                }
            }
        }
        max_lip
    }

    /// Calcula el radio efectivo del núcleo de vorticidad (segundo momento espacial de enstrofía en el toro periódico).
    pub fn compute_effective_vortex_radius(&self, omega: &[f64]) -> f64 {
        let mut max_idx = 0;
        let mut max_val = 0.0f64;
        for (i, &w) in omega.iter().enumerate() {
            if w.abs() > max_val {
                max_val = w.abs();
                max_idx = i;
            }
        }

        let v0 = max_idx / 3;
        let x0 = v0 % self.mesh.n;
        let y0 = (v0 / self.mesh.n) % self.mesh.n;
        let z0 = v0 / (self.mesh.n * self.mesh.n);

        let mut total_enstrophy = 0.0f64;
        let mut moment_2 = 0.0f64;
        let n = self.mesh.n as f64;
        let h = self.grid_spacing_h;

        for z in 0..self.mesh.n {
            for y in 0..self.mesh.n {
                for x in 0..self.mesh.n {
                    let dx = ((x as isize - x0 as isize).abs() as f64).min(n - (x as isize - x0 as isize).abs() as f64) * h;
                    let dy = ((y as isize - y0 as isize).abs() as f64).min(n - (y as isize - y0 as isize).abs() as f64) * h;
                    let dz = ((z as isize - z0 as isize).abs() as f64).min(n - (z as isize - z0 as isize).abs() as f64) * h;
                    let dist_sq = dx * dx + dy * dy + dz * dz;

                    for dir in 0..3 {
                        let w = omega[self.mesh.face_idx(x, y, z, dir)];
                        let enst = w * w;
                        total_enstrophy += enst;
                        moment_2 += dist_sq * enst;
                    }
                }
            }
        }

        if total_enstrophy < 1e-14 {
            0.0
        } else {
            (moment_2 / total_enstrophy).sqrt()
        }
    }

    /// Avanza un paso temporal adaptativo mediante RK4 garantizando estabilidad CFL.
    pub fn step_adaptive_rk4(&mut self) -> SimulationDiagnostics {
        let dt = self.compute_adaptive_dt();
        self.step_rk4(dt)
    }

    /// Diagnósticos instantáneos de energía, enstrofía, helicidad y BKM.
    pub fn diagnostics(&self) -> SimulationDiagnostics {
        let omega = self.compute_vorticity(&self.u);
        let div = DiscreteDeRham::codifferential_d0_star_f64(&self.mesh, &self.u);

        let ke: f64 = 0.5 * self.u.iter().map(|&v| v * v).sum::<f64>();
        let enstrophy: f64 = 0.5 * omega.iter().map(|&w| w * w).sum::<f64>();

        let mut helicity = 0.0f64;
        for i in 0..self.mesh.num_edges {
            helicity += self.u[i] * omega[i % self.mesh.num_faces];
        }

        let max_vorticity = omega.iter().map(|&w| w.abs()).fold(0.0f64, f64::max);
        let max_div = div.iter().map(|&d| d.abs()).fold(0.0f64, f64::max);
        let is_reg = max_vorticity < self.bkm_threshold;

        let adaptive_dt = self.compute_adaptive_dt();
        let cf_smooth = self.compute_regularized_cf_smoothness(&omega);
        let eff_radius = self.compute_effective_vortex_radius(&omega);

        SimulationDiagnostics {
            time: self.time,
            step: self.step_count,
            kinetic_energy: ke,
            enstrophy,
            helicity,
            max_vorticity,
            max_divergence: max_div,
            bkm_accumulated: self.bkm_accumulated,
            is_regular: is_reg,
            adaptive_dt,
            vortex_direction_smoothness: cf_smooth,
            effective_vortex_radius: eff_radius,
        }
    }
}

/// Verifica formalmente las identidades de nilpotencia mimética de De Rham en silicio:
/// - `d1 ∘ d0 ≡ 0` (rot ∘ grad ≡ 0)
/// - `d2 ∘ d1 ≡ 0` (div ∘ rot ≡ 0)
///
/// Retornos:
/// - `0`: Nilpotencia exacta verificada a nivel de bit
/// - `1`: Violación en `d1 ∘ d0`
/// - `2`: Violación en `d2 ∘ d1`
/// - `-1`: Dimensión inválida (`n < 2` o `n > 60`)
pub fn verify_mimetic_nilpotency(n: usize) -> i32 {
    if !(2..=60).contains(&n) {
        return -1;
    }
    let mesh = CubicMesh3D::new(n);

    // 1. Probar d1 ∘ d0 ≡ 0 sobre potencial escalar pseudoaleatorio no trivial
    let mut p_vals = Vec::with_capacity(mesh.num_vertices);
    for i in 0..mesh.num_vertices {
        p_vals.push(((i as i64 * 13 + 7) % 60) - 30);
    }
    let phi = Form0 { values: p_vals };
    let grad_phi = DiscreteDeRham::d0(&mesh, &phi);
    let curl_grad = DiscreteDeRham::d1(&mesh, &grad_phi);
    if !curl_grad.values.iter().all(|&v| v == 0) {
        return 1;
    }

    // 2. Probar d2 ∘ d1 ≡ 0 sobre campo de velocidad arbitrario no trivial
    let mut u_vals = Vec::with_capacity(mesh.num_edges);
    for i in 0..mesh.num_edges {
        u_vals.push(((i as i64 * 37 + 19) % 60) - 30);
    }
    let u = Form1 { values: u_vals };
    let vorticity = DiscreteDeRham::d1(&mesh, &u);
    let div_vort = DiscreteDeRham::d2(&mesh, &vorticity);
    if !div_vort.values.iter().all(|&v| v == 0) {
        return 2;
    }

    0
}
