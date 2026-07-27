import {
  alice,
  bob,
  charlie,
  deployer,
  dlmmCore,
  dlmmSwapRouter,
  sbtcUsdcPool,
  mockSbtcToken,
  mockUsdcToken,
  setupTestEnvironment,
} from "../tests/helpers/helpers";

import { describe, it, expect, beforeEach } from 'vitest';
import { txOk, rovOk } from '@clarigen/test';
import { getFuzzConfig } from './harnesses/config';

import {
  calculateBinSwap,
  calculateBinSwapFloat,
  calculateFeeRateBPS,
  BinData,
} from './harnesses/swap-calculations';
import {
  estimateBinsNeeded,
  getSampleBins,
  discoverBinsForSwap,
  calculateMultiBinSwap,
  calculateMultiBinSwapFloat,
  PoolState as MultiBinPoolState,
} from './harnesses/multi-bin-quote-estimation';
import { LogManager, SeededRandom, DirectionType, SwapType } from './utils';

interface PoolState {
  activeBinId: bigint;
  binBalances: Map<bigint, { xBalance: bigint; yBalance: bigint }>;
}

interface SwapValidationResult {
  txNumber: number;
  direction: DirectionType;
  inputAmount: bigint;
  actualSwappedIn: bigint;
  actualSwappedOut: bigint;
  expectedInteger: bigint;
  expectedFloat: bigint;
  integerMatch: boolean;
  floatMatch: boolean;
  bugDetected: boolean;
  binId: bigint;
  binPrice: bigint;
  feeRateBPS: bigint;
  swapType?: SwapType;
}

interface SwapResult {
  swappedIn: bigint;
  swappedOut: bigint;
}

interface PoolData {
  binStep: bigint;
  initialPrice: bigint;
  xProtocolFee?: bigint;
  yProtocolFee?: bigint;
  xProviderFee?: bigint;
  yProviderFee?: bigint;
  xVariableFee?: bigint;
  yVariableFee?: bigint;
}

class TestConfig {
  static readonly PRICE_SCALE_BPS = 100000000n;
  static readonly MIN_SWAP_AMOUNT = 100n;
  static readonly PERCENTAGE_PRECISION = 10000n;
  
  static readonly SINGLE_BIN_MIN_PERCENT = 0.01; // 1%
  static readonly SINGLE_BIN_MAX_PERCENT = 0.30; // 30%
  
  static readonly MULTI_BIN_MIN_PERCENT = 0.80; // 80%
  static readonly MULTI_BIN_MAX_PERCENT = 1.20; // 120%
  static readonly MULTI_BIN_FALLBACK_MIN = 0.50; // 50%
  static readonly MULTI_BIN_FALLBACK_MAX = 1.00; // 100%
  
  static readonly MULTI_BIN_CAPTURE_RADIUS = 20;
  
  static readonly MIN_INTEGER_MATCH_RATE = 90;
  static readonly MIN_FLOAT_MATCH_RATE = 80;
  
  static readonly INITIAL_BTC_BALANCE = 10000000000n; // 100
  static readonly INITIAL_USDC_BALANCE = 1000000000000n; // 10M
}

class PoolStateManager {
  static async captureSingleBin(): Promise<PoolState> {
    const activeBinId = rovOk(sbtcUsdcPool.getActiveBinId());
    const binBalances = new Map<bigint, { xBalance: bigint; yBalance: bigint }>();

    const unsignedBin = rovOk(dlmmCore.getUnsignedBinId(activeBinId));
    try {
      const balances = rovOk(sbtcUsdcPool.getBinBalances(unsignedBin));
      binBalances.set(activeBinId, {
        xBalance: balances.xBalance,
        yBalance: balances.yBalance,
      });
    } catch (e) {
      binBalances.set(activeBinId, { xBalance: 0n, yBalance: 0n });
    }

    return { activeBinId, binBalances };
  }

