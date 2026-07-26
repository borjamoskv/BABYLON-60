# C5-REAL EXERGY CERTIFIED
import json
import numpy as np
import scipy
import scipy.io.wavfile as wav
from scipy.signal import butter, lfilter

SAMPLE_RATE = 44100
BPM = 128
BEATS_PER_SEC = BPM / 60.0
SEC_PER_BEAT = 1.0 / BEATS_PER_SEC
SEC_PER_BAR = SEC_PER_BEAT * 4
TOTAL_BARS = 32
TOTAL_LENGTH_SEC = TOTAL_BARS * SEC_PER_BAR

def normalize(audio):
    peak = np.max(np.abs(audio))
    if peak > 0:
        # -0.1 dB is approx 0.9885
        return audio * (10 ** (-0.1 / 20) / peak)
    return audio

def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype="low", analog=False)
    return b, a

def lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y

def butter_highpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype="high", analog=False)
    return b, a

def highpass_filter(data, cutoff, fs, order=5):
    b, a = butter_highpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y

def get_kick():
    length_sec = 0.5
    t = np.linspace(0, length_sec, int(SAMPLE_RATE * length_sec), endpoint=False)
    freq_sweep = np.exp(-t * 20) * (150 - 40) + 40
    phase = np.cumsum(freq_sweep * 2 * np.pi / SAMPLE_RATE)
    kick = np.sin(phase)
    env = np.exp(-t * 10)
    click = np.random.randn(len(t)) * np.exp(-t * 150)
    kick = (kick * env + click * 0.2) * 0.8
    return kick

def get_closed_hat():
    length_sec = 0.1
    t = np.linspace(0, length_sec, int(SAMPLE_RATE * length_sec), endpoint=False)
    noise = np.random.randn(len(t))
    noise = highpass_filter(noise, 6000, SAMPLE_RATE, order=3)
    env = np.exp(-t * 60)
    return noise * env * 0.4

def get_open_hat():
    length_sec = 0.3
    t = np.linspace(0, length_sec, int(SAMPLE_RATE * length_sec), endpoint=False)
    noise = np.random.randn(len(t))
    noise = highpass_filter(noise, 5000, SAMPLE_RATE, order=3)
    env = np.exp(-t * 15)
    return noise * env * 0.5

def get_snare():
    length_sec = 0.3
    t = np.linspace(0, length_sec, int(SAMPLE_RATE * length_sec), endpoint=False)
    tone = np.sin(2 * np.pi * 200 * t) * np.exp(-t * 20)
    noise = np.random.randn(len(t))
    noise = highpass_filter(noise, 1500, SAMPLE_RATE) * np.exp(-t * 25)
    return (tone * 0.3 + noise * 0.7) * 0.6

def generate_tone(freq, length_sec, shape="square"):
    t = np.linspace(0, length_sec, int(SAMPLE_RATE * length_sec), endpoint=False)
    if shape == "square":
        return np.sign(np.sin(2 * np.pi * freq * t))
    elif shape == "saw":
        return 2.0 * (t * freq - np.floor(0.5 + t * freq))
    elif shape == "sine":
        return np.sin(2 * np.pi * freq * t)

def get_bass_note(freq, length_sec=0.25):
    t = np.linspace(0, length_sec, int(SAMPLE_RATE * length_sec), endpoint=False)
    saw1 = generate_tone(freq, length_sec, "saw")
    saw2 = generate_tone(freq * 1.01, length_sec, "saw")  # Detune
    tone = (saw1 + saw2) * 0.5
    tone = lowpass_filter(tone, 800, SAMPLE_RATE, order=2)
    env = np.exp(-t * 8)
    return tone * env * 0.7

def get_chord(freqs, length_sec=0.3):
    t = np.linspace(0, length_sec, int(SAMPLE_RATE * length_sec), endpoint=False)
    chord = np.zeros(len(t))
    for f in freqs:
        chord += generate_tone(f, length_sec, "saw") + generate_tone(f, length_sec, "square")
    chord /= len(freqs)
    # LPF sweep env
    np.exp(-t * 4) * 3000 + 300
    # Apply time-varying filter roughly
    chord_filtered = lowpass_filter(chord, 1500, SAMPLE_RATE, order=2)  # Simplification
    env = np.exp(-t * 5)
    return chord_filtered * env * 0.4

