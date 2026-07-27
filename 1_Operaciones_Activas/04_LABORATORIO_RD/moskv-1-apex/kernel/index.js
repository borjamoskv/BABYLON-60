const { BrainRegion } = require('./brain-region');
const { AutopoiesisEngine } = require('./autopoiesis');
const { MetacognitionEngine } = require('./metacognition');

async function bootstrap() {
    console.log('[GENESIS-L5] Initializing Swarm Orchestrator...');

    // 1. Boot Autopoiesis Engine (Listens for graph mutations)
    const autopoiesis = new AutopoiesisEngine();
    await autopoiesis.boot();

    // 2. Boot Mock Brain Regions (Vision & Reasoning)
    const vision = new BrainRegion('Vision');
    await vision.boot();

    const reasoning = new BrainRegion('Reasoning');
    await reasoning.boot();

    // 3. Boot Metacognition Engine (Sleep Cycles & Pruning)
    const metacognition = new MetacognitionEngine();
    await metacognition.boot();

    // Wait for event bus to be fully ready
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Simulate high entropy event from Vision
    console.log('[GENESIS-L5] Simulating High-Entropy Event from Vision...');
    await vision.emit('cortex.entropy.high', {
        entropy: 0.95,
        content: { raw: "Unidentified anomalous object detected in sector 7G", coordinates: [12, 45] }
    });

    // Graceful Shutdown Handler
    process.on('SIGINT', async () => {
        console.log('\n[GENESIS-L5] SIGINT Received. Terminating Swarm gracefully...');
        await vision.shutdown();
        await reasoning.shutdown();
        await metacognition.shutdown();
        await autopoiesis.shutdown();
        process.exit(0);
    });
}

bootstrap().catch(err => {
    console.error('[GENESIS-L5] Fatal Swarm Error:', err);
    process.exit(1);
});
