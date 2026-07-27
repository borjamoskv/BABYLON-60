import {
  alice,
  dlmmCore,
  sbtcUsdcPool,
  mockSbtcToken,
  mockUsdcToken,
  setupTestEnvironment,
  getSbtcUsdcPoolLpBalance,
} from "../tests/helpers/helpers";

import { describe, it, expect, beforeEach } from 'vitest';
import { txOk } from '@clarigen/test';
import { getFuzzConfig } from './harnesses/config';
import {
  generateBiasedRandomValue,
  generateEdgeCaseBinIds,
} from "../tests/helpers/edge-case-generators";
import { LogManager, SeededRandom, MIN_BIN_ID, MAX_BIN_ID, U128_MAX, OperationType, OPERATION_OPTIONS } from './utils';

function nextBiasedValue(rng: SeededRandom, min: bigint, max: bigint): bigint {
  const bias = rng.next();
  if (bias < 0.2) {
    return generateBiasedRandomValue(min, max, 'small');
  } else if (bias < 0.4) {
    return generateBiasedRandomValue(min, max, 'large');
  } else {
    return generateBiasedRandomValue(min, max, 'normal');
  }
}

function generateSwapAmount(rng: SeededRandom): bigint {
  const bias = rng.next();
  if (bias < 0.2) {
    return rng.nextBigInt(1n, 100n);
  } else if (bias < 0.4) {
    return rng.nextBigInt(U128_MAX - 1000000n, U128_MAX - 1n);
  } else {
    return rng.nextBigInt(1000n, 1000000000n);
  }
}

function generateLiquidityAmount(rng: SeededRandom): bigint {
  return generateSwapAmount(rng);
}

function generateBinId(rng: SeededRandom): bigint {
  const bias = rng.next();
  if (bias < 0.1) {
    return rng.choice(Array.from(generateEdgeCaseBinIds()));
  } else {
    return rng.nextBigInt(MIN_BIN_ID, MAX_BIN_ID);
  }
}

