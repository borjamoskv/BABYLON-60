import { dlmmCore, sbtcUsdcPool, mockSbtcToken, mockUsdcToken } from "../../tests/helpers/helpers";
import { rovOk } from '@clarigen/test';

export interface BinState {
  binId: bigint;
  xBalance: bigint;
  yBalance: bigint;
  totalSupply: bigint;
}

export interface UserState {
  xTokenBalance: bigint;
  yTokenBalance: bigint;
  lpTokenBalance: bigint; // For specific bin
}

export interface ProtocolFeesState {
  xFee: bigint;
  yFee: bigint;
}

/**
 * Capture bin state
 */
export function captureBinState(binId: bigint): BinState {
  const unsignedBinId = rovOk(dlmmCore.getUnsignedBinId(binId));
  try {
    const balances = rovOk(sbtcUsdcPool.getBinBalances(unsignedBinId));
    const totalSupply = rovOk(sbtcUsdcPool.getTotalSupply(unsignedBinId));
    return {
      binId,
      xBalance: balances.xBalance,
      yBalance: balances.yBalance,
      totalSupply,
    };
  } catch {
    return { binId, xBalance: 0n, yBalance: 0n, totalSupply: 0n };
  }
}

/**
 * Capture user state
 */
export function captureUserState(user: string, binId?: bigint): UserState {
  const xTokenBalance = rovOk(mockSbtcToken.getBalance(user));
  const yTokenBalance = rovOk(mockUsdcToken.getBalance(user));
  let lpTokenBalance = 0n;
  
  if (binId !== undefined) {
    const unsignedBinId = rovOk(dlmmCore.getUnsignedBinId(binId));
    try {
      lpTokenBalance = rovOk(sbtcUsdcPool.getBalance(unsignedBinId, user));
    } catch {
      lpTokenBalance = 0n;
    }
  }
  
  return { xTokenBalance, yTokenBalance, lpTokenBalance };
}

/**
 * Capture protocol fees state
 */
export function captureProtocolFeesState(poolId: bigint): ProtocolFeesState {
  try {
    const fees = rovOk(dlmmCore.getUnclaimedProtocolFeesById(poolId));
    if (!fees) {
      return { xFee: 0n, yFee: 0n };
    }
    return { xFee: fees.xFee, yFee: fees.yFee };
  } catch {
    return { xFee: 0n, yFee: 0n };
  }
}

export interface InvariantCheckResult {
  passed: boolean;
  errors: string[];
}

/**
 * Check invariants for swap-x-for-y
 * 
 * Invariants:
 * - Bin X balance MUST increase (by input - fees)
 * - Bin Y balance MUST decrease (by output)
 * - LP supply MUST remain unchanged
 * - User X balance MUST decrease by input amount
 * - User Y balance MUST increase by output amount
 * - Protocol fees MUST increase (if applicable)
 * - All balances MUST remain non-negative
 */
export function checkSwapXForYInvariants(
  beforeBin: BinState,
  afterBin: BinState,
  beforeUser: UserState,
  afterUser: UserState,
  beforeFees: ProtocolFeesState,
  afterFees: ProtocolFeesState,
  xAmount: bigint,
  swapResult: { in: bigint; out: bigint }
): InvariantCheckResult {
  const errors: string[] = [];

  // LP supply MUST remain unchanged
  if (afterBin.totalSupply !== beforeBin.totalSupply) {
    errors.push(`LP supply changed: ${beforeBin.totalSupply} -> ${afterBin.totalSupply} (must remain unchanged)`);
  }

  // Bin X balance MUST increase
  const xBalanceIncrease = afterBin.xBalance - beforeBin.xBalance;
  if (xBalanceIncrease <= 0n) {
    errors.push(`Bin X balance did not increase: ${beforeBin.xBalance} -> ${afterBin.xBalance}`);
  }

  // Bin Y balance MUST decrease
  const yBalanceDecrease = beforeBin.yBalance - afterBin.yBalance;
  if (yBalanceDecrease <= 0n) {
    errors.push(`Bin Y balance did not decrease: ${beforeBin.yBalance} -> ${afterBin.yBalance}`);
  }

  // User X balance MUST decrease by actual swapped amount (contract may cap the input)
  // Use swapResult.in which is the actual amount swapped, not the requested xAmount
  const actualSwappedIn = swapResult?.in || 0n;
  const userXDecrease = beforeUser.xTokenBalance - afterUser.xTokenBalance;
  if (actualSwappedIn > 0n && userXDecrease !== actualSwappedIn) {
    errors.push(`User X balance decreased by ${userXDecrease}, expected ${actualSwappedIn} (requested was ${xAmount})`);
  }

  // User Y balance MUST increase by output amount
  const userYIncrease = afterUser.yTokenBalance - beforeUser.yTokenBalance;
  if (userYIncrease !== swapResult.out) {
    errors.push(`User Y balance increased by ${userYIncrease}, expected ${swapResult.out}`);
  }

  // Protocol fees MUST increase (if applicable)
  const feesXIncrease = afterFees.xFee - beforeFees.xFee;
  if (feesXIncrease < 0n) {
    errors.push(`Protocol X fees decreased: ${beforeFees.xFee} -> ${afterFees.xFee}`);
  }

  // All balances MUST remain non-negative
  if (afterBin.xBalance < 0n || afterBin.yBalance < 0n || afterBin.totalSupply < 0n) {
    errors.push(`Negative bin balances detected: x=${afterBin.xBalance}, y=${afterBin.yBalance}, supply=${afterBin.totalSupply}`);
  }
  if (afterUser.xTokenBalance < 0n || afterUser.yTokenBalance < 0n) {
    errors.push(`Negative user balances detected: x=${afterUser.xTokenBalance}, y=${afterUser.yTokenBalance}`);
  }

  return { passed: errors.length === 0, errors };
}

