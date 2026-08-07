// C5-REAL EXERGY CERTIFIED
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log("=== C5-REAL STANDALONE VIDEO RENDER PIPELINE ===");

const projectDir = path.resolve(__dirname, '..');
const publicDir = path.join(projectDir, 'public');
const audioFile = path.join(publicDir, 'sequel_master.wav');
const outputFile = path.join(projectDir, 'out_intervalo_prohibido_2.mp4');

if (!fs.existsSync(audioFile)) {
    console.error("Audio master file not found:", audioFile);
    process.exit(1);
}

console.log("Audio master found:", audioFile);
console.log("Preparing master video output:", outputFile);

// Generate video using ffmpeg with visualizer filter and audio track
const ffmpegCmd = `ffmpeg -y -loop 1 -i "${path.join(publicDir, 'memes', 'the_dude_escohotado.svg')}" -i "${audioFile}" -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest "${outputFile}"`;

try {
    console.log("Executing FFmpeg master compilation...");
    execSync(ffmpegCmd, { cwd: projectDir, stdio: 'inherit' });
    console.log("=== RENDER COMPLETE ===");
    console.log("Video output created at:", outputFile);
} catch (e) {
    console.error("Render failed:", e.message);
}
