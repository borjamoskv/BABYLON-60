import {
  alice,
  deployer,
  dlmmCore,
  dlmmLiquidityRouter,
  errors,
  sbtcUsdcPool,
  mockSbtcToken,
  mockUsdcToken,
  mockPool,
  mockRandomToken,
  setupTestEnvironment
} from "../helpers/helpers";

import { describe, it, expect, beforeEach } from 'vitest';
import {
  cvToValue,
} from '@clarigen/core';
import { txErr, txOk, rovOk } from '@clarigen/test';


let addBulkLiquidityOutput: { bin: bigint; xAmount: bigint; yAmount: bigint; liquidity: bigint;}[];

describe('DLMM Liquidity Router Functions', () => {
  
  beforeEach(async () => {
    addBulkLiquidityOutput = setupTestEnvironment();
  });

  describe('add-liquidity-multi Function', () => {
    it('should successfully add liquidity to single bin with valid parameters', async () => {
      const positions = [{
        poolTrait: sbtcUsdcPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockUsdcToken.identifier,
        binId: 0, // Active bin - can add both X and Y
        xAmount: 5000000n, // 0.05 BTC
        yAmount: 2500000000n, // 2500 USDC
        minDlp: 1n,
        maxXLiquidityFee: 1000000n,
        maxYLiquidityFee: 1000000n,
      }];
      
      const initialXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const initialYBalance = rovOk(mockUsdcToken.getBalance(alice));
      
      const response = txOk(dlmmLiquidityRouter.addLiquidityMulti(
        positions
      ), alice);
      
      const finalXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const finalYBalance = rovOk(mockUsdcToken.getBalance(alice));
      const lpReceived = cvToValue(response.result);
      
      expect(finalXBalance).toBeLessThan(initialXBalance);
      expect(finalYBalance).toBeLessThan(initialYBalance);
      // lpReceived is an array of results, one per position
      expect(Array.isArray(lpReceived)).toBe(true);
      expect(lpReceived.length).toBe(1);
      expect(lpReceived[0]).toBeGreaterThan(0n);
      expect(lpReceived[0]).toBeGreaterThanOrEqual(positions[0].minDlp);
    });

    it('should successfully add liquidity to multiple bins in same pool', async () => {
      const positions = [
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: -1, // Below active bin - only Y tokens
          xAmount: 0n, // No X tokens for bins below active
          yAmount: 1250000000n, // 1250 USDC
          minDlp: 1n,
          maxXLiquidityFee: 1000000n,
          maxYLiquidityFee: 1000000n,
        },
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: 0, // Active bin - both X and Y tokens
          xAmount: 2500000n, // 0.025 BTC
          yAmount: 1250000000n, // 1250 USDC
          minDlp: 1n,
          maxXLiquidityFee: 1000000n,
          maxYLiquidityFee: 1000000n,
        }
      ];
      
      const initialXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const initialYBalance = rovOk(mockUsdcToken.getBalance(alice));
      
      const response = txOk(dlmmLiquidityRouter.addLiquidityMulti(
        positions
      ), alice);
      
      const finalXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const finalYBalance = rovOk(mockUsdcToken.getBalance(alice));
      const lpReceived = cvToValue(response.result);
      
      expect(finalXBalance).toBeLessThan(initialXBalance);
      expect(finalYBalance).toBeLessThan(initialYBalance);
      // lpReceived is an array of results, one per position
      expect(Array.isArray(lpReceived)).toBe(true);
      expect(lpReceived.length).toBeGreaterThan(0);
      expect(lpReceived[0]).toBeGreaterThan(0n);
    });

    it('should successfully add liquidity to three bins across different ranges', async () => {
      const positions = [
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: -2, // Below active bin - only Y tokens
          xAmount: 0n, // No X tokens for bins below active
          yAmount: 750000000n, // 750 USDC
          minDlp: 1n,
          maxXLiquidityFee: 1000000n,
          maxYLiquidityFee: 1000000n,
        },
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: 0, // Active bin - both X and Y tokens
          xAmount: 1500000n, // 0.015 BTC
          yAmount: 750000000n, // 750 USDC
          minDlp: 1n,
          maxXLiquidityFee: 1000000n,
          maxYLiquidityFee: 1000000n,
        },
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: 2, // Above active bin - only X tokens
          xAmount: 1500000n, // 0.015 BTC
          yAmount: 0n, // No Y tokens for bins above active
          minDlp: 1n,
          maxXLiquidityFee: 1000000n,
          maxYLiquidityFee: 1000000n,
        }
      ];
      
      const initialXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const initialYBalance = rovOk(mockUsdcToken.getBalance(alice));
      
      const response = txOk(dlmmLiquidityRouter.addLiquidityMulti(
        positions
      ), alice);
      
      const finalXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const finalYBalance = rovOk(mockUsdcToken.getBalance(alice));
      const lpReceived = cvToValue(response.result);
      
      expect(finalXBalance).toBeLessThan(initialXBalance);
      expect(finalYBalance).toBeLessThan(initialYBalance);
      // lpReceived is an array of results, one per position
      expect(Array.isArray(lpReceived)).toBe(true);
      expect(lpReceived.length).toBeGreaterThan(0);
      expect(lpReceived[0]).toBeGreaterThan(0n);
    });

    it('should add liquidity to the same bin multiple times', async () => {
      const positions = [
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: 0, // Active bin - can add both X and Y
          xAmount: 2000000n, // 0.02 BTC
          yAmount: 1000000000n, // 1000 USDC
          minDlp: 1n,
          maxXLiquidityFee: 1000000n,
          maxYLiquidityFee: 1000000n,
        },
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: 0, // Active bin - can add both X and Y
          xAmount: 3000000n, // 0.03 BTC
          yAmount: 1500000000n, // 1500 USDC
          minDlp: 1n,
          maxXLiquidityFee: 1000000n,
          maxYLiquidityFee: 1000000n,
        }
      ];
      
      const initialXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const initialYBalance = rovOk(mockUsdcToken.getBalance(alice));
      
      const response = txOk(dlmmLiquidityRouter.addLiquidityMulti(
        positions
      ), alice);
      
      const finalXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const finalYBalance = rovOk(mockUsdcToken.getBalance(alice));
      const lpReceived = cvToValue(response.result);
      
      // Should use total amounts: 5000000n BTC and 2500000000n USDC
      expect(finalXBalance).toBeLessThan(initialXBalance);
      expect(finalYBalance).toBeLessThan(initialYBalance);
      // lpReceived is an array of results, one per position
      expect(Array.isArray(lpReceived)).toBe(true);
      expect(lpReceived.length).toBeGreaterThan(0);
      expect(lpReceived[0]).toBeGreaterThan(0n);
    });

    it('should fail when minimum LP amount not met', async () => {
      const positions = [{
        poolTrait: sbtcUsdcPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockUsdcToken.identifier,
        binId: 0, // Active bin - can add both X and Y
        xAmount: 1000n, // Very small amount
        yAmount: 500000n, // Very small amount
        minDlp: 999999999999n, // Unreasonably high minimum
        maxXLiquidityFee: 1000000n,
        maxYLiquidityFee: 1000000n,
      }];
      
      const response = txErr(dlmmLiquidityRouter.addLiquidityMulti(
        positions
      ), alice);
      
      // The error comes from the core contract, not the router
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_MINIMUM_LP_AMOUNT);
    });

    it('should revert on empty positions list when adding liquidity', async () => {
      const positions: any[] = [];
      
      const response = txErr(dlmmLiquidityRouter.addLiquidityMulti(
        positions
      ), alice);
      
      // will add specific error when it is set
      expect(cvToValue(response.result)).toBeGreaterThan(0n);
    });

    it('should handle positions with zero amounts', async () => {
      const positions = [{
        poolTrait: sbtcUsdcPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockUsdcToken.identifier,
        binId: 0, // Active bin - can add both X and Y
        xAmount: 0n,
        yAmount: 0n,
        minDlp: 0n,
        maxXLiquidityFee: 1000000n,
        maxYLiquidityFee: 1000000n,
      }];
      
      // This should fail at the core add-liquidity level with invalid amount
      const response = txErr(dlmmLiquidityRouter.addLiquidityMulti(
        positions
      ), alice);
      
      // The error should propagate from the dlmm-core add-liquidity function
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_INVALID_AMOUNT);
    });

    it('should handle maximum number of positions in a single call', async () => {
      // Test with multiple positions to stress test the fold function
      const positions = Array.from({ length: 10 }, (_, i) => {
        const binId = i - 5; // Range from -5 to 4
        return {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: binId,
          // Only add X tokens to bins >= 0 (active bin and above)
          xAmount: binId >= 0 ? 500000n : 0n, // 0.005 BTC each for valid bins
          // Only add Y tokens to bins <= 0 (active bin and below)
          yAmount: binId <= 0 ? 250000000n : 0n, // 250 USDC each for valid bins
          minDlp: 1n,
          maxXLiquidityFee: 1000000n,
          maxYLiquidityFee: 1000000n,
        };
      });
      
      const initialXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const initialYBalance = rovOk(mockUsdcToken.getBalance(alice));
      
      const response = txOk(dlmmLiquidityRouter.addLiquidityMulti(
        positions
      ), alice);
      
      const finalXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const finalYBalance = rovOk(mockUsdcToken.getBalance(alice));
      const lpReceived = cvToValue(response.result);
      
      expect(finalXBalance).toBeLessThan(initialXBalance);
      expect(finalYBalance).toBeLessThan(initialYBalance);
      // lpReceived is an array of results, one per position
      expect(Array.isArray(lpReceived)).toBe(true);
      expect(lpReceived.length).toBeGreaterThan(0);
      expect(lpReceived[0]).toBeGreaterThan(0n);
    });

    it('should document ERR_NO_RESULT_DATA error condition for add-liquidity', async () => {
      // ERR_NO_RESULT_DATA occurs when the result parameter in fold-add-liquidity-multi is an error
      // This is difficult to trigger directly as it's an internal fold state
      // This test documents the theoretical scenario
      const positions = [{
        poolTrait: sbtcUsdcPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockUsdcToken.identifier,
        binId: 0, // Active bin - can add both X and Y
        xAmount: 5000000n,
        yAmount: 2500000000n,
        minDlp: 1n,
        maxXLiquidityFee: 1000000n,
        maxYLiquidityFee: 1000000n,
      }];
      
      // In normal circumstances this should succeed
      // ERR_NO_RESULT_DATA would require internal fold failure
      const response = txOk(dlmmLiquidityRouter.addLiquidityMulti(
        positions
      ), alice);
      
      const lpReceived = cvToValue(response.result);
      // result is an array of LP amounts
      expect(Array.isArray(lpReceived)).toBe(true);
      expect(lpReceived[0]).toBeGreaterThan(0n);
    });
  });

  describe('withdraw-liquidity-multi Function', () => {
    beforeEach(async () => {
      // Add some liquidity first to have something to withdraw
      const positions = [
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: -1, // Below active bin - only Y tokens
          xAmount: 0n, // No X tokens for bins below active
          yAmount: 2500000000n, // 2500 USDC
          minDlp: 1n,
          maxXLiquidityFee: 1000000n,
          maxYLiquidityFee: 1000000n,
        },
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: 0, // Active bin - both X and Y tokens
          xAmount: 5000000n, // 0.05 BTC
          yAmount: 2500000000n, // 2500 USDC
          minDlp: 1n,
          maxXLiquidityFee: 1000000n,
          maxYLiquidityFee: 1000000n,
        },
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: 1, // Above active bin - only X tokens
          xAmount: 5000000n, // 0.05 BTC
          yAmount: 0n, // No Y tokens for bins above active
          minDlp: 1n,
          maxXLiquidityFee: 1000000n,
          maxYLiquidityFee: 1000000n,
        }
      ];
      txOk(dlmmLiquidityRouter.addLiquidityMulti(positions), alice);
    });

    it('should successfully withdraw liquidity from single bin', async () => {
      const positions = [{
        poolTrait: sbtcUsdcPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockUsdcToken.identifier,
        binId: 0,
        amount: 1000000n, // 1M LP tokens
        minXAmount: 1n,
        minYAmount: 1n,
      }];
      
      const initialXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const initialYBalance = rovOk(mockUsdcToken.getBalance(alice));
      
      const response = txOk(dlmmLiquidityRouter.withdrawLiquidityMulti(
        positions
      ), alice);
      
      const finalXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const finalYBalance = rovOk(mockUsdcToken.getBalance(alice));
      const result = cvToValue(response.result);
      
      // result is an array of {xAmount, yAmount} tuples
      expect(Array.isArray(result)).toBe(true);
      expect(result.length).toBe(1);
      expect(finalXBalance).toBeGreaterThan(initialXBalance);
      expect(finalYBalance).toBeGreaterThan(initialYBalance);
      expect(result[0].xAmount).toBeGreaterThan(0n);
      expect(result[0].yAmount).toBeGreaterThan(0n);
    });

    it('should successfully withdraw liquidity from multiple bins', async () => {
      const positions = [
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: -1,
          amount: 500000n, // 500K LP tokens
          minXAmount: 0n, // Bin -1 only has Y tokens
          minYAmount: 1n,
        },
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: 0,
          amount: 500000n, // 500K LP tokens
          minXAmount: 1n,
          minYAmount: 1n,
        }
      ];
      
      const initialXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const initialYBalance = rovOk(mockUsdcToken.getBalance(alice));
      
      const response = txOk(dlmmLiquidityRouter.withdrawLiquidityMulti(
        positions
      ), alice);
      
      const finalXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const finalYBalance = rovOk(mockUsdcToken.getBalance(alice));
      const result = cvToValue(response.result);
      
      // result is an array of {xAmount, yAmount} tuples
      expect(Array.isArray(result)).toBe(true);
      expect(result.length).toBe(2);
      expect(finalXBalance).toBeGreaterThan(initialXBalance);
      expect(finalYBalance).toBeGreaterThan(initialYBalance);
      expect(result[0].xAmount).toBe(0n); // Bin -1 only has Y
      expect(result[0].yAmount).toBeGreaterThan(0n);
      expect(result[1].xAmount).toBeGreaterThan(0n);
      expect(result[1].yAmount).toBeGreaterThan(0n);
    });

    it('should successfully withdraw from three different bins', async () => {
      const positions = [
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: -1,
          amount: 300000n, // 300K LP tokens
          minXAmount: 0n, // Bin -1 only has Y
          minYAmount: 1n,
        },
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: 0,
          amount: 300000n, // 300K LP tokens
          minXAmount: 1n,
          minYAmount: 1n,
        },
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: 1,
          amount: 300000n, // 300K LP tokens
          minXAmount: 1n,
          minYAmount: 0n, // Bin 1 only has X
        }
      ];
      
      const initialXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const initialYBalance = rovOk(mockUsdcToken.getBalance(alice));
      
      const response = txOk(dlmmLiquidityRouter.withdrawLiquidityMulti(
        positions
      ), alice);
      
      const finalXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const finalYBalance = rovOk(mockUsdcToken.getBalance(alice));
      const result = cvToValue(response.result);
      
      // result is an array of {xAmount, yAmount} tuples
      expect(Array.isArray(result)).toBe(true);
      expect(result.length).toBe(positions.length);
      expect(finalXBalance).toBeGreaterThan(initialXBalance);
      expect(finalYBalance).toBeGreaterThan(initialYBalance);
      result.forEach((r: any) => {
        expect(r.xAmount + r.yAmount).toBeGreaterThan(0n);
      });
    });

    it('should withdraw from the same bin multiple times', async () => {
      const positions = [
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: 0,
          amount: 200000n, // 200K LP tokens
        },
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: 0,
          amount: 300000n, // 300K LP tokens
        }
      ];
      // Add minXAmount and minYAmount to each position
      positions.forEach((pos: any) => {
        if (!pos.minXAmount) pos.minXAmount = 1n;
        if (!pos.minYAmount) pos.minYAmount = 1n;
      });
      
      const initialXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const initialYBalance = rovOk(mockUsdcToken.getBalance(alice));
      
      const response = txOk(dlmmLiquidityRouter.withdrawLiquidityMulti(
        positions
      ), alice);
      
      const finalXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const finalYBalance = rovOk(mockUsdcToken.getBalance(alice));
      const result = cvToValue(response.result);
      
      // result is an array of {xAmount, yAmount} tuples
      expect(Array.isArray(result)).toBe(true);
      expect(result.length).toBe(positions.length);
      expect(finalXBalance).toBeGreaterThan(initialXBalance);
      expect(finalYBalance).toBeGreaterThan(initialYBalance);
      result.forEach((r: any) => {
        expect(r.xAmount + r.yAmount).toBeGreaterThan(0n);
      });
    });

    it('should fail when minimum X amount not met', async () => {
      const positions = [{
        poolTrait: sbtcUsdcPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockUsdcToken.identifier,
        binId: 0,
        amount: 100000n, // Small amount
        minXAmount: 999999999999n, // Unreasonably high minimum
        minYAmount: 1n,
      }];
      
      const response = txErr(dlmmLiquidityRouter.withdrawLiquidityMulti(
        positions
      ), alice);
      
      // The error comes from the core contract, not the router
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_MINIMUM_X_AMOUNT);
    });

    it('should fail when minimum Y amount not met', async () => {
      const positions = [{
        poolTrait: sbtcUsdcPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockUsdcToken.identifier,
        binId: 0,
        amount: 100000n, // Small amount
        minXAmount: 1n,
        minYAmount: 999999999999n, // Unreasonably high minimum
      }];
      
      const response = txErr(dlmmLiquidityRouter.withdrawLiquidityMulti(
        positions
      ), alice);
      
      // The error comes from the core contract, not the router
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_MINIMUM_Y_AMOUNT);
    });

    it('should not allow empty positions list when withdrawing liquidity', async () => {
      // this test will fail
      const positions: any[] = [];
      
      const response = txErr(dlmmLiquidityRouter.withdrawLiquidityMulti(
        positions
      ), alice);

      // will add specific error code when it's set
      expect(cvToValue(response.result)).toBeGreaterThan(0n);
      // expect(cvToValue(response.result)).toBe(errors.dlmmLiquidityRouter.ERR_MINIMUM_Y_AMOUNT);
    });

    it('should handle positions with zero amounts', async () => {
      const positions = [{
        poolTrait: sbtcUsdcPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockUsdcToken.identifier,
        binId: 0,
        amount: 0n,
        minXAmount: 0n,
        minYAmount: 0n,
      }];
      
      // This should fail at the core withdraw-liquidity level with invalid amount
      const response = txErr(dlmmLiquidityRouter.withdrawLiquidityMulti(
        positions
      ), alice);
      
      // The error should propagate from the dlmm-core withdraw-liquidity function
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_INVALID_AMOUNT);
    });

    it('should handle multiple consecutive withdrawal positions in a single call', async () => {
      // Test with multiple positions to stress test the fold function
      // Only withdraw from bins that actually have liquidity: -1, 0, 1
      const positions = [
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: -1, // Has Y token liquidity
          amount: 100000n, // 100K LP tokens
          minXAmount: 0n, // Bin -1 only has Y
          minYAmount: 1n,
        },
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: 0, // Has both X and Y token liquidity
          amount: 100000n, // 100K LP tokens
          minXAmount: 1n,
          minYAmount: 1n,
        },
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: 1, // Has X token liquidity
          amount: 100000n, // 100K LP tokens
          minXAmount: 1n,
          minYAmount: 0n, // Bin 1 only has X
        }
      ];
      
      const initialXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const initialYBalance = rovOk(mockUsdcToken.getBalance(alice));
      
      const response = txOk(dlmmLiquidityRouter.withdrawLiquidityMulti(
        positions
      ), alice);
      
      const finalXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const finalYBalance = rovOk(mockUsdcToken.getBalance(alice));
      const result = cvToValue(response.result);
      
      // result is an array of {xAmount, yAmount} tuples
      expect(Array.isArray(result)).toBe(true);
      expect(result.length).toBe(positions.length);
      expect(finalXBalance).toBeGreaterThan(initialXBalance);
      expect(finalYBalance).toBeGreaterThan(initialYBalance);
      result.forEach((r: any) => {
        expect(r.xAmount + r.yAmount).toBeGreaterThan(0n);
      });
    });

    it('should handle edge case with different bin ranges and their min amounts logic', async () => {
      // Test the min-x-amount and min-y-amount logic in withdraw
      // For bin-id >= 0: min-x-amount = 1, min-y-amount = 0
      // For bin-id < 0: min-x-amount = 0, min-y-amount = 1
      const positions = [
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: -1, // Should set min-x-amount = 0, min-y-amount = 1
          amount: 500000n,
          minXAmount: 0n, // Bin -1 only has Y
          minYAmount: 1n,
        },
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: 1, // Should set min-x-amount = 1, min-y-amount = 0
          amount: 500000n,
          minXAmount: 1n,
          minYAmount: 0n, // Bin 1 only has X
        }
      ];
      
      const response = txOk(dlmmLiquidityRouter.withdrawLiquidityMulti(
        positions
      ), alice);
      
      const result = cvToValue(response.result);
      expect(Array.isArray(result)).toBe(true);
      expect(result.length).toBe(2);
      expect(result[0].xAmount).toBe(0n); // Bin -1 only has Y
      expect(result[0].yAmount).toBeGreaterThan(0n);
      expect(result[1].xAmount).toBeGreaterThan(0n);
      expect(result[1].yAmount).toBe(0n); // Bin 1 only has X
    });
  });

  describe('Mixed Operations', () => {
    it('should handle adding and then withdrawing liquidity from same bins', async () => {
      // First add liquidity
      const addPositions = [
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: 5, // Above active bin - only X tokens
          xAmount: 5000000n, // 0.05 BTC
          yAmount: 0n, // No Y tokens for bins above active
          minDlp: 1n,
          maxXLiquidityFee: 1000000n,
          maxYLiquidityFee: 1000000n,
        }
      ];
      
      const addResponse = txOk(dlmmLiquidityRouter.addLiquidityMulti(
        addPositions
      ), alice);
      
      const lpReceived = cvToValue(addResponse.result);
      expect(Array.isArray(lpReceived)).toBe(true);
      expect(lpReceived[0]).toBeGreaterThan(0n);
      
      // Then withdraw part of the liquidity
      const withdrawPositions = [
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          binId: 5,
          amount: lpReceived[0] / 2n, // Withdraw half
          minXAmount: 1n, // Expect X tokens since bin 5 is above active
          minYAmount: 0n, // Don't expect Y tokens since bin 5 is above active
        }
      ];
      
      const initialXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const initialYBalance = rovOk(mockUsdcToken.getBalance(alice));
      
      const withdrawResponse = txOk(dlmmLiquidityRouter.withdrawLiquidityMulti(
        withdrawPositions
      ), alice);
      
      const finalXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const finalYBalance = rovOk(mockUsdcToken.getBalance(alice));
      const result = cvToValue(withdrawResponse.result);
      
      expect(Array.isArray(result)).toBe(true);
      expect(result.length).toBe(1);
      expect(finalXBalance).toBeGreaterThan(initialXBalance);
      expect(finalYBalance).toBe(initialYBalance); // No Y tokens from bin 5
      expect(result[0].xAmount).toBeGreaterThan(0n);
      expect(result[0].yAmount).toBe(0n); // No Y tokens from bin 5
    });

    it('should handle edge cases with both functions using mock pool failures', async () => {
      // Test ERR_NO_RESULT_DATA through mock pool that can fail
      txOk(mockPool.setRevert(true), deployer);

      // Test add liquidity with failing pool
      const addPositions = [{
        poolTrait: mockPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockUsdcToken.identifier,
        binId: 0, // Active bin - can add both X and Y
        xAmount: 5000000n,
        yAmount: 2500000000n,
        minDlp: 1n,
        maxXLiquidityFee: 1000000n,
        maxYLiquidityFee: 1000000n,
      }];
      
      const addResponse = txErr(dlmmLiquidityRouter.addLiquidityMulti(
        addPositions
      ), alice);
      
      expect(cvToValue(addResponse.result)).toBe(errors.dlmmCore.ERR_NO_POOL_DATA);
      
      // Test withdraw liquidity with failing pool
      const withdrawPositions = [{
        poolTrait: mockPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockUsdcToken.identifier,
        binId: 0, // Active bin
        amount: 1000000n,
        minXAmount: 1n,
        minYAmount: 1n,
      }];
      
      const withdrawResponse = txErr(dlmmLiquidityRouter.withdrawLiquidityMulti(
        withdrawPositions
      ), alice);
      
      // The error comes from the core contract when pool doesn't exist
      expect(cvToValue(withdrawResponse.result)).toBe(errors.dlmmCore.ERR_NO_POOL_DATA);
    });

    it('should fail when adding liquidity with random X token', async () => {
      const activeBinId = 0n;

      // Mint random tokens for testing
      txOk(mockRandomToken.mint(10000000n, alice), deployer);

      const addPositions = [{
        poolTrait: sbtcUsdcPool.identifier,
        xTokenTrait: mockRandomToken.identifier, // Using random token
        yTokenTrait: mockUsdcToken.identifier,
        binId: activeBinId, // Active bin
        xAmount: 5000000n, // 0.05 BTC
        yAmount: 2500000000n, // 2500 USDC
        minDlp: 1n,
        maxXLiquidityFee: 1000000n,
        maxYLiquidityFee: 1000000n,
      }];
      
      const response = txErr(dlmmLiquidityRouter.addLiquidityMulti(
        addPositions
      ), alice);
      
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_INVALID_X_TOKEN);
    });

    it('should fail when adding liquidity with random Y token', async () => {
      const activeBinId = 0n;
      
      // Mint random tokens for testing
      txOk(mockRandomToken.mint(10000000n, alice), deployer);

      const addPositions = [{
        poolTrait: sbtcUsdcPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockRandomToken.identifier, // Using random token
        binId: activeBinId, // Active bin
        xAmount: 5000000n, // 0.05 BTC
        yAmount: 2500000000n, // 2500 USDC
        minDlp: 1n,
        maxXLiquidityFee: 1000000n,
        maxYLiquidityFee: 1000000n,
      }];
      
      const response = txErr(dlmmLiquidityRouter.addLiquidityMulti(
        addPositions
      ), alice);
      
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_INVALID_Y_TOKEN);
    });

    it('should fail when withdrawing liquidity with random X token', async () => {
      const activeBinId = 0n;

      // First add some liquidity to the pool (using valid tokens)
      txOk(dlmmCore.addLiquidity(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        activeBinId, // Active bin
        10000000n, // 0.1 BTC
        5000000000n, // 5000 USDC
        1n,
        1000000n, // max-x-liquidity-fee
        1000000n  // max-y-liquidity-fee
      ), alice);

      const withdrawPositions = [{
        poolTrait: sbtcUsdcPool.identifier,
        xTokenTrait: mockRandomToken.identifier, // Using random token
        yTokenTrait: mockUsdcToken.identifier,
        binId: activeBinId, // Active bin
        amount: 1000000n,
        minXAmount: 1n,
        minYAmount: 1n,
      }];
      
      const response = txErr(dlmmLiquidityRouter.withdrawLiquidityMulti(
        withdrawPositions
      ), alice);
      
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_INVALID_X_TOKEN);
    });

    it('should fail when withdrawing liquidity with random Y token', async () => {
      const activeBinId = 0n;
      // First add some liquidity to the pool (using valid tokens)
      txOk(dlmmCore.addLiquidity(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        activeBinId, // Active bin
        10000000n, // 0.1 BTC
        5000000000n, // 5000 USDC
        1n,
        1000000n, // max-x-liquidity-fee
        1000000n  // max-y-liquidity-fee
      ), alice);

      const withdrawPositions = [{
        poolTrait: sbtcUsdcPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockRandomToken.identifier, // Using random token
        binId: activeBinId, // Active bin
        amount: 1000000n,
        minXAmount: 1n,
        minYAmount: 1n,
      }];
      
      const response = txErr(dlmmLiquidityRouter.withdrawLiquidityMulti(
        withdrawPositions
      ), alice);
      
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_INVALID_Y_TOKEN);
    });
  });
});