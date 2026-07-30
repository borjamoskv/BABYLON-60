import numpy as np
import soundfile as sf
import os

def main():
    base_dir = "/Users/borjafernandezangulo/Documents/antigravity/lively-maxwell/remix_project"
    stems_dir = os.path.join(base_dir, "htdemucs", "source_video")
    
    print("Loading stems into numpy arrays...")
    vocals, sr = sf.read(os.path.join(stems_dir, "vocals.wav"))
    other, _ = sf.read(os.path.join(stems_dir, "other.wav"))
    drums, _ = sf.read(os.path.join(stems_dir, "drums.wav"))
    bass, _ = sf.read(os.path.join(stems_dir, "bass.wav"))
    
    # Calculate indices
    fade_in_samples = 2 * sr
    intro_samples = 10 * sr
    
    print("Processing Intro (0s-10s)...")
    # Intro (0 to 10s)
    intro_vocals = vocals[:intro_samples].copy()
    intro_other = other[:intro_samples].copy()
    
    # Check bounds
    fade_in_actual = min(fade_in_samples, len(intro_vocals))
    
    # Fade in linear
    if intro_vocals.ndim == 2:
        fade_curve = np.linspace(0, 1, fade_in_actual)[:, None]
    else:
        fade_curve = np.linspace(0, 1, fade_in_actual)
        
    intro_vocals[:fade_in_actual] *= fade_curve
    intro_other[:fade_in_actual] *= fade_curve
    
    intro_mix = intro_vocals + intro_other
    
    print("Processing Drop (10s onwards) with MLX Hardware Acceleration...")
    # Drop (10s onwards)
    drop_vocals = vocals[intro_samples:].copy()
    drop_other = other[intro_samples:].copy()
    drop_drums = drums[intro_samples:].copy()
    drop_bass = bass[intro_samples:].copy()
    
    # The lengths might differ slightly if the files differ, truncate to min_len
    min_len = min(len(drop_vocals), len(drop_other), len(drop_drums), len(drop_bass))
    drop_vocals = drop_vocals[:min_len]
    drop_other = drop_other[:min_len]
    drop_drums = drop_drums[:min_len]
    drop_bass = drop_bass[:min_len]

    # MLX Acceleration for tensor math (C5-REAL Silicon Optimization)
    try:
        import mlx.core as mx
        # Move arrays to Apple Unified Memory GPU
        v_mx = mx.array(drop_vocals)
        o_mx = mx.array(drop_other)
        d_mx = mx.array(drop_drums)
        b_mx = mx.array(drop_bass)
        
        # Panning logic (reduce right channel)
        if len(o_mx.shape) == 2 and o_mx.shape[1] == 2:
            left = o_mx[:, 0:1]
            right = o_mx[:, 1:2] * 0.5
            o_mx = mx.concatenate([left, right], axis=1)
            
        # Boost bass by 4dB (1.58)
        b_mx = b_mx * 1.58
        
        drop_mix_mx = v_mx + o_mx + d_mx + b_mx
        
        # Evaluate lazily executed graph and retrieve as numpy
        mx.eval(drop_mix_mx)
        drop_mix = np.array(drop_mix_mx)
        print("[+] MLX Tensor compilation & execution complete.")
        
    except ImportError:
        print("[-] MLX no detectado. Cayendo a fallback sincrónico en CPU (numpy).")
        # Fallback numpy logic
        if drop_other.ndim == 2 and drop_other.shape[1] == 2:
            drop_other[:, 1] *= 0.5
        drop_bass *= 1.58
        drop_mix = drop_vocals + drop_other + drop_drums + drop_bass
    
    print("Concatenating and rendering...")
    final_mix = np.concatenate((intro_mix, drop_mix))
    
    # Fade out last 5 seconds
    fade_out_samples = 5 * sr
    if len(final_mix) > fade_out_samples:
        if final_mix.ndim == 2:
            fade_curve_out = np.linspace(1, 0, fade_out_samples)[:, None]
        else:
            fade_curve_out = np.linspace(1, 0, fade_out_samples)
        final_mix[-fade_out_samples:] *= fade_curve_out
    
    # Normalize to prevent clipping
    max_val = np.max(np.abs(final_mix))
    if max_val > 1.0:
        final_mix /= max_val
    
    output_path = os.path.join(base_dir, "remix_output.wav")
    print(f"Exporting to {output_path}...")
    sf.write(output_path, final_mix, sr)
    print("Export complete.")

if __name__ == "__main__":
    main()
