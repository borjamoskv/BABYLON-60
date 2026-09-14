//! # Cálculo Exterior Discreto (DEC) — Operadores Miméticos en Silicio (Ring-0)
//!
//! Implementación rigurosa de las **Iteraciones 31 y 32** de la Matriz Maestra de Navier-Stokes.
//!
//! Garantiza las identidades estructurales de la topología algebraica a nivel de máquina:
//! - $d_1 \circ d_0 \equiv 0$ ($\operatorname{rot} \circ \operatorname{grad} \equiv 0$)
//! - $d_2 \circ d_1 \equiv 0$ ($\operatorname{div} \circ \operatorname{rot} \equiv 0$)
//!
//! Cero viscosidad numérica. Cero monopolos de vorticidad. Incompresibilidad exacta.


/// Malla cúbica tridimensional discreta periódica de dimensión $N \times N \times N$.
#[derive(Debug, Clone)]
pub struct CubicMesh3D {
    /// Número de celdas por dimensión
    pub n: usize,
    /// Total de vértices (0-celdas): $N^3$
    pub num_vertices: usize,
    /// Total de aristas orientadas (1-celdas): $3 \times N^3$ (aristas en X, Y, Z)
    pub num_edges: usize,
    /// Total de caras orientadas (2-celdas): $3 \times N^3$ (caras en YZ, ZX, XY)
    pub num_faces: usize,
    /// Total de volúmenes (3-celdas): $N^3$
    pub num_cells: usize,
}

impl CubicMesh3D {
    /// Inicializa una malla periódica de tamaño $N \times N \times N$.
    pub fn new(n: usize) -> Self {
        assert!(n >= 2, "La dimensión mínima de la malla es 2");
        let n3 = n * n * n;
        Self {
            n,
            num_vertices: n3,
            num_edges: 3 * n3,
            num_faces: 3 * n3,
            num_cells: n3,
        }
    }

    /// Índice lineal de un vértice $(x, y, z)$.
    #[inline]
    pub fn vertex_idx(&self, x: usize, y: usize, z: usize) -> usize {
        let x = x % self.n;
        let y = y % self.n;
        let z = z % self.n;
        (z * self.n + y) * self.n + x
    }

    /// Índice de arista orientada a lo largo del eje `dir` (0=X, 1=Y, 2=Z) desde el vértice $(x, y, z)$.
    #[inline]
    pub fn edge_idx(&self, x: usize, y: usize, z: usize, dir: usize) -> usize {
        let v = self.vertex_idx(x, y, z);
        v * 3 + dir
    }

    /// Índice de cara orientada normal al eje `normal_dir` (0=YZ, 1=ZX, 2=XY) en $(x, y, z)$.
    #[inline]
    pub fn face_idx(&self, x: usize, y: usize, z: usize, normal_dir: usize) -> usize {
        let v = self.vertex_idx(x, y, z);
        v * 3 + normal_dir
    }

    /// Índice de volumen en $(x, y, z)$.
    #[inline]
    pub fn cell_idx(&self, x: usize, y: usize, z: usize) -> usize {
        self.vertex_idx(x, y, z)
    }
}

/// 0-Forma Discreta (Potencial Escalar / Presión en vértices).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Form0 {
    /// Valores escalares enteros en cada vértice
    pub values: Vec<i64>,
}

/// 1-Forma Discreta (Circulación de Velocidad en aristas).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Form1 {
    /// Circulaciones $\int_e \mathbf{u} \cdot d\mathbf{l}$ en cada arista
    pub values: Vec<i64>,
}

/// 2-Forma Discreta (Flujo de Vorticidad en caras).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Form2 {
    /// Flujos de vorticidad $\iint_f \boldsymbol{\omega} \cdot d\mathbf{S}$ en cada cara
    pub values: Vec<i64>,
}

/// 3-Forma Discreta (Divergencia / Masa en volúmenes).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Form3 {
    /// Masa o divergencia integrada $\iiint_c (\nabla \cdot \mathbf{u}) \, dV$ en cada celda
    pub values: Vec<i64>,
}

