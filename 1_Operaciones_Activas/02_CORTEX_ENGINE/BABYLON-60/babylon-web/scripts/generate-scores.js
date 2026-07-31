#!/usr/bin/env node
// C5-REAL EXERGY CERTIFIED — MASSIVE SCORE GENERATOR (1–120,000)
// Usage: node scripts/generate-scores.js [--dry-run]

import { readFileSync, writeFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

import {
  sieveOfEratosthenes,
  countDivisors,
  fibonacciArrayUpTo,
  fibonacciDistance,
  precomputePerfectPowers,
  computeScore
} from '../src/scoreEngine.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const isDryRun = process.argv.includes('--dry-run');

console.log('==========================================');
console.log('■ C5-REAL SCORE GENERATOR (1–120,000)');
console.log('==========================================');

// 1. Load config
const configPath = join(__dirname, '..', 'scoreConfig.json');
const config = JSON.parse(readFileSync(configPath, 'utf-8'));
const { min, max } = config.range;

console.log(`➜ Range: ${min}–${max}`);
console.log(`➜ Scale: ${config.scale.min}–${config.scale.max}`);
console.log(`➜ Dry Run: ${isDryRun}`);

// 2. Pre-compute sieve
console.log('➜ [1/5] Computing Sieve of Eratosthenes...');
const primes = sieveOfEratosthenes(max);
let primeCount = 0;
for (let i = min; i <= max; i++) if (primes[i]) primeCount++;
console.log(`  ✔ ${primeCount} primes found in range.`);

// 3. Pre-compute max divisors (sample for normalization)
console.log('➜ [2/5] Computing divisor normalization ceiling...');
let maxDivisors = 0;
for (let i = min; i <= max; i++) {
  const d = countDivisors(i);
  if (d > maxDivisors) maxDivisors = d;
}
console.log(`  ✔ Max divisors in range: ${maxDivisors}`);

// 4. Pre-compute Fibonacci array
console.log('➜ [3/5] Building Fibonacci proximity index...');
const fibArray = fibonacciArrayUpTo(max);
let maxFibDist = 0;
for (let i = min; i <= max; i++) {
  const d = fibonacciDistance(i, fibArray);
  if (d > maxFibDist) maxFibDist = d;
}
console.log(`  ✔ ${fibArray.length} Fibonacci numbers indexed. Max distance: ${maxFibDist}`);

// 4.5 Pre-compute perfect powers
console.log('➜ [3.5/5] Building perfect powers index...');
const perfectPowersSet = precomputePerfectPowers(max);
console.log(`  ✔ ${perfectPowersSet.size} perfect powers indexed.`);

// 5. Generate all scores
console.log('➜ [4/5] Generating scores...');
const t0 = performance.now();

const scores = new Float32Array(max - min + 1);
for (let i = min; i <= max; i++) {
  scores[i - min] = computeScore(i, primes, maxDivisors, fibArray, maxFibDist, perfectPowersSet, config);
}

const t1 = performance.now();
const elapsed = ((t1 - t0) / 1000).toFixed(3);
console.log(`  ✔ ${max - min + 1} scores generated in ${elapsed}s`);

// 6. Compute distribution stats
let minScore = 100, maxScore = 0, sumScore = 0;
const histogram = new Uint32Array(10); // 10 buckets: 0-10, 10-20, ..., 90-100
for (let i = 0; i < scores.length; i++) {
  const s = scores[i];
  if (s < minScore) minScore = s;
  if (s > maxScore) maxScore = s;
  sumScore += s;
  const bucket = Math.min(9, Math.floor(s / 10));
  histogram[bucket]++;
}
const avgScore = (sumScore / scores.length).toFixed(2);

console.log(`  ■ Distribution: min=${minScore.toFixed(2)} avg=${avgScore} max=${maxScore.toFixed(2)}`);
console.log('  ■ Histogram (0-100 in 10 buckets):');
for (let b = 0; b < 10; b++) {
  const lo = b * 10;
  const hi = lo + 10;
  const bar = '█'.repeat(Math.ceil(histogram[b] / (max / 100)));
  console.log(`    [${String(lo).padStart(2, '0')}-${String(hi).padStart(3, '0')}] ${String(histogram[b]).padStart(6)} ${bar}`);
}

if (isDryRun) {
  console.log('➜ [5/5] DRY RUN — skipping file write.');
  console.log(`  Estimated JSON size: ~${((max - min + 1) * 12 / 1024 / 1024).toFixed(2)} MiB`);
} else {
  // 7. Write JSON output
  console.log('➜ [5/5] Writing public/scores.json...');
  const output = {
    metadata: {
      range: config.range,
      scale: config.scale,
      criteria: Object.keys(config.criteria).filter(k => config.criteria[k].enabled),
      generatedAt: new Date().toISOString(),
      totalScores: scores.length,
      stats: { min: minScore, max: maxScore, avg: parseFloat(avgScore) },
      histogram: Array.from(histogram)
    },
    scores: {}
  };

  for (let i = 0; i < scores.length; i++) {
    output.scores[i + min] = scores[i];
  }

  const outputPath = join(__dirname, '..', 'public', 'scores.json');
  writeFileSync(outputPath, JSON.stringify(output));
  const fileSizeKB = (Buffer.byteLength(JSON.stringify(output)) / 1024).toFixed(1);
  console.log(`  ✔ Written to ${outputPath} (${fileSizeKB} KiB)`);
}

console.log('==========================================');
console.log('■ GENERATION COMPLETE (Zero Anergy)');
console.log('==========================================');
