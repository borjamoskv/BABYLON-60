// C5-REAL EXERGY CERTIFIED
use crossbeam_channel::unbounded;
use moskv84_daemon::{Config, MantleMonitor, Tick, Verdict};
use notify::{RecommendedWatcher, RecursiveMode, Watcher};
use std::path::Path;
use std::time::Duration;

fn main() -> notify::Result<()> {
    println!("╔══════════════════════════════════════════════════════════════════════╗");
    println!("║ MOSKV84 - MANTLE MONITOR DAEMON (CCT)                                ║");
    println!("╚══════════════════════════════════════════════════════════════════════╝");

    // Directorio a vigilar (podemos parametrizarlo después)
    let watch_path = "/Users/borjafernandezangulo/10_PROJECTS";
    println!("> Instanciando en: {}", watch_path);

    // Canal para recibir eventos crudos del sistema de archivos
    let (tx, rx) = unbounded();

    // Configurar el watcher de notify (fsevents en macOS)
    let mut watcher = RecommendedWatcher::new(
        move |res: notify::Result<notify::Event>| {
            if let Ok(event) = res {
                // Filtro hiper-básico: ignorar eventos de acceso/lectura puros si es posible
                // y quedarnos con modificaciones, creaciones, borrados.
                // Para el MVP contamos cualquier evento que pase fsevents.
                let _ = tx.send(event);
            }
        },
        notify::Config::default(),
    )?;

    watcher.watch(Path::new(watch_path), RecursiveMode::Recursive)?;
    println!("> [OK] Acoplamiento Estructural (fsevents) establecido.");

    // Configurar el Motor Termodinámico (Acelerado para PoC)
    let mut cfg = Config::default();
    cfg.warmup_ticks = 3;
    cfg.slowing_persist = 3;
    cfg.cusum_threshold = 3.0;
    let mut monitor = MantleMonitor::new(cfg);

    // Bucle principal de reloj (Ticks)
    let tick_duration = Duration::from_secs(1);

    println!("> Iniciando loop termodinámico (Tick = 1s)...");
    println!("------------------------------------------------------------------------");
    println!("{:<8} | {:<8} | {:<6} | {:<8} | {:<12} | {}",
             "Tick", "Eventos", "λ", "Exceso", "CUSUM", "VEREDICTO");
    println!("------------------------------------------------------------------------");

    loop {
        std::thread::sleep(tick_duration);

        // Vaciar el canal de eventos del último segundo
        let mut total_events = 0;
        while let Ok(_) = rx.try_recv() {
            total_events += 1;
        }

        // Construir el tick (asumimos 0 auto-causados en esta PoC)
        let tick = Tick {
            total_events,
            self_caused: 0,
        };

        // Procesar termodinámica
        let reading = monitor.step(tick);

        // Formatear salida visual
        let verdict_str = match reading.verdict {
            Verdict::Warmup => "\x1b[90mWARMUP\x1b[0m", // Gris
            Verdict::Nominal => "\x1b[32mNOMINAL\x1b[0m", // Verde
            Verdict::Refractory => "\x1b[33mREFRACTARIO\x1b[0m", // Amarillo
            Verdict::PreCollapse => "\x1b[35m[!] PRE-COLAPSO (RALENTIZACIÓN)\x1b[0m", // Magenta
            Verdict::Breach => "\x1b[31;1m[!!!] BREACH (MANTO PERFORADO)\x1b[0m", // Rojo brillante
        };

        // Solo imprimir si hay actividad o un cambio crítico para no inundar la terminal
        // o podemos imprimir siempre para ver el latido. Imprimamos siempre por ahora
        // pero con un formato que permita ver la evolución.
        println!(
            "{:<8} | {:<8} | {:<6.2} | {:<8.2} | {:<12.2} | {}",
            monitor.ticks(),
            total_events,
            reading.lambda,
            reading.excess_z,
            reading.cusum,
            verdict_str
        );

        // Acción de disparo (Intervención de Emergencia)
        if reading.verdict == Verdict::PreCollapse {
            println!("\x1b[45;37m[ACCIÓN REQUERIDA] RALENTIZACIÓN CRÍTICA DETECTADA. DISPARANDO SNAPSHOT DE PREVENCIÓN.\x1b[0m");
            println!("\x1b[45;37m> Inyección de Entropía Biológica (η) detectada escapando a la semántica.\x1b[0m");
            // Aquí iría la ejecución del script .snapshots
        } else if reading.verdict == Verdict::Breach {
            println!("\x1b[41;37m[EMERGENCIA] MANTO PERFORADO. LA FUNCION DE ONDA HA COLAPSADO FUERA DEL MODELO.\x1b[0m");
            // Aquí iría un hard reset o snapshot de emergencia mayor
        }
    }
}