  /**
   * Capture pool state including multiple bins around the active bin.
   * 
   * @param radius - Number of bins to capture on each side of active bin
   */
  static async captureMultiBin(radius: number = TestConfig.MULTI_BIN_CAPTURE_RADIUS): Promise<PoolState> {
    const activeBinId = rovOk(sbtcUsdcPool.getActiveBinId());
    const binBalances = new Map<bigint, { xBalance: bigint; yBalance: bigint }>();

    for (let offset = -radius; offset <= radius; offset++) {
      const binId = activeBinId + BigInt(offset);
      const unsignedBin = rovOk(dlmmCore.getUnsignedBinId(binId));
      try {
        const balances = rovOk(sbtcUsdcPool.getBinBalances(unsignedBin));
        binBalances.set(binId, {
          xBalance: balances.xBalance,
          yBalance: balances.yBalance,
        });
      } catch (e) {
        binBalances.set(binId, { xBalance: 0n, yBalance: 0n });
      }
    }

    return { activeBinId, binBalances };
  }
}

class SwapAmountGenerator {
  static generateSingleBin(
    rng: SeededRandom,
    poolState: PoolState,
    binId: bigint,
    direction: DirectionType,
    userBalance: bigint,
    binPrice: bigint
  ): bigint | null {
    const binData = poolState.binBalances.get(binId);
    if (!binData) return null;

    if (direction === 'x-for-y') {
      if (binData.yBalance === 0n || userBalance === 0n) return null;
      
      // Formula from pricing.py: max_x_amount = ((reserve_y * PRICE_SCALE_BPS + (bin_price - 1)) / bin_price)
      const maxXFromBin = binPrice > 0n
        ? ((binData.yBalance * TestConfig.PRICE_SCALE_BPS + (binPrice - 1n)) / binPrice)
        : 0n;
      
      const maxAmount = userBalance < maxXFromBin ? userBalance : maxXFromBin;
      if (maxAmount < TestConfig.MIN_SWAP_AMOUNT) return null;
      
      const percentage = rng.next() * (TestConfig.SINGLE_BIN_MAX_PERCENT - TestConfig.SINGLE_BIN_MIN_PERCENT) + TestConfig.SINGLE_BIN_MIN_PERCENT;
      const amount = (maxAmount * BigInt(Math.floor(percentage * Number(TestConfig.PERCENTAGE_PRECISION)))) / TestConfig.PERCENTAGE_PRECISION;
      return amount < TestConfig.MIN_SWAP_AMOUNT ? null : amount;
    } else {
      if (binData.xBalance === 0n || userBalance === 0n) return null;
      
      // Formula from pricing.py: max_y_amount = ((reserve_x * bin_price + (PRICE_SCALE_BPS - 1)) / PRICE_SCALE_BPS)
      const maxYFromBin = ((binData.xBalance * binPrice + (TestConfig.PRICE_SCALE_BPS - 1n)) / TestConfig.PRICE_SCALE_BPS);
      
      const maxAmount = userBalance < maxYFromBin ? userBalance : maxYFromBin;
      if (maxAmount < TestConfig.MIN_SWAP_AMOUNT) return null;
      
      const percentage = rng.next() * (TestConfig.SINGLE_BIN_MAX_PERCENT - TestConfig.SINGLE_BIN_MIN_PERCENT) + TestConfig.SINGLE_BIN_MIN_PERCENT;
      const amount = (maxAmount * BigInt(Math.floor(percentage * Number(TestConfig.PERCENTAGE_PRECISION)))) / TestConfig.PERCENTAGE_PRECISION;
      return amount < TestConfig.MIN_SWAP_AMOUNT ? null : amount;
    }
  }

