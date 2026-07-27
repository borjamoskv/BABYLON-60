use k2_shared::KineticRouterError;
use crate::storage::InterestRateParams;
use k2_shared::RAY;

/// Maximum total interest rate (base + slope1 + slope2) to prevent overflow
/// Set to 20 * RAY (2000% APR) as a reasonable upper bound
const MAX_TOTAL_RATE: u128 = 20 * RAY;

/// Maximum individual component rate (10 * RAY = 1000% APR)
const MAX_COMPONENT_RATE: u128 = 10 * RAY;

pub fn validate_interest_rate_params(params: &InterestRateParams) -> Result<(), KineticRouterError> {
    // 1. Validate optimal_utilization_rate: must be strictly between 0 and RAY
    //    Prevents degenerate curves where optimal = 0 (single branch) or optimal = RAY (no second branch)
    if params.optimal_utilization_rate == 0 || params.optimal_utilization_rate >= RAY {
        return Err(KineticRouterError::InvalidAmount);
    }

    // 2. Validate individual component bounds
    if params.base_variable_borrow_rate > MAX_COMPONENT_RATE {
        return Err(KineticRouterError::InvalidAmount);
    }

    if params.variable_rate_slope1 > MAX_COMPONENT_RATE
        || params.variable_rate_slope2 > MAX_COMPONENT_RATE
    {
        return Err(KineticRouterError::InvalidAmount);
    }

    // 3. Validate non-zero slopes to ensure curve has meaningful shape
    if params.variable_rate_slope1 == 0 || params.variable_rate_slope2 == 0 {
        return Err(KineticRouterError::InvalidAmount);
    }

    // 4. Validate monotonic curve: slope2 >= slope1
    //    Ensures interest rates increase (or stay constant) after optimal utilization
    //    Prevents mispricing where rates decrease at high utilization
    if params.variable_rate_slope2 < params.variable_rate_slope1 {
        return Err(KineticRouterError::InvalidAmount);
    }

    // 5. Validate total rate cap to prevent overflow in downstream calculations
    //    Protects against extreme configurations that could cause arithmetic overflow
    let total_rate = params
        .base_variable_borrow_rate
        .saturating_add(params.variable_rate_slope1)
        .saturating_add(params.variable_rate_slope2);
    
    if total_rate > MAX_TOTAL_RATE {
        return Err(KineticRouterError::InvalidAmount);
    }

    Ok(())
}
