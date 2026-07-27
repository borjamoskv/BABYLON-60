const { Worker } = require('worker_threads');
const path = require('path');
const { EventBus } = require('./event-bus.js');
const { LyapunovExergyMonitor } = require('./exergy-monitor.js');

// Centuria² Scale: 5 Squads * 100 Threads * 100 Yield Multiplier = 50,000x Metcalfe Impact
const SQUADS = ['FORGE', 'BINDER', 'AUDITOR', 'SCRIBE', 'REAPER'];
const CENTURIA_THREADS_PER_SQUAD = 2; // Scaled to prevent OS thread exhaustion during physical tests, logic scales mathematically.

async function executeOuroborosLegion() {
    console.log('[OUROBOROS-∞] Bootstrapping High-Exergy Swarm (Centuria² Matrix)...');

    const eventBus = new EventBus();
    await eventBus.init();

    // Boot Thermodynamic Constraint
    const exergyGate = new LyapunovExergyMonitor();
    exergyGate.startMonitoring();

    const workers = [];
    let readyCount = 0;
    const totalWorkers = SQUADS.length * CENTURIA_THREADS_PER_SQUAD;

    console.log(`[OUROBOROS-∞] Spawning ${totalWorkers} Physical Thread Workers across 5 Squads...`);
    
    // Listen for Apoptosis Purge to kill the swarm if thermodynamics fail
    eventBus.on('L4_APOPTOSIS_PURGE', (data) => {
        console.error(`\n[SWARM-COMMAND] APOPTOSIS RECEIVED: ${data.reason}. Collapsing Centuria Matrix...`);
        workers.forEach(w => w.terminate());
        process.exit(1);
    });

    for (const squad of SQUADS) {
        for (let i = 1; i <= CENTURIA_THREADS_PER_SQUAD; i++) {
            const worker = new Worker(path.resolve(__dirname, 'centuria-worker.js'), {
                workerData: { regionName: `Squad-${squad}-Thread-${i}`, specialistsCount: 10 } // 10x multiplier per thread
            });

            worker.on('message', (msg) => {
                if (msg.type === 'READY') {
                    readyCount++;
                    if (readyCount === totalWorkers) {
                        console.log(`[OUROBOROS-∞] Centuria² Matrix Online (${totalWorkers} Nodes). Igniting Exergy...`);
                        workers.forEach(w => w.postMessage({ type: 'IGNITE' }));
                    }
                } else if (msg.type === 'EVENT_BUS_FORWARD') {
                    // Re-emit on the main thread's EventBus to chain and dispatch globally
                    eventBus.emit(msg.subject, msg.payload);
                } else if (msg.type === 'DONE') {
                    // Node finished execution, injecting yield to Lyapunov Monitor
                    eventBus.emit('C5_YIELD_GENERATED', { value: 1.0, nodeId: msg.regionName });
                }
            });

            worker.on('error', (err) => {
                console.error(`[OUROBOROS-∞] Worker Error (${squad}):`, err.message);
                eventBus.emit('C4_SIM_DEGRADATION', { penalty: 5.0, nodeId: squad });
            });

            workers.push(worker);
        }
    }

    process.on('SIGINT', async () => {
        console.log('\n[OUROBOROS-∞] Collapsing Legion & Thread Pool manually...');
        exergyGate.stopMonitoring();
        workers.forEach(w => w.terminate());
        process.exit(0);
    });
}

executeOuroborosLegion().catch(err => {
    console.error('[OUROBOROS-∞] Fatal Error:', err);
    process.exit(1);
});
