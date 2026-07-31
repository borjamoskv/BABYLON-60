// C5-REAL EXERGY CERTIFIED — SCORING ENGINE (Ω10 Auto-Resolved Criteria)
// Multi-criteria evaluation for integers 1–120,000

/**
 * Sieve of Eratosthenes — returns a boolean array where index i is true if i is prime
 */
export function sieveOfEratosthenes(max) {
  const sieve = new Uint8Array(max + 1);
  sieve.fill(1);
  sieve[0] = 0;
  sieve[1] = 0;
  for (let i = 2; i * i <= max; i++) {
    if (sieve[i]) {
      for (let j = i * i; j <= max; j += i) {
        sieve[j] = 0;
      }
    }
  }
  return sieve;
}

/**
 * Count divisors of n
 */
export function countDivisors(n) {
  if (n <= 0) return 0;
  let count = 0;
  const sqrt = Math.floor(Math.sqrt(n));
  for (let i = 1; i <= sqrt; i++) {
    if (n % i === 0) {
      count += (i === n / i) ? 1 : 2;
    }
  }
  return count;
}

/**
 * Popcount SWAR (SIMD Within A Register) — O(1) bitwise set-bits count
 */
export function popcount(n) {
  n = n - ((n >>> 1) & 0x55555555);
  n = (n & 0x33333333) + ((n >>> 2) & 0x33333333);
  return (((n + (n >>> 4)) & 0x0f0f0f0f) * 0x01010101) >>> 24;
}

/**
 * Bit length of n (Hardware Intrinsic Optimization O(1))
 * Compila a instrucción BSR / LZCNT a nivel de silicio
 */
export function bitLength(n) {
  if (n <= 0) return 1;
  return 32 - Math.clz32(n);
}

/**
 * Pre-compute Fibonacci numbers up to max
 */
export function fibonacciSetUpTo(max) {
  const fibs = new Set();
  let a = 0, b = 1;
  while (a <= max) {
    fibs.add(a);
    [a, b] = [b, a + b];
  }
  return fibs;
}

/**
 * Sorted Fibonacci array for proximity search
 */
export function fibonacciArrayUpTo(max) {
  const fibs = [];
  let a = 1, b = 1;
  while (a <= max * 2) {
    fibs.push(a);
    [a, b] = [b, a + b];
  }
  return fibs;
}

/**
 * Find distance to nearest Fibonacci number
 */
export function fibonacciDistance(n, fibArray) {
  let minDist = Infinity;
  for (const f of fibArray) {
    const d = Math.abs(n - f);
    if (d < minDist) minDist = d;
    if (f > n) break;
  }
  return minDist;
}

/**
 * Thermodynamic Collapse: Precompute perfect powers up to max O(1) lookup
 * Eradicates Math.pow and loops from the hot path.
 */
export function precomputePerfectPowers(max) {
  const pp = new Set();
  const maxBase = Math.floor(Math.sqrt(max));
  for (let b = 2; b <= maxBase; b++) {
    let power = b * b;
    while (power <= max) {
      pp.add(power);
      power *= b;
    }
  }
  return pp;
}

/**
 * Compute score for a single number given pre-computed data
 * @param {number} n - The number to score
 * @param {Uint8Array} primes - Sieve array
 * @param {number} maxDivisors - Max divisor count in range (for normalization)
 * @param {number[]} fibArray - Sorted Fibonacci numbers
 * @param {number} maxFibDist - Max Fibonacci distance in range (for normalization)
 * @param {Set} perfectPowersSet - Precomputed Hash Set of perfect powers
 * @param {object} config - Score configuration
 * @returns {number} Score 0-100
 */
export function computeScore(n, primes, maxDivisors, fibArray, maxFibDist, perfectPowersSet, config) {
  const criteria = config.criteria;
  let score = 0;
  let totalWeight = 0;

  // 1. Primality (binary: prime = 1.0, composite = 0.0)
  if (criteria.primality.enabled) {
    const primalityScore = primes[n] ? 1.0 : 0.0;
    score += primalityScore * criteria.primality.weight;
    totalWeight += criteria.primality.weight;
  }

  // 2. Divisor Richness (log-normalized)
  if (criteria.divisorRichness.enabled) {
    const divCount = countDivisors(n);
    const divScore = maxDivisors > 0 ? Math.log(1 + divCount) / Math.log(1 + maxDivisors) : 0;
    score += divScore * criteria.divisorRichness.weight;
    totalWeight += criteria.divisorRichness.weight;
  }

  // 3. Bit Density (popcount / bitLength)
  if (criteria.bitDensity.enabled) {
    const bits = bitLength(n);
    const density = bits > 0 ? popcount(n) / bits : 0;
    score += density * criteria.bitDensity.weight;
    totalWeight += criteria.bitDensity.weight;
  }

  // 4. Fibonacci Proximity (inverse distance, normalized)
  if (criteria.fibonacciProximity.enabled) {
    const dist = fibonacciDistance(n, fibArray);
    const fibScore = maxFibDist > 0 ? 1.0 - (dist / maxFibDist) : 0;
    score += Math.max(0, fibScore) * criteria.fibonacciProximity.weight;
    totalWeight += criteria.fibonacciProximity.weight;
  }

  // 5. Perfect Power (binary bonus via O(1) Hash Set)
  if (criteria.perfectPower.enabled) {
    const ppScore = perfectPowersSet.has(n) ? 1.0 : 0.0;
    score += ppScore * criteria.perfectPower.weight;
    totalWeight += criteria.perfectPower.weight;
  }

  // Normalize to 0-100 scale
  const normalized = totalWeight > 0 ? (score / totalWeight) * 100 : 0;
  return Math.round(normalized * 100) / 100;
}
