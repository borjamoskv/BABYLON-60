#!/usr/bin/env node
/**
 * ═══════════════════════════════════════════════════════════════════════
 * MOSKV CREATIVE DIRECTOR — Autonomous LLM-as-Director Pipeline v1.0
 * ═══════════════════════════════════════════════════════════════════════
 *
 * Implements the "LLM-as-director -> specialist models" design pattern:
 *   1. Reads a source script (e.g. guion_notebooklm_borja.md).
 *   2. Queries Gemini 3.5 Flash to act as Creative Director, outputting a
 *      structured JSON storyboard with image prompts, durations, and effects.
 *   3. Attempts to generate high-fidelity visual assets via Imagen 4.0.
 *   4. Falls back to generating elegant Industrial Noir placeholder images via
 *      ffmpeg if the API key lacks paid Imagen credentials.
 *   5. Emits a manifest for pipeline.js and executes it.
 *
 * Nivel de realidad: C5-REAL (Gemini orchestration / FFmpeg generation).
 *
 * @author MOSKV-1 / Antigravity
 * @license SOVEREIGN
 */

import { execSync, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, writeFileSync, readFileSync, readdirSync } from "node:fs";
import { join, resolve, dirname, extname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

// ═══════════════════════════════════════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════════════════════════════════════

function log(level, msg) {
  const ts = new Date().toISOString().slice(11, 19);
  const prefix = { info: "▸", ok: "✓", warn: "⚠", err: "✗", step: "◆" };
  console.log(`  ${prefix[level] || "·"} [${ts}] ${msg}`);
}

// ═══════════════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════════════

const NOIR_PALETTE = {
  bg: "#0A0A0A",
  primary: "#2B3BE5",
  accent: "#FFB800",
  text: "#E0E0E0",
};

// ═══════════════════════════════════════════════════════════════════════
// MAIN PIPELINE
// ═══════════════════════════════════════════════════════════════════════

async function main() {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    log("err", "GEMINI_API_KEY environment variable is not defined.");
    process.exit(1);
  }

  const args = process.argv.slice(2);
  const scriptPath = args[0] || resolve(__dirname, "../guion_notebooklm_borja.md");
  const presetArg = args[1] || "widescreen"; // test, reel, loop, widescreen

  console.log(`
  ╔═══════════════════════════════════════════════════════════╗
  ║   MOSKV CREATIVE DIRECTOR — Autonomous Orchestrator v1.0 ║
  ║   LLM-as-Director -> Specialist Assets                   ║
  ╚═══════════════════════════════════════════════════════════╝
  `);

  if (!existsSync(scriptPath)) {
    log("err", `Script file not found: ${scriptPath}`);
    process.exit(1);
  }
  log("ok", `Loaded script source: ${scriptPath}`);

  const scriptContent = readFileSync(scriptPath, "utf-8");

  // Define the schema for Gemini structured output
  const responseSchema = {
    type: "OBJECT",
    properties: {
      title: { type: "STRING", description: "Title of the video project" },
      preset: { type: "STRING", description: "Video preset: test, reel, loop, widescreen" },
      duration: { type: "INTEGER", description: "Total duration in seconds" },
      theme: { type: "STRING", description: "Global visual theme/mood" },
      scenes: {
        type: "ARRAY",
        description: "Array of scenes mapping out the visual storyboard",
        items: {
          type: "OBJECT",
          properties: {
            narration: { type: "STRING", description: "Spoken voiceover script for the scene" },
            duration: { type: "INTEGER", description: "Duration in seconds for this scene" },
            imagePrompt: { type: "STRING", description: "Detailed, photorealistic prompt for generating a noir style visual asset. Describe the lighting, composition, camera angle, and subject." },
            overlayText: { type: "STRING", description: "Short textual callout/overlay for the scene" },
            effects: {
              type: "ARRAY",
              items: { type: "STRING" },
              description: "Visual effects list: kenburns, scanlines, grain, glitch, vignette"
            }
          },
          required: ["narration", "duration", "imagePrompt", "overlayText", "effects"]
        }
      }
    },
    required: ["title", "preset", "duration", "theme", "scenes"]
  };

  const systemPrompt = `
You are the Creative Director (Gemini 3) in a three-model video generation pipeline.
Your job is to read the user's raw script and deconstruct it into a visual storyboard manifest.
Keep the aesthetic STRICTLY: Industrial Noir 2026 — colors: #0A0A0A (background), #2B3BE5 (primary blue), high contrast, raw industrial texture, technical blueprint overlay accents.
Map the scenes to the user's script content. Each scene must be coherent.
Target preset: ${presetArg}.
Ensure the sum of scene durations matches the preset duration:
- test: 5 seconds (1-2 scenes)
- loop: 15 seconds (2-3 scenes)
- reel: 30 seconds (3-5 scenes)
- widescreen: 60 seconds (5-8 scenes)
`;

  log("step", "Querying Gemini 3.5 Flash as Creative Director...");

  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key=${apiKey}`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      contents: [{
        parts: [
          { text: systemPrompt },
          { text: `Raw Script Content:\n\n${scriptContent}` }
        ]
      }],
      generationConfig: {
        responseMimeType: "application/json",
        responseSchema: responseSchema,
        temperature: 0.2
      }
    })
  });

  if (!response.ok) {
    const errorText = await response.text();
    log("err", `Gemini API call failed: ${errorText}`);
    process.exit(1);
  }

  const result = await response.json();
  const rawText = result.candidates[0].content.parts[0].text;
  const storyboard = JSON.parse(rawText.trim());

  log("ok", "Storyboard structured successfully!");
  log("info", `Title: "${storyboard.title}"`);
  log("info", `Theme: ${storyboard.theme}`);
  log("info", `Total Scenes: ${storyboard.scenes.length}`);

  // Create output directory
  const outputDir = join(__dirname, "output");
  if (!existsSync(outputDir)) {
    mkdirSync(outputDir, { recursive: true });
  }

  // Iterate over scenes and generate/mock assets
  const images = [];
  log("step", "Beginning asset generation lifecycle...");

  for (let i = 0; i < storyboard.scenes.length; i++) {
    const scene = storyboard.scenes[i];
    const imgName = `scene_${String(i).padStart(2, "0")}.png`;
    const imgPath = join(outputDir, imgName);

    log("info", `Scene ${i}: "${scene.overlayText}" (${scene.duration}s)`);
    log("info", `Prompt: "${scene.imagePrompt}"`);

    // Try generating image via Imagen 4.0
    let generated = false;
    try {
      const imgUrl = `https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key=${apiKey}`;
      const imgResponse = await fetch(imgUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          instances: [{ prompt: `${scene.imagePrompt}, industrial noir style, #0A0A0A base with #2B3BE5 accents` }],
          parameters: { sampleCount: 1, aspectRatio: presetArg === "reel" ? "9:16" : "16:9" }
        })
      });

      const imgData = await imgResponse.json();
      if (imgResponse.ok && imgData.predictions?.[0]?.bytesBase64Encoded) {
        const base64 = imgData.predictions[0].bytesBase64Encoded;
        writeFileSync(imgPath, Buffer.from(base64, "base64"));
        log("ok", `Generated via Imagen 4.0: ${imgName}`);
        generated = true;
      } else {
        // Log paid tier restriction message or schema mismatch
        const msg = imgData.error?.message || "Billing restriction / Free plan limit";
        log("warn", `Imagen API skipped: ${msg}`);
      }
    } catch (err) {
      log("warn", `Imagen generation error: ${err.message}`);
    }

    // Fallback: Generate custom premium industrial noir visual placeholder via python (PIL)
    if (!generated) {
      log("info", `Deploying placeholder asset generator for Scene ${i} (C4-SIMULACIÓN)...`);
      const width = presetArg === "reel" ? 1080 : 1920;
      const height = presetArg === "reel" ? 1920 : 1080;

      const scriptPath = join(__dirname, "generate_placeholder.py");
      const res = spawnSync("python3", [
        scriptPath,
        "--output", imgPath,
        "--text", scene.overlayText,
        "--width", String(width),
        "--height", String(height)
      ]);

      if (res.status === 0) {
        log("ok", `Created placeholder: ${imgName}`);
      } else {
        log("err", `Python placeholder generation failed: ${res.stderr?.toString()}`);
        process.exit(1);
      }
    }

    images.push(imgPath);
  }

  // Find default audio in the directory if available
  const parentAssets = discoverAudio(resolve(__dirname, ".."));
  const audioFile = parentAssets[0] || null;

  // Build the pipeline.js compatible manifest
  const pipelinePreset = presetArg === "widescreen" || presetArg === "reel" || presetArg === "loop" || presetArg === "test" ? presetArg : "widescreen";
  
  const manifest = {
    version: "1.0.0",
    created: new Date().toISOString(),
    pipeline: "MOSKV Creative Director Orchestrator",
    preset: pipelinePreset,
    source: resolve(__dirname, ".."),
    assets: {
      images: images,
      audio: audioFile,
    },
    output: {
      directory: outputDir,
    },
    storyboard: storyboard
  };

  const manifestPath = join(outputDir, "director_manifest.json");
  writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
  log("ok", `Manifest emitted: ${manifestPath}`);

  // Run the render pipeline
  log("step", "Starting pipeline.js rendering...");
  const pipelineScript = join(__dirname, "pipeline.js");
  const renderArgs = ["pipeline.js", "--preset", pipelinePreset, "--manifest", manifestPath];
  
  const render = spawnSync("node", renderArgs, { cwd: __dirname, stdio: "inherit" });
  if (render.status === 0) {
    log("ok", "Video render complete!");
  } else {
    log("err", `Render pipeline execution failed with exit code ${render.status}`);
  }
}

function discoverAudio(dir) {
  const audExts = new Set([".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac"]);
  const audio = [];
  try {
    const files = readdirSync(dir);
    for (const file of files) {
      if (audExts.has(extname(file).toLowerCase())) {
        audio.push(join(dir, file));
      }
    }
  } catch {}
  return audio;
}

main().catch((err) => {
  log("err", err.stack || err.message);
  process.exit(1);
});
