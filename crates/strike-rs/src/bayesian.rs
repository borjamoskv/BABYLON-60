// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
//! Axiom 4: Constructive Bayesian Disintegration & Non-Hallucination
//!
//! Enforces:
//! 1. Joint probability symmetry: p x f = (p f) x f^\dagger_p
//! 2. Support non-hallucination invariant: supp(f^\dagger_p(y)) <= supp(p)
//! 3. Split Epi reduction under deterministic incommensurability collapse.

use std::collections::{HashMap, HashSet};

/// Stochastic morphism f: X -> Y defined by a transition matrix P(Y|X).
#[derive(Debug, Clone)]
pub struct FiniteMarkovKernel {
    pub x_states: HashSet<String>,
    pub y_states: HashSet<String>,
    pub matrix: HashMap<(String, String), f64>,
}

#[derive(Debug, Clone, PartialEq)]
pub enum DisintegrationError {
    HallucinatedOrigin(HashSet<String>),
    JointAsymmetry,
}

impl FiniteMarkovKernel {
    pub fn new(x_states: HashSet<String>, y_states: HashSet<String>, matrix: HashMap<(String, String), f64>) -> Self {
        Self { x_states, y_states, matrix }
    }

    /// Compute the pushforward distribution p * f on Y.
    pub fn apply_prior(&self, p: &HashMap<String, f64>) -> HashMap<String, f64> {
        let mut pf = HashMap::new();
        for y in &self.y_states {
            pf.insert(y.clone(), 0.0);
        }

        for (x, prob_x) in p {
            if *prob_x > 0.0 {
                for y in &self.y_states {
                    let transition_prob = self.matrix.get(&(x.clone(), y.clone())).copied().unwrap_or(0.0);
                    *pf.get_mut(y).unwrap() += prob_x * transition_prob;
                }
            }
        }
        pf
    }

    /// Constructive Bayesian Disintegration f^\dagger_p: Y -> X.
    /// Computes P(X=x | Y=y) = P(Y=y | X=x) * p(x) / (p f)(y).
    /// Enforces supp(f^\dagger_p(y)) <= supp(p) (Axiom 4.3).
    pub fn disintegrate(&self, p: &HashMap<String, f64>) -> Result<HashMap<(String, String), f64>, DisintegrationError> {
        let pf = self.apply_prior(p);
        
        let mut prior_supp = HashSet::new();
        for (x, prob) in p {
            if *prob > 0.0 {
                prior_supp.insert(x.clone());
            }
        }

        let mut f_dagger = HashMap::new();
        let mut hallucinated_origins = HashSet::new();

        for y in &self.y_states {
            let py = pf.get(y).copied().unwrap_or(0.0);
            
            for x in &self.x_states {
                if py > 0.0 {
                    if prior_supp.contains(x) {
                        let prob_xy = self.matrix.get(&(x.clone(), y.clone())).copied().unwrap_or(0.0) * p.get(x).copied().unwrap_or(0.0);
                        f_dagger.insert((y.clone(), x.clone()), prob_xy / py);
                    } else {
                        // Non-hallucination invariant: force 0 outside prior support
                        f_dagger.insert((y.clone(), x.clone()), 0.0);
                        
                        // If the kernel matrix assigned a non-zero probability outside the prior,
                        // this violates the support subset invariant if it were allowed. 
                        // But since we forcibly set it to 0.0, we just track if the source tried to hallucinate.
                        let prob_xy = self.matrix.get(&(x.clone(), y.clone())).copied().unwrap_or(0.0) * p.get(x).copied().unwrap_or(0.0);
                        if prob_xy > 0.0 {
                            hallucinated_origins.insert(x.clone());
                        }
                    }
                } else {
                    // Observation outside image: zero distribution (circuit breaker)
                    f_dagger.insert((y.clone(), x.clone()), 0.0);
                }
            }
        }

        if !hallucinated_origins.is_empty() {
            return Err(DisintegrationError::HallucinatedOrigin(hallucinated_origins));
        }

        // Verify Axiom 4.1 Joint Probability Symmetry: p x f = (p f) x f^\dagger_p
        for x in &self.x_states {
            for y in &self.y_states {
                let joint_left = p.get(x).copied().unwrap_or(0.0) * self.matrix.get(&(x.clone(), y.clone())).copied().unwrap_or(0.0);
                let joint_right = pf.get(y).copied().unwrap_or(0.0) * f_dagger.get(&(y.clone(), x.clone())).copied().unwrap_or(0.0);
                
                if (joint_left - joint_right).abs() > 1e-6 {
                    return Err(DisintegrationError::JointAsymmetry);
                }
            }
        }

        Ok(f_dagger)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_disintegration_engine() {
        let mut x_states = HashSet::new();
        x_states.insert("state_A".to_string());
        x_states.insert("state_B".to_string());
        x_states.insert("state_C".to_string());

        let mut y_states = HashSet::new();
        y_states.insert("obs_1".to_string());
        y_states.insert("obs_2".to_string());

        let mut p = HashMap::new();
        p.insert("state_A".to_string(), 0.7);
        p.insert("state_B".to_string(), 0.3);
        p.insert("state_C".to_string(), 0.0);

        let mut matrix = HashMap::new();
        matrix.insert(("state_A".to_string(), "obs_1".to_string()), 0.8);
        matrix.insert(("state_A".to_string(), "obs_2".to_string()), 0.2);
        matrix.insert(("state_B".to_string(), "obs_1".to_string()), 0.1);
        matrix.insert(("state_B".to_string(), "obs_2".to_string()), 0.9);
        matrix.insert(("state_C".to_string(), "obs_1".to_string()), 0.5);
        matrix.insert(("state_C".to_string(), "obs_2".to_string()), 0.5);

        let kernel = FiniteMarkovKernel::new(x_states, y_states, matrix);
        
        let pf = kernel.apply_prior(&p);
        assert!((pf.get("obs_1").unwrap() - 0.59).abs() < 1e-6);
        assert!((pf.get("obs_2").unwrap() - 0.41).abs() < 1e-6);

        let f_dagger = kernel.disintegrate(&p).expect("Disintegration should succeed without hallucinations");
        
        // P(state_A | obs_1) = (0.8 * 0.7) / 0.59 = 0.9491...
        let p_a_given_1 = f_dagger.get(&("obs_1".to_string(), "state_A".to_string())).unwrap();
        assert!((*p_a_given_1 - 0.949152).abs() < 1e-5);
    }
}