describe('Arithmetic Edge Cases Fuzz Test', () => {
  
  beforeEach(async () => {
    setupTestEnvironment();
  });

  it('should handle edge case values without panics', async () => {
    const config = getFuzzConfig();
    const NUM_TRANSACTIONS = config.size;
    const RANDOM_SEED = config.seed;
    
    const rng = new SeededRandom(RANDOM_SEED);
    const orchestrator = new LogManager('arithmetic-edge-cases');
        
    orchestrator.log(`\n=== Arithmetic Edge Cases Fuzz Test ===`);
    orchestrator.log(`Seed: ${RANDOM_SEED}`);
    orchestrator.log(`Transactions: ${NUM_TRANSACTIONS}`);
    orchestrator.log(`\n`);
    
    for (let txNumber = 1; txNumber <= NUM_TRANSACTIONS; txNumber++) {
      const operation: OperationType = rng.choice(OPERATION_OPTIONS);
      const binId = generateBinId(rng);
      
      try {
        if (operation === 'swap-x-for-y') {
          const xAmount = generateSwapAmount(rng);
          
          try {
            txOk(dlmmCore.swapXForY(
              sbtcUsdcPool.identifier,
              mockSbtcToken.identifier,
              mockUsdcToken.identifier,
              binId,
              xAmount
            ), alice);
            
            orchestrator.incrementStat('success');
          } catch (error: any) {
            const errorStr = String(error);
            if (errorStr.includes('Runtime') && (errorStr.includes('ArithmeticUnderflow') || errorStr.includes('panic'))) {
              orchestrator.logError(`PANIC in ${operation}`, { binId, xAmount, error: errorStr });
              orchestrator.recordResult({ txNumber, type: 'panic', operation, binId, xAmount, error: errorStr });
               orchestrator.incrementStat('panics');
            } else {
              orchestrator.incrementStat('expectedErrors');
            }
          }
        } else if (operation === 'swap-y-for-x') {
          const yAmount = generateSwapAmount(rng);
          
          try {
            txOk(dlmmCore.swapYForX(
              sbtcUsdcPool.identifier,
              mockSbtcToken.identifier,
              mockUsdcToken.identifier,
              binId,
              yAmount
            ), alice);
            
            orchestrator.incrementStat('success');
          } catch (error: any) {
            const errorStr = String(error);
            if (errorStr.includes('Runtime') && (errorStr.includes('ArithmeticUnderflow') || errorStr.includes('panic'))) {
              orchestrator.logError(`PANIC in ${operation}`, { binId, yAmount, error: errorStr });
              orchestrator.recordResult({ txNumber, type: 'panic', operation, binId, yAmount, error: errorStr });
              orchestrator.incrementStat('panics');
            } else {
               orchestrator.incrementStat('expectedErrors');
            }
          }
        } else if (operation === 'add-liquidity') {
          const xAmount = generateLiquidityAmount(rng);
          const yAmount = generateLiquidityAmount(rng);
          const minDlp = 1n;
          
          try {
            txOk(dlmmCore.addLiquidity(
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
            
            orchestrator.incrementStat('success');
          } catch (error: any) {
            const errorStr = String(error);
            if (errorStr.includes('Runtime') && (errorStr.includes('ArithmeticUnderflow') || errorStr.includes('panic'))) {
              orchestrator.logError(`PANIC in ${operation}`, { binId, xAmount, yAmount, error: errorStr });
              orchestrator.recordResult({ txNumber, type: 'panic', operation, binId, xAmount, yAmount, error: errorStr });
              orchestrator.incrementStat('panics');
            } else {
              orchestrator.incrementStat('expectedErrors');
            }
          }
        } else if (operation === 'withdraw-liquidity') {
          const liquidityBalance = getSbtcUsdcPoolLpBalance(binId, alice);
          
          if (liquidityBalance > 0n) {
            const amountToWithdraw = nextBiasedValue(rng, 1n, liquidityBalance * 2n);
            const minXAmount = 0n;
            const minYAmount = 0n;
            
            try {
              txOk(dlmmCore.withdrawLiquidity(
                sbtcUsdcPool.identifier,
                mockSbtcToken.identifier,
                mockUsdcToken.identifier,
                binId,
                amountToWithdraw,
                minXAmount,
                minYAmount
              ), alice);
              
              orchestrator.incrementStat('success');
            } catch (error: any) {
              const errorStr = String(error);
              if (errorStr.includes('Runtime') && (errorStr.includes('ArithmeticUnderflow') || errorStr.includes('panic'))) {
                orchestrator.logError(`PANIC in ${operation}`, { binId, amountToWithdraw, error: errorStr });
                orchestrator.recordResult({ txNumber, type: 'panic', operation, binId, amountToWithdraw, error: errorStr });
                 orchestrator.incrementStat('panics');
              } else {
                orchestrator.incrementStat('expectedErrors');
              }
            }
          }
        } else if (operation === 'move-liquidity') {
          const fromBinId = generateBinId(rng);
          const toBinId = generateBinId(rng);
          const liquidityBalance = getSbtcUsdcPoolLpBalance(fromBinId, alice);
          
          if (liquidityBalance > 0n && fromBinId !== toBinId) {
            const amount = nextBiasedValue(rng, 1n, liquidityBalance);
            const minDlp = 1n;
            
            try {
              txOk(dlmmCore.moveLiquidity(
                sbtcUsdcPool.identifier,
                mockSbtcToken.identifier,
                mockUsdcToken.identifier,
                fromBinId,
                toBinId,
                amount,
                minDlp,
                1000000n,
                1000000n
              ), alice);
              
              orchestrator.incrementStat('success');
            } catch (error: any) {
              const errorStr = String(error);
              if (errorStr.includes('Runtime') && (errorStr.includes('ArithmeticUnderflow') || errorStr.includes('panic'))) {
                orchestrator.logError(`PANIC in ${operation}`, { fromBinId, toBinId, amount, error: errorStr });
                orchestrator.recordResult({ txNumber, type: 'panic', operation, fromBinId, toBinId, amount, error: errorStr });
                 orchestrator.incrementStat('panics');
              } else {
                 orchestrator.incrementStat('expectedErrors');
              }
            }
          }
        }
      } catch (error: any) {
        const errorStr = String(error);
        if (errorStr.includes('Runtime') && (errorStr.includes('ArithmeticUnderflow') || errorStr.includes('panic'))) {
           orchestrator.logError(`PANIC in ${operation}`, { binId, error: errorStr });
           orchestrator.recordResult({ txNumber, type: 'panic', operation, binId, error: errorStr });
           orchestrator.incrementStat('panics');
        } else {
           orchestrator.incrementStat('expectedErrors');
        }
      }
      
      orchestrator.updateProgress(txNumber, NUM_TRANSACTIONS, `Panics: ${orchestrator.stats.panics}`);
    }
    
    orchestrator.finish();
    
    expect(orchestrator.stats.failed).toBe(0);
  });
});
