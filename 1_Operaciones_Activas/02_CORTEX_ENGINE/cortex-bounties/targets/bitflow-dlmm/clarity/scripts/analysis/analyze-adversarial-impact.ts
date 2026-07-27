#!/usr/bin/env node
/**
 * Script to analyze adversarial rounding impact from fuzz test results
 * 
 * This script:
 * 1. Analyzes rounding bias patterns (does rounding favor pool or users?)
 * 2. Calculates cumulative pool value leakage
 * 3. Identifies worst-case scenarios
 * 4. Assesses balance conservation violations
 * 5. Generates a comprehensive impact report
 */

import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

interface RoundingBiasData {
  txNumber: number;
  functionName: string;
  biasDirection: 'pool_favored' | 'user_favored' | 'neutral';
  biasAmount: string; // bigint as string
  biasPercent: number;
  poolValueBefore: string;
  poolValueAfter: string;
  poolValueChange: string;
  expectedPoolValueChange: string;
  poolValueLeakage: string;
}

interface BalanceConservationData {
  txNumber: number;
  functionName: string;
  xBalanceConserved: boolean;
  yBalanceConserved: boolean;
  xBalanceError?: string;
  yBalanceError?: string;
  poolValueConserved: boolean;
  poolValueError?: string;
  lpSupplyConserved?: boolean;
  lpSupplyError?: string;
}

interface AdversarialAnalysisData {
  roundingBias: RoundingBiasData[];
  balanceConservation: BalanceConservationData[];
  cumulativePoolValueLeakage: string;
  stats: {
    totalSwaps: number;
    userFavored: number;
    poolFavored: number;
    neutral: number;
    totalBias: string;
    totalLeakage: string;
    balanceConservationViolations: number;
  };
}

function analyzeBiasPatterns(biasData: RoundingBiasData[]) {
  console.log('=== Rounding Bias Analysis ===\n');
  
  const totalSwaps = biasData.length;
  const userFavored = biasData.filter(b => b.biasDirection === 'user_favored').length;
  const poolFavored = biasData.filter(b => b.biasDirection === 'pool_favored').length;
  const neutral = biasData.filter(b => b.biasDirection === 'neutral').length;
  
  console.log(`Total swaps: ${totalSwaps}`);
  console.log(`  User favored: ${userFavored} (${((userFavored / totalSwaps) * 100).toFixed(1)}%)`);
  console.log(`  Pool favored: ${poolFavored} (${((poolFavored / totalSwaps) * 100).toFixed(1)}%)`);
  console.log(`  Neutral: ${neutral} (${((neutral / totalSwaps) * 100).toFixed(1)}%)\n`);
  
  // Calculate total bias
  const totalBias = biasData.reduce((sum, b) => sum + BigInt(b.biasAmount), 0n);
  const totalBiasPositive = biasData
    .filter(b => b.biasDirection === 'user_favored')
    .reduce((sum, b) => sum + BigInt(b.biasAmount), 0n);
  const totalBiasNegative = biasData
    .filter(b => b.biasDirection === 'pool_favored')
    .reduce((sum, b) => sum + BigInt(b.biasAmount), 0n);
  
  console.log(`Total bias: ${totalBias.toString()} tokens`);
  console.log(`  User benefit: ${totalBiasPositive.toString()} tokens`);
  console.log(`  Pool benefit: ${totalBiasNegative.toString()} tokens\n`);
  
  // Find worst cases
  const sortedByBias = [...biasData].sort((a, b) => {
    const aBias = BigInt(a.biasAmount);
    const bBias = BigInt(b.biasAmount);
    return aBias > bBias ? -1 : aBias < bBias ? 1 : 0;
  });
  
  console.log('Top 10 swaps favoring users (by bias amount):');
  sortedByBias
    .filter(b => b.biasDirection === 'user_favored')
    .slice(0, 10)
    .forEach((b, i) => {
      console.log(`  ${i + 1}. Tx ${b.txNumber} (${b.functionName}): +${b.biasAmount} tokens (${b.biasPercent.toFixed(6)}%)`);
    });
  
  console.log('\nTop 10 swaps favoring pool (by bias amount):');
  sortedByBias
    .filter(b => b.biasDirection === 'pool_favored')
    .slice(0, 10)
    .forEach((b, i) => {
      console.log(`  ${i + 1}. Tx ${b.txNumber} (${b.functionName}): ${b.biasAmount} tokens (${b.biasPercent.toFixed(6)}%)`);
    });
  
  return {
    totalSwaps,
    userFavored,
    poolFavored,
    neutral,
    totalBias: totalBias.toString(),
    totalBiasPositive: totalBiasPositive.toString(),
    totalBiasNegative: totalBiasNegative.toString(),
  };
}

