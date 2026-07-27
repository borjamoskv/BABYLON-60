#!/usr/bin/env node
/**
 * Script to analyze rounding differences in swap calculations
 * 
 * This script:
 * 1. Verifies rounding direction in contract formulas
 * 2. Analyzes rounding difference data to categorize by conditions
 * 3. Identifies patterns in when rounding differences are large vs small
 * 4. Generates a comprehensive report
 */

import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

interface RoundingDifference {
  txNumber: number;
  functionName: 'swap-x-for-y' | 'swap-y-for-x';
  binId: number;
  inputAmount: number;
  outputAmount: number;
  binPrice: number;
  swapFeeTotal: number;
  yBalanceBefore?: number;
  xBalanceBefore?: number;
  expectedInteger: number;
  expectedFloat: number;
  integerDiff: number;
  floatDiff: number;
  floatPercentDiff: number;
  activeBinId: number;
}

interface CategoryStats {
  count: number;
  meanFloatDiff: number;
  maxFloatDiff: number;
  meanFloatPercentDiff: number;
  maxFloatPercentDiff: number;
  meanIntegerDiff: number;
  maxIntegerDiff: number;
  zeroDiffCount: number;
  smallDiffCount: number; // < 0.1%
  mediumDiffCount: number; // 0.1% - 1%
  largeDiffCount: number; // > 1%
}

function categorizeInputAmount(amount: number): string {
  if (amount < 1000) return 'very-small';
  if (amount < 100000) return 'small';
  if (amount < 10000000) return 'medium';
  if (amount < 1000000000) return 'large';
  return 'very-large';
}

function categorizeBinPrice(price: number): string {
  if (price < 10000000) return 'low';
  if (price < 100000000) return 'medium';
  return 'high';
}

function categorizeFees(fees: number): string {
  if (fees === 0) return 'zero';
  if (fees < 1000) return 'low';
  if (fees < 3000) return 'medium';
  return 'high';
}

function categorizeBalance(balance: number): string {
  if (balance < 1000000) return 'low';
  if (balance < 100000000) return 'medium';
  return 'high';
}

function categorizeBinPosition(binId: number, activeBinId: number): string {
  if (binId === activeBinId) return 'active';
  if (binId < activeBinId) return 'below-active';
  return 'above-active';
}

function categorizeOutputAmount(amount: number): string {
  if (amount < 1000) return 'very-small';
  if (amount < 100000) return 'small';
  if (amount < 10000000) return 'medium';
  if (amount < 1000000000) return 'large';
  return 'very-large';
}

function calculateCategoryStats(differences: RoundingDifference[]): CategoryStats {
  if (differences.length === 0) {
    return {
      count: 0,
      meanFloatDiff: 0,
      maxFloatDiff: 0,
      meanFloatPercentDiff: 0,
      maxFloatPercentDiff: 0,
      meanIntegerDiff: 0,
      maxIntegerDiff: 0,
      zeroDiffCount: 0,
      smallDiffCount: 0,
      mediumDiffCount: 0,
      largeDiffCount: 0,
    };
  }

  const floatDiffs = differences.map(d => Math.abs(d.floatDiff));
  const floatPercentDiffs = differences.map(d => Math.abs(d.floatPercentDiff));
  const integerDiffs = differences.map(d => Math.abs(d.integerDiff));

  return {
    count: differences.length,
    meanFloatDiff: floatDiffs.reduce((a, b) => a + b, 0) / floatDiffs.length,
    maxFloatDiff: Math.max(...floatDiffs),
    meanFloatPercentDiff: floatPercentDiffs.reduce((a, b) => a + b, 0) / floatPercentDiffs.length,
    maxFloatPercentDiff: Math.max(...floatPercentDiffs),
    meanIntegerDiff: integerDiffs.reduce((a, b) => a + b, 0) / integerDiffs.length,
    maxIntegerDiff: Math.max(...integerDiffs),
    zeroDiffCount: differences.filter(d => Math.abs(d.floatDiff) === 0).length,
    smallDiffCount: differences.filter(d => Math.abs(d.floatPercentDiff) < 0.1).length,
    mediumDiffCount: differences.filter(d => Math.abs(d.floatPercentDiff) >= 0.1 && Math.abs(d.floatPercentDiff) < 1).length,
    largeDiffCount: differences.filter(d => Math.abs(d.floatPercentDiff) >= 1).length,
  };
}

