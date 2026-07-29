import fs from 'fs';
import path from 'path';
import { execFile } from 'child_process';
import util from 'util';

const execFileAsync = util.promisify(execFile);
const SRC_DIR = path.resolve('./src');
const RAW_SCRIPT = path.join(SRC_DIR, 'raw_script.json');
const OUT_SCRIPT = path.join(SRC_DIR, 'script.json');
const PUBLIC_DIR = path.resolve('./public');

if (!fs.existsSync(PUBLIC_DIR)) {
  fs.mkdirSync(PUBLIC_DIR);
}

async function getAudioDuration(filePath) {
  // Use afinfo to get duration precisely
  const { stdout } = await execFileAsync('afinfo', [filePath]);
  const durationMatch = stdout.match(/estimated duration: ([\d.]+) sec/);
  if (durationMatch && durationMatch[1]) {
    return parseFloat(durationMatch[1]);
  }
  return 0;
}

async function processScript() {
  const rawData = JSON.parse(fs.readFileSync(RAW_SCRIPT, 'utf-8'));
  const processed = [];

  for (let i = 0; i < rawData.length; i++) {
    const scene = rawData[i];
    const text = scene.text;
    const aiffPath = path.join(PUBLIC_DIR, `audio_${i}.aiff`);
    const wavPath = path.join(PUBLIC_DIR, `audio_${i}.wav`);

    console.log(`Processing scene ${i}...`);
    // C5-REAL Anti-Command-Injection: use execFile with flat arguments
    await execFileAsync('say', ['-v', 'Monica', '-r', '160', '-o', aiffPath, text]);

    // Convert to wav using ffmpeg for web/Remotion compatibility
    // Anti-m4a trap: use .wav
    await execFileAsync('ffmpeg', ['-y', '-i', aiffPath, wavPath]);

    // Clean up aiff
    fs.unlinkSync(aiffPath);

    const durationSeconds = await getAudioDuration(wavPath);
    const durationFrames = Math.ceil(durationSeconds * 30); // assuming 30fps

    // Word-level sync approximation
    const words = text.split(/\s+/);
    const framesPerWord = durationFrames / words.length;
    const timestamps = words.map((word, idx) => ({
      word,
      startFrame: Math.floor(idx * framesPerWord),
      endFrame: Math.floor((idx + 1) * framesPerWord),
    }));

    processed.push({
      ...scene,
      audioFile: `/audio_${i}.wav`,
      durationFrames,
      timestamps,
    });
  }

  fs.writeFileSync(OUT_SCRIPT, JSON.stringify(processed, null, 2));
  console.log(`Crystallized ${processed.length} scenes to script.json`);
}

processScript().catch(console.error);
