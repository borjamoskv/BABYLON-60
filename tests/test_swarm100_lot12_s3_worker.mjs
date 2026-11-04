// Runs the checked-in Worker with an injected MIME parser and no external I/O.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { webcrypto } from 'node:crypto';
import vm from 'node:vm';

const source = await readFile(new URL('../01_KISH_ENGINE/services/email_inbound/worker.js', import.meta.url), 'utf8');
async function fixture(outcomes) {
  let calls = 0;
  const delays = [];
  const context = vm.createContext({
    TextEncoder, Response, Uint8Array, crypto: webcrypto, btoa,
    console: { log() {}, warn() {}, error() {} },
    setTimeout(fn, ms) { delays.push(ms); fn(); },
    async fetch() {
      const outcome = outcomes[calls++];
      if (outcome instanceof Error) throw outcome;
      return { ok: outcome === 200, status: outcome, async text() { return 'fixture response'; } };
    },
  });
  const parser = new vm.SyntheticModule(['default'], function() {
    this.setExport('default', class { async parse() { return { text: 'fixture body' }; } });
  }, { context });
  const worker = new vm.SourceTextModule(source, { context });
  await worker.link(async (name) => { assert.equal(name, 'postal-mime'); return parser; });
  await worker.evaluate();
  const message = { from: 'fixture@example.test', to: 'target@example.test', raw: 'fixture', headers: new Headers() };
  return { run: () => worker.namespace.default.email(message, { WEBHOOK_SECRET: 'synthetic-test-key' }, {}),
           calls: () => calls, delays };
}

const failed = await fixture([503, 503, 503]);
await assert.rejects(failed.run(), /delivery|Webhook/i, 'C0422 must reject after all delivery attempts fail');
assert.equal(failed.calls(), 3);
assert.deepEqual(failed.delays, [1000, 2000]);

const network = await fixture([new Error('fixture network'), new Error('fixture network'), new Error('fixture network')]);
await assert.rejects(network.run(), /delivery|Webhook/i);
assert.equal(network.calls(), 3);

const recovered = await fixture([503, 200]);
await recovered.run();
assert.equal(recovered.calls(), 2);
assert.deepEqual(recovered.delays, [1000]);
const immediate = await fixture([200]);
await immediate.run();
assert.equal(immediate.calls(), 1);
assert.deepEqual(immediate.delays, []);
console.log('4 Worker fixtures passed: exhausted HTTP/network failures and retry/direct successes');