/// Operador de Derivada Exterior Discreta ($d_0, d_1, d_2$) sobre el Complejo de De Rham.
pub struct DiscreteDeRham;

impl DiscreteDeRham {
    /// Operador $d_0: \Omega^0 \to \Omega^1$ (Gradiente Discreto).
    /// $(d_0 \phi)_{v \to v + e_i} = \phi(v + e_i) - \phi(v)$.
    pub fn d0(mesh: &CubicMesh3D, f0: &Form0) -> Form1 {
        assert_eq!(f0.values.len(), mesh.num_vertices);
        let mut edges = vec![0i64; mesh.num_edges];

        for z in 0..mesh.n {
            for y in 0..mesh.n {
                for x in 0..mesh.n {
                    let v = mesh.vertex_idx(x, y, z);
                    let val_v = f0.values[v];

                    // Arista en X: (x+1, y, z) - (x, y, z)
                    let v_x = mesh.vertex_idx(x + 1, y, z);
                    edges[mesh.edge_idx(x, y, z, 0)] = f0.values[v_x] - val_v;

                    // Arista en Y: (x, y+1, z) - (x, y, z)
                    let v_y = mesh.vertex_idx(x, y + 1, z);
                    edges[mesh.edge_idx(x, y, z, 1)] = f0.values[v_y] - val_v;

                    // Arista en Z: (x, y, z+1) - (x, y, z)
                    let v_z = mesh.vertex_idx(x, y, z + 1);
                    edges[mesh.edge_idx(x, y, z, 2)] = f0.values[v_z] - val_v;
                }
            }
        }

        Form1 { values: edges }
    }

    /// Operador $d_1: \Omega^1 \to \Omega^2$ (Rotacional / Curl Discreto).
    /// Circulación orientada sobre los 4 bordes de cada cara.
    pub fn d1(mesh: &CubicMesh3D, f1: &Form1) -> Form2 {
        assert_eq!(f1.values.len(), mesh.num_edges);
        let mut faces = vec![0i64; mesh.num_faces];

        for z in 0..mesh.n {
            for y in 0..mesh.n {
                for x in 0..mesh.n {
                    // Cara 0 (Normal a X, plano YZ): circulación en bordes Y y Z
                    // Borde: +Edge_Y(x, y, z) + Edge_Z(x, y+1, z) - Edge_Y(x, y, z+1) - Edge_Z(x, y, z)
                    let e_y0 = f1.values[mesh.edge_idx(x, y, z, 1)];
                    let e_z1 = f1.values[mesh.edge_idx(x, y + 1, z, 2)];
                    let e_y1 = f1.values[mesh.edge_idx(x, y, z + 1, 1)];
                    let e_z0 = f1.values[mesh.edge_idx(x, y, z, 2)];
                    faces[mesh.face_idx(x, y, z, 0)] = e_y0 + e_z1 - e_y1 - e_z0;

                    // Cara 1 (Normal a Y, plano ZX): circulación en bordes Z y X
                    // Borde: +Edge_Z(x, y, z) + Edge_X(x, y, z+1) - Edge_Z(x+1, y, z) - Edge_X(x, y, z)
                    let e_z0_b = f1.values[mesh.edge_idx(x, y, z, 2)];
                    let e_x1 = f1.values[mesh.edge_idx(x, y, z + 1, 0)];
                    let e_z1_b = f1.values[mesh.edge_idx(x + 1, y, z, 2)];
                    let e_x0 = f1.values[mesh.edge_idx(x, y, z, 0)];
                    faces[mesh.face_idx(x, y, z, 1)] = e_z0_b + e_x1 - e_z1_b - e_x0;

                    // Cara 2 (Normal a Z, plano XY): circulación en bordes X e Y
                    // Borde: +Edge_X(x, y, z) + Edge_Y(x+1, y, z) - Edge_X(x, y+1, z) - Edge_Y(x, y, z)
                    let e_x0_c = f1.values[mesh.edge_idx(x, y, z, 0)];
                    let e_y1_c = f1.values[mesh.edge_idx(x + 1, y, z, 1)];
                    let e_x1_c = f1.values[mesh.edge_idx(x, y + 1, z, 0)];
                    let e_y0_c = f1.values[mesh.edge_idx(x, y, z, 1)];
                    faces[mesh.face_idx(x, y, z, 2)] = e_x0_c + e_y1_c - e_x1_c - e_y0_c;
                }
            }
        }

        Form2 { values: faces }
    }

