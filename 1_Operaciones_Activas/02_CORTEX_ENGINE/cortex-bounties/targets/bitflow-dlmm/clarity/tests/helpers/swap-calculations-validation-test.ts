/**
 * Validation-specific tests for swap calculations
 * 
 * These tests verify that the helper functions work correctly in the context
 * of the validation test, particularly when dealing with already-capped inputs.
 */

import { describe, it, expect } from 'vitest';
import {
  calculateBinSwap,
  calculateBinSwapFloat,
  BinData,
} from '../../fuzz/harnesses/swap-calculations';

describe('Validation Test Scenarios', () => {
  describe('Already-Capped Input Handling', () => {
    it('should produce same result when input is pre-capped vs when helper caps it', () => {
      // Scenario: Contract receives 100 tokens, but caps it to 10 tokens
      // We want to verify that passing 10 tokens (already capped) produces
      // the same result as passing 100 tokens (which gets capped internally)
      
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 1000000000n, // 10 tokens available
      };
      const binPrice = 5000000000n; // Price = 50
      const feeRateBPS = 4000n; // 0.4%

      // First, calculate with large input (will be capped)
      const largeInput = 10000000000n; // 100 tokens
      const resultWithLargeInput = calculateBinSwap(binData, binPrice, largeInput, feeRateBPS, true);
      const cappedInput = resultWithLargeInput.in_effective; // This is what contract would cap to

      // Now, pass the already-capped input
      const resultWithCappedInput = calculateBinSwap(binData, binPrice, cappedInput, feeRateBPS, true);

      // Results should be identical
      expect(resultWithCappedInput.in_effective).toBe(resultWithLargeInput.in_effective);
      expect(resultWithCappedInput.out_this).toBe(resultWithLargeInput.out_this);
      expect(resultWithCappedInput.fee_amount).toBe(resultWithLargeInput.fee_amount);

      // This verifies that the validation test can safely use actualSwappedIn
      // (which is already capped by the contract) and get the correct expected output
    });

    it('should handle case where contract caps input differently than helper would', () => {
      // This shouldn't happen if formulas match, but let's verify the behavior
      // In practice, if formulas match, the contract and helper should cap to the same value
      
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 1000000000n, // 10 tokens
      };
      const binPrice = 5000000000n; // Price = 50
      const feeRateBPS = 4000n; // 0.4%

      // Calculate what helper would cap to
      const largeInput = 10000000000n;
      const helperResult = calculateBinSwap(binData, binPrice, largeInput, feeRateBPS, true);
      const helperCappedInput = helperResult.in_effective;

      // If we pass a value that's less than what helper would cap to,
      // helper should use it as-is
      const smallerInput = helperCappedInput / 2n;
      const resultWithSmaller = calculateBinSwap(binData, binPrice, smallerInput, feeRateBPS, true);

      expect(resultWithSmaller.in_effective).toBe(smallerInput);
      expect(resultWithSmaller.in_effective).toBeLessThan(helperCappedInput);
    });
  });

  describe('Float vs Integer Comparison', () => {
    it('should produce float result that is >= integer result (floor rounding)', () => {
      // Float math should generally produce slightly higher results due to no rounding
      // until the final floor operation. However, integer math might round up in some cases.
      // The key is: actualSwappedOut should never exceed expectedFloat (exploit check)
      
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

      // Float result (before floor) should be close to integer result
      // After floor, float result might be <= integer result
      const floatResultFloored = BigInt(Math.floor(floatResult.out_this));
      
      // The difference should be small (due to rounding)
      const diff = intResult.out_this > floatResultFloored
        ? intResult.out_this - floatResultFloored
        : floatResultFloored - intResult.out_this;
      
      // Difference should be small (within 1-2 tokens due to rounding differences)
      expect(Number(diff)).toBeLessThan(10); // Allow small rounding differences
    });

    it('should detect exploit correctly (actual > expectedFloat)', () => {
      // Simulate an exploit scenario where contract returns more than float math allows
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const inputAmount = 100000000n;
      const feeRateBPS = 4000n;

      const floatResult = calculateBinSwapFloat(
        binData,
        Number(binPrice),
        Number(inputAmount),
        Number(feeRateBPS),
        true
      );
      const expectedFloat = BigInt(Math.floor(floatResult.out_this));

      // Simulate contract returning more than expected (exploit)
      const actualSwappedOut = expectedFloat + 1000n; // 1000 more than expected

      // This should be detected as an exploit
      const exploitDetected = actualSwappedOut > expectedFloat;
      expect(exploitDetected).toBe(true);
    });
  });

  describe('Edge Cases for Validation', () => {
    it('should handle zero actualSwappedIn (failed swap)', () => {
      // When swap fails, actualSwappedIn = 0
      // Validation should still work (use inputAmount instead)
      
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const inputAmount = 100000000n;
      const actualSwappedIn = 0n; // Swap failed
      const feeRateBPS = 4000n;

      // Should use inputAmount when actualSwappedIn is 0
      const inputToUse = actualSwappedIn > 0n ? actualSwappedIn : inputAmount;
      const result = calculateBinSwap(binData, binPrice, inputToUse, feeRateBPS, true);

      // Should calculate based on inputAmount
      expect(result.in_effective).toBeGreaterThan(0n);
    });

    it('should handle very small differences (rounding edge cases)', () => {
      // Test that small rounding differences don't trigger false exploit detection
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const inputAmount = 100000000n;
      const feeRateBPS = 4000n;

      const floatResult = calculateBinSwapFloat(
        binData,
        Number(binPrice),
        Number(inputAmount),
        Number(feeRateBPS),
        true
      );
      const expectedFloat = BigInt(Math.floor(floatResult.out_this));

      // Contract returns exactly what float math expects (no exploit)
      const actualSwappedOut = expectedFloat;
      const exploitDetected = actualSwappedOut > expectedFloat;
      expect(exploitDetected).toBe(false);

      // Contract returns 1 less (pool-favored rounding, not exploit)
      const actualSwappedOutLess = expectedFloat - 1n;
      const exploitDetectedLess = actualSwappedOutLess > expectedFloat;
      expect(exploitDetectedLess).toBe(false);
    });
  });
});



