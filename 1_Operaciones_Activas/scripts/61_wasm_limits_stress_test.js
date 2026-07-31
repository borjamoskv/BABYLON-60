#!/usr/bin/env node
// C5-REAL EXERGY CERTIFIED
// [CORTEX-TAINT:STRESS-TEST]
// Axiom Ω15 (Hardware Exergy Maximization) & Ω3 (Zero-Rhetoric)

import { performance } from 'perf_hooks';
import init, * as wasm from '../02_CORTEX_ENGINE/cortex-wasm/pkg/cortex_wasm.js';
import crypto from 'crypto';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const NAMESPACE = '1b671a64-40d5-491e-99b0-da01ff1f3341';
const sessionId = crypto.createHash('sha256').update(NAMESPACE + Date.now().toString()).digest('hex').substring(0, 8);

console.log(`[CORTEX-TAINT:STRESS-TEST] UUIDv5 Session: ${sessionId}`);
console.log('========================================================================');
console.log('■ ULTRATHINK WASM LIMITS (LINEAR MEMORY & MAX THROUGHPUT BOUNDARIES)');
console.log('========================================================================\n');

async function runLimits() {
    const wasmBuffer = fs.readFileSync(join(__dirname, '../02_CORTEX_ENGINE/cortex-wasm/pkg/cortex_wasm_bg.wasm'));
    await init(wasmBuffer);

    const scales = [1_200_000, 12_000_000, 120_000_000, 1_200_000_000];

    for (const maxLimit of scales) {
        console.log(`\n>>> INICIANDO ESCALA: ${maxLimit.toLocaleString()} OPERACIONES`);
        try {
            // 1. Memory Allocation (Vec<bool> Sieve of Eratosthenes)
            const t0_alloc = performance.now();
            const engine = new wasm.WasmScoreEngine(maxLimit);
            const t1_alloc = performance.now();

            console.log(`  [✓] ALLOC & SIEVE: ${(t1_alloc - t0_alloc).toFixed(2)}ms`);

            // 2. SIMD Batch Evaluation (Vec<f32>) - We cap the batch to avoid immediate OOM just from the output buffer
            // A 1.2B f32 array = 4.8 GB (Exceeds WASM32 4GB limit). So we evaluate a chunk of it to test the CPU throughput.
            const BATCH_SIZE = Math.min(maxLimit, 10_000_000); // 10M chunk max for output serialization
            const t0_eval = performance.now();
            const results = engine.evaluate_batch(1, BATCH_SIZE, 144);
            const t1_eval = performance.now();

            const opsPerMs = Math.floor(BATCH_SIZE / (t1_eval - t0_eval));

            console.log(`  [✓] BATCH EVAL (${BATCH_SIZE.toLocaleString()} ops): ${(t1_eval - t0_eval).toFixed(2)}ms`);
            console.log(`  [⚡] THROUGHPUT EXERGÉTICO: ${opsPerMs.toLocaleString()} ops/ms`);

            // Explicitly force garbage collection / memory drop on JS side
            engine.free();

        } catch (e) {
            console.log(`  [FATAL] COLAPSO FÍSICO EN LÍMITE: ${maxLimit.toLocaleString()}`);
            console.log(`  [ERROR-LOG] ${e.message}`);
            break; // Stop climbing the scale
        }
    }

    console.log('\n========================================================================');
    console.log('■ PRUEBA DE LÍMITES COMPLETADA');
    console.log('========================================================================');
}

runLimits();
