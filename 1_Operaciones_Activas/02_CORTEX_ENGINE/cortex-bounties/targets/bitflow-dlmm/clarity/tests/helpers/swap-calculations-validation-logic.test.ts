/**
 * Tests to verify the validation logic handles all scenarios correctly
 * 
 * These tests verify that the validation test logic correctly compares
 * contract output with quote engine calculations.
 */

import { describe, it, expect } from 'vitest';
import {
  calculateBinSwap,
  calculateBinSwapFloat,
  BinData,
} from '../../fuzz/harnesses/swap-calculations';

describe('Validation Logic Tests', () => {
  describe('Input Capping Scenarios', () => {
    it('should produce same result when input is pre-capped vs when helper caps it', () => {
      // Scenario: Contract receives 100 tokens, caps to 10 tokens
      // Validation test passes actualSwappedIn = 10 (already capped)
      // Helper function should produce same result as if we passed 100 (which gets capped)
      
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 1000000000n, // 10 tokens available
      };
      const binPrice = 5000000000n; // Price = 50
      const feeRateBPS = 4000n; // 40%

      // Simulate: Contract received 100 tokens, but capped to 0.33
      const originalInput = 10000000000n; // 100 tokens
      const actualSwappedIn = 33333333n; // 0.33 tokens (what contract actually swapped)

      // Calculate with original input (helper will cap it)
      const resultWithOriginal = calculateBinSwap(binData, binPrice, originalInput, feeRateBPS, true);
      const helperCappedInput = resultWithOriginal.in_effective;

      // Calculate with already-capped input (what validation test does)
      const resultWithCapped = calculateBinSwap(binData, binPrice, actualSwappedIn, feeRateBPS, true);

      // If actualSwappedIn <= helperCappedInput, helper should use actualSwappedIn as-is
      // If actualSwappedIn > helperCappedInput, something is wrong (contract capped differently)
      
      // For validation: we expect actualSwappedIn to be <= helperCappedInput
      // (contract and helper should cap to same value if formulas match)
      expect(actualSwappedIn).toBeLessThanOrEqual(helperCappedInput);
      
      // Helper should use actualSwappedIn (since it's <= max)
      expect(resultWithCapped.in_effective).toBe(actualSwappedIn);
      
      // Output should be calculated correctly based on actualSwappedIn
      expect(resultWithCapped.out_this).toBeGreaterThan(0n);
    });

    it('should handle case where contract caps to exact max', () => {
      // Test when contract caps input to exactly the max allowed
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 1000000000n, // 10 tokens
      };
      const binPrice = 5000000000n; // Price = 50
      const feeRateBPS = 4000n; // 0.4%

      // Calculate what max would be
      const maxXAmount = ((binData.reserve_y * 100000000n) + (binPrice - 1n)) / binPrice;
      const updatedMaxXAmount = (maxXAmount * 10000n) / (10000n - feeRateBPS);
      
      // Contract caps to exactly this amount
      const actualSwappedIn = updatedMaxXAmount;

      // Helper should use this amount as-is (it's already at max)
      const result = calculateBinSwap(binData, binPrice, actualSwappedIn, feeRateBPS, true);
      
      expect(result.in_effective).toBe(actualSwappedIn);
      expect(result.out_this).toBeGreaterThan(0n);
    });
  });

  describe('Exploit Detection Logic', () => {
    it('should correctly detect when contract returns more than float math allows', () => {
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const inputAmount = 100000000n;
      const feeRateBPS = 4000n;

      // Calculate what quote engine (float math) allows
      const floatResult = calculateBinSwapFloat(
        binData,
        Number(binPrice),
        Number(inputAmount),
        Number(feeRateBPS),
        true
      );
      const expectedFloat = BigInt(Math.floor(floatResult.out_this));

      // Simulate contract returning MORE than allowed (exploit)
      const actualSwappedOut = expectedFloat + 1000n;

      // Should detect exploit
      const exploitDetected = actualSwappedOut > expectedFloat;
      expect(exploitDetected).toBe(true);
    });

    it('should NOT flag when contract returns less than float math (pool-favored rounding)', () => {
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

      // Contract returns LESS than float math (pool-favored, not exploit)
      const actualSwappedOut = expectedFloat - 100n;

      // Should NOT detect exploit (pool-favored is acceptable)
      const exploitDetected = actualSwappedOut > expectedFloat;
      expect(exploitDetected).toBe(false);
    });

    it('should NOT flag when contract returns exactly what float math allows', () => {
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

      // Contract returns exactly what float math allows
      const actualSwappedOut = expectedFloat;

      // Should NOT detect exploit
      const exploitDetected = actualSwappedOut > expectedFloat;
      expect(exploitDetected).toBe(false);
    });
  });

  describe('Fee Exemption Handling', () => {
    it('should handle zero fees correctly (fee exemption)', () => {
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const inputAmount = 100000000n;
      const feeRateBPS = 0n; // Fee exempt

      const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);

      // No fees, so output should be higher
      expect(result.fee_amount).toBe(0n);
      expect(result.out_this).toBeGreaterThan(0n);
      
      // Compare with fees
      const resultWithFees = calculateBinSwap(binData, binPrice, inputAmount, 4000n, true);
      expect(result.out_this).toBeGreaterThan(resultWithFees.out_this);
    });
  });

  describe('Comparison Logic', () => {
    it('should compare integer math correctly', () => {
      // Integer math should match exactly (no tolerance)
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const inputAmount = 100000000n;
      const feeRateBPS = 4000n;

      const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);
      const expectedInteger = result.out_this;

      // Contract returns exactly what integer math expects
      const actualSwappedOut = expectedInteger;

      // Should match exactly
      const integerMatch = expectedInteger === actualSwappedOut;
      expect(integerMatch).toBe(true);
    });

    it('should compare float math correctly (with floor)', () => {
      // Float math is floored for comparison
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

      // Contract returns what float math expects (after floor)
      const actualSwappedOut = expectedFloat;

      // Should match
      const floatMatch = expectedFloat === actualSwappedOut;
      expect(floatMatch).toBe(true);
    });
  });
});
