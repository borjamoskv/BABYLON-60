// C5-REAL EXERGY CERTIFIED
const { bundle } = require("@remotion/bundler");
const { renderMedia, selectComposition } = require("@remotion/renderer");
const path = require("path");

async function start() {
  console.log("Bundling Remotion project...");
  const entryPoint = path.join(__dirname, "../src/index.ts");
  const bundled = await bundle({
    entryPoint,
    webpackOverride: (config) => config,
  });

  const compositionId = "IntervaloProhibido2";
  console.log("Selecting composition:", compositionId);
  const composition = await selectComposition({
    serveUrl: bundled,
    id: compositionId,
  });

  const outputPath = path.join(__dirname, "../out_intervalo_prohibido_2.mp4");
  console.log("Rendering media to:", outputPath);

  await renderMedia({
    composition,
    serveUrl: bundled,
    codec: "h264",
    outputLocation: outputPath,
    audioBitrate: "256k",
    concurrency: 1,
  });

  console.log("=== RENDER REMOTION COMPLETO EXITOSO ===");
  console.log("Output video created at:", outputPath);
}

start().catch((err) => {
  console.error("Render failed:", err);
  process.exit(1);
});
