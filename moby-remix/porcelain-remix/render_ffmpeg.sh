# C5-REAL EXERGY CERTIFIED
#!/bin/bash
cd /Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/moby-remix/porcelain-remix

mkdir -p out

ffmpeg -y \
  -i public/remix_video.mp4 \
  -i public/remix_audio_microtonal.mp3 \
  -filter_complex "
    [0:v]eq=contrast=1.2:saturation=1.5,hue=h=45,
    drawtext=text='PORCELAIN':fontcolor=white@0.8:fontsize=80:x=(w-text_w)/2:y=(h-text_h)/2-40:shadowcolor=black@0.5:shadowx=2:shadowy=2,
    drawtext=text='MICROTONAL COSMIC DOWNTEMPO':fontcolor=white@0.6:fontsize=30:x=(w-text_w)/2:y=(h-text_h)/2+60:shadowcolor=black@0.5:shadowx=2:shadowy=2[v]
  " \
  -map "[v]" -map 1:a \
  -c:v libx264 -preset fast -crf 22 \
  -c:a aac -b:a 192k \
  -shortest \
  out/Moby_Porcelain_Cosmic_Downtempo_Microtonal_Remix.mp4
