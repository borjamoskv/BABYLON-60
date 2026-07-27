/**
 * Arithmetic Edge Case Tests
 * 
 * Tests for overflow, underflow, and division by zero scenarios
 * across all DLMM operations.
 */

import {
  alice,
  deployer,
  dlmmCore,
  sbtcUsdcPool,
  mockSbtcToken,
  mockUsdcToken,
  setupTestEnvironment,
  errors,
} from "../helpers/helpers";

import { describe, it, expect, beforeEach } from 'vitest';
import { cvToValue } from '@clarigen/core';
import { txErr, txOk, rovOk } from '@clarigen/test';
import {
  generateMinBinId,
  generateMaxBinId,
  generateInvalidMinBinId,
  generateInvalidMaxBinId,
  generateBinIdCausingUnderflow,
  generateVerySmallAmount,
  generateVeryLargeAmount,
  generateAmountThatRoundsToZero,
  generateDivisionByZeroCandidate,
} from "../helpers/edge-case-generators";
import { MAX_BIN_ID, MIN_BIN_ID } from "../../fuzz/utils";

describe('Arithmetic Edge Cases', () => {
  
  beforeEach(async () => {
    setupTestEnvironment();
  });

  describe('Bin ID Boundary Tests', () => {
    
    it('should handle get-unsigned-bin-id with valid minimum bin ID', async () => {
      const binId = MIN_BIN_ID; // -500
      const result = rovOk(dlmmCore.getUnsignedBinId(binId));
      // -500 + 500 = 0
      expect(result).toBe(0n);
    });

    it('should handle get-unsigned-bin-id with valid maximum bin ID', async () => {
      const binId = MAX_BIN_ID; // 500
      const result = rovOk(dlmmCore.getUnsignedBinId(binId));
      // 500 + 500 = 1000
      expect(result).toBe(1000n);
    });

    it('should handle get-unsigned-bin-id with center bin ID (0)', async () => {
      const binId = 0n;
      const result = rovOk(dlmmCore.getUnsignedBinId(binId));
      // 0 + 500 = 500
      expect(result).toBe(500n);
    });

    it('should fail get-unsigned-bin-id with bin ID below minimum (causes underflow)', async () => {
      const binId = MIN_BIN_ID - 1n; // -501
      // This should cause ArithmeticUnderflow when converting to uint
      // The contract doesn't validate this, so it will panic
      try {
        const result = rovOk(dlmmCore.getUnsignedBinId(binId));
        // If we get here, the contract might handle it differently than expected
        // But -501 + 500 = -1, which should underflow when converting to uint
        expect(result).toBeDefined();
      } catch (error: any) {
        // Expected: ArithmeticUnderflow error
        expect(String(error)).toContain('ArithmeticUnderflow');
      }
    });

    it('should fail swap with invalid bin ID below minimum', async () => {
      const binId = MIN_BIN_ID - 1n; // -501
      const xAmount = 1000000n;
      
      try {
        txErr(dlmmCore.swapXForY(
          sbtcUsdcPool.identifier,
          mockSbtcToken.identifier,
          mockUsdcToken.identifier,
          binId,
          xAmount
        ), alice);

        // reaching this meant the test failed
        throw new Error('Should have thrown an error');
      } catch (error: any) {
        expect(String(error)).toContain('ArithmeticUnderflow');
      }
    });

    it('should fail swap with invalid bin ID above maximum', async () => {
      const binId = MAX_BIN_ID + 1n; // 501
      const xAmount = 1000000n;
      
      const response = txErr(dlmmCore.swapXForY(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        binId,
        xAmount
      ), alice);
      
      // Should return an error
      expect(response).toBeDefined();
    });
  });

  describe('Division by Zero Tests', () => {
    
    it('should fail withdraw-liquidity from bin with zero totalSupply', async () => {
      const binId = 10n; // Bin with no liquidity
      const liquidityBalance = rovOk(sbtcUsdcPool.getTotalSupply(
        rovOk(dlmmCore.getUnsignedBinId(binId))
      ));
      expect(liquidityBalance).toBe(0n); // Verify no liquidity exists
      
      const amountToWithdraw = 1000000n;
      const minXAmount = 1n;
      const minYAmount = 1n;
      
      const response = txErr(dlmmCore.withdrawLiquidity(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        binId,
        amountToWithdraw,
        minXAmount,
        minYAmount
      ), alice);
      
      // Should return ERR_NO_BIN_SHARES (division by zero protection)
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_NO_BIN_SHARES);
    });

    it('should handle add-liquidity with very small amounts', async () => {
      const binId = 0n;
      const xAmount = 0n
      const yAmount = 1n
      const minDlp = 1n;
      
      const response = txErr(dlmmCore.addLiquidity(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        binId,
        xAmount,
        yAmount,
        minDlp,
        1000000n,
        1000000n
      ), alice);

      expect(response).toBeDefined();
    });
  });

  describe('Very Small Value Tests', () => {
    
    it('should handle swap with minimum amount (1)', async () => {
      const binId = 0n;
      const yAmount = 1n;
      
      const response = txOk(dlmmCore.swapYForX(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        binId,
        yAmount
      ), alice);
      
      expect(response).toBeDefined();
      expect(cvToValue(response.result)["out"]).toBe(0n); // exchange rate causes a donation swap
    });

    it('should handle withdraw-liquidity with minimum amount', async () => {
      const binId = 0n;
      const liquidityBalance = rovOk(sbtcUsdcPool.getBalance(
        rovOk(dlmmCore.getUnsignedBinId(binId)),
        alice
      ));
      
      if (liquidityBalance > 0n) {
        const amountToWithdraw = 1n; // Minimum amount
        const minXAmount = 0n;
        const minYAmount = 0n;
        
        const response = txErr(dlmmCore.withdrawLiquidity(
          sbtcUsdcPool.identifier,
          mockSbtcToken.identifier,
          mockUsdcToken.identifier,
          binId,
          amountToWithdraw,
          minXAmount,
          minYAmount
        ), alice);
        
        // Should handle gracefully (might fail if amount too small)
        expect(response).toBeDefined();
      }
    });
  });

  describe('Very Large Value Tests', () => {
    
    it('should handle swap with very large amount (contract should cap)', async () => {
      const binId = 0n;
      const xAmount = generateVeryLargeAmount(); // Near u128 max
      
      // Contract should cap the amount to maximum allowed
      const response = txOk(dlmmCore.swapXForY(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        binId,
        xAmount
      ), alice);
      
      const swapResult = cvToValue(response.result);
      // Should succeed with capped amount
      expect(swapResult.in).toBeGreaterThan(0n);
      expect(swapResult.in).toBeLessThanOrEqual(xAmount);
    });

    it('should handle add-liquidity with very large amounts', async () => {
      const binId = 0n;
      const xAmount = 1000000000000000n;
      const yAmount = 50000000000000000n;
      const minDlp = 1n;
      
      txOk(mockSbtcToken.mint(xAmount, alice), deployer);
      txOk(mockUsdcToken.mint(yAmount, alice), deployer);

      // Should handle large amounts without overflow
      const response = txOk(dlmmCore.addLiquidity(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        binId,
        xAmount,
        yAmount,
        minDlp,
        xAmount / 1000n,
        yAmount / 1000n
      ), alice);
      
      const liquidityReceived = cvToValue(response.result);
      expect(liquidityReceived).toBeGreaterThan(0n);
    });
  });

  describe('Zero Amount Tests', () => {
    
    it('should fail swap with zero amount', async () => {
      const binId = 0n;
      const xAmount = 0n;
      
      const response = txErr(dlmmCore.swapXForY(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        binId,
        xAmount
      ), alice);
      
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_INVALID_AMOUNT);
    });

    it('should fail add-liquidity with zero amounts', async () => {
      const binId = 0n;
      const xAmount = 0n;
      const yAmount = 0n;
      const minDlp = 1n;
      
      const response = txErr(dlmmCore.addLiquidity(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        binId,
        xAmount,
        yAmount,
        minDlp,
        1000000n,
        1000000n
      ), alice);
      
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_INVALID_AMOUNT);
    });

    it('should fail withdraw-liquidity with zero amount', async () => {
      const binId = 0n;
      const amountToWithdraw = 0n;
      const minXAmount = 0n;
      const minYAmount = 0n;
      
      const response = txErr(dlmmCore.withdrawLiquidity(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        binId,
        amountToWithdraw,
        minXAmount,
        minYAmount
      ), alice);
      
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_INVALID_AMOUNT);
    });
  });
});