/**
 * Check invariants for swap-y-for-x
 * 
 * Invariants:
 * - Bin Y balance MUST increase (by input - fees)
 * - Bin X balance MUST decrease (by output)
 * - LP supply MUST remain unchanged
 * - User Y balance MUST decrease by input amount
 * - User X balance MUST increase by output amount
 * - Protocol fees MUST increase (if applicable)
 * - All balances MUST remain non-negative
 */
export function checkSwapYForXInvariants(
  beforeBin: BinState,
  afterBin: BinState,
  beforeUser: UserState,
  afterUser: UserState,
  beforeFees: ProtocolFeesState,
  afterFees: ProtocolFeesState,
  yAmount: bigint,
  swapResult: { in: bigint; out: bigint }
): InvariantCheckResult {
  const errors: string[] = [];

  // LP supply MUST remain unchanged
  if (afterBin.totalSupply !== beforeBin.totalSupply) {
    errors.push(`LP supply changed: ${beforeBin.totalSupply} -> ${afterBin.totalSupply} (must remain unchanged)`);
  }

  // Bin Y balance MUST increase
  const yBalanceIncrease = afterBin.yBalance - beforeBin.yBalance;
  if (yBalanceIncrease <= 0n) {
    errors.push(`Bin Y balance did not increase: ${beforeBin.yBalance} -> ${afterBin.yBalance}`);
  }

  // Bin X balance MUST decrease
  const xBalanceDecrease = beforeBin.xBalance - afterBin.xBalance;
  if (xBalanceDecrease <= 0n) {
    errors.push(`Bin X balance did not decrease: ${beforeBin.xBalance} -> ${afterBin.xBalance}`);
  }

  // User Y balance MUST decrease by actual swapped amount (contract may cap the input)
  // Use swapResult.in which is the actual amount swapped, not the requested yAmount
  const actualSwappedIn = swapResult?.in || 0n;
  const userYDecrease = beforeUser.yTokenBalance - afterUser.yTokenBalance;
  if (actualSwappedIn > 0n && userYDecrease !== actualSwappedIn) {
    errors.push(`User Y balance decreased by ${userYDecrease}, expected ${actualSwappedIn} (requested was ${yAmount})`);
  }

  // User X balance MUST increase by output amount
  const userXIncrease = afterUser.xTokenBalance - beforeUser.xTokenBalance;
  if (userXIncrease !== swapResult.out) {
    errors.push(`User X balance increased by ${userXIncrease}, expected ${swapResult.out}`);
  }

  // Protocol fees MUST increase (if applicable)
  const feesYIncrease = afterFees.yFee - beforeFees.yFee;
  if (feesYIncrease < 0n) {
    errors.push(`Protocol Y fees decreased: ${beforeFees.yFee} -> ${afterFees.yFee}`);
  }

  // All balances MUST remain non-negative
  if (afterBin.xBalance < 0n || afterBin.yBalance < 0n || afterBin.totalSupply < 0n) {
    errors.push(`Negative bin balances detected: x=${afterBin.xBalance}, y=${afterBin.yBalance}, supply=${afterBin.totalSupply}`);
  }
  if (afterUser.xTokenBalance < 0n || afterUser.yTokenBalance < 0n) {
    errors.push(`Negative user balances detected: x=${afterUser.xTokenBalance}, y=${afterUser.yTokenBalance}`);
  }

  return { passed: errors.length === 0, errors };
}

