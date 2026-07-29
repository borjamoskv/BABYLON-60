import { execFile } from 'child_process';
import util from 'util';
import path from 'path';
import fs from 'fs';

const execFileAsync = util.promisify(execFile);
const SRC_DIR = path.resolve('./src');

async function runAutonomousLoop() {
  console.log('[MOSKV-STUDIO] Iniciando Forja de Video Autónoma (Economía de la Atención)...');

  // Paso 1: Orquestación TTS
  console.log('[MOSKV-STUDIO] [1/3] Sintetizando Estado de Audio y Sincronización BFT...');
  await execFileAsync('node', ['build_state.mjs']);

  // Paso 2: Renderizado Remotion Offthread
  console.log('[MOSKV-STUDIO] [2/3] Renderizando Composición (Remotion SOTA)...');
  const outPath = path.resolve('./out/CortexImperial.mp4');

  if (!fs.existsSync(path.dirname(outPath))) {
    fs.mkdirSync(path.dirname(outPath), { recursive: true });
  }

  // Se renderiza el composition 'CortexImperial'
  await execFileAsync('npx', ['remotion', 'render', 'CortexImperial', outPath]);

  console.log(`[MOSKV-STUDIO] Renderizado completado en: ${outPath}`);

  // Paso 3: Subida a YouTube (Simulación API/Orquestación)
  console.log('[MOSKV-STUDIO] [3/3] Desplegando en YouTube (Simulación Autónoma)...');
  // Aquí se invocaría la API de Google / YouTube v3 con el auth de OAuth2
  // await execFileAsync('python3', ['scripts/youtube_uploader.py', '--file', outPath]);

  console.log('[MOSKV-STUDIO] ✅ Ciclo Autónomo Completado. Exergía extraída.');
}

runAutonomousLoop().catch(err => {
  console.error('[MOSKV-STUDIO] Falla Termodinámica en el pipeline autónomo:', err);
  process.exit(1);
});
