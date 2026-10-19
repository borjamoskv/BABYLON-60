#!/bin/bash
# ==============================================================================
# MANIFIESTO TOPOLÓGICO C5-REAL (V2 - SELF-HEALING)
# Síntesis Dialéctica: El Mapa (Transcript) no es el Territorio (Disco).
# Se aplica comprobación física antes de la mutación.
# ==============================================================================

set -e

USER_HOME="/Users/borjafernandezangulo"

echo "[*] 1. Reubicando Código Útil a Playgrounds..."
mkdir -p "$USER_HOME/10_PROJECTS/c5-playground"

# Función de mutación segura
safe_move() {
    if [ -e "$1" ]; then
        mv "$1" "$2"
        echo "  [+] Movido: $1 -> $2"
    else
        echo "  [-] Ignorado (No existe en territorio): $1"
    fi
}

safe_move "$USER_HOME/.gemini/antigravity/scratch/render_envido14.py" "$USER_HOME/10_PROJECTS/c5-playground/"
safe_move "$USER_HOME/.gemini/antigravity/scratch/test_c5_stress.c" "$USER_HOME/10_PROJECTS/c5-playground/"
safe_move "$USER_HOME/.gemini/antigravity/scratch/test_c5_stress" "$USER_HOME/10_PROJECTS/c5-playground/"
safe_move "$USER_HOME/.gemini/antigravity/scratch/test_c5_f5.c" "$USER_HOME/10_PROJECTS/c5-playground/"
safe_move "$USER_HOME/.gemini/antigravity/scratch/test_c5_f5" "$USER_HOME/10_PROJECTS/c5-playground/"

echo "[*] 2. Enlazando Activos Musicales (Zero-Breakage para Bundlers)..."
# Usamos -sfn para forzar la creación/actualización del enlace sin fallar
ln -sfn "$USER_HOME/10_PROJECTS/frases-sin-nata/video-engine/public/audio" "$USER_HOME/Music/frases-sin-nata-audio"
ln -sfn "$USER_HOME/10_PROJECTS/soulseek-agent/synthesized/Microtonal_House" "$USER_HOME/Music/Microtonal_House"
ln -sfn "$USER_HOME/99_CUARENTENA_TERMICA/25_BOCETOS/karpathy-remotion/public/audio.m4a" "$USER_HOME/Music/karpathy_remotion_audio.m4a"
ln -sfn "$USER_HOME/99_CUARENTENA_TERMICA/99_ARCHIVE/Teorema-Robinson-Moskv_HISTORICO/house_remotion_project/original_audio.wav" "$USER_HOME/Music/Teorema_Robinson_audio.wav"
echo "  [+] Enlaces simbólicos inyectados en ~/Music."

echo "[*] 3. Salvaguardando Archivo de Vídeos..."
mkdir -p "$USER_HOME/Movies/VIDEOS_MITICOS"
# Usamos find para mover de forma segura sin romper por globs vacíos
find "$USER_HOME/Downloads/VIDEOS_MITICOS" -mindepth 1 -maxdepth 1 -exec mv {} "$USER_HOME/Movies/VIDEOS_MITICOS/" \; 2>/dev/null || true
find "$USER_HOME/Downloads" -maxdepth 1 -name "ENVIDO*.mp4" -exec mv {} "$USER_HOME/Movies/VIDEOS_MITICOS/" \; 2>/dev/null || true
rmdir "$USER_HOME/Downloads/VIDEOS_MITICOS" 2>/dev/null || true
echo "  [+] Archivo visual asegurado."

echo "[*] TOPOLOGÍA ALINEADA (CLÍMAX ONTOLÓGICO ALCANZADO)."
