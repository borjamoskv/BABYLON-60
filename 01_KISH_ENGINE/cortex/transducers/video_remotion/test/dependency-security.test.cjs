"use strict";

// Regressions for four fast-uri advisories and the bounded Zod collection fix.
// Pure local inputs: no browser, network, or media rendering.
const assert = require("node:assert/strict");
const test = require("node:test");
const {spawnSync} = require("node:child_process");
const path = require("node:path");
const uri = require("fast-uri");

function testCase(ghsa, name, reference, body) {
  test(`${ghsa}: ${name}`, (context) => {
    context.diagnostic(reference);
    const check = (condition, invariant, actual, expected) => {
      assert.ok(condition, `${invariant} Actual: ${JSON.stringify(actual)}; expected: ${JSON.stringify(expected)}`);
    };
    const throws = (fn) => {
      try {return {threw: false, result: fn()};}
      catch (error) {return {threw: true, message: error.message};}
    };
    body(check, () => {}, throws);
  });
}

testCase('GHSA-w74x-v6f9-j3xg', 'Encoded scheme tokens remain inert and are rejected',
  'https://www.rfc-editor.org/rfc/rfc3986.html#section-3.1', (check, observe, throws) => {
    const dangerousScheme = /^(?:javascript|data|vbscript)$/i;
    const inputs = ['%6Aavascript:alert(1)', '%u006Aavascript:alert(1)', '%64ata:text/plain,example'];
    for (const input of inputs) {
      const parsed = uri.parse(input);
      const normalized = uri.normalize(input);
      const resolution = throws(() => uri.resolve('https://safe.example/app/', input));
      observe({input, parsed, normalized, resolution});
      check(Boolean(parsed.error), 'A percent-encoded scheme is malformed under RFC 3986.', parsed.error, 'nonempty parse error');
      check(!dangerousScheme.test(String(parsed.scheme)), 'Parsing cannot activate an encoded dangerous scheme.', parsed.scheme, 'no dangerous scheme');
      check(normalized === input, 'Normalization preserves malformed encoded scheme input.', normalized, input);
      check(resolution.threw, 'Resolution rejects malformed encoded scheme input.', resolution, 'exception');
    }
    const alias = uri.equal('%68ttp://a.example/', 'http://a.example/');
    observe({encodedSchemeEqualsPlainScheme: alias});
    check(alias === false, 'Encoded schemes cannot bypass equality checks.', alias, false);
  });

testCase('GHSA-xhq7-xmqj-769h', 'Relative normalization preserves the resolved resource',
  'https://www.rfc-editor.org/rfc/rfc3986.html#section-5.2.2', (check, observe) => {
    const inputs = ['a/../b', '../x', 'x/..', 'a/../a:b'];
    const bases = ['https://safe.example/app/nested/page', 'https://safe.example/one/two/'];
    for (const input of inputs) {
      const normalized = uri.normalize(input);
      const parsed = uri.parse(normalized);
      check(parsed.scheme === undefined && parsed.host === undefined, 'A relative path cannot acquire a scheme or authority.', parsed, 'no scheme or authority');
      check(!normalized.startsWith('/'), 'A document-relative reference cannot become root-relative.', normalized, 'relative path');
      for (const base of bases) {
        const direct = uri.resolve(base, input);
        const afterNormalization = uri.resolve(base, normalized);
        observe({base, input, normalized, direct, afterNormalization});
        check(afterNormalization === direct, 'Normalize-then-resolve must reach the same resource as direct resolution.', afterNormalization, direct);
      }
    }
  });

testCase('GHSA-wjr9-j795-jxcr', 'Malformed HTTP authorities fail without host rewriting',
  'https://www.rfc-editor.org/rfc/rfc3986.html#section-3.2.2', (check, observe, throws) => {
    const inputs = [
      {raw: 'http://a@b@evil.example/', clean: 'http://a@evil.example/'},
      {raw: 'http://ev\til.example/', clean: 'http://evil.example/'}
    ];
    for (const {raw, clean} of inputs) {
      const parsed = uri.parse(raw);
      const normalized = uri.normalize(raw);
      const resolution = throws(() => uri.resolve('https://safe.example/app/', raw));
      const alias = uri.equal(raw, clean);
      observe({raw, clean, parsed, normalized, resolution, aliasesCleanHost: alias});
      check(Boolean(parsed.error), 'Invalid reg-name characters cannot silently pass host validation.', parsed.error, 'nonempty parse error');
      check(normalized === raw, 'Malformed authority normalization cannot remove host data.', normalized, raw);
      check(alias === false, 'Malformed and clean authorities cannot be treated as equal.', alias, false);
      check(resolution.threw, 'Resolution rejects the malformed authority.', resolution, 'exception');
    }
    const valid = uri.parse('https://safe.example/');
    observe({validControl: valid});
    check(!valid.error, 'A well-formed HTTPS authority remains accepted.', valid.error, 'no parse error');
  });