  static generateMultiBin(
    rng: SeededRandom,
    poolState: PoolState,
    activeBinId: bigint,
    userBalance: bigint
  ): bigint | null {
    const activeBinData = poolState.binBalances.get(activeBinId);
    if (!activeBinData) return null;

    // Sample adjacent bins to estimate total available liquidity
    const sampleBins = getSampleBins(poolState, activeBinId, 5);
    
    // Calculate average liquidity across sampled bins
    const avgLiquidity = sampleBins.length > 0
      ? sampleBins.reduce((sum, bin) => {
          const minReserve = bin.reserve_x < bin.reserve_y ? bin.reserve_x : bin.reserve_y;
          return sum + minReserve;
        }, 0n) / BigInt(sampleBins.length)
      : 0n;
    
    // Calculate active bin capacity; min == 80% of bin
    const minReserve = activeBinData.xBalance < activeBinData.yBalance 
      ? activeBinData.xBalance 
      : activeBinData.yBalance;
    const activeBinCapacity = (minReserve * 80n) / 100n;
    
    // Estimate total liquidity across ~5 bins
    const estimatedTotalLiquidity = avgLiquidity > 0n
      ? activeBinCapacity + (avgLiquidity * 4n) // Active + 4 adjacent bins
      : activeBinCapacity * 2n; // Fallback: assume 2x active bin
    
    // Generate amount; 110-150% of active bin capacity
    // Cap at 50% of total estimated liquidity
    const minAmount = (activeBinCapacity * 110n) / 100n;
    const maxFromActiveRatio = (activeBinCapacity * 150n) / 100n;
    const maxFromTotalLiquidity = (estimatedTotalLiquidity * 50n) / 100n;
    const maxAmount = maxFromActiveRatio < maxFromTotalLiquidity 
      ? maxFromActiveRatio 
      : maxFromTotalLiquidity;
    
    // Apply user balance constraint
    const effectiveMax = userBalance < maxAmount ? userBalance : maxAmount;
    
    // Validate bounds
    if (effectiveMax < minAmount || effectiveMax < TestConfig.MIN_SWAP_AMOUNT) {
      return null;
    }
    
    // in range [minAmount, effectiveMax]
    const range = effectiveMax - minAmount;
    const amount = minAmount + (range * BigInt(Math.floor(rng.next() * Number(TestConfig.PERCENTAGE_PRECISION)))) / TestConfig.PERCENTAGE_PRECISION;
    
    return amount < TestConfig.MIN_SWAP_AMOUNT ? null : amount;
  }
}

class SwapExecutor {
  /**
   * Execute a single-bin swap.
   */
  static executeSingleBin(
    direction: DirectionType,
    amount: bigint,
    activeBinId: bigint,
    user: string
  ): SwapResult {
    if (direction === 'x-for-y') {
      const result = txOk(dlmmCore.swapXForY(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        Number(activeBinId),
        amount
      ), user);
      return { swappedIn: result.value.in, swappedOut: result.value.out };
    } else {
      const result = txOk(dlmmCore.swapYForX(
        sbtcUsdcPool.identifier,
        mockSbtcToken.identifier,
        mockUsdcToken.identifier,
        Number(activeBinId),
        amount
      ), user);
      return { swappedIn: result.value.in, swappedOut: result.value.out };
    }
  }

  /**
   * Execute a multi-bin swap using the swap router.
   */
  static executeMultiBin(
    direction: DirectionType,
    amount: bigint,
    user: string
  ): SwapResult {
    if (direction === 'x-for-y') {
      const result = txOk(
        dlmmSwapRouter.swapXForYSimpleMulti(
          sbtcUsdcPool.identifier,
          mockSbtcToken.identifier,
          mockUsdcToken.identifier,
          amount,
          0n
        ),
        user
      );
      return { swappedIn: result.value.in, swappedOut: result.value.out };
    } else {
      const result = txOk(
        dlmmSwapRouter.swapYForXSimpleMulti(
          sbtcUsdcPool.identifier,
          mockSbtcToken.identifier,
          mockUsdcToken.identifier,
          amount,
          0n
        ),
        user
      );
      return { swappedIn: result.value.in, swappedOut: result.value.out };
    }
  }
}

