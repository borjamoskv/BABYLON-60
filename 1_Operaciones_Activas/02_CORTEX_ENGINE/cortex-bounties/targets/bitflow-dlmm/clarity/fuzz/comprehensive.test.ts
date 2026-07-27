import {
  alice,
  bob,
  charlie,
  deployer,
  dlmmCore,
  sbtcUsdcPool,
  mockSbtcToken,
  mockUsdcToken,
  setupTestEnvironment,
  getSbtcUsdcPoolLpBalance,
} from "../tests/helpers/helpers";

import { describe, it, expect, beforeEach } from 'vitest';
import { cvToValue } from '@clarigen/core';
import { txOk, rovOk } from '@clarigen/test';
import { getFuzzConfig } from './harnesses/config';
import {
  checkSwapXForYInvariants,
  checkSwapYForXInvariants,
  checkAddLiquidityInvariants as checkAddLiquidityInvariantsCore,
  checkWithdrawLiquidityInvariants as checkWithdrawLiquidityInvariantsCore,
  checkMoveLiquidityInvariants as checkMoveLiquidityInvariantsCore,
  BinState,
  UserState,
} from "./properties/invariants";
import { LogManager, SeededRandom, MIN_BIN_ID, MAX_BIN_ID, OperationType } from './utils';

interface PoolState {
  activeBinId: bigint;
  binBalances: Map<bigint, { xBalance: bigint; yBalance: bigint; totalSupply: bigint }>;
  userBalances: Map<string, { xToken: bigint; yToken: bigint; lpTokens: Map<bigint, bigint> }>;
  protocolFees: { xFee: bigint; yFee: bigint };
}

interface TransactionLog {
  txNumber: number;
  functionName: string;
  caller: string;
  params: any;
  result: 'success' | 'failure';
  error?: string;
  invariantChecks?: string[];
}

class TestConfig {
  // Bin range for sampling
  static readonly MIN_BIN_SAMPLE = -10;
  static readonly MAX_BIN_SAMPLE = 10;
  
  // Liquidity parameters
  static readonly MAX_LIQUIDITY_FEE = 1000000n;
  static readonly MIN_DLP = 1n;
  
  // Amount generation
  static readonly MIN_SWAP_AMOUNT = 100n;
  static readonly MIN_LIQUIDITY_AMOUNT = 1000n;
  
  // Random Generation Probabilities
  static readonly PROB_SWAP_VERY_SMALL = 0.2; // <0.1%
  static readonly PROB_SWAP_SMALL = 0.3;      // 0.1-1%
  static readonly PROB_SWAP_MEDIUM = 0.3;     // 1-10%
  static readonly PROB_SWAP_LARGE = 0.2;      // 10-30%
  
  // Error Handling
  static readonly MAX_CONSECUTIVE_FAILURES = 100;
  
  // Progress Reporting
  static readonly PROGRESS_BAR_WIDTH = 40;
  static readonly PROGRESS_UPDATE_INTERVAL = 10;
}