testCase('GHSA-333x-w4r6-6crp', 'Authority-free suffix serialization cannot activate a scheme',
  'https://www.rfc-editor.org/rfc/rfc3986.html#section-3.3', (check, observe) => {
    // A valid URI component can contain a scheme and no authority. Suffix
    // serialization suppresses that scheme, so its emitted path must obey
    // path-noscheme grammar. The old predicate checked component.scheme even
    // though suffix output omitted it. Ambiguous suffix string parsing is not
    // used as an oracle for this no-authority serialization invariant.
    for (const input of ['javascript:alert(1)', 'data:text/plain,example', 'vbscript:msgbox(1)']) {
      const component = {scheme: 'x', path: input};
      const serialized = uri.serialize(component, {reference: 'suffix'});
      const reparsed = uri.parse(serialized);
      observe({component, serialized, reparsed});
      check(reparsed.scheme === undefined, 'A path-noscheme reference cannot acquire an absolute URI scheme.', reparsed.scheme, 'no scheme');
      check(reparsed.host === undefined, 'Authority-free suffix serialization cannot create an authority.', reparsed.host, 'no authority');
      check(!reparsed.error, 'Escaped relative suffix output remains a well-formed URI reference.', reparsed.error, 'no parse error');
      check(!serialized.split('/')[0].includes(':'), 'The first path-noscheme segment contains no bare colon.', serialized, 'first segment without literal colon');
    }
  });


// The fix concerns leading upper-size checks. It does not bound issues from
// unbounded collections. Counter and issue assertions avoid timing thresholds.
// Upstream fix: https://github.com/colinhacks/zod/commit/a0ebf97
// Discussion: https://github.com/colinhacks/zod/pull/6652
test("GHSA-mrhx-c7xc-m3w5: bounded Zod collections and upstream schemas", {timeout: 12_000}, () => {
  const worker = String.raw`
    const assert = require("node:assert/strict");
    const imported = require("zod");
    const z = imported.z || imported;
    let visits = 0;
    const element = z.string().superRefine((_value, ctx) => {
      visits++;
      ctx.addIssue({code: "custom", message: "bounded security probe"});
    });
    const oversized = z.array(element).max(1).safeParse(Array(4096).fill("invalid-by-refinement"));
    assert.equal(oversized.success, false);
    assert.equal(visits, 0, "upper-size bound must run before element validation");
    assert.equal(oversized.error.issues.length, 1, "oversized input must allocate one issue");
    assert.equal(oversized.error.issues[0].code, "too_big");
    assert.equal(oversized.error.issues[0].maximum, 1);
    assert.deepEqual(oversized.error.issues[0].path, []);
    let admittedVisits = 0;
    const admitted = z.array(z.string().superRefine(() => {admittedVisits++;})).max(1).safeParse(["valid"]);
    assert.equal(admitted.success, true);
    assert.equal(admittedVisits, 1);
    assert.deepEqual(admitted.data, ["valid"]);
    const invalid = z.array(z.string()).max(1).safeParse([7]);
    assert.equal(invalid.success, false);
    assert.equal(invalid.error.issues.length, 1);
    assert.equal(invalid.error.issues[0].code, "invalid_type");
    assert.deepEqual(invalid.error.issues[0].path, [0]);
    process.stdout.write(JSON.stringify({inputElements: 4096, maximum: 1, visits, issues: oversized.error.issues.length}));
  `;
  const run = spawnSync(process.execPath, ["--max-old-space-size=128", "--eval", worker], {
    cwd: path.resolve(__dirname, ".."),
    timeout: 10_000,
    maxBuffer: 2 * 1024 * 1024,
    encoding: "utf8",
    env: {...process.env, NODE_OPTIONS: ""},
  });
  assert.equal(run.error, undefined, run.error?.message);
  assert.equal(run.signal, null, `bounded child terminated: ${run.signal}`);
  assert.equal(run.status, 0, run.stderr);
  assert.deepEqual(JSON.parse(run.stdout), {inputElements: 4096, maximum: 1, visits: 0, issues: 1});

  // Exercise the parent's actual bundled Zod schemas through its exported parser.
  const {StudioProtocolInternals} = require("@remotion/studio-protocol");
  const parse = StudioProtocolInternals.parseStudioProtocolDescriptor;
  const descriptor = {
    protocol: "remotion-studio-protocol",
    protocolVersion: 1,
    studioVersion: "fixture",
    projectName: "security-regression",
    capabilities: [
      {type: "install-element", payloadType: "remotion-element", payloadVersions: [1], target: null},
      {type: "set-license-key", target: null},
      {type: "add-element-library", target: null},
    ],
  };
  assert.deepEqual(parse(structuredClone(descriptor)), descriptor);
  for (const invalid of [
    {...descriptor, protocol: "invalid-protocol"},
    {...descriptor, protocolVersion: 2},
    {...descriptor, projectName: 123},
    {...descriptor, capabilities: "invalid-array"},
    {...descriptor, capabilities: [descriptor.capabilities[0], descriptor.capabilities[0]]},
  ]) assert.equal(parse(invalid), null);
  const filtered = parse({...descriptor, capabilities: [...descriptor.capabilities, {
    type: "install-element", payloadType: "remotion-element", payloadVersions: ["wrong-type"], target: null,
  }]});
  assert.deepEqual(filtered, descriptor);
});
