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
 * Popcount — number of set bits in binary representation
 */
export function popcount(n) {
  let count = 0;
  let v = n;
  while (v) {
    count += v & 1;
    v >>>= 1;
  }
  return count;
}

/**
 * Bit length of n
 */
export function bitLength(n) {
  if (n <= 0) return 1;
  return Math.floor(Math.log2(n)) + 1;
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
 * Check if n is a perfect power (square, cube, etc.)
 */
export function isPerfectPower(n) {
  if (n <= 1) return false;
  for (let exp = 2; exp <= Math.log2(n); exp++) {
    const root = Math.round(Math.pow(n, 1 / exp));
    // Check root and neighbors due to floating point
    for (const candidate of [root - 1, root, root + 1]) {
      if (candidate >= 2 && Math.pow(candidate, exp) === n) {
        return true;
      }
    }
  }
  return false;
}

/**
 * Compute score for a single number given pre-computed data
 * @param {number} n - The number to score
 * @param {Uint8Array} primes - Sieve array
 * @param {number} maxDivisors - Max divisor count in range (for normalization)
 * @param {number[]} fibArray - Sorted Fibonacci numbers
 * @param {number} maxFibDist - Max Fibonacci distance in range (for normalization)
 * @param {object} config - Score configuration
 * @returns {number} Score 0-100
 */
export function computeScore(n, primes, maxDivisors, fibArray, maxFibDist, config) {
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

  // 5. Perfect Power (binary bonus)
  if (criteria.perfectPower.enabled) {
    const ppScore = isPerfectPower(n) ? 1.0 : 0.0;
    score += ppScore * criteria.perfectPower.weight;
    totalWeight += criteria.perfectPower.weight;
  }

  // Normalize to 0-100 scale
  const normalized = totalWeight > 0 ? (score / totalWeight) * 100 : 0;
  return Math.round(normalized * 100) / 100;
}