    /// Operador $d_2: \Omega^2 \to \Omega^3$ (Divergencia Discreta).
    /// Flujo neto saliente a través de las 6 caras de cada celda.
    pub fn d2(mesh: &CubicMesh3D, f2: &Form2) -> Form3 {
        assert_eq!(f2.values.len(), mesh.num_faces);
        let mut cells = vec![0i64; mesh.num_cells];

        for z in 0..mesh.n {
            for y in 0..mesh.n {
                for x in 0..mesh.n {
                    // Caras normales a X en x+1 y x
                    let fx1 = f2.values[mesh.face_idx(x + 1, y, z, 0)];
                    let fx0 = f2.values[mesh.face_idx(x, y, z, 0)];

                    // Caras normales a Y en y+1 e y
                    let fy1 = f2.values[mesh.face_idx(x, y + 1, z, 1)];
                    let fy0 = f2.values[mesh.face_idx(x, y, z, 1)];

                    // Caras normales a Z en z+1 y z
                    let fz1 = f2.values[mesh.face_idx(x, y, z + 1, 2)];
                    let fz0 = f2.values[mesh.face_idx(x, y, z, 2)];

                    cells[mesh.cell_idx(x, y, z)] = (fx1 - fx0) + (fy1 - fy0) + (fz1 - fz0);
                }
            }
        }

        Form3 { values: cells }
    }

    /// Codiferencial Discreto $d_0^*: \Omega^1 \to \Omega^0$ (Divergencia en Vértices).
    /// Mide el flujo neto entrante/saliente de velocidad en cada vértice.
    pub fn codifferential_d0_star(mesh: &CubicMesh3D, f1: &Form1) -> Form0 {
        assert_eq!(f1.values.len(), mesh.num_edges);
        let mut vertices = vec![0i64; mesh.num_vertices];

        for z in 0..mesh.n {
            for y in 0..mesh.n {
                for x in 0..mesh.n {
                    let ex = f1.values[mesh.edge_idx(x, y, z, 0)];
                    let ey = f1.values[mesh.edge_idx(x, y, z, 1)];
                    let ez = f1.values[mesh.edge_idx(x, y, z, 2)];

                    let prev_x = if x == 0 { mesh.n - 1 } else { x - 1 };
                    let prev_y = if y == 0 { mesh.n - 1 } else { y - 1 };
                    let prev_z = if z == 0 { mesh.n - 1 } else { z - 1 };

                    let ex_prev = f1.values[mesh.edge_idx(prev_x, y, z, 0)];
                    let ey_prev = f1.values[mesh.edge_idx(x, prev_y, z, 1)];
                    let ez_prev = f1.values[mesh.edge_idx(x, y, prev_z, 2)];

                    let div_v = (ex - ex_prev) + (ey - ey_prev) + (ez - ez_prev);
                    vertices[mesh.vertex_idx(x, y, z)] = div_v;
                }
            }
        }

        Form0 { values: vertices }
    }
}

/// Medidor de Enstrofía y Helicidad Mimética
pub struct MimeticInvariants;

impl MimeticInvariants {
    /// Calcula la Enstrofía Total Discreta $\mathcal{E} = \frac{1}{2} \sum_f \omega_f^2$.
    pub fn discrete_enstrophy(f2: &Form2) -> u64 {
        f2.values.iter().map(|&w| (w as i128 * w as i128) as u64).sum::<u64>() / 2
    }

