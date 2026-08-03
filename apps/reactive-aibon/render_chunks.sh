#!/bin/bash
set -e

# Purgamos anergía previa
rm -rf out/chunks
mkdir -p out/chunks

echo "[*] Iniciando Fase 1: 0-3000"
npx remotion render src/index.ts AibonReactive out/chunks/chunk_1.mp4 --frames=0-3000 --concurrency=10 --scale=0.25 --gl=angle --crf=30 --preset=ultrafast

echo "[*] Iniciando Fase 2: 3001-6000"
npx remotion render src/index.ts AibonReactive out/chunks/chunk_2.mp4 --frames=3001-6000 --concurrency=10 --scale=0.25 --gl=angle --crf=30 --preset=ultrafast

echo "[*] Iniciando Fase 3: 6001-9000"
npx remotion render src/index.ts AibonReactive out/chunks/chunk_3.mp4 --frames=6001-9000 --concurrency=10 --scale=0.25 --gl=angle --crf=30 --preset=ultrafast

echo "[*] Iniciando Fase 4: 9001-12505"
npx remotion render src/index.ts AibonReactive out/chunks/chunk_4.mp4 --frames=9001-12505 --concurrency=10 --scale=0.25 --gl=angle --crf=30 --preset=ultrafast

echo "[*] Stitching Final (FFmpeg concat)"
echo "file 'chunk_1.mp4'" > out/chunks/list.txt
echo "file 'chunk_2.mp4'" >> out/chunks/list.txt
echo "file 'chunk_3.mp4'" >> out/chunks/list.txt
echo "file 'chunk_4.mp4'" >> out/chunks/list.txt

ffmpeg -y -f concat -safe 0 -i out/chunks/list.txt -c copy out/video.mp4

echo "[*] Exergy cristalizada en out/video.mp4"
