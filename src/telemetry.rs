//! Módulo de Telemetría Termodinámica para captura de ciclos (Efecto Observador Mitigado).

#[cfg(feature = "cortex-telemetry")]
#[derive(Debug, Clone, Copy)]
#[derive(serde::Serialize)]
pub struct TelemetryLog {
    pub probe_id: &'static str,
    pub start_cycle: u64,
    pub end_cycle: u64,
    pub delta_cycles: u64,
}

#[cfg(feature = "cortex-telemetry")]
pub const TELEMETRY_CAPACITY: usize = 1_000_000;

#[cfg(feature = "cortex-telemetry")]
pub struct ThreadLocalTelemetry {
    pub buffer: Box<[TelemetryLog; TELEMETRY_CAPACITY]>,
    pub index: usize,
}

// Usamos UnsafeCell en thread_local para evitar el overhead de RefCell::borrow_mut()
#[cfg(feature = "cortex-telemetry")]
thread_local! {
    pub static TELEMETRY: std::cell::UnsafeCell<ThreadLocalTelemetry> = std::cell::UnsafeCell::new(ThreadLocalTelemetry {
        // En Rust estable necesitamos inicializar el Box de esta forma sin causar stack overflow
        buffer: vec![TelemetryLog { probe_id: "", start_cycle: 0, end_cycle: 0, delta_cycles: 0 }; TELEMETRY_CAPACITY]
            .into_boxed_slice()
            .try_into()
            .unwrap(),
        index: 0,
    });
}

/// Obtiene el ciclo de reloj actual usando instrucciones nativas (overhead cercano a 0).
#[inline(always)]
pub fn get_cycles() -> u64 {
    #[cfg(target_arch = "aarch64")]
    {
        let cycles: u64;
        unsafe { core::arch::asm!("mrs {}, cntvct_el0", out(reg) cycles) };
        cycles
    }
    #[cfg(target_arch = "x86_64")]
    {
        unsafe { core::arch::x86_64::_rdtsc() }
    }
    #[cfg(not(any(target_arch = "aarch64", target_arch = "x86_64")))]
    {
        0
    }
}

#[cfg(feature = "cortex-telemetry")]
#[inline(always)]
pub fn record_telemetry(probe_id: &'static str, start: u64, end: u64) {
    TELEMETRY.with(|t| {
        unsafe {
            let t = &mut *t.get();
            if t.index < TELEMETRY_CAPACITY {
                let log = t.buffer.get_unchecked_mut(t.index);
                log.probe_id = probe_id;
                log.start_cycle = start;
                log.end_cycle = end;
                log.delta_cycles = end.saturating_sub(start);
                t.index += 1;
            }
        }
    });
}

/// Inicia la sonda de telemetría (se compila a Nada si el feature está desactivado)
#[macro_export]
macro_rules! probe_start {
    () => {
        #[cfg(feature = "cortex-telemetry")]
        let __probe_start_cycle = $crate::telemetry::get_cycles();
    };
}

/// Cierra la sonda y guarda el registro en el buffer en memoria.
#[macro_export]
macro_rules! probe_end {
    ($id:expr) => {
        #[cfg(feature = "cortex-telemetry")]
        {
            let __probe_end_cycle = $crate::telemetry::get_cycles();
            $crate::telemetry::record_telemetry($id, __probe_start_cycle, __probe_end_cycle);
        }
    };
}

#[cfg(feature = "cortex-telemetry")]
pub fn dump_telemetry(filename: &str) {
    use std::fs::File;
    use std::io::Write;
    TELEMETRY.with(|t| {
        unsafe {
            let t = &*t.get();
            if let Ok(mut file) = File::create(filename) {
                for i in 0..t.index {
                    if let Ok(json) = serde_json::to_string(t.buffer.get_unchecked(i)) {
                        let _ = writeln!(file, "{}", json);
                    }
                }
            }
        }
    });
}
