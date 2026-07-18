use pyo3::prelude::*;

// ==========================================
// STATIC ONTOLOGY DICTIONARIES (STRING MAPPINGS)
// ==========================================

fn get_domain_str(d: u8) -> &'static str {
    match d {
        0 => "SOURCE",
        1 => "MATRIX",
        2 => "PULSE",
        3 => "KINETIC",
        4 => "LOGIC",
        5 => "VECTOR",
        6 => "STORAGE",
        7 => "OSINT",
        8 => "CLOCK",
        9 => "COMPILER",
        _ => "UNKNOWN",
    }
}

fn get_primitive_str(p: u8) -> &'static str {
    match p {
        0 => "INIT",
        1 => "PREDICT",
        2 => "UPDATE",
        3 => "INNOVATION",
        4 => "GAIN",
        5 => "COVARIANCE",
        6 => "DRIFT_CHECK",
        7 => "RECONSTRUCT",
        8 => "SANITY_ASSERT",
        9 => "FLUSH_LEDGER",
        _ => "UNKNOWN",
    }
}

fn get_modifier_str(m: u8) -> &'static str {
    match m {
        0 => "RAW",
        1 => "ATOMIC",
        2 => "KALMAN_EXTENDED",
        3 => "LUENBERGER_RIGID",
        4 => "PARTICLE_PF",
        5 => "SLIDING_MODE",
        6 => "QUANTIZED",
        7 => "ADAPTIVE_R",
        8 => "NEURAL_LATENT",
        9 => "BFT_CONSENSUS",
        _ => "UNKNOWN",
    }
}

fn get_neuro_domain_str(d: u8) -> &'static str {
    match d {
        0 => "ENERGY_BOUND",
        1 => "ATTRACTOR_DECAY",
        2 => "COGNITIVE_DRIFT",
        3 => "RESOURCE_EXHAUST",
        4 => "SYBIL_REVERB",
        5 => "BAYESIAN_FREE_ENERGY",
        6 => "LATENT_TORQUE",
        7 => "SURPRISAL_GATE",
        8 => "TEMPORAL_PHASE",
        9 => "DEEP_MCTS_DEPTH",
        _ => "UNKNOWN",
    }
}

fn get_neuro_primitive_str(p: u8) -> &'static str {
    match p {
        0 => "HOMEOSTASIS_INIT",
        1 => "HOMEOSTASIS_MUTATE",
        2 => "PREDICTION_GENERATE",
        3 => "PREDICTION_AUDIT",
        4 => "ATTENTION_FOCUS",
        5 => "ATTENTION_QUANTIZE",
        6 => "ACTION_DISPATCH",
        7 => "ACTION_ASSERT",
        8 => "LANGUAGE_COLLAPSE",
        9 => "LANGUAGE_FLUSH",
        _ => "UNKNOWN",
    }
}

fn get_neuro_modifier_str(m: u8) -> &'static str {
    match m {
        0 => "RAW",
        1 => "ATOMIC",
        2 => "ACTIVE_INFERENCE",
        3 => "LYAPUNOV_STABLE",
        4 => "SPARSE_KV",
        5 => "BFT_CONSENSUS",
        6 => "FEEDFORWARD",
        7 => "BACKPROP_ERROR",
        8 => "SLIDING_SURFACE",
        9 => "EPIDEMIC_PURGE",
        _ => "UNKNOWN",
    }
}

fn get_tts_domain_str(d: u8) -> &'static str {
    match d {
        0 => "ENTROPY_ALLOC",
        1 => "LATENT_LOOKAHEAD",
        2 => "POLICY_IMPROVE",
        3 => "HARNESS_DISCOVERY",
        4 => "PROGRAMMATIC_JIT",
        5 => "SWARM_GRAPH",
        6 => "TRI_TIER_MEMORY",
        7 => "INFO_KV_EVICTION",
        8 => "STAGE_DECOUPLE",
        9 => "VECTOR_QUANT",
        _ => "UNKNOWN",
    }
}

