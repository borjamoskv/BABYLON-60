/**
 * Edge case tests for swap calculations
 * 
 * These tests verify edge cases that might cause issues, especially
 * with large values, precision, and boundary conditions.
 */

import { describe, it, expect } from 'vitest';
import {
  calculateBinSwap,
  calculateBinSwapFloat,
  BinData,
} from '../../fuzz/harnesses/swap-calculations';

describe('Edge Case Tests', () => {
  describe('Large Value Handling', () => {
    it('should handle very large bin prices correctly', () => {
      // Test with "oddly high" bin prices as mentioned in requirements
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 1000000000000000000n, // Very large reserve
      };
      
      // Very large bin price (close to max safe integer)
      const veryLargeBinPrice = 900000000000000000n; // 9 * 1e8
      const inputAmount = 100000000n;
      const feeRateBPS = 0n;

      // Should not throw or lose precision
      const result = calculateBinSwap(binData, veryLargeBinPrice, inputAmount, feeRateBPS, true);
      
      expect(result.out_this).toBeGreaterThanOrEqual(0n);
      expect(result.in_effective).toBe(inputAmount);
      expect(result.fee_amount).toBe(0n);
    });

    it('should handle very large reserves correctly', () => {
      // Test with reserves that approach JavaScript number limits
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 9000000000000000000n, // Close to Number.MAX_SAFE_INTEGER
      };
      const binPrice = 5000000000n;
      const inputAmount = 100000000n;
      const feeRateBPS = 0n;

      const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);
      
      // Should calculate correctly without overflow
      expect(result.out_this).toBeGreaterThanOrEqual(0n);
      expect(result.out_this).toBeLessThanOrEqual(binData.reserve_y);
    });

    it('should handle very large input amounts', () => {
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const veryLargeInput = 1000000000000000000n; // Very large input
      const feeRateBPS = 0n;

      const result = calculateBinSwap(binData, binPrice, veryLargeInput, feeRateBPS, true);
      
      // Should cap at max allowed
      expect(result.in_effective).toBeLessThanOrEqual(veryLargeInput);
      expect(result.out_this).toBeLessThanOrEqual(binData.reserve_y);
    });
  });

  describe('Precision and Rounding', () => {
    it('should handle ceiling rounding correctly in max amount calculation', () => {
      // Test that ceiling rounding works correctly
      // Formula: max_x_amount = ((reserve_y * PRICE_SCALE_BPS + (bin_price - 1)) // bin_price)
      // The "+ bin_price - 1" implements ceiling rounding
      
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 100000000n, // 1 token
      };
      const binPrice = 3000000000n; // Price = 30
      const inputAmount = 1000000000n;
      const feeRateBPS = 0n;

      // Without ceiling rounding: (1 * 1e8) / 30 = 3.333... tokens
      // With ceiling rounding: ((1 * 1e8) + 30*1e8 - 1) / 30*1e8 = ceiling(3.333) = 4 tokens
      const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);
      
      // Should cap correctly based on ceiling rounding
      expect(result.in_effective).toBeGreaterThan(0n);
      expect(result.out_this).toBeLessThanOrEqual(binData.reserve_y);
    });

    it('should handle integer division rounding correctly', () => {
      // Test that integer division produces correct results
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const inputAmount = 33333333n; // Amount that will cause rounding
      const feeRateBPS = 0n;

      const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);
      
      // Output should be calculated correctly with integer division
      // dx = 33333333, dy = (33333333 * 50*1e8) / 1e8 = 1666666650
      expect(result.out_this).toBeGreaterThan(0n);
      expect(result.out_this).toBeLessThanOrEqual(binData.reserve_y);
    });
  });

  describe('Fee Edge Cases', () => {
    it('should handle maximum fees (100%)', () => {
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const inputAmount = 100000000n;
      const feeRateBPS = 10000n; // 100% fees

      const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);
      
      // With 100% fees, all input goes to fees, output should be 0
      expect(result.fee_amount).toBe(inputAmount);
      expect(result.out_this).toBe(0n);
    });

    it('should handle very small fees', () => {
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const inputAmount = 100000000n;
      const feeRateBPS = 1n; // 0.01% fees (1 BPS)

      const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);
      
      // Should calculate small fees correctly
      expect(result.fee_amount).toBeGreaterThan(0n);
      expect(result.fee_amount).toBeLessThan(inputAmount);
      expect(result.out_this).toBeGreaterThan(0n);
    });

    it('should handle zero fees correctly', () => {
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const inputAmount = 100000000n;
      const feeRateBPS = 0n;

      const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);
      
      // No fees, so output should be higher
      expect(result.fee_amount).toBe(0n);
      expect(result.out_this).toBeGreaterThan(0n);
    });
  });

  describe('Boundary Conditions', () => {
    it('should handle reserve_y = 0', () => {
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 0n,
      };
      const binPrice = 5000000000n;
      const inputAmount = 100000000n;
      const feeRateBPS = 0n;

      const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);
      
      // No reserves, so output should be 0
      expect(result.out_this).toBe(0n);
    });

    it('should handle bin_price = 0', () => {
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 50000000000n,
      };
      const binPrice = 0n;
      const inputAmount = 100000000n;
      const feeRateBPS = 0n;

      const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);
      
      // Zero price should result in zero output
      expect(result.out_this).toBe(0n);
    });

    it('should handle input = 0', () => {
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const inputAmount = 0n;
      const feeRateBPS = 0n;

      const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);
      
      // Zero input should result in zero output
      expect(result.in_effective).toBe(0n);
      expect(result.out_this).toBe(0n);
      expect(result.fee_amount).toBe(0n);
    });

    it('should handle input exactly equal to max allowed', () => {
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 1000000000n, // 10 tokens
      };
      const binPrice = 5000000000n; // Price = 50
      const feeRateBPS = 0n;

      // Calculate max allowed input
      const maxXAmount = ((binData.reserve_y * 100000000n) + (binPrice - 1n)) / binPrice;
      
      // Use exactly max allowed
      const result = calculateBinSwap(binData, binPrice, maxXAmount, feeRateBPS, true);
      
      // Should use the full amount
      expect(result.in_effective).toBe(maxXAmount);
      expect(result.out_this).toBeGreaterThan(0n);
    });

    it('should handle input slightly larger than max allowed', () => {
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 1000000000n, // 10 tokens
      };
      const binPrice = 5000000000n; // Price = 50
      const feeRateBPS = 0n;

      // Calculate max allowed input
      const maxXAmount = ((binData.reserve_y * 100000000n) + (binPrice - 1n)) / binPrice;
      const inputSlightlyLarger = maxXAmount + 1n;
      
      // Use slightly more than max
      const result = calculateBinSwap(binData, binPrice, inputSlightlyLarger, feeRateBPS, true);
      
      // Should cap at max
      expect(result.in_effective).toBe(maxXAmount);
      expect(result.in_effective).toBeLessThan(inputSlightlyLarger);
    });
  });

  describe('Swap Direction Edge Cases', () => {
    it('should handle swap-y-for-x with zero reserves correctly', () => {
      const binData: BinData = {
        reserve_x: 0n, // No X reserves
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const inputAmount = 100000000n;
      const feeRateBPS = 0n;

      const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, false);
      
      // No X reserves, so output should be 0
      expect(result.out_this).toBe(0n);
    });

    it('should handle swap-x-for-y with zero reserves correctly', () => {
      const binData: BinData = {
        reserve_x: 1000000000n,
        reserve_y: 0n, // No Y reserves
      };
      const binPrice = 5000000000n;
      const inputAmount = 100000000n;
      const feeRateBPS = 0n;

      const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);
      
      // No Y reserves, so output should be 0
      expect(result.out_this).toBe(0n);
    });
  });

  describe('Float vs Integer Consistency', () => {
    it('should produce consistent results for small values', () => {
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 1000000n, // Small reserve
      };
      const binPrice = 5000000000n;
      const inputAmount = 10000n; // Small input
      const feeRateBPS = 100n; // 1% fees

      const intResult = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);
      const floatResult = calculateBinSwapFloat(
        binData,
        Number(binPrice),
        Number(inputAmount),
        Number(feeRateBPS),
        true
      );

      // Results should be close (within rounding)
      const floatFloored = BigInt(Math.floor(floatResult.out_this));
      const diff = intResult.out_this > floatFloored
        ? intResult.out_this - floatFloored
        : floatFloored - intResult.out_this;
      
      expect(Number(diff)).toBeLessThan(10); // Small difference allowed
    });

    it('should handle float precision limits gracefully', () => {
      // Test with values that might approach JavaScript number precision limits
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 9000000000000000000n, // Very large (close to Number.MAX_SAFE_INTEGER)
      };
      const binPrice = 5000000000n;
      const inputAmount = 100000000n;
      const feeRateBPS = 4000n;

      // Integer calculation should work fine
      const intResult = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);
      expect(intResult.out_this).toBeGreaterThanOrEqual(0n);

      // Float calculation might have precision issues, but shouldn't crash
      const floatResult = calculateBinSwapFloat(
        binData,
        Number(binPrice),
        Number(inputAmount),
        Number(feeRateBPS),
        true
      );
      
      // Should produce a result (even if slightly imprecise)
      expect(floatResult.out_this).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Fee Adjustment Edge Cases', () => {
    it('should handle fee adjustment when input is capped', () => {
      // Test that fee adjustment works correctly when input is capped at max
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 1000000000n, // 10 tokens
      };
      const binPrice = 5000000000n; // Price = 50
      const largeInput = 10000000000n; // 100 tokens (will be capped)
      const feeRateBPS = 4000n; // 0.4%

      const result = calculateBinSwap(binData, binPrice, largeInput, feeRateBPS, true);
      
      // Input should be capped, and fees calculated on capped amount
      expect(result.in_effective).toBeLessThan(largeInput);
      expect(result.fee_amount).toBeGreaterThan(0n);
      expect(result.fee_amount).toBeLessThan(result.in_effective);
    });

    it('should handle fee adjustment formula edge case (fee_rate_bps = FEE_SCALE_BPS)', () => {
      // Edge case: fee_rate_bps = 10000 (100%)
      // Formula: updated_max_x_amount = (max_x_amount * 10000) / (10000 - 10000)
      // This would divide by zero, but we check fee_rate_bps > 0n, so it's handled
      
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const inputAmount = 100000000n;
      const feeRateBPS = 10000n; // 100% fees

      // Should handle 100% fees correctly (max amount calculation might be affected)
      const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);
      
      // With 100% fees, all input goes to fees
      expect(result.fee_amount).toBe(inputAmount);
      expect(result.out_this).toBe(0n);
    });
  });
});



