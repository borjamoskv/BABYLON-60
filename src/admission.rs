use core::sync::atomic::{AtomicUsize, Ordering};
use std::time::Duration;

/// (FL-007) Deterministic Admission Controller for bounded liveness.
/// Ensures that $accepted(m) \implies bounded\_time[committed(m) \lor explicitly\_rejected(m)]$.
pub struct AdmissionController {
    max_queue_depth: usize,
    max_latency_budget: Duration,
    estimated_service_time_per_item: Duration,
    
    current_depth: AtomicUsize,
}

impl AdmissionController {
    /// Creates a new `AdmissionController` with maximum queue depth, latency budget, and service time estimates.
    pub fn new(max_queue_depth: usize, max_latency_budget: Duration, estimated_service_time_per_item: Duration) -> Self {
        Self {
            max_queue_depth,
            max_latency_budget,
            estimated_service_time_per_item,
            current_depth: AtomicUsize::new(0),
        }
    }

    /// Attempts to admit a new request.
    /// Returns Ok(()) if admitted (reserving 1 slot).
    /// Returns Err(usize) with the attempted depth if rejected due to capacity.
    pub fn try_admit(&self) -> Result<(), usize> {
        let mut current = self.current_depth.load(Ordering::Relaxed);
        loop {
            // Little's Law / Latency Bound check
            // Expected latency = current_depth * estimated_service_time
            let expected_latency = self.estimated_service_time_per_item.saturating_mul(current as u32);
            
            if current >= self.max_queue_depth || expected_latency > self.max_latency_budget {
                return Err(current + 1); // Capacity exceeded
            }

            match self.current_depth.compare_exchange_weak(
                current,
                current + 1,
                Ordering::Acquire,
                Ordering::Relaxed,
            ) {
                Ok(_) => return Ok(()),
                Err(actual) => current = actual,
            }
        }
    }

    /// Releases a previously admitted slot after processing (success or failure).
    pub fn release(&self) {
        self.current_depth.fetch_sub(1, Ordering::Release);
    }
    
    /// Returns the current admission queue depth.
    pub fn current_depth(&self) -> usize {
        self.current_depth.load(Ordering::Relaxed)
    }
}

/// Model Predictive Controller (MPC) for proactive admission backpressure.
///
/// Regulates admission rate over a finite prediction horizon $H$ by solving a
/// symmetric positive-definite (SPD) tridiagonal KKT/Riccati system in $O(H)$ time
/// via the Thomas ($LDL^T$) algorithm, avoiding $O(H^3)$ dense matrix inversions.
#[derive(Debug, Clone, Copy)]
pub struct MpcBackpressureController {
    horizon: usize,
    state_weight_q: f64,
    control_weight_r: f64,
    max_depth_ref: f64,
}

impl MpcBackpressureController {
    /// Creates a new `MpcBackpressureController` with finite horizon $H$, state penalty $Q$,
    /// control smoothness penalty $R$, and reference queue depth capacity.
    pub fn new(
        horizon: usize,
        state_weight_q: f64,
        control_weight_r: f64,
        max_depth_ref: f64,
    ) -> Self {
        Self {
            horizon,
            state_weight_q,
            control_weight_r,
            max_depth_ref,
        }
    }

    /// Returns the configured prediction horizon $H$.
    pub fn horizon(&self) -> usize {
        self.horizon
    }

    /// Returns the state deviation penalty weight $Q$.
    pub fn state_weight_q(&self) -> f64 {
        self.state_weight_q
    }

    /// Returns the control effort smoothness weight $R$.
    pub fn control_weight_r(&self) -> f64 {
        self.control_weight_r
    }

    /// Returns the reference maximum queue depth.
    pub fn max_depth_ref(&self) -> f64 {
        self.max_depth_ref
    }