# Create empty mix
t_total = np.linspace(0, TOTAL_LENGTH_SEC, int(SAMPLE_RATE * TOTAL_LENGTH_SEC), endpoint=False)
mix_l = np.zeros(len(t_total))
mix_r = np.zeros(len(t_total))

def add_to_mix(audio, start_sec, pan=0.0):
    start_idx = int(start_sec * SAMPLE_RATE)
    end_idx = start_idx + len(audio)
    if end_idx > len(mix_l):
        audio = audio[: len(mix_l) - start_idx]
        end_idx = len(mix_l)

    pan_l = np.cos((pan + 1) * np.pi / 4)
    pan_r = np.sin((pan + 1) * np.pi / 4)

    mix_l[start_idx:end_idx] += audio * pan_l
    mix_r[start_idx:end_idx] += audio * pan_r

# Drum elements
kick = get_kick()
ch = get_closed_hat()
oh = get_open_hat()
snare = get_snare()

# Bass notes
bass_freqs = {"D2": 73.42, "F2": 87.31, "G2": 98.00, "A2": 110.00, "C3": 130.81, "D3": 146.83}
chord_freqs_Dm9 = [146.83, 174.61, 220.00, 261.63, 329.63]  # D3, F3, A3, C4, E4

# Vocal chop
vocal_chop = np.zeros(int(SAMPLE_RATE * 0.25))
vocal_chop2 = np.zeros(int(SAMPLE_RATE * 0.25))
try:
    fs_orig, orig_audio = wav.read("original_audio.wav")
    if len(orig_audio.shape) > 1:
        orig_audio = np.mean(orig_audio, axis=1)
    # Just take an arbitrary segment for chop
    chop_start = int(fs_orig * 1.5)
    chop_len = int(fs_orig * 0.25)
    vocal_chop_raw = orig_audio[chop_start : chop_start + chop_len]
    if len(vocal_chop_raw) > 0:
        # Interpolate to sample rate and pitch up
        x = np.arange(len(vocal_chop_raw))
        x_new = np.linspace(0, len(vocal_chop_raw), int(SAMPLE_RATE * 0.25 * 1.2))  # Pitch up
        vocal_chop = np.interp(x_new, x, vocal_chop_raw)
        vocal_chop = vocal_chop[: int(SAMPLE_RATE * 0.25)]
        vocal_chop = vocal_chop / np.max(np.abs(vocal_chop)) * 0.5
        vocal_chop2 = vocal_chop[::-1]  # Reverse
except Exception as e:
    print(f"Could not load original audio: {e}")

