#!/usr/bin/env python3
"""
================================================================================
BABYLON-60 | BALAG-60: SOVEREIGN ACOUSTIC & PHYSICAL RESONATOR ENGINE
Pipeline de Síntesis Acústica Exergética, Afinaciones No Temperadas y Ritmos Euclidianos
================================================================================

Misión:
1. Generación de afinaciones no temperadas en formato canónico Scala (.scl) y ratios
   puros de Just Intonation (5-limit/7-limit), Pitagóricos (3-limit) y Armónicos Sexagesimales.
2. Cálculo de la Matriz de Ritmo Euclidiano E(k, n) mediante el algoritmo de Bjorklund
   con evaluación de entropía de Shannon sobre intervalos inter-pulso.
3. Síntesis DSP de resonadores modales físicos y excitadores transitorios no lineales
   a 48.000 Hz / 16-bit PCM estéreo.
4. Aplicación estricta de RULE[music_assets_centralization_invariant]:
   Centralización directa y enlace simbólico canónico en ~/Music/BALAG60_ACOUSTICS
   (con alias compatible ~/Music/BABYLON60_ACOUSTICS).
"""

from __future__ import annotations

import os
import sys
import json
import math
import hashlib
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Tuple, Any

import numpy as np
import scipy.io.wavfile as wavfile

# Configuración de Logging de Alta Exergía
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [BALAG-60:DSP] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)

# Constantes Fundacionales
SAMPLE_RATE = 48000
ROOT_HZ_CANONIC = 216.0  # Frecuencia base sexagesimal (60 * 3.6 Hz, C3+ Just Intonation)
TEMPO_BPM = 108.0       # Tempo sexagesimal (108 BPM = 1.8 Hz pulso base)


# ==============================================================================
# 1. ESCALAS NO TEMPERADAS & FORMATO SCALA (.SCL)
# ==============================================================================