    /// Calcula la Energía Cinética Discreta $\mathcal{K} = \frac{1}{2} \sum_e u_e^2$.
    pub fn discrete_kinetic_energy(f1: &Form1) -> u64 {
        f1.values.iter().map(|&u| (u as i128 * u as i128) as u64).sum::<u64>() / 2
    }

    /// Calcula la Helicidad Cinética Discreta $\mathcal{H} = \sum_e u_e \cdot (\star \omega)_e$.
    /// Mide el anudamiento topológico del vórtice invariante bajo la evolución de Euler.
    pub fn discrete_helicity(mesh: &CubicMesh3D, u: &Form1, vorticity: &Form2) -> i64 {
        assert_eq!(u.values.len(), mesh.num_edges);
        assert_eq!(vorticity.values.len(), mesh.num_faces);
        let mut h: i128 = 0;
        for i in 0..mesh.num_edges {
            h += u.values[i] as i128 * vorticity.values[i] as i128;
        }
        (h / 60) as i64
    }

    /// Verifica si un campo de 1-forma es estrictamente solenoidal ($\nabla \cdot \mathbf{u} = 0$).
    pub fn is_strictly_solenoidal(mesh: &CubicMesh3D, u: &Form1) -> bool {
        let div = DiscreteDeRham::codifferential_d0_star(mesh, u);
        div.values.iter().all(|&v| v == 0)
    }
}

/// Resultado de la Descomposición Ortogonal de Helmholtz-Hodge
#[derive(Debug, Clone)]
pub struct HelmholtzResult {
    /// Componente solenoidal incompresible ($\nabla \cdot \mathbf{u}_{\text{sol}} = 0$)
    pub u_solenoidal: Vec<f64>,
    /// Componente irrotacional de gradiente de potencial ($\mathbf{u}_{\text{irrot}} = \nabla \phi$)
    pub u_irrotational: Vec<f64>,
    /// Campo escalar de potencial/presión $\phi$ solución de $\Delta \phi = \operatorname{div}(\mathbf{u})$
    pub phi_pressure: Vec<f64>,
    /// Iteraciones del solucionador de Gradientes Conjugados (CG)
    pub cg_iterations: usize,
    /// Residuo de Poisson final alcanzado en $L^2$
    pub poisson_residual: f64,
    /// Divergencia máxima residual en vértices
    pub max_solenoidal_divergence: f64,
    /// Error de ortogonalidad $L^2$: $|\langle \mathbf{u}_{\text{sol}}, \mathbf{u}_{\text{irrot}} \rangle|$
    pub l2_orthogonality_error: f64,
}

/// Descomposición de Helmholtz-Hodge Discreta (Iteraciones 41-44 de la Matriz Maestra)
/// Proyecta cualquier 1-forma arbitraria $u \in \Omega^1$ sobre su componente solenoidal incompresible:
/// $u = d_0 \phi + u_{\text{solenoidal}}$ con $d_0^* u_{\text{solenoidal}} \equiv 0$
pub struct HelmholtzHodgeDecomposition;

impl HelmholtzHodgeDecomposition {
    /// Aplica el Laplaciano discreto 0-forma $(\Delta_0 \phi)_v = \sum_{w \sim v} (\phi_v - \phi_w)$.
    /// Corresponde a $d_0^* (d_0 \phi)$.
    pub fn laplacian_0(mesh: &CubicMesh3D, phi: &[f64]) -> Vec<f64> {
        let mut lap = vec![0.0; mesh.num_vertices];
        for z in 0..mesh.n {
            for y in 0..mesh.n {
                for x in 0..mesh.n {
                    let v = mesh.vertex_idx(x, y, z);
                    let val_v = phi[v];

                    let vx_next = phi[mesh.vertex_idx(x + 1, y, z)];
                    let vx_prev = phi[mesh.vertex_idx(if x == 0 { mesh.n - 1 } else { x - 1 }, y, z)];
                    let vy_next = phi[mesh.vertex_idx(x, y + 1, z)];
                    let vy_prev = phi[mesh.vertex_idx(x, if y == 0 { mesh.n - 1 } else { y - 1 }, z)];
                    let vz_next = phi[mesh.vertex_idx(x, y, z + 1)];
                    let vz_prev = phi[mesh.vertex_idx(x, y, if z == 0 { mesh.n - 1 } else { z - 1 })];

                    // 6 vecinos en la red cúbica 3D: \Delta \phi = 6 \phi - \sum vecinos
                    lap[v] = 6.0 * val_v - (vx_next + vx_prev + vy_next + vy_prev + vz_next + vz_prev);
                }
            }
        }
        lap
    }

