# C5-REAL EXERGY CERTIFIED
#!/bin/bash
cd /Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/moby-remix/separated/htdemucs/source

ffmpeg -y \
  -i vocals.wav \
  -i drums.wav \
  -i bass.wav \
  -i other.wav \
  -filter_complex "
    [0:a]asetrate=44100*0.85,aresample=44100,aecho=0.8:0.8:1000:0.4,volume=1.2[v];
    [1:a]asetrate=44100*0.85,aresample=44100,lowpass=f=3500,volume=0.9[d];
    [2:a]asetrate=44100*0.85,aresample=44100,aecho=0.8:0.8:500:0.2,volume=1.0[b];
    [3:a]asetrate=44100*0.8749,aresample=44100,atempo=0.9715,aecho=0.8:0.8:1500:0.5,volume=1.0[o];
    [v][d][b][o]amix=inputs=4:duration=longest,volume=1.5[out]
  " \
  -map "[out]" \
  ../../../porcelain-remix/public/remix_audio_microtonal.mp3
