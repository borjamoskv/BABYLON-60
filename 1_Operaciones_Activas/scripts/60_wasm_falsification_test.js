#!/usr/bin/env node
// C5-REAL EXERGY CERTIFIED
// [CORTEX-TAINT:FALSIFY]
// Axiom Ω22 (Popperian Falsifiability) & Ω3 (Zero-Rhetoric Console Mirror)

import { performance } from 'perf_hooks';
import init, * as wasm from '../02_CORTEX_ENGINE/cortex-wasm/pkg/cortex_wasm.js';
import crypto from 'crypto';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// UUIDv5 Idempotent Injection
const NAMESPACE = '1b671a64-40d5-491e-99b0-da01ff1f3341';
const sessionId = crypto.createHash('sha256').update(NAMESPACE + Date.now().toString()).digest('hex').substring(0, 8);

console.log(`[CORTEX-TAINT:VERIFY] UUIDv5 Session: ${sessionId}`);
console.log('====================================================');
console.log('■ FALSIFICATION TEST: "WASM is the Thermodynamic Peak"');
console.log('====================================================\n');

console.log('[1/3] Initializing WASM Engine...');
const wasmBuffer = fs.readFileSync(join(__dirname, '../02_CORTEX_ENGINE/cortex-wasm/pkg/cortex_wasm_bg.wasm'));
await init(wasmBuffer);
const engine = new wasm.WasmScoreEngine(120000);
console.log('✔ WASM Engine Initialized (max: 120000)');

const ITERATIONS = 120_000;

console.log(`\n[2/3] Executing JS-Native Trivial Loop (${ITERATIONS} iteraciones)...`);
let jsCounter = 0;
const t0_js = performance.now();
for (let i = 0; i < ITERATIONS; i++) {
    jsCounter += 1; // Trivial compute (1 CPU cycle), perfectly inlined by V8 JIT
}
const t1_js = performance.now();
const jsTime = (t1_js - t0_js).toFixed(4);
console.log(`  ➜ JS Native Time: ${jsTime}ms (JIT Inlining: Max Exergy)`);

console.log(`\n[3/3] Executing WASM-Boundary Trivial Loop (${ITERATIONS} iteraciones)...`);
let wasmCounter = 0;
const t0_wasm = performance.now();
for (let i = 0; i < ITERATIONS; i++) {
    wasmCounter += wasm.WasmScoreEngine.count_divisors(0); // Trivial compute in WASM, but forces Boundary Crossing
}
const t1_wasm = performance.now();
const wasmTime = (t1_wasm - t0_wasm).toFixed(4);
console.log(`  ➜ WASM Boundary Time: ${wasmTime}ms`);

console.log('\n====================================================');
console.log('■ FALSIFICATION RESULT');
console.log('====================================================');
if (parseFloat(wasmTime) > parseFloat(jsTime)) {
    console.log('[FATAL] STATEMENT FALSIFIED.');
    console.log('WASM is NOT the absolute thermodynamic peak of local-first computation.');
    console.log(`The V8 JIT compiler (JS) outperformed WASM by ${(parseFloat(wasmTime) / parseFloat(jsTime)).toFixed(2)}x.`);
    console.log('Reason: When computational density is low, the JS <-> WASM Boundary Friction (Anergia) exceeds the execution cost.');
    console.log('True Exergy requires Flat Array Pointers (Ω30 Data-Packing) to minimize boundary context-switching.');
} else {
    console.log('[ACK] WASM maintained absolute dominance despite boundary friction.');
}