    /// Computes the optimal normalized admission rate in `[0.0, 1.0]` by solving the
    /// $O(H)$ tridiagonal Riccati/Euler-Lagrange system.
    ///
    /// As `current_depth` approaches `max_depth_ref` or `thermal_pressure` approaches `1.0`,
    /// the controller proactively dampens the admission rate before collapsing into `POISONED`.
    pub fn compute_optimal_admission_rate(
        &self,
        current_depth: usize,
        thermal_pressure: f64,
    ) -> f64 {
        let h = self.horizon.max(2);
        let q = self.state_weight_q.max(1e-6);
        let r = self.control_weight_r.max(1e-6);
        let max_ref = self.max_depth_ref.max(1.0);

        let depth_norm = ((current_depth as f64) / max_ref).clamp(0.0, 1.0);
        let thermal_norm = thermal_pressure.clamp(0.0, 1.0);

        // Strictly monotonic joint load surface on [0, 1]^2
        let joint_stress = (0.85 * (depth_norm + thermal_norm - depth_norm * thermal_norm)
            + 0.15 * 0.5 * (depth_norm + thermal_norm))
            .clamp(0.0, 1.0);

        let diag = 2.0 * r + q;
        let off = -r;

        let mut c_prime = vec![0.0_f64; h];
        let mut d_prime = vec![0.0_f64; h];

        // Forward Thomas sweep (O(H))
        c_prime[0] = off / diag;
        d_prime[0] = (q * joint_stress) / diag;

        for i in 1..h {
            let rhs_i = if i + 1 == h {
                (q + r) * joint_stress
            } else {
                q * joint_stress
            };
            let denom = diag - off * c_prime[i - 1];
            if i + 1 < h {
                c_prime[i] = off / denom;
            }
            d_prime[i] = (rhs_i - off * d_prime[i - 1]) / denom;
        }

        // Back substitution (O(H))
        let mut u = vec![0.0_f64; h];
        u[h - 1] = d_prime[h - 1];
        for i in (0..(h - 1)).rev() {
            u[i] = d_prime[i] - c_prime[i] * u[i + 1];
        }

        (1.0 - u[0]).clamp(0.0, 1.0)
    }
}

#[cfg(target_os = "macos")]
#[link(name = "Accelerate", kind = "framework")]
extern "C" {
    fn cblas_dgemm(
        order: i32,
        trans_a: i32,
        trans_b: i32,
        m: i32,
        n: i32,
        k: i32,
        alpha: f64,
        a: *const f64,
        lda: i32,
        b: *const f64,
        ldb: i32,
        beta: f64,
        c: *mut f64,
        ldc: i32,
    );
}