fn get_tts_primitive_str(p: u8) -> &'static str {
    match p {
        0 => "INIT",
        1 => "EXPAND",
        2 => "EVALUATE",
        3 => "BACKPROP",
        4 => "PRUNE",
        5 => "QUANTIZE",
        6 => "ASSERT_BFT",
        7 => "EXECUTE_SANDBOX",
        8 => "RECONSTRUCT_STATE",
        9 => "FLUSH_LEDGER",
        _ => "UNKNOWN",
    }
}

fn get_tts_modifier_str(m: u8) -> &'static str {
    match m {
        0 => "RAW",
        1 => "ATOMIC",
        2 => "ADAPTIVE_COT",
        3 => "RETRO_ATTENTION",
        4 => "FORWARD_INFLUENCE",
        5 => "TURBO_QUANT",
        6 => "META_PROPOSER",
        7 => "FEEDFORWARD_OPEN",
        8 => "SLIDING_WINDOW",
        9 => "EPIDEMIC_PURGE",
        _ => "UNKNOWN",
    }
}

// ==========================================
// 1. STATE OBSERVER VECTOR
// ==========================================

#[pyclass]
#[derive(Clone, Debug)]
pub struct StateVector {
    #[pyo3(get, set)]
    pub states: Vec<f64>,
    #[pyo3(get, set)]
    pub covariance: Vec<Vec<f64>>,
    #[pyo3(get, set)]
    pub innovation: Vec<f64>,
    #[pyo3(get, set)]
    pub norm_error: f64,
    #[pyo3(get, set)]
    pub execution_count: u64,
}

#[pymethods]
impl StateVector {
    #[new]
    pub fn new() -> Self {
        Self {
            states: vec![0.0; 4],
            covariance: vec![
                vec![1.0, 0.0, 0.0, 0.0],
                vec![0.0, 1.0, 0.0, 0.0],
                vec![0.0, 0.0, 1.0, 0.0],
                vec![0.0, 0.0, 0.0, 1.0],
            ],
            innovation: vec![0.0; 4],
            norm_error: 0.0,
            execution_count: 0,
        }
    }
}
impl Default for StateVector {
    fn default() -> Self {
        Self::new()
    }
}

// ==========================================
// 2. COGNITIVE CHAIN VECTOR
// ==========================================

#[pyclass]
#[derive(Clone, Debug)]
pub struct CognitiveChainVector {
    #[pyo3(get, set)]
    pub homeostasis_energy: f64,
    #[pyo3(get, set)]
    pub prediction_error: f64,
    #[pyo3(get, set)]
    pub attention_weight: f64,
    #[pyo3(get, set)]
    pub action_torque: f64,
    #[pyo3(get, set)]
    pub language_entropy: f64,
    #[pyo3(get, set)]
    pub execution_count: u64,
}

#[pymethods]
impl CognitiveChainVector {
    #[new]
    pub fn new() -> Self {
        Self {
            homeostasis_energy: 1.0,
            prediction_error: 0.0,
            attention_weight: 1.0,
            action_torque: 0.0,
            language_entropy: 0.0,
            execution_count: 0,
        }
    }
}
impl Default for CognitiveChainVector {
    fn default() -> Self {
        Self::new()
    }
}

// ==========================================
// 3. TTS HARNESS STATE
// ==========================================

#[pyclass]
#[derive(Clone, Debug)]
pub struct TTSHarnessState {
    #[pyo3(get, set)]
    pub mcts_budget_tokens: i64,
    #[pyo3(get, set)]
    pub latent_value: f64,
    #[pyo3(get, set)]
    pub harness_score: f64,
    #[pyo3(get, set)]
    pub kv_cache_efficiency: f64,
    #[pyo3(get, set)]
    pub pruning_rate: f64,
    #[pyo3(get, set)]
    pub execution_count: u64,
}

#[pymethods]
impl TTSHarnessState {
    #[new]
    pub fn new() -> Self {
        Self {
            mcts_budget_tokens: 0,
            latent_value: 0.0,
            harness_score: 0.0,
            kv_cache_efficiency: 1.0,
            pruning_rate: 0.0,
            execution_count: 0,
        }
    }
}
impl Default for TTSHarnessState {
    fn default() -> Self {
        Self::new()
    }
}