# Sequence
for bar in range(TOTAL_BARS):
    bar_start = bar * SEC_PER_BAR

    # Structure logic
    # Bars 1-8: Intro (Kick + Hats + Vocal Chops)
    # Bars 9-16: Main Drop (Full Kick + Bassline + Chords + Hats + Snare)
    # Bars 17-24: Breakdown / Filtered Section (Chords + Vocal Chop + Rising Snare Roll)
    # Bars 25-32: Peak Drop (Full Drums + Driving Bassline + Chords + Vocal Chops)

    is_intro = bar < 8
    is_main_drop = 8 <= bar < 16
    is_breakdown = 16 <= bar < 24
    is_peak = 24 <= bar < 32

    # Drums
    if is_intro or is_main_drop or is_peak:
        for beat in range(4):
            beat_start = bar_start + beat * SEC_PER_BEAT
            add_to_mix(kick, beat_start)

            # Offbeat open hat
            add_to_mix(oh, beat_start + SEC_PER_BEAT * 0.5, pan=0.1)

            # Closed hats 16ths
            add_to_mix(ch, beat_start + SEC_PER_BEAT * 0.25, pan=-0.1)
            add_to_mix(ch, beat_start + SEC_PER_BEAT * 0.75, pan=-0.1)

            if is_main_drop or is_peak:
                if beat % 2 == 1:
                    add_to_mix(snare, beat_start)

    # Snare roll in breakdown
    if is_breakdown:
        roll_rate = 1
        if bar >= 20:
            roll_rate = 2
        if bar >= 22:
            roll_rate = 4
        if bar >= 23:
            roll_rate = 8
        step = SEC_PER_BEAT / roll_rate
        for i in np.arange(0, SEC_PER_BAR, step):
            vol = (bar - 16 + i / SEC_PER_BAR) / 8.0
            add_to_mix(snare * vol, bar_start + i)

    # Bassline
    if is_main_drop or is_peak:
        b1 = get_bass_note(bass_freqs["D2"])
        b2 = get_bass_note(bass_freqs["F2"])
        b3 = get_bass_note(bass_freqs["C3"])
        b4 = get_bass_note(bass_freqs["A2"])

        add_to_mix(b1, bar_start + SEC_PER_BEAT * 0.5)
        add_to_mix(b1, bar_start + SEC_PER_BEAT * 1.5)
        add_to_mix(b2, bar_start + SEC_PER_BEAT * 2.5)
        add_to_mix(b3, bar_start + SEC_PER_BEAT * 2.75)
        add_to_mix(b4, bar_start + SEC_PER_BEAT * 3.5)

    # Chords
    if is_main_drop or is_breakdown or is_peak:
        c1 = get_chord(chord_freqs_Dm9)
        vol = 0.5 if is_breakdown else 1.0
        # Syncopated rhythm
        add_to_mix(c1 * vol, bar_start + SEC_PER_BEAT * 1.5, pan=-0.2)
        add_to_mix(c1 * vol, bar_start + SEC_PER_BEAT * 2.5, pan=0.2)

    # Vocal chops
    if is_intro or is_peak or (is_breakdown and bar % 2 == 0):
        add_to_mix(vocal_chop, bar_start + SEC_PER_BEAT * 0.75, pan=0.3)
        add_to_mix(vocal_chop2, bar_start + SEC_PER_BEAT * 3.25, pan=-0.3)

# Mixdown & Master
mix_l = normalize(mix_l)
mix_r = normalize(mix_r)

stereo_mix = np.vstack((mix_l, mix_r)).T

# Convert to 16-bit PCM
audio_out = np.int16(stereo_mix * 32767)
wav.write("house_track.wav", SAMPLE_RATE, audio_out)

print("Exported house_track.wav")

# Generate FFT Data for Remotion
# Video is 30 FPS
fps = 30
frame_length_sec = 1.0 / fps
num_frames = int(TOTAL_LENGTH_SEC * fps)

audio_mono = (mix_l + mix_r) / 2.0

fft_data = []

def get_band_energy(freqs, Pxx, f_min, f_max):
    idx = np.logical_and(freqs >= f_min, freqs <= f_max)
    if not np.any(idx):
        return 0.0
    return float(np.sum(Pxx[idx]))

# Process frame by frame
for i in range(num_frames):
    start_sample = int(i * frame_length_sec * SAMPLE_RATE)
    end_sample = int((i + 1) * frame_length_sec * SAMPLE_RATE)

    frame_audio = audio_mono[start_sample:end_sample]
    if len(frame_audio) == 0:
        break

    window = np.hanning(len(frame_audio))
    f, Pxx = scipy.signal.welch(frame_audio * window, SAMPLE_RATE, nperseg=min(len(frame_audio), 1024))

    overall = float(np.mean(frame_audio**2))
    bass = get_band_energy(f, Pxx, 20, 250)
    mid = get_band_energy(f, Pxx, 250, 4000)
    treble = get_band_energy(f, Pxx, 4000, 20000)

    fft_data.append({"frame": i, "overall": overall, "bass": bass, "mid": mid, "treble": treble})

# Normalize FFT values for JSON output (0 to 1 range roughly for animation ease)
max_bass = max([d["bass"] for d in fft_data]) or 1.0
max_mid = max([d["mid"] for d in fft_data]) or 1.0
max_treble = max([d["treble"] for d in fft_data]) or 1.0
max_overall = max([d["overall"] for d in fft_data]) or 1.0

for d in fft_data:
    d["bass"] /= max_bass
    d["mid"] /= max_mid
    d["treble"] /= max_treble
    d["overall"] /= max_overall

with open("audio_data.json", "w") as f:
    json.dump(fft_data, f)

print("Exported audio_data.json")
