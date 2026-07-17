use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use tokio::sync::mpsc;
use ringbuf::{HeapRb, Producer, Consumer};

/// Estado global del motor de Vibe Coding y Telepatía
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

pub fn ignite_vibe_dictation(
    engine_state: Arc<VoiceEngine>,
    tx_audio_chunks: mpsc::Sender<Vec<f32>>,
    tx_physiological_cmds: mpsc::Sender<&'static str>
) {
    println!("🎙️ VIBE CODE: Inicializando bus acústico omnidireccional (Beamforming & Transientes).");

    let host = cpal::default_host();
    let device = match host.default_input_device() {
        Some(d) => d,
        None => {
            eprintln!("[-] VIBE CODE: No se detectó array de micrófonos. Dictado espacial deshabilitado.");
            return;
        }
    };

    let config = device.default_input_config().unwrap();

    std::thread::spawn(move || {
        match config.sample_format() {
            cpal::SampleFormat::F32 => run_input_stream::<f32>(&device, &config.into(), engine_state, tx_audio_chunks, tx_physiological_cmds),
            _ => eprintln!("Formato de entrada no soportado. Se requiere f32 para Vibe Code."),
        }
    });
}

fn run_input_stream<T>(
    device: &cpal::Device, 
    config: &cpal::StreamConfig, 
    state: Arc<VoiceEngine>,
    tx_audio: mpsc::Sender<Vec<f32>>,
    tx_cmds: mpsc::Sender<&'static str>
) 
where T: cpal::Sample + cpal::IntoSample<f32>
{
    let capacity = (config.sample_rate.0 as usize) * 5; // 5 segundos de Chaos Buffer
    let ring_buffer = HeapRb::<f32>::new(capacity);
    let (mut producer, mut consumer) = ring_buffer.split();

    let channels = config.channels as usize;
    let threshold_voice: f32 = 0.03; 
    let threshold_click: f32 = 0.8; // Transiente agudo (Chasquido)
    let threshold_sigh: f32 = 0.4;  // Energía sostenida (Suspiro)

    let mut click_cooldown = 0;
    let mut sigh_accumulator = 0.0;

    let err_fn = |err| eprintln!("Input Stream colapsó: {}", err);

    let stream = device.build_input_stream(
        config,
        move |data: &[T], _: &cpal::InputCallbackInfo| {
            if !state.is_listening.load(Ordering::Relaxed) {
                return;
            }

            for frame in data.chunks(channels) {
                // Cálculo de Beamforming básico (Diferencia de fase/amplitud L vs R)
                let left: f32 = frame.get(0).map(|s| s.clone().into_sample()).unwrap_or(0.0);
                let right: f32 = frame.get(1).map(|s| s.clone().into_sample()).unwrap_or(left);
                
                let _pan_ratio = if left.abs() + right.abs() > 0.001 {
                    (right.abs() - left.abs()) / (left.abs() + right.abs())
                } else {
                    0.0
                };
                
                let mono_sample = (left + right) / 2.0;
                let energy = mono_sample.abs();

                // 1. Detección Fisiológica: CHASQUIDO (Transiente puro)
                if energy > threshold_click && click_cooldown == 0 {
                    let _ = tx_cmds.try_send("CMD_ENTER_EXECUTE");
                    click_cooldown = 44100; // 1 seg cooldown
                }
                if click_cooldown > 0 { click_cooldown -= 1; }

                // 2. Detección Fisiológica: SUSPIRO (Energía sostenida sin ser grito)
                if energy > 0.1 && energy < threshold_sigh {
                    sigh_accumulator += energy;
                } else {
                    sigh_accumulator *= 0.99; // Decay
                }

                if sigh_accumulator > 2000.0 { // Suspiro profundo detectado
                    let _ = tx_cmds.try_send("CMD_CONTEXT_FLUSH");
                    sigh_accumulator = 0.0;
                }

                // 3. Chaos Buffer (Stream of Consciousness)
                if energy > threshold_voice {
                    let _ = producer.push(mono_sample); 
                }
            }
        },
        err_fn,
        None,
    ).unwrap();

    stream.play().unwrap();

    // Drenado asíncrono
    let rt = tokio::runtime::Runtime::new().unwrap();
    rt.block_on(async move {
        loop {
            tokio::time::sleep(tokio::time::Duration::from_millis(1000)).await;
            if consumer.len() > 16000 {
                let mut chunk = Vec::with_capacity(consumer.len());
                while let Some(sample) = consumer.pop() {
                    chunk.push(sample);
                }
                if tx_audio.send(chunk).await.is_err() { break; }
            }
        }
    });
}
