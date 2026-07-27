import * as fs from 'fs';
import * as path from 'path';

export type DirectionType = 'x-for-y' | 'y-for-x';
export type SwapType = "single-bin" | "multi-bin";

export type OperationType = 'swap-x-for-y' | 'swap-y-for-x' | 'add-liquidity' | 'withdraw-liquidity' | 'move-liquidity';
export const OPERATION_OPTIONS: OperationType[] = ['swap-x-for-y', 'swap-y-for-x', 'add-liquidity', 'withdraw-liquidity', 'move-liquidity'];

export const MIN_BIN_ID = -500n;
export const MAX_BIN_ID = 500n;
export const CENTER_BIN_ID = 500n; // absolute value
export const U128_MAX = 2n ** 128n - 1n;

export class SeededRandom {
  private seed: number;

  constructor(seed: number) {
    this.seed = seed;
  }

  next(): number {
    this.seed = (this.seed * 9301 + 49297) % 233280;
    return this.seed / 233280;
  }

  nextInt(min: number, max: number): number {
    return Math.floor(this.next() * (max - min + 1)) + min;
  }

  nextBigInt(min: bigint, max: bigint): bigint {
    const range = max - min;
    const randomValue = BigInt(Math.floor(this.next() * Number(range)));
    return min + randomValue;
  }

  nextBoolean(): boolean {
    return this.next() > 0.5;
  }

  choice<T>(array: T[]): T {
    return array[this.nextInt(0, array.length - 1)];
  }

  applyJitter(amount: bigint, jitterPercent: number): bigint {
    const minMultiplier = 1 - jitterPercent;
    const maxMultiplier = 1 + jitterPercent;
    const randomMultiplier = minMultiplier + (this.next() * (maxMultiplier - minMultiplier));
    const jitteredAmount = (amount * BigInt(Math.floor(randomMultiplier * 10000))) / 10000n;
    return jitteredAmount > 0n ? jitteredAmount : 1n;
  }
}

export interface Statistics {
  total: number;
  success: number;
  failed: number;
  [key: string]: any;
}

export class LogManager<TResult = any> {
  public testName: string;
  public logDir: string;
  public stats: Statistics;
  private logFile: string;
  private errorFile: string;
  private results: TResult[] = [];
  private ttyFd: number | null = null;
  private startTime: number;

  constructor(testName: string) {
    this.testName = testName;
    this.startTime = Date.now();
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    this.logDir = path.join(process.cwd(), 'logs', testName, timestamp);
    if (!fs.existsSync(this.logDir)) {
      fs.mkdirSync(this.logDir, { recursive: true });
    }

    this.logFile = path.join(this.logDir, 'main.log');
    this.errorFile = path.join(this.logDir, 'errors.log');
    
    this.stats = {
      total: 0,
      success: 0,
      failed: 0,
    };

    try {
      this.ttyFd = fs.openSync('/dev/tty', 'w');
    } catch (e) {
      this.ttyFd = null;
    }

    this.log(`=== Starting Fuzz Test: ${testName} ===`);
    this.log(`Log Directory: ${this.logDir}`);
  }

  log(message: string, echoToConsole: boolean = true): void {
    const timestamp = new Date().toISOString();
    const logLine = `[${timestamp}] ${message}\n`;
    
    fs.appendFileSync(this.logFile, logLine);
    
    if (echoToConsole) {
      console.log(message);
    }
  }

  logError(message: string, error?: any): void {
    const timestamp = new Date().toISOString();
    const errorStr = error ? (error.stack || JSON.stringify(error, null, 2)) : '';
    const logLine = `[${timestamp}] ERROR: ${message}\n${errorStr}\n`;
    
    fs.appendFileSync(this.errorFile, logLine);
    fs.appendFileSync(this.logFile, logLine);
    
    console.error(`ERROR: ${message}`);
  }

  recordResult(result: TResult): void {
    this.results.push(result);
  }

  incrementStat(key: keyof Statistics, amount: number = 1): void {
    if (typeof this.stats[key] === 'undefined') {
      this.stats[key] = 0;
    }
    
    this.stats.total += amount;
    this.stats[key] += amount;
  
    const _key = key.toString();
    if (_key.includes('failed') && _key !== "failed") {
        this.stats.failed += amount;
    } else if (_key.includes('success') && _key !== "success") {
        this.stats.success += amount;
    }
  }

  updateProgress(current: number, total: number, extraInfo: string = ''): void {
    if (this.ttyFd === null) return;

    const width = 30;
    const percentage = Math.min(100, Math.floor((current / total) * 100));
    const filled = Math.floor((width * percentage) / 100);
    const empty = width - filled;
    
    const bar = '█'.repeat(filled) + '░'.repeat(empty);
    const elapsed = ((Date.now() - this.startTime) / 1000).toFixed(1);
    
    const line = `\r[${bar}] ${percentage}% (${current}/${total}) | ${elapsed}s | ${extraInfo}`;
    
    try {
      fs.writeSync(this.ttyFd, `\x1b[2K${line}`);
    } catch (e) {
      // ignore
    }
  }

  finish(): void {
    if (this.ttyFd !== null) {
      try {
        fs.writeSync(this.ttyFd, '\n');
        fs.closeSync(this.ttyFd);
      } catch (e) {}
    }

    const duration = ((Date.now() - this.startTime) / 1000).toFixed(2);
    this.log(`\n=== Test Completed in ${duration}s ===`);
    this.log(`Total: ${this.stats.total}`);
    this.log(`Success: ${this.stats.success}`);
    this.log(`Failed: ${this.stats.failed}`);

    const resultsPath = path.join(this.logDir, 'results.json');
    fs.writeFileSync(resultsPath, JSON.stringify({
      stats: this.stats,
      results: this.results
    }, (_, v) => typeof v === 'bigint' ? v.toString() : v, 2));

    this.log(`Results saved to: ${resultsPath}`);
    
    this.generateMarkdownSummary();
  }

  private generateMarkdownSummary(): void {
    let md = `# ${this.testName} Report\n\n`;
    md += `**Date:** ${new Date().toISOString()}\n`;
    md += `**Duration:** ${((Date.now() - this.startTime) / 1000).toFixed(2)}s\n\n`;
    
    md += `## Statistics\n`;
    for (const [key, value] of Object.entries(this.stats)) {
      md += `- **${key}:** ${value}\n`;
    }

    md += `\n## Logs\n`;
    md += `- [Main Log](./main.log)\n`;
    md += `- [Error Log](./errors.log)\n`;
    md += `- [Raw Results](./results.json)\n`;

    fs.writeFileSync(path.join(this.logDir, 'SUMMARY.md'), md);
  }
}