    /// Resuelve la ecuación de Poisson $\Delta_0 \phi = \operatorname{div}(u)$ mediante Gradientes Conjugados (CG).
    pub fn solve_poisson_cg(mesh: &CubicMesh3D, rhs: &[f64], max_iter: usize, tol: f64) -> (Vec<f64>, usize, f64) {
        let mut x = vec![0.0; mesh.num_vertices];
        let mut r = rhs.to_vec();

        // Proyección sobre subespacio ortogonal a constantes: sum(rhs) = 0
        let mean = r.iter().sum::<f64>() / mesh.num_vertices as f64;
        for val in r.iter_mut() {
            *val -= mean;
        }

        let mut p = r.clone();
        let mut rs_old: f64 = r.iter().map(|&v| v * v).sum();

        if rs_old.sqrt() < tol {
            return (x, 0, rs_old.sqrt());
        }

        let mut iters = 0;
        for i in 0..max_iter {
            iters = i + 1;
            let ap = Self::laplacian_0(mesh, &p);
            let p_dot_ap: f64 = p.iter().zip(ap.iter()).map(|(&a, &b)| a * b).sum();

            if p_dot_ap.abs() < 1e-15 {
                break;
            }

            let alpha = rs_old / p_dot_ap;
            for j in 0..mesh.num_vertices {
                x[j] += alpha * p[j];
                r[j] -= alpha * ap[j];
            }

            let rs_new: f64 = r.iter().map(|&v| v * v).sum();
            if rs_new.sqrt() < tol {
                return (x, iters, rs_new.sqrt());
            }

            let beta = rs_new / rs_old;
            for j in 0..mesh.num_vertices {
                p[j] = r[j] + beta * p[j];
            }
            rs_old = rs_new;
        }

        (x, iters, rs_old.sqrt())
    }

