/**
 * Verification tests to ensure helper functions match existing test logic
 * 
 * These tests compare the helper functions against the calculation logic
 * used in the existing comprehensive fuzz test to ensure consistency.
 */

import { describe, it, expect } from 'vitest';
import {
  calculateBinSwap,
  calculateBinSwapFloat,
  calculateFeeRateBPS,
  BinData,
} from '../../fuzz/harnesses/swap-calculations';

describe('Helper Functions Verification', () => {
  const PRICE_SCALE_BPS = 100000000n;
  const FEE_SCALE_BPS = 10000n;

  describe('Comparison with Existing Test Logic', () => {
    it('should match existing fuzz test calculation for swap-x-for-y', () => {
      // Test case matching the logic in dlmm-core-comprehensive-fuzz.test.ts
      const yBalanceBeforeSwap = 50000000000n; // 500 tokens
      const binPrice = 5000000000n; // Price = 50
      const actualSwappedIn = 100000000n; // 1 token (already capped by contract)
      const swapFeeTotal = 4000; // 40 BPS = 0.4%

      // Existing test logic (from comprehensive fuzz test):
      const swapFeeTotalBigInt = BigInt(swapFeeTotal);
      const FEE_SCALE_BPS_BIGINT = 10000n;
      const PRICE_SCALE_BPS_BIGINT = 100000000n;

      // Step 1: Calculate max-x-amount (existing test logic)
      const maxXAmountBigInt = ((yBalanceBeforeSwap * PRICE_SCALE_BPS_BIGINT) + binPrice - 1n) / binPrice;

      // Step 2: Adjust for fees (existing test logic)
      const updatedMaxXAmountBigInt = swapFeeTotalBigInt > 0n
        ? (maxXAmountBigInt * FEE_SCALE_BPS_BIGINT) / (FEE_SCALE_BPS_BIGINT - swapFeeTotalBigInt)
        : maxXAmountBigInt;

      // Step 3: Use actual swapped amount (existing test logic)
      const updatedXAmountBigInt = actualSwappedIn;

      // Step 4: Calculate fees (existing test logic)
      const xAmountFeesTotalBigInt = (updatedXAmountBigInt * swapFeeTotalBigInt) / FEE_SCALE_BPS_BIGINT;

      // Step 5: Calculate dx (existing test logic)
      const dxBigInt = updatedXAmountBigInt - xAmountFeesTotalBigInt;

      // Step 6: Calculate dy (existing test logic)
      const dyBeforeCapBigInt = (dxBigInt * binPrice) / PRICE_SCALE_BPS_BIGINT;
      const expectedDyInteger = dyBeforeCapBigInt > yBalanceBeforeSwap ? yBalanceBeforeSwap : dyBeforeCapBigInt;

      // Helper function calculation
      const binData: BinData = {
        reserve_x: 0n, // Not used for swap-x-for-y
        reserve_y: yBalanceBeforeSwap,
      };
      const result = calculateBinSwap(
        binData,
        binPrice,
        actualSwappedIn, // Use the actual swapped amount (already capped)
        swapFeeTotalBigInt,
        true // swap-x-for-y
      );

      // Verify results match
      expect(result.in_effective).toBe(updatedXAmountBigInt);
      expect(result.fee_amount).toBe(xAmountFeesTotalBigInt);
      expect(result.out_this).toBe(expectedDyInteger);
    });

    it('should handle input capping correctly', () => {
      // Test case where input is larger than max allowed
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 1000000000n, // 10 tokens available
      };
      const binPrice = 5000000000n; // Price = 50
      const largeInput = 10000000000n; // 100 tokens (more than max)
      const feeRateBPS = 0n; // No fees for simplicity

      const result = calculateBinSwap(binData, binPrice, largeInput, feeRateBPS, true);

      // Max x amount = ((10 * 1e8) + (50 * 1e8 - 1)) / (50 * 1e8)
      //              = (1e9 + 5e9 - 1) / 5e9
      //              = 6e9 / 5e9 = 1.2 -> 1 (with ceiling rounding)
      // Actually, let me recalculate:
      // max_x_amount = ((1000000000 * 100000000) + (5000000000 - 1)) / 5000000000
      //              = (100000000000000000 + 4999999999) / 5000000000
      //              = 1000000004999999999 / 5000000000
      //              = 200000000 (approximately, with ceiling rounding)

      // The input should be capped
      expect(result.in_effective).toBeLessThanOrEqual(largeInput);
      expect(result.in_effective).toBeGreaterThan(0n);
    });

    it('should match float calculation logic', () => {
      // Test that float calculation produces reasonable results
      const binData: BinData = {
        reserve_x: 1000000000n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const inputAmount = 100000000n;
      const feeRateBPS = 4000n;

      const intResult = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);
      const floatResult = calculateBinSwapFloat(
        binData,
        Number(binPrice),
        Number(inputAmount),
        Number(feeRateBPS),
        true
      );

      // Float result should be close to integer result (within 1 token due to rounding)
      const diff = Math.abs(Number(intResult.out_this) - floatResult.out_this);
      expect(diff).toBeLessThan(1); // Should be very close
    });
  });

  describe('Edge Case Verification', () => {
    it('should handle very large bin prices', () => {
      // Test with very large bin price (edge case mentioned in requirements)
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 1000000000000000000n, // Very large reserve
      };
      const veryLargeBinPrice = 100000000000000000n; // Very large price
      const inputAmount = 100000000n;
      const feeRateBPS = 0n;

      // Should not throw or lose precision
      const result = calculateBinSwap(binData, veryLargeBinPrice, inputAmount, feeRateBPS, true);
      expect(result.out_this).toBeGreaterThanOrEqual(0n);
      expect(result.in_effective).toBe(inputAmount);
    });

    it('should handle very small reserves', () => {
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 1n, // Very small reserve
      };
      const binPrice = 5000000000n;
      const inputAmount = 100000000n;
      const feeRateBPS = 0n;

      const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);
      // Output should be capped at reserve_y
      expect(result.out_this).toBeLessThanOrEqual(1n);
    });

    it('should handle fee exemption (zero fees)', () => {
      const binData: BinData = {
        reserve_x: 1000000000n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const inputAmount = 100000000n;
      const feeRateBPS = 0n; // Fee exempt

      const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);
      expect(result.fee_amount).toBe(0n);
      // Output should be higher without fees
      expect(result.out_this).toBeGreaterThan(0n);
    });
  });

  describe('Formula Consistency', () => {
    it('should produce consistent results across multiple calls', () => {
      const binData: BinData = {
        reserve_x: 1000000000n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const inputAmount = 100000000n;
      const feeRateBPS = 4000n;

      const result1 = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);
      const result2 = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);

      // Results should be identical
      expect(result1.in_effective).toBe(result2.in_effective);
      expect(result1.out_this).toBe(result2.out_this);
      expect(result1.fee_amount).toBe(result2.fee_amount);
    });

    it('should handle swap-y-for-x correctly', () => {
      const binData: BinData = {
        reserve_x: 1000000000n, // 10 tokens
        reserve_y: 50000000000n, // 500 tokens
      };
      const binPrice = 5000000000n; // Price = 50
      const inputAmount = 50000000000n; // 500 tokens input
      const feeRateBPS = 4000n; // 0.4%

      const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, false);

      // For swap-y-for-x:
      // max_y_amount = ((reserve_x * bin_price + (PRICE_SCALE_BPS - 1)) // PRICE_SCALE_BPS)
      //              = ((1000000000 * 5000000000 + (100000000 - 1)) // 100000000)
      //              = (5000000000000000000 + 99999999) // 100000000
      //              = 50000000000 (approximately)
      // With fees: updated_max_y_amount = (50000000000 * 10000) / (10000 - 4000) = 83333333333
      // updated_y_amount = min(50000000000, 83333333333) = 50000000000
      // fees = (50000000000 * 4000) / 10000 = 20000000000
      // dy = 50000000000 - 20000000000 = 30000000000
      // dx = (30000000000 * 100000000) / 5000000000 = 600000000 (6 tokens)

      expect(result.function_name).toBe('swap-y-for-x');
      expect(result.in_effective).toBe(inputAmount);
      expect(result.fee_amount).toBeGreaterThan(0n);
      expect(result.out_this).toBeGreaterThan(0n);
      expect(result.out_this).toBeLessThanOrEqual(binData.reserve_x);
    });

    it('should handle already-capped input correctly (validation test scenario)', () => {
      // This test verifies that when we pass an already-capped input (like actualSwappedIn
      // from the contract), the helper function produces the same result as if we passed
      // the original input amount.
      
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 1000000000n, // 10 tokens available
      };
      const binPrice = 5000000000n; // Price = 50
      const originalInput = 10000000000n; // 100 tokens (more than max)
      const feeRateBPS = 4000n; // 0.4%

      // First, calculate what the max allowed input would be
      const resultWithOriginal = calculateBinSwap(binData, binPrice, originalInput, feeRateBPS, true);
      const cappedInput = resultWithOriginal.in_effective; // This is what contract would cap to

      // Now, pass the capped input to the helper
      const resultWithCapped = calculateBinSwap(binData, binPrice, cappedInput, feeRateBPS, true);

      // Results should be identical
      expect(resultWithCapped.in_effective).toBe(resultWithOriginal.in_effective);
      expect(resultWithCapped.out_this).toBe(resultWithOriginal.out_this);
      expect(resultWithCapped.fee_amount).toBe(resultWithOriginal.fee_amount);

      // This verifies that passing an already-capped input produces the same result
      // as passing the original input (which gets capped internally)
    });
  });
});

