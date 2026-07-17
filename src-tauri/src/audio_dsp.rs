use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use std::sync::Arc;
use std::f32::consts::PI;
use std::sync::atomic::{AtomicU32, Ordering};

/// Estado termodinámico del código.
pub struct AstAcoustics {
    complexity_index: AtomicU32,
    memory_pressure: AtomicU32,
    harmonic_feedback: AtomicU32, // 0.0 = Dron neutro, 1.0 = Armonía Perfecta, -1.0 = Caos
    spatial_pan: AtomicU32, // -1.0 = Frontend (Izquierda), 1.0 = Backend (Derecha)
}

impl AstAcoustics {
    pub fn new() -> Self {
        Self {
            complexity_index: AtomicU32::new(0.0f32.to_bits()),
            memory_pressure: AtomicU32::new(0.0f32.to_bits()),
            harmonic_feedback: AtomicU32::new(0.0f32.to_bits()),
            spatial_pan: AtomicU32::new(0.0f32.to_bits()),
        }
    }

    pub fn set_complexity(&self, val: f32) { self.complexity_index.store(val.to_bits(), Ordering::Release); }
    pub fn get_complexity(&self) -> f32 { f32::from_bits(self.complexity_index.load(Ordering::Acquire)) }

    pub fn set_pressure(&self, val: f32) { self.memory_pressure.store(val.to_bits(), Ordering::Release); }
    pub fn get_pressure(&self) -> f32 { f32::from_bits(self.memory_pressure.load(Ordering::Acquire)) }

    pub fn set_feedback(&self, val: f32) { self.harmonic_feedback.store(val.to_bits(), Ordering::Release); }
    pub fn get_feedback(&self) -> f32 { f32::from_bits(self.harmonic_feedback.load(Ordering::Acquire)) }

    pub fn set_pan(&self, val: f32) { self.spatial_pan.store(val.to_bits(), Ordering::Release); }
    pub fn get_pan(&self) -> f32 { f32::from_bits(self.spatial_pan.load(Ordering::Acquire)) }
}

pub fn ignite_dsp_engine(state: Arc<AstAcoustics>) {
    println!("🎛️ DSP: Inicializando bus de síntesis espaciada y armónica.");

    let host = cpal::default_host();
    let device = host.default_output_device().expect("Fallo al acceder a la interfaz de audio");
    let config = device.default_output_config().unwrap();

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
    
    let mut phase: f32 = 0.0;
    let mut phase_fifth: f32 = 0.0;
    
    let base_freq = 98.0; // Sol
    let fifth_freq = base_freq * 1.5; // Quinta perfecta (Re)

    let err_fn = |err| eprintln!("DSP Stream colapsó: {}", err);

    let stream = device.build_output_stream(
        config,
        move |data: &mut [T], _: &cpal::OutputCallbackInfo| {
            let fm_amount = state.get_complexity(); 
            let pitch_shift = state.get_pressure() * 10.0; 
            let feedback = state.get_feedback(); // 1.0 (Armonía), -1.0 (Disonancia)
            let pan = state.get_pan(); // -1.0 L, 1.0 R

            for frame in data.chunks_mut(channels) {
                // Modulación por complejidad o feedback disonante
                let chaos_fm = if feedback < 0.0 { fm_amount + (feedback.abs() * 5.0) } else { fm_amount };
                let modulator = (phase * (base_freq * 2.0) * 2.0 * PI / sample_rate).sin() * chaos_fm;
                
                let current_freq = base_freq + pitch_shift + (modulator * 50.0);
                phase = (phase + current_freq / sample_rate) % 1.0;
                
                // Generador Base
                let mut raw_val = (phase * 2.0 * PI).sin() * 0.1;

                // Armonía (Quinta Perfecta) si el feedback es positivo
                if feedback > 0.0 {
                    phase_fifth = (phase_fifth + fifth_freq / sample_rate) % 1.0;
                    let fifth_val = (phase_fifth * 2.0 * PI).sin() * 0.05 * feedback;
                    raw_val += fifth_val;
                }

                // Soft-Clipper
                let limit_val = raw_val.tanh(); 

                // Spatial Panning (Ecolocalización)
                let pan_l = (1.0 - pan).min(1.0).max(0.0);
                let pan_r = (1.0 + pan).min(1.0).max(0.0);

                if channels >= 2 {
                    let sample_l: T = cpal::Sample::from_sample(limit_val * pan_l);
                    let sample_r: T = cpal::Sample::from_sample(limit_val * pan_r);
                    frame[0] = sample_l;
                    frame[1] = sample_r;
                } else {
                    let sample: T = cpal::Sample::from_sample(limit_val);
                    for sample_out in frame.iter_mut() {
                        *sample_out = sample;
                    }
                }
            }
        },
        err_fn,
        None,
    ).unwrap();

    stream.play().unwrap();
    std::thread::park(); 
}