function analyzePoolValueLeakage(biasData: RoundingBiasData[]) {
  console.log('\n=== Pool Value Leakage Analysis ===\n');
  
  const totalLeakage = biasData.reduce((sum, b) => sum + BigInt(b.poolValueLeakage), 0n);
  const positiveLeakage = biasData
    .filter(b => BigInt(b.poolValueLeakage) > 0n)
    .reduce((sum, b) => sum + BigInt(b.poolValueLeakage), 0n);
  const negativeLeakage = biasData
    .filter(b => BigInt(b.poolValueLeakage) < 0n)
    .reduce((sum, b) => sum + BigInt(b.poolValueLeakage), 0n);
  
  console.log(`Total cumulative leakage: ${totalLeakage.toString()} tokens`);
  console.log(`  Positive (pool gains): ${positiveLeakage.toString()} tokens`);
  console.log(`  Negative (pool loses): ${negativeLeakage.toString()} tokens\n`);
  
  // Find worst cases
  const sortedByLeakage = [...biasData].sort((a, b) => {
    const aLeak = BigInt(a.poolValueLeakage);
    const bLeak = BigInt(b.poolValueLeakage);
    return aLeak < bLeak ? -1 : aLeak > bLeak ? 1 : 0; // Sort negative first (worst for pool)
  });
  
  console.log('Top 10 worst pool value leaks (most negative):');
  sortedByLeakage.slice(0, 10).forEach((b, i) => {
    const leak = BigInt(b.poolValueLeakage);
    const leakPercent = BigInt(b.expectedPoolValueChange) > 0n
      ? (Number(leak) / Number(b.expectedPoolValueChange)) * 100
      : 0;
    console.log(`  ${i + 1}. Tx ${b.txNumber} (${b.functionName}): ${leak.toString()} tokens (${leakPercent.toFixed(2)}% of expected)`);
  });
  
  // Calculate average leakage per swap
  const avgLeakage = totalLeakage / BigInt(biasData.length);
  console.log(`\nAverage leakage per swap: ${avgLeakage.toString()} tokens`);
  
  return {
    totalLeakage: totalLeakage.toString(),
    positiveLeakage: positiveLeakage.toString(),
    negativeLeakage: negativeLeakage.toString(),
    avgLeakage: avgLeakage.toString(),
  };
}

function analyzeBalanceConservation(conservationData: BalanceConservationData[]) {
  console.log('\n=== Balance Conservation Analysis ===\n');
  
  const total = conservationData.length;
  const xViolations = conservationData.filter(c => !c.xBalanceConserved).length;
  const yViolations = conservationData.filter(c => !c.yBalanceConserved).length;
  const poolValueViolations = conservationData.filter(c => !c.poolValueConserved).length;
  const lpSupplyViolations = conservationData.filter(c => c.lpSupplyConserved === false).length;
  const anyViolations = conservationData.filter(c => !c.xBalanceConserved || !c.yBalanceConserved || !c.poolValueConserved || c.lpSupplyConserved === false).length;
  
  console.log(`Total swaps checked: ${total}`);
  console.log(`  X balance violations: ${xViolations} (${((xViolations / total) * 100).toFixed(1)}%)`);
  console.log(`  Y balance violations: ${yViolations} (${((yViolations / total) * 100).toFixed(1)}%)`);
  console.log(`  Pool value violations: ${poolValueViolations} (${((poolValueViolations / total) * 100).toFixed(1)}%)`);
  console.log(`  LP supply violations: ${lpSupplyViolations} (${((lpSupplyViolations / total) * 100).toFixed(1)}%)`);
  console.log(`  Any violations: ${anyViolations} (${((anyViolations / total) * 100).toFixed(1)}%)\n`);
  
  // Find worst violations
  const violations = conservationData.filter(c => !c.xBalanceConserved || !c.yBalanceConserved || !c.poolValueConserved);
  
  if (violations.length > 0) {
    console.log('Top 10 worst balance conservation violations:');
    violations
      .sort((a, b) => {
        const aError = BigInt(a.poolValueError || a.xBalanceError || a.yBalanceError || '0');
        const bError = BigInt(b.poolValueError || b.xBalanceError || b.yBalanceError || '0');
        return aError > bError ? -1 : aError < bError ? 1 : 0;
      })
      .slice(0, 10)
      .forEach((v, i) => {
        const errors = [];
        if (!v.xBalanceConserved && v.xBalanceError) errors.push(`X: ${v.xBalanceError}`);
        if (!v.yBalanceConserved && v.yBalanceError) errors.push(`Y: ${v.yBalanceError}`);
        if (!v.poolValueConserved && v.poolValueError) errors.push(`Pool: ${v.poolValueError}`);
        console.log(`  ${i + 1}. Tx ${v.txNumber} (${v.functionName}): ${errors.join(', ')}`);
      });
  }
  
  // Analyze LP supply violations
  if (lpSupplyViolations > 0) {
    console.log('⚠️  CRITICAL: LP supply violations detected!');
    const lpViolations = conservationData.filter(c => c.lpSupplyConserved === false);
    console.log(`\nLP Supply Violations (${lpViolations.length}):`);
    lpViolations.slice(0, 10).forEach((v, i) => {
      console.log(`  ${i + 1}. Tx ${v.txNumber} (${v.functionName}): LP supply changed by ${v.lpSupplyError || 'unknown'}`);
    });
  } else {
    console.log('✅ LP supply remains constant during all swaps (as expected)\n');
  }
  
  return {
    total,
    xViolations,
    yViolations,
    poolValueViolations,
    lpSupplyViolations,
    anyViolations,
  };
}