class SwapValidator {
  /**
   * Validate a single-bin swap against the quote engine.
   */
  static validateSingleBin(
    txNumber: number,
    direction: DirectionType,
    inputAmount: bigint,
    actualSwappedIn: bigint,
    actualSwappedOut: bigint,
    poolState: PoolState,
    binId: bigint,
    binPrice: bigint,
    protocolFeeBPS: bigint,
    providerFeeBPS: bigint,
    variableFeeBPS: bigint
  ): SwapValidationResult {
    const feeRateBPS = calculateFeeRateBPS(protocolFeeBPS, providerFeeBPS, variableFeeBPS);
    
    const binData: BinData = {
      reserve_x: poolState.binBalances.get(binId)?.xBalance || 0n,
      reserve_y: poolState.binBalances.get(binId)?.yBalance || 0n,
    };

    const swapForY = direction === 'x-for-y';
    const effectiveInput = actualSwappedIn > 0n ? actualSwappedIn : inputAmount;
    
    const integerResult = calculateBinSwap(binData, binPrice, effectiveInput, feeRateBPS, swapForY);
    const floatResult = calculateBinSwapFloat(
      binData,
      Number(binPrice),
      Number(effectiveInput),
      Number(feeRateBPS),
      swapForY
    );

    const expectedInteger = integerResult.out_this;
    const expectedFloat = BigInt(Math.floor(floatResult.out_this));
    const integerMatch = expectedInteger === actualSwappedOut;
    const floatMatch = expectedFloat === actualSwappedOut;
    const bugDetected = actualSwappedOut > expectedFloat;

    return {
      txNumber,
      direction,
      inputAmount,
      actualSwappedIn,
      actualSwappedOut,
      expectedInteger,
      expectedFloat,
      integerMatch,
      floatMatch,
      bugDetected,
      binId,
      binPrice,
      feeRateBPS,
    };
  }

  /**
   * Validate a multi-bin swap against the quote engine.
   */
  static async validateMultiBin(
    txNumber: number,
    direction: DirectionType,
    inputAmount: bigint,
    actualSwappedIn: bigint,
    actualSwappedOut: bigint,
    poolState: PoolState,
    poolData: PoolData,
    protocolFeeBPS: bigint,
    providerFeeBPS: bigint,
    variableFeeBPS: bigint
  ): Promise<SwapValidationResult> {
    const feeRateBPS = calculateFeeRateBPS(protocolFeeBPS, providerFeeBPS, variableFeeBPS);
    const swapForY = direction === 'x-for-y';
    const activeBinId = poolState.activeBinId;

    const multiBinPoolState: MultiBinPoolState = {
      activeBinId,
      binBalances: poolState.binBalances,
    };

    const activeBinData = poolState.binBalances.get(activeBinId);
    if (!activeBinData) throw new Error('Active bin data not found');

    const binData: BinData = {
      reserve_x: activeBinData.xBalance,
      reserve_y: activeBinData.yBalance,
    };

    const effectiveInput = actualSwappedIn > 0n ? actualSwappedIn : inputAmount;
    const sampleBins = getSampleBins(multiBinPoolState, activeBinId, 2);
    const estimatedBins = estimateBinsNeeded(effectiveInput, binData, sampleBins);

    const getBinPrice = async (initialPrice: bigint, binStep: bigint, binId: bigint): Promise<bigint> => {
      return rovOk(dlmmCore.getBinPrice(initialPrice, binStep, binId));
    };

    const getBinBalances = async (binId: bigint): Promise<{ xBalance: bigint; yBalance: bigint } | null> => {
      try {
        const unsignedBin = rovOk(dlmmCore.getUnsignedBinId(binId));
        const balances = rovOk(sbtcUsdcPool.getBinBalances(unsignedBin));
        return {
          xBalance: balances.xBalance,
          yBalance: balances.yBalance,
        };
      } catch (e) {
        return null;
      }
    };

    const discoveredBins = await discoverBinsForSwap(
      multiBinPoolState,
      activeBinId,
      swapForY,
      estimatedBins,
      getBinPrice,
      poolData.initialPrice,
      poolData.binStep,
      getBinBalances
    );

    const integerResult = calculateMultiBinSwap(discoveredBins, effectiveInput, feeRateBPS, swapForY);
    const floatResult = calculateMultiBinSwapFloat(discoveredBins, effectiveInput, feeRateBPS, swapForY);

    const expectedInteger = integerResult.totalOut;
    const expectedFloat = BigInt(Math.floor(floatResult.totalOut));
    const integerMatch = expectedInteger === actualSwappedOut;
    const floatMatch = expectedFloat === actualSwappedOut;
    const bugDetected = actualSwappedOut > expectedFloat;
    const binPrice = rovOk(dlmmCore.getBinPrice(poolData.initialPrice, poolData.binStep, activeBinId));

    return {
      txNumber,
      direction,
      inputAmount,
      actualSwappedIn,
      actualSwappedOut,
      expectedInteger,
      expectedFloat,
      integerMatch,
      floatMatch,
      bugDetected,
      binId: activeBinId,
      binPrice,
      feeRateBPS,
    };
  }
}

