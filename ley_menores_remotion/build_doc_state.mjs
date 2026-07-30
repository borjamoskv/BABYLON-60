import fs from "node:fs/promises";
import path from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

const RAW_SCRIPT_PATH = path.resolve("./src/raw_script.json");
const OUTPUT_SCRIPT_PATH = path.resolve("./src/script.json");
const AUDIO_DIR = path.resolve("./public/audio");

async function main() {
  console.log("=== INICIANDO TRANSMUTACIÓN Y ORQUESTACIÓN TTS FISICA ===");
  await fs.mkdir(AUDIO_DIR, { recursive: true });

  const rawData = await fs.readFile(RAW_SCRIPT_PATH, "utf-8");
  const rawScript = JSON.parse(rawData);

  const FPS = rawScript.fps || 30;
  let currentFramePointer = 0;
  const compiledLines = [];

  for (const line of rawScript.lines) {
    const fileName = `scene_${line.id}.wav`;
    const audioFilePath = path.join(AUDIO_DIR, fileName);

    console.log(`[TTS] Generando escena ${line.id} (${line.speaker} / ${line.voice}): "${line.text.slice(0, 30)}..."`);

    // 1. Ejecución segura de macOS say mediante execFile (Anti-Command Injection - Skill Invariant)
    const sayArgs = [
      "-v", line.voice,
      "-r", String(line.rate || 175),
      "-o", audioFilePath,
      "--data-format=LEI16@44100",
      line.text
    ];

    await execFileAsync("say", sayArgs);

    // 2. Medición física de duración mediante afinfo
    const { stdout: afinfoOutput } = await execFileAsync("afinfo", [audioFilePath]);
    const durationMatch = afinfoOutput.match(/estimated duration:\s*([0-9.]+)\s*sec/);
    if (!durationMatch) {
      throw new Error(`No se pudo determinar la duración física con afinfo para ${audioFilePath}`);
    }

    const durationInSeconds = parseFloat(durationMatch[1]);
    const durationInFrames = Math.ceil(durationInSeconds * FPS);

    // 3. Generación matemática de marcas de tiempo palabra por palabra (Word-Level Timestamps)
    const words = line.text.split(/\s+/).filter(Boolean);
    const totalChars = words.reduce((acc, w) => acc + w.length, 0);

    let wordFrameOffset = 0;
    const wordTimestamps = words.map((word) => {
      const wordProportion = word.length / Math.max(1, totalChars);
      const wordDuration = Math.max(1, Math.round(wordProportion * durationInFrames));
      const startFrame = currentFramePointer + wordFrameOffset;
      const endFrame = startFrame + wordDuration;

      wordFrameOffset += wordDuration;

      return {
        word,
        startFrame,
        endFrame
      };
    });

    const startFrame = currentFramePointer;
    const endFrame = startFrame + durationInFrames;

    compiledLines.push({
      ...line,
      audioFile: `/audio/${fileName}`,
      durationInSeconds,
      durationInFrames,
      startFrame,
      endFrame,
      wordTimestamps
    });

    // Añadimos un pequeño margen de pausa entre intervenciones (15 frames = 0.5s)
    currentFramePointer = endFrame + 15;
  }

  const finalScript = {
    title: rawScript.title,
    fps: FPS,
    totalDurationInFrames: currentFramePointer,
    chapters: rawScript.chapters,
    lines: compiledLines
  };

  await fs.writeFile(OUTPUT_SCRIPT_PATH, JSON.stringify(finalScript, null, 2), "utf-8");
  console.log(`=== ORQUESTACIÓN CONCLUIDA CON ÉXITO ===`);
  console.log(`Duración total: ${currentFramePointer} frames (${(currentFramePointer / FPS / 60).toFixed(2)} minutos)`);
  console.log(`Script compilado sellado en: ${OUTPUT_SCRIPT_PATH}`);
}

main().catch((err) => {
  console.error("FATAL ERROR EN EL ORQUESTADOR TTS:", err);
  process.exit(1);
});
