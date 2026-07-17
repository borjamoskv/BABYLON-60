use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use tokio::sync::mpsc;
use ringbuf::{HeapRb, Producer, Consumer};

/// Estado global del motor de Vibe Coding (Dictado de Voz)
pub struct VoiceEngine {
    pub is_listening: AtomicBool,
}

impl VoiceEngine {
    pub fn new() -> Self {
        Self {
            is_listening: AtomicBool::new(false),
        }
    }

    pub fn toggle(&self) -> bool {
        let current = self.is_listening.load(Ordering::Acquire);
        self.is_listening.store(!current, Ordering::Release);
        !current
    }
}

/// Transductor físico: Convierte la presión acústica del Operador (Micrófono) 
/// en fragmentos listos para el tensor de Whisper (Ollama / Local ASR).
pub fn ignite_vibe_dictation(
    engine_state: Arc<VoiceEngine>,
    tx_audio_chunks: mpsc::Sender<Vec<f32>>
) {
    println!("🎙️ VIBE CODE: Inicializando bus de entrada de micrófono (Zero-Latency).");

    let host = cpal::default_host();
    let device = match host.default_input_device() {
        Some(d) => d,
        None => {
            eprintln!("[-] VIBE CODE: No se detectó micrófono de estudio. Dictado deshabilitado.");
            return;
        }
    };

    let config = device.default_input_config().unwrap();

    std::thread::spawn(move || {
        match config.sample_format() {
            cpal::SampleFormat::F32 => run_input_stream::<f32>(&device, &config.into(), engine_state, tx_audio_chunks),
            _ => eprintln!("Formato de entrada no soportado. Se requiere f32 para Vibe Code."),
        }
    });
}

fn run_input_stream<T>(
    device: &cpal::Device, 
    config: &cpal::StreamConfig, 
    state: Arc<VoiceEngine>,
    tx: mpsc::Sender<Vec<f32>>
) 
where T: cpal::Sample + cpal::IntoSample<f32>
{
    // RingBuffer para acumular frames sin bloquear el RT-Audio thread
    // Capacidad de ~2 segundos a 44100Hz
    let capacity = (config.sample_rate.0 as usize) * 2;
    let ring_buffer = HeapRb::<f32>::new(capacity);
    let (mut producer, mut consumer) = ring_buffer.split();

    let channels = config.channels as usize;
    let threshold: f32 = 0.05; // Noise Gate Threshold

    let err_fn = |err| eprintln!("Input Stream colapsó: {}", err);

    let stream = device.build_input_stream(
        config,
        move |data: &[T], _: &cpal::InputCallbackInfo| {
            // Si el modo dictado está apagado, tiramos la energía
            if !state.is_listening.load(Ordering::Relaxed) {
                return;
            }

            // Downmix a Mono y Noise Gate C5-REAL
            for frame in data.chunks(channels) {
                let mut mono_sample = 0.0;
                for sample in frame.iter() {
                    let f32_sample: f32 = (*sample).into_sample();
                    mono_sample += f32_sample;
                }
                mono_sample /= channels as f32;

                // VAD Básico (Voice Activity Detection) - Noise Gate
                if mono_sample.abs() > threshold {
                    let _ = producer.push(mono_sample); // Push atómico, non-blocking
                }
            }
        },
        err_fn,
        None,
    ).unwrap();

    stream.play().unwrap();

    // Hilo secundario para drenar el buffer de audio y mandarlo a la IA/Whisper
    let rt = tokio::runtime::Runtime::new().unwrap();
    rt.block_on(async move {
        loop {
            tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
            if consumer.len() > 10000 {
                // Hay suficientes datos para procesar fonemas
                let mut chunk = Vec::with_capacity(consumer.len());
                while let Some(sample) = consumer.pop() {
                    chunk.push(sample);
                }
                
                // Enviamos el chunk crudo al Motor de Transcripción (Asíncrono)
                if tx.send(chunk).await.is_err() {
                    break; // Receiver cerrado
                }
            }
        }
    });
}
