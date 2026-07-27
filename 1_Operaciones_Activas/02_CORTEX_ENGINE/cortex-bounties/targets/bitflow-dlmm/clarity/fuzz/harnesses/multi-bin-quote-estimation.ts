/**
 * Multi-bin swap quote estimation helpers
 * 
 * This module provides functions for estimating and calculating multi-bin swaps
 * without requiring a Redis API. It ports the logic from pricing.py's
 * MultiBinDLMMStrategy to work directly with contract queries.
 * 
 * Reference: pricing.py lines 800-902 (bin estimation), 337-486 (bin traversal)
 */

import { calculateBinSwap, calculateBinSwapFloat, BinData, SwapCalculationResult } from './swap-calculations';

export interface BinWithPrice {
  binId: bigint;
  price: bigint;
  reserves: BinData;
}

export interface MultiBinSwapResult {
  totalOut: bigint;
  totalFees: bigint;
  executionPath: Array<{
    binId: bigint;
    in: bigint;
    out: bigint;
    fees: bigint;
  }>;
}

export interface MultiBinSwapResultFloat {
  totalOut: number;
  totalFees: number;
  executionPath: Array<{
    binId: bigint;
    in: number;
    out: number;
    fees: number;
  }>;
}

export interface PoolState {
  activeBinId: bigint;
  binBalances: Map<bigint, { xBalance: bigint; yBalance: bigint }>;
}

const MAX_BINS_ESTIMATION = 1000; // Maximum bins to estimate
const LARGE_TRADE_THRESHOLD = 100000000n; // 100M tokens
const VERY_LARGE_TRADE_THRESHOLD = 10000000n; // 10M tokens

/**
 * Estimate how many bins are needed for a swap based on trade size.
 * 
 * Ported from pricing.py _estimate_bins_needed() (lines 800-850)
 * 
 * @param amountIn - Amount to swap
 * @param activeBinData - Active bin reserves
 * @param sampleBins - Sample of nearby bins to estimate average liquidity
 * @returns Estimated number of bins needed
 */
export function estimateBinsNeeded(
  amountIn: bigint,
  activeBinData: BinData,
  sampleBins: BinData[] = []
): number {
  try {
    // Calculate available liquidity in active bin
    const reserve_x = activeBinData.reserve_x;
    const reserve_y = activeBinData.reserve_y;
    
    // Estimate how much of the trade the active bin can handle (80% of min reserve)
    const minReserve = reserve_x < reserve_y ? reserve_x : reserve_y;
    const activeBinCapacity = (minReserve * 80n) / 100n;
    
    if (amountIn <= activeBinCapacity) {
      // Trade fits in active bin
      return 1;
    }
    
    // For very large trades, return maximum estimate
    if (amountIn > LARGE_TRADE_THRESHOLD) {
      return MAX_BINS_ESTIMATION;
    }
    
    // Need additional bins - calculate based on remaining amount
    const remainingAmount = amountIn - activeBinCapacity;
    
    // Calculate average liquidity per bin from sample
    const avgLiquidityPerBin = calculateAvgLiquidity(sampleBins);
    
    if (avgLiquidityPerBin > 0n) {
      // Estimate bins needed based on average liquidity
      let estimatedBins = Number(remainingAmount / avgLiquidityPerBin) + 1;
      
      // For large trades, apply 3x safety margin
      if (amountIn > VERY_LARGE_TRADE_THRESHOLD) {
        estimatedBins = estimatedBins * 3;
      }
      
      // Cap at reasonable maximum
      return Math.min(estimatedBins, MAX_BINS_ESTIMATION);
    } else {
      // Fallback if we can't calculate average liquidity
      return 1;
    }
  } catch (e) {
    // Fallback on error
    return 1;
  }
}

/**
 * Calculate average liquidity per bin from sample bins.
 * 
 * Ported from pricing.py _calculate_avg_liquidity() (lines 889-900)
 * 
 * @param sampleBins - Array of sample bin data
 * @returns Average liquidity per bin
 */
function calculateAvgLiquidity(sampleBins: BinData[]): bigint {
  if (sampleBins.length === 0) {
    return 0n;
  }
  
  let totalLiquidity = 0n;
  for (const binData of sampleBins) {
    // Use minimum of X and Y reserves as available liquidity
    const minReserve = binData.reserve_x < binData.reserve_y 
      ? binData.reserve_x 
      : binData.reserve_y;
    totalLiquidity += minReserve;
  }
  
  return totalLiquidity / BigInt(sampleBins.length);
}

/**
 * Get sample bins around the active bin for liquidity estimation.
 * 
 * Ported from pricing.py _get_sample_bins() (lines 868-887)
 * 
 * @param poolState - Current pool state
 * @param activeBinId - Active bin ID
 * @param maxOffset - Maximum offset to check (default: 2)
 * @returns Array of sample bin data
 */
