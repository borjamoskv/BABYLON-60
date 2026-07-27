/**
 * Unit tests for multi-bin quote estimation helpers
 */

import { describe, it, expect } from 'vitest';
import {
  estimateBinsNeeded,
  getSampleBins,
  calculateMultiBinSwap,
  getAdaptiveMaxAttempts,
  BinWithPrice,
  PoolState,
} from '../../fuzz/harnesses/multi-bin-quote-estimation';
import { BinData } from '../../fuzz/harnesses/swap-calculations';

describe('estimateBinsNeeded', () => {
  it('should return 1 for trade that fits in active bin', () => {
    const activeBin: BinData = {
      reserve_x: 1000000n,
      reserve_y: 1000000n,
    };
    const amountIn = 500000n; // Less than 80% of min reserve (800k)
    
    const result = estimateBinsNeeded(amountIn, activeBin, []);
    expect(result).toBe(1);
  });

  it('should apply 3x safety margin for very large trades', () => {
    const activeBin: BinData = {
      reserve_x: 10000000n,
      reserve_y: 10000000n,
    };
    const sampleBins: BinData[] = [
      { reserve_x: 1000000n, reserve_y: 1000000n },
      { reserve_x: 1000000n, reserve_y: 1000000n },
    ];
    const amountIn = 20000000n; // 20M tokens (above 10M threshold)
    
    const result = estimateBinsNeeded(amountIn, activeBin, sampleBins);
    // Should be significantly higher due to 3x safety margin
    expect(result).toBeGreaterThan(10);
  });

  it('should return max bins for extremely large trades', () => {
    const activeBin: BinData = {
      reserve_x: 1000000n,
      reserve_y: 1000000n,
    };
    const amountIn = 200000000n; // 200M tokens (above 100M threshold)
    
    const result = estimateBinsNeeded(amountIn, activeBin, []);
    expect(result).toBe(1000); // MAX_BINS_ESTIMATION
  });

  it('should fallback to 1 if no sample bins available', () => {
    const activeBin: BinData = {
      reserve_x: 1000000n,
      reserve_y: 1000000n,
    };
    const amountIn = 2000000n; // Exceeds active bin capacity
    
    const result = estimateBinsNeeded(amountIn, activeBin, []);
    expect(result).toBe(1); // Fallback
  });
});

describe('getSampleBins', () => {
  it('should return sample bins around active bin', () => {
    const poolState: PoolState = {
      activeBinId: 0n,
      binBalances: new Map([
        [-2n, { xBalance: 1000n, yBalance: 1000n }],
        [-1n, { xBalance: 2000n, yBalance: 2000n }],
        [0n, { xBalance: 3000n, yBalance: 3000n }], // Active bin
        [1n, { xBalance: 4000n, yBalance: 4000n }],
        [2n, { xBalance: 5000n, yBalance: 5000n }],
      ]),
    };
    
    const result = getSampleBins(poolState, 0n, 2);
    expect(result.length).toBe(4); // Should get 4 bins (skip active)
    expect(result[0].reserve_x).toBe(1000n); // -2
    expect(result[1].reserve_x).toBe(2000n); // -1
    expect(result[2].reserve_x).toBe(4000n); // 1
    expect(result[3].reserve_x).toBe(5000n); // 2
  });

  it('should skip bins with zero liquidity', () => {
    const poolState: PoolState = {
      activeBinId: 0n,
      binBalances: new Map([
        [-1n, { xBalance: 0n, yBalance: 0n }], // Empty
        [0n, { xBalance: 3000n, yBalance: 3000n }],
        [1n, { xBalance: 4000n, yBalance: 4000n }],
      ]),
    };
    
    const result = getSampleBins(poolState, 0n, 2);
    expect(result.length).toBe(1); // Only bin 1
    expect(result[0].reserve_x).toBe(4000n);
  });
});

describe('calculateMultiBinSwap', () => {
  it('should calculate 2-bin swap correctly', () => {
    const bins: BinWithPrice[] = [
      {
        binId: 0n,
        price: 100000000n, // 1.0
        reserves: { reserve_x: 1000000n, reserve_y: 1000000n },
      },
      {
        binId: -1n,
        price: 99000000n, // 0.99
        reserves: { reserve_x: 1000000n, reserve_y: 1000000n },
      },
    ];
    
    const amountIn = 1500000n;
    const feeRateBPS = 30n; // 0.3%
    const swapForY = true; // X→Y
    
    const result = calculateMultiBinSwap(bins, amountIn, feeRateBPS, swapForY);
    
    expect(result.totalOut).toBeGreaterThan(0n);
    expect(result.totalFees).toBeGreaterThan(0n);
    expect(result.executionPath.length).toBeGreaterThan(0);
    expect(result.executionPath[0].binId).toBe(0n); // First bin should be active
  });

  it('should stop when trade is complete', () => {
    const bins: BinWithPrice[] = [
      {
        binId: 0n,
        price: 100000000n,
        reserves: { reserve_x: 1000000n, reserve_y: 1000000n },
      },
      {
        binId: -1n,
        price: 99000000n,
        reserves: { reserve_x: 1000000n, reserve_y: 1000000n },
      },
    ];
    
    const amountIn = 500000n; // Small amount that fits in first bin
    const feeRateBPS = 30n;
    const swapForY = true;
    
    const result = calculateMultiBinSwap(bins, amountIn, feeRateBPS, swapForY);
    
    // Should only use first bin
    expect(result.executionPath.length).toBe(1);
    expect(result.executionPath[0].binId).toBe(0n);
  });

  it('should handle empty bins correctly', () => {
    const bins: BinWithPrice[] = [
      {
        binId: 0n,
        price: 100000000n,
        reserves: { reserve_x: 0n, reserve_y: 0n }, // Empty
      },
      {
        binId: -1n,
        price: 99000000n,
        reserves: { reserve_x: 1000000n, reserve_y: 1000000n },
      },
    ];
    
    const amountIn = 500000n;
    const feeRateBPS = 30n;
    const swapForY = true;
    
    const result = calculateMultiBinSwap(bins, amountIn, feeRateBPS, swapForY);
    
    // Should skip empty bin and use second bin
    expect(result.executionPath.length).toBe(1);
    expect(result.executionPath[0].binId).toBe(-1n);
  });
});

describe('getAdaptiveMaxAttempts', () => {
  it('should return 3', () => {
    const result = getAdaptiveMaxAttempts();
    expect(result).toBe(3);
  });
});

