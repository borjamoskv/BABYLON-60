import os
import sys
import math
import wave
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

def load_audio_envelope(wav_path, target_fps=30, total_frames=7200):
    """
    Extracts frame-by-frame audio energy metrics (sub-bass, mid, high, peak)
    from 48kHz WAV audio for sound-reactive visual animation.
    """
    print(f"Analyzing audio waveform from {wav_path}...")
    with wave.open(wav_path, 'rb') as wf:
        sr = wf.getframerate()
        n_channels = wf.getnchannels()
        n_frames = wf.getnframes()
        raw_bytes = wf.readframes(n_frames)
        
    audio = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    if n_channels > 1:
        audio = 0.5 * (audio[0::2] + audio[1::2])  # Downmix to mono for analysis
        
    samples_per_frame = sr // target_fps
    
    amplitudes = np.zeros(total_frames, dtype=np.float32)
    sub_bass = np.zeros(total_frames, dtype=np.float32)
    mid_energy = np.zeros(total_frames, dtype=np.float32)
    high_energy = np.zeros(total_frames, dtype=np.float32)
    
    # Simple FFT per frame to extract frequency band energy
    fft_size = 2048
    freqs = np.fft.rfftfreq(fft_size, d=1.0/sr)
    
    sub_mask = (freqs >= 20) & (freqs <= 120)
    mid_mask = (freqs > 120) & (freqs <= 2000)
    high_mask = (freqs > 2000) & (freqs <= 16000)
    
    for f in range(total_frames):
        start_idx = f * samples_per_frame
        end_idx = min(start_idx + fft_size, len(audio))
        chunk = audio[start_idx:end_idx]
        
        if len(chunk) < fft_size:
            chunk = np.pad(chunk, (0, fft_size - len(chunk)))
            
        # RMS amplitude
        rms = np.sqrt(np.mean(chunk**2))
        amplitudes[f] = rms
        
        # FFT spectrum
        spec = np.abs(np.fft.rfft(chunk * np.hanning(fft_size)))
        sub_bass[f] = np.mean(spec[sub_mask]) if np.any(sub_mask) else 0.0
        mid_energy[f] = np.mean(spec[mid_mask]) if np.any(mid_mask) else 0.0
        high_energy[f] = np.mean(spec[high_mask]) if np.any(high_mask) else 0.0

    # Normalize metrics to [0.0, 1.0] range
    def norm_array(arr):
        mx = np.max(arr)
        return arr / mx if mx > 0 else arr

    return {
        "rms": norm_array(amplitudes),
        "sub": norm_array(sub_bass),
        "mid": norm_array(mid_energy),
        "high": norm_array(high_energy)
    }

