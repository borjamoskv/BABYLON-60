//! Binario ejecutable ERIDU-INFER (Sovereign Local Inference Runtime).
//! Orquesta el servidor dual (41343 para LM Studio CLI y 1234 para OpenAI API + Web HUD),
//! el canal IPC Zero-HTTP via Unix Domain Sockets, el Causal Gate y el demonio launchd en macOS.

use std::env;
use std::fs;
use std::path::PathBuf;
use std::process::Command;
use std::sync::Arc;
use tokio::net::TcpListener;

use eridu_infer::ipc::{start_uds_listener, DEFAULT_SOCKET_PATH};
use eridu_infer::server::{create_router, AppState, CANDIDATE_PORTS};

const DAEMON_LABEL: &str = "com.babylon60.eridu-infer";

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();

    if args.len() > 1 {
        match args[1].as_str() {
            "--install-daemon" | "install" => {
                return install_launchd_service();
            }
            "--uninstall-daemon" | "uninstall" => {
                return uninstall_launchd_service();
            }
            "--status" | "status" => {
                return check_daemon_status().await;
            }
            "--help" | "-h" => {
                print_help();
                return Ok(());
            }
            _ => {}
        }
    }

    println!("╔══════════════════════════════════════════════════════════════════════════╗");
    println!("║  ERIDU-INFER · SOVEREIGN INFERENCE RUNTIME (BABYLON-60 AIR-GAPPED)       ║");
    println!("╚══════════════════════════════════════════════════════════════════════════╝");

    let state = Arc::new(AppState::new()?);
    let manifest = state.gate.lock().await.manifest();
    let telemetry = Arc::clone(&state.telemetry);

    let app = create_router(state);

    // Iniciar canal Zero-HTTP UDS para comunicación inter-agente
    if let Err(e) = start_uds_listener(DEFAULT_SOCKET_PATH, manifest, telemetry).await {
        eprintln!("[-] Advertencia iniciando canal UDS: {}", e);
    } else {
        println!("[+] Canal IPC Zero-HTTP UDS activo en: {}", DEFAULT_SOCKET_PATH);
    }

    // Intentar enlace dual: 41343 (LM Studio CLI) y 1234 (OpenAI REST / Web HUD)
    let listener_41343 = TcpListener::bind("127.0.0.1:41343").await.ok();
    let listener_1234 = TcpListener::bind("127.0.0.1:1234").await.ok();

    match (listener_41343, listener_1234) {
        (Some(l_lms), Some(l_oa)) => {
            println!("[+] Enlazado en puerto 41343 (LM Studio CLI Discovery)");
            println!("[+] Enlazado en puerto 1234  (OpenAI REST API + Web HUD)");
            println!("[*] Web HUD Operativo          : http://127.0.0.1:1234/ y http://127.0.0.1:41343/");
            println!("[*] API Completions            : http://127.0.0.1:1234/v1/chat/completions");
            println!("[*] Causal Gate BABYLON-60     : ACTIVO (EU AI Act Arts. 12-14)");

            let app_clone = app.clone();
            tokio::spawn(async move {
                let _ = axum::serve(l_lms, app_clone).await;
            });
            axum::serve(l_oa, app).await?;
        }
        (Some(l_lms), None) => {
            println!("[+] Enlazado en puerto 41343 (LM Studio CLI Discovery)");
            println!("[*] Web HUD Operativo          : http://127.0.0.1:41343/");
            println!("[*] Causal Gate BABYLON-60     : ACTIVO (EU AI Act Arts. 12-14)");
            axum::serve(l_lms, app).await?;
        }
        (None, Some(l_oa)) => {
            println!("[+] Enlazado en puerto 1234 (OpenAI REST API + Web HUD)");
            println!("[*] Web HUD Operativo          : http://127.0.0.1:1234/");
            println!("[*] Causal Gate BABYLON-60     : ACTIVO (EU AI Act Arts. 12-14)");
            axum::serve(l_oa, app).await?;
        }
        (None, None) => {
            for &port in &CANDIDATE_PORTS {
                if let Ok(l) = TcpListener::bind(format!("127.0.0.1:{}", port)).await {
                    println!("[+] Enlazado en puerto candidato alternativo: {}", port);
                    println!("[*] Web HUD Operativo      : http://127.0.0.1:{}/", port);
                    axum::serve(l, app).await?;
                    return Ok(());
                }
            }
            eprintln!("[-] Error fatal: No se pudo enlazar a ningún puerto local.");
            std::process::exit(1);
        }
    }

    Ok(())
}

fn get_plist_path() -> PathBuf {
    let home = env::var("HOME").unwrap_or_else(|_| ".".to_string());
    PathBuf::from(home)
        .join("Library")
        .join("LaunchAgents")
        .join(format!("{}.plist", DAEMON_LABEL))
}