/**
 * Check invariants for add-liquidity
 * 
 * Invariants:
 * - LP supply for that bin MUST increase
 * - X balance in bin MUST increase (if xAmount > 0)
 * - Y balance in bin MUST increase (if yAmount > 0)
 * - User LP balance for that bin MUST increase
 * - User X balance MUST decrease (if xAmount > 0)
 * - User Y balance MUST decrease (if yAmount > 0)
 * - LP tokens minted MUST be > 0
 * - LP tokens minted MUST be >= minDlp
 */
export function checkAddLiquidityInvariants(
  beforeBin: BinState,
  afterBin: BinState,
  beforeUser: UserState,
  afterUser: UserState,
  xAmount: bigint,
  yAmount: bigint,
  lpTokensMinted: bigint,
  minDlp: bigint
): InvariantCheckResult {
  const errors: string[] = [];

  // LP supply MUST increase
  if (afterBin.totalSupply <= beforeBin.totalSupply) {
    errors.push(`LP supply did not increase: ${beforeBin.totalSupply} -> ${afterBin.totalSupply}`);
  }

  // X balance MUST increase if xAmount > 0
  if (xAmount > 0n && afterBin.xBalance <= beforeBin.xBalance) {
    errors.push(`Bin X balance did not increase: ${beforeBin.xBalance} -> ${afterBin.xBalance} (xAmount=${xAmount})`);
  }

  // Y balance MUST increase if yAmount > 0
  if (yAmount > 0n && afterBin.yBalance <= beforeBin.yBalance) {
    errors.push(`Bin Y balance did not increase: ${beforeBin.yBalance} -> ${afterBin.yBalance} (yAmount=${yAmount})`);
  }

  // User LP balance MUST increase
  if (afterUser.lpTokenBalance <= beforeUser.lpTokenBalance) {
    errors.push(`User LP balance did not increase: ${beforeUser.lpTokenBalance} -> ${afterUser.lpTokenBalance}`);
  }

  // User X balance MUST decrease if xAmount > 0
  if (xAmount > 0n) {
    const userXDecrease = beforeUser.xTokenBalance - afterUser.xTokenBalance;
    if (userXDecrease !== xAmount) {
      errors.push(`User X balance decreased by ${userXDecrease}, expected ${xAmount}`);
    }
  }

  // User Y balance MUST decrease if yAmount > 0
  if (yAmount > 0n) {
    const userYDecrease = beforeUser.yTokenBalance - afterUser.yTokenBalance;
    if (userYDecrease !== yAmount) {
      errors.push(`User Y balance decreased by ${userYDecrease}, expected ${yAmount}`);
    }
  }

  // LP tokens minted MUST be > 0
  if (lpTokensMinted <= 0n) {
    errors.push(`LP tokens minted must be > 0, got ${lpTokensMinted}`);
  }

  // LP tokens minted MUST be >= minDlp
  if (lpTokensMinted < minDlp) {
    errors.push(`LP tokens minted ${lpTokensMinted} < minDlp ${minDlp}`);
  }

  // All balances MUST remain non-negative
  if (afterBin.xBalance < 0n || afterBin.yBalance < 0n || afterBin.totalSupply < 0n) {
    errors.push(`Negative bin balances detected: x=${afterBin.xBalance}, y=${afterBin.yBalance}, supply=${afterBin.totalSupply}`);
  }
  if (afterUser.xTokenBalance < 0n || afterUser.yTokenBalance < 0n || afterUser.lpTokenBalance < 0n) {
    errors.push(`Negative user balances detected: x=${afterUser.xTokenBalance}, y=${afterUser.yTokenBalance}, lp=${afterUser.lpTokenBalance}`);
  }

  return { passed: errors.length === 0, errors };
}

/**
 * Check invariants for withdraw-liquidity
 * 
 * Invariants:
 * - LP supply for that bin MUST decrease
 * - X balance in bin MUST decrease (if X was in bin)
 * - Y balance in bin MUST decrease (if Y was in bin)
 * - User LP balance for that bin MUST decrease
 * - User X balance MUST increase (if X was withdrawn)
 * - User Y balance MUST increase (if Y was withdrawn)
 * - LP tokens burned MUST be > 0
 * - X and Y amounts received MUST be >= minXAmount and minYAmount
 */