class PoolStateManager {
  static async captureState(): Promise<PoolState> {
    const activeBinId = rovOk(sbtcUsdcPool.getActiveBinId());
    const binBalances = new Map<bigint, { xBalance: bigint; yBalance: bigint; totalSupply: bigint }>();
    const userBalances = new Map<string, { xToken: bigint; yToken: bigint; lpTokens: Map<bigint, bigint> }>();
    const users = [deployer, alice, bob, charlie];

    // Get protocol fees
    const poolId = 1n;
    const fees = rovOk(dlmmCore.getUnclaimedProtocolFeesById(poolId));
    const protocolFees = fees ? { xFee: fees.xFee, yFee: fees.yFee } : { xFee: 0n, yFee: 0n };

    // Sample bins around active bin
    for (let offset = TestConfig.MIN_BIN_SAMPLE; offset <= TestConfig.MAX_BIN_SAMPLE; offset++) {
      const binId = activeBinId + BigInt(offset);
      if (binId >= MIN_BIN_ID && binId <= MAX_BIN_ID) {
        const unsignedBin = rovOk(dlmmCore.getUnsignedBinId(binId));
        try {
          const balances = rovOk(sbtcUsdcPool.getBinBalances(unsignedBin));
          const totalSupply = rovOk(sbtcUsdcPool.getTotalSupply(unsignedBin));
          binBalances.set(binId, {
            xBalance: balances.xBalance,
            yBalance: balances.yBalance,
            totalSupply: totalSupply,
          });
        } catch (e) {
          binBalances.set(binId, { xBalance: 0n, yBalance: 0n, totalSupply: 0n });
        }
      }
    }

    // Get user balances
    for (const user of users) {
      const xToken = rovOk(mockSbtcToken.getBalance(user));
      const yToken = rovOk(mockUsdcToken.getBalance(user));
      const lpTokens = new Map<bigint, bigint>();

      for (const binId of binBalances.keys()) {
        try {
          const lpBalance = getSbtcUsdcPoolLpBalance(binId, user);
          if (lpBalance > 0n) {
            lpTokens.set(binId, lpBalance);
          }
        } catch { }
      }

      userBalances.set(user, { xToken, yToken, lpTokens });
    }

    return {
      activeBinId,
      binBalances,
      userBalances,
      protocolFees,
    };
  }
}

class AmountGenerator {
  constructor(private rng: SeededRandom) {}

  generateSwapAmount(poolState: PoolState, binId: bigint, direction: 'x-for-y' | 'y-for-x', user: string): bigint | null {
    const binData = poolState.binBalances.get(binId);
    if (!binData) return null;

    const userBalance = poolState.userBalances.get(user);
    if (!userBalance) return null;

    if (direction === 'x-for-y') {
      if (binData.yBalance === 0n || userBalance.xToken === 0n) return null;
      
      const maxFromUser = userBalance.xToken;
      const maxFromBin = (binData.yBalance * 80n) / 100n; // 80% buffer
      const maxAmount = maxFromUser < maxFromBin ? maxFromUser : maxFromBin;
      
      if (maxAmount < TestConfig.MIN_SWAP_AMOUNT) return null;
      
      return this.randomizeAmount(maxAmount);
    } else {
      if (binData.xBalance === 0n || userBalance.yToken === 0n) return null;
      
      const maxFromUser = userBalance.yToken;
      const maxFromBin = (binData.xBalance * 80n) / 100n;
      const maxAmount = maxFromUser < maxFromBin ? maxFromUser : maxFromBin;
      
      if (maxAmount < TestConfig.MIN_SWAP_AMOUNT) return null;
      
      return this.randomizeAmount(maxAmount);
    }
  }

  generateAddLiquidityAmount(poolState: PoolState, binId: bigint, user: string): { xAmount: bigint; yAmount: bigint } | null {
    const userBalance = poolState.userBalances.get(user);
    if (!userBalance) return null;

    const activeBinId = poolState.activeBinId;
    let xAmount = 0n;
    let yAmount = 0n;

    if (binId < activeBinId) {
      if (userBalance.yToken === 0n) return null;
      yAmount = this.randomizeAmount(userBalance.yToken, 0.5);
      if (yAmount < TestConfig.MIN_LIQUIDITY_AMOUNT) return null;
    } else if (binId === activeBinId) {
      if (userBalance.xToken === 0n || userBalance.yToken === 0n) return null;
      xAmount = this.randomizeAmount(userBalance.xToken, 0.5);
      yAmount = this.randomizeAmount(userBalance.yToken, 0.5);
      if (xAmount < TestConfig.MIN_LIQUIDITY_AMOUNT || yAmount < TestConfig.MIN_LIQUIDITY_AMOUNT) return null;
    } else {
      if (userBalance.xToken === 0n) return null;
      xAmount = this.randomizeAmount(userBalance.xToken, 0.5);
      if (xAmount < TestConfig.MIN_LIQUIDITY_AMOUNT) return null;
    }

    return { xAmount, yAmount };
  }

