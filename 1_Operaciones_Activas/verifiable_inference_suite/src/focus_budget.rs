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
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AdmissionVerdict {
    Admitted,
    RejectedTokenLimitExceeded,
    RejectedCostLimitExceeded,
    RejectedTimeLimitExceeded,
    RejectedToolCallLimitExceeded,
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
        };

        let verdict = controller.evaluate_admission(&tracker, 500, 50_000); // Total cost 530k > max 500k
        assert_eq!(verdict, AdmissionVerdict::RejectedCostLimitExceeded);
    }
}