// ==========================================
// DISPATCH ENGINE FUNCTION IMPLEMENTATIONS
// ==========================================

/// Dispatches an observation step on the StateVector given domain d, primitive p, and modifier m.
#[pyfunction]
pub fn dispatch_state_observer(
    d: u8,
    p: u8,
    m: u8,
    mut state: PyRefMut<StateVector>,
) -> PyResult<(u16, String, f64)> {
    if d > 9 || p > 9 || m > 9 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Index out of range [0-9]",
        ));
    }
    let code = (d as u16) * 100 + (p as u16) * 10 + (m as u16);
    let name = format!(
        "OBS-{}-{}-{}",
        get_domain_str(d),
        get_primitive_str(p),
        get_modifier_str(m)
    );

    state.execution_count += 1;
    let mut sum_sq = 0.0;
    if state.states.len() < 4 || state.innovation.len() < 4 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "StateVector arrays states/innovation must have length >= 4",
        ));
    }
    for i in 0..4 {
        state.states[i] += ((code as f64) + (i as f64)).sin() * 0.01;
        state.innovation[i] = ((code as f64).cos() - state.states[i]) * 0.1;
        sum_sq += state.innovation[i] * state.innovation[i];
    }
    state.norm_error = sum_sq.sqrt();
    Ok((code, name, state.norm_error))
}

/// Dispatches a neuro-chain mutation step on the CognitiveChainVector.
#[pyfunction]
pub fn dispatch_neuro_chain(
    d: u8,
    p: u8,
    m: u8,
    mut vec: PyRefMut<CognitiveChainVector>,
) -> PyResult<(u16, String, f64)> {
    if d > 9 || p > 9 || m > 9 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Index out of range [0-9]",
        ));
    }
    let code = (d as u16) * 100 + (p as u16) * 10 + (m as u16);
    let name = format!(
        "NEURO-{}-{}-{}",
        get_neuro_domain_str(d),
        get_neuro_primitive_str(p),
        get_neuro_modifier_str(m)
    );

    vec.execution_count += 1;
    let cos_val = (code as f64).cos();
    vec.homeostasis_energy = f64::max(0.01, vec.homeostasis_energy * 0.98 + 0.02 * cos_val);
    vec.prediction_error = ((code as f64).sin() * 0.1 - vec.homeostasis_energy * 0.05).abs();
    vec.attention_weight = 1.0 / (1.0 + vec.prediction_error);
    vec.action_torque = vec.attention_weight * (((code % 10) as f64) + 1.0);
    vec.language_entropy = (1.0 + vec.action_torque).log2();

    Ok((code, name, vec.language_entropy))
}

/// Dispatches a TTS harness evaluation step on the TTSHarnessState.
#[pyfunction]
pub fn dispatch_tts_harness(
    d: u8,
    p: u8,
    m: u8,
    mut state: PyRefMut<TTSHarnessState>,
) -> PyResult<(u16, String, f64)> {
    if d > 9 || p > 9 || m > 9 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Index out of range [0-9]",
        ));
    }
    let code = (d as u16) * 100 + (p as u16) * 10 + (m as u16);
    let name = format!(
        "TTS-{}-{}-{}",
        get_tts_domain_str(d),
        get_tts_primitive_str(p),
        get_tts_modifier_str(m)
    );

    state.execution_count += 1;
    state.mcts_budget_tokens += ((code % 50) as i64) + 10;
    state.latent_value = ((code as f64) * 0.001).tanh();
    state.harness_score = 0.5 + 0.5 * ((code as f64).sin());
    state.kv_cache_efficiency = f64::min(1.0, 0.2 + ((code % 10) as f64) * 0.08);
    state.pruning_rate = 1.0 - state.kv_cache_efficiency * 0.5;

    Ok((code, name, state.harness_score))
}

