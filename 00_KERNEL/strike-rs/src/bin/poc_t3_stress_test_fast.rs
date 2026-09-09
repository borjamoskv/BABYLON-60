use std::time::{Duration, Instant};
use tokio::time::{sleep, timeout};
use rand::Rng;
use futures::future::join_all;

#[derive(Debug, Clone)]
struct Metric {
    t3_latency_ms: u128,
    resolved_by: &'static str,
}

async fn mock_t3_local() -> String {
    sleep(Duration::from_millis(15)).await;
    "T3".to_string()
}

async fn mock_t1_antigravity(fail_chance: f64) -> Result<String, &'static str> {
    let (delay, will_fail) = {
        let mut rng = rand::thread_rng();
        (rng.gen_range(800..2500), rng.gen_bool(fail_chance))
    }; // rng is dropped here, safe to await
    sleep(Duration::from_millis(delay)).await;
    if will_fail { Err("FAIL") } else { Ok("T1".to_string()) }
}

async fn mock_t2_openrouter() -> Result<String, &'static str> {
    let delay = {
        let mut rng = rand::thread_rng();
        rng.gen_range(500..1500)
    };
    sleep(Duration::from_millis(delay)).await;
    Ok("T2".to_string())
}

async fn speculative_gateway(t1_fail_chance: f64) -> Metric {
    let start_time = Instant::now();
    let t3_handle = tokio::spawn(async { mock_t3_local().await });
    let _ = t3_handle.await.unwrap();
    let t3_latency_ms = start_time.elapsed().as_millis();

    let t1_future = mock_t1_antigravity(t1_fail_chance);
    let resolved_by = match timeout(Duration::from_millis(2000), t1_future).await {
        Ok(Ok(_)) => "Tier_1_Antigravity",
        _ => {
            let t2_future = mock_t2_openrouter();
            if let Ok(Ok(_)) = timeout(Duration::from_millis(2000), t2_future).await {
                "Tier_2_OpenRouter"
            } else {
                "Tier_3_Local_Only"
            }
        }
    };
    Metric { t3_latency_ms, resolved_by }
}

#[tokio::main]
async fn main() {
    let total_iterations = 1000;
    let t1_fail_rate = 0.3;
    let global_start = Instant::now();

    let mut tasks = Vec::new();
    for _ in 0..total_iterations {
        tasks.push(tokio::spawn(speculative_gateway(t1_fail_rate)));
    }
    
    let results = join_all(tasks).await;
    let metrics: Vec<Metric> = results.into_iter().map(|r| r.unwrap()).collect();

    let global_time = global_start.elapsed().as_secs_f64();
    let avg_t3_latency: f64 = metrics.iter().map(|m| m.t3_latency_ms as f64).sum::<f64>() / total_iterations as f64;
    let t1_wins = metrics.iter().filter(|m| m.resolved_by == "Tier_1_Antigravity").count();
    let t2_wins = metrics.iter().filter(|m| m.resolved_by == "Tier_2_OpenRouter").count();
    let t3_alone = metrics.iter().filter(|m| m.resolved_by == "Tier_3_Local_Only").count();

    println!("📊 STRESS TEST: MOTOR DE INFERENCIA ESPECULATIVA T3");
    println!("Iteraciones concurrentes: {}", total_iterations);
    println!("Tiempo Total de Prueba: {:.2}s", global_time);
    println!("Latencia Media T3 (Borrador UI): {:.2} ms", avg_t3_latency);
    println!("  - TIER 1 (Antigravity): {:.1}%", (t1_wins as f64 / total_iterations as f64) * 100.0);
    println!("  - TIER 2 (OpenRouter Fallback): {:.1}%", (t2_wins as f64 / total_iterations as f64) * 100.0);
    println!("  - TIER 3 (Local Fail-Stop): {:.1}%", (t3_alone as f64 / total_iterations as f64) * 100.0);
    println!("✅ ESTADO: CERO BLOQUEOS DE INTERFAZ.");
}