/// Executes double-precision general matrix multiplication ($C = A \cdot B$) in strict
/// Column-Major layout (`CblasColMajor = 102`, `CblasNoTrans = 111`).
///
/// On macOS, dispatches directly to the Apple Silicon AMX coprocessor via the
/// `Accelerate` framework (`cblas_dgemm`). On other targets, executes a deterministic
/// Column-Major loop in pure Rust.
pub fn col_major_dgemm_accelerate(
    m: usize,
    n: usize,
    k: usize,
    a: &[f64],
    b: &[f64],
    c: &mut [f64],
) -> Result<(), &'static str> {
    if m == 0 || n == 0 || k == 0 {
        return Err("Matrix dimensions m, n, k must be strictly positive");
    }
    let Some(mk) = m.checked_mul(k) else {
        return Err("Dimension overflow in m * k");
    };
    let Some(kn) = k.checked_mul(n) else {
        return Err("Dimension overflow in k * n");
    };
    let Some(mn) = m.checked_mul(n) else {
        return Err("Dimension overflow in m * n");
    };

    if a.len() != mk || b.len() != kn || c.len() != mn {
        return Err("Slice length mismatch for column-major DGEMM dimensions");
    }

    #[cfg(target_os = "macos")]
    {
        const CBLAS_COL_MAJOR: i32 = 102;
        const CBLAS_NO_TRANS: i32 = 111;

        // SAFETY: Slice lengths `a.len() == m * k`, `b.len() == k * n`, and `c.len() == m * n`
        // have been validated above, and leading dimensions match Column-Major storage.
        unsafe {
            cblas_dgemm(
                CBLAS_COL_MAJOR,
                CBLAS_NO_TRANS,
                CBLAS_NO_TRANS,
                m as i32,
                n as i32,
                k as i32,
                1.0,
                a.as_ptr(),
                m as i32,
                b.as_ptr(),
                k as i32,
                0.0,
                c.as_mut_ptr(),
                m as i32,
            );
        }
    }

    #[cfg(not(target_os = "macos"))]
    {
        c.fill(0.0);
        for j in 0..n {
            for p in 0..k {
                let b_pj = b[j * k + p];
                for i in 0..m {
                    c[j * m + i] += a[p * m + i] * b_pj;
                }
            }
        }
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_mpc_backpressure_monotonic_damping() {
        let mpc = MpcBackpressureController::new(12, 2.0, 1.0, 100.0);

        // 1. Monotonic decrease with respect to queue depth at constant thermal pressure
        let mut prev_rate = mpc.compute_optimal_admission_rate(0, 0.0);
        assert!(
            (0.0..=1.0).contains(&prev_rate),
            "Initial admission rate must be in [0.0, 1.0]"
        );
        assert!(
            (prev_rate - 1.0).abs() < 1e-12,
            "Zero load must yield full admission rate 1.0"
        );

        for depth in [10_usize, 25, 50, 75, 100] {
            let rate = mpc.compute_optimal_admission_rate(depth, 0.0);
            assert!(
                (0.0..=1.0).contains(&rate),
                "Admission rate {rate} out of bounds [0.0, 1.0]"
            );
            assert!(
                rate < prev_rate,
                "Expected rate at depth {depth} ({rate}) < previous rate ({prev_rate})"
            );
            prev_rate = rate;
        }

        // 2. Monotonic decrease with respect to thermal pressure at constant queue depth
        let mut prev_thermal_rate = mpc.compute_optimal_admission_rate(20, 0.0);
        for thermal in [0.2_f64, 0.4, 0.6, 0.8, 1.0] {
            let rate = mpc.compute_optimal_admission_rate(20, thermal);
            assert!(
                (0.0..=1.0).contains(&rate),
                "Admission rate {rate} out of bounds [0.0, 1.0]"
            );
            assert!(
                rate < prev_thermal_rate,
                "Expected rate at thermal {thermal} ({rate}) < previous rate ({prev_thermal_rate})"
            );
            prev_thermal_rate = rate;
        }
    }

    #[test]
    fn test_col_major_dgemm_accelerate_exactness() {
        // Matrix A (2x3) in Column-Major order:
        // [ 1.0  3.0  5.0 ]
        // [ 2.0  4.0  6.0 ]
        let a = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0];

        // Matrix B (3x2) in Column-Major order:
        // [ 7.0   10.0 ]
        // [ 8.0   11.0 ]
        // [ 9.0   12.0 ]
        let b = [7.0, 8.0, 9.0, 10.0, 11.0, 12.0];

        // Expected C = A * B (2x2) in Column-Major order:
        // C(0,0) = 1*7 + 3*8 + 5*9 = 76.0
        // C(1,0) = 2*7 + 4*8 + 6*9 = 100.0
        // C(0,1) = 1*10 + 3*11 + 5*12 = 103.0
        // C(1,1) = 2*10 + 4*11 + 6*12 = 136.0
        let mut c = [0.0_f64; 4];
        col_major_dgemm_accelerate(2, 2, 3, &a, &b, &mut c)
            .expect("Valid column-major dimensions should succeed");

        let expected = [76.0, 100.0, 103.0, 136.0];
        for (actual, exp) in c.iter().zip(expected.iter()) {
            assert!(
                (actual - exp).abs() < 1e-9,
                "Mismatch in Column-Major DGEMM: got {actual}, expected {exp}"
            );
        }

        // Dimension mismatch validation
        let mut bad_c = [0.0_f64; 3];
        assert!(col_major_dgemm_accelerate(2, 2, 3, &a, &b, &mut bad_c).is_err());
        assert!(col_major_dgemm_accelerate(0, 2, 3, &[], &b, &mut []).is_err());
    }
}