function verifyRoundingDirection() {
  console.log('=== Rounding Direction Verification ===\n');
  
  const contractFile = path.join(__dirname, '../contracts/dlmm-core-v-1-1.clar');
  const contractCode = fs.readFileSync(contractFile, 'utf-8');
  
  // Check for ceiling operations: pattern (+ (* a b) (- scale 1)) / scale
  const ceilingPattern = /\(\+\s*\(\*\s*[^)]+\)\s*\(\-\s*[^)]+\s+u?1\)\)\s*\/\s*[^)]+/g;
  const ceilingMatches = contractCode.match(ceilingPattern);
  
  console.log('Ceiling operations found (rounds up):');
  if (ceilingMatches && ceilingMatches.length > 0) {
    console.log(`  Found ${ceilingMatches.length} ceiling operations`);
    // Show key ones
    const keyMatches = ceilingMatches.filter(m => 
      m.includes('max-x-amount') || m.includes('max-y-amount') || 
      m.includes('PRICE_SCALE_BPS') || m.includes('bin-price')
    );
    keyMatches.slice(0, 3).forEach((match, i) => {
      console.log(`  ${i + 1}. ${match.substring(0, 120)}...`);
    });
  } else {
    console.log('  None found');
  }
  
  // Check key formulas
  console.log('\n=== Key Swap Formulas ===');
  
  // swap-x-for-y: max-x-amount calculation (line 1260)
  const maxXMatch = contractCode.match(/max-x-amount.*?\([^)]+\)/s);
  if (maxXMatch) {
    const line = maxXMatch[0].substring(0, 150);
    console.log('max-x-amount (swap-x-for-y):');
    console.log(`  ${line}...`);
    if (line.includes('(+ (*') && line.includes('(-')) {
      console.log('  ✓ Uses CEILING rounding (rounds up)');
    } else {
      console.log('  ✗ Uses FLOOR rounding (rounds down)');
    }
  }
  
  // swap-y-for-x: max-y-amount calculation (line 1405)
  const maxYMatch = contractCode.match(/max-y-amount.*?\([^)]+\)/s);
  if (maxYMatch) {
    const line = maxYMatch[0].substring(0, 150);
    console.log('max-y-amount (swap-y-for-x):');
    console.log(`  ${line}...`);
    if (line.includes('(+ (*') && line.includes('(-')) {
      console.log('  ✓ Uses CEILING rounding (rounds up)');
    } else {
      console.log('  ✗ Uses FLOOR rounding (rounds down)');
    }
  }
  
  console.log('\n');
}