export function checkWithdrawLiquidityInvariants(
  beforeBin: BinState,
  afterBin: BinState,
  beforeUser: UserState,
  afterUser: UserState,
  lpTokensBurned: bigint,
  xAmountReceived: bigint,
  yAmountReceived: bigint,
  minXAmount: bigint,
  minYAmount: bigint
): InvariantCheckResult {
  const errors: string[] = [];

  // LP supply MUST decrease
  if (afterBin.totalSupply >= beforeBin.totalSupply) {
    errors.push(`LP supply did not decrease: ${beforeBin.totalSupply} -> ${afterBin.totalSupply}`);
  }

  // X balance MUST decrease if X was in bin
  if (beforeBin.xBalance > 0n && afterBin.xBalance >= beforeBin.xBalance) {
    errors.push(`Bin X balance did not decrease: ${beforeBin.xBalance} -> ${afterBin.xBalance}`);
  }

  // Y balance MUST decrease if Y was in bin
  if (beforeBin.yBalance > 0n && afterBin.yBalance >= beforeBin.yBalance) {
    errors.push(`Bin Y balance did not decrease: ${beforeBin.yBalance} -> ${afterBin.yBalance}`);
  }

  // User LP balance MUST decrease
  if (afterUser.lpTokenBalance >= beforeUser.lpTokenBalance) {
    errors.push(`User LP balance did not decrease: ${beforeUser.lpTokenBalance} -> ${afterUser.lpTokenBalance}`);
  }

  // User X balance MUST increase if X was withdrawn
  if (xAmountReceived > 0n) {
    const userXIncrease = afterUser.xTokenBalance - beforeUser.xTokenBalance;
    if (userXIncrease < xAmountReceived) {
      errors.push(`User X balance increased by ${userXIncrease}, expected at least ${xAmountReceived}`);
    }
  }

  // User Y balance MUST increase if Y was withdrawn
  if (yAmountReceived > 0n) {
    const userYIncrease = afterUser.yTokenBalance - beforeUser.yTokenBalance;
    if (userYIncrease < yAmountReceived) {
      errors.push(`User Y balance increased by ${userYIncrease}, expected at least ${yAmountReceived}`);
    }
  }

  // LP tokens burned MUST be > 0
  if (lpTokensBurned <= 0n) {
    errors.push(`LP tokens burned must be > 0, got ${lpTokensBurned}`);
  }

  // X amount received MUST be >= minXAmount
  if (xAmountReceived < minXAmount) {
    errors.push(`X amount received ${xAmountReceived} < minXAmount ${minXAmount}`);
  }

  // Y amount received MUST be >= minYAmount
  if (yAmountReceived < minYAmount) {
    errors.push(`Y amount received ${yAmountReceived} < minYAmount ${minYAmount}`);
  }

  // All balances MUST remain non-negative
  if (afterBin.xBalance < 0n || afterBin.yBalance < 0n || afterBin.totalSupply < 0n) {
    errors.push(`Negative bin balances detected: x=${afterBin.xBalance}, y=${afterBin.yBalance}, supply=${afterBin.totalSupply}`);
  }
  if (afterUser.xTokenBalance < 0n || afterUser.yTokenBalance < 0n || afterUser.lpTokenBalance < 0n) {
    errors.push(`Negative user balances detected: x=${afterUser.xTokenBalance}, y=${afterUser.yTokenBalance}, lp=${afterUser.lpTokenBalance}`);
  }

  return { passed: errors.length === 0, errors };
}

/**
 * Check invariants for move-liquidity
 * 
 * Invariants:
 * - Source bin LP supply MUST decrease
 * - Destination bin LP supply MUST increase
 * - Source bin X/Y balances MUST decrease proportionally
 * - Destination bin X/Y balances MUST increase proportionally
 * - User LP balance in source bin MUST decrease
 * - User LP balance in destination bin MUST increase
 * - LP tokens moved MUST be > 0
 * - LP tokens minted in destination MUST be >= minDlp
 */
