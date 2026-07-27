const { EventBus } = require('./event-bus');

class BrainRegion {
    /**
     * @param {string} regionName Identifier for this worker node
     */
    constructor(regionName) {
        this.regionName = regionName;
        this.bus = new EventBus();
        this.subscriptions = [];
    }

    async boot() {
        await this.bus.init();
        console.log(`[CEN-Cluster] BrainRegion <${this.regionName}> Online. Exergy optimized.`);
    }

    /**
     * Emits an event with the sourceRegion automatically appended
     */
    async emit(subject, payload) {
        return await this.bus.emit(subject, { ...payload, sourceRegion: this.regionName });
    }

    /**
     * Listens to a subject. Can provide a durableName for persistent state tracking across restarts.
     * @param {string} subject 
     * @param {Function} handler async (event, msg) => void
     * @param {string} [durableName] 
     */
    async listen(subject, handler, durableName = null) {
        const iter = await this.bus.subscribe(subject, async (event, msg) => {
            // C5-REAL logging for audit
            console.log(`[${this.regionName}] Received Event Hash: ${event.hash}`);
            await handler(event, msg);
        }, durableName);
        this.subscriptions.push(iter);
    }

    async shutdown() {
        console.log(`[CEN-Cluster] BrainRegion <${this.regionName}> Shutting down...`);
        for (const iter of this.subscriptions) {
             iter.stop();
        }
        await this.bus.close();
    }
}

module.exports = { BrainRegion };
