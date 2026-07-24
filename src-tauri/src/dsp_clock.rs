use std::time::{Instant, Duration};

pub struct DspClock {
    pub bpm: f32,
    start_time: Instant,
}

impl DspClock {
    pub fn new(bpm: f32) -> Self {
        Self {
            bpm,
            start_time: Instant::now(),
        }
    }

    pub fn is_downbeat(&self) -> bool {
        let elapsed = self.start_time.elapsed().as_secs_f32();
        let beats_per_second = self.bpm / 60.0;
        let beat_duration = 1.0 / beats_per_second;
        
        let phase = elapsed % beat_duration;
        phase < 0.05 || phase > (beat_duration - 0.05)
    }
}

pub fn sync_drop_to_grid() {
    println!("⚡ [GRID_SYNC] Esperando al Downbeat (130 BPM)...");
    let clock = DspClock::new(130.0);
    
    loop {
        if clock.is_downbeat() {
            println!("💥 [DROP] AST Inyectado en el bombo. Fricción: 0.0");
            break;
        }
        std::thread::sleep(Duration::from_millis(5));
    }
}