function analyzeRoundingDifferences(differences: RoundingDifference[]) {
  console.log('=== Rounding Differences Analysis ===\n');
  console.log(`Total swaps analyzed: ${differences.length}\n`);
  
  // Add categories to each difference
  const categorized = differences.map(d => ({
    ...d,
    inputAmountCategory: categorizeInputAmount(d.inputAmount),
    binPriceCategory: categorizeBinPrice(d.binPrice),
    feeCategory: categorizeFees(d.swapFeeTotal),
    balanceCategory: categorizeBalance(d.yBalanceBefore || d.xBalanceBefore || 0),
    binPositionCategory: categorizeBinPosition(d.binId, d.activeBinId),
    outputAmountCategory: categorizeOutputAmount(d.outputAmount),
  }));
  
  // Overall statistics
  const overallStats = calculateCategoryStats(differences);
  console.log('Overall Statistics:');
  console.log(`  Mean float diff: ${overallStats.meanFloatDiff.toFixed(2)} tokens`);
  console.log(`  Max float diff: ${overallStats.maxFloatDiff} tokens`);
  console.log(`  Mean float % diff: ${overallStats.meanFloatPercentDiff.toFixed(4)}%`);
  console.log(`  Max float % diff: ${overallStats.maxFloatPercentDiff.toFixed(4)}%`);
  console.log(`  Zero diff count: ${overallStats.zeroDiffCount} (${((overallStats.zeroDiffCount / overallStats.count) * 100).toFixed(1)}%)`);
  console.log(`  Small diff (<0.1%): ${overallStats.smallDiffCount} (${((overallStats.smallDiffCount / overallStats.count) * 100).toFixed(1)}%)`);
  console.log(`  Medium diff (0.1-1%): ${overallStats.mediumDiffCount} (${((overallStats.mediumDiffCount / overallStats.count) * 100).toFixed(1)}%)`);
  console.log(`  Large diff (>1%): ${overallStats.largeDiffCount} (${((overallStats.largeDiffCount / overallStats.count) * 100).toFixed(1)}%)`);
  console.log(`  Mean integer diff: ${overallStats.meanIntegerDiff.toFixed(2)} tokens`);
  console.log(`  Max integer diff: ${overallStats.maxIntegerDiff} tokens`);
  console.log(`  Integer diff = 0: ${differences.filter(d => d.integerDiff === 0).length} (${((differences.filter(d => d.integerDiff === 0).length / differences.length) * 100).toFixed(1)}%)\n`);
  
  // Statistics by category
  const categories = {
    functionName: ['swap-x-for-y', 'swap-y-for-x'],
    inputAmountCategory: ['very-small', 'small', 'medium', 'large', 'very-large'],
    binPriceCategory: ['low', 'medium', 'high'],
    feeCategory: ['zero', 'low', 'medium', 'high'],
    balanceCategory: ['low', 'medium', 'high'],
    binPositionCategory: ['active', 'below-active', 'above-active'],
    outputAmountCategory: ['very-small', 'small', 'medium', 'large', 'very-large'],
  };
  
  console.log('=== Statistics by Category ===\n');
  
  for (const [categoryName, categoryValues] of Object.entries(categories)) {
    console.log(`By ${categoryName}:`);
    for (const value of categoryValues) {
      const filtered = categorized.filter(d => (d as any)[categoryName] === value);
      if (filtered.length > 0) {
        const stats = calculateCategoryStats(filtered);
        console.log(`  ${value}:`);
        console.log(`    Count: ${stats.count}`);
        console.log(`    Mean float % diff: ${stats.meanFloatPercentDiff.toFixed(4)}%`);
        console.log(`    Max float % diff: ${stats.maxFloatPercentDiff.toFixed(4)}%`);
        console.log(`    Large diff (>1%): ${stats.largeDiffCount} (${((stats.largeDiffCount / stats.count) * 100).toFixed(1)}%)`);
        console.log(`    Integer diff = 0: ${filtered.filter(d => d.integerDiff === 0).length} (${((filtered.filter(d => d.integerDiff === 0).length / stats.count) * 100).toFixed(1)}%)`);
      }
    }
    console.log('');
  }
  
  // Find worst cases
  console.log('=== Worst Cases (Top 10 by Float % Diff) ===\n');
  const sortedByPercent = [...differences].sort((a, b) => 
    Math.abs(b.floatPercentDiff) - Math.abs(a.floatPercentDiff)
  );
  
  sortedByPercent.slice(0, 10).forEach((d, i) => {
    console.log(`${i + 1}. Tx ${d.txNumber} (${d.functionName}):`);
    console.log(`   Float diff: ${d.floatDiff} tokens (${d.floatPercentDiff.toFixed(4)}%)`);
    console.log(`   Integer diff: ${d.integerDiff} tokens`);
    console.log(`   Input: ${d.inputAmount}, Output: ${d.outputAmount}`);
    console.log(`   Bin: ${d.binId}, Price: ${d.binPrice}, Fees: ${d.swapFeeTotal}`);
    console.log('');
  });
  
  return categorized;
}

function generateReport(categorized: any[], outputFile: string) {
  const report = {
    summary: {
      totalSwaps: categorized.length,
      timestamp: new Date().toISOString(),
    },
    categorized,
  };
  
  fs.writeFileSync(outputFile, JSON.stringify(report, null, 2), 'utf-8');
  console.log(`\nDetailed report saved to: ${outputFile}`);
}

function main() {
  console.log('Rounding Difference Analysis Script\n');
  console.log('='.repeat(60) + '\n');
  
  // Step 1: Verify rounding direction
  verifyRoundingDirection();
  
  // Step 2: Load and analyze rounding differences
  const resultsDir = path.join(__dirname, '../logs/fuzz-test-results');
  if (!fs.existsSync(resultsDir)) {
    console.log('No results directory found. Run tests first.');
    return;
  }
  
  const roundingFiles = fs.readdirSync(resultsDir)
    .filter(f => f.endsWith('.json') && f.includes('rounding-differences'))
    .sort()
    .reverse();
  
  if (roundingFiles.length === 0) {
    console.log('No rounding differences files found. Run tests with enhanced logging first.');
    return;
  }
  
  const latestFile = path.join(resultsDir, roundingFiles[0]);
  console.log(`Loading: ${roundingFiles[0]}\n`);
  
  const differences: RoundingDifference[] = JSON.parse(fs.readFileSync(latestFile, 'utf-8'));
  
  if (differences.length === 0) {
    console.log('No rounding differences found in file.');
    return;
  }
  
  // Step 3: Analyze
  const categorized = analyzeRoundingDifferences(differences);
  
  // Step 4: Generate report
  const reportFile = path.join(resultsDir, `rounding-analysis-${new Date().toISOString().replace(/[:.]/g, '-')}.json`);
  generateReport(categorized, reportFile);
  
  console.log('\n=== Analysis Complete ===');
}

main();
