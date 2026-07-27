import {
  alice,
  deployer,
  dlmmSwapRouter,
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

describe('DLMM Swap Helper Functions', () => {
  
  beforeEach(async () => {
    addBulkLiquidityOutput = setupTestEnvironment();
  });

  describe('swap-helper Function', () => {
    it('should successfully execute single swap with valid parameters', async () => {
      const swaps = [{
        poolTrait: sbtcUsdcPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockUsdcToken.identifier,
        expectedBinId: 0,
        amount: 1000000n, // 0.01 BTC
        minReceived: 1n,
        xForY: true
      }];
      const maxUnfavorableBins = 5n;
      
      const initialXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const initialYBalance = rovOk(mockUsdcToken.getBalance(alice));
      
      const response = txOk(dlmmSwapRouter.swapMulti(
        swaps,
        maxUnfavorableBins
      ), alice);
      
      const finalXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const finalYBalance = rovOk(mockUsdcToken.getBalance(alice));
      const result = cvToValue(response.result);
      const received = result.results.reduce((sum: bigint, r: {in: bigint, out: bigint}) => sum + r.out, 0n);
      
      expect(finalXBalance).toBeLessThan(initialXBalance);
      expect(finalYBalance).toBe(initialYBalance + received);
      expect(received).toBeGreaterThan(0n);
    });

    it('should successfully execute 2 swaps in same pool', async () => {
      const swaps = [
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          expectedBinId: 0,
          amount: 500000n, // 0.005 BTC
          minReceived: 1n,
          xForY: true
        },
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          expectedBinId: 1,
          amount: 500000n, // 0.005 BTC
          minReceived: 1n,
          xForY: true
        }
      ];
      const maxUnfavorableBins = 10n;
      
      const initialXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const initialYBalance = rovOk(mockUsdcToken.getBalance(alice));
      
      const response = txOk(dlmmSwapRouter.swapMulti(
        swaps,
        maxUnfavorableBins
      ), alice);
      
      const finalXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const finalYBalance = rovOk(mockUsdcToken.getBalance(alice));
      const result = cvToValue(response.result);
      const received = result.results.reduce((sum: bigint, r: {in: bigint, out: bigint}) => sum + r.out, 0n);
      
      expect(finalXBalance).toBe(initialXBalance - 1000000n); // Total amount swapped
      expect(finalYBalance).toBe(initialYBalance + received);
      expect(received).toBeGreaterThan(0n);
    });

    it('should successfully execute 3 swaps in same pool (different bins)', async () => {
      const swaps = [
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          expectedBinId: 0,
          amount: 300000n, // 0.003 BTC
          minReceived: 1n,
          xForY: true
        },
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          expectedBinId: 1,
          amount: 300000n, // 0.003 BTC
          minReceived: 1n,
          xForY: true
        },
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          expectedBinId: 2,
          amount: 300000n, // 0.003 BTC
          minReceived: 1n,
          xForY: true
        }
      ];
      const maxUnfavorableBins = 10n;
      
      const initialXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const initialYBalance = rovOk(mockUsdcToken.getBalance(alice));
      
      const response = txOk(dlmmSwapRouter.swapMulti(
        swaps,
        maxUnfavorableBins
      ), alice);
      
      const finalXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const finalYBalance = rovOk(mockUsdcToken.getBalance(alice));
      const result = cvToValue(response.result);
      const received = result.results.reduce((sum: bigint, r: {in: bigint, out: bigint}) => sum + r.out, 0n);
      
      expect(finalXBalance).toBe(initialXBalance - 900000n); // Total amount swapped (3 * 300000n)
      expect(finalYBalance).toBe(initialYBalance + received);
      expect(received).toBeGreaterThan(0n);
    });

    it('should successfully execute 2 swaps in same pool in the same bin', async () => {
      const swaps = [
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          expectedBinId: 0,
          amount: 400000n, // 0.004 BTC
          minReceived: 1n,
          xForY: true
        },
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          expectedBinId: 0,
          amount: 600000n, // 0.006 BTC
          minReceived: 1n,
          xForY: true
        }
      ];
      const maxUnfavorableBins = 5n;
      
      const initialXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const initialYBalance = rovOk(mockUsdcToken.getBalance(alice));
      
      const response = txOk(dlmmSwapRouter.swapMulti(
        swaps,
        maxUnfavorableBins
      ), alice);
      
      const finalXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const finalYBalance = rovOk(mockUsdcToken.getBalance(alice));
      const result = cvToValue(response.result);
      const received = result.results.reduce((sum: bigint, r: {in: bigint, out: bigint}) => sum + r.out, 0n);
      
      expect(finalXBalance).toBe(initialXBalance - 1000000n); // Total amount swapped (400000n + 600000n)
      expect(finalYBalance).toBe(initialYBalance + received);
      expect(received).toBeGreaterThan(0n);
    });

    it('should execute Y for X swaps successfully', async () => {
      const swaps = [{
        poolTrait: sbtcUsdcPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockUsdcToken.identifier,
        expectedBinId: 0,
        amount: 50000000n, // 50 USDC
        minReceived: 1n,
        xForY: false
      }];
      const maxUnfavorableBins = 5n;
      
      const initialXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const initialYBalance = rovOk(mockUsdcToken.getBalance(alice));
      
      const response = txOk(dlmmSwapRouter.swapMulti(
        swaps,
        maxUnfavorableBins
      ), alice);
      
      const finalXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const finalYBalance = rovOk(mockUsdcToken.getBalance(alice));
      const result = cvToValue(response.result);
      const received = result.results.reduce((sum: bigint, r: {in: bigint, out: bigint}) => sum + r.out, 0n);
      
      expect(finalXBalance).toBe(initialXBalance + received);
      expect(finalYBalance).toBeLessThan(initialYBalance);
      expect(received).toBeGreaterThan(0n);
    });

    it('should fail when minimum received not met', async () => {
      const swaps = [{
        poolTrait: sbtcUsdcPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockUsdcToken.identifier,
        expectedBinId: 0,
        amount: 1000000n,
        minReceived: 999999999999n, // Unreasonably high minimum
        xForY: true
      }];
      const maxUnfavorableBins = 5n;
      
      const response = txErr(dlmmSwapRouter.swapMulti(
        swaps,
        maxUnfavorableBins
      ), alice);
      
      expect(cvToValue(response.result)).toBe(errors.dlmmSwapRouter.ERR_MINIMUM_RECEIVED);
    });

    it('should fail when unfavorable bins exceed maximum', async () => {
      // For X for Y, bins with ID > active bin are unfavorable
      const activeBinId = rovOk(sbtcUsdcPool.getActiveBinId());
      const swaps = [{
        poolTrait: sbtcUsdcPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockUsdcToken.identifier,
        expectedBinId: Number(activeBinId) + 10, // 10 bins higher = very unfavorable for X for Y
        amount: 1000000n,
        minReceived: 1n,
        xForY: true
      }];
      const maxUnfavorableBins = 5n; // Lower than the unfavorable bin count (10)
      
      const response = txErr(dlmmSwapRouter.swapMulti(
        swaps,
        maxUnfavorableBins
      ), alice);
      
      expect(cvToValue(response.result)).toBe(errors.dlmmSwapRouter.ERR_BIN_SLIPPAGE);
    });

    it('should revert on empty swap list', async () => {
      // test will fail
      const swaps: any[] = [];
      const maxUnfavorableBins = 5n;
      
      const response = txErr(dlmmSwapRouter.swapMulti(
        swaps,
        maxUnfavorableBins
      ), alice);

      // will be changed with specific error code once set
      expect(cvToValue(response.result)).toBeGreaterThan(0n);
    });

    it('should handle swaps with zero amounts', async () => {
      const swaps = [{
        poolTrait: sbtcUsdcPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockUsdcToken.identifier,
        expectedBinId: 0,
        amount: 0n,
        minReceived: 0n,
        xForY: true
      }];
      const maxUnfavorableBins = 5n;
      
      // This should fail at the core swap level with invalid amount
      const response = txErr(dlmmSwapRouter.swapMulti(
        swaps,
        maxUnfavorableBins
      ), alice);
      
      // The error should propagate from the dlmm-core swap function
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_INVALID_AMOUNT);
    });

    it('should calculate unfavorable bins correctly for X for Y swaps', async () => {
      // For X for Y swaps, bins with ID greater than active bin are unfavorable
      // bin-id-delta = active-bin-id - expected-bin-id, unfavorable when bin-id-delta < 0
      // This means expected-bin-id > active-bin-id is unfavorable
      const activeBinId = rovOk(sbtcUsdcPool.getActiveBinId());
      const swaps = [{
        poolTrait: sbtcUsdcPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockUsdcToken.identifier,
        expectedBinId: Number(activeBinId) + 3, // 3 bins higher than active = unfavorable
        amount: 1000000n,
        minReceived: 1n,
        xForY: true
      }];
      const maxUnfavorableBins = 2n; // Should fail as unfavorable count is 3
      
      const response = txErr(dlmmSwapRouter.swapMulti(
        swaps,
        maxUnfavorableBins
      ), alice);
      
      expect(cvToValue(response.result)).toBe(errors.dlmmSwapRouter.ERR_BIN_SLIPPAGE);
    });

    it('should calculate unfavorable bins correctly for Y for X swaps', async () => {
      // For Y for X swaps, bins with ID less than active bin are unfavorable  
      // bin-id-delta = active-bin-id - expected-bin-id, unfavorable when bin-id-delta > 0
      // This means expected-bin-id < active-bin-id is unfavorable
      const activeBinId = rovOk(sbtcUsdcPool.getActiveBinId());
      const swaps = [{
        poolTrait: sbtcUsdcPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockUsdcToken.identifier,
        expectedBinId: Number(activeBinId) - 3, // 3 bins lower than active = unfavorable
        amount: 50000000n,
        minReceived: 1n,
        xForY: false
      }];
      const maxUnfavorableBins = 2n; // Should fail as unfavorable count is 3
      
      const response = txErr(dlmmSwapRouter.swapMulti(
        swaps,
        maxUnfavorableBins
      ), alice);
      
      expect(cvToValue(response.result)).toBe(errors.dlmmSwapRouter.ERR_BIN_SLIPPAGE);
    });

    it('should handle mixed favorable and unfavorable swaps', async () => {
      const activeBinId = rovOk(sbtcUsdcPool.getActiveBinId());
      const swaps = [
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          expectedBinId: Number(activeBinId), // Favorable (active bin)
          amount: 500000n,
          minReceived: 1n,
          xForY: true
        },
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          expectedBinId: Number(activeBinId) + 2, // Unfavorable (2 bins above active for X for Y)
          amount: 500000n,
          minReceived: 1n,
          xForY: true
        }
      ];
      const maxUnfavorableBins = 3n; // Should pass as total unfavorable is 2
      
      const response = txOk(dlmmSwapRouter.swapMulti(
        swaps,
        maxUnfavorableBins
      ), alice);
      
      const result = cvToValue(response.result);
      const received = result.results.reduce((sum: bigint, r: {in: bigint, out: bigint}) => sum + r.out, 0n);
      expect(received).toBeGreaterThan(0n);
    });

    it('should document ERR_NO_ACTIVE_BIN_DATA error condition', async () => {
      // ERR_NO_ACTIVE_BIN_DATA occurs when pool-trait.get-active-bin-id() fails
      // This is difficult to trigger with valid contracts as get-active-bin-id is a simple read
      // In practice, this error would occur if:
      // 1. The pool contract is not properly initialized
      // 2. The pool contract has internal state corruption
      // 3. The pool contract explicitly returns an error from get-active-bin-id
      
      // without this the pool does not revert on get-active-bin-id
      txOk(mockPool.setRevert(true), deployer);

      const swaps = [{
        poolTrait: mockPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockUsdcToken.identifier,
        expectedBinId: 0,
        amount: 1000000n,
        minReceived: 1n,
        xForY: true
      }];
      const maxUnfavorableBins = 5n;
      
      const response = txErr(dlmmSwapRouter.swapMulti(
        swaps,
        maxUnfavorableBins
      ), alice);

      expect(cvToValue(response.result)).toBe(errors.dlmmSwapRouter.ERR_NO_ACTIVE_BIN_DATA);
    });

    it('should handle edge case with extremely large unfavorable bin count', async () => {
      // For X for Y, bins with ID > active bin are unfavorable
      const activeBinId = rovOk(sbtcUsdcPool.getActiveBinId());
      const swaps = [{
        poolTrait: sbtcUsdcPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockUsdcToken.identifier,
        expectedBinId: Number(activeBinId) + 500, // Very far above active bin = very unfavorable
        amount: 1000000n,
        minReceived: 1n,
        xForY: true
      }];
      const maxUnfavorableBins = 1n; // Very low threshold
      
      const response = txErr(dlmmSwapRouter.swapMulti(
        swaps,
        maxUnfavorableBins
      ), alice);
      
      expect(cvToValue(response.result)).toBe(errors.dlmmSwapRouter.ERR_BIN_SLIPPAGE);
    });

    it('should handle maximum number of swaps in a single call', async () => {
      // Test with multiple swaps to stress test the fold function
      const swaps = Array.from({ length: 10 }, (_, i) => ({
        poolTrait: sbtcUsdcPool.identifier,
        xTokenTrait: mockSbtcToken.identifier,
        yTokenTrait: mockUsdcToken.identifier,
        expectedBinId: i - 5, // Range from -5 to 4
        amount: 100000n, // 0.001 BTC each
        minReceived: 1n,
        xForY: true
      }));
      const maxUnfavorableBins = 50n; // High threshold to allow all swaps
      
      const initialXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const initialYBalance = rovOk(mockUsdcToken.getBalance(alice));
      
      const response = txOk(dlmmSwapRouter.swapMulti(
        swaps,
        maxUnfavorableBins
      ), alice);
      
      const finalXBalance = rovOk(mockSbtcToken.getBalance(alice));
      const finalYBalance = rovOk(mockUsdcToken.getBalance(alice));
      const result = cvToValue(response.result);
      const received = result.results.reduce((sum: bigint, r: {in: bigint, out: bigint}) => sum + r.out, 0n);
      
      expect(finalXBalance).toBe(initialXBalance - 1000000n); // Total: 10 * 100000n
      expect(finalYBalance).toBe(initialYBalance + received);
      expect(received).toBeGreaterThan(0n);
    });

    it('should handle mixed X-for-Y and Y-for-X swaps', async () => {
      const swaps = [
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          expectedBinId: 0,
          amount: 500000n, // 0.005 BTC
          minReceived: 0n,
          xForY: true
        },
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockUsdcToken.identifier,
          expectedBinId: 0,
          amount: 25000000n, // 25 USDC
          minReceived: 0n,
          xForY: false
        }
      ];
      const maxUnfavorableBins = 5n;
      
      const response = txOk(dlmmSwapRouter.swapMulti(
        swaps,
        maxUnfavorableBins
      ), alice);
      
      const result = cvToValue(response.result);
      const received = result.results.reduce((sum: bigint, r: {in: bigint, out: bigint}) => sum + r.out, 0n);
      expect(received).toBeGreaterThanOrEqual(0n);
    });

    it('should fail when using random token in swap helper', async () => {
      // Mint random tokens for testing
      txOk(mockRandomToken.mint(1000000n, alice), deployer);

      const swaps = [
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockRandomToken.identifier, // Using random token
          yTokenTrait: mockUsdcToken.identifier,
          expectedBinId: 0,
          amount: 500000n,
          minReceived: 0n,
          xForY: true
        }
      ];
      const maxUnfavorableBins = 5n;
      
      const response = txErr(dlmmSwapRouter.swapMulti(
        swaps,
        maxUnfavorableBins
      ), alice);
      
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_INVALID_X_TOKEN);
    });

    it('should fail when using random Y token in swap helper', async () => {
      // Mint random tokens for testing
      txOk(mockRandomToken.mint(1000000n, alice), deployer);

      const swaps = [
        {
          poolTrait: sbtcUsdcPool.identifier,
          xTokenTrait: mockSbtcToken.identifier,
          yTokenTrait: mockRandomToken.identifier, // Using random token
          expectedBinId: 0,
          amount: 500000n,
          minReceived: 0n,
          xForY: true
        }
      ];
      const maxUnfavorableBins = 5n;
      
      const response = txErr(dlmmSwapRouter.swapMulti(
        swaps,
        maxUnfavorableBins
      ), alice);
      
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_INVALID_Y_TOKEN);
    });
  });
});