function generateReport(
  biasStats: any,
  leakageStats: any,
  conservationStats: any,
  outputFile: string
) {
  const report = {
    timestamp: new Date().toISOString(),
    summary: {
      bias: biasStats,
      leakage: leakageStats,
      conservation: conservationStats,
    },
    assessment: {
      isSystematicBias: biasStats.userFavored > biasStats.poolFavored * 2,
      isSignificantLeakage: BigInt(leakageStats.totalLeakage) < -1000000n,
      hasBalanceIssues: conservationStats.anyViolations > 0,
    },
  };
  
  fs.writeFileSync(outputFile, JSON.stringify(report, null, 2), 'utf-8');
  console.log(`\nDetailed report saved to: ${outputFile}`);
}

function main() {
  console.log('Adversarial Rounding Impact Analysis Script\n');
  console.log('='.repeat(60) + '\n');
  
  // Load adversarial analysis data
  const resultsDir = path.join(__dirname, '../logs/fuzz-test-results');
  if (!fs.existsSync(resultsDir)) {
    console.log('No results directory found. Run tests first.');
    return;
  }
  
  const adversarialFiles = fs.readdirSync(resultsDir)
    .filter(f => f.endsWith('.json') && f.includes('adversarial-analysis'))
    .sort()
    .reverse();
  
  if (adversarialFiles.length === 0) {
    console.log('No adversarial analysis files found. Run tests with adversarial analysis first.');
    return;
  }
  
  const latestFile = path.join(resultsDir, adversarialFiles[0]);
  console.log(`Loading: ${adversarialFiles[0]}\n`);
  
  const data: AdversarialAnalysisData = JSON.parse(fs.readFileSync(latestFile, 'utf-8'));
  
  if (data.roundingBias.length === 0) {
    console.log('No rounding bias data found in file.');
    return;
  }
  
  // Analyze
  const biasStats = analyzeBiasPatterns(data.roundingBias);
  const leakageStats = analyzePoolValueLeakage(data.roundingBias);
  const conservationStats = analyzeBalanceConservation(data.balanceConservation);
  
  // Generate report
  const reportFile = path.join(resultsDir, `adversarial-impact-report-${new Date().toISOString().replace(/[:.]/g, '-')}.json`);
  generateReport(biasStats, leakageStats, conservationStats, reportFile);
  
  // Future Swap Impact Analysis
  console.log('\n=== Future Swap Impact Analysis ===\n');
  console.log('State Propagation:');
  console.log('  - Each swap uses state from previous swaps (compounding)');
  console.log('  - Rounding differences in one swap affect subsequent swaps through bin balances');
  console.log('  - Pool value leakage accumulates over time');
  console.log(`  - Cumulative leakage after ${biasStats.totalSwaps} swaps: ${leakageStats.totalLeakage} tokens`);
  console.log(`  - Average leakage per swap: ${leakageStats.avgLeakage} tokens\n`);
  
  // Summary
  console.log('\n=== Summary ===\n');
  console.log(`Bias: ${biasStats.userFavored > biasStats.poolFavored ? 'Favors users' : biasStats.poolFavored > biasStats.userFavored ? 'Favors pool' : 'Neutral'}`);
  console.log(`Total leakage: ${leakageStats.totalLeakage} tokens`);
  console.log(`Balance violations: ${conservationStats.anyViolations} / ${conservationStats.total}`);
  console.log(`LP supply violations: ${conservationStats.lpSupplyViolations} / ${conservationStats.total}`);
  
  // Assessment
  console.log('\n=== Security Assessment ===\n');
  const isSystematicBias = biasStats.userFavored > biasStats.poolFavored * 2;
  const isSignificantLeakage = BigInt(leakageStats.totalLeakage) < -1000000n;
  const hasBalanceIssues = conservationStats.anyViolations > 0;
  const hasLpIssues = conservationStats.lpSupplyViolations > 0;
  
  console.log(`Systematic bias: ${isSystematicBias ? '⚠️  YES - Rounding systematically favors users' : '✅ NO - Bias is random/neutral'}`);
  console.log(`Significant leakage: ${isSignificantLeakage ? '⚠️  YES - Pool loses significant value' : '✅ NO - Leakage is acceptable'}`);
  console.log(`Balance issues: ${hasBalanceIssues ? '⚠️  YES - Balance conservation violations detected' : '✅ NO - Balances are conserved'}`);
  console.log(`LP supply issues: ${hasLpIssues ? '🚨 CRITICAL - LP supply changed during swaps!' : '✅ NO - LP supply remains constant'}`);
  
  console.log('\n=== Analysis Complete ===');
}

main();