class TestOrchestrator {
  private orchestrator: LogManager;
  private rng: SeededRandom;
  private users: string[];

  constructor(orchestrator: LogManager, rng: SeededRandom) {
    this.orchestrator = orchestrator;
    this.rng = rng;
    this.users = [alice, bob, charlie];
  }

  async runSwapIteration(
    txNumber: number,
    _totalTransactions: number,
    multiBinMode: boolean
  ): Promise<{ success: boolean; bugDetected: boolean }> {
    const useMultiBin = multiBinMode && this.rng.next() < 0.5;
    
    const beforeState = useMultiBin
      ? await PoolStateManager.captureMultiBin()
      : await PoolStateManager.captureSingleBin();
    
    const activeBinId = beforeState.activeBinId;
    const poolData = rovOk(sbtcUsdcPool.getPool());
    const binPrice = rovOk(dlmmCore.getBinPrice(poolData.initialPrice, poolData.binStep, activeBinId));
    
    const user = this.users[this.rng.nextInt(0, this.users.length - 1)];
    const direction: DirectionType = this.rng.next() < 0.5 ? 'x-for-y' : 'y-for-x';
    
    const userXBalance = rovOk(mockSbtcToken.getBalance(user));
    const userYBalance = rovOk(mockUsdcToken.getBalance(user));
    const userBalance = direction === 'x-for-y' ? userXBalance : userYBalance;
    
    const swapAmount = useMultiBin
      ? SwapAmountGenerator.generateMultiBin(this.rng, beforeState, activeBinId, userBalance)
      : SwapAmountGenerator.generateSingleBin(this.rng, beforeState, activeBinId, direction, userBalance, binPrice);
    
    if (!swapAmount || swapAmount === 0n) {
      return { success: false, bugDetected: false };
    }
    
    try {
      const swapResult = useMultiBin
        ? SwapExecutor.executeMultiBin(direction, swapAmount, user)
        : SwapExecutor.executeSingleBin(direction, swapAmount, activeBinId, user);
      
      const protocolFeeBPS = direction === 'x-for-y' ? poolData.xProtocolFee || 0n : poolData.yProtocolFee || 0n;
      const providerFeeBPS = direction === 'x-for-y' ? poolData.xProviderFee || 0n : poolData.yProviderFee || 0n;
      const variableFeeBPS = direction === 'x-for-y' ? poolData.xVariableFee || 0n : poolData.yVariableFee || 0n;
      
      const validation = useMultiBin
        ? await SwapValidator.validateMultiBin(
            txNumber,
            direction,
            swapAmount,
            swapResult.swappedIn,
            swapResult.swappedOut,
            beforeState,
            poolData,
            protocolFeeBPS,
            providerFeeBPS,
            variableFeeBPS
          )
        : SwapValidator.validateSingleBin(
            txNumber,
            direction,
            swapAmount,
            swapResult.swappedIn,
            swapResult.swappedOut,
            beforeState,
            activeBinId,
            binPrice,
            protocolFeeBPS,
            providerFeeBPS,
            variableFeeBPS
          );
      
      validation.swapType = useMultiBin ? 'multi-bin' : 'single-bin';
      
      this.orchestrator.recordResult(validation);
      this.updateStats(validation);
      
      if (validation.bugDetected) {
        this.orchestrator.logError(`BUG DETECTED at tx ${txNumber}`, validation);
        return { success: true, bugDetected: true };
      }
      
      return { success: true, bugDetected: false };
    } catch (e: any) {
        // swap fail
        this.orchestrator.incrementStat('failedSwaps');
        return { success: false, bugDetected: false };
    }
  }