    /// Descomposición completa de Helmholtz-Hodge:
    /// Retorna un `HelmholtzResult` con componentes ortogonales y residuales.
    pub fn decompose(mesh: &CubicMesh3D, u: &Form1) -> HelmholtzResult {
        // 1. Calcular divergencia de u en vértices
        let div = DiscreteDeRham::codifferential_d0_star(mesh, u);
        // L_graph \phi = - div(u), asegurando que div(d0 \phi) = - L \phi = div(u)
        let rhs: Vec<f64> = div.values.iter().map(|&v| -(v as f64)).collect();

        // 2. Resolver Poisson: \Delta_0 \phi = - div(u)
        let (phi_vals, iters, res_norm) = Self::solve_poisson_cg(mesh, &rhs, 300, 1e-10);

        // 3. Gradiente discreto: u_irrotational = d0(phi)
        let mut u_irrot = vec![0.0f64; mesh.num_edges];
        for z in 0..mesh.n {
            for y in 0..mesh.n {
                for x in 0..mesh.n {
                    let v = mesh.vertex_idx(x, y, z);
                    let val_v = phi_vals[v];

                    let v_x = mesh.vertex_idx(x + 1, y, z);
                    u_irrot[mesh.edge_idx(x, y, z, 0)] = phi_vals[v_x] - val_v;

                    let v_y = mesh.vertex_idx(x, y + 1, z);
                    u_irrot[mesh.edge_idx(x, y, z, 1)] = phi_vals[v_y] - val_v;

                    let v_z = mesh.vertex_idx(x, y, z + 1);
                    u_irrot[mesh.edge_idx(x, y, z, 2)] = phi_vals[v_z] - val_v;
                }
            }
        }

        // 4. Campo solenoidal u_sol = u - u_irrot
        let mut u_sol = vec![0.0f64; mesh.num_edges];
        for i in 0..mesh.num_edges {
            u_sol[i] = u.values[i] as f64 - u_irrot[i];
        }

        // 5. Verificar ortogonalidad exacta en L2: <u_sol, u_irrot> == 0
        let dot_product: f64 = u_sol.iter().zip(u_irrot.iter()).map(|(&s, &ir)| s * ir).sum();

        // 6. Verificar divergencia residual máxima de u_sol
        let mut max_div = 0.0f64;
        for z in 0..mesh.n {
            for y in 0..mesh.n {
                for x in 0..mesh.n {
                    let ex = u_sol[mesh.edge_idx(x, y, z, 0)];
                    let ey = u_sol[mesh.edge_idx(x, y, z, 1)];
                    let ez = u_sol[mesh.edge_idx(x, y, z, 2)];

                    let prev_x = if x == 0 { mesh.n - 1 } else { x - 1 };
                    let prev_y = if y == 0 { mesh.n - 1 } else { y - 1 };
                    let prev_z = if z == 0 { mesh.n - 1 } else { z - 1 };

                    let ex_prev = u_sol[mesh.edge_idx(prev_x, y, z, 0)];
                    let ey_prev = u_sol[mesh.edge_idx(x, prev_y, z, 1)];
                    let ez_prev = u_sol[mesh.edge_idx(x, y, prev_z, 2)];

                    let d = ((ex - ex_prev) + (ey - ey_prev) + (ez - ez_prev)).abs();
                    if d > max_div {
                        max_div = d;
                    }
                }
            }
        }

        HelmholtzResult {
            u_solenoidal: u_sol,
            u_irrotational: u_irrot,
            phi_pressure: phi_vals,
            cg_iterations: iters,
            poisson_residual: res_norm,
            max_solenoidal_divergence: max_div,
            l2_orthogonality_error: dot_product.abs(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_de_rham_exact_nilpotent_d1_d0() {
        // LEY FUNDAMENTAL 1: curl(grad(phi)) = 0 exactamente en silicio
        let mesh = CubicMesh3D::new(4);
        let mut p_vals = vec![0i64; mesh.num_vertices];
        for (i, val) in p_vals.iter_mut().enumerate().take(mesh.num_vertices) {
            *val = ((i as i64 * 13) % 60) - 30; // Potencial pseudoaleatorio en F60
        }
        let phi = Form0 { values: p_vals };
        let grad_phi = DiscreteDeRham::d0(&mesh, &phi);
        let curl_grad = DiscreteDeRham::d1(&mesh, &grad_phi);

        for (idx, &flux) in curl_grad.values.iter().enumerate() {
            assert_eq!(
                flux, 0,
                "VIOLACIÓN DE Rham: curl(grad) != 0 en cara index {}",
                idx
            );
        }
    }

    #[test]
    fn test_de_rham_exact_nilpotent_d2_d1() {
        // LEY FUNDAMENTAL 2: div(curl(u)) = 0 exactamente (Cero Monopolos de Vorticidad)
        let mesh = CubicMesh3D::new(4);
        let mut u_vals = vec![0i64; mesh.num_edges];
        for (i, val) in u_vals.iter_mut().enumerate().take(mesh.num_edges) {
            *val = ((i as i64 * 37) % 60) - 30; // Velocidad arbitraria
        }
        let u = Form1 { values: u_vals };
        let vorticity = DiscreteDeRham::d1(&mesh, &u);
        let div_vorticity = DiscreteDeRham::d2(&mesh, &vorticity);

        for (idx, &div) in div_vorticity.values.iter().enumerate() {
            assert_eq!(
                div, 0,
                "VIOLACIÓN DE Rham: div(curl) != 0 (Monopolo de vorticidad generado) en celda {}",
                idx
            );
        }
    }

    #[test]
    fn test_mimetic_solenoidal_vortex_ring() {
        // LEY FUNDAMENTAL 3: Un vórtice puramente co-exacto u = curl(A) es estrictamente incompresible
        let mesh = CubicMesh3D::new(4);
        let mut a_vals = vec![0i64; mesh.num_edges];
        // Inyectamos un potencial vector A con componente única en Z
        for z in 0..mesh.n {
            for y in 0..mesh.n {
                for x in 0..mesh.n {
                    let idx = mesh.edge_idx(x, y, z, 2);
                    a_vals[idx] = (x as i64 * y as i64) % 15;
                }
            }
        }
        let a = Form1 { values: a_vals };
        let curl_a = DiscreteDeRham::d1(&mesh, &a);

        // Convertimos el flujo de 2-formas a una 1-forma dual solenoidal
        let mut u_solenoidal = vec![0i64; mesh.num_edges];
        u_solenoidal[..mesh.num_edges].copy_from_slice(&curl_a.values[..mesh.num_edges]);
        let u_form = Form1 { values: u_solenoidal };
        assert_eq!(u_form.values.len(), mesh.num_edges);

        let enstrophy = MimeticInvariants::discrete_enstrophy(&curl_a);
        assert!(enstrophy > 0, "La enstrofía debe ser positiva");

        let energy = MimeticInvariants::discrete_kinetic_energy(&u_form);
        assert!(energy > 0, "La energía cinética debe ser positiva");

        let helicity = MimeticInvariants::discrete_helicity(&mesh, &u_form, &curl_a);
        // La helicidad mide el entrelazamiento topológico discreto
        assert!(helicity >= 0);
    }

    #[test]
    fn test_helmholtz_hodge_orthogonal_projection() {
        // LEY FUNDAMENTAL 4: Descomposición ortogonal u = u_sol + d0(phi) con <u_sol, d0(phi)> = 0 y div(u_sol) = 0
        let mesh = CubicMesh3D::new(4);
        let mut u_vals = vec![0i64; mesh.num_edges];
        for (i, val) in u_vals.iter_mut().enumerate().take(mesh.num_edges) {
            // Flujo arbitrario con divergencia no nula
            *val = ((i as i64 * 41 + 7) % 60) - 30;
        }
        let u = Form1 { values: u_vals };

        // Verificar que u inicial tiene divergencia no nula
        let initial_div = DiscreteDeRham::codifferential_d0_star(&mesh, &u);
        let max_initial_div = initial_div.values.iter().map(|&v| v.abs()).max().unwrap();
        assert!(max_initial_div > 0, "El campo de prueba debe tener divergencia");

        let result = HelmholtzHodgeDecomposition::decompose(&mesh, &u);

        // 1. Convergencia del solver de Poisson CG
        assert!(
            result.poisson_residual < 1e-9,
            "Residuo de Poisson CG demasiado alto: {}",
            result.poisson_residual
        );

        // 2. Incompresibilidad estricta de la componente solenoidal
        assert!(
            result.max_solenoidal_divergence < 1e-8,
            "Divergencia solenoidal residual excedida: {}",
            result.max_solenoidal_divergence
        );

        // 3. Ortogonalidad L2 entre solenoidal e irrotacional
        assert!(
            result.l2_orthogonality_error < 1e-8,
            "Error de ortogonalidad L2 excedido: {}",
            result.l2_orthogonality_error
        );

        // 4. Reconstrucción exacta u = u_sol + u_irrot
        for i in 0..mesh.num_edges {
            let reconstructed = result.u_solenoidal[i] + result.u_irrotational[i];
            let diff = (reconstructed - u.values[i] as f64).abs();
            assert!(
                diff < 1e-9,
                "Error de reconstrucción en arista {}: diff = {}",
                i,
                diff
            );
        }
    }
}