fn install_launchd_service() -> Result<(), Box<dyn std::error::Error>> {
    let home = env::var("HOME").unwrap_or_else(|_| ".".to_string());
    let bin_path = PathBuf::from(&home).join(".local").join("bin").join("eridu-infer");
    let log_dir = PathBuf::from(&home).join(".babylon60").join("logs");
    fs::create_dir_all(&log_dir)?;

    let plist_path = get_plist_path();
    if let Some(parent) = plist_path.parent() {
        fs::create_dir_all(parent)?;
    }

    let stdout_path = log_dir.join("eridu-infer.stdout.log");
    let stderr_path = log_dir.join("eridu-infer.stderr.log");

    let plist_content = format!(
        r#"<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{}</string>
    <key>StandardErrorPath</key>
    <string>{}</string>
</dict>
</plist>
"#,
        DAEMON_LABEL,
        bin_path.display(),
        stdout_path.display(),
        stderr_path.display()
    );

    fs::write(&plist_path, plist_content)?;
    println!("[+] Plist generado en: {}", plist_path.display());

    let _ = Command::new("launchctl")
        .args(["unload", plist_path.to_str().unwrap()])
        .output();

    let output = Command::new("launchctl")
        .args(["load", plist_path.to_str().unwrap()])
        .output()?;

    if output.status.success() {
        println!("[+] Servicio launchd {} cargado exitosamente.", DAEMON_LABEL);
        println!("[+] Binario de ejecución: {}", bin_path.display());
        println!("[+] Logs en tiempo real : tail -f {}", stdout_path.display());
    } else {
        eprintln!(
            "[-] Error al cargar launchctl: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }

    Ok(())
}

fn uninstall_launchd_service() -> Result<(), Box<dyn std::error::Error>> {
    let plist_path = get_plist_path();
    if plist_path.exists() {
        let _ = Command::new("launchctl")
            .args(["unload", plist_path.to_str().unwrap()])
            .output();
        fs::remove_file(&plist_path)?;
        println!("[+] Servicio {} descargado y eliminado.", DAEMON_LABEL);
    } else {
        println!("[-] No se encontró el archivo plist del servicio.");
    }
    Ok(())
}

async fn check_daemon_status() -> Result<(), Box<dyn std::error::Error>> {
    println!("[*] Verificando estado del runtime ERIDU-INFER...");
    let ports = [41343, 1234];
    let mut any_ok = false;

    for port in ports {
        let url = format!("http://127.0.0.1:{}/lms-status", port);
        match reqwest_check(&url).await {
            Ok(body) => {
                println!("[+] Puerto {}: ACTIVO -> {}", port, body);
                any_ok = true;
            }
            Err(e) => {
                println!("[-] Puerto {}: No responde ({})", port, e);
            }
        }
    }

    if any_ok {
        println!("[✓] ERIDU-INFER está en ejecución y respondiendo en el sustrato local.");
    } else {
        println!("[-] El runtime no se encuentra activo.");
    }

    Ok(())
}

async fn reqwest_check(url: &str) -> Result<String, String> {
    use tokio::io::{AsyncReadExt, AsyncWriteExt};
    use tokio::net::TcpStream;

    let parsed_port = if url.contains(":41343") { 41343 } else { 1234 };
    let mut stream = TcpStream::connect(format!("127.0.0.1:{}", parsed_port))
        .await
        .map_err(|e| e.to_string())?;

    let req = format!("GET /lms-status HTTP/1.1\r\nHost: 127.0.0.1:{}\r\nConnection: close\r\n\r\n", parsed_port);
    stream.write_all(req.as_bytes()).await.map_err(|e| e.to_string())?;

    let mut buf = vec![0u8; 1024];
    let n = stream.read(&mut buf).await.map_err(|e| e.to_string())?;
    let resp = String::from_utf8_lossy(&buf[..n]).to_string();
    if resp.contains("200 OK") {
        let body = resp.split("\r\n\r\n").nth(1).unwrap_or("").trim();
        Ok(body.to_string())
    } else {
        Err("HTTP status no es 200 OK".to_string())
    }
}

fn print_help() {
    println!("Uso: eridu-infer [COMANDO]");
    println!();
    println!("Comandos disponibles:");
    println!("  (sin argumentos)    Inicia el servidor en primer plano (puertos 41343 y 1234 + UDS)");
    println!("  --install-daemon    Instala y activa el demonio launchd en macOS (~/Library/LaunchAgents)");
    println!("  --uninstall-daemon  Descarga y elimina el demonio launchd de macOS");
    println!("  --status            Comprueba el estado y conectividad del runtime activo");
    println!("  --help, -h          Muestra este mensaje de ayuda");
}
