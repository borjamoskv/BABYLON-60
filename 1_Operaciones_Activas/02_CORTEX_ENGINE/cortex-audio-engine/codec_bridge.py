# C5-REAL EXERGY CERTIFIED
import torch
import torchaudio
import dac
import os

class C5RealCodecBridge:
    """
    [Primitive 02] Descript Audio Codec (DAC) Bridge.
    Inyecta el puente entre el mundo físico (PCM a 44.1kHz) y la topología espacial discreta (RVQ).
    """
    def __init__(self, model_type="44khz", device=None):
        self.device = device if device else ("mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
        print(f"[CORTEX] Cargando DAC {model_type} en modo térmico: {self.device}")

        # Descarga de pesos determinista (Zero-Grad)
        model_path = dac.utils.download(model_type=model_type)
        self.model = dac.DAC.load(model_path).to(self.device)
        self.model.eval() # Fricción Cero, no se entrena el codec.
        self.sample_rate = 44100

    @torch.no_grad()
    def pcm_to_latent(self, audio_path):
        """
        Convierte audio crudo en un tensor continuo Z (espacio sin cuantizar)
        o en los códigos discretos (RVQ). Para Flow Matching usaremos los latentes continuos.
        """
        signal, sr = torchaudio.load(audio_path)

        # Resampleo incondicional si la base no encaja
        if sr != self.sample_rate:
            resampler = torchaudio.transforms.Resample(sr, self.sample_rate)
            signal = resampler(signal)

        # Convertir a mono físico si es estéreo para evitar desalineación de fase inicial
        if signal.shape[0] > 1:
            signal = torch.mean(signal, dim=0, keepdim=True)

        signal = signal.to(self.device).unsqueeze(0) # [1, 1, T]

        # Extracción latente
        z, codes, latents, _, _ = self.model.encode(signal)
        return z # [1, Dim, T_latent]

    @torch.no_grad()
    def latent_to_pcm(self, z, output_path):
        """
        Colapso del tensor Z hacia una onda acústica PCM física.
        """
        audio_tensor = self.model.decode(z)
        audio_tensor = audio_tensor.squeeze(0).cpu() # [1, T]

        torchaudio.save(output_path, audio_tensor, self.sample_rate)
        print(f"[CORTEX] Audio inyectado físicamente en: {output_path}")

# SYS_ID: borjamoskv
# Nivel: C5-REAL
