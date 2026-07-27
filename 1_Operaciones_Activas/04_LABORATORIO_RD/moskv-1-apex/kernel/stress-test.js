/**
 * C5-REAL HARDWARE STRESS TEST (EXERGY SATURATION PROBE)
 * Forces maximum thermodynamic load on the host CPU.
 * Utilizes OS-level thread pools to max out CPU cores with cryptographic hashing.
 */

const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
const os = require('os');
const crypto = require('crypto');

if (isMainThread) {
    const numCores = os.cpus().length;
    console.log(`[STRESS-TEST] Target OS: macOS | CPU Cores detected: ${numCores}`);
    console.log(`[STRESS-TEST] Igniting C5-REAL Exergy Saturation Probe...`);
    console.log(`[STRESS-TEST] Forcing 100% load across all ${numCores} logical cores via SHA-256 derivation.`);

    const workers = [];
    const startTime = Date.now();
    let totalHashes = 0;
    const testDurationMs = 5000; // 5-second burst to prevent true thermal throttling shutdown

    for (let i = 0; i < numCores; i++) {
        const worker = new Worker(__filename, { workerData: { id: i, duration: testDurationMs } });
        
        worker.on('message', (msg) => {
            if (msg.type === 'RESULT') {
                totalHashes += msg.hashes;
            }
        });

        worker.on('error', (err) => console.error(`[CORE-${i}] Failure:`, err));
        
        workers.push(worker);
    }

    setTimeout(() => {
        const elapsed = (Date.now() - startTime) / 1000;
        const hashRate = totalHashes / elapsed;
        console.log(`\n[STRESS-TEST] Probe Terminated.`);
        console.log(`[STRESS-TEST] Elapsed Time: ${elapsed.toFixed(2)}s`);
        console.log(`[STRESS-TEST] Total Computations (Yield): ${totalHashes.toLocaleString()}`);
        console.log(`[STRESS-TEST] Physical Hashrate: ${(hashRate / 1000000).toFixed(2)} MH/s`);
        
        const coreType = os.cpus()[0].model;
        console.log(`[STRESS-TEST] Hardware Signature: ${coreType}`);
        
        process.exit(0);
    }, testDurationMs + 500); // Wait slightly longer than the worker duration to collect results

} else {
    // Worker Thread Logic: Maximum Entropy Generation
    const end = Date.now() + workerData.duration;
    let localHashes = 0;
    let seed = crypto.randomBytes(32).toString('hex');

    while (Date.now() < end) {
        // Tight computational loop (no I/O blocking, pure CPU load)
        seed = crypto.createHash('sha256').update(seed).digest('hex');
        localHashes++;
    }

    parentPort.postMessage({ type: 'RESULT', hashes: localHashes });
}
