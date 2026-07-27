const { parentPort, workerData } = require('worker_threads');
const { BrainRegion } = require('./brain-region');

async function runCenturia() {
    const { regionName, specialistsCount } = workerData;
    const region = new BrainRegion(regionName);
    
    await region.boot();
    
    // Announce readiness to the main orchestrator
    parentPort.postMessage({ type: 'READY', regionName });

    // Listen for the ignition command
    parentPort.on('message', async (msg) => {
        if (msg.type === 'IGNITE') {
            console.log(`[${regionName}] IGNITE received. Emitting ${specialistsCount} events...`);
            try {
                const promises = [];
                for (let j = 1; j <= specialistsCount; j++) {
                    const entropyVal = 0.85 + (Math.random() * 0.15); // E >= 0.85
                    const emitTask = region.emit('cortex.entropy.high', {
                        entropy: entropyVal,
                        specialistId: `${regionName}-Spec-${j}`,
                        content: { 
                            directive: 'STRUCTURAL_MUTATION', 
                            vector: [Math.random(), Math.random()] 
                        }
                    });
                    promises.push(emitTask);
                }
                
                // Wait for all emissions to finish
                await Promise.all(promises);
                console.log(`[${regionName}] All emissions complete. Posting DONE.`);
                parentPort.postMessage({ type: 'DONE', regionName, emitted: specialistsCount });
            } catch (err) {
                console.error(`[${regionName}] Error during execution:`, err);
                parentPort.postMessage({ type: 'ERROR', regionName, error: err.message });
            }
        }

        if (msg.type === 'SHUTDOWN') {
            await region.shutdown();
            process.exit(0);
        }
    });
}

runCenturia().catch(err => {
    parentPort.postMessage({ type: 'ERROR', regionName: workerData.regionName, error: err.message });
    process.exit(1);
});
