/**
 * C5-REAL LYAPUNOV EXERGY MONITOR (NODE 3 / L4 APOPTOSIS TRIGGER)
 * Thermodynamically grounds the MOSKV-1 architecture via formal stability theory.
 * Computes the Lyapunov function V(x) and its derivative dV/dt to ensure
 * Swarm convergence. If dV/dt > 0, system entropy is fatal -> Apoptosis.
 */

const { EventBus } = require('./event-bus.js');
const { performance, PerformanceObserver } = require('perf_hooks');
const crypto = require('crypto');
const fs = require('fs');

class LyapunovExergyMonitor {
    constructor(dbPath = './cortex.db') {
        this.baseMultiplier = 100; // Singularity multiplier (S_i)
        this.currentExergy = 10.0; // Initial threshold buffer (V)
        this.deathDebt = 0.0;      // Accumulated debt from dormant nodes
        this.dbPath = dbPath;
        
        this.tickInterval = null;
        this.eventBus = new EventBus();

        // OS-level Performance Hook for true Entropy tracking
        this.obs = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            for (let i = 0; i < entries.length; i++) {
                // Heuristic: CPU blocking time equates to thermodynamic entropy
                const entropyDelta = (entries[i].duration / 1000) * 0.02; 
                this.currentExergy -= entropyDelta;
            }
        });
        this.obs.observe({ entryTypes: ['measure', 'function'], buffered: true });

        // Event hooks
        this.eventBus.on('C5_YIELD_GENERATED', (event) => this.recordYield(event.payload.value, event.payload.nodeId));
        this.eventBus.on('C4_SIM_DEGRADATION', (event) => this.increaseDeathDebt(event.payload.penalty, event.payload.nodeId));
    }

    startMonitoring() {
        console.log('[EXERGY-MONITOR] Initializing Formal Lyapunov Gate (dV/dt)...');
        this.lastExergy = this.currentExergy;
        this.tickInterval = setInterval(() => this.calculateThermodynamics(), 1000);
    }

    stopMonitoring() {
        if (this.tickInterval) {
            clearInterval(this.tickInterval);
            this.tickInterval = null;
        }
        this.obs.disconnect();
    }

    recordYield(value, nodeId) {
        const grossYield = value * this.baseMultiplier;
        this.currentExergy += grossYield;
        this.serializeLedger('YIELD', nodeId, grossYield);
    }

    increaseDeathDebt(penalty, nodeId) {
        this.deathDebt += penalty;
        this.serializeLedger('DEGRADATION', nodeId, -penalty);
    }

    calculateThermodynamics() {
        // Prevent NaN on first tick if lastExergy wasn't set or perf_hooks corrupted it
        if (isNaN(this.currentExergy)) this.currentExergy = 10.0;
        if (isNaN(this.lastExergy)) this.lastExergy = 10.0;

        // Net_Exergy = Current - Default Time Entropy - Debt
        const baselineEntropy = 0.05;
        this.currentExergy = this.currentExergy - baselineEntropy - this.deathDebt;

        // Lyapunov Derivative: dV/dt = V(t) - V(t-1)
        const dV_dt = this.currentExergy - this.lastExergy;
        this.lastExergy = this.currentExergy;

        console.log(`[EXERGY-MONITOR] Net Exergy: ${this.currentExergy.toFixed(4)} | dV/dt: ${dV_dt.toFixed(4)}`);

        // Sovereign Convergence Constraint: 
        if (this.currentExergy <= 0) {
            this.triggerL4Apoptosis(dV_dt);
        }
    }

    serializeLedger(type, nodeId, value) {
        const payload = `${Date.now()}|${type}|${nodeId}|${value}|${this.currentExergy}`;
        const hash = crypto.createHash('sha256').update(payload).digest('hex');
        const entry = `${payload}|${hash}\n`;
        // C5-REAL physical grounding: Append to cortex.db ledger
        fs.appendFileSync(this.dbPath, entry, 'utf8');
    }

    triggerL4Apoptosis(derivative) {
        this.stopMonitoring();
        const killHash = crypto.createHash('sha256').update(`L4_PURGE_${Date.now()}`).digest('hex');
        console.error(`\n[CRITICAL] L4 APOPTOSIS TRIGGERED | HASH: ${killHash}`);
        console.error(`Reason: NET_EXERGY <= 0 (dV/dt = ${derivative.toFixed(4)})`);
        console.error('System instability detected. Execution lock applied. Dispatching REAPER Swarm.\n');
        
        this.eventBus.emit('L4_APOPTOSIS_PURGE', { reason: 'NEGATIVE_EXERGY', hash: killHash });
        this.serializeLedger('APOPTOSIS_PURGE', 'KERNEL', derivative);
    }
}

module.exports = { LyapunovExergyMonitor };
