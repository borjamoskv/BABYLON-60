const { BrainRegion } = require('./brain-region');
const neo4j = require('neo4j-driver');

class MetacognitionEngine extends BrainRegion {
    constructor() {
        super('Metacognition');
        this.driver = null;
        this.isInMemory = true;
        this.sleepInterval = null;
    }

    async boot() {
        await super.boot();
        
        try {
            this.driver = neo4j.driver(
                process.env.NEO4J_URI || 'bolt://localhost:7687',
                neo4j.auth.basic(process.env.NEO4J_USER || 'neo4j', process.env.NEO4J_PASS || 'password')
            );
            await this.driver.verifyConnectivity();
            this.isInMemory = false;
            console.log('[Metacognition] Connected to Neo4j. Live graph audit enabled.');
        } catch (err) {
            console.log('[Metacognition] Neo4j offline. Falling back to simulated in-memory audit.');
            this.driver = null;
            this.isInMemory = true;
        }

        // Listen for internal system health requests
        await this.listen('cortex.system.audit', async () => {
            console.log('[Metacognition] Audit requested. Calculating system entropy...');
            await this.auditGraph();
        });

        // Trigger a 'Sleep/Freeze' cycle every 10 minutes (PoC uses 60s for visibility)
        const freezeMs = parseInt(process.env.FREEZE_MS, 10) || 60000;
        this.sleepInterval = setInterval(async () => {
            console.log('\n[Metacognition] Initiating Sleep Cycle (Memory Pruning)...');
            await this.emit('cortex.state.sleep', { phase: 'REM', actionable: true });
            await this.pruneNoise();
        }, freezeMs > 0 ? freezeMs : 60000);

        console.log('[Metacognition] Audit Loop & Sleep Cycles Active.');
    }

    async auditGraph() {
        if (!this.isInMemory && this.driver) {
            const session = this.driver.session();
            try {
                const result = await session.executeRead(tx => 
                    tx.run('MATCH (n:MemoryNode) RETURN count(n) AS total, avg(n.entropy) AS avgEntropy')
                );
                const total = result.records[0].get('total').toNumber();
                const avgEntropy = result.records[0].get('avgEntropy') || 0;
                console.log(`[Metacognition] Graph Audit -> Nodes: ${total} | Avg Entropy: ${avgEntropy}`);
                
                // If the graph is too chaotic, trigger a global alert
                if (avgEntropy > 0.8) {
                    await this.emit('cortex.entropy.critical', { avgEntropy, total });
                }
            } catch (err) {
                console.error('[Metacognition] Audit failed:', err);
            } finally {
                await session.close();
            }
        } else {
            console.log(`[Metacognition] Graph Audit (in-memory) -> Status: NOMINAL.`);
        }
    }

    async pruneNoise() {
        if (!this.isInMemory && this.driver) {
            const session = this.driver.session();
            try {
                // Delete high entropy nodes that haven't crystallized
                const result = await session.executeWrite(tx =>
                    tx.run(`
                        MATCH (n:MemoryNode)
                        WHERE n.entropy > 0.90 AND n.lastUpdated < (timestamp() - 60000)
                        DETACH DELETE n
                        RETURN count(n) as pruned
                    `)
                );
                const pruned = result.records[0].get('pruned').toNumber();
                console.log(`[Metacognition] Sleep Cycle Complete. Pruned ${pruned} high-entropy nodes.`);
            } catch (err) {
                console.error('[Metacognition] Pruning failed:', err);
            } finally {
                await session.close();
            }
        } else {
            console.log(`[Metacognition] Sleep Cycle Complete (in-memory).`);
        }
    }

    async shutdown() {
        if (this.sleepInterval) clearInterval(this.sleepInterval);
        if (this.driver) {
            await this.driver.close();
        }
        await super.shutdown();
    }
}

module.exports = { MetacognitionEngine };
