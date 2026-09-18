use std::sync::mpsc::channel;
use std::time::{Duration, Instant};
use notify::{Watcher, RecursiveMode, Event};
use babylon60_kernel::scheduler::{F60ThermodynamicScheduler, AgentExecutionState};
use babylon60_kernel::thermodynamics::MarkovBlanket;
use babylon60_kernel::shared_manifest::SharedManifest;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!(">>> BABYLON-60 PoC: Darwin FSEvents -> F60ThermodynamicScheduler");
    println!(">>> Booting F60 Kernel (60Hz / 16.6ms Tick)...");

    let mut scheduler = F60ThermodynamicScheduler::new();
    let sensory = SharedManifest::new();
    let active = SharedManifest::new();
    
    // We set a max capacity of 50 to easily demonstrate Burnout when high FS entropy hits
    let blanket = MarkovBlanket::new(50, &sensory, &active);

    // Setup FSEvents listener (simulating the C/PyO3 bridge from 01_CORTEX_ENGINE)
    let (tx, rx) = channel();
    let mut watcher = notify::recommended_watcher(move |res: notify::Result<Event>| {
        if let Ok(event) = res {
            // Send FS event to the main loop to simulate the FFI boundary
            let _ = tx.send(event);
        }
    })?;

    // Watch the current directory recursively
    watcher.watch(std::path::Path::new("."), RecursiveMode::Recursive)?;
    println!(">>> Listening for FSEvents on '.'...");

    let tick_duration = Duration::from_nanos(1_000_000_000 / 60); // 60Hz
    let mut last_tick = Instant::now();
    let mut iteration = 0;

    loop {
        // Wait for next tick to maintain 60Hz determinism
        let elapsed = last_tick.elapsed();
        if elapsed < tick_duration {
            std::thread::sleep(tick_duration - elapsed);
        }
        last_tick = Instant::now();

        // Drain pending FSEvents and inject them into the sensory channel
        let mut entropy_injected = 0;
        while let Ok(event) = rx.try_recv() {
            // Simple entropy mapping: count paths changed
            let surprise_value = event.paths.len() as u8 * 10;
            entropy_injected += surprise_value;
        }

        if entropy_injected > 0 {
            // Simulate PyO3 FFI writing to the sensory SharedManifest (Ring-0)
            // We use a dummy ID and inject the entropy as the first byte of payload
            println!("    [PyO3 Bridge] FSEvents mapped to surprise: +{}", entropy_injected);
            sensory.publish(1, &[entropy_injected as u64, 0, 0, 0]).unwrap();
        }

        // Execute deterministic step
        let state = scheduler.step(&blanket).unwrap();
        iteration += 1;

        if entropy_injected > 0 || iteration % 60 == 0 {
            println!("Tick {:04} | Entropy Injected: {:>3} | State: {:?}", 
                     scheduler.logical_clock.0, entropy_injected, state);
        }

        if let AgentExecutionState::BurnoutHalted { at_tick } = state {
            println!(">>> [C5-REAL INVARIANT TRIGGERED] Burnout at tick {}!", at_tick);
            println!(">>> Epistemic Halt. Exceeds max_tfe_capacity (50). Zero-trust preserved.");
            break;
        }

        if iteration > 600 { // 10 seconds of simulation
            println!(">>> PoC completed successfully after 600 ticks without thermodynamic collapse.");
            break;
        }
    }

    Ok(())
}