  generateWithdrawAmount(poolState: PoolState, binId: bigint, user: string): bigint | null {
    const userBalance = poolState.userBalances.get(user);
    if (!userBalance) return null;

    const lpBalance = userBalance.lpTokens.get(binId) || 0n;
    if (lpBalance === 0n) return null;

    const percentage = this.rng.next() * 0.7 + 0.2; // 20-90%
    const amount = (lpBalance * BigInt(Math.floor(percentage * 100))) / 100n;
    
    const minAmount = lpBalance > 5000n ? 1000n : (lpBalance * 20n / 100n);
    if (amount < minAmount) {
      return lpBalance >= minAmount ? minAmount : null;
    }
    return amount;
  }

  generateMoveAmount(poolState: PoolState, sourceBinId: bigint, user: string): bigint | null {
    const userBalance = poolState.userBalances.get(user);
    if (!userBalance) return null;

    const lpBalance = userBalance.lpTokens.get(sourceBinId) || 0n;
    if (lpBalance === 0n) return null;

    const percentage = this.rng.next() * 0.8 + 0.1; // 10-90%
    const amount = (lpBalance * BigInt(Math.floor(percentage * 100))) / 100n;
    
    if (amount < 1n) return null;
    return amount;
  }

  private randomizeAmount(maxAmount: bigint, maxPercent: number = 1.0): bigint {
    const rand = this.rng.next();
    let percentage: number;
    
    if (rand < TestConfig.PROB_SWAP_VERY_SMALL) {
      percentage = this.rng.next() * 0.001;
    } else if (rand < TestConfig.PROB_SWAP_VERY_SMALL + TestConfig.PROB_SWAP_SMALL) {
      percentage = this.rng.next() * 0.009 + 0.001;
    } else if (rand < TestConfig.PROB_SWAP_VERY_SMALL + TestConfig.PROB_SWAP_SMALL + TestConfig.PROB_SWAP_MEDIUM) {
      percentage = this.rng.next() * 0.09 + 0.01;
    } else {
      percentage = this.rng.next() * (maxPercent - 0.1) + 0.1;
    }
    
    return (maxAmount * BigInt(Math.floor(percentage * 10000))) / 10000n;
  }
}

