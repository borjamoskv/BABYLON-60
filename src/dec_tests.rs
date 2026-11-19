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

#[test]
fn test_codifferential_d1_star_adjoint_property() {
    // LEY FUNDAMENTAL 5: Adjunción exacta <d1 u, w> = <u, d1* w>
    let mesh = CubicMesh3D::new(4);
    let mut u_vals = vec![0i64; mesh.num_edges];
    for (i, val) in u_vals.iter_mut().enumerate().take(mesh.num_edges) {
        *val = ((i as i64 * 19 + 3) % 60) - 30;
    }
    let u = Form1 { values: u_vals };

    let mut w_vals = vec![0i64; mesh.num_faces];
    for (i, val) in w_vals.iter_mut().enumerate().take(mesh.num_faces) {
        *val = ((i as i64 * 23 + 11) % 60) - 30;
    }
    let w = Form2 { values: w_vals };

    let d1_u = DiscreteDeRham::d1(&mesh, &u);
    let d1_star_w = DiscreteDeRham::codifferential_d1_star(&mesh, &w);

    let lhs: i128 = d1_u.values.iter().zip(w.values.iter()).map(|(&a, &b)| a as i128 * b as i128).sum();
    let rhs: i128 = u.values.iter().zip(d1_star_w.values.iter()).map(|(&a, &b)| a as i128 * b as i128).sum();

    assert_eq!(
        lhs, rhs,
        "VIOLACIÓN DE ADJUNCIÓN: <d1 u, w> ({}) != <u, d1* w> ({})",
        lhs, rhs
    );
}

#[test]
fn test_codifferential_nilpotency_d0_star_d1_star() {
    // LEY FUNDAMENTAL 6: d0*(d1* w) = 0 idénticamente para toda 2-forma w (Divergencia Cero Automática)
    let mesh = CubicMesh3D::new(4);
    let mut w_vals = vec![0i64; mesh.num_faces];
    for (i, val) in w_vals.iter_mut().enumerate().take(mesh.num_faces) {
        *val = ((i as i64 * 31 + 17) % 60) - 30;
    }
    let w = Form2 { values: w_vals };

    let d1_star_w = DiscreteDeRham::codifferential_d1_star(&mesh, &w);
    let div = DiscreteDeRham::codifferential_d0_star(&mesh, &d1_star_w);

    for (idx, &d) in div.values.iter().enumerate() {
        assert_eq!(
            d, 0,
            "VIOLACIÓN DE NILPOTENCIA: d0*(d1* w) != 0 en vértice {}",
            idx
        );
    }
}

#[test]
fn test_navier_stokes_taylor_green_rk4_simulation() {
    // LEY FUNDAMENTAL 7: Simulación mimética de Navier-Stokes con decaimiento monótono e incompresibilidad exacta
    let mut sim = MimeticNavierStokes::new(4, 0.05);
    sim.init_taylor_green(1.0);

    let initial_diag = sim.diagnostics();
    assert!(initial_diag.kinetic_energy > 0.0);
    assert!(initial_diag.max_divergence < 1e-12, "Divergencia inicial debe ser cero");

    let dt = 0.01;
    let mut prev_energy = initial_diag.kinetic_energy;

    for step in 1..=25 {
        let diag = sim.step_rk4(dt);

        // 1. Conservación estricta de la incompresibilidad en cada tick
        assert!(
            diag.max_divergence < 1e-10,
            "Paso {}: divergencia residual excedida ({})",
            step,
            diag.max_divergence
        );

        // 2. Decaimiento monótono estricto de energía cinética por viscosidad
        assert!(
            diag.kinetic_energy <= prev_energy + 1e-12,
            "Paso {}: la energía cinética creció espuriamente ({} > {})",
            step,
            diag.kinetic_energy,
            prev_energy
        );
        prev_energy = diag.kinetic_energy;

        // 3. Regularidad BKM preservada
        assert!(diag.is_regular, "Paso {}: candidata a singularidad detectada", step);
    }

    let final_diag = sim.diagnostics();
    assert!(final_diag.kinetic_energy < initial_diag.kinetic_energy);
    assert!(final_diag.bkm_accumulated > 0.0);
}

#[test]
fn test_adaptive_cfl_and_regularized_cf_smoothness() {
    // LEY FUNDAMENTAL 8: Mitigación de Falsación (CFL adaptativo y suavidad Constantin-Fefferman regularizada)
    let mut sim = MimeticNavierStokes::new(4, 0.05);
    sim.init_taylor_green(1.0);

    for step in 1..=15 {
        let diag = sim.step_adaptive_rk4();

        // 1. Paso adaptativo acotado por CFL
        assert!(diag.adaptive_dt > 1e-4 && diag.adaptive_dt <= 0.05, "Paso {}: dt fuera de cotas CFL: {}", step, diag.adaptive_dt);

        // 2. Incompresibilidad exacta
        assert!(diag.max_divergence < 1e-10, "Paso {}: divergencia excedida: {}", step, diag.max_divergence);

        // 3. Suavidad de Constantin-Fefferman regularizada (<60.0 en flujo regular suave)
        assert!(diag.vortex_direction_smoothness < 60.0, "Paso {}: CF smoothness rota: {}", step, diag.vortex_direction_smoothness);

        // 4. Radio efectivo de vórtice positivo y finito (ausencia de colapso a volumen cero)
        assert!(diag.effective_vortex_radius > 0.1, "Paso {}: radio efectivo colapsado a cero", step);
    }
}

#[test]
fn test_verify_mimetic_nilpotency_entrypoint() {
    assert_eq!(verify_mimetic_nilpotency(3), 0);
    assert_eq!(verify_mimetic_nilpotency(4), 0);
    assert_eq!(verify_mimetic_nilpotency(1), -1);
    assert_eq!(verify_mimetic_nilpotency(61), -1);
}
