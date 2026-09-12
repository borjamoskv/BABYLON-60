use clap::{Parser, Subcommand, ValueEnum};
use std::fs;
use std::io::{Read, Write};
use std::net::TcpListener;
use std::path::PathBuf;

use babylon_attest::env;
use babylon_attest::ledger;
use babylon_attest::license::{self, LicenseStatus};

#[derive(Parser)]
#[command(name = "babylon-attest")]
#[command(version = "1.0.0")]
#[command(
    about = "BABYLON-60 / agents.archi — Sovereign WORM Ledger & Cryptographic SCITT Attestation Engine",
    long_about = "High-performance verifiable ledger for autonomous AI agents. Compliant with EU AI Act (Regulation 2024/1689, Articles 9-14) and IETF SCITT."
)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Initialize local cryptographic keys and WORM ledger directory
    Init,

    /// Attest an agent action into the immutable WORM ledger
    Attest {
        /// JSON payload string to attest
        #[arg(value_name = "PAYLOAD")]
        payload: Option<String>,

        /// Path to a JSON or text file containing the payload
        #[arg(short, long)]
        file: Option<PathBuf>,

        /// Output format
        #[arg(short, long, value_enum, default_value_t = OutputFormat::Human)]
        format: OutputFormat,
    },

    /// Cryptographically verify the integrity of the WORM ledger chain
    Verify {
        /// Output format
        #[arg(short, long, value_enum, default_value_t = OutputFormat::Human)]
        format: OutputFormat,
    },

    /// Display current enterprise license status and capabilities
    LicenseCheck,

    /// Generate an authorized enterprise license (Vendor master command)
    LicenseGen {
        /// Organization or client name
        #[arg(short, long)]
        org: String,

        /// Subscription tier
        #[arg(short, long, default_value = "enterprise-byoc")]
        tier: String,

        /// Maximum concurrent agents permitted
        #[arg(short, long, default_value_t = 100)]
        max_agents: u32,

        /// Validity duration in days
        #[arg(short, long, default_value_t = 365)]
        days: u64,

        /// Output file path (defaults to $BABYLON_HOME/license.key)
        #[arg(short, long)]
        output: Option<PathBuf>,
    },

    /// Run background HTTP sidecar listener for agent interception
    Serve {
        /// TCP port to bind
        #[arg(short, long, default_value_t = 6060)]
        port: u16,

        /// Host address to bind
        #[arg(long, default_value = "127.0.0.1")]
        host: String,
    },
}

#[derive(Copy, Clone, PartialEq, Eq, PartialOrd, Ord, ValueEnum, serde::Serialize, serde::Deserialize)]
enum OutputFormat {
    Human,
    Json,
    Scitt,
}

fn enforce_license_policy() -> Result<(), String> {
    let current_blocks = ledger::get_chain_blocks()
        .map(|b| b.len())
        .unwrap_or(0);

    match license::check_license_file(env::license_file(), current_blocks) {
        LicenseStatus::Active(lic) => {
            println!(
                "\x1b[32m[LICENSE ACTIVE]\x1b[0m Organization: {} | Tier: {} | Max Agents: {}",
                lic.org, lic.tier, lic.max_agents
            );
            Ok(())
        }
        LicenseStatus::CommunityEvaluation {
            events_count,
            max_events,
        } => {
            if events_count >= max_events {
                return Err(format!(
                    "COMMUNITY EVALUATION LIMIT EXCEEDED ({} / {} events). Enterprise license required.",
                    events_count, max_events
                ));
            }
            println!(
                "\x1b[33m[COMMUNITY EVALUATION]\x1b[0m {}/{} events consumed. For enterprise BYOC, visit https://agents.archi",
                events_count, max_events
            );
            Ok(())
        }
        LicenseStatus::Expired { org, expired_at } => {
            Err(format!("LICENSE EXPIRED for {} at timestamp {}. Please renew subscription.", org, expired_at))
        }
        LicenseStatus::Invalid(reason) => {
            Err(format!("INVALID LICENSE: {}. Fail-closed security halt.", reason))
        }
    }
}