class InvariantChecker {
  static checkInvariants(
    functionName: string,
    beforeState: PoolState,
    afterState: PoolState,
    params: any,
    result: any,
    user: string
  ): string[] {
    const issues: string[] = [];
    const binId = params.binId !== undefined ? params.binId : params.sourceBinId;
    
    // Helper to construct state objects
    const getBinState = (state: PoolState, id: bigint): BinState | null => {
      const bin = state.binBalances.get(id);
      return bin ? { binId: id, xBalance: bin.xBalance, yBalance: bin.yBalance, totalSupply: bin.totalSupply } : null;
    };

    const getUserState = (state: PoolState, u: string, id: bigint): UserState | null => {
      const userBal = state.userBalances.get(u);
      return userBal ? { 
        xTokenBalance: userBal.xToken, 
        yTokenBalance: userBal.yToken, 
        lpTokenBalance: userBal.lpTokens.get(id) || 0n 
      } : null;
    };

    const beforeBin = getBinState(beforeState, binId);
    const afterBin = getBinState(afterState, binId);
    const beforeUser = getUserState(beforeState, user, binId);
    const afterUser = getUserState(afterState, user, binId);

    if (!beforeBin || !afterBin || !beforeUser || !afterUser) {
      issues.push(`State data missing for bin ${binId} or user ${user}`);
      return issues;
    }

    if (functionName === 'swap-x-for-y') {
      const check = checkSwapXForYInvariants(
        beforeBin, afterBin, beforeUser, afterUser,
        beforeState.protocolFees, afterState.protocolFees,
        params.amount, result
      );
      issues.push(...check.errors);
    } else if (functionName === 'swap-y-for-x') {
      const check = checkSwapYForXInvariants(
        beforeBin, afterBin, beforeUser, afterUser,
        beforeState.protocolFees, afterState.protocolFees,
        params.amount, result
      );
      issues.push(...check.errors);
    } else if (functionName === 'add-liquidity') {
      const check = checkAddLiquidityInvariantsCore(
        beforeBin, afterBin, beforeUser, afterUser,
        params.xAmount, params.yAmount, result, params.minDlp || 1n
      );
      issues.push(...check.errors);
    } else if (functionName === 'withdraw-liquidity') {
      const check = checkWithdrawLiquidityInvariantsCore(
        beforeBin, afterBin, beforeUser, afterUser,
        params.amount, result.xAmount || 0n, result.yAmount || 0n,
        params.minXAmount || 0n, params.minYAmount || 0n
      );
      issues.push(...check.errors);
    } else if (functionName === 'move-liquidity') {
      const destBinId = params.destBinId;
      const beforeDestBin = getBinState(beforeState, destBinId);
      const afterDestBin = getBinState(afterState, destBinId);
      const beforeUserDest = getUserState(beforeState, user, destBinId);
      const afterUserDest = getUserState(afterState, user, destBinId);

      if (beforeDestBin && afterDestBin && beforeUserDest && afterUserDest) {
        const check = checkMoveLiquidityInvariantsCore(
          beforeBin, afterBin, beforeDestBin, afterDestBin,
          beforeUser, afterUser, beforeUserDest, afterUserDest,
          params.amount, result, params.minDlp || 1n
        );
        issues.push(...check.errors);
      }
    }

    // Global invariants
    if (afterState.activeBinId < MIN_BIN_ID || afterState.activeBinId > MAX_BIN_ID) {
      issues.push(`Active bin out of range: ${afterState.activeBinId}`);
    }

    return issues;
  }
}

class TestOrchestrator {
  private orchestrator: LogManager;
  private rng: SeededRandom;
  private amountGen: AmountGenerator;
  private users = [deployer, alice, bob, charlie];
  private functions: OperationType[] = ['swap-x-for-y', 'swap-y-for-x', 'add-liquidity', 'withdraw-liquidity', 'move-liquidity'];

  constructor(seed: number, orchestrator: LogManager) {
    this.orchestrator = orchestrator;
    this.rng = new SeededRandom(seed);
    this.amountGen = new AmountGenerator(this.rng);
  }

  async run(totalTransactions: number) {
    this.orchestrator.log(`Starting fuzz test with ${totalTransactions} transactions...`);
    let consecutiveFailures = 0;

    for (let i = 1; i <= totalTransactions; i++) {
     this.orchestrator.updateProgress(i, totalTransactions);

      let beforeState: PoolState;
      try {
        beforeState = await PoolStateManager.captureState();
      } catch (e) {
        continue;
      }

      const functionName = this.rng.choice(this.functions);
      const caller = this.rng.choice(this.users);
      const txResult = await this.executeTransaction(functionName, caller, beforeState);

      if (txResult.result === 'failure') {
        consecutiveFailures++;
        if (consecutiveFailures >= TestConfig.MAX_CONSECUTIVE_FAILURES) {
          this.regenerateState(beforeState);
          consecutiveFailures = 0;
        }
        this.orchestrator.incrementStat('failedTransactions');
      } else {
        consecutiveFailures = 0;
        this.orchestrator.incrementStat('successfulTransactions');
      }
      
      this.orchestrator.incrementStat('totalTransactions');
      this.orchestrator.recordResult({ ...txResult, txNumber: i });
      
      if (txResult.invariantChecks && txResult.invariantChecks.length > 0) {
        this.orchestrator.incrementStat('invariantViolations', txResult.invariantChecks.length);
        this.orchestrator.logError(`INVARIANT VIOLATION in tx ${i}`, txResult.invariantChecks);
      }
    }

    this.orchestrator.finish();
    
    expect(this.orchestrator.stats.invariantViolations || 0).toBe(0);
  }

