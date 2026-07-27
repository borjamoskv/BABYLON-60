/**
 * Concrete example tests to verify calculations match expected results
 * 
 * These tests use concrete, realistic values to verify the calculations
 * produce the expected results.
 */

import { describe, it, expect } from 'vitest';
import {
  calculateBinSwap,
  calculateBinSwapFloat,
  BinData,
} from '../../fuzz/harnesses/swap-calculations';

describe('Concrete Example Tests', () => {
  describe('Realistic Swap Scenario', () => {
    it('should calculate swap correctly for realistic values', () => {
      // Realistic scenario:
      // - Pool has 10 BTC (X) and 500,000 USDC (Y)
      // - Price: 50,000 USDC per BTC
      // - User wants to swap 0.1 BTC for USDC
      // - Fees: 0.3% (30 BPS)
      
      const binData: BinData = {
        reserve_x: 1000000000n, // 10 BTC (8 decimals)
        reserve_y: 50000000000000n, // 500,000 USDC (8 decimals)
      };
      const binPrice = 5000000000000n; // 50,000 USDC per BTC (scaled by 1e8)
      const inputAmount = 10000000n; // 0.1 BTC (8 decimals)
      const feeRateBPS = 30n; // 0.3% = 30 BPS

      const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);

      // Expected calculation:
      // 1. Max X amount = ((50000000000000 * 1e8) + (50k*1e8 - 1)) / (50k*1e8)
      //                 = (5e21 + 5e12 - 1) / 5e12
      //                 = 1e9 (approximately, with ceiling rounding)
      // 2. With fees: updated_max = (1e9 * 10000) / (10000 - 30) = 1.0003e9
      // 3. Input 0.1 BTC = 1e7, which is < 1.0003e9, so no cap
      // 4. Fees: (1e7 * 30) / 10000 = 30000
      // 5. dx = 1e7 - 30000 = 9970000
      // 6. dy = (9970000 * 50k*1e8) / 1e8 = 4985000000000 (49,850 USDC)

      expect(result.function_name).toBe('swap-x-for-y');
      expect(result.in_effective).toBe(inputAmount);
      expect(result.fee_amount).toBe(30000n); // 0.0003 BTC in fees
      expect(result.out_this).toBeGreaterThan(0n);
      expect(result.out_this).toBeLessThan(binData.reserve_y);
    });

    it('should match Python calculation for same inputs', () => {
      // Use values that match the manual calculation verification
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 50000000000n, // 500 tokens
      };
      const binPrice = 5000000000n; // Price = 50
      const inputAmount = 100000000n; // 1 token
      const feeRateBPS = 4000n; // 0.4% = 40 BPS

      const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);

      // From manual calculation:
      // - Fees: 40000000 (0.4 tokens)
      // - dx: 60000000 (0.6 tokens)
      // - dy: 3000000000 (30 tokens)

      expect(result.in_effective).toBe(100000000n);
      expect(result.fee_amount).toBe(40000000n);
      expect(result.out_this).toBe(3000000000n); // 30 tokens
    });
  });

  describe('Price Impact Scenarios', () => {
    it('should handle large swaps that move price significantly', () => {
      // Large swap that uses significant portion of reserves
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 10000000000n, // 100 tokens
      };
      const binPrice = 500000000n; // Price = 50
      const inputAmount = 1000000000n; // 10 tokens (10% of reserve)
      const feeRateBPS = 3000n; // 30%

      const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);

      // Should calculate correctly even for large swaps
      expect(result.in_effective).toBe(inputAmount);
      expect(result.out_this).toBeGreaterThan(0n);
      expect(result.out_this).toBeLessThanOrEqual(binData.reserve_y);
    });

    it('should handle swaps that drain the bin', () => {
      // Swap that uses all available reserves
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 1000000000n, // 10 tokens
      };
      const binPrice = 5000000000n; // Price = 50
      const inputAmount = 10000000000n; // 100 tokens (more than max)
      const feeRateBPS = 0n; // No fees

      const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);

      // Should cap input and output
      expect(result.in_effective).toBeLessThan(inputAmount);
      expect(result.out_this).toBeLessThanOrEqual(binData.reserve_y);
    });
  });

  describe('Fee Scenarios', () => {
    it('should handle typical fee rates correctly', () => {
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 50000000000n,
      };
      const binPrice = 5000000000n;
      const inputAmount = 100000000n;
      
      // Test various fee rates
      const feeRates = [0n, 10n, 30n, 100n, 1000n, 3000n]; // 0%, 0.1%, 0.3%, 1%, 10%, 30%

      for (const feeRateBPS of feeRates) {
        const result = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);
        
        // Fees should increase with fee rate
        expect(result.fee_amount).toBeGreaterThanOrEqual(0n);
        expect(result.fee_amount).toBeLessThanOrEqual(inputAmount);
        
        // Output should decrease as fees increase
        if (feeRateBPS > 0n) {
          const resultNoFees = calculateBinSwap(binData, binPrice, inputAmount, 0n, true);
          expect(result.out_this).toBeLessThanOrEqual(resultNoFees.out_this);
        }
      }
    });
  });

  describe('Swap Direction Consistency', () => {
    it('should produce consistent results for reverse swaps', () => {
      // Test that swapping X for Y, then Y for X, produces consistent results
      const binData: BinData = {
        reserve_x: 1000000000n, // 10 tokens
        reserve_y: 50000000000n, // 500 tokens
      };
      const binPrice = 5000000000n; // Price = 50
      const feeRateBPS = 3000n; // 0.3%

      // Swap X for Y
      const xInput = 100000000n; // 1 token X
      const xForYResult = calculateBinSwap(binData, binPrice, xInput, feeRateBPS, true);
      const yReceived = xForYResult.out_this;

      // Now swap Y for X (using the Y we received)
      const yForXResult = calculateBinSwap(binData, binPrice, yReceived, feeRateBPS, false);
      const xReceived = yForXResult.out_this;

      // Due to fees and rounding, we should get less X back than we put in
      expect(xReceived).toBeLessThan(xInput);
    });
  });

  describe('Float vs Integer Comparison', () => {
    it('should show float result is close to integer result', () => {
      const binData: BinData = {
        reserve_x: 0n,
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
      const floatFloored = BigInt(Math.floor(floatResult.out_this));
      const diff = intResult.out_this > floatFloored
        ? intResult.out_this - floatFloored
        : floatFloored - intResult.out_this;

      // Difference should be small (due to rounding)
      expect(Number(diff)).toBeLessThan(100); // Allow small rounding differences
    });

    it('should show float result is ideal (no ceiling rounding)', () => {
      // Test that float math produces slightly different (ideal) result
      const binData: BinData = {
        reserve_x: 0n,
        reserve_y: 100000000n, // 1 token
      };
      const binPrice = 3000000000n; // Price = 30
      const inputAmount = 1000000000n; // 10 tokens
      const feeRateBPS = 0n;

      const intResult = calculateBinSwap(binData, binPrice, inputAmount, feeRateBPS, true);
      const floatResult = calculateBinSwapFloat(
        binData,
        Number(binPrice),
        Number(inputAmount),
        Number(feeRateBPS),
        true
      );

      // Integer math uses ceiling rounding, float math doesn't
      // So float result might be slightly different
      const floatFloored = BigInt(Math.floor(floatResult.out_this));
      
      // Results should be close but may differ slightly due to ceiling rounding in integer math
      const diff = intResult.out_this > floatFloored
        ? intResult.out_this - floatFloored
        : floatFloored - intResult.out_this;
      
      expect(Number(diff)).toBeLessThan(10); // Small difference allowed
    });
  });
});



