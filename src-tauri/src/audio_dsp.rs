use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use std::sync::Arc;
use std::f32::consts::PI;
use std::sync::atomic::{AtomicU32, Ordering};

/// Estado termodinámico del código. El AST en tiempo real modificará estos valores.
/// [MEJORALO]: Usamos Lock-Free Atomics (AtomicU32) para evitar dropouts y priorizar el RT-Audio Thread.
pub struct AstAcoustics {
    complexity_index: AtomicU32, // Anidamiento de IFs/Loops (Aumenta la distorsión FM)
    memory_pressure: AtomicU32,  // Variables mutables/Locks (Modula la frecuencia base)
}

impl AstAcoustics {
    pub fn new() -> Self {
        Self {
            complexity_index: AtomicU32::new(0.0f32.to_bits()),
            memory_pressure: AtomicU32::new(0.0f32.to_bits()),
        }
    }

    pub fn set_complexity(&self, val: f32) {
        self.complexity_index.store(val.to_bits(), Ordering::Release);
    }

    pub fn get_complexity(&self) -> f32 {
        f32::from_bits(self.complexity_index.load(Ordering::Acquire))
    }

    pub fn set_pressure(&self, val: f32) {
        self.memory_pressure.store(val.to_bits(), Ordering::Release);
    }

    pub fn get_pressure(&self) -> f32 {
        f32::from_bits(self.memory_pressure.load(Ordering::Acquire))
    }
}

pub fn ignite_dsp_engine(state: Arc<AstAcoustics>) {
    println!("🎛️ DSP: Inicializando bus de audio CoreAudio. Latencia ultrabaja.");

    let host = cpal::default_host();
    let device = host.default_output_device().expect("Fallo al acceder a la interfaz de audio");
    let config = device.default_output_config().unwrap();

    // Lanzamos el stream en un hilo dedicado
    std::thread::spawn(move || {
        match config.sample_format() {
            cpal::SampleFormat::F32 => run_synth::<f32>(&device, &config.into(), state),
            _ => eprintln!("Formato de audio no soportado para el dron analógico."),
        }
    });
}

fn run_synth<T>(device: &cpal::Device, config: &cpal::StreamConfig, state: Arc<AstAcoustics>) 
where T: cpal::Sample + cpal::FromSample<f32>
{
    let sample_rate = config.sample_rate.0 as f32;
    let channels = config.channels as usize;
    
    // Variables de fase del oscilador
    let mut phase: f32 = 0.0;
    
    // Frecuencia base (Un Sol profundo, anclaje y enfoque)
    let base_freq = 98.0; 

    let err_fn = |err| eprintln!("DSP Stream colapsó: {}", err);

    let stream = device.build_output_stream(
        config,
        move |data: &mut [T], _: &cpal::OutputCallbackInfo| {
            // 1. Lectura Atómica Libre de Bloqueos (Cero contención)
            let fm_amount = state.get_complexity(); 
            let pitch_shift = state.get_pressure() * 10.0; 

            // 2. Generación de síntesis FM (Frecuencia Modulada)
            for frame in data.chunks_mut(channels) {
                // Modulador: Cuanto más complejo es el código, más agresiva es la modulación
                let modulator = (phase * (base_freq * 2.0) * 2.0 * PI / sample_rate).sin() * fm_amount;
                
                // Portador: El dron base
                let current_freq = base_freq + pitch_shift + (modulator * 50.0);
                phase = (phase + current_freq / sample_rate) % 1.0;
                
                // [MEJORALO]: Soft-Clipper/Limitador asintótico (tanh) para proteger transductores biológicos
                let raw_val = (phase * 2.0 * PI).sin() * 0.1;
                let limit_val = raw_val.tanh(); 

                let sample: T = cpal::Sample::from_sample(limit_val);
                for sample_out in frame.iter_mut() {
                    *sample_out = sample;
                }
            }
        },
        err_fn,
        None,
    ).unwrap();

    stream.play().unwrap();
    
    // Mantenemos el hilo de audio vivo infinitamente
    std::thread::park(); 
}
