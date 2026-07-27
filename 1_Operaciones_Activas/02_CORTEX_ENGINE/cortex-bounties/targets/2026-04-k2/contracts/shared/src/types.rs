use soroban_sdk::{contracttype, Address, String, Symbol, Vec};

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ReserveData {
    pub liquidity_index: u128,
    pub variable_borrow_index: u128,
    pub current_liquidity_rate: u128,
    pub current_variable_borrow_rate: u128,
    pub last_update_timestamp: u64,
    pub a_token_address: Address,
    pub debt_token_address: Address,
    pub interest_rate_strategy_address: Address,
    pub id: u32,
    pub configuration: ReserveConfiguration,
}

/// Bitmap layout:
/// data_low: LTV (0-13), liquidation_threshold (14-27), liquidation_bonus (28-41),
///          decimals (42-49), flags (50-56), reserve_factor (57-70)
/// data_high: borrow_cap (0-63), supply_cap (64-127)
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ReserveConfiguration {
    pub data_low: u128,
    pub data_high: u128,
}

/// Bitmap: each pair of bits = [collateral, borrowed] for reserve index
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct UserConfiguration {
    pub data: u128,
}

/// Isolation mode configuration
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct IsolationModeData {
    /// Maximum debt ceiling for isolated asset
    pub debt_ceiling: u128,
    /// Current total debt for isolated asset
    pub total_debt: u128,
    /// Whether isolation mode is enabled
    pub isolation_mode_enabled: bool,
}

/// Interest rate calculation parameters
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct InterestRateData {
    /// Available liquidity in the reserve
    pub available_liquidity: u128,
    /// Total variable debt
    pub total_variable_debt: u128,
    /// Reserve factor
    pub reserve_factor: u128,
}

/// Liquidation call parameters
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct LiquidationCallParams {
    /// Collateral asset to liquidate
    pub collateral_asset: Address,
    /// Debt asset to repay
    pub debt_asset: Address,
    /// User being liquidated
    pub user: Address,
    /// Amount of debt to cover
    pub debt_to_cover: u128,
    /// Whether to receive aToken or underlying asset
    pub receive_a_token: bool,
}

/// Flash loan parameters
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FlashLoanParams {
    /// Assets to flash loan
    pub assets: Vec<Address>,
    /// Amounts to flash loan
    pub amounts: Vec<u128>,
    /// Interest rate modes (0 = no open debt, 1 = variable)
    pub modes: Vec<u32>,
    /// User on whose behalf the flash loan is taken
    pub on_behalf_of: Address,
    /// Additional parameters for flash loan callback
    pub params: soroban_sdk::Bytes,
}

/// Flash loan fee configuration
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FlashLoanConfig {
    /// Flash loan fee in basis points (e.g., 30 = 0.3%)
    pub fee_bps: u32,
    /// Flash loan premium percentage (total to protocol)
    pub premium_total: u128,
    /// Flash loan premium to protocol (vs LP suppliers)
    pub premium_to_protocol: u128,
}

/// User account data
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct UserAccountData {
    /// Total collateral in base currency
    pub total_collateral_base: u128,
    /// Total debt in base currency
    pub total_debt_base: u128,
    /// Available borrows in base currency
    pub available_borrows_base: u128,
    /// Current liquidation threshold
    pub current_liquidation_threshold: u128,
    /// Loan to value ratio
    pub ltv: u128,
    /// Health factor
    pub health_factor: u128,
}

/// Flash liquidation validation parameters
/// Passed to helper contract to reduce parameter count
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FlashLiquidationValidationParams {
    pub router: Address,
    pub user: Address,
    pub collateral_asset: Address,
    pub debt_asset: Address,
    pub debt_to_cover: u128,
    pub collateral_to_seize: u128,
    pub collateral_price: u128,
    pub debt_price: u128,
    pub debt_reserve: ReserveData,
    pub collateral_reserve: ReserveData,
    pub min_swap_out: u128,
    pub debt_balance: u128,
    pub min_output_bps: u128,
    pub oracle_price_precision: u32,
}

/// Flash liquidation validation result
/// Returned by the flash liquidation helper contract
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FlashLiquidationValidationResult {
    pub collateral_amount_to_seize: u128,
    pub expected_debt_out: u128,
    pub effective_min_out: u128,
    pub debt_to_cover_base: u128,
    pub total_debt_base: u128,
}

/// Calculated interest rates from strategy
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CalculatedRates {
    pub liquidity_rate: u128,
    pub variable_borrow_rate: u128,
}

/// Reserve initialization parameters
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct InitReserveParams {
    /// Number of decimals for the asset
    pub decimals: u32,
    /// Loan to value ratio (in basis points)
    pub ltv: u32,
    /// Liquidation threshold (in basis points)
    pub liquidation_threshold: u32,
    /// Liquidation bonus (in basis points)
    pub liquidation_bonus: u32,
    /// Reserve factor (in basis points)
    pub reserve_factor: u32,
    /// Supply cap in whole tokens (e.g., 1000000 = 1M tokens)
    /// When checking caps, multiply by 10^decimals to get smallest units
    pub supply_cap: u128,
    /// Borrow cap in whole tokens (e.g., 500000 = 500K tokens)
    /// When checking caps, multiply by 10^decimals to get smallest units
    pub borrow_cap: u128,
    /// Whether borrowing is enabled
    pub borrowing_enabled: bool,
    /// Whether flash loans are enabled
    pub flashloan_enabled: bool,
}

