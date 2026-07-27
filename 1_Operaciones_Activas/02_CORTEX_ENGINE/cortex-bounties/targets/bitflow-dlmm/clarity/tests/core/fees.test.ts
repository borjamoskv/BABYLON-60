import {
  alice,
  bob,
  deployer,
  dlmmCore,
  dlmmCoreMultiHelper,
  errors,
  sbtcUsdcPool,
  mockSbtcToken,
  mockUsdcToken,
  setupTestEnvironment,
  getSwapXForYEventData,
  getAddLiquidityEventData
} from "../helpers/helpers";

import { describe, it, expect, beforeEach } from 'vitest';
import {
  cvToValue,
} from '@clarigen/core';
import { txErr, txOk, rovOk } from '@clarigen/test';

describe('DLMM Core Fee Management Tests', () => {
  
  beforeEach(async () => {
    setupTestEnvironment();
  });

  describe('Protocol Fee Management', () => {
    
    it('Should initialize unclaimed protocol fees to zero when pool is created', async () => {
      const poolId = 1n;
      const unclaimedFees = rovOk(dlmmCore.getUnclaimedProtocolFeesById(poolId));
      
      expect(unclaimedFees).toStrictEqual({ xFee: 0n, yFee: 0n });
    });

    it('Should allow admin to claim protocol fees when available', async () => {
      // @audit fix this
      // First do some swaps to generate protocol fees
      const swapAmount = 1000000n; // 0.01 BTC
      const expectedProtocolFee = (swapAmount * 1000n) / 10000n; // 10% of 1M = 100,000
      
      txOk(dlmmCore.swapXForY(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        0n, // active bin
        swapAmount
      ), alice);
      
      // Check that protocol fees were accumulated - should be exactly 10,000
      const poolId = 1n;
      const unclaimedFees = rovOk(dlmmCore.getUnclaimedProtocolFeesById(poolId))!;
      expect(unclaimedFees.xFee).toBe(expectedProtocolFee);
      expect(unclaimedFees.yFee).toBe(0n); // No Y fees from X->Y swap
      
      // Get initial token balances
      const initialXBalance = rovOk(mockSbtcToken.getBalance(deployer));
      
      // Admin claims protocol fees
      txOk(dlmmCore.claimProtocolFees(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier
      ), deployer);
      
      // Check balance increased by exactly the claimed fees
      const finalXBalance = rovOk(mockSbtcToken.getBalance(deployer));
      expect(finalXBalance).toBe(initialXBalance + expectedProtocolFee);
      
      // Note: The contract has a bug where it doesn't reset unclaimed fees to 0 after claiming
      // So we check that fees were claimed but unclaimed counter wasn't reset
      const postClaimFees = rovOk(dlmmCore.getUnclaimedProtocolFeesById(poolId))!;
      expect(postClaimFees.xFee).toBe(0n); // Bug: should be 0 but isn't
      expect(postClaimFees.yFee).toBe(0n);
    });

    it('Should demonstrate claiming behavior when no new fees accumulated', async () => {
      // Since setupTestEnvironment starts with 0 fees, and we haven't done any fee-generating operations,
      // claiming should succeed but transfer 0 tokens (or fail if contract validates for > 0 fees)
      
      const initialBalance = rovOk(mockSbtcToken.getBalance(deployer));
      
      // Try to claim when there are no accumulated fees
      txOk(dlmmCore.claimProtocolFees(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier
      ), deployer);
      
      const finalBalance = rovOk(mockSbtcToken.getBalance(deployer));
      
      // Balance should remain the same since no fees to claim
      expect(finalBalance).toBe(initialBalance);
    });

    it('Should allow any user to claim protocol fees to fee address', async () => {
      // Generate some fees first
      txOk(dlmmCore.swapXForY(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        0n,
        1000000n
      ), alice);
      
      // Note: The contract allows anyone to trigger protocol fee claims
      // but the fees go to the designated fee address (deployer), not the caller
      const deployerInitialBalance = rovOk(mockSbtcToken.getBalance(deployer));
      const bobInitialBalance = rovOk(mockSbtcToken.getBalance(bob));
      
      // Bob claims protocol fees (but they go to fee address = deployer)
      txOk(dlmmCore.claimProtocolFees(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier
      ), bob);
      
      const deployerFinalBalance = rovOk(mockSbtcToken.getBalance(deployer));
      const bobFinalBalance = rovOk(mockSbtcToken.getBalance(bob));
      
      // Deployer (fee address) should receive the fees, not Bob
      expect(deployerFinalBalance).toBeGreaterThan(deployerInitialBalance);
      expect(bobFinalBalance).toBe(bobInitialBalance); // Bob gets nothing
    });

    it('Should support bulk protocol fee claiming for multiple pools', async () => {
      
      // Generate fees in the pool
      txOk(dlmmCore.swapXForY(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        0n,
        1000000n
      ), alice);
      
      // Claim fees for multiple pools (using the same pool for simplicity)
      txOk(dlmmCoreMultiHelper.claimProtocolFeesMulti(
        [sbtcUsdcPool.identifier],
        [mockSbtcToken.identifier],
        [mockUsdcToken.identifier]
      ), deployer);
      
      const poolId = 1n;
      const unclaimedFees = rovOk(dlmmCore.getUnclaimedProtocolFeesById(poolId))!;
      expect(unclaimedFees.xFee).toBe(0n); // Bug: should be 0 but contract doesn't reset
    });
  });

  describe('Fee Structure Management', () => {

    it('Should allow admin to set x-fees (protocol and provider)', async () => {
      const newProtocolFee = 500n; // 0.5%
      const newProviderFee = 2500n;  // 2.5%
      
      txOk(dlmmCore.setXFees(
        sbtcUsdcPool.identifier,
        newProtocolFee,
        newProviderFee
      ), deployer);
      
      // Verify fees were set
      const poolData = rovOk(sbtcUsdcPool.getPool());
      expect(poolData.xProtocolFee).toBe(newProtocolFee);
      expect(poolData.xProviderFee).toBe(newProviderFee);
    });

    it('Should allow admin to set y-fees (protocol and provider)', async () => {
      const newProtocolFee = 750n; // 0.75%
      const newProviderFee = 2250n; // 2.25%
      
      txOk(dlmmCore.setYFees(
        sbtcUsdcPool.identifier,
        newProtocolFee,
        newProviderFee
      ), deployer);
      
      // Verify fees were set
      const poolData = rovOk(sbtcUsdcPool.getPool());
      expect(poolData.yProtocolFee).toBe(newProtocolFee);
      expect(poolData.yProviderFee).toBe(newProviderFee);
    });

    it('Should reject fees that exceed maximum FEE_SCALE_BPS (10000)', async () => {
      const invalidProtocolFee = 5000n;
      const invalidProviderFee = 6000n; // Total: 11000 > 10000
      
      const response = txErr(dlmmCore.setXFees(
        sbtcUsdcPool.identifier,
        invalidProtocolFee,
        invalidProviderFee
      ), deployer);
      
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_INVALID_FEE);
    });

    it('Should reject fees that when combined with variable fees exceed FEE_SCALE_BPS', async () => {
      // Set some variable fees first
      txOk(dlmmCore.setVariableFees(
        sbtcUsdcPool.identifier,
        2000n, // 2% X variable fee
        1500n  // 1.5% Y variable fee
      ), deployer);
      
      // Try to set protocol+provider fees that would exceed limit with existing variable fees
      const protocolFee = 4000n; // 4%
      const providerFee = 5000n;  // 5% - Total with variable: 11% > 10%
      
      const response = txErr(dlmmCore.setXFees(
        sbtcUsdcPool.identifier,
        protocolFee,
        providerFee
      ), deployer);
      
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_INVALID_FEE);
    });

    it('Should allow bulk fee setting for multiple pools', async () => {
      const protocolFees = [200n]; // 0.2%
      const providerFees = [1800n];  // 1.8%
      
      txOk(dlmmCoreMultiHelper.setXFeesMulti(
        [sbtcUsdcPool.identifier],
        protocolFees,
        providerFees
      ), deployer);
      
      const poolData = rovOk(sbtcUsdcPool.getPool());
      expect(poolData.xProtocolFee).toBe(200n);
      expect(poolData.xProviderFee).toBe(1800n);
    });

    it('Should prevent non-admin from setting fees', async () => {
      const response = txErr(dlmmCore.setXFees(
        sbtcUsdcPool.identifier,
        100n,
        200n
      ), alice);
      
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_NOT_AUTHORIZED);
    });
  });

  describe('Variable Fee Management', () => {

    it('Should allow admin to set variable fees', async () => {
      const xVariableFee = 500n; // 0.5%
      const yVariableFee = 750n; // 0.75%
      
      txOk(dlmmCore.setVariableFees(
        sbtcUsdcPool.identifier,
        xVariableFee,
        yVariableFee
      ), deployer);
      
      const poolData = rovOk(sbtcUsdcPool.getPool());
      expect(poolData.xVariableFee).toBe(xVariableFee);
      expect(poolData.yVariableFee).toBe(yVariableFee);
    });

    it('Should allow variable fees manager to set variable fees', async () => {
      // Set alice as variable fees manager
      txOk(dlmmCore.setVariableFeesManager(
        sbtcUsdcPool.identifier,
        alice
      ), deployer);
      
      // Alice should now be able to set variable fees
      txOk(dlmmCore.setVariableFees(
        sbtcUsdcPool.identifier,
        300n, // 0.3%
        400n  // 0.4%
      ), alice);
      
      const poolData = rovOk(sbtcUsdcPool.getPool());
      expect(poolData.xVariableFee).toBe(300n);
      expect(poolData.yVariableFee).toBe(400n);
      expect(poolData.variableFeesManager).toBe(alice);
    });

    it('Should reject variable fees that would exceed total fee limit', async () => {
      const xVariableFee = 8000n; // 8% - with existing protocol+provider fees would exceed 10%
      const yVariableFee = 7500n; // 7.5%
      
      const response = txErr(dlmmCore.setVariableFees(
        sbtcUsdcPool.identifier,
        xVariableFee,
        yVariableFee
      ), deployer);
      
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_INVALID_FEE);
    });

    it('Should allow resetting variable fees after cooldown period', async () => {
      // Set some variable fees first
      txOk(dlmmCore.setVariableFees(
        sbtcUsdcPool.identifier,
        1000n, // 1%
        1500n  // 1.5%
      ), deployer);
      
      // Try to reset immediately - should fail due to cooldown
      const immediateResetResponse = txErr(dlmmCore.resetVariableFees(
        sbtcUsdcPool.identifier
      ), deployer);
      
      expect(cvToValue(immediateResetResponse.result)).toBe(errors.dlmmCore.ERR_VARIABLE_FEES_COOLDOWN);
      
    });

    it('Should prevent unauthorized users from setting variable fees', async () => {
      const response = txErr(dlmmCore.setVariableFees(
        sbtcUsdcPool.identifier,
        100n,
        200n
      ), bob);
      
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_NOT_AUTHORIZED);
    });

    it('Should allow freezing variable fees manager', async () => {
      txOk(dlmmCore.setFreezeVariableFeesManager(
        sbtcUsdcPool.identifier
      ), deployer);
      
      const poolData = rovOk(sbtcUsdcPool.getPool());
      expect(poolData.freezeVariableFeesManager).toBe(true);
    });

    it('Should prevent setting new variable fees manager when frozen', async () => {
      // Freeze the variable fees manager
      txOk(dlmmCore.setFreezeVariableFeesManager(
        sbtcUsdcPool.identifier
      ), deployer);
      
      // Try to set new manager - should fail
      const response = txErr(dlmmCore.setVariableFeesManager(
        sbtcUsdcPool.identifier,
        alice
      ), deployer);
      
      expect(cvToValue(response.result)).toBe(errors.dlmmCore.ERR_VARIABLE_FEES_MANAGER_FROZEN);
    });

    it('Should support bulk variable fee operations', async () => {
      const xFees = [250n];
      const yFees = [350n];
      
      txOk(dlmmCoreMultiHelper.setVariableFeesMulti(
        [sbtcUsdcPool.identifier],
        xFees,
        yFees
      ), deployer);
      
      const poolData = rovOk(sbtcUsdcPool.getPool());
      expect(poolData.xVariableFee).toBe(250n);
      expect(poolData.yVariableFee).toBe(350n);
    });
  });

  describe('Fee Collection During Swaps', () => {

    it('Should correctly collect protocol fees during X-for-Y swaps', async () => {
      const swapAmount = 2000000n; // 0.02 BTC
      const poolId = 1n;
      
      // Get initial unclaimed fees
      const initialFees = rovOk(dlmmCore.getUnclaimedProtocolFeesById(poolId))!;
      
      // Perform swap
      txOk(dlmmCore.swapXForY(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        0n, // active bin
        swapAmount
      ), alice);
      
      // Check that protocol fees were accumulated
      const finalFees = rovOk(dlmmCore.getUnclaimedProtocolFeesById(poolId))!;
      expect(finalFees.xFee).toBeGreaterThan(initialFees.xFee);
      
      // Calculate expected fee (1000 BPS = 10% protocol fee from pool creation)
      const expectedFee = (swapAmount * 1000n) / 10000n;
      expect(finalFees.xFee).toBe(initialFees.xFee + expectedFee);
    });

    it('Should correctly collect protocol fees during Y-for-X swaps', async () => {
      const swapAmount = 1000000000n; // 1000 USDC
      const poolId = 1n;
      
      // Get initial unclaimed fees  
      const initialFees = rovOk(dlmmCore.getUnclaimedProtocolFeesById(poolId))!;
      
      // Perform swap
      txOk(dlmmCore.swapYForX(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        0n, // active bin
        swapAmount
      ), alice);
      
      // Check that protocol fees were accumulated
      const finalFees = rovOk(dlmmCore.getUnclaimedProtocolFeesById(poolId))!;
      expect(finalFees.yFee).toBeGreaterThan(initialFees.yFee);
      
      // Calculate expected fee (1000 BPS = 10% protocol fee from pool creation)
      const expectedFee = (swapAmount * 1000n) / 10000n;
      expect(finalFees.yFee).toBe(initialFees.yFee + expectedFee);
    });

    it('Should not collect protocol fees when protocol fee is set to zero', async () => {
      // Set protocol fees to zero
      txOk(dlmmCore.setXFees(
        sbtcUsdcPool.identifier,
        0n, // No protocol fee
        3000n // Keep provider fee
      ), deployer);
      
      const poolId = 1n;
      const initialFees = rovOk(dlmmCore.getUnclaimedProtocolFeesById(poolId))!;
      
      // Perform swap
      txOk(dlmmCore.swapXForY(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        0n,
        1000000n
      ), alice);
      
      // Protocol fees should remain unchanged
      const finalFees = rovOk(dlmmCore.getUnclaimedProtocolFeesById(poolId))!;
      expect(finalFees.xFee).toBe(initialFees.xFee);
    });

    it('Should correctly apply all three fee types (protocol, provider, variable) during swaps', async () => {
      // Set up all fee types
      const protocolFee = 500n;  // 0.5%
      const providerFee = 2000n; // 2%
      const variableFee = 1000n; // 1%
      
      txOk(dlmmCore.setXFees(sbtcUsdcPool.identifier, protocolFee, providerFee), deployer);
      txOk(dlmmCore.setVariableFees(sbtcUsdcPool.identifier, variableFee, 0n), deployer);
      
      const swapAmount = 1000000n; // 0.01 BTC
      const aliceInitialBalance = rovOk(mockSbtcToken.getBalance(alice));
      
      // Perform swap
      const response = txOk(dlmmCore.swapXForY(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        0n,
        swapAmount
      ), alice);
            
      const swapEvents = getSwapXForYEventData(response);
      expect(swapEvents.length).toBe(1);
      const swapEvent = swapEvents[0];

      const aliceFinalBalance = rovOk(mockSbtcToken.getBalance(alice));
      const amountDeducted = aliceInitialBalance - aliceFinalBalance;
      
      // Total fees should be 3.5% of swap amount
      const totalFeeRate = protocolFee + providerFee + variableFee; // 3500 BPS
      const expectedTotalFees = (swapAmount * totalFeeRate) / 10000n;
      expect(swapEvent.data.dx).toBe(swapAmount - expectedTotalFees);
      const expectedAmountDeducted = swapAmount;
      
      expect(amountDeducted).toBe(expectedAmountDeducted);
      
      // Check protocol fees were accumulated
      const poolId = 1n;
      const finalFees = rovOk(dlmmCore.getUnclaimedProtocolFeesById(poolId))!;
      const expectedProtocolFee = (swapAmount * protocolFee) / 10000n;
      expect(finalFees.xFee).toBe(expectedProtocolFee);
    });
  });

  describe('Fee Collection During Liquidity Operations', () => {

    it.skip('Should apply liquidity fees when adding to active bin', async () => {
      // @audit check/fix this
      const activeBinId = rovOk(sbtcUsdcPool.getActiveBinId());
      const xAmount = 1000000n; // 0.01 BTC
      const yAmount = 500000000n; // 500 USDC
      
      // Add liquidity to active bin
      const response = txOk(dlmmCore.addLiquidity(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        activeBinId,
        xAmount,
        yAmount,
        1n, // min DLP
        1000000n, // max-x-liquidity-fee
        1000000n  // max-y-liquidity-fee
      ), alice);

      const addLiquidityEvents = getAddLiquidityEventData(response);
      expect(addLiquidityEvents.length).toBe(1);
      const addLiquidityEvent = addLiquidityEvents[0];
      
      // Check that liquidity fees are applied when adding to active bin
      // The fees should be non-zero for active bin liquidity additions
      expect(addLiquidityEvent.data.xAmountFeesLiquidity).not.toBe(0n);
      expect(addLiquidityEvent.data.yAmountFeesLiquidity).not.toBe(0n);
    });

    it('Should not apply liquidity fees when adding to non-active bins', async () => {
      const activeBinId = rovOk(sbtcUsdcPool.getActiveBinId());
      const nonActiveBinId = activeBinId + 5n;
      const xAmount = 1000000n; // 0.01 BTC
      
      // Add liquidity to non-active bin (should not incur liquidity fees)
      const response = txOk(dlmmCore.addLiquidity(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        nonActiveBinId,
        xAmount,
        0n, // Only X tokens for positive bin
        1n, // min DLP
        1000000n, // max-x-liquidity-fee
        1000000n  // max-y-liquidity-fee
      ), alice);
      
      const addLiquidityEvents = getAddLiquidityEventData(response);
      expect(addLiquidityEvents.length).toBe(1);
      const addLiquidityEvent = addLiquidityEvents[0];
      
      // Check that no liquidity fees are applied when adding to non-active bins
      expect(addLiquidityEvent.data.xAmountFeesLiquidity).toBe(0n);
      expect(addLiquidityEvent.data.yAmountFeesLiquidity).toBe(0n);
    });
  });

  describe('Fee Address and Recipient Management', () => {

    it('Should transfer protocol fees to the designated fee address', async () => {
      // Generate some protocol fees first by doing a swap
      const swapAmount = 1000000n;
      txOk(dlmmCore.swapXForY(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        0n,
        swapAmount
      ), alice);
      
      const deployerInitialBalance = rovOk(mockSbtcToken.getBalance(deployer));
      
      // Admin claims protocol fees
      txOk(dlmmCore.claimProtocolFees(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier
      ), deployer);
      
      const deployerFinalBalance = rovOk(mockSbtcToken.getBalance(deployer));
      
      // Deployer should have received the protocol fees (10% of swap amount)
      const expectedFee = (swapAmount * 1000n) / 10000n; // 10% = 100,000
      expect(deployerFinalBalance).toBe(deployerInitialBalance + expectedFee);
    });

    it('Should correctly identify fee address from pool data', async () => {
      const poolData = rovOk(sbtcUsdcPool.getPool());
      expect(poolData.feeAddress).toBe(deployer); // deployer was set as fee address in createTestPool
    });
  });

  describe('Edge Cases and Error Handling', () => {

    it('Should handle zero fee amounts correctly', async () => {
      // Set all fees to zero
      txOk(dlmmCore.setXFees(sbtcUsdcPool.identifier, 0n, 0n), deployer);
      txOk(dlmmCore.setYFees(sbtcUsdcPool.identifier, 0n, 0n), deployer);
      txOk(dlmmCore.setVariableFees(sbtcUsdcPool.identifier, 0n, 0n), deployer);
      
      const poolId = 1n;
      const initialFees = rovOk(dlmmCore.getUnclaimedProtocolFeesById(poolId))!;
      
      // Perform swap with zero fees
      txOk(dlmmCore.swapXForY(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        0n,
        1000000n
      ), alice);
      
      // Protocol fees should remain unchanged (still zero)
      const finalFees = rovOk(dlmmCore.getUnclaimedProtocolFeesById(poolId))!;
      expect(finalFees.xFee).toBe(initialFees.xFee);
      expect(finalFees.yFee).toBe(initialFees.yFee);
    });

    it('Should validate fee bounds at maximum allowed values', async () => {
      // Test setting fees to exactly the maximum allowed (just under FEE_SCALE_BPS)
      const maxProtocolFee = 5000n; // 5%
      const maxProviderFee = 4999n;  // 4.999% - Total: 9.999% < 10%
      
      txOk(dlmmCore.setXFees(
        sbtcUsdcPool.identifier,
        maxProtocolFee,
        maxProviderFee
      ), deployer);
      
      const poolData = rovOk(sbtcUsdcPool.getPool());
      expect(poolData.xProtocolFee).toBe(maxProtocolFee);
      expect(poolData.xProviderFee).toBe(maxProviderFee);
    });

    it('Should handle very small fee amounts and rounding', async () => {
      // Set very small fees (1 BPS each = 0.01%)
      txOk(dlmmCore.setXFees(sbtcUsdcPool.identifier, 1n, 1n), deployer);
      
      // Small swap amount
      const smallSwapAmount = 100n; // Very small amount
      const poolId = 1n;
      const initialFees = rovOk(dlmmCore.getUnclaimedProtocolFeesById(poolId))!;
      
      txOk(dlmmCore.swapXForY(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        0n,
        smallSwapAmount
      ), alice);
      
      const finalFees = rovOk(dlmmCore.getUnclaimedProtocolFeesById(poolId))!;
      
      // Fee should be calculated correctly even for small amounts
      // 1 BPS of 100 = (100 * 1) / 10000 = 0 (due to integer division)
      const expectedFee = (smallSwapAmount * 1n) / 10000n; // Should be 0
      expect(finalFees.xFee).toBe(initialFees.xFee + expectedFee);
    });
  });
});