// C5-REAL EXERGY CERTIFIED - REMOTION FULL RENDERER
const { bundle } = require("@remotion/bundler");
const { renderMedia, selectComposition } = require("@remotion/renderer");
const path = require("path");
const fs = require("fs");

async function main() {
  console.log("=== REMOTION FULL REACT COMPOSITION RENDERER ===");
  const entryPoint = path.resolve(__dirname, "../src/index.ts");
  const outputLocation = path.resolve(__dirname, "../out_intervalo_prohibido_2.mp4");

  console.log("1. Bundling React Remotion Composition from:", entryPoint);
  const bundled = await bundle({
    entryPoint,
    webpackOverride: (config) => config,
  });

  console.log("2. Selecting composition 'IntervaloProhibido2'...");
  const composition = await selectComposition({
    serveUrl: bundled,
    id: "IntervaloProhibido2",
  });

  console.log(`Composition found! Duration: ${composition.durationInFrames} frames (${composition.fps} FPS), Resolution: ${composition.width}x${composition.height}`);

  console.log("3. Rendering full MP4 video with subtitles, memes, and audio...");
  await renderMedia({
    composition,
    serveUrl: bundled,
    codec: "h264",
    outputLocation,
    audioBitrate: "256k",
    onProgress: ({ progress, renderedFrames, totalFrames }) => {
      if (renderedFrames % 100 === 0 || progress === 1) {
        console.log(`Render Progress: ${(progress * 100).toFixed(1)}% (${renderedFrames}/${totalFrames} frames)`);
      }
    },
  });

  console.log("=== REMOTION FULL REACT RENDER COMPLETE ===");
  console.log("Video output created at:", outputLocation);
}

main().catch((err) => {
  console.error("Remotion render error:", err);
  process.exit(1);
});