  private async executeTransaction(functionName: OperationType, caller: string, beforeState: PoolState): Promise<Omit<TransactionLog, 'txNumber'>> {
    let params: any = {};
    let result: any;
    let success = false;
    let error: string | undefined;
    let invariantIssues: string[] = [];

    try {
      if (functionName.startsWith('swap')) {
        // Swap implementation
        const activeBinId = beforeState.activeBinId;
        const direction = functionName === 'swap-x-for-y' ? 'x-for-y' : 'y-for-x';
        const amount = this.amountGen.generateSwapAmount(beforeState, activeBinId, direction, caller);
        
        if (!amount) throw new Error("Could not generate valid swap amount");
        
        params = { binId: activeBinId, amount, caller };
        const response = direction === 'x-for-y'
          ? txOk(dlmmCore.swapXForY(sbtcUsdcPool.identifier, mockSbtcToken.identifier, mockUsdcToken.identifier, activeBinId, amount), caller)
          : txOk(dlmmCore.swapYForX(sbtcUsdcPool.identifier, mockSbtcToken.identifier, mockUsdcToken.identifier, activeBinId, amount), caller);
        
        result = cvToValue(response.result);
        if (typeof result === 'bigint' || typeof result === 'number') result = { in: BigInt(result), out: 0n };
        success = true;

      } else if (functionName === 'add-liquidity') {
        // Add Liquidity implementation
        const binOffset = this.rng.nextInt(TestConfig.MIN_BIN_SAMPLE, TestConfig.MAX_BIN_SAMPLE);
        const binId = beforeState.activeBinId + BigInt(binOffset);
        const clampedBinId = binId < MIN_BIN_ID ? MIN_BIN_ID : (binId > MAX_BIN_ID ? MAX_BIN_ID : binId);
        
        const amounts = this.amountGen.generateAddLiquidityAmount(beforeState, clampedBinId, caller);
        if (!amounts) throw new Error("Could not generate liquidity amounts");

        params = { binId: clampedBinId, ...amounts, caller };
        const response = txOk(dlmmCore.addLiquidity(
          sbtcUsdcPool.identifier, mockSbtcToken.identifier, mockUsdcToken.identifier, clampedBinId,
          amounts.xAmount, amounts.yAmount, TestConfig.MIN_DLP,
          TestConfig.MAX_LIQUIDITY_FEE, TestConfig.MAX_LIQUIDITY_FEE
        ), caller);
        
        result = cvToValue(response.result);
        success = true;

      } else if (functionName === 'withdraw-liquidity') {
        // Withdraw Liquidity implementation
        const userBal = beforeState.userBalances.get(caller);
        if (!userBal || userBal.lpTokens.size === 0) throw new Error("User has no LP tokens");
        
        const binId = this.rng.choice(Array.from(userBal.lpTokens.keys()));
        const amount = this.amountGen.generateWithdrawAmount(beforeState, binId, caller);
        if (!amount) throw new Error("Could not generate withdraw amount");

        // min out assert bypass
        const binData = beforeState.binBalances.get(binId);
        let minX = 0n;
        let minY = 0n;
        
        if (binData && binData.xBalance > 0n) {
             minX = 1n;
        } else {
             minY = 1n;
        }

        params = { binId, amount, caller, minXAmount: minX, minYAmount: minY };
        const response = txOk(dlmmCore.withdrawLiquidity(
          sbtcUsdcPool.identifier, mockSbtcToken.identifier, mockUsdcToken.identifier, binId,
          amount, minX, minY
        ), caller);
        
        result = cvToValue(response.result);
        success = true;

      } else if (functionName === 'move-liquidity') {
        // Move Liquidity implementation
        const userBal = beforeState.userBalances.get(caller);
        if (!userBal || userBal.lpTokens.size === 0) throw new Error("User has no LP tokens");
        
        const sourceBinId = this.rng.choice(Array.from(userBal.lpTokens.keys()));
        const amount = this.amountGen.generateMoveAmount(beforeState, sourceBinId, caller);
        if (!amount) throw new Error("Could not generate move amount");

        // Find compatible destination bin
        let destBinId = sourceBinId;
        const sourceBin = beforeState.binBalances.get(sourceBinId);
        const hasX = sourceBin && sourceBin.xBalance > 0n;
        const hasY = sourceBin && sourceBin.yBalance > 0n;
        
        let attempts = 0;
        do {
          const offset = this.rng.nextInt(-5, 5);
          const candidate = beforeState.activeBinId + BigInt(offset);
          
          // Compatibility check based on active bin pricing
          if (candidate === beforeState.activeBinId) {
            destBinId = candidate; // Active bin accepts both
          } else if (candidate > beforeState.activeBinId && hasX && !hasY) {
            destBinId = candidate; // Higher bins needs X
          } else if (candidate < beforeState.activeBinId && hasY && !hasX) {
            destBinId = candidate; // Lower bins needs Y
          }
          attempts++;
        } while(destBinId === sourceBinId && attempts < 10);

        if (destBinId === sourceBinId) throw new Error("Could not find valid destination bin");

        params = { sourceBinId, destBinId, amount, caller };
        const response = txOk(dlmmCore.moveLiquidity(
          sbtcUsdcPool.identifier, mockSbtcToken.identifier, mockUsdcToken.identifier,
          sourceBinId, destBinId, amount, TestConfig.MIN_DLP,
          TestConfig.MAX_LIQUIDITY_FEE, TestConfig.MAX_LIQUIDITY_FEE
        ), caller);
        
        result = cvToValue(response.result);
        success = true;
      }

      // Capture after state and check invariants
      if (success) {
        const afterState = await PoolStateManager.captureState();
        invariantIssues = InvariantChecker.checkInvariants(functionName, beforeState, afterState, params, result, caller);
      }

    } catch (e: any) {
      success = false;
      error = e.message || String(e);
    }

    return { functionName, caller, params, result: success ? 'success' : 'failure', error, invariantChecks: invariantIssues };
  }

