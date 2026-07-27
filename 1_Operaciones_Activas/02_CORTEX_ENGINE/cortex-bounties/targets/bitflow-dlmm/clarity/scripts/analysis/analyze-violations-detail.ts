#!/usr/bin/env node
/**
 * Detailed analysis of pool value violations
 */

import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

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

interface RoundingBiasData {
  txNumber: number;
  functionName: string;
  biasDirection: string;
  biasAmount: string;
  biasPercent: number;
  poolValueBefore: string;
  poolValueAfter: string;
  poolValueChange: string;
  expectedPoolValueChange: string;
  poolValueLeakage: string;
}

interface AdversarialAnalysisData {
  roundingBias: RoundingBiasData[];
  balanceConservation: BalanceConservationData[];
  cumulativePoolValueLeakage: string;
  stats: any;
}

function main() {
  const resultsDir = path.join(__dirname, '../logs/fuzz-test-results');
  const adversarialFiles = fs.readdirSync(resultsDir)
    .filter(f => f.endsWith('.json') && f.includes('adversarial-analysis'))
    .sort()
    .reverse();
  
  if (adversarialFiles.length === 0) {
    console.log('No adversarial analysis files found.');
    return;
  }
  
  const latestFile = path.join(resultsDir, adversarialFiles[0]);
  console.log(`Loading: ${adversarialFiles[0]}\n`);
  
  const data: AdversarialAnalysisData = JSON.parse(fs.readFileSync(latestFile, 'utf-8'));
  
  // Find all pool value violations
  const violations = data.balanceConservation.filter(c => !c.poolValueConserved);
  console.log(`=== Pool Value Violations Analysis ===\n`);
  console.log(`Total violations: ${violations.length}\n`);
  
  // Group by error amount
  const errorGroups = new Map<string, number>();
  violations.forEach(v => {
    const error = v.poolValueError || '0';
    errorGroups.set(error, (errorGroups.get(error) || 0) + 1);
  });
  
  console.log('Violations by error amount:');
  Array.from(errorGroups.entries())
    .sort((a, b) => parseInt(a[0]) - parseInt(b[0]))
    .forEach(([error, count]) => {
      console.log(`  ${error} tokens: ${count} violations`);
    });
  
  // Group by function
  const byFunction = new Map<string, number>();
  violations.forEach(v => {
    byFunction.set(v.functionName, (byFunction.get(v.functionName) || 0) + 1);
  });
  
  console.log('\nViolations by function:');
  Array.from(byFunction.entries()).forEach(([fn, count]) => {
    console.log(`  ${fn}: ${count} violations`);
  });
  
  // Get corresponding bias data for violations
  console.log('\n=== Violation Details (First 20) ===\n');
  violations.slice(0, 20).forEach(v => {
    const bias = data.roundingBias.find(b => b.txNumber === v.txNumber);
    if (bias) {
      const expectedFees = BigInt(bias.expectedPoolValueChange);
      const tolerance = expectedFees > 0n ? expectedFees / 1000n : 0n; // 0.1% tolerance
      const error = BigInt(v.poolValueError || '0');
      const withinTolerance = error <= tolerance;
      
      console.log(`Tx ${v.txNumber} (${v.functionName}):`);
      console.log(`  Pool value error: ${v.poolValueError} tokens`);
      console.log(`  Expected fees: ${bias.expectedPoolValueChange} tokens`);
      console.log(`  Tolerance (0.1%): ${tolerance.toString()} tokens`);
      console.log(`  Within tolerance: ${withinTolerance ? '✅ YES' : '❌ NO'}`);
      console.log(`  Bias: ${bias.biasAmount} tokens (${bias.biasDirection})`);
      console.log(`  Pool value leakage: ${bias.poolValueLeakage} tokens`);
      console.log('');
    }
  });
  
  // Check if all violations are within tolerance
  let withinToleranceCount = 0;
  violations.forEach(v => {
    const bias = data.roundingBias.find(b => b.txNumber === v.txNumber);
    if (bias) {
      const expectedFees = BigInt(bias.expectedPoolValueChange);
      const tolerance = expectedFees > 0n ? expectedFees / 1000n : 0n;
      const error = BigInt(v.poolValueError || '0');
      if (error <= tolerance) {
        withinToleranceCount++;
      }
    }
  });
  
  console.log(`\n=== Summary ===\n`);
  console.log(`Total violations: ${violations.length}`);
  console.log(`Within tolerance (0.1%): ${withinToleranceCount} (${((withinToleranceCount / violations.length) * 100).toFixed(1)}%)`);
  console.log(`Outside tolerance: ${violations.length - withinToleranceCount} (${(((violations.length - withinToleranceCount) / violations.length) * 100).toFixed(1)}%)`);
}

main();

