import { project, accounts } from './clarigen-types';
import {
  cvToValue,
  projectErrors,
  projectFactory,
  CoreNodeEventType
} from '@clarigen/core';
import { rovOk, txOk, filterEvents } from '@clarigen/test';

export const contracts = projectFactory(project, "simnet");

export const deployer = accounts.deployer.address;
export const alice = accounts.wallet_1.address;
export const bob = accounts.wallet_2.address;
export const charlie = accounts.wallet_3.address;

export const dlmmCore = contracts.dlmmCoreV11;
export const dlmmCoreMultiHelper = contracts.dlmmCoreMultiHelperV11;
export const dlmmSwapRouter = contracts.dlmmSwapRouterV11;
export const dlmmLiquidityRouter = contracts.dlmmLiquidityRouterV11;
export const sbtcUsdcPool = contracts.dlmmPoolSbtcUsdcV11;
export const mockSbtcToken = contracts.mockSbtcToken;
export const mockUsdcToken = contracts.mockUsdcToken;
export const mockPool = contracts.mockPool;
export const mockRandomToken = contracts.mockRandomToken;

const _errors = projectErrors(project);

export const errors = {
  dlmmCore: _errors.dlmmCoreV11,
  sbtcUsdcPool: _errors.dlmmPoolSbtcUsdcV11,
  dlmmSwapRouter: _errors.dlmmSwapRouterV11,
  dlmmLiquidityRouter: _errors.dlmmLiquidityRouterV11
};

export function getPrintEvents(response: any) {
  return filterEvents(
    response.events,
    CoreNodeEventType.ContractEvent
  );
}

export function getEventsDataByAction(action: string, response: any) {
  return getPrintEvents(response)
    .map(printEvent => cvToValue(printEvent.data.value))
    .filter(parsedEvent => parsedEvent.action === action);
}

export function getSwapXForYEventData(response: any) {
  return getEventsDataByAction("swap-x-for-y", response);
}

export function getSwapYForXEventData(response: any) {
  return getEventsDataByAction("swap-y-for-x", response);
}

export function getAddLiquidityEventData(response: any) {
  return getEventsDataByAction("add-liquidity", response);
}

export function getWithdrawLiquidityEventData(response: any) {
  return getEventsDataByAction("withdraw-liquidity", response);
}


// Common pool setup functionality
export function setupTokens() {
  // Step 1: Mint tokens to required parties
  txOk(mockSbtcToken.mint(1000000000n, deployer), deployer);  // 10 BTC to deployer
  txOk(mockUsdcToken.mint(500000000000n, deployer), deployer); // 500k USDC to deployer
  txOk(mockSbtcToken.mint(100000000n, alice), deployer);  // 1 BTC to alice
  txOk(mockUsdcToken.mint(50000000000n, alice), deployer); // 50k USDC to alice
  txOk(mockSbtcToken.mint(100000000n, bob), deployer);  // 1 BTC to bob
  txOk(mockUsdcToken.mint(50000000000n, bob), deployer); // 50k USDC to bob
}

export function createTestPool() {
  
  // Create pool with proper parameters
  txOk(dlmmCore.createPool(
    sbtcUsdcPool.identifier,           
    mockSbtcToken.identifier,          
    mockUsdcToken.identifier,          
    10000000n,    // 0.1 BTC in active bin
    5000000000n,  // 5000 USDC in active bin  
    1000n,        // burn amount
    1000n, 3000n, // x fees (0.1% protocol, 0.3% provider)
    1000n, 3000n, // y fees (0.1% protocol, 0.3% provider)
    25n,          // bin step (25 basis points)
    900n,         // variable fees cooldown
    false,        // freeze variable fees manager
    null,         // dynamic-config (optional)
    deployer,     // fee address
    "https://bitflow.finance/dlmm", // uri
    true          // status
  ), deployer);
}


export function addLiquidityToBins(
  binsToAddLiquidity: { bin: bigint; xAmount: bigint; yAmount: bigint; }[],
  poolContract: string = sbtcUsdcPool.identifier,
  tokenXContract: string = mockSbtcToken.identifier,
  tokenYContract: string = mockUsdcToken.identifier,
  caller: string = deployer) 
  {

  const minDlp = 1n; // Must be > 0
  const activeBinId = rovOk(sbtcUsdcPool.getActiveBinId());  
  const output: { bin: bigint; xAmount: bigint; yAmount: bigint; liquidity: bigint;}[] = [];

  for (const { bin, xAmount, yAmount } of binsToAddLiquidity) {
    let _xAmount: bigint, _yAmount: bigint;
    
    if (bin < activeBinId) {
      // Negative bins: only Y tokens (higher price bins)
      _xAmount = 0n;
      _yAmount = yAmount;
    } else if (bin === activeBinId) {
      // Active bin: both X and Y tokens
      _xAmount = xAmount;
      _yAmount = yAmount;
    } else {
      // Positive bins: only X tokens (lower price bins)
      _xAmount = xAmount;
      _yAmount = 0n;
    }
    
    const liquidity = txOk(dlmmCore.addLiquidity(
      poolContract,
      tokenXContract,
      tokenYContract,
      bin,
      _xAmount,
      _yAmount,
      minDlp,
      1000000n, // max-x-liquidity-fee
      1000000n  // max-y-liquidity-fee
    ), caller);

    output.push({
      bin: bin,
      xAmount: _xAmount,
      yAmount: _yAmount,
      liquidity: cvToValue(liquidity.result)
    });
  }
  
  return output;
}

