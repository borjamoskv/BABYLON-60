use c5real::exergy_bridge_client::ExergyBridgeClient;
use c5real::{LedgerRequest, ExergyState};
use std::io::Write;
use std::time::Instant;

pub mod c5real {
    tonic::include_proto!("c5real");
}

/// Umbrales de anomalía (AI Watchdog)
const EXERGY_CRITICAL: f64 = 0.990;
const EXERGY_WARNING: f64 = 0.995;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    
    // Parsear flags simples
    let log_path = args.iter().position(|a| a == "--log")
        .and_then(|i| args.get(i + 1))
        .map(|s| s.to_string());
    let max_events: Option<u64> = args.iter().position(|a| a == "--max")
        .and_then(|i| args.get(i + 1))
        .and_then(|s| s.parse().ok());
    let anomaly_only = args.iter().any(|a| a == "--anomaly-only");
    let summary_mode = args.iter().any(|a| a == "--summary");
    
    let url = args.iter().position(|a| a == "--url")
        .and_then(|i| args.get(i + 1))
        .map(|s| s.to_string())
        .unwrap_or_else(|| "http://127.0.0.1:50051".to_string());

    eprintln!("[C5-CLI] AI-Exclusive Telemetry Watcher");
    eprintln!("[C5-CLI] Target: {}", url);
    if let Some(ref p) = log_path { eprintln!("[C5-CLI] Logging to: {}", p); }
    if anomaly_only { eprintln!("[C5-CLI] Mode: ANOMALY-ONLY (exergy < {})", EXERGY_WARNING); }
    if let Some(max) = max_events { eprintln!("[C5-CLI] Max events: {}", max); }

    let mut client = ExergyBridgeClient::connect(url).await?;

    let request = tonic::Request::new(LedgerRequest { from_sequence: 0 });
    let mut stream = client.stream_ledger(request).await?.into_inner();

    // Archivo de log opcional
    let mut log_file = log_path.map(|p| {
        std::fs::OpenOptions::new()
            .create(true).append(true).open(p)
            .expect("Failed to open log file")
    });

    // Contadores para resumen
    let start = Instant::now();
    let mut total: u64 = 0;
    let mut warnings: u64 = 0;
    let mut criticals: u64 = 0;
    let mut max_seq: u64 = 0;
    let mut min_exergy: f64 = f64::MAX;
    let mut max_exergy: f64 = f64::MIN;
    let mut sum_exergy: f64 = 0.0;

    while let Some(state) = stream.message().await? {
        total += 1;
        let seq = state.sequence_id;
        let ex = state.exergy_level;

        // Actualizar estadísticas
        if seq > max_seq { max_seq = seq; }
        if ex < min_exergy { min_exergy = ex; }
        if ex > max_exergy { max_exergy = ex; }
        sum_exergy += ex;

        // Clasificar severidad
        let severity = if ex < EXERGY_CRITICAL {
            criticals += 1;
            "CRITICAL"
        } else if ex < EXERGY_WARNING {
            warnings += 1;
            "WARNING"
        } else {
            "OK"
        };

        // Filtro de anomalías
        if anomaly_only && severity == "OK" {
            continue;
        }

        // Emitir JSONL
        let line = format!(
            "{{\"event\":\"bft_block\",\"seq\":{},\"hash\":\"{}\",\"exergy\":{:.5},\"severity\":\"{}\",\"proof_len\":{},\"ts_ms\":{}}}",
            seq, state.block_hash, ex, severity, state.cryptographic_proof.len(),
            start.elapsed().as_millis()
        );

        println!("{}", line);

        // Persistir si hay archivo de log
        if let Some(ref mut f) = log_file {
            writeln!(f, "{}", line)?;
        }

        // Límite de eventos
        if let Some(max) = max_events {
            if total >= max { break; }
        }
    }

    // Resumen final (siempre a stderr para no contaminar el JSONL de stdout)
    if summary_mode || total > 0 {
        let elapsed = start.elapsed();
        let avg_exergy = if total > 0 { sum_exergy / total as f64 } else { 0.0 };
        eprintln!("---");
        eprintln!("[C5-CLI] Session Summary:");
        eprintln!("  Total blocks:    {}", total);
        eprintln!("  Max sequence:    {}", max_seq);
        eprintln!("  Exergy range:    [{:.5}, {:.5}]", min_exergy, max_exergy);
        eprintln!("  Exergy avg:      {:.5}", avg_exergy);
        eprintln!("  Warnings:        {}", warnings);
        eprintln!("  Criticals:       {}", criticals);
        eprintln!("  Elapsed:         {:.2}s", elapsed.as_secs_f64());
        eprintln!("  Throughput:      {:.1} blocks/s", total as f64 / elapsed.as_secs_f64());
    }

    Ok(())
}