  private regenerateState(state: PoolState) {
    // Add liquidity to random bins to fix stuck state
    try {
      for (let i = 0; i < 5; i++) {
        const binId = state.activeBinId + BigInt(this.rng.nextInt(-5, 5));
        const amounts = this.amountGen.generateAddLiquidityAmount(state, binId, deployer);
        if (amounts) {
          txOk(dlmmCore.addLiquidity(
            sbtcUsdcPool.identifier, mockSbtcToken.identifier, mockUsdcToken.identifier, binId,
            amounts.xAmount, amounts.yAmount, 1n, TestConfig.MAX_LIQUIDITY_FEE, TestConfig.MAX_LIQUIDITY_FEE
          ), deployer);
        }
      }
    } catch {}
  }
}

describe('DLMM Core Comprehensive Fuzz Test', () => {
  const config = getFuzzConfig();
  const NUM_TRANSACTIONS = config.size;
  const RANDOM_SEED = config.seed;

  beforeEach(async () => {
    setupTestEnvironment();
    // Mint tokens
    txOk(mockSbtcToken.mint(10000000000n, alice), deployer);
    txOk(mockUsdcToken.mint(1000000000000n, alice), deployer);
    txOk(mockSbtcToken.mint(10000000000n, bob), deployer);
    txOk(mockUsdcToken.mint(1000000000000n, bob), deployer);
    txOk(mockSbtcToken.mint(10000000000n, charlie), deployer);
    txOk(mockUsdcToken.mint(1000000000000n, charlie), deployer);
  });

  it(`should execute ${NUM_TRANSACTIONS} random transactions and maintain invariants`, async () => {
    const orchestrator = new LogManager('comprehensive-fuzz');
    const testOrchestrator = new TestOrchestrator(RANDOM_SEED, orchestrator);
    await testOrchestrator.run(NUM_TRANSACTIONS);
  }, 21600000); // 6 hour timeout
});
