use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, USER_AGENT};
use serde::Deserialize;
use tokio::sync::mpsc::Sender;
use std::sync::{Arc, Mutex};
use crate::dashboard::Babylon60State;

#[derive(Deserialize, Debug)]
struct GithubEvent {
    // Estructura simplificada para detectar commits en repositorios pre-lanzamiento
    #[serde(rename = "type")]
    event_type: String,
    repo: RepoInfo,
    payload: Option<PayloadInfo>,
}

#[derive(Deserialize, Debug)]
struct RepoInfo {
    name: String,
}

#[derive(Deserialize, Debug)]
struct PayloadInfo {
    commits: Option<Vec<CommitInfo>>,
}

#[derive(Deserialize, Debug)]
struct CommitInfo {
    message: String,
}

pub async fn run_github_monitor(
    token: String,
    targets: Vec<String>,
    _signal_tx: Sender<String>,
    state: Arc<Mutex<Babylon60State>>,
) -> Result<(), Box<dyn std::error::Error>> {

    let client = reqwest::Client::new();
    let mut headers = HeaderMap::new();
    headers.insert(AUTHORIZATION, HeaderValue::from_str(&format!("token {}", token))?);
    headers.insert(USER_AGENT, HeaderValue::from_static("Ouroboros-Sniper-Sovereign"));

    println!(">>> [GITHUB] Iniciando vigilancia de repositorios pre-lanzamiento...");

    loop {
        for repo_path in &targets {
            let url = format!("https://api.github.com/repos/{}/events", repo_path);

            if let Ok(res) = client.get(&url).headers(headers.clone()).send().await {
                if let Ok(events) = res.json::<Vec<GithubEvent>>().await {
                    for event in events {
                        if event.event_type == "PushEvent" {
                            if let Some(payload) = event.payload {
                                if let Some(commits) = payload.commits {
                                    for commit in commits {
                                        // Detección de palabras clave: "liquidity", "deploy", "genesis", "contract"
                                        let msg = commit.message.to_lowercase();
                                        if msg.contains("liquidity") || msg.contains("addliquidity") || msg.contains("deploy") {
                                            {
                                                let mut s = state.lock().unwrap();
                                                s.log.push(format!("[GITHUB🎯] Actividad en {}", event.repo.name));
                                                s.signals_detected += 1;
                                            }
                                            // En este punto, el Sniper activaría un escaneo profundo del commit
                                            // buscando el Contract Address inyectado en los scripts.
                                            println!(">>> [GITHUB] SEÑAL DETECTADA EN {}: {}", event.repo.name, commit.message);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // Polling interval (P0: GitHub Events API tiene límites de rate, ajustar según token)
        tokio::time::sleep(tokio::time::Duration::from_secs(30)).await;
    }
}