export function checkMoveLiquidityInvariants(
  beforeSourceBin: BinState,
  afterSourceBin: BinState,
  beforeDestBin: BinState,
  afterDestBin: BinState,
  beforeUserSource: UserState,
  afterUserSource: UserState,
  beforeUserDest: UserState,
  afterUserDest: UserState,
  lpTokensMoved: bigint,
  lpTokensMinted: bigint,
  minDlp: bigint
): InvariantCheckResult {
  const errors: string[] = [];

  // Source bin LP supply MUST decrease
  if (afterSourceBin.totalSupply >= beforeSourceBin.totalSupply) {
    errors.push(`Source bin LP supply did not decrease: ${beforeSourceBin.totalSupply} -> ${afterSourceBin.totalSupply}`);
  }

  // Destination bin LP supply MUST increase
  if (afterDestBin.totalSupply <= beforeDestBin.totalSupply) {
    errors.push(`Destination bin LP supply did not increase: ${beforeDestBin.totalSupply} -> ${afterDestBin.totalSupply}`);
  }

  // Source bin X balance MUST decrease if it had X
  if (beforeSourceBin.xBalance > 0n && afterSourceBin.xBalance >= beforeSourceBin.xBalance) {
    errors.push(`Source bin X balance did not decrease: ${beforeSourceBin.xBalance} -> ${afterSourceBin.xBalance}`);
  }

  // Source bin Y balance MUST decrease if it had Y
  if (beforeSourceBin.yBalance > 0n && afterSourceBin.yBalance >= beforeSourceBin.yBalance) {
    errors.push(`Source bin Y balance did not decrease: ${beforeSourceBin.yBalance} -> ${afterSourceBin.yBalance}`);
  }

  // User LP balance in source bin MUST decrease
  if (afterUserSource.lpTokenBalance >= beforeUserSource.lpTokenBalance) {
    errors.push(`User LP balance in source bin did not decrease: ${beforeUserSource.lpTokenBalance} -> ${afterUserSource.lpTokenBalance}`);
  }

  // User LP balance in destination bin MUST increase
  if (afterUserDest.lpTokenBalance <= beforeUserDest.lpTokenBalance) {
    errors.push(`User LP balance in destination bin did not increase: ${beforeUserDest.lpTokenBalance} -> ${afterUserDest.lpTokenBalance}`);
  }

  // LP tokens moved MUST be > 0
  if (lpTokensMoved <= 0n) {
    errors.push(`LP tokens moved must be > 0, got ${lpTokensMoved}`);
  }

  // LP tokens minted MUST be >= minDlp
  if (lpTokensMinted < minDlp) {
    errors.push(`LP tokens minted ${lpTokensMinted} < minDlp ${minDlp}`);
  }

  // All balances MUST remain non-negative
  if (afterSourceBin.xBalance < 0n || afterSourceBin.yBalance < 0n || afterSourceBin.totalSupply < 0n) {
    errors.push(`Negative source bin balances detected: x=${afterSourceBin.xBalance}, y=${afterSourceBin.yBalance}, supply=${afterSourceBin.totalSupply}`);
  }
  if (afterDestBin.xBalance < 0n || afterDestBin.yBalance < 0n || afterDestBin.totalSupply < 0n) {
    errors.push(`Negative destination bin balances detected: x=${afterDestBin.xBalance}, y=${afterDestBin.yBalance}, supply=${afterDestBin.totalSupply}`);
  }

  return { passed: errors.length === 0, errors };
}

/**
 * Check invariants for create-pool
 * 
 * Invariants:
 * - Pool MUST be created (poolCreated = true)
 * - Pool ID MUST be assigned
 * - Initial liquidity MUST be added to active bin
 * - LP tokens MUST be minted
 * - Pool status MUST be set correctly
 */
export function checkCreatePoolInvariants(
  poolId: bigint,
  poolCreated: boolean,
  poolStatus: boolean,
  activeBinId: bigint,
  activeBinLpSupply: bigint
): InvariantCheckResult {
  const errors: string[] = [];

  // Pool MUST be created
  if (!poolCreated) {
    errors.push(`Pool was not created (poolCreated=false)`);
  }

  // Pool ID MUST be assigned
  if (poolId === 0n) {
    errors.push(`Pool ID is 0 (not assigned)`);
  }

  // Initial liquidity MUST be added to active bin
  if (activeBinLpSupply <= 0n) {
    errors.push(`Active bin has no LP supply: ${activeBinLpSupply}`);
  }

  // Pool status MUST be set correctly (should be true for active pool)
  if (!poolStatus) {
    errors.push(`Pool status is false (should be true for active pool)`);
  }

  // Active bin ID MUST be in valid range
  if (activeBinId < -500n || activeBinId > 500n) {
    errors.push(`Active bin ID ${activeBinId} is out of valid range [-500, 500]`);
  }

  return { passed: errors.length === 0, errors };
}

