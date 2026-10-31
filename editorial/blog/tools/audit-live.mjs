#!/usr/bin/env node
// BABYLON-60 publication origin audit. Read-only against the live website.
// Optional --build writes ONLY local dist/. No Cloudflare, Touch ID or key access.
import { readFileSync, existsSync } from "node:fs";
import { join, resolve } from "node:path";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";

const args = new Set(process.argv.slice(2));
const help = args.has("--help") || args.has("-h");
if (help) {
  console.log("Usage: node audit-live.mjs [--build] [--verify] [--json]");
  console.log("Run in ~/10_PROJECTS/babylon60.com. Neither option publishes.");
  process.exit(0);
}
const root = process.cwd();
if (!existsSync(join(root, "scripts/build-complete.mjs")) ||
    !existsSync(join(root, "src/data/articles.json"))) {
  console.error("WRONG_PROJECT: run from the babylon60.com project root");
  process.exit(2);
}
const run = (cmd, parameters) => {
  const p = spawnSync(cmd, parameters, { cwd: root, encoding: "utf8", maxBuffer: 4 * 1024 * 1024 });
  if (p.status !== 0) {
    console.error("PREFLIGHT_FAILED: " + cmd + " " + parameters.join(" "));
    console.error((p.stderr || p.stdout || "").slice(-2500));
    process.exit(p.status || 3);
  }
  if (!args.has("--json")) process.stderr.write(p.stdout);
};
if (args.has("--build")) run("npm", ["run", "build"]);
if (args.has("--verify")) run("npm", ["run", "verify"]);

const raw = JSON.parse(readFileSync(join(root, "src/data/articles.json"), "utf8"));
const list = Array.isArray(raw) ? raw : raw.articles;
if (!Array.isArray(list)) {
  console.error("SCHEMA_UNKNOWN: expected array or {articles: []}");
  process.exit(4);
}
const keys = [...new Set(list.flatMap(item => Object.keys(item)))].sort();
const slugs = (lang) => list
  .map(item => item["slug_" + lang])
  .filter(value => typeof value === "string" && /^[a-z0-9-]+$/.test(value))
  .slice(0, 30);
const paths = [
  "/",
  "/blog/",
  "/en/blog/",
  "/documentacion/",
  "/en/docs/",
  "/evidencia/",
  "/en/assurance/",
  ...slugs("es").map(x => "/blog/" + x + "/"),
  ...slugs("en").map(x => "/en/blog/" + x + "/"),
  "/sitemap.xml",
  "/robots.txt"
];
const distinctPaths = [...new Set(paths)];
const digest = data => createHash("sha256").update(data).digest("hex");
const origin = "https://babylon60.com";
const entries = [];
const fetchOne = async (route) => {
  const relative = route.endsWith("/") ? route + "index.html" : route;
  const localFile = join(root, "dist", relative.replace(/^\/+/, ""));
  const item = {route, local_exists:existsSync(localFile), local_sha256:null, http_status:null,
    remote_sha256:null, byte_equal:null, error:null};
  if (!item.local_exists) { item.error="LOCAL_DIST_MISSING"; return item; }
  const localBytes = readFileSync(localFile);
  item.local_sha256 = digest(localBytes);
  try {
    const response = await fetch(origin + route, {
      redirect:"follow",
      headers: { "Accept": "text/html,application/xml,text/plain;q=0.9" },
      signal: AbortSignal.timeout(12000)
    });
    item.http_status = response.status;
    if (!response.ok) { item.error="HTTP_" + response.status; return item; }
    const remoteBytes = Buffer.from(await response.arrayBuffer());
    item.remote_sha256 = digest(remoteBytes);
    item.byte_equal = localBytes.equals(remoteBytes);
    item.local_bytes = localBytes.length;
    item.remote_bytes = remoteBytes.length;
    item.content_type = response.headers.get("content-type");
  } catch(e) { item.error = (e.name || "NetworkError") + ": " + String(e.message).slice(0,120); }
  return item;
};
for (let i=0; i<distinctPaths.length; i+=3) {
  const results = await Promise.all(distinctPaths.slice(i,i+3).map(fetchOne));
  entries.push(...results);
}
const comparable=entries.filter(x => x.byte_equal !== null);
const matches=comparable.filter(x => x.byte_equal);
const mismatches=comparable.filter(x => !x.byte_equal);
const report={
  schema:"babylon60.origin-audit/v1",
  timestamp:new Date().toISOString(),
  source:"local babylon60.com vs live babylon60.com",
  project_root:root,
  articles:list.length,
  article_keys:keys,
  routes_checked:entries.length,
  comparable:comparable.length,
  matches:matches.length,
  mismatches:mismatches.length,
  verdict:matches.length>=4 && mismatches.length===0 && comparable.length>=4
    ? "LOCAL_OUTPUT_MATCHES_LIVE_FOR_CHECKED_PATHS"
    : mismatches.length>0
      ? "LOCAL_OUTPUT_DIFFERS_FROM_LIVE"
      : "INCONCLUSIVE",
  notes:[
    "Matching bytes support equivalence for checked routes only, not Git/Cloudflare deployment provenance.",
    "A mismatched route may reflect an older deploy, changed source, cache or transformation.",
    "No upload, credential read, key activation or biometric authentication performed."
  ],
  results:entries
};
if (args.has("--json")) {
  process.stdout.write(JSON.stringify(report,null,2)+"\n");
} else {
  console.log("\n" + report.verdict + " | " + matches.length + "/" + comparable.length + " matched");
  console.log("ARTICLE_SCHEMA_KEYS: " + keys.join(", "));
  for (const x of entries) {
    console.log((x.byte_equal===true?"MATCH":x.byte_equal===false?"DIFF":"NO_COMPARE") +
      " " + x.route + (x.error?" ("+x.error+")":""));
  }
  console.log("No production changes performed.");
}
process.exitCode = report.verdict==="LOCAL_OUTPUT_MATCHES_LIVE_FOR_CHECKED_PATHS" ? 0 : 1;
