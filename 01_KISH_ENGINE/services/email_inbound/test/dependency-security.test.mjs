import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';
import { copyFile, mkdtemp, readFile, rm } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import test from 'node:test';
import PostalMime, { decodeWords } from 'postal-mime';

// Wrangler bundles worker.js as an ES module even though package.json marks
// the package CommonJS. Import an identical .mjs copy inside this app so its
// real postal-mime dependency resolves normally; always remove our own temp.
const workerUrl = new URL('../worker.js', import.meta.url);
const tempDir = await mkdtemp(join(dirname(fileURLToPath(workerUrl)), '.dependency-security-'));
let worker;
try {
  const modulePath = join(tempDir, 'worker.mjs');
  await copyFile(workerUrl, modulePath);
  assert.deepEqual(await readFile(modulePath), await readFile(workerUrl));
  ({ default: worker } = await import(pathToFileURL(modulePath).href));
} finally {
  await rm(tempDir, { recursive: true, force: true });
}

const multipart = [
  'From: Sender <sender@example.test>',
  'To: inbox@example.test',
  'Subject: =?utf-8?B?VGVzdCDinJM=?=',
  'Message-ID: <fixture@example.test>',
  'MIME-Version: 1.0',
  'Content-Type: multipart/mixed; boundary="outer"',
  '',
  '--outer',
  'Content-Type: multipart/alternative; boundary="inner"',
  '',
  '--inner',
  'Content-Type: text/plain; charset=utf-8',
  '',
  'Plain email body',
  '--inner',
  'Content-Type: text/html; charset=utf-8',
  '',
  '<p>HTML email body</p>',
  '--inner--',
  '--outer',
  'Content-Type: application/octet-stream; name="sample.bin"',
  'Content-Disposition: attachment; filename="sample.bin"',
  'Content-Transfer-Encoding: base64',
  '',
  'AQID',
  '--outer--',
  ''
].join('\r\n');
const message = raw => ({
  from: 'sender@example.test', to: 'inbox@example.test',
  headers: new Headers({ subject: 'fallback', 'message-id': '<fixture@example.test>' }),
  raw: new Response(raw).body
});

test('real Worker parses text, HTML and binary attachments and signs delivery', async context => {
  const sent = [];
  context.mock.method(globalThis, 'fetch', async (url, init) => {
    sent.push({ url, init });
    return new Response('ok', { status: 200 });
  });
  const secret = 'isolated-test-secret';
  await worker.email(message(multipart), { WEBHOOK_SECRET: secret, WEBHOOK_URL: 'https://receiver.invalid/inbound' }, {});
  assert.equal(sent.length, 1);
  const { url, init } = sent[0];
  const payload = JSON.parse(init.body);
  assert.equal(url, 'https://receiver.invalid/inbound');
  assert.equal(payload.subject, 'Test ✓');
  assert.match(payload.text_body, /Plain email body/);
  assert.match(payload.html_body, /<p>HTML email body<\/p>/);
  assert.equal(payload.attachments_count, 1);
  assert.deepEqual(payload.attachments_metadata, [{ filename: 'sample.bin', mimeType: 'application/octet-stream', size: 3, content_b64: 'AQID' }]);
  assert.equal(payload.message_id, '<fixture@example.test>');
  assert.equal(init.headers['X-Babylon-Signature'], createHmac('sha256', secret).update(init.body).digest('hex'));
});

test('missing webhook secret rejects before any delivery', async context => {
  let calls = 0;
  context.mock.method(globalThis, 'fetch', async () => { calls++; throw new Error('unexpected delivery'); });
  await assert.rejects(worker.email(message(multipart), {}, {}), /WEBHOOK_SECRET is required/);
  assert.equal(calls, 0);
});

test('RFC 2047 encoded words decode at N and 2N with bounded observed timings', async context => {
  const samples = [];
  // No timing threshold: record observations without turning scheduling noise
  // into a pass criterion. The process timeout bounds this security probe.
  for (const count of [2048, 4096]) {
    const header = '=?utf-8?B?QUJD?= '.repeat(count);
    const raw = `Subject: ${header}\r\n\r\nBody`;
    const decodeStart = performance.now();
    assert.equal(decodeWords(header).trim(), 'ABC'.repeat(count));
    const decodeMs = performance.now() - decodeStart;
    const parseStart = performance.now();
    const parsed = await new PostalMime().parse(new TextEncoder().encode(raw).buffer);
    const parseMs = performance.now() - parseStart;
    assert.equal(parsed.subject, 'ABC'.repeat(count));
    samples.push({ words: count, rawBytes: new TextEncoder().encode(raw).byteLength, decodeMs, parseMs });
  }
  context.diagnostic(JSON.stringify({ samples, decodeRatio2N: samples[1].decodeMs / samples[0].decodeMs, parseRatio2N: samples[1].parseMs / samples[0].parseMs, note: 'bounded observations, no complexity or performance guarantee' }));
});

test('header accounting charges short lines against the whole header budget', async () => {
  await assert.rejects(new PostalMime({ maxHeadersSize: 100 }).parse('A:b\r\nB:c\r\n\r\nbody'), /Maximum header size/);
});

test('inline forwarded messages share the outer MIME part budget', async () => {
  const forwarded = [
    'MIME-Version: 1.0', 'Content-Type: multipart/mixed; boundary="top"', '',
    '--top', 'Content-Type: message/rfc822', '',
    'Subject: forwarded', 'Content-Type: multipart/mixed; boundary="nested"', '',
    '--nested', 'Content-Type: text/plain', '', 'one',
    '--nested', 'Content-Type: text/plain', '', 'two', '--nested--', '--top--', ''
  ].join('\r\n');
  await assert.rejects(new PostalMime({ maxPartCount: 3 }).parse(forwarded), /Maximum MIME part count/);
});
