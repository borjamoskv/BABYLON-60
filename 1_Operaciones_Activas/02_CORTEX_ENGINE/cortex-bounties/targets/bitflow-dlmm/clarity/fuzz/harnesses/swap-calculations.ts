/**
 * Swap calculation helpers matching pricing.py _calculate_bin_swap API
 * 
 * This module provides functions that replicate the exact logic from
 * pricing.py's _calculate_bin_swap method, ensuring consistency between
 * the Python quote engine and TypeScript test validation.
 * 
 * Reference: pricing.py lines 904-973
 */

const PRICE_SCALE_BPS = 100000000n; // 1e8
const FEE_SCALE_BPS = 10000n; // 1e4

export interface BinData {
  reserve_x: bigint;
  reserve_y: bigint;
}

export interface SwapCalculationResult {
  in_effective: bigint;
  out_this: bigint;
  function_name: 'swap-x-for-y' | 'swap-y-for-x';
  fee_amount: bigint;
}

export interface SwapCalculationResultFloat {
  in_effective: number;
  out_this: number;
  function_name: 'swap-x-for-y' | 'swap-y-for-x';
  fee_amount: number;
}

/**
 * Calculate swap amounts for a single bin using Clarity DLMM math.
 * 
 * This function matches pricing.py's _calculate_bin_swap method exactly.
 * 
 * @param bin_data - Bin data with reserves
 * @param bin_price - Bin price (as BigInt, scaled by PRICE_SCALE_BPS)
 * @param remaining - Remaining amount to swap
 * @param fee_rate_bps - Fee rate in basis points (e.g., 30 = 0.3%)
 * @param swap_for_y - True for X→Y swap, False for Y→X swap
 * @returns Tuple of (in_effective, out_this, function_name, fee_amount)
 */
export function calculateBinSwap(
  bin_data: BinData,
  bin_price: bigint,
  remaining: bigint,
  fee_rate_bps: bigint,
  swap_for_y: boolean
): SwapCalculationResult {
  const reserve_x = bin_data.reserve_x;
  const reserve_y = bin_data.reserve_y;

  if (swap_for_y) {
    // X → Y swap: Following Clarity DLMM math
    // Calculate max X that can be swapped based on available Y
    // Formula: max_x_amount = ((reserve_y * PRICE_SCALE_BPS + (bin_price - 1)) // bin_price)
    // This implements ceiling rounding: (a + b - 1) / b
    const max_x_amount = bin_price > 0n
      ? ((reserve_y * PRICE_SCALE_BPS + (bin_price - 1n)) / bin_price)
      : 0n;

    // Apply fee adjustment to max amount
    // Formula: updated_max_x_amount = (max_x_amount * FEE_SCALE_BPS) / (FEE_SCALE_BPS - fee_rate_bps)
    const updated_max_x_amount = fee_rate_bps > 0n && fee_rate_bps < FEE_SCALE_BPS
      ? (max_x_amount * FEE_SCALE_BPS) / (FEE_SCALE_BPS - fee_rate_bps)
      : max_x_amount;

    // Use the smaller of remaining input or max allowed
    const updated_x_amount = remaining < updated_max_x_amount ? remaining : updated_max_x_amount;

    // Calculate fees using Clarity math: x-amount-fees-total = (updated-x-amount * fee_rate_bps) / FEE_SCALE_BPS
    const x_amount_fees_total = (updated_x_amount * fee_rate_bps) / FEE_SCALE_BPS;
    const dx = updated_x_amount - x_amount_fees_total;

    // Calculate output using DLMM formula: dy = min((dx * bin-price) // PRICE_SCALE_BPS, reserve_y)
    const dy_before_cap = (dx * bin_price) / PRICE_SCALE_BPS;
    const out_this = dy_before_cap > reserve_y ? reserve_y : dy_before_cap;
    const in_effective = updated_x_amount;
    const fee_amount = x_amount_fees_total;

    return {
      in_effective,
      out_this,
      function_name: 'swap-x-for-y',
      fee_amount,
    };
  } else {
    // Y → X swap: Following Clarity DLMM math
    // Calculate max Y that can be swapped based on available X
    // Formula: max_y_amount = ((reserve_x * bin_price + (PRICE_SCALE_BPS - 1)) // PRICE_SCALE_BPS)
    const max_y_amount = ((reserve_x * bin_price + (PRICE_SCALE_BPS - 1n)) / PRICE_SCALE_BPS);

    // Apply fee adjustment to max amount
    // Formula: updated_max_y_amount = (max_y_amount * FEE_SCALE_BPS) / (FEE_SCALE_BPS - fee_rate_bps)
    const updated_max_y_amount = fee_rate_bps > 0n
      ? (max_y_amount * FEE_SCALE_BPS) / (FEE_SCALE_BPS - fee_rate_bps)
      : max_y_amount;

    // Use the smaller of remaining input or max allowed
    const updated_y_amount = remaining < updated_max_y_amount ? remaining : updated_max_y_amount;

    // Calculate fees using Clarity math: y-amount-fees-total = (updated-y-amount * fee_rate_bps) / FEE_SCALE_BPS
    const y_amount_fees_total = (updated_y_amount * fee_rate_bps) / FEE_SCALE_BPS;
    const dy = updated_y_amount - y_amount_fees_total;

    // Calculate output using DLMM formula: dx = min((dy * PRICE_SCALE_BPS) // bin-price, reserve_x)
    const out_this = bin_price > 0n
      ? (() => {
          const dx_before_cap = (dy * PRICE_SCALE_BPS) / bin_price;
          return dx_before_cap > reserve_x ? reserve_x : dx_before_cap;
        })()
      : 0n;
    const in_effective = updated_y_amount;
    const fee_amount = y_amount_fees_total;

    return {
      in_effective,
      out_this,
      function_name: 'swap-y-for-x',
      fee_amount,
    };
  }
}

