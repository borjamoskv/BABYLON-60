# C5-REAL EXERGY CERTIFIED
import torch
from model import CortexAudioOmega
from codec_bridge import C5RealCodecBridge
import os

class InferenceEngine:
    """
    [Primitive 04 & 41] Euler ODE Solver + CFG.
    El colapso de la función de onda de ruido a señal física.
    """
    def __init__(self, checkpoint_path=None, device="mps"):
        self.device = device
        self.model = CortexAudioOmega().to(self.device)
        self.model.eval()

        if checkpoint_path and os.path.exists(checkpoint_path):
            self.model.load_state_dict(torch.load(checkpoint_path, map_location=self.device))

        self.codec = C5RealCodecBridge(device=self.device)

    @torch.no_grad()
    def generate(self, context_cond, context_uncond, steps=50, cfg_scale=7.5, output_path="output_c5_real.wav"):
        """
        Euler method para resolver la EDO de Flow Matching con CFG.
        context_cond: [B, L_text, C] - Prompt deseado.
        context_uncond: [B, L_text, C] - Prompt vacío para repulsión (Negative Prompt).
        """
        B = context_cond.shape[0]
        # Tensor Latente Inicial: Ruido termodinámico puro
        # Supongamos longitud latente L_audio = 1000 (aprox 10 segundos a 100Hz)
        L_audio = 1000
        dim_audio = 1024

        z = torch.randn((B, L_audio, dim_audio), device=self.device)

        # Pasos discretos de tiempo [0, 1]
        t_steps = torch.linspace(0, 1, steps, device=self.device)
        dt = 1.0 / steps

        print(f"[CORTEX] Iniciando colapso latente. Pasos: {steps}, CFG: {cfg_scale}")

        for i in range(steps):
            t = t_steps[i].unsqueeze(0).repeat(B)

            # Predicción Condicionada
            v_cond = self.model(z, t, context_cond)

            # Predicción Incondicionada (CFG)
            v_uncond = self.model(z, t, context_uncond)

            # [Primitive 41] Classifier-Free Guidance
            v_cfg = v_uncond + cfg_scale * (v_cond - v_uncond)

            # Paso Euler
            z = z + v_cfg * dt

        # El tensor z ahora es el latente de audio colapsado
        print("[CORTEX] Resolución ODE completada. Decodificando a PCM físico...")
        self.codec.latent_to_pcm(z.transpose(1,2), output_path)
        return output_path

# SYS_ID: borjamoskv
# Nivel: C5-REAL