  private updateStats(result: SwapValidationResult) {
      this.orchestrator.incrementStat('totalSwaps');
      if (result.actualSwappedOut > 0n) this.orchestrator.incrementStat('successfulSwaps');
      else this.orchestrator.incrementStat('failedSwaps');
      
      if (result.integerMatch) this.orchestrator.incrementStat('integerMatches');
      if (result.floatMatch) this.orchestrator.incrementStat('floatMatches');
      if (result.bugDetected) this.orchestrator.incrementStat('bugsDetected');
  }
}

describe('DLMM Core Quote Engine Validation Fuzz Test', () => {
  let rng: SeededRandom;
  
  const config = getFuzzConfig();
  const NUM_TRANSACTIONS = config.size;
  const RANDOM_SEED = config.seed;
  const MULTI_BIN_MODE = config.multiBin ?? false;

  beforeEach(async () => {
    setupTestEnvironment();
    
    txOk(mockSbtcToken.mint(TestConfig.INITIAL_BTC_BALANCE, alice), deployer);
    txOk(mockUsdcToken.mint(TestConfig.INITIAL_USDC_BALANCE, alice), deployer);
    txOk(mockSbtcToken.mint(TestConfig.INITIAL_BTC_BALANCE, bob), deployer);
    txOk(mockUsdcToken.mint(TestConfig.INITIAL_USDC_BALANCE, bob), deployer);
    txOk(mockSbtcToken.mint(TestConfig.INITIAL_BTC_BALANCE, charlie), deployer);
    txOk(mockUsdcToken.mint(TestConfig.INITIAL_USDC_BALANCE, charlie), deployer);
    
    rng = new SeededRandom(RANDOM_SEED);
  });

  it(`should validate swap calculations against quote engine (${NUM_TRANSACTIONS} transactions)`, async () => {
    const orchestrator = new LogManager('quote-engine-validation');
    const testOrchestrator = new TestOrchestrator(orchestrator, rng);
    
    let txNumber = 0;

    orchestrator.log(`\n Starting Quote Engine Validation Fuzz Test`);
    orchestrator.log(`   Transactions: ${NUM_TRANSACTIONS}`);
    orchestrator.log(`   Random Seed: ${RANDOM_SEED}`);
    orchestrator.log(`   Multi-Bin Mode: ${MULTI_BIN_MODE ? 'ENABLED' : 'DISABLED'}\n`);

    for (let i = 0; i < NUM_TRANSACTIONS; i++) {
      txNumber++;
      
      orchestrator.updateProgress(txNumber, NUM_TRANSACTIONS);
      
      const result = await testOrchestrator.runSwapIteration(txNumber, NUM_TRANSACTIONS, MULTI_BIN_MODE);
      
      if (!result.success) {
        txNumber--;
        continue;
      }
    }
    
    orchestrator.finish();
    
    expect(orchestrator.stats.bugsDetected || 0).toBe(0);
    
    const totalSwaps = orchestrator.stats.totalSwaps || 0;
    if (totalSwaps > 0) {
      const integerMatchRate = ((orchestrator.stats.integerMatches || 0) / totalSwaps) * 100;
      const floatMatchRate = ((orchestrator.stats.floatMatches || 0) / totalSwaps) * 100;
      
      expect(integerMatchRate).toBeGreaterThanOrEqual(TestConfig.MIN_INTEGER_MATCH_RATE);
      expect(floatMatchRate).toBeGreaterThanOrEqual(TestConfig.MIN_FLOAT_MATCH_RATE);
    } else {
      expect(totalSwaps).toBeGreaterThan(0);
    }
  }, NUM_TRANSACTIONS > 100 ? 300000 : NUM_TRANSACTIONS > 50 ? 120000 : 60000);
});
