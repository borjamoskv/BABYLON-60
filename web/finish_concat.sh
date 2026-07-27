#!/bin/bash
set -e

# Render the last missing video (PaywallGuillotine) with concurrency=1
npx remotion render src/remotion/index.ts PaywallGuillotine out/PaywallGuillotine.mp4 --concurrency=1

# Run ffmpeg to concatenate
cd out
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy ~/Desktop/El_Cartel_Documental.mp4
echo "Concatenation complete! Desktop file created."