@dataclass
class ScalaScale:
    name: str
    description: str
    note_entries: List[str]     # Formato Scala: ratio (ej. "9/8") o cents (ej. "203.91000")
    cents: List[float]
    ratios: List[float]

    @property
    def num_notes(self) -> int:
        return len(self.note_entries)

    def to_scl_content(self) -> str:
        """Compila la escala al formato estándar de Manuel Op de Coul (.scl)."""
        lines = [
            f"! {self.name}.scl",
            "!",
            self.description.strip(),
            str(self.num_notes),
            "!",
        ]
        for entry in self.note_entries:
            lines.append(entry)
        return "\n".join(lines) + "\n"

    def save(self, destination: Path) -> Path:
        """Persiste el archivo .scl en disco."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(self.to_scl_content(), encoding="utf-8")
        return destination

    def get_frequencies(self, root_hz: float = ROOT_HZ_CANONIC) -> List[float]:
        """Obtiene las frecuencias fundamentales de cada grado (incluyendo unísono)."""
        return [root_hz] + [root_hz * r for r in self.ratios]


def ratio_to_cents(ratio: float) -> float:
    return 1200.0 * math.log2(ratio)


def build_just_intonation_12() -> ScalaScale:
    """Escala cromática Just Intonation de 12 notas (Límites 5 y 7 de alta consonancia)."""
    raw_ratios = [
        ("16/15", 16 / 15),  # Semitono diatónico
        ("9/8", 9 / 8),      # Tono entero mayor
        ("6/5", 6 / 5),      # Tercera menor justa
        ("5/4", 5 / 4),      # Tercera mayor pura (386.31 cents)
        ("4/3", 4 / 3),      # Cuarta justa
        ("7/5", 7 / 5),      # Tritono septimal de Euler
        ("3/2", 3 / 2),      # Quinta justa perfecta
        ("8/5", 8 / 5),      # Sexta menor justa
        ("5/3", 5 / 3),      # Sexta mayor justa
        ("7/4", 7 / 4),      # Séptima armónica pura (968.83 cents)
        ("15/8", 15 / 8),    # Séptima mayor sensible
        ("2/1", 2.0 / 1.0),  # Octava pura
    ]
    entries = [r[0] for r in raw_ratios]
    ratios = [r[1] for r in raw_ratios]
    cents = [ratio_to_cents(r) for r in ratios]
    return ScalaScale(
        name="babylon60_just_intonation_12",
        description="Babylon-60 12-Tone Just Intonation (5/7-Limit Harmonic Ratios)",
        note_entries=entries,
        cents=cents,
        ratios=ratios
    )


def build_pythagorean_12() -> ScalaScale:
    """Escala de afinación Pitagórica de 12 notas basada en el ciclo puro de quintas 3/2."""
    raw_ratios = [
        ("256/243", 256 / 243),
        ("9/8", 9 / 8),
        ("32/27", 32 / 27),
        ("81/64", 81 / 64),
        ("4/3", 4 / 3),
        ("729/512", 729 / 512),
        ("3/2", 3 / 2),
        ("128/81", 128 / 81),
        ("27/16", 27 / 16),
        ("16/9", 16 / 9),
        ("243/128", 243 / 128),
        ("2/1", 2.0 / 1.0),
    ]
    entries = [r[0] for r in raw_ratios]
    ratios = [r[1] for r in raw_ratios]
    cents = [ratio_to_cents(r) for r in ratios]
    return ScalaScale(
        name="pythagorean_12",
        description="Pythagorean 12-Tone Scale (3-Limit Circle of Pure Fifths)",
        note_entries=entries,
        cents=cents,
        ratios=ratios
    )


def build_babylon_sexagesimal_harmonics() -> ScalaScale:
    """
    Afinación Sexagesimal ENKI-60 basada en armónicos primos del retículo de 60 (2, 3, 5).
    Ratios exactos de alta exergía armónica.
    """
    raw_ratios = [
        ("16/15", 16 / 15),
        ("9/8", 9 / 8),
        ("6/5", 6 / 5),
        ("5/4", 5 / 4),
        ("4/3", 4 / 3),
        ("45/32", 45 / 32),
        ("3/2", 3 / 2),
        ("8/5", 8 / 5),
        ("5/3", 5 / 3),
        ("9/5", 9 / 5),
        ("15/8", 15 / 8),
        ("2/1", 2.0 / 1.0),
    ]
    entries = [r[0] for r in raw_ratios]
    ratios = [r[1] for r in raw_ratios]
    cents = [ratio_to_cents(r) for r in ratios]
    return ScalaScale(
        name="babylon60_sexagesimal_harmonics",
        description="Babylon-60 ENKI-60 Sexagesimal Lattice Pure Harmonics",
        note_entries=entries,
        cents=cents,
        ratios=ratios
    )


# ==============================================================================
# 2. ALGORITMO DE BJORKLUND & MATRIZ DE RITMOS EUCLIDIANOS E(k, n)
# ==============================================================================

class BjorklundEuclidean:
    """Implementación formal del algoritmo euclidiano de Bjorklund (Toussaint 2005)."""

    @staticmethod
    def generate(k: int, n: int) -> List[int]:
        """Calcula el vector de ritmo euclidiano E(k, n) distribuyendo k pulsos en n pasos."""
        if k <= 0:
            return [0] * n
        if k >= n:
            return [1] * n

        head: List[List[int]] = [[1] for _ in range(k)]
        tail: List[List[int]] = [[0] for _ in range(n - k)]

        while len(tail) > 0:
            m = min(len(head), len(tail))
            new_head = [head[i] + tail[i] for i in range(m)]
            new_tail = head[m:] if len(head) > len(tail) else tail[m:]
            head = new_head
            tail = new_tail
            if len(tail) <= 1:
                break

        res: List[int] = []
        for seq in head:
            res.extend(seq)
        for seq in tail:
            res.extend(seq)
        return res

    @staticmethod
    def calculate_shannon_entropy(pattern: List[int]) -> float:
        """
        Calcula la entropía de Shannon H sobre la distribución de intervalos
        temporales entre onsets consecutivos.
        """
        onsets = [i for i, val in enumerate(pattern) if val == 1]
        if len(onsets) <= 1:
            return 0.0

        n = len(pattern)
        intervals = []
        for i in range(len(onsets)):
            next_idx = (i + 1) % len(onsets)
            intv = (onsets[next_idx] - onsets[i]) % n
            if intv == 0:
                intv = n
            intervals.append(intv)

        # Distribución de probabilidad
        total = len(intervals)
        counts: Dict[int, int] = {}
        for d in intervals:
            counts[d] = counts.get(d, 0) + 1

        entropy = 0.0
        for count in counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        return round(entropy, 4)

    @staticmethod
    def to_visual_grid(matrix_dict: Dict[str, List[int]]) -> str:
        """Genera un render visual ASCII de la matriz polirrítmica euclidiana."""
        lines = []
        max_name_len = max(len(k) for k in matrix_dict.keys())
        for name, pattern in matrix_dict.items():
            symbols = "".join([" [■] " if p == 1 else "  ·  " for p in pattern])
            lines.append(f"{name.ljust(max_name_len)} : {symbols}")
        return "\n".join(lines)


# ==============================================================================
# 3. MOTOR DE SÍNTESIS ACÚSTICA EXERGÉTICA (DSP MODAL & TRANSIENTES)
# ==============================================================================

class AcousticExergySynthesizer:
    """
    Sintetizador DSP basado en modelos físicos de resonadores modales
    y excitación acústica no lineal.
    """

    def __init__(self, sample_rate: int = SAMPLE_RATE) -> None:
        self.sr = sample_rate

    def synth_modal_resonator(
        self,
        freq: float,
        duration: float,
        decay_tau: float = 0.45,
        modes: Tuple[Tuple[float, float, float], ...] = (
            (1.0, 1.0, 1.0),      # (ratio_freq, amp, decay_mult)
            (2.756, 0.4, 0.6),    # Modo inarmónico de campana/barra acústica
            (5.404, 0.15, 0.35),  # Modo superior amortiguado
            (8.933, 0.05, 0.18),  # Brillo metálico / cerámico
        ),
        transient_noise_ms: float = 4.0,
    ) -> np.ndarray:
        """
        Sintetiza una cuerda pulsada o lámina modal acústica afinada a 'freq'.
        """
        num_samples = int(self.sr * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)
        signal = np.zeros(num_samples, dtype=np.float32)

        # Modos resonantes amortiguados exponencialmente
        for f_mult, amp, d_mult in modes:
            m_freq = freq * f_mult
            if m_freq >= self.sr * 0.48:
                continue
            tau = decay_tau * d_mult
            mode_sig = amp * np.sin(2.0 * np.pi * m_freq * t) * np.exp(-t / max(tau, 0.005))
            signal += mode_sig

        # Excitador transitorio (burst de impacto)
        noise_samples = int(self.sr * (transient_noise_ms / 1000.0))
        if noise_samples > 0 and noise_samples <= num_samples:
            noise = np.random.uniform(-1.0, 1.0, noise_samples).astype(np.float32)
            noise_env = np.exp(-np.linspace(0, 5.0, noise_samples))
            signal[:noise_samples] += 0.25 * noise * noise_env

        # Envolvente anti-clic de ataque (2 ms)
        attack_len = int(self.sr * 0.002)
        if attack_len < num_samples:
            signal[:attack_len] *= np.linspace(0.0, 1.0, attack_len)

        return signal

    def synth_bass_pulse(self, freq: float = 54.0, duration: float = 0.6) -> np.ndarray:
        """Sintetiza un pulso acústico percusivo de sub-grave (kick acústico)."""
        num_samples = int(self.sr * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)
        # Caída de pitch exponencial para emular la elasticidad de membrana
        f_pitch = freq + 70.0 * np.exp(-t / 0.035)
        phase = 2.0 * np.pi * np.cumsum(f_pitch) / self.sr
        envelope = np.exp(-t / 0.22)
        sig = np.sin(phase) * envelope
        # Transiente de golpe
        click_len = int(self.sr * 0.005)
        sig[:click_len] += 0.4 * np.sin(2.0 * np.pi * 320.0 * t[:click_len]) * np.linspace(1, 0, click_len)
        return sig.astype(np.float32)

    def synth_crotale_transient(self, freq: float = 1728.0, duration: float = 0.25) -> np.ndarray:
        """Sintetiza un transiente acústico metálico brillante (crotale / campana pequeña)."""
        num_samples = int(self.sr * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)
        sig = (
            0.6 * np.sin(2.0 * np.pi * freq * t) * np.exp(-t / 0.06)
            + 0.3 * np.sin(2.0 * np.pi * (freq * 1.583) * t) * np.exp(-t / 0.04)
            + 0.2 * np.sin(2.0 * np.pi * (freq * 2.314) * t) * np.exp(-t / 0.02)
        )
        return sig.astype(np.float32)

    def spatialize_stereo(self, mono_sig: np.ndarray, pan: float = 0.0) -> np.ndarray:
        """
        Aplica paneo estéreo de ley de potencia constante (-1.0 izq, 0.0 centro, +1.0 der).
        """
        pan = np.clip(pan, -1.0, 1.0)
        angle = (pan + 1.0) * (np.pi / 4.0)
        gain_l = np.cos(angle)
        gain_r = np.sin(angle)
        stereo = np.zeros((len(mono_sig), 2), dtype=np.float32)
        stereo[:, 0] = mono_sig * gain_l
        stereo[:, 1] = mono_sig * gain_r
        return stereo

    def render_euclidean_microtonal_groove(
        self,
        scale: ScalaScale,
        e_kick: List[int],
        e_melody: List[int],
        e_crotale: List[int],
        tempo_bpm: float = TEMPO_BPM,
        bars: int = 4,
    ) -> np.ndarray:
        """
        Renderiza una obra polirrítmica completa acoplando los ritmos euclidianos
        con las frecuencias no temperadas de la escala Scala.
        """
        steps_per_bar = len(e_kick)  # Generalmente 16 pasos
        total_steps = steps_per_bar * bars
        step_duration = 60.0 / (tempo_bpm * 4.0)  # Duración de una semicorchea (16th note)
        total_duration = (total_steps * step_duration) + 2.0  # +2s de reverb/decay ringout
        total_samples = int(self.sr * total_duration)

        master_buffer = np.zeros((total_samples, 2), dtype=np.float32)
        freqs = scale.get_frequencies(root_hz=ROOT_HZ_CANONIC)

        melody_step_idx = 0
        crotale_step_idx = 0

        for step in range(total_steps):
            step_time = step * step_duration
            start_idx = int(step_time * self.sr)

            # Capa 1: Pulso de Bajo Acústico (E_kick)
            kick_val = e_kick[step % len(e_kick)]
            if kick_val == 1:
                kick_sig = self.synth_bass_pulse(freq=54.0, duration=0.55) * 0.75
                k_stereo = self.spatialize_stereo(kick_sig, pan=0.0)
                end_idx = min(start_idx + len(kick_sig), total_samples)
                master_buffer[start_idx:end_idx] += k_stereo[: end_idx - start_idx]

            # Capa 2: Resonadores Modales Microtonales (E_melody)
            mel_val = e_melody[step % len(e_melody)]
            if mel_val == 1:
                # Selección determinista no temperada
                freq = freqs[melody_step_idx % len(freqs)]
                melody_step_idx += 1
                pan = 0.5 * math.sin(step * 0.785)  # Paneo dinámico sinusoidal
                resonator_sig = self.synth_modal_resonator(
                    freq=freq,
                    duration=1.2,
                    decay_tau=0.55,
                    transient_noise_ms=3.0
                ) * 0.55
                r_stereo = self.spatialize_stereo(resonator_sig, pan=pan)
                end_idx = min(start_idx + len(resonator_sig), total_samples)
                master_buffer[start_idx:end_idx] += r_stereo[: end_idx - start_idx]

            # Capa 3: Crotale / Metal Transiente (E_crotale polirrítmico)
            crot_val = e_crotale[step % len(e_crotale)]
            if crot_val == 1:
                pan_crot = -0.6 if (crotale_step_idx % 2 == 0) else 0.6
                crotale_step_idx += 1
                crot_sig = self.synth_crotale_transient(freq=1728.0, duration=0.25) * 0.28
                c_stereo = self.spatialize_stereo(crot_sig, pan=pan_crot)
                end_idx = min(start_idx + len(crot_sig), total_samples)
                master_buffer[start_idx:end_idx] += c_stereo[: end_idx - start_idx]

        # Normalización estricta a -0.5 dBFS para evitar anergía por distorsión digital
        peak = np.max(np.abs(master_buffer))
        if peak > 0:
            target_peak = 10.0 ** (-0.5 / 20.0)  # ~0.944
            master_buffer = (master_buffer / peak) * target_peak

        return (master_buffer * 32767.0).astype(np.int16)

    def render_pure_just_intonation_drone(
        self,
        scale: ScalaScale,
        duration: float = 6.0,
    ) -> np.ndarray:
        """
        Sintetiza un acorde sostenido puro en Just Intonation (Tónica 1/1, Tercera Mayor 5/4,
        Quinta Justa 3/2, Séptima Armónica 7/4) para evidenciar la ausencia de batimientos
        de fase (máxima exergía consonante).
        """
        num_samples = int(self.sr * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)
        stereo = np.zeros((num_samples, 2), dtype=np.float32)

        # Tríada/Tétrada pura de armónicos
        chord_ratios = [1.0, 5 / 4, 3 / 2, 7 / 4]
        pans = [-0.4, 0.3, -0.2, 0.4]
        amps = [0.45, 0.35, 0.35, 0.25]

        # Envolvente suave de campana / drone
        envelope = np.sin(np.pi * np.linspace(0, 1, num_samples)) ** 1.2

        for r, pan, amp in zip(chord_ratios, pans, amps):
            f = ROOT_HZ_CANONIC * r
            # Fundamental + armónico puro 2x
            voice = amp * (
                np.sin(2.0 * np.pi * f * t) +
                0.25 * np.sin(2.0 * np.pi * (f * 2.0) * t)
            ) * envelope
            stereo += self.spatialize_stereo(voice, pan=pan)

        peak = np.max(np.abs(stereo))
        if peak > 0:
            stereo = (stereo / peak) * (10.0 ** (-1.0 / 20.0))

        return (stereo * 32767.0).astype(np.int16)


# ==============================================================================
# 4. GESTOR DE CENTRALIZACIÓN DE ACTIVOS MUSICALES (~/Music/)
# ==============================================================================

class MusicAssetsCentralizer:
    """
    Garante de RULE[music_assets_centralization_invariant]:
    Centraliza todos los artefactos de audio, presets y escalas directamente
    en ~/Music/BALAG60_ACOUSTICS (con alias ~/Music/BABYLON60_ACOUSTICS).
    """

    def __init__(self, local_output_dir: Path) -> None:
        self.local_dir = local_output_dir.resolve()
        self.canonical_music_dir = Path.home() / "Music"
        self.balag_symlink = self.canonical_music_dir / "BALAG60_ACOUSTICS"
        self.legacy_symlink = self.canonical_music_dir / "BABYLON60_ACOUSTICS"

    def _link_path(self, target_link: Path) -> str:
        if target_link.is_symlink():
            if target_link.resolve() != self.local_dir:
                target_link.unlink()
                target_link.symlink_to(self.local_dir, target_is_directory=True)
                return "updated"
            return "already_configured"
        elif target_link.exists():
            return "path_already_exists_as_regular_file"
        else:
            target_link.symlink_to(self.local_dir, target_is_directory=True)
            return "created"

    def ensure_centralization(self) -> Dict[str, Any]:
        """Crea el directorio y asegura los enlaces simbólicos en ~/Music/."""
        self.local_dir.mkdir(parents=True, exist_ok=True)
        self.canonical_music_dir.mkdir(parents=True, exist_ok=True)

        balag_status = self._link_path(self.balag_symlink)
        legacy_status = self._link_path(self.legacy_symlink)

        verified_readable = self.balag_symlink.exists() and self.balag_symlink.is_dir()

        return {
            "local_storage_dir": str(self.local_dir),
            "canonical_symlink": str(self.balag_symlink),
            "legacy_symlink": str(self.legacy_symlink),
            "balag_status": balag_status,
            "legacy_status": legacy_status,
            "verified_readable": verified_readable,
        }


# ==============================================================================
# 5. PIPELINE PRINCIPAL Y EJECUCIÓN
# ==============================================================================

def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def run_pipeline() -> Dict[str, Any]:
    logging.info("Inicializando Agente 9 (Acoustic DSP Synthesizer) - BABYLON-60...")

    repo_root = Path(__file__).resolve().parent.parent.parent
    local_output_dir = repo_root / "data" / "c5_acoustics"

    centralizer = MusicAssetsCentralizer(local_output_dir)
    centralization_info = centralizer.ensure_centralization()
    logging.info(f"Frontera ~/Music verificada: {centralization_info['canonical_symlink']}")

    # 1. Afinaciones no temperadas (Scala format .scl)
    logging.info("Sintetizando escalas no temperadas y presets .scl...")
    scales = [
        build_just_intonation_12(),
        build_pythagorean_12(),
        build_babylon_sexagesimal_harmonics(),
    ]

    saved_scl_files = []
    for sc in scales:
        dest = local_output_dir / f"{sc.name}.scl"
        sc.save(dest)
        saved_scl_files.append({
            "name": sc.name,
            "path": str(dest),
            "notes": sc.num_notes,
            "sha256": compute_sha256(dest),
        })
        logging.info(f"Preset Scala compilado: {dest.name} ({sc.num_notes} grados)")

    # 2. Cálculo de la Matriz de Ritmo Euclidiano E(k, n)
    logging.info("Calculando matrices de ritmo euclidiano (Bjorklund E(k, n))...")
    bj = BjorklundEuclidean()

    e_patterns = {
        "E(4,16)_Fundamento": bj.generate(4, 16),
        "E(7,16)_Modal_Bells": bj.generate(7, 16),
        "E(11,24)_Polymeter_Crotales": bj.generate(11, 24),
        "E(5,12)_Syncopated_Mid": bj.generate(5, 12),
        "E(3,8)_Tresillo_Canonico": bj.generate(3, 8),
    }

    pattern_metrics = {}
    for name, pat in e_patterns.items():
        entropy = bj.calculate_shannon_entropy(pat)
        onsets_count = sum(pat)
        pattern_metrics[name] = {
            "pattern": pat,
            "pulses": onsets_count,
            "steps": len(pat),
            "density": round(onsets_count / len(pat), 4),
            "shannon_entropy": entropy,
        }

    grid_ascii = bj.to_visual_grid({
        "E(4,16) Fundamento": e_patterns["E(4,16)_Fundamento"],
        "E(7,16) Bells     ": e_patterns["E(7,16)_Modal_Bells"],
        "E(5,12) Syncop    ": e_patterns["E(5,12)_Syncopated_Mid"],
        "E(3,8)  Tresillo  ": e_patterns["E(3,8)_Tresillo_Canonico"],
    })

    # 3. Síntesis DSP Acústica
    logging.info("Ejecutando síntesis DSP estéreo a 48.000 Hz...")
    synth = AcousticExergySynthesizer(sample_rate=SAMPLE_RATE)

    # Obra 1: Groove Polirrítmico Euclidiano Microtonal
    audio_groove = synth.render_euclidean_microtonal_groove(
        scale=scales[0],  # Just Intonation 12
        e_kick=e_patterns["E(4,16)_Fundamento"],
        e_melody=e_patterns["E(7,16)_Modal_Bells"],
        e_crotale=e_patterns["E(11,24)_Polymeter_Crotales"],
        tempo_bpm=TEMPO_BPM,
        bars=4,
    )
    groove_wav_path = local_output_dir / "poc_euclidean_microtonal_groove.wav"
    wavfile.write(str(groove_wav_path), SAMPLE_RATE, audio_groove)
    logging.info(f"Render acústico finalizado: {groove_wav_path.name}")

    # Obra 2: Drone Puro Just Intonation (Consonancia de fase)
    audio_drone = synth.render_pure_just_intonation_drone(scale=scales[0], duration=5.0)
    drone_wav_path = local_output_dir / "poc_just_intonation_consonance_drone.wav"
    wavfile.write(str(drone_wav_path), SAMPLE_RATE, audio_drone)
    logging.info(f"Drone consonante finalizado: {drone_wav_path.name}")

    # 4. Telemetría y Sitrep
    sitrep = {
        "agent": "BALAG-60 (Sovereign Acoustic Resonator & Physical DSP Engine)",
        "framework": "BABYLON-60 C5-REAL",
        "centralization": centralization_info,
        "sample_rate_hz": SAMPLE_RATE,
        "root_frequency_hz": ROOT_HZ_CANONIC,
        "tempo_bpm": TEMPO_BPM,
        "scales": saved_scl_files,
        "euclidean_patterns": pattern_metrics,
        "rendered_audio_assets": [
            {
                "file": groove_wav_path.name,
                "path": str(groove_wav_path),
                "duration_s": round(len(audio_groove) / SAMPLE_RATE, 3),
                "channels": 2,
                "sha256": compute_sha256(groove_wav_path),
                "size_bytes": groove_wav_path.stat().st_size,
            },
            {
                "file": drone_wav_path.name,
                "path": str(drone_wav_path),
                "duration_s": round(len(audio_drone) / SAMPLE_RATE, 3),
                "channels": 2,
                "sha256": compute_sha256(drone_wav_path),
                "size_bytes": drone_wav_path.stat().st_size,
            },
        ],
    }

    sitrep_path = local_output_dir / "acoustic_sitrep.json"
    sitrep_path.write_text(json.dumps(sitrep, indent=2), encoding="utf-8")
    logging.info(f"Sitrep acústico persistido: {sitrep_path.name}")

    # Confirmar visibilidad a través de ~/Music/BALAG60_ACOUSTICS
    music_symlink = Path(centralization_info["canonical_symlink"])
    centralized_files = [f.name for f in music_symlink.iterdir()] if music_symlink.exists() else []

    print("\n" + "=" * 80)
    print(" [ BABYLON-60 ] BALAG-60: MOTOR ACÚSTICO & RESONADOR FÍSICO SOBERANO")
    print("=" * 80)
    print(f"[*] Repositorio Local:  {local_output_dir}")
    print(f"[*] Enlace Canónico:    {centralization_info['canonical_symlink']}")
    print(f"[*] Enlace Compatible:  {centralization_info['legacy_symlink']}")
    print(f"[*] Activos en ~/Music: {centralized_files}")
    print("\n[+] MATRIZ POLIRRÍTMICA EUCLIDIANA (Bjorklund):")
    print(grid_ascii)
    print("\n[+] AFINACIONES NO TEMPERADAS (.SCL):")
    for s in saved_scl_files:
        print(f"  - {s['name']}.scl : {s['notes']} grados | SHA-256: {s['sha256'][:16]}...")
    print("\n[+] ARCHIVOS DE AUDIO MASTERIZADOS (48 kHz / 16-bit):")
    for a in sitrep["rendered_audio_assets"]:
        print(f"  - {a['file']} : {a['duration_s']}s | {a['size_bytes'] / 1024:.1f} KB")
    print("=" * 80 + "\n")

    return sitrep


if __name__ == "__main__":
    run_pipeline()
