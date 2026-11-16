// Independent control-flow checks of the real Worker module. No SMTP/HTTP I/O.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { webcrypto } from 'node:crypto';
import vm from 'node:vm';

const source = await readFile(new URL('../../../../../01_KISH_ENGINE/services/email_inbound/worker.js', import.meta.url), 'utf8');

async function runCase(outcomes, secret = 'fixture-only-authority') {
  const calls = [];
  const waits = [];
  const context = vm.createContext({
    TextEncoder, Response, Uint8Array, Headers, crypto: webcrypto, btoa,
    console: { log() {}, warn() {}, error() {} },
    setTimeout(fn, milliseconds) { waits.push(milliseconds); fn(); },
    async fetch(url, options) {
      const position = calls.length;
      calls.push({ url, options });
      const outcome = outcomes[position];
      if (outcome instanceof Error) throw outcome;
      assert.ok(outcome, 'No fourth attempt is allowed');
      return {
        status: outcome.status,
        ok: outcome.status >= 200 && outcome.status < 300,
        async text() {
          if (outcome.readError) throw new Error('fixture response body failure');
          return 'inert fixture response';
        },
      };
    },
  });
  const postal = new vm.SyntheticModule(['default'], function() {
    this.setExport('default', class {
      async parse() { return { subject: 'Independent fixture', text: 'inert body' }; }
    });
  }, { context });
  const worker = new vm.SourceTextModule(source, { context });
  await worker.link(async (name) => {
    assert.equal(name, 'postal-mime');
    return postal;
  });
  await worker.evaluate();
  let failure;
  try {
    await worker.namespace.default.email({
      from: 'sender@example.test', to: 'receiver@example.test', raw: 'synthetic MIME',
      headers: new Headers({ 'message-id': '<independent@example.test>' }),
    }, { WEBHOOK_URL: 'https://fixture.invalid/inbound', WEBHOOK_SECRET: secret }, {});
  } catch (error) {
    failure = error;
  }
  return { calls, waits, failure };
}

const exhausted = await runCase([{ status: 400 }, { status: 503 }, { status: 429 }]);
assert.ok(exhausted.failure);
assert.match(exhausted.failure.message, /all attempts/);
assert.equal(exhausted.calls.length, 3);
assert.deepEqual(exhausted.waits, [1000, 2000]);
assert.equal(new Set(exhausted.calls.map(call => call.options.body)).size, 1);
assert.equal(new Set(exhausted.calls.map(call => call.options.headers['X-Babylon-Signature'])).size, 1);

const network = await runCase([new TypeError('fixture transport'), new TypeError('fixture transport'), new TypeError('fixture transport')]);
assert.ok(network.failure);
assert.equal(network.calls.length, 3);
assert.deepEqual(network.waits, [1000, 2000]);

const unreadable = await runCase([{ status: 500, readError: true }, { status: 502 }, { status: 500 }]);
assert.ok(unreadable.failure);
assert.equal(unreadable.calls.length, 3);

const recovered = await runCase([new TypeError('fixture transport'), { status: 503 }, { status: 201 }]);
assert.equal(recovered.failure, undefined);
assert.equal(recovered.calls.length, 3);
assert.deepEqual(recovered.waits, [1000, 2000]);

const accepted = await runCase([{ status: 202 }]);
assert.equal(accepted.failure, undefined);
assert.equal(accepted.calls.length, 1);
assert.deepEqual(accepted.waits, []);

const absentSecret = await runCase([], '');
assert.ok(absentSecret.failure);
assert.match(absentSecret.failure.message, /WEBHOOK_SECRET/);
assert.equal(absentSecret.calls.length, 0);
console.log('6 independent Worker fixtures passed; failures reject and 2xx success resolves. No SMTP retry asserted.');
