import assert from 'node:assert/strict';
import {createHmac} from 'node:crypto';
import {test} from 'node:test';
import PostalMime from 'postal-mime';
import worker from './worker.js';

const secret = 'isolated-test-secret';

test('parses MIME attachments and signs the exact webhook payload', async (t) => {
  const deliveries = [];
  t.mock.method(globalThis, 'fetch', async (url, request) => {
    deliveries.push({url, request});
    return new Response('', {status: 200});
  });
  const raw = [
    'From: sender@example.invalid',
    'To: receiver@example.invalid',
    'Subject: =?UTF-8?B?UHJ1ZWJhIMOx?=',
    'MIME-Version: 1.0',
    'Content-Type: multipart/mixed; boundary="test-boundary"',
    '',
    '--test-boundary',
    'Content-Type: text/plain; charset=utf-8',
    '',
    'Message body',
    '--test-boundary',
    'Content-Type: application/octet-stream',
    'Content-Disposition: attachment; filename="sample.bin"',
    'Content-Transfer-Encoding: base64',
    '',
    'aGVsbG8=',
    '--test-boundary--',
    '',
  ].join('\r\n');
  await worker.email({
    from: 'sender@example.invalid',
    to: 'receiver@example.invalid',
    headers: new Headers({'message-id': '<isolated-test@example.invalid>'}),
    raw: new TextEncoder().encode(raw),
  }, {WEBHOOK_SECRET: secret, WEBHOOK_URL: 'https://webhook.example.invalid'}, {});

  assert.equal(deliveries.length, 1);
  const {url, request} = deliveries[0];
  assert.equal(url, 'https://webhook.example.invalid');
  const payload = JSON.parse(request.body);
  assert.equal(payload.subject, 'Prueba ñ');
  assert.equal(payload.text_body.trim(), 'Message body');
  assert.equal(payload.message_id, '<isolated-test@example.invalid>');
  assert.equal(payload.attachments_count, 1);
  assert.deepEqual(payload.attachments_metadata[0], {
    filename: 'sample.bin', mimeType: 'application/octet-stream',
    size: 5, content_b64: 'aGVsbG8=',
  });
  assert.equal(request.headers['Authorization'], `Bearer ${secret}`);
  assert.equal(request.headers['X-Babylon-Signature'],
    createHmac('sha256', secret).update(request.body).digest('hex'));
});

test('rejects missing webhook credentials before parsing or delivery', async (t) => {
  const fetch = t.mock.method(globalThis, 'fetch', () => {
    throw new Error('unexpected external call');
  });
  await assert.rejects(worker.email({}, {}, {}), /WEBHOOK_SECRET/);
  assert.equal(fetch.mock.callCount(), 0);
});

test('decodes repeated encoded header words after warmup', {timeout: 5000}, async () => {
  await PostalMime.parse('Subject: warmup\r\n\r\nbody');
  const count = 2000;
  const encoded = Array(count).fill('=?UTF-8?B?aGVsbG8=?=').join(' ');
  for (let iteration = 0; iteration < 20; iteration++) {
    const parsed = await PostalMime.parse(`Subject: ${encoded}\r\n\r\nbody`);
    assert.equal(parsed.subject, 'hello'.repeat(count));
  }
});
