/**
 * Helper functions for generating edge case values for testing
 * 
 * These functions generate values that are likely to trigger arithmetic
 * edge cases: overflow, underflow, division by zero, etc.
 */

const U128_MAX = 2n ** 128n - 1n;
const MIN_BIN_ID = -500n;
const MAX_BIN_ID = 500n;
const CENTER_BIN_ID = 500n;

/**
 * Generate a very small amount (near minimum)
 */
export function generateVerySmallAmount(): bigint {
  return 1n;
}

/**
 * Generate a very small amount that might round to zero after fees
 */
export function generateAmountThatRoundsToZero(feeRateBPS: bigint = 100n): bigint {
  // Generate amount so small that after fees it rounds to zero
  // If fee is 1% (100 BPS), amount of 1-99 will round to zero after fees
  return BigInt(Math.floor(99 / (Number(feeRateBPS) / 10000)));
}

/**
 * Generate a very large amount (near u128 max)
 */
export function generateVeryLargeAmount(): bigint {
  // Use a value close to but not at max to avoid immediate overflow
  return U128_MAX - 1000000n;
}

/**
 * Generate a large amount that might cause intermediate overflow
 */
export function generateLargeAmountForOverflow(): bigint {
  // Use a value that might cause issues in intermediate calculations
  // e.g., when multiplied by price or fees
  return 2n ** 100n; // Large but not max
}

/**
 * Generate a bin ID at the minimum boundary
 */
export function generateMinBinId(): bigint {
  return MIN_BIN_ID;
}

/**
 * Generate a bin ID just below minimum (invalid)
 */
export function generateInvalidMinBinId(): bigint {
  return MIN_BIN_ID - 1n;
}

/**
 * Generate a bin ID at the maximum boundary
 */
export function generateMaxBinId(): bigint {
  return MAX_BIN_ID;
}

/**
 * Generate a bin ID just above maximum (invalid)
 */
export function generateInvalidMaxBinId(): bigint {
  return MAX_BIN_ID + 1n;
}

/**
 * Generate a bin ID that would cause underflow in get-unsigned-bin-id
 * (bin-id < -500 means bin-id + 500 < 0, causing underflow when converting to uint)
 */
export function generateBinIdCausingUnderflow(): bigint {
  return MIN_BIN_ID - 1n; // -501
}

/**
 * Generate edge case bin IDs for testing
 */
export function generateEdgeCaseBinIds(): bigint[] {
  return [
    MIN_BIN_ID,           // -500 (valid minimum)
    MIN_BIN_ID - 1n,      // -501 (invalid, causes underflow)
    -1n,                  // -1 (valid, near center)
    0n,                   // 0 (center)
    1n,                   // 1 (valid, near center)
    MAX_BIN_ID,           // 500 (valid maximum)
    MAX_BIN_ID + 1n,      // 501 (invalid, exceeds max)
  ];
}

/**
 * Generate a random value biased toward edge cases
 * @param bias - 'small', 'large', 'normal', or 'mixed'
 */
export function generateBiasedRandomValue(
  min: bigint,
  max: bigint,
  bias: 'small' | 'large' | 'normal' | 'mixed' = 'mixed'
): bigint {
  const range = max - min;
  
  if (bias === 'small') {
    // Bias toward small values (first 10% of range)
    const smallMax = min + range / 10n;
    return min + (BigInt(Math.floor(Math.random() * Number(smallMax - min))));
  } else if (bias === 'large') {
    // Bias toward large values (last 10% of range)
    const largeMin = max - range / 10n;
    return largeMin + (BigInt(Math.floor(Math.random() * Number(max - largeMin))));
  } else if (bias === 'normal') {
    // Normal distribution (middle 80% of range)
    const normalMin = min + range / 10n;
    const normalMax = max - range / 10n;
    return normalMin + (BigInt(Math.floor(Math.random() * Number(normalMax - normalMin))));
  } else {
    // Mixed: 20% small, 20% large, 60% normal
    const rand = Math.random();
    if (rand < 0.2) {
      return generateBiasedRandomValue(min, max, 'small');
    } else if (rand < 0.4) {
      return generateBiasedRandomValue(min, max, 'large');
    } else {
      return generateBiasedRandomValue(min, max, 'normal');
    }
  }
}

/**
 * Generate a value that might cause division by zero
 * Returns very small amounts that might round to zero
 */
export function generateDivisionByZeroCandidate(): bigint {
  // Return amounts that are very small and might round to zero
  return BigInt(Math.floor(Math.random() * 10) + 1); // 1-10
}