/**
 * Calculate swap amounts using float math (for comparison with quote engine).
 * 
 * This function provides the "ideal" float-based calculation that the quote engine
 * uses, which we compare against to detect rounding errors and exploits.
 * 
 * @param bin_data - Bin data with reserves
 * @param bin_price - Bin price (as number, scaled by PRICE_SCALE_BPS)
 * @param remaining - Remaining amount to swap
 * @param fee_rate_bps - Fee rate in basis points (e.g., 30 = 0.3%)
 * @param swap_for_y - True for X→Y swap, False for Y→X swap
 * @returns Tuple of (in_effective, out_this, function_name, fee_amount) using float math
 */
export function calculateBinSwapFloat(
  bin_data: BinData,
  bin_price: number,
  remaining: number,
  fee_rate_bps: number,
  swap_for_y: boolean
): SwapCalculationResultFloat {
  const reserve_x = Number(bin_data.reserve_x);
  const reserve_y = Number(bin_data.reserve_y);
  const PRICE_SCALE_BPS_FLOAT = Number(PRICE_SCALE_BPS);
  const FEE_SCALE_BPS_FLOAT = Number(FEE_SCALE_BPS);

  if (swap_for_y) {
    // X → Y swap: Float version
    // Calculate max X that can be swapped based on available Y
    const max_x_amount = bin_price > 0
      ? Math.ceil((reserve_y * PRICE_SCALE_BPS_FLOAT) / bin_price)
      : 0;

    // Apply fee adjustment to max amount
    const updated_max_x_amount = fee_rate_bps > 0
      ? Math.floor((max_x_amount * FEE_SCALE_BPS_FLOAT) / (FEE_SCALE_BPS_FLOAT - fee_rate_bps))
      : max_x_amount;

    // Use the smaller of remaining input or max allowed
    const updated_x_amount = Math.min(remaining, updated_max_x_amount);

    const x_amount_fees_total = Math.floor((updated_x_amount * fee_rate_bps) / FEE_SCALE_BPS_FLOAT);
    const dx = updated_x_amount - x_amount_fees_total;

    const dy_before_cap = Math.floor((dx * bin_price) / PRICE_SCALE_BPS_FLOAT);
    const out_this = Math.min(dy_before_cap, reserve_y);
    const in_effective = updated_x_amount;
    const fee_amount = x_amount_fees_total;

    return {
      in_effective,
      out_this,
      function_name: 'swap-x-for-y',
      fee_amount,
    };
  } else {
    // Y → X swap: Float version
    const max_y_amount = Math.ceil((reserve_x * bin_price) / PRICE_SCALE_BPS_FLOAT);

    // Apply fee adjustment to max amount
    const updated_max_y_amount = fee_rate_bps > 0
      ? Math.floor((max_y_amount * FEE_SCALE_BPS_FLOAT) / (FEE_SCALE_BPS_FLOAT - fee_rate_bps))
      : max_y_amount;

    // Use the smaller of remaining input or max allowed
    const updated_y_amount = Math.min(remaining, updated_max_y_amount);

    const y_amount_fees_total = Math.floor((updated_y_amount * fee_rate_bps) / FEE_SCALE_BPS_FLOAT);
    const dy = updated_y_amount - y_amount_fees_total;

    const out_this = bin_price > 0
      ? Math.min(Math.floor((dy * PRICE_SCALE_BPS_FLOAT) / bin_price), reserve_x)
      : 0;
    const in_effective = updated_y_amount;
    const fee_amount = y_amount_fees_total;

    return {
      in_effective,
      out_this,
      function_name: 'swap-y-for-x',
      fee_amount,
    };
  }
}

/**
 * Calculate fee rate in BPS from protocol, provider, and variable fees.
 * 
 * This matches pricing.py's calculate_fee_rate method.
 * 
 * @param protocol_fee_bps - Protocol fee in basis points
 * @param provider_fee_bps - Provider fee in basis points
 * @param variable_fee_bps - Variable fee in basis points
 * @returns Total fee rate in basis points
 */
export function calculateFeeRateBPS(
  protocol_fee_bps: bigint,
  provider_fee_bps: bigint,
  variable_fee_bps: bigint
): bigint {
  return protocol_fee_bps + provider_fee_bps + variable_fee_bps;
}

/**
 * Calculate fee rate in BPS from protocol, provider, and variable fees (number version).
 */
export function calculateFeeRateBPSFloat(
  protocol_fee_bps: number,
  provider_fee_bps: number,
  variable_fee_bps: number
): number {
  return protocol_fee_bps + provider_fee_bps + variable_fee_bps;
}