fn main() {
    let cli = Cli::parse();

    match cli.command {
        Commands::Init => {
            match ledger::get_or_create_node_keys() {
                Ok((_, vk)) => {
                    println!("\x1b[32m[SUCCESS]\x1b[0m BABYLON-60 Sovereign Ledger Initialized.");
                    println!("Home Directory:    {}", env::babylon_home().display());
                    println!("Ledger Chain:      {}", env::ledger_file().display());
                    println!("Node Public Key:   {}", hex::encode(vk.to_bytes()));
                    println!("Compliance Target: EU AI Act Regulation 2024/1689, Article 12");
                }
                Err(e) => {
                    eprintln!("\x1b[31m[ERROR]\x1b[0m Initialization failed: {}", e);
                    std::process::exit(1);
                }
            }
        }

        Commands::Attest { payload, file, format } => {
            if let Err(e) = enforce_license_policy() {
                eprintln!("\x1b[31m[LICENSE HALT]\x1b[0m {}", e);
                std::process::exit(1);
            }

            let raw_json_str = if let Some(path) = file {
                match fs::read_to_string(&path) {
                    Ok(c) => c,
                    Err(e) => {
                        eprintln!("\x1b[31m[ERROR]\x1b[0m Cannot read file {}: {}", path.display(), e);
                        std::process::exit(1);
                    }
                }
            } else if let Some(p) = payload {
                p
            } else {
                eprintln!("\x1b[31m[ERROR]\x1b[0m Either PAYLOAD or --file must be provided.");
                std::process::exit(1);
            };

            let parsed_payload: serde_json::Value = match serde_json::from_str(&raw_json_str) {
                Ok(v) => v,
                Err(_) => serde_json::json!({ "raw_message": raw_json_str }),
            };

            match ledger::append_event(parsed_payload) {
                Ok(block) => match format {
                    OutputFormat::Human => {
                        println!("\x1b[32m[ATTESTATION COMMITTED]\x1b[0m");
                        println!("Block Height: {}", block.index);
                        println!("Block Hash:   {}", block.block_hash);
                        println!("Prev Hash:    {}", block.prev_hash);
                        println!("Timestamp:    {}", block.timestamp);
                        println!("Signature:    {}...", &block.signature[..16]);
                    }
                    OutputFormat::Json => {
                        println!("{}", serde_json::to_string_pretty(&block).expect("BFT Fallback"));
                    }
                    OutputFormat::Scitt => {
                        let voucher = ledger::export_scitt_voucher(&block);
                        println!("{}", serde_json::to_string_pretty(&voucher).expect("BFT Fallback"));
                    }
                },
                Err(e) => {
                    eprintln!("\x1b[31m[ERROR]\x1b[0m Attestation failed: {}", e);
                    std::process::exit(1);
                }
            }
        }

        Commands::Verify { format } => {
            match ledger::verify_chain() {
                Ok(report) => match format {
                    OutputFormat::Human => {
                        println!("\x1b[32m[LEDGER AUDIT: SATISFIED (SAT)]\x1b[0m");
                        println!("Total Blocks:     {}", report.total_blocks);
                        println!("Genesis Hash:     {}", report.genesis_hash);
                        println!("Latest Block:     {}", report.latest_block_hash);
                        println!("Cryptographic:    Valid SHA3-256 Merkle Chain with Ed25519 Signatures");
                        println!("Legal Compliance: {}", report.eu_ai_act_compliance);
                    }
                    OutputFormat::Json | OutputFormat::Scitt => {
                        println!("{}", serde_json::to_string_pretty(&report).expect("BFT Fallback"));
                    }
                },
                Err(e) => {
                    eprintln!("\x1b[31m[LEDGER AUDIT: VIOLATION (UNSAT)]\x1b[0m {}", e);
                    std::process::exit(1);
                }
            }
        }

        Commands::LicenseCheck => {
            let current_blocks = ledger::get_chain_blocks()
                .map(|b| b.len())
                .unwrap_or(0);

            match license::check_license_file(env::license_file(), current_blocks) {
                LicenseStatus::Active(lic) => {
                    println!("\x1b[32m=== ENTERPRISE SOVEREIGN LICENSE ===\x1b[0m");
                    println!("Status:       ACTIVE");
                    println!("Organization: {}", lic.org);
                    println!("Tier:         {}", lic.tier);
                    println!("Max Agents:   {}", lic.max_agents);
                    println!("Expires (TS): {}", lic.valid_until);
                    println!("Features:     {:?}", lic.features);
                }
                LicenseStatus::CommunityEvaluation {
                    events_count,
                    max_events,
                } => {
                    println!("\x1b[33m=== COMMUNITY EVALUATION MODE ===\x1b[0m");
                    println!("License File: Not Found (or missing)");
                    println!("Path Checked: {}", env::license_file().display());
                    println!("Events Used:  {} / {}", events_count, max_events);
                    println!("Upgrade:      Visit https://agents.archi for Enterprise BYOC");
                }
                LicenseStatus::Expired { org, expired_at } => {
                    println!("\x1b[31m=== LICENSE EXPIRED ===\x1b[0m");
                    println!("Organization: {}", org);
                    println!("Expired At:   {}", expired_at);
                }
                LicenseStatus::Invalid(reason) => {
                    println!("\x1b[31m=== LICENSE REJECTED ===\x1b[0m");
                    println!("Reason:       {}", reason);
                }
            }
        }

        Commands::LicenseGen {
            org,
            tier,
            max_agents,
            days,
            output,
        } => {
            let lic = license::generate_license(
                &org,
                &tier,
                max_agents,
                days,
                vec!["attest".into(), "scitt".into(), "byoc".into(), "hypervisor".into()],
                None,
            );

            let out_path = output.unwrap_or_else(env::license_file);
            let serialized = serde_json::to_string_pretty(&lic).expect("BFT Fallback");

            if let Some(parent) = out_path.parent() {
                let _ = fs::create_dir_all(parent);
            }

            match fs::write(&out_path, &serialized) {
                Ok(_) => {
                    println!("\x1b[32m[SUCCESS]\x1b[0m License issued for '{}'", org);
                    println!("Saved to:     {}", out_path.display());
                    println!("Valid Days:   {}", days);
                    println!("Signature:    {}...", &lic.signature_hex[..16]);
                }
                Err(e) => {
                    eprintln!("\x1b[31m[ERROR]\x1b[0m Failed to write license: {}", e);
                    std::process::exit(1);
                }
            }
        }

        Commands::Serve { port, host } => {
            let addr = format!("{}:{}", host, port);
            println!("\x1b[32m[BABYLON-ATTEST SIDECAR]\x1b[0m Listening on http://{}", addr);
            println!("Endpoints:");
            println!("  POST /attest -> Appends agent event to WORM ledger");
            println!("  GET  /verify -> Cryptographic audit of chain");
            println!("  GET  /status -> System & License status");

            let listener = match TcpListener::bind(&addr) {
                Ok(l) => l,
                Err(e) => {
                    eprintln!("\x1b[31m[ERROR]\x1b[0m Cannot bind to {}: {}", addr, e);
                    std::process::exit(1);
                }
            };

            for stream in listener.incoming() {
                if let Ok(mut stream) = stream {
                    let mut buffer = [0u8; 8192];
                    if let Ok(bytes_read) = stream.read(&mut buffer) {
                        let request_str = String::from_utf8_lossy(&buffer[..bytes_read]);
                        let (status_line, response_body) = if request_str.starts_with("GET /verify") {
                            match ledger::verify_chain() {
                                Ok(report) => ("HTTP/1.1 200 OK", serde_json::to_string_pretty(&report).expect("BFT Fallback")),
                                Err(e) => ("HTTP/1.1 500 INTERNAL SERVER ERROR", serde_json::json!({"error": e}).to_string()),
                            }
                        } else if request_str.starts_with("GET /status") {
                            let blocks_count = ledger::get_chain_blocks().map(|b| b.len()).unwrap_or(0);
                            let lic_status = format!("{:?}", license::check_license_file(env::license_file(), blocks_count));
                            let status_json = serde_json::json!({
                                "status": "ONLINE",
                                "engine": "BABYLON-60 Sovereign Ledger",
                                "blocks": blocks_count,
                                "license": lic_status
                            });
                            ("HTTP/1.1 200 OK", status_json.to_string())
                        } else if request_str.starts_with("POST /attest") {
                            // Extract body
                            if let Some(body_start) = request_str.find("\r\n\r\n") {
                                let body = &request_str[body_start + 4..];
                                let parsed: serde_json::Value = serde_json::from_str(body)
                                    .unwrap_or_else(|_| serde_json::json!({ "raw": body }));
                                match ledger::append_event(parsed) {
                                    Ok(b) => ("HTTP/1.1 200 OK", serde_json::to_string_pretty(&b).expect("BFT Fallback")),
                                    Err(e) => ("HTTP/1.1 500 INTERNAL SERVER ERROR", serde_json::json!({"error": e}).to_string()),
                                }
                            } else {
                                ("HTTP/1.1 400 BAD REQUEST", "{\"error\": \"Empty Body\"}".to_string())
                            }
                        } else {
                            ("HTTP/1.1 404 NOT FOUND", "{\"error\": \"Not Found\"}".to_string())
                        };

                        let response = format!(
                            "{}\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
                            status_line,
                            response_body.len(),
                            response_body
                        );
                        let _ = stream.write_all(response.as_bytes());
                    }
                }
            }
        }
    }
}
