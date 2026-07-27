/**
 * C5-REAL OMEGA STRESS TEST (JOINT SATURATION)
 * Ignites the Hardware SHA-256 Stress Test AND the Centuria² Swarm simultaneously.
 * Objective: Observe if the Lyapunov Exergy Gate triggers L4 Apoptosis when the 
 * Apple M3 Pro is choked of compute resources, demonstrating true thermodynamic limits.
 */

const { spawn } = require('child_process');
const path = require('path');

console.log(`\n=============================================================`);
console.log(`[OMEGA-TEST] INITIATING JOINT ARCHITECTURE STRESS TEST`);
console.log(`=============================================================\n`);

// 1. Ignite the Raw Hardware Saturation Probe
console.log(`[OMEGA-TEST] Phase 1: Igniting 11-Core SHA-256 Saturation...`);
const stressTest = spawn('node', [path.resolve(__dirname, 'stress-test.js')], { stdio: 'pipe' });

stressTest.stdout.on('data', (data) => {
    // Filter out some noise, keep results
    const str = data.toString();
    if (str.includes('MH/s') || str.includes('Yield')) {
        console.log(`\n[HARDWARE-SATURATION] ${str.trim()}`);
    }
});

// 2. Wait 1 second for CPU to choke, then ignite the Swarm Orchestrator
setTimeout(() => {
    console.log(`\n[OMEGA-TEST] Phase 2: CPU Starved. Igniting Centuria² Swarm Orchestrator...`);
    
    const legionSwarm = spawn('node', [path.resolve(__dirname, 'legion.js')], { stdio: 'pipe' });
    
    legionSwarm.stdout.on('data', (data) => {
        const out = data.toString().trim();
        if (out.includes('dV/dt') || out.includes('CRITICAL')) {
            console.log(`${out}`);
        }
    });

    legionSwarm.stderr.on('data', (data) => {
        console.error(`\x1b[31m${data.toString().trim()}\x1b[0m`); // Print errors in red
    });

    legionSwarm.on('exit', (code) => {
        console.log(`\n[OMEGA-TEST] Swarm Matrix collapsed with code: ${code}`);
    });

}, 1000);

// Ensure cleanup
process.on('SIGINT', () => {
    stressTest.kill();
    process.exit(0);
});
