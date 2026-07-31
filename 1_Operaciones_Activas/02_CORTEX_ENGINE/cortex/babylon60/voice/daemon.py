# C5-REAL EXERGY CERTIFIED
"""Cortex Voice Daemon for VAD (Voice Activity Detection) and hardware acoustic capture."""
import time
import logging
import math
import struct
try:
    import pyaudio
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False

class VoiceDaemon:
    def __init__(self, sample_rate=16000, chunk_size=1024, energy_threshold=300):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.energy_threshold = energy_threshold
        self._running = False
        self.logger = logging.getLogger("VoiceDaemon")

    def _compute_rms(self, data: bytes) -> float:
        """Calcular Root-Mean-Square para medir energía térmica/acústica (Axioma Ω15)."""
        count = len(data) / 2
        format = "%dh" % count
        shorts = struct.unpack(format, data)
        sum_squares = sum(s * s for s in shorts)
        return math.sqrt(sum_squares / count) if count > 0 else 0

    def listen(self, callback):
        """Bloqueo de captura de hardware y VAD determinista."""
        self._running = True
        self.logger.info(f"■ INICIANDO HARDWARE DAEMON [{self.sample_rate} Hz] | VAD Threshold: {self.energy_threshold}")

        if not HAS_AUDIO:
            self.logger.error("■ [FATAL] PyAudio no detectado. Violación de hardware físico. Instale 'portaudio'.")
            return

        audio = pyaudio.PyAudio()
        stream = audio.open(format=pyaudio.paInt16, channels=1,
                            rate=self.sample_rate, input=True,
                            frames_per_buffer=self.chunk_size)
        try:
            while self._running:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                rms = self._compute_rms(data)

                # VAD Filter: Solo emite ciclos de CPU si se rompe el umbral de energía (Zero-Anergy)
                if rms > self.energy_threshold:
                    self.logger.info(f"■ ACÚSTICA DETECTADA [RMS: {rms:.2f}] -> Despachando a Transductor.")
                    callback(data)
                else:
                    # Silencio: Ahorro de CPU
                    time.sleep(0.01)
        except KeyboardInterrupt:
            self.stop()
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()

    def stop(self):
        self.logger.info("■ DETENIENDO DAEMON ACÚSTICO Y LIBERANDO HARDWARE")
        self._running = False