mod arm64_re;
use arm64_re::{dispatch_arm64_re, Arm64ReMatrix};

// ==========================================
// PYMOD PYFUNCTION SIGNATURE
// ==========================================

#[pymodule]
fn strike_rs(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<StateVector>()?;
    m.add_class::<CognitiveChainVector>()?;
    m.add_class::<TTSHarnessState>()?;
    m.add_class::<Arm64ReMatrix>()?;
    m.add_function(wrap_pyfunction!(dispatch_state_observer, m)?)?;
    m.add_function(wrap_pyfunction!(dispatch_neuro_chain, m)?)?;
    m.add_function(wrap_pyfunction!(dispatch_tts_harness, m)?)?;
    m.add_function(wrap_pyfunction!(dispatch_arm64_re, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    // strike-rs lib is a PyO3 cdylib — pure Rust logic (state machines, math)
    // tested without Python runtime via direct function calls.

    use super::*;

    // ── Static string dictionaries ────────────────────────────────────────────

    #[test]
    fn get_domain_str_all_valid() {
        let expected = [
            "SOURCE", "MATRIX", "PULSE", "KINETIC", "LOGIC", "VECTOR", "STORAGE", "OSINT", "CLOCK",
            "COMPILER",
        ];
        for (i, &label) in expected.iter().enumerate() {
            assert_eq!(get_domain_str(i as u8), label);
        }
    }

    #[test]
    fn get_domain_str_oob_returns_unknown() {
        assert_eq!(get_domain_str(10), "UNKNOWN");
        assert_eq!(get_domain_str(255), "UNKNOWN");
    }

    #[test]
    fn get_primitive_str_all_valid() {
        let expected = [
            "INIT",
            "PREDICT",
            "UPDATE",
            "INNOVATION",
            "GAIN",
            "COVARIANCE",
            "DRIFT_CHECK",
            "RECONSTRUCT",
            "SANITY_ASSERT",
            "FLUSH_LEDGER",
        ];
        for (i, &label) in expected.iter().enumerate() {
            assert_eq!(get_primitive_str(i as u8), label);
        }
    }

    #[test]
    fn get_modifier_str_all_valid() {
        let expected = [
            "RAW",
            "ATOMIC",
            "KALMAN_EXTENDED",
            "LUENBERGER_RIGID",
            "PARTICLE_PF",
            "SLIDING_MODE",
            "QUANTIZED",
            "ADAPTIVE_R",
            "NEURAL_LATENT",
            "BFT_CONSENSUS",
        ];
        for (i, &label) in expected.iter().enumerate() {
            assert_eq!(get_modifier_str(i as u8), label);
        }
    }

    #[test]
    fn get_neuro_domain_str_all_valid() {
        let expected = [
            "ENERGY_BOUND",
            "ATTRACTOR_DECAY",
            "COGNITIVE_DRIFT",
            "RESOURCE_EXHAUST",
            "SYBIL_REVERB",
            "BAYESIAN_FREE_ENERGY",
            "LATENT_TORQUE",
            "SURPRISAL_GATE",
            "TEMPORAL_PHASE",
            "DEEP_MCTS_DEPTH",
        ];
        for (i, &label) in expected.iter().enumerate() {
            assert_eq!(get_neuro_domain_str(i as u8), label);
        }
    }

    #[test]
    fn get_neuro_primitive_str_all_valid() {
        let expected = [
            "HOMEOSTASIS_INIT",
            "HOMEOSTASIS_MUTATE",
            "PREDICTION_GENERATE",
            "PREDICTION_AUDIT",
            "ATTENTION_FOCUS",
            "ATTENTION_QUANTIZE",
            "ACTION_DISPATCH",
            "ACTION_ASSERT",
            "LANGUAGE_COLLAPSE",
            "LANGUAGE_FLUSH",
        ];
        for (i, &label) in expected.iter().enumerate() {
            assert_eq!(get_neuro_primitive_str(i as u8), label);
        }
    }

    #[test]
    fn get_neuro_modifier_str_all_valid() {
        let expected = [
            "RAW",
            "ATOMIC",
            "ACTIVE_INFERENCE",
            "LYAPUNOV_STABLE",
            "SPARSE_KV",
            "BFT_CONSENSUS",
            "FEEDFORWARD",
            "BACKPROP_ERROR",
            "SLIDING_SURFACE",
            "EPIDEMIC_PURGE",
        ];
        for (i, &label) in expected.iter().enumerate() {
            assert_eq!(get_neuro_modifier_str(i as u8), label);
        }
    }

    #[test]
    fn get_tts_domain_str_all_valid() {
        let expected = [
            "ENTROPY_ALLOC",
            "LATENT_LOOKAHEAD",
            "POLICY_IMPROVE",
            "HARNESS_DISCOVERY",
            "PROGRAMMATIC_JIT",
            "SWARM_GRAPH",
            "TRI_TIER_MEMORY",
            "INFO_KV_EVICTION",
            "STAGE_DECOUPLE",
            "VECTOR_QUANT",
        ];
        for (i, &label) in expected.iter().enumerate() {
            assert_eq!(get_tts_domain_str(i as u8), label);
        }
    }

    #[test]
    fn get_tts_primitive_str_all_valid() {
        let expected = [
            "INIT",
            "EXPAND",
            "EVALUATE",
            "BACKPROP",
            "PRUNE",
            "QUANTIZE",
            "ASSERT_BFT",
            "EXECUTE_SANDBOX",
            "RECONSTRUCT_STATE",
            "FLUSH_LEDGER",
        ];
        for (i, &label) in expected.iter().enumerate() {
            assert_eq!(get_tts_primitive_str(i as u8), label);
        }
    }

    #[test]
    fn get_tts_modifier_str_all_valid() {
        let expected = [
            "RAW",
            "ATOMIC",
            "ADAPTIVE_COT",
            "RETRO_ATTENTION",
            "FORWARD_INFLUENCE",
            "TURBO_QUANT",
            "META_PROPOSER",
            "FEEDFORWARD_OPEN",
            "SLIDING_WINDOW",
            "EPIDEMIC_PURGE",
        ];
        for (i, &label) in expected.iter().enumerate() {
            assert_eq!(get_tts_modifier_str(i as u8), label);
        }
    }

    // ── StateVector pure logic ────────────────────────────────────────────────

    #[test]
    fn state_vector_initial_values() {
        let sv = StateVector::new();
        assert_eq!(sv.states.len(), 4);
        assert!(sv.states.iter().all(|&x| x == 0.0));
        assert_eq!(sv.norm_error, 0.0);
        assert_eq!(sv.execution_count, 0);
        // identity covariance
        for (i, row) in sv.covariance.iter().enumerate() {
            for (j, &v) in row.iter().enumerate() {
                let expected = if i == j { 1.0 } else { 0.0 };
                assert_eq!(v, expected, "cov[{i}][{j}] mismatch");
            }
        }
    }

    // ── CognitiveChainVector pure logic ───────────────────────────────────────

    #[test]
    fn cognitive_chain_vector_initial_values() {
        let cv = CognitiveChainVector::new();
        assert_eq!(cv.homeostasis_energy, 1.0);
        assert_eq!(cv.prediction_error, 0.0);
        assert_eq!(cv.attention_weight, 1.0);
        assert_eq!(cv.action_torque, 0.0);
        assert_eq!(cv.language_entropy, 0.0);
        assert_eq!(cv.execution_count, 0);
    }

    // ── TTSHarnessState pure logic ────────────────────────────────────────────

    #[test]
    fn tts_harness_state_initial_values() {
        let ts = TTSHarnessState::new();
        assert_eq!(ts.mcts_budget_tokens, 0);
        assert_eq!(ts.latent_value, 0.0);
        assert_eq!(ts.harness_score, 0.0);
        assert_eq!(ts.kv_cache_efficiency, 1.0);
        assert_eq!(ts.pruning_rate, 0.0);
        assert_eq!(ts.execution_count, 0);
    }
}