export function addLiquidityToBinsRelativeToActiveBin(positionData: { relativeBinId: bigint; xAmount: bigint; yAmount: bigint;}[]) {

  const activeBinId = rovOk(sbtcUsdcPool.getActiveBinId());  
  const binsToAddLiquidity: { bin: bigint; xAmount: bigint; yAmount: bigint; }[] = [];
  
  for (const { relativeBinId, xAmount, yAmount } of positionData) {
    binsToAddLiquidity.push({
      bin: activeBinId + relativeBinId,
      xAmount: xAmount,
      yAmount: yAmount
    });
  }
  return addLiquidityToBins(binsToAddLiquidity);
}

export function bulkAddLiquidityToBins(
  bins: bigint[],
  xAmountPerBin: bigint,
  yAmountPerBin: bigint,
  tokenXContract: string = mockSbtcToken.identifier,
  tokenYContract: string = mockUsdcToken.identifier,
  poolContract: string = sbtcUsdcPool.identifier,
  relativeToActiveBin: boolean = false,
  receiver: string = deployer
) {
  
  const binsToAddLiquidity: { bin: bigint; xAmount: bigint; yAmount: bigint; }[] = [];
  const activeBinId = rovOk(sbtcUsdcPool.getActiveBinId());

  for (const bin of bins) {
    const newEntry = {
      bin: bin,
      xAmount: xAmountPerBin,
      yAmount: yAmountPerBin
    };
    
    if (relativeToActiveBin) {
      newEntry.bin += activeBinId;
    }

    binsToAddLiquidity.push(newEntry);
  }

  return addLiquidityToBins(
    binsToAddLiquidity,
    poolContract,
    tokenXContract,
    tokenYContract,
    receiver
  );
}

export function generateBinFactors(numEntries: number = Number(dlmmCore.constants.NUM_OF_BINS), startValue: bigint = 1000000n): bigint[] {
  const CENTER_BIN_ID = 500; // NUM_OF_BINS / 2 = 1001 / 2 = 500
  const PRICE_SCALE_BPS = 100000000n;
  // Calculate starting value so that index CENTER_BIN_ID equals PRICE_SCALE_BPS
  // If we want factors[i] = baseValue + i, and factors[CENTER_BIN_ID] = PRICE_SCALE_BPS
  // Then: baseValue + CENTER_BIN_ID = PRICE_SCALE_BPS
  // So: baseValue = PRICE_SCALE_BPS - CENTER_BIN_ID
  const baseValue = PRICE_SCALE_BPS - BigInt(CENTER_BIN_ID);
  const factors: bigint[] = [];
  
  for (let i = 0; i < numEntries; i++) {
    factors.push(baseValue + BigInt(i));
  }
  
  return factors;
}

export function setupTestEnvironment() {
  setupTokens();
  
  // Register bin-step 25 before creating pool
  const binStep = 25n;
  const factors = generateBinFactors();
  txOk(dlmmCore.addBinStep(binStep, factors), deployer);
  
  createTestPool();

  const xAmountPerBin = 5000000n;    // 0.05 BTC
  const yAmountPerBin = 2500000000n; // 2500 USDC
  
  const binsToAddLiquidity = [
    { bin: -5n, xAmount: 0n,            yAmount: yAmountPerBin },
    { bin: -3n, xAmount: 0n,            yAmount: yAmountPerBin },
    { bin: -2n, xAmount: 0n,            yAmount: yAmountPerBin },
    { bin: -1n, xAmount: 0n,            yAmount: yAmountPerBin },
    { bin:  0n, xAmount: xAmountPerBin, yAmount: yAmountPerBin },
    { bin:  1n, xAmount: xAmountPerBin, yAmount: 0n },
    { bin:  2n, xAmount: xAmountPerBin, yAmount: 0n },
    { bin:  3n, xAmount: xAmountPerBin, yAmount: 0n },
    { bin:  5n, xAmount: xAmountPerBin, yAmount: 0n },
  ];
  const totalX = binsToAddLiquidity.reduce((sum, bin) => sum + bin.xAmount, 0n);
  const totalY = binsToAddLiquidity.reduce((sum, bin) => sum + bin.yAmount, 0n);
  txOk(mockSbtcToken.mint(totalX, deployer), deployer);
  txOk(mockUsdcToken.mint(totalY, deployer), deployer);

  return addLiquidityToBins(
    binsToAddLiquidity,
    sbtcUsdcPool.identifier,
    mockSbtcToken.identifier,
    mockUsdcToken.identifier,
    deployer
  );
}

export function getSbtcUsdcPoolLpBalance(binId: bigint, address: string): bigint {
  const unsignedBin = rovOk(dlmmCore.getUnsignedBinId(binId));
  return rovOk(sbtcUsdcPool.getBalance(unsignedBin, address));
}
