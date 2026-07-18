use pyo3::prelude::*;

#[pyclass]
#[derive(Clone)]
pub struct Arm64ReMatrix {
    #[pyo3(get, set)]
    pub execution_count: u64,
    #[pyo3(get, set)]
    pub pac_bypass_entropy: f64,
    #[pyo3(get, set)]
    pub dyld_cache_hit_rate: f64,
    #[pyo3(get, set)]
    pub amfi_enforcement_level: f64,
}

#[pymethods]
impl Arm64ReMatrix {
    #[new]
    pub fn new() -> Self {
        Self {
            execution_count: 0,
            pac_bypass_entropy: 0.0,
            dyld_cache_hit_rate: 1.0,
            amfi_enforcement_level: 1.0,
        }
    }

    pub fn compute_re_entropy(&self) -> f64 {
        self.pac_bypass_entropy * 0.4
            + (1.0 - self.dyld_cache_hit_rate) * 0.3
            + self.amfi_enforcement_level * 0.3
    }
}

pub fn get_arm64_domain_str(d: u8) -> &'static str {
    match d {
        0 => "ARM64_ISA_CORE",
        1 => "MACHO_STRUCT",
        2 => "XNU_KERNEL",
        3 => "PAC_MECHANICS",
        4 => "OBJC_RUNTIME",
        5 => "SWIFT_ABI",
        6 => "ENTITLEMENTS_CODESIGN",
        7 => "DYNAMIC_INSTRUMENTATION",
        8 => "DECOMPILATION_HEURISTICS",
        9 => "HARDWARE_CRYPTO",
        _ => "UNKNOWN",
    }
}

#[pyfunction]
pub fn dispatch_arm64_re(
    d: u8,
    p: u8,
    m: u8,
    mut matrix: PyRefMut<Arm64ReMatrix>,
) -> PyResult<(u16, String, f64)> {
    if d > 9 || p > 9 || m > 9 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Index out of range [0-9]",
        ));
    }
    let code = (d as u16) * 100 + (p as u16) * 10 + (m as u16);
    let name = format!("ARM64-{}-{}-{}", get_arm64_domain_str(d), p, m); // Simplificando por entropía

    matrix.execution_count += 1;
    matrix.pac_bypass_entropy = ((code as f64) * 0.01).sin().abs();
    matrix.dyld_cache_hit_rate = ((code as f64) * 0.02).cos().abs();
    matrix.amfi_enforcement_level = 1.0 / (1.0 + matrix.pac_bypass_entropy);

    Ok((code, name, matrix.compute_re_entropy()))
}
