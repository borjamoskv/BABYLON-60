// Interop probe with the official MCP TypeScript client (@modelcontextprotocol/client),
// the same package dsh-mcp-client imports. NOT DeepSeek Harness itself.
//
// Preparación aislada reproducible (sin tocar package.json ni lockfiles del repositorio):
//   Fuente oficial: https://github.com/modelcontextprotocol/typescript-sdk/blob/main/docs/get-started/first-client.md
//   TMP_DIR=$(mktemp -d /tmp/cortex-mcp-probe.XXXXXX) && cd "$TMP_DIR"
//   npm init -y
//   npm install @modelcontextprotocol/client@2.4.0
//   cp "<repo>/scripts/cortex_memory/sdk_ab_probe.mjs" "$TMP_DIR/"
//   node "$TMP_DIR/sdk_ab_probe.mjs" <abs-python> <abs-repo> <abs-binding> <abs-pubkey> <abs-ledger> <abs-brokerlib>
//   rm -rf "$TMP_DIR"
//
// Nota Node ESM: NODE_PATH no resuelve imports bare en módulos .mjs; debe ejecutarse la copia en el directorio con node_modules.
// Usage: node sdk_ab_probe.mjs <python> <repo> <binding> <pubkey> <ledger> <brokerlib>
import { Client } from "@modelcontextprotocol/client";
import { StdioClientTransport } from "@modelcontextprotocol/client/stdio";

const [python, repo, binding, pub, ledger, lib] = process.argv.slice(2);
const SCRUB = /KEY|PASSWORD|SECRET|TOKEN/i; // documented DSH stdio scrub rule
const env = Object.fromEntries(Object.entries(process.env).filter(([k]) => !SCRUB.test(k) && !k.startsWith("DSH_")));

async function session(label, fn) {
  const transport = new StdioClientTransport({
    command: python,
    args: ["-m", "babylon60.mcp.cortex_memory_mcp", "serve", "--binding", binding, "--trust-pubkey", pub, "--ledger", ledger, "--broker-lib", lib],
    env, cwd: repo, stderr: "ignore",
  });
  const client = new Client({ name: `sdk-probe-${label}`, version: "1.0.0" });
  await client.connect(transport);
  const proto = transport._protocolVersion ?? client.getNegotiatedProtocolVersion?.() ?? null;
  const tools = (await client.listTools()).tools.map((t) => t.name);
  const out = await fn(client);
  await client.close();
  return { label, proto, tools, ...out };
}

const suffix = Date.now().toString(36);
const a = await session("A", async (c) => {
  const r = await c.callTool({ name: "memory_append", arguments: { request_id: `sdk-${suffix}`, value: `validation drink is lapsang-${suffix}` } });
  return { isError: r.isError, result: r.structuredContent };
});
const b = await session("B", async (c) => {
  const r = await c.callTool({ name: "memory_read", arguments: { text: `lapsang-${suffix}` } });
  return { isError: r.isError, values: r.structuredContent.items.map((i) => i.value), receipt: r.structuredContent.receipt, served_by: r.structuredContent.served_by };
});
const ok = !a.isError && b.values.length === 1 && b.values[0].endsWith(suffix) && a.result.served_by.instance_id !== b.served_by.instance_id;
console.log(JSON.stringify({ ok, a, b }, null, 2));
process.exit(ok ? 0 : 1);
