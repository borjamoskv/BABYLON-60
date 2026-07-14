import os
import io
import numpy as np
import soundfile as sf
import librosa
from whisper import load_model

class SpeechToText:
    """Wrapper around Whisper for low‑latency partial transcription.
    The model is loaded once; `transcribe_partial` can be called repeatedly on
    growing audio buffers.
    """

    def __init__(self, model_name: str = "base"):
        # Whisper model names: tiny, base, small, medium, large
        self.model = load_model(model_name)
        self.sample_rate = 16000

    def _preprocess(self, audio_bytes: bytes) -> np.ndarray:
        audio, sr = sf.read(io.BytesIO(audio_bytes))
        if sr != self.sample_rate:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=self.sample_rate)
        return audio.astype(np.float32)

    def transcribe_partial(self, audio_bytes: bytes) -> str:
        """Return best‑guess transcript for the current buffer.
        Whisper is invoked with language detection disabled for speed.
        """
        audio = self._preprocess(audio_bytes)
        options = dict(language="es", without_timestamps=True, fp16=True)
        result = self.model.transcribe(audio, **options)
        return result["text"].strip()