export function getSampleBins(
  poolState: PoolState,
  activeBinId: bigint,
  maxOffset: number = 2
): BinData[] {
  const sampleBins: BinData[] = [];
  
  // Sample bins on each side of active bin
  for (let offset = -maxOffset; offset <= maxOffset; offset++) {
    if (offset === 0) {
      // Skip active bin
      continue;
    }
    
    const binId = activeBinId + BigInt(offset);
    const binData = poolState.binBalances.get(binId);
    
    if (binData && binData.xBalance > 0n && binData.yBalance > 0n) {
      sampleBins.push({
        reserve_x: binData.xBalance,
        reserve_y: binData.yBalance,
      });
    }
  }
  
  return sampleBins;
}

/**
 * Discover bins for a swap by querying adjacent bins.
 * 
 * This function queries bins from the contract and sorts them by price
 * in the correct order for the swap direction.
 * 
 * @param poolState - Current pool state
 * @param activeBinId - Active bin ID
 * @param swapForY - True for X→Y swap, False for Y→X swap
 * @param estimatedBinsNeeded - Estimated number of bins needed
 * @param getBinPrice - Function to get bin price (initialPrice, binStep, binId) => price
 * @param initialPrice - Initial pool price
 * @param binStep - Bin step size
 * @returns Array of bins with prices, sorted in correct order
 */
export async function discoverBinsForSwap(
  poolState: PoolState,
  activeBinId: bigint,
  swapForY: boolean,
  estimatedBinsNeeded: number,
  getBinPrice: (initialPrice: bigint, binStep: bigint, binId: bigint) => Promise<bigint>,
  initialPrice: bigint,
  binStep: bigint,
  getBinBalances?: (binId: bigint) => Promise<{ xBalance: bigint; yBalance: bigint } | null>
): Promise<BinWithPrice[]> {
  const discoveredBins: BinWithPrice[] = [];
  
  // Determine traversal direction
  // X→Y: traverse LEFT (lower prices, binId decreasing)
  // Y→X: traverse RIGHT (higher prices, binId increasing)
  const direction = swapForY ? -1 : 1;
  
  // Always include active bin first if it has liquidity
  let activeBinData = poolState.binBalances.get(activeBinId);
  if (!activeBinData && getBinBalances) {
    const balances = await getBinBalances(activeBinId);
    if (balances) {
      activeBinData = balances;
    }
  }
  
  if (activeBinData) {
    const hasLiquidity = swapForY 
      ? activeBinData.yBalance > 0n
      : activeBinData.xBalance > 0n;
    
    if (hasLiquidity) {
      const price = await getBinPrice(initialPrice, binStep, activeBinId);
      discoveredBins.push({
        binId: activeBinId,
        price,
        reserves: {
          reserve_x: activeBinData.xBalance,
          reserve_y: activeBinData.yBalance,
        },
      });
    }
  }
  
  // Start from bins adjacent to active bin
  let currentBinId = activeBinId + BigInt(direction);
  let checkedCount = 0;
  // Check up to 500 bins to ensure we find all bins with liquidity
  // The swap router can traverse up to 350 bins, so 500 gives us a safety margin
  const maxBinsToCheck = Math.max(estimatedBinsNeeded * 5, 500);
  
  // Query bins in the correct direction (skip active bin since we already added it)
  // Continue discovering bins until we've checked enough bins (don't stop early)
  while (checkedCount < maxBinsToCheck) {
    let binData = poolState.binBalances.get(currentBinId);
    
    // If bin not in poolState and we have a query function, query it
    if (!binData && getBinBalances) {
      const balances = await getBinBalances(currentBinId);
      if (balances) {
        binData = balances;
      }
    }
    
    if (binData) {
      // Check if bin has liquidity for swap direction
      const hasLiquidity = swapForY 
        ? binData.yBalance > 0n  // X→Y needs Y reserves
        : binData.xBalance > 0n;  // Y→X needs X reserves
      
      if (hasLiquidity) {
        // Get bin price
        const price = await getBinPrice(initialPrice, binStep, currentBinId);
        
        discoveredBins.push({
          binId: currentBinId,
          price,
          reserves: {
            reserve_x: binData.xBalance,
            reserve_y: binData.yBalance,
          },
        });
      }
    }
    
    // Move to next bin in traversal direction
    currentBinId = currentBinId + BigInt(direction);
    checkedCount++;
  }
  
  // Sort bins by price in correct order
  // X→Y: Descending price (right to left)
  // Y→X: Ascending price (left to right)
  discoveredBins.sort((a, b) => {
    if (swapForY) {
      // Descending order for X→Y
      return a.price > b.price ? -1 : a.price < b.price ? 1 : 0;
    } else {
      // Ascending order for Y→X
      return a.price < b.price ? -1 : a.price > b.price ? 1 : 0;
    }
  });
  
  return discoveredBins;
}

/**
 * Calculate multi-bin swap by traversing bins sequentially.
 * 
 * Ported from pricing.py bin traversal logic (lines 337-486)
 * 
 * @param bins - Array of bins with prices, sorted in correct order
 * @param amountIn - Amount to swap
 * @param feeRateBPS - Fee rate in basis points
 * @param swapForY - True for X→Y swap, False for Y→X swap
 * @returns Multi-bin swap result with total output, fees, and execution path
 */
