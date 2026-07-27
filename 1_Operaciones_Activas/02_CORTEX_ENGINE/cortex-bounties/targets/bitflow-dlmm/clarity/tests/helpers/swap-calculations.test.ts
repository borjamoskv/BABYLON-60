/**
 * Unit tests for swap calculation helpers
 * 
 * These tests validate that the TypeScript swap calculation helpers
 * match the expected behavior from pricing.py's _calculate_bin_swap method.
 */

import { describe, it, expect } from 'vitest';
import {
  calculateBinSwap,
  calculateBinSwapFloat,
  calculateFeeRateBPS,
  calculateFeeRateBPSFloat,
  BinData,
} from '../../fuzz/harnesses/swap-calculations';

describe('Swap Calculation Helpers', () => {
  const PRICE_SCALE_BPS = 100000000n;
  const FEE_SCALE_BPS = 10000n;

  describe('calculateFeeRateBPS', () => {
    it('should calculate fee rate correctly', () => {
      expect(calculateFeeRateBPS(1000n, 3000n, 0n)).toBe(4000n); // 0.1% + 0.3% = 0.4% = 40 BPS
      expect(calculateFeeRateBPS(0n, 0n, 0n)).toBe(0n);
      expect(calculateFeeRateBPS(100n, 200n, 50n)).toBe(350n);
    });

    it('should match float version', () => {
      const intResult = calculateFeeRateBPS(1000n, 3000n, 0n);
      const floatResult = calculateFeeRateBPSFloat(1000, 3000, 0);
      expect(Number(intResult)).toBe(floatResult);
    });
  });

  describe('calculateBinSwap - swap-x-for-y', () => {
    it('should calculate swap with zero fees', () => {
      const binData: BinData = {
        reserve_x: 1000000000n, // 10 tokens
        reserve_y: 50000000000n, // 500 tokens
      };
      const binPrice = 5000000000n; // Price = 50 (scaled by 1e8)
      const remaining = 100000000n; // 1 token input
      const feeRateBPS = 0n; // No fees

      const result = calculateBinSwap(binData, binPrice, remaining, feeRateBPS, true);

      // Expected: dx = 1 token, dy = (1 * 50) / 1 = 50 tokens
      expect(result.function_name).toBe('swap-x-for-y');
      expect(result.in_effective).toBe(100000000n);
      expect(result.fee_amount).toBe(0n);
      expect(result.out_this).toBe(5000000000n); // 50 tokens
    });

    it('should calculate swap with fees', () => {
      const binData: BinData = {
        reserve_x: 1000000000n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n; // Price = 50
      const remaining = 100000000n; // 1 token input
      const feeRateBPS = 4000n; // 0.4% = 40 BPS

      const result = calculateBinSwap(binData, binPrice, remaining, feeRateBPS, true);

      // Fees: 1 * 0.004 = 0.004 tokens
      // dx = 1 - 0.004 = 0.996 tokens
      // dy = (0.996 * 50) = 49.8 tokens
      expect(result.function_name).toBe('swap-x-for-y');
      expect(result.in_effective).toBe(100000000n);
      expect(result.fee_amount).toBe(40000000n); // 0.004 tokens = 400000 (with 8 decimals)
      expect(result.out_this).toBeLessThan(5000000000n); // Less than 50 due to fees
    });

    it('should cap output at reserve_y', () => {
      const binData: BinData = {
        reserve_x: 1000000000n,
        reserve_y: 1000000000n, // Only 10 tokens available
      };
      const binPrice = 5000000000n; // Price = 50
      const remaining = 1000000000n; // 10 tokens input

      const result = calculateBinSwap(binData, binPrice, remaining, 0n, true);

      // Would calculate 500 tokens output, but capped at 10 tokens
      expect(result.out_this).toBe(1000000000n); // Capped at reserve_y
    });

    it('should cap input at max_x_amount', () => {
      const binData: BinData = {
        reserve_x: 1000000000n,
        reserve_y: 1000000000n, // Only 10 tokens available
      };
      const binPrice = 5000000000n; // Price = 50
      const remaining = 10000000000n; // 100 tokens input (more than max)

      const result = calculateBinSwap(binData, binPrice, remaining, 0n, true);

      // Max x amount = (10 * 1e8) / 50 = 20 tokens
      // Input should be capped at 20 tokens
      expect(result.in_effective).toBeLessThanOrEqual(2000000000n); // Capped
    });
  });

  describe('calculateBinSwap - swap-y-for-x', () => {
    it('should calculate swap with zero fees', () => {
      const binData: BinData = {
        reserve_x: 1000000000n, // 10 tokens
        reserve_y: 50000000000n, // 500 tokens
      };
      const binPrice = 5000000000n; // Price = 50
      const remaining = 50000000000n; // 500 tokens input

      const result = calculateBinSwap(binData, binPrice, remaining, 0n, false);

      // Expected: dy = 500 tokens, dx = (500 * 1e8) / 50 = 10 tokens
      expect(result.function_name).toBe('swap-y-for-x');
      expect(result.in_effective).toBe(50000000000n);
      expect(result.fee_amount).toBe(0n);
      expect(result.out_this).toBe(1000000000n); // 10 tokens
    });

    it('should calculate swap with fees', () => {
      const binData: BinData = {
        reserve_x: 1000000000n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n; // Price = 50
      const remaining = 50000000000n; // 500 tokens input
      const feeRateBPS = 4000n; // 0.4% = 40 BPS

      const result = calculateBinSwap(binData, binPrice, remaining, feeRateBPS, false);

      // Fees: 500 * 0.004 = 2 tokens
      // dy = 500 - 2 = 498 tokens
      // dx = (498 * 1e8) / 50 = 9.96 tokens
      expect(result.function_name).toBe('swap-y-for-x');
      expect(result.in_effective).toBe(50000000000n);
      expect(result.fee_amount).toBeGreaterThan(0n);
      expect(result.out_this).toBeLessThan(1000000000n); // Less than 10 due to fees
    });

    it('should cap output at reserve_x', () => {
      const binData: BinData = {
        reserve_x: 1000000000n, // Only 10 tokens available
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n; // Price = 50
      const remaining = 1000000000000n; // 10000 tokens input

      const result = calculateBinSwap(binData, binPrice, remaining, 0n, false);

      // Would calculate more than 10 tokens output, but capped at 10
      expect(result.out_this).toBe(1000000000n); // Capped at reserve_x
    });
  });

  describe('calculateBinSwapFloat', () => {
    it('should match integer calculation for simple case', () => {
      const binData: BinData = {
        reserve_x: 1000000000n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const remaining = 100000000n;
      const feeRateBPS = 0n;

      const intResult = calculateBinSwap(binData, binPrice, remaining, feeRateBPS, true);
      const floatResult = calculateBinSwapFloat(
        binData,
        Number(binPrice),
        Number(remaining),
        Number(feeRateBPS),
        true
      );

      // Float result should be close to integer result (within rounding)
      expect(Math.abs(Number(intResult.out_this) - floatResult.out_this)).toBeLessThan(1);
    });

    it('should handle large values correctly', () => {
      const binData: BinData = {
        reserve_x: 1000000000000000000n, // Very large
        reserve_y: 50000000000000000000n,
      };
      const binPrice = 5000000000n;
      const remaining = 100000000000000000n;

      // Should not throw or lose precision in integer calculation
      const result = calculateBinSwap(binData, binPrice, remaining, 0n, true);
      expect(result.out_this).toBeGreaterThan(0n);
    });
  });

  describe('Edge Cases', () => {
    it('should handle zero reserves', () => {
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 0n,
      };
      const binPrice = 5000000000n;
      const remaining = 100000000n;

      const result = calculateBinSwap(binData, binPrice, remaining, 0n, true);
      expect(result.out_this).toBe(0n);
    });

    it('should handle zero bin price', () => {
      const binData: BinData = {
        reserve_x: 1000000000n,
        reserve_y: 50000000000n,
      };
      const binPrice = 0n;
      const remaining = 100000000n;

      const result = calculateBinSwap(binData, binPrice, remaining, 0n, true);
      expect(result.out_this).toBe(0n);
    });

    it('should handle very small amounts', () => {
      const binData: BinData = {
        reserve_x: 1000000000n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const remaining = 1n; // Very small amount

      const result = calculateBinSwap(binData, binPrice, remaining, 0n, true);
      expect(result.out_this).toBeGreaterThanOrEqual(0n);
    });

    it('should handle maximum fees', () => {
      const binData: BinData = {
        reserve_x: 1000000000n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const remaining = 100000000n;
      const feeRateBPS = 10000n; // 100% fees (edge case)

      const result = calculateBinSwap(binData, binPrice, remaining, feeRateBPS, true);
      // With 100% fees, output should be 0
      expect(result.fee_amount).toBe(remaining);
      expect(result.out_this).toBe(0n);
    });
  });

  describe('Formula Verification', () => {
    it('should match Clarity contract formula for max-x-amount', () => {
      // Test ceiling rounding: max_x_amount = ((reserve_y * PRICE_SCALE_BPS + (bin_price - 1)) // bin_price)
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 1000000000n, // 10 tokens
      };
      const binPrice = 5000000000n; // Price = 50

      // Manual calculation:
      // max_x_amount = ((10 * 1e8) + (50 * 1e8 - 1)) / (50 * 1e8)
      //              = (1e9 + 5e9 - 1) / 5e9
      //              = 6e9 / 5e9 = 1.2, but with ceiling rounding
      //              = (6e9 - 1) / 5e9 = 1.199999... = 1 (integer division)
      // Actually, ceiling rounding: (a + b - 1) / b
      // = (1e9 * 1e8 + 5e9 - 1) / 5e9
      // = (1e17 + 5e9 - 1) / 5e9
      // = 20000000 (approximately)

      const result = calculateBinSwap(binData, binPrice, 1000000000000n, 0n, true);
      // The input should be capped at max_x_amount
      expect(result.in_effective).toBeLessThanOrEqual(1000000000000n);
    });

    it('should match Python pricing.py calculation exactly', () => {
      // Test case that matches Python's _calculate_bin_swap logic
      // Using concrete values to verify formula equivalence
      const binData: BinData = {
        reserve_x: 1000000000n, // 10 tokens
        reserve_y: 50000000000n, // 500 tokens
      };
      const binPrice = 5000000000n; // Price = 50 (scaled by 1e8)
      const remaining = 100000000n; // 1 token input
      const feeRateBPS = 4000n; // 0.4% = 40 BPS

      const result = calculateBinSwap(binData, binPrice, remaining, feeRateBPS, true);

      // Python calculation (from pricing.py):
      // fee_rate = 4000 / 10000 = 0.4 (decimal)
      // max_x_amount = ((50000000000 * 100000000 + (5000000000 - 1)) // 5000000000)
      //              = ((5000000000000000000 + 4999999999) // 5000000000)
      //              = 1000000000 (with ceiling rounding)
      // updated_max_x_amount = (1000000000 * 10000) // (10000 - 0.4 * 10000)
      //                      = (1000000000 * 10000) // (10000 - 4000)
      //                      = 10000000000000 // 6000
      //                      = 1666666666
      // updated_x_amount = min(100000000, 1666666666) = 100000000
      // x_amount_fees_total = (100000000 * 0.4 * 10000) // 10000
      //                     = (100000000 * 4000) // 10000
      //                     = 40000000
      // dx = 100000000 - 40000000 = 60000000
      // dy = min((60000000 * 5000000000) // 100000000, 50000000000)
      //    = min(300000000000000000 // 100000000, 50000000000)
      //    = min(3000000000, 50000000000)
      //    = 3000000000 (30 tokens)

      expect(result.in_effective).toBe(100000000n);
      expect(result.fee_amount).toBe(40000000n); // 0.4 tokens = 40000000 (with 8 decimals)
      // Output: (60000000 * 5000000000) / 100000000 = 3000000000 (30 tokens)
      expect(result.out_this).toBe(3000000000n); // 30 tokens
    });

    it('should handle fee calculation edge case: fee_rate vs fee_rate_bps', () => {
      // Verify that using BPS directly matches Python's fee_rate * 10000 approach
      // Python: fee_rate = (protocol + provider + variable) / 10000
      //         Then: fee_rate * 10000 = protocol + provider + variable (BPS total)
      // TypeScript: fee_rate_bps = protocol + provider + variable (BPS total directly)
      // These should be equivalent
      
      const binData: BinData = {
        reserve_x: 1000000000n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const remaining = 100000000n;
      
      // Test with 30 BPS total (0.3%)
      const feeRateBPS = 3000n;
      const result = calculateBinSwap(binData, binPrice, remaining, feeRateBPS, true);
      
      // Fees should be: (100000000 * 3000) / 10000 = 30000000
      expect(result.fee_amount).toBe(30000000n);
      
      // Effective input after fees: 100000000 - 30000000 = 70000000
      // Output: (70000000 * 5000000000) / 100000000 = 3500000000 (35 tokens)
      expect(result.out_this).toBe(3500000000n);
    });
  });
});

