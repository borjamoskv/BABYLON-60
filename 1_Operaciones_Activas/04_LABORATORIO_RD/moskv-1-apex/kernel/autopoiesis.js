const neo4j = require('neo4j-driver');
const { BrainRegion } = require('./brain-region');

class AutopoiesisEngine extends BrainRegion {
    constructor() {
        super('Autopoiesis');
        this.driver = null;
    }

    async boot() {
        await super.boot();
        
        try {
            this.driver = neo4j.driver(
                process.env.NEO4J_URI || 'bolt://localhost:7687',
                neo4j.auth.basic(process.env.NEO4J_USER || 'neo4j', process.env.NEO4J_PASS || 'password'),
                { maxConnectionPoolSize: 50, connectionAcquisitionTimeout: 20000 }
            );
            await this.driver.verifyConnectivity();
            console.log('[Autopoiesis] Neo4j Driver connected. Graph mutation active.');
            this.isInMemory = false;
        } catch (error) {
            console.log('[Autopoiesis] Using in-memory graph store fallback (Neo4j driver offline).');
            this.driver = null;
            this.isInMemory = true;
            this._nodes = {};
            this._relationships = [];
        }

        // Listen for high-entropy / exergy events that require topology mutation
        // We use a durable consumer so mutations aren't lost on restart
        await this.listen('cortex.entropy.high', async (event, msg) => {
            const payload = event.payload;
            console.log(`[Autopoiesis] High Exergy Event Detected [Seq: ${msg.seq}]. Mutating Topology...`);
            await this.mutateGraph(payload, event.hash);
        }, 'autopoiesis_mutator');

        console.log('[Autopoiesis] Engine Ready.');
    }

    /**
     * Executes Cypher queries to structurally modify the graph based on exergy payload
     */
    async mutateGraph(payload, eventHash) {
        if (!this.isInMemory && this.driver) {
            const session = this.driver.session();
            try {
                // C5-REAL Structural Invariant Creation
                const cypher = `
                    MERGE (r:BrainRegion {name: $sourceRegion})
                    MERGE (n:MemoryNode {id: $id}) 
                    SET n.entropy = $entropy, 
                        n.content = $content, 
                        n.lastUpdated = timestamp(),
                        n.spawnHash = $hash
                    MERGE (n)-[:SYNTHESIZED_BY]->(r)
                    RETURN n
                `;
                const params = { 
                    id: payload.nodeId || eventHash, 
                    entropy: payload.entropy || 1.0, 
                    content: typeof payload.content === 'object' ? JSON.stringify(payload.content) : (payload.content || 'Void'),
                    sourceRegion: payload.sourceRegion || 'Unknown',
                    hash: eventHash
                };

                const result = await session.executeWrite(tx => tx.run(cypher, params));
                console.log(`[Autopoiesis] Mutation Applied. Nodes affected: ${result.records.length}`);
            } catch (error) {
                console.error('[Autopoiesis] Graph Mutation Failed:', error);
                throw error; // Let the event bus handle NAK if needed
            } finally {
                await session.close();
            }
        } else {
            // In-memory fallback
            const id = payload.nodeId || eventHash;
            const sourceRegion = payload.sourceRegion || 'Unknown';
            const entropy = payload.entropy || 1.0;
            const content = typeof payload.content === 'object' ? JSON.stringify(payload.content) : (payload.content || 'Void');
            
            this._nodes[id] = {
                id,
                entropy,
                content,
                lastUpdated: Date.now(),
                spawnHash: eventHash,
                sourceRegion
            };
            this._relationships.push({ from: id, to: sourceRegion, type: 'SYNTHESIZED_BY' });
            console.log(`[Autopoiesis] Mutation Applied (in-memory). Total nodes: ${Object.keys(this._nodes).length}`);
        }
    }

    async shutdown() {
        console.log('[Autopoiesis] Initiating shutdown...');
        if (this.driver) {
            await this.driver.close();
        }
        await super.shutdown();
    }
}

module.exports = { AutopoiesisEngine };

// Direct execution support
if (require.main === module) {
    const engine = new AutopoiesisEngine();
    engine.boot().catch(console.error);

    process.on('SIGINT', async () => {
        await engine.shutdown();
        process.exit(0);
    });
}
