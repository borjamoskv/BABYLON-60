# C5-REAL EXERGY CERTIFIED
import torch
import torchaudio
import os
import math

class Base60AudioDataset(torch.utils.data.Dataset):
    """
    [Primitive 31 & 35] Ingesta Termodinámica Base-60.
    Alineación absoluta de chunks para evitar Jitter y deriva térmica.
    """
    def __init__(self, data_dir, sample_rate=44100, chunk_duration_ms=600):
        self.data_dir = data_dir
        self.sample_rate = sample_rate

        # El chunk de duración en Base-60 (múltiplos de 60, ej: 600ms)
        # Esto asegura que divisiones rítmicas de 120BPM caigan en enteros.
        if chunk_duration_ms % 60 != 0:
            raise ValueError("[FATAL] La duración del chunk debe ser divisible por 60 para evitar entropía rítmica.")

        self.chunk_samples = int((chunk_duration_ms / 1000.0) * self.sample_rate)

        self.files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.wav')]

        # Pre-cálculo de chunks disponibles para evitar lecturas IO estocásticas
        self.chunks_map = []
        for file_path in self.files:
            info = torchaudio.info(file_path)
            num_chunks = info.num_frames // self.chunk_samples
            for i in range(num_chunks):
                self.chunks_map.append((file_path, i * self.chunk_samples))

        print(f"[CORTEX] Dataset inicializado. {len(self.chunks_map)} matrices temporales descubiertas en Base-60.")

    def __len__(self):
        return len(self.chunks_map)

    def __getitem__(self, idx):
        file_path, start_frame = self.chunks_map[idx]

        # Extracción determinista O(1) de memoria
        waveform, sr = torchaudio.load(
            file_path,
            frame_offset=start_frame,
            num_frames=self.chunk_samples
        )

        # Si por alguna razón el sample rate biológico no coincide, abortar
        if sr != self.sample_rate:
            raise RuntimeError(f"[FATAL] Sample rate mismatch en {file_path}. Esperado {self.sample_rate}, recibido {sr}.")

        # Convertir a mono físico si es estéreo
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)

        # Devolver el tensor [1, T_samples]
        # (Posteriormente pasará por codec_bridge.py antes del Transformer)
        return waveform

# SYS_ID: borjamoskv
# Nivel: C5-REAL
