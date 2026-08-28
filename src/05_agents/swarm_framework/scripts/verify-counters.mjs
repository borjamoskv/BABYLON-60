// verify-counters.mjs — invariante agents-archi: contadores del home == datos REPORTS.
import { readFileSync, writeFileSync, rmSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { pathToFileURL } from 'node:url';
const root = process.cwd();
const dataSrc = resolve(root, 'src/components/auditReport.js');
const stripped = readFileSync(dataSrc, 'utf8').replace(/^\s*import\s+['"][^'"]+\.(css|scss|sass)['"];?\s*$/gm, '');
const tmp = resolve(dirname(dataSrc), `.__verify_${Date.now()}.mjs`);
writeFileSync(tmp, stripped);
let REPORTS; try { ({ REPORTS } = await import(pathToFileURL(tmp).href)); } finally { rmSync(tmp, { force: true }); }
const seen = new Set(); const d = { total: 0, critical: 0, high: 0, medium: 0 };
for (const k of Object.keys(REPORTS)) {
  const desc = Object.getOwnPropertyDescriptor(REPORTS, k);
  if (desc && typeof desc.get === 'function' && !('value' in desc)) continue;
  const r = REPORTS[k]; if (!r || !r.id || seen.has(r.id)) continue; seen.add(r.id);
  d.total++; const s = String(r.severity || '').toUpperCase();
  if (s === 'CRITICAL') d.critical++; else if (s === 'HIGH') d.high++; else if (s === 'MEDIUM') d.medium++;
}
const html = readFileSync(resolve(root, 'index.html'), 'utf8');
const num = re => { const m = html.match(re); return m ? parseInt(m[1], 10) : null; };
const h = { total: num(/bounty-total-count">\s*([0-9]+)/), critical: num(/([0-9]+)\s*Críticos/), high: num(/([0-9]+)\s*Alta/), medium: num(/([0-9]+)\s*Media/) };
let fail = 0; const chk = (n, a, b) => { const ok = a === b; console.log(`${ok ? '✓' : '✗'} ${n}: html=${a} · datos=${b}`); if (!ok) fail = 1; };
chk('total hallazgos', h.total, d.total); chk('críticos', h.critical, d.critical); chk('alta', h.high, d.high); chk('media', h.medium, d.medium);
console.log('------------------------------------------------');
if (fail) { console.log('VERIFY-COUNTERS: FAIL'); process.exit(1); } console.log('VERIFY-COUNTERS: PASS');
