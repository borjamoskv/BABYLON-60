// Prerender estático de /audit/<slug>. Uso: node scripts/prerender-audits.mjs [templateHtml] [outDir]
import { readFileSync, writeFileSync, mkdirSync, rmSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const __dir = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dir, '..');
const templatePath = resolve(root, process.argv[2] || 'dist/index.html');
const outDir = resolve(root, process.argv[3] || 'dist');
const ORIGIN = 'https://agents.archi';
const dataSrc = resolve(root, 'src/components/auditReport.js');
const stripped = readFileSync(dataSrc, 'utf8').replace(/^\s*import\s+['"][^'"]+\.(css|scss|sass)['"];?\s*$/gm, '');
const tmpMod = resolve(dirname(dataSrc), `.__prerender_${Date.now()}.mjs`);
writeFileSync(tmpMod, stripped);
let REPORTS; try { ({ REPORTS } = await import(pathToFileURL(tmpMod).href)); } finally { rmSync(tmpMod, { force: true }); }
const template = readFileSync(templatePath, 'utf8');
const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const clip = (s,n=157) => { s=String(s||'').replace(/\s+/g,' ').trim(); return s.length>n ? s.slice(0,n-1).trimEnd()+'…' : s; };
let n = 0;
for (const slug of Object.keys(REPORTS)) {
  const dd = Object.getOwnPropertyDescriptor(REPORTS, slug);
  if (dd && typeof dd.get === 'function' && !('value' in dd)) continue;
  const r = REPORTS[slug]; if (!r || !r.title) continue;
  const title = `${r.title} — agents.archi`;
  const description = clip(r.summary || r.subtitle || '');
  const url = `${ORIGIN}/audit/${slug}`;
  const htmlOut = template
    .replace(/<title>[\s\S]*?<\/title>/, `<title>${esc(title)}</title>`)
    .replace(/(<meta name="description" content=")[^"]*(")/, `$1${esc(description)}$2`)
    .replace(/(<meta property="og:title" content=")[^"]*(")/, `$1${esc(title)}$2`)
    .replace(/(<meta property="og:description" content=")[^"]*(")/, `$1${esc(description)}$2`)
    .replace(/(<meta property="og:url" content=")[^"]*(")/, `$1${esc(url)}$2`)
    .replace(/(<meta property="og:type" content=")[^"]*(")/, `$1article$2`)
    .replace(/(<meta name="twitter:title" content=")[^"]*(")/, `$1${esc(title)}$2`)
    .replace(/(<meta name="twitter:description" content=")[^"]*(")/, `$1${esc(description)}$2`)
    .replace(/(<link rel="canonical" href=")[^"]*(")/, `$1${esc(url)}$2`);
  const dest = resolve(outDir, 'audit', slug, 'index.html');
  mkdirSync(dirname(dest), { recursive: true }); writeFileSync(dest, htmlOut); n++;
}
console.log(`[prerender] ${n} páginas /audit/* generadas en ${outDir}`);
