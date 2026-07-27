require('dotenv').config();
const neo4j = require('neo4j-driver');

async function initializeGraph() {
    const driver = neo4j.driver(
        process.env.NEO4J_URI || 'bolt://localhost:7687',
        neo4j.auth.basic(process.env.NEO4J_USER || 'neo4j', process.env.NEO4J_PASS || 'password')
    );
    const session = driver.session();

    try {
        console.log('[Neo4j Init] Bootstrapping constraints and indexes...');
        
        const constraints = [
            'CREATE CONSTRAINT memory_node_id IF NOT EXISTS FOR (m:MemoryNode) REQUIRE m.id IS UNIQUE',
            'CREATE CONSTRAINT brain_region_name IF NOT EXISTS FOR (r:BrainRegion) REQUIRE r.name IS UNIQUE',
            'CREATE INDEX memory_entropy IF NOT EXISTS FOR (m:MemoryNode) ON (m.entropy)'
        ];

        for (const query of constraints) {
            await session.executeWrite(tx => tx.run(query));
            console.log(`[Neo4j Init] Executed: ${query.split('IF NOT EXISTS')[0].trim()}`);
        }

        console.log('[Neo4j Init] Graph Schema Bootstrapped Successfully. Ready for Autopoiesis.');
    } catch (err) {
        console.error('[Neo4j Init] Failed to initialize graph:', err);
        process.exit(1);
    } finally {
        await session.close();
        await driver.close();
    }
}

initializeGraph();
