// C5-REAL EXERGY CERTIFIED
//! FOCUS (FinOps Open Cost & Usage Specification) Discrete Budget Controller
//! Enforces strict 4D admission bounds (Tokens, USD Microcents, Wall-Clock ms, Tool Calls)
//! prior to transition execution, rejecting continuous topology metaphors.

#[derive(Debug, Clone)]
pub struct FOCUSBudgetLimits {
    pub max_tokens: usize,
    pub max_usd_micros: u64,
    pub max_wall_clock_ms: u64,
    pub max_tool_calls: usize,
}

impl Default for FOCUSBudgetLimits {
    fn default() -> Self {
        Self {
            max_tokens: 100_000,
            max_usd_micros: 500_000, // 0.50 USD in microcents
            max_wall_clock_ms: 10_000,
            max_tool_calls: 20,
        }
    }
}

#[derive(Debug, Clone)]
pub struct FOCUSUsageTracker {
    pub current_tokens: usize,
    pub current_usd_micros: u64,
    pub current_wall_clock_ms: u64,
    pub current_tool_calls: usize,
    pub current_landauer_nats: f64,
}

impl Default for FOCUSUsageTracker {
    fn default() -> Self {
        Self {
            current_tokens: 0,
            current_usd_micros: 0,
            current_wall_clock_ms: 0,
            current_tool_calls: 0,
            current_landauer_nats: 0.0,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AdmissionVerdict {
    Admitted,
    RejectedTokenLimitExceeded,
    RejectedCostLimitExceeded,
    RejectedTimeLimitExceeded,
    RejectedToolCallLimitExceeded,
    RejectedLandauerEnergyExceeded,
}

pub struct FOCUSBudgetController {
    limits: FOCUSBudgetLimits,
}

impl FOCUSBudgetController {
    pub fn new(limits: FOCUSBudgetLimits) -> Self {
        Self { limits }
    }

    /// Evaluates admissibility of a requested transition against FOCUS 4D discrete budget limits
    pub fn evaluate_admission(&self, usage: &FOCUSUsageTracker, est_tokens: usize, est_cost_micros: u64) -> AdmissionVerdict {
        if usage.current_tokens + est_tokens > self.limits.max_tokens {
            return AdmissionVerdict::RejectedTokenLimitExceeded;
        }
        if usage.current_usd_micros + est_cost_micros > self.limits.max_usd_micros {
            return AdmissionVerdict::RejectedCostLimitExceeded;
        }
        if usage.current_wall_clock_ms >= self.limits.max_wall_clock_ms {
            return AdmissionVerdict::RejectedTimeLimitExceeded;
        }
        if usage.current_tool_calls >= self.limits.max_tool_calls {
            return AdmissionVerdict::RejectedToolCallLimitExceeded;
        }
        AdmissionVerdict::Admitted
    }

    /// Consume atómicamente un paso de ejecución si la admisión es aprobada.
    /// Calcula la disipación mínima de entropía (Límite de Landauer: 1 bit borrado = ln(2) nats).
    pub fn consume(&self, usage: &mut FOCUSUsageTracker, est_tokens: usize, est_cost_micros: u64, duration_ms: u64, is_tool_call: bool) -> Result<(), AdmissionVerdict> {
        let verdict = self.evaluate_admission(usage, est_tokens, est_cost_micros);
        if verdict != AdmissionVerdict::Admitted {
            return Err(verdict);
        }

        usage.current_tokens += est_tokens;
        usage.current_usd_micros += est_cost_micros;
        usage.current_wall_clock_ms += duration_ms;
        if is_tool_call {
            usage.current_tool_calls += 1;
        }
        // Disipación de Landauer: k_B * T * ln(2) por bit purgado. 1 token ~= 4 bits.
        usage.current_landauer_nats += (est_tokens * 4) as f64 * std::f64::consts::LN_2;

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_focus_budget_admission_approved() {
        let controller = FOCUSBudgetController::new(FOCUSBudgetLimits::default());
        let tracker = FOCUSUsageTracker {
            current_tokens: 1_000,
            current_usd_micros: 10_000,
            current_wall_clock_ms: 200,
            current_tool_calls: 1,
            current_landauer_nats: 0.0,
        };

        let verdict = controller.evaluate_admission(&tracker, 500, 5_000);
        assert_eq!(verdict, AdmissionVerdict::Admitted);
    }

    #[test]
    fn test_focus_budget_admission_rejected_cost() {
        let controller = FOCUSBudgetController::new(FOCUSBudgetLimits::default());
        let tracker = FOCUSUsageTracker {
            current_tokens: 1_000,
            current_usd_micros: 480_000,
            current_wall_clock_ms: 200,
            current_tool_calls: 1,
            current_landauer_nats: 0.0,
        };

        let verdict = controller.evaluate_admission(&tracker, 500, 50_000); // Total cost 530k > max 500k
        assert_eq!(verdict, AdmissionVerdict::RejectedCostLimitExceeded);
    }

    #[test]
    fn test_focus_budget_consume_updates_tracker_and_landauer() {
        let controller = FOCUSBudgetController::new(FOCUSBudgetLimits::default());
        let mut tracker = FOCUSUsageTracker::default();

        let result = controller.consume(&mut tracker, 100, 1_000, 50, true);
        assert!(result.is_ok());
        assert_eq!(tracker.current_tokens, 100);
        assert_eq!(tracker.current_usd_micros, 1_000);
        assert_eq!(tracker.current_wall_clock_ms, 50);
        assert_eq!(tracker.current_tool_calls, 1);
        assert!(tracker.current_landauer_nats > 0.0);
    }
}