// ============================================================================
// ORACLE TYPES
// ============================================================================

/// Asset identifier for price queries
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Asset {
    Stellar(Address), // Stellar-native asset by contract address
    Other(Symbol),    // External assets (BTC, ETH, etc.)
}

/// Price data returned from oracle
#[contracttype]
#[derive(Clone, Debug)]
pub struct PriceData {
    pub price: u128,    // Price with 14 decimal precision (always positive)
    pub timestamp: u64, // Ledger timestamp of price
}

/// Asset configuration for whitelist
#[contracttype]
#[derive(Clone, Debug)]
pub struct AssetConfig {
    pub asset: Asset,
    pub enabled: bool,
    pub manual_override_price: Option<u128>,
    /// Unix timestamp in seconds (matching env.ledger().timestamp()) when manual override expires
    pub override_expiry_timestamp: Option<u64>,
    /// Unix timestamp when the manual override was set (returned as PriceData.timestamp
    /// so downstream staleness checks detect stale overrides). H-01 fix.
    pub override_set_timestamp: Option<u64>,
    pub custom_oracle: Option<Address>,
    /// Maximum age in seconds for custom/batch oracle prices (None = use global staleness threshold)
    pub max_age: Option<u64>,
    /// Cached decimals for the oracle source — skips the decimals() cross-contract call when set
    pub oracle_decimals: Option<u32>,
    /// Batch-capable adapter address (any oracle implementing read_price_data interface)
    pub batch_adapter: Option<Address>,
    /// Feed identifier for the batch adapter (e.g. "BTC", "ETH")
    pub feed_id: Option<String>,
}

/// Oracle configuration settings
#[contracttype]
#[derive(Clone, Debug)]
pub struct OracleConfig {
    pub price_staleness_threshold: u64, // Max age in seconds (default: 3600 = 1 hour)
    pub price_precision: u32,           // Oracle price precision (default: 14)
    pub wad_precision: u32,             // Protocol precision (default: 18)
    pub conversion_factor: u128,        // Factor to convert oracle to WAD (default: 10_000)
    pub ltv_precision: u128,            // LTV calculation precision (default: 1e18)
    pub basis_points: u128,             // Basis points conversion (default: 10_000)
    /// Circuit breaker: max price change between consecutive queries in basis points.
    /// Default: 2000 = 20%. Prevents oracle failures from causing extreme price jumps.
    /// Set to 0 to disable. See L-8 security audit finding.
    pub max_price_change_bps: u32,
}

/// Result of atomic flash liquidation
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct LiquidationResult {
    /// Amount of collateral seized from user
    pub collateral_seized: u128,
    /// Amount of debt repaid
    pub debt_repaid: u128,
    /// Protocol fee charged from liquidation
    pub protocol_fee: u128,
    /// Liquidator's profit after covering debt + fees
    pub profit: u128,
    /// Debt asset address (needed for profit distribution)
    pub debt_asset: Address,
}

/// Soroswap configuration settings
#[contracttype]
#[derive(Clone, Debug)]
pub struct SoroswapConfig {
    pub router_address: Address,
    pub factory_address: Address,
}

/// Internal debt tracking during flash loan execution
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FlashLoanDebt {
    /// Asset being borrowed
    pub asset: Address,
    /// aToken address for the asset
    pub atoken_address: Address,
    /// Total amount owed (principal + premium)
    pub total_owed: u128,
    /// Premium amount only
    pub premium: u128,
    /// Initial balance before flash loan
    pub initial_balance: u128,
}

/// Liquidation callback parameters for flash loan-based liquidation
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct LiquidationCallbackParams {
    /// User being liquidated
    pub user: Address,
    /// Collateral asset to seize
    pub collateral_asset: Address,
    /// Debt asset to repay
    pub debt_asset: Address,
    /// Amount of debt to cover
    pub debt_to_cover: u128,
    /// Collateral amount to seize
    pub collateral_to_seize: u128,
    /// Minimum swap output for slippage protection
    pub min_swap_out: u128,
    /// Deadline timestamp
    pub deadline_ts: u64,
    /// Collateral price from oracle (validated at call time)
    pub collateral_price: u128,
    /// Debt price from oracle (validated at call time)
    pub debt_price: u128,
    /// Liquidator address (receives profit)
    pub liquidator: Address,
    /// Collateral reserve data (cached to avoid re-reads)
    pub collateral_reserve_data: ReserveData,
    /// Debt reserve data (cached to avoid re-reads)
    pub debt_reserve_data: ReserveData,
    /// Optional swap handler for DEX-agnostic swaps
    pub swap_handler: Option<Address>,
}