export function calculateMultiBinSwap(
  bins: BinWithPrice[],
  amountIn: bigint,
  feeRateBPS: bigint,
  swapForY: boolean
): MultiBinSwapResult {
  let remaining = amountIn;
  let totalOut = 0n;
  let totalFees = 0n;
  const executionPath: Array<{ binId: bigint; in: bigint; out: bigint; fees: bigint }> = [];
  
  // Traverse bins sequentially
  for (const bin of bins) {
    // Check if trade is complete
    if (remaining <= 0n) {
      break;
    }
    
    // Calculate swap for this bin
    const result: SwapCalculationResult = calculateBinSwap(
      bin.reserves,
      bin.price,
      remaining,
      feeRateBPS,
      swapForY
    );
    
    // Only process if we have some effective input and output
    if (result.in_effective > 0n && result.out_this > 0n) {
      // Add to execution path
      executionPath.push({
        binId: bin.binId,
        in: result.in_effective,
        out: result.out_this,
        fees: result.fee_amount,
      });
      
      // Accumulate fees and amounts
      totalFees += result.fee_amount;
      totalOut += result.out_this;
      remaining -= result.in_effective;
    }
  }
  
  return {
    totalOut,
    totalFees,
    executionPath,
  };
}

/**
 * Calculate multi-bin swap by traversing bins sequentially using float math.
 * 
 * This is the float-based version for comparison with the quote engine.
 * Mirrors calculateMultiBinSwap but uses float arithmetic.
 * 
 * @param bins - Array of bins with prices, sorted in correct order
 * @param amountIn - Amount to swap (bigint, will be converted to number)
 * @param feeRateBPS - Fee rate in basis points (bigint, will be converted to number)
 * @param swapForY - True for X→Y swap, False for Y→X swap
 * @returns Multi-bin swap result with total output, fees, and execution path (float)
 */
export function calculateMultiBinSwapFloat(
  bins: BinWithPrice[],
  amountIn: bigint,
  feeRateBPS: bigint,
  swapForY: boolean
): MultiBinSwapResultFloat {
  let remaining = Number(amountIn);
  let totalOut = 0;
  let totalFees = 0;
  const executionPath: Array<{ binId: bigint; in: number; out: number; fees: number }> = [];
  
  // Traverse bins sequentially
  for (const bin of bins) {
    // Check if trade is complete
    if (remaining <= 0) {
      break;
    }
    
    // Calculate swap for this bin using float math
    const result = calculateBinSwapFloat(
      bin.reserves,
      Number(bin.price),
      remaining,
      Number(feeRateBPS),
      swapForY
    );
    
    // Only process if we have some effective input and output
    if (result.in_effective > 0 && result.out_this > 0) {
      // Add to execution path
      executionPath.push({
        binId: bin.binId,
        in: result.in_effective,
        out: result.out_this,
        fees: result.fee_amount,
      });
      
      // Accumulate fees and amounts
      totalFees += result.fee_amount;
      totalOut += result.out_this;
      remaining -= result.in_effective;
    }
  }
  
  return {
    totalOut,
    totalFees,
    executionPath,
  };
}

/**
 * Get maximum attempts for adaptive bin loading.
 * 
 * Ported from pricing.py _get_adaptive_max_attempts() (lines 857-860)
 * 
 * @returns Maximum attempts (default: 3)
 */
export function getAdaptiveMaxAttempts(): number {
  return 3;
}

/**
 * Load bins adaptively with exponential backoff.
 * 
 * Ported from pricing.py adaptive loading pattern (lines 195-262)
 * 
 * @param poolState - Current pool state
 * @param activeBinId - Active bin ID
 * @param swapForY - True for X→Y swap, False for Y→X swap
 * @param initialEstimate - Initial estimate of bins needed
 * @param getBinPrice - Function to get bin price
 * @param initialPrice - Initial pool price
 * @param binStep - Bin step size
 * @returns Array of bins with prices
 */
export async function loadBinsAdaptively(
  poolState: PoolState,
  activeBinId: bigint,
  swapForY: boolean,
  initialEstimate: number,
  getBinPrice: (initialPrice: bigint, binStep: bigint, binId: bigint) => Promise<bigint>,
  initialPrice: bigint,
  binStep: bigint
): Promise<BinWithPrice[]> {
  const maxAttempts = getAdaptiveMaxAttempts();
  let estimate = initialEstimate;
  
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    // Try with current estimate
    const bins = await discoverBinsForSwap(
      poolState,
      activeBinId,
      swapForY,
      estimate,
      getBinPrice,
      initialPrice,
      binStep
    );
    
    // If we found enough bins, return them
    if (bins.length >= estimate) {
      return bins;
    }
    
    // Exponential backoff: try 2x, then 3x
    estimate = estimate * (attempt + 2);
  }
  
  // Return whatever we found after max attempts
  return await discoverBinsForSwap(
    poolState,
    activeBinId,
    swapForY,
    estimate,
    getBinPrice,
    initialPrice,
    binStep
  );
}

