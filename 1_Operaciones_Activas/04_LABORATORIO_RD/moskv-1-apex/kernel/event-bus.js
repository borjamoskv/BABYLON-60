const crypto = require('crypto');
const { EventEmitter } = require('events');
const { isMainThread, parentPort } = require('worker_threads');

/**
 * C5-REAL NATIVE EVENT BUS (Zero Dependency)
 * Bypasses the need for an external NATS broker while maintaining
 * the same interface and Ledger hashing for Swarm execution.
 */
class EventBus {
    constructor() {
        if (!EventBus.instance) {
            this.emitter = new EventEmitter();
            this.lastHash = 'GENESIS';
            EventBus.instance = this;
        }
        return EventBus.instance;
    }

    async init() {
        console.log('[EventBus] Native C5-REAL EventBus Connected. Ready for execution.');
        return Promise.resolve();
    }

    _hash(payload, prevHash) {
        return crypto.createHash('sha256')
            .update(prevHash + JSON.stringify(payload))
            .digest('hex');
    }

    async emit(subject, payload) {
        if (!isMainThread && parentPort) {
            parentPort.postMessage({ type: 'EVENT_BUS_FORWARD', subject, payload });
        }

        const currentHash = this._hash(payload, this.lastHash);
        const event = {
            timestamp: Date.now(),
            payload,
            prevHash: this.lastHash,
            hash: currentHash
        };

        this.lastHash = currentHash;
        
        // Asynchronous native emit to simulate network decoupling
        setImmediate(() => {
            this.emitter.emit(subject, event);
        });

        return { hash: currentHash, seq: Date.now() };
    }

    async subscribe(subject, callback, durableName = null) {
        const listener = (event) => {
            const msg = {
                seq: Date.now(),
                ack: () => Promise.resolve(),
                nak: () => Promise.resolve()
            };
            callback(event, msg);
        };
        this.emitter.on(subject, listener);
        return {
            stop: () => {
                this.emitter.off(subject, listener);
            }
        };
    }

    async on(subject, callback) {
        this.emitter.on(subject, callback);
    }

    async close() {
        this.emitter.removeAllListeners();
        console.log('[EventBus] Connection closed.');
    }
}

module.exports = { EventBus };
