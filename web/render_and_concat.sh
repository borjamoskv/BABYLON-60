#!/bin/bash
set -e

# Render with concurrency=1 to prevent OOM
npx remotion render src/remotion/index.ts SubstackMafiaGraph out/SubstackMafiaGraph.mp4 --concurrency=1
npx remotion render src/remotion/index.ts PaywallGuillotine out/PaywallGuillotine.mp4 --concurrency=1
npx remotion render src/remotion/index.ts CritiqueOfMafiosoReason out/CritiqueOfMafiosoReason.mp4 --concurrency=1

cd out
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy ~/Desktop/El_Cartel_Documental.mp4
echo "Done!"