def render_cosmic_video():
    project_dir = "/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/apps/cosmic_avant_garde_video"
    wav_path = os.path.join(project_dir, "assets/cosmic_avant_garde_suite.wav")
    img1_path = os.path.join(project_dir, "assets/cosmic_quantum_manifold.png")
    img2_path = os.path.join(project_dir, "assets/event_horizon_bifurcation.png")
    out_mp4 = os.path.join(project_dir, "out/cosmic_avant_garde_video_4min.mp4")
    
    width, height = 1920, 1080
    fps = 30
    duration_sec = 240
    total_frames = fps * duration_sec  # 7200 frames
    
    # Load audio envelope
    audio_data = load_audio_envelope(wav_path, target_fps=fps, total_frames=total_frames)
    
    # Load background images
    bg1 = Image.open(img1_path).convert("RGB")
    bg2 = Image.open(img2_path).convert("RGB")
    
    # Pre-generate orbital starfield particle coordinates
    np.random.seed(42)
    num_particles = 180
    particle_r = np.random.uniform(120, 450, num_particles)
    particle_theta = np.random.uniform(0, 2 * np.pi, num_particles)
    particle_speed = np.random.uniform(0.005, 0.025, num_particles)
    particle_size = np.random.uniform(2, 6, num_particles)
    
    # Try loading a clean font, or default
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        font_subtitle = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
        font_time = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        font_hud = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except Exception:
        font_title = ImageFont.load_default()
        font_subtitle = font_title
        font_time = font_title
        font_hud = font_title

    # FFmpeg pipe command
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{width}x{height}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",  # Pipe input from stdin
        "-i", wav_path,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "320k",
        "-shortest",
        out_mp4
    ]
    
    print(f"Launching FFmpeg video pipe rendering to {out_mp4} ({total_frames} frames)...")
    pipe = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    
    center_x, center_y = width // 2, height // 2

    for frame in range(total_frames):
        t = frame / fps
        
        # Audio energy at this frame
        rms_val = audio_data["rms"][frame]
        sub_val = audio_data["sub"][frame]
        mid_val = audio_data["mid"][frame]
        high_val = audio_data["high"][frame]
        
        # Determine background blend based on movement
        # Mov 1 (0-60s), Mov 2 (60-135s), Mov 3 (135-195s), Mov 4 (195-240s)
        if t < 130:
            blend_factor = 0.0
        elif 130 <= t <= 140:
            blend_factor = (t - 130) / 10.0  # Smooth transition to image 2
        elif 140 < t < 190:
            blend_factor = 1.0
        elif 190 <= t <= 200:
            blend_factor = 1.0 - (t - 190) / 10.0  # Transition back to image 1
        else:
            blend_factor = 0.0

        # Dynamic zoom & pan
        zoom = 1.0 + 0.15 * math.sin(t * 0.05) + 0.05 * sub_val
        angle = t * 0.4  # Slow rotation degrees
        
        # Base image crop & zoom
        if blend_factor <= 0.0:
            curr_bg = bg1
        elif blend_factor >= 1.0:
            curr_bg = bg2
        else:
            curr_bg = Image.blend(bg1, bg2, blend_factor)

        # Apply zoom & rotation via PIL
        w_crop = int(curr_bg.width / zoom)
        h_crop = int(curr_bg.height / zoom)
        left_c = (curr_bg.width - w_crop) // 2 + int(15 * math.cos(t * 0.1))
        top_c = (curr_bg.height - h_crop) // 2 + int(15 * math.sin(t * 0.1))
        
        cropped = curr_bg.crop((left_c, top_c, left_c + w_crop, top_c + h_crop)).resize((width, height), Image.Resampling.BILINEAR)
        
        if angle != 0:
            rotated = cropped.rotate(angle, resample=Image.Resampling.BILINEAR, expand=False)
        else:
            rotated = cropped

        # Canvas drawing overlay
        frame_img = rotated.copy()
        draw = ImageDraw.Draw(frame_img, "RGBA")
        
        # -------------------------------------------------------------
        # Sound-Reactive Quantum Event Horizon Ring
        # -------------------------------------------------------------
        base_radius = 160 + int(70 * sub_val + 30 * rms_val)
        
        # Outer glow rings
        for r_offset, alpha in [(30, 25), (20, 50), (10, 90)]:
            r = base_radius + r_offset
            color = (0, 220, 255, alpha) if t < 135 else (255, 0, 180, alpha)
            draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r], outline=color, width=3)
            
        # Core ring
        ring_color = (0, 240, 255, 220) if t < 135 else (255, 50, 200, 220)
        draw.ellipse([center_x - base_radius, center_y - base_radius, center_x + base_radius, center_y + base_radius], outline=ring_color, width=4)
        
        # Event Horizon Rays / Starburst
        num_rays = 24
        ray_length = 40 + int(120 * mid_val + 60 * sub_val)
        for i in range(num_rays):
            ray_angle = (i * (360 / num_rays) + t * 15) * (math.pi / 180.0)
            x1 = center_x + int((base_radius) * math.cos(ray_angle))
            y1 = center_y + int((base_radius) * math.sin(ray_angle))
            x2 = center_x + int((base_radius + ray_length) * math.cos(ray_angle))
            y2 = center_y + int((base_radius + ray_length) * math.sin(ray_angle))
            ray_col = (180, 240, 255, int(150 + 100 * high_val)) if i % 2 == 0 else (255, 180, 240, int(150 + 100 * high_val))
            draw.line([x1, y1, x2, y2], fill=ray_col, width=2)
            
        # -------------------------------------------------------------
        # Orbital Starfield Particles
        # -------------------------------------------------------------
        particle_theta += particle_speed * (1.0 + 2.0 * sub_val)
        for p in range(num_particles):
            pr = particle_r[p] * (1.0 + 0.1 * math.sin(t * 0.5 + p))
            pt = particle_theta[p]
            px = center_x + int(pr * math.cos(pt))
            py = center_y + int(pr * math.sin(pt))
            psize = particle_size[p] * (1.0 + 1.5 * high_val)
            p_alpha = int(120 + 130 * math.sin(t * 2.0 + p))
            p_col = (255, 255, 255, p_alpha) if p % 3 == 0 else (0, 220, 255, p_alpha)
            draw.ellipse([px - psize, py - psize, px + psize, py + psize], fill=p_col)

        # -------------------------------------------------------------
        # Motion Graphics HUD & Dynamic Typography
        # -------------------------------------------------------------
        # Top HUD Bar
        draw.rectangle([0, 0, width, 50], fill=(10, 10, 20, 180))
        draw.text((30, 14), "TEOREMA ROBINSON-MOSKV // C5-REAL AVANT-GARDE AUDIOVISUAL", fill=(0, 240, 255, 230), font=font_hud)
        
        # Audio Spectrum Bar Visualizer (32 Bands)
        num_bars = 32
        bar_w = 12
        bar_gap = 6
        start_x = (width - (num_bars * (bar_w + bar_gap))) // 2
        for b in range(num_bars):
            # Generate animated band height based on audio metrics
            band_phase = (b / num_bars) * math.pi
            b_height = int(15 + 80 * (rms_val * math.sin(band_phase) + sub_val * (1.0 - abs(b - 16)/16.0)))
            bx = start_x + b * (bar_w + bar_gap)
            by1 = height - 70
            by2 = by1 - b_height
            bar_col = (0, 220, 255, 200) if b < 16 else (255, 80, 200, 200)
            draw.rectangle([bx, by2, bx + bar_w, by1], fill=bar_col)
            
        # Movement Titles & Text Subtitles
        if t < 60:
            mov_title = "MOVEMENT I: SINGULARITY & MICROTONAL VACUUM"
            mov_sub = "Sub-bass Resonance (32 Hz) • 24-TET Microtonal Cluster • Resonant Wind"
        elif 60 <= t < 135:
            mov_title = "MOVEMENT II: QUANTUM PULSAR & GRANULAR STARLIGHT"
            mov_sub = "Generative Pulsar Rhythm (120 BPM) • Shepard-Risset Glissando • Shimmer Reverb"
        elif 135 <= t < 195:
            mov_title = "MOVEMENT III: EVENT HORIZON BIFURCATION"
            mov_sub = "High-Exergy FM Synthesis • Polyrhythmic Metallic Drop • Phase Bifurcation"
        else:
            mov_title = "MOVEMENT IV: ENTROPIC DRIFT & ZERO EXERGY RETURN"
            mov_sub = "Harmonic Overtones Decay • Spatial Overtones • Sub-frequency Dissolution"

        # Movement Banner Card
        card_w, card_h = 950, 80
        card_x = (width - card_w) // 2
        card_y = height - 170
        draw.rectangle([card_x, card_y, card_x + card_w, card_y + card_h], fill=(15, 15, 30, 210), outline=(0, 240, 255, 120), width=1)
        draw.text((card_x + 30, card_y + 12), mov_title, fill=(255, 255, 255, 240), font=font_subtitle)
        draw.text((card_x + 30, card_y + 45), mov_sub, fill=(0, 220, 255, 200), font=font_hud)

        # Timecode Display [MM:SS.FF / 04:00.00]
        mins = int(t) // 60
        secs = int(t) % 60
        frames_cur = int((t - int(t)) * fps)
        tc_str = f"[{mins:02d}:{secs:02d}.{frames_cur:02d} / 04:00.00]"
        draw.text((width - 320, 12), tc_str, fill=(255, 255, 255, 220), font=font_time)

        # Write frame bytes to FFmpeg stdin pipe
        pipe.stdin.write(frame_img.tobytes())
        
        if frame % 300 == 0 or frame == total_frames - 1:
            progress_pct = (frame / total_frames) * 100
            print(f"Rendering Progress: Frame {frame}/{total_frames} ({progress_pct:.1f}%) - Time: {mins:02d}:{secs:02d}")

    pipe.stdin.close()
    pipe.wait()
    print(f"\nVideo rendering complete! Output saved to: {out_mp4}")

if __name__ == '__main__':
    render_cosmic_video()
