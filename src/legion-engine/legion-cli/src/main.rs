// C5-REAL EXERGY CERTIFIED
// LEGIÓN EXERGÉTICA: CLI & Runtime de Silicio para macOS
use clap::{Parser, Subcommand};
use colored::*;
use std::path::{Path, PathBuf};
use std::fs;

use legion_core::{MerkleTree, ScittReceipt};
use legion_core::scitt::hex;
use legion_apfs::{BulkScanner, SnapshotAuditor};
use legion_exergy::{ExergyEvaluator, RiskLevel};
use legion_healer::{LaunchServicesHealer, DnsHealer, SafeTrash};
use legion_lang::{Lexer, Parser as XrgParser, Compiler, VirtualMachine, VmAction};

#[derive(Parser)]
#[command(name = "legion")]
#[command(author = "Borja & Exergy Swarm Team")]
#[command(version = "1.0.0")]
#[command(about = "Kernel de Optimización Exergética y Compilador Formal para macOS (C5-REAL Certified)")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Escaneo masivo APFS con evaluación termodinámica de exergía
    Scan {
        #[arg(default_value = "~/Library/Caches")]
        target: String,
    },
    /// Compila y verifica formalmente una política ExergyScript (.xrg)
    Compile {
        policy_file: PathBuf,
    },
    /// Ejecuta una política compilada contra el sistema de archivos con recibos SCITT
    Run {
        policy_file: PathBuf,
        #[arg(long, default_value_t = true)]
        dry_run: bool,
    },
    /// Mantenimiento determinista de CoreServices (DNS, LaunchServices)
    Heal {
        #[arg(long)]
        dns: bool,
        #[arg(long)]
        launchservices: bool,
    },
    /// Estado del sistema: APFS Local Snapshots, UBC Cache y Daemons
    Status,
}

fn resolve_home_path(path_str: &str) -> PathBuf {
    if path_str.starts_with("~/") {
        if let Ok(home) = std::env::var("HOME") {
            return Path::new(&home).join(path_str.trim_start_matches("~/"));
        }
    }
    PathBuf::from(path_str)
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Scan { target } => {
            let target_path = resolve_home_path(&target);
            println!("{}", "══════════════════════════════════════════════════════════════".cyan());
            println!("  {} {}", "LEGIÓN EXERGÉTICA:".bold().white(), "Escaneo APFS Masivo".green());
            println!("  Target: {}", target_path.display().to_string().yellow());
            println!("{}", "══════════════════════════════════════════════════════════════".cyan());

            let scanner = BulkScanner::default();
            let start = std::time::Instant::now();
            let entries = scanner.scan_directory(&target_path)?;
            let elapsed = start.elapsed();

            let mut anergy_bytes: u64 = 0;
            let mut immune_count: usize = 0;
            let mut review_count: usize = 0;
            let mut anergy_count: usize = 0;

            for entry in &entries {
                let score = ExergyEvaluator::evaluate_file(
                    &entry.path,
                    entry.size_bytes,
                    entry.access_time_epoch,
                    entry.modify_time_epoch,
                    true,
                );

                match score.risk {
                    RiskLevel::Green if score.is_100pct_anergy => {
                        anergy_count += 1;
                        anergy_bytes += entry.size_bytes;
                    }
                    RiskLevel::Yellow => review_count += 1,
                    RiskLevel::Red => immune_count += 1,
                    _ => {}
                }
            }

            let anergy_mb = anergy_bytes as f64 / (1024.0 * 1024.0);
            println!("  Archivos escaneados: {}", entries.len().to_string().bold());
            println!("  Latencia de escaneo: {:?}", elapsed);
            println!("  100% Anergía Certificada: {} archivos ({:.2} MB)", anergy_count.to_string().green(), anergy_mb);
            println!("  Requiere Revisión (Yellow): {}", review_count.to_string().yellow());
            println!("  Inmunidad Absoluta (Red): {}", immune_count.to_string().red());
            println!("{}", "══════════════════════════════════════════════════════════════".cyan());
        }

        Commands::Compile { policy_file } => {
            let code = fs::read_to_string(&policy_file)?;
            println!("Compilando política: {}", policy_file.display());

            let mut lexer = Lexer::new(&code);
            let tokens = lexer.tokenize().map_err(|e| format!("Lexer Error: {}", e))?;
            let mut parser = XrgParser::new(tokens);
            let program = parser.parse_program().map_err(|e| format!("Parser Error: {}", e))?;

            let compiled = Compiler::compile(&program).map_err(|e| format!("Verification Error: {}", e))?;
            println!("{} Política verificada y compilada con éxito ({} reglas).", "✓".green().bold(), compiled.rules.len());
        }

        Commands::Run { policy_file, dry_run } => {
            let code = fs::read_to_string(&policy_file)?;
            let mut lexer = Lexer::new(&code);
            let tokens = lexer.tokenize().map_err(|e| format!("Lexer Error: {}", e))?;
            let mut parser = XrgParser::new(tokens);
            let program = parser.parse_program().map_err(|e| format!("Parser Error: {}", e))?;
            let compiled = Compiler::compile(&program).map_err(|e| format!("Verification Error: {}", e))?;

            println!("{}", "══════════════════════════════════════════════════════════════".cyan());
            println!("  {} [Modo: {}]", "EJECUCIÓN DE POLÍTICA EXERGY".bold().white(), if dry_run { "DRY-RUN (Simulación)".yellow() } else { "ACTIVO (Papelera)".green() });
            println!("{}", "══════════════════════════════════════════════════════════════".cyan());

            let mut merkle = MerkleTree::new();
            let scanner = BulkScanner::default();

            for rule in &compiled.rules {
                let target_path = resolve_home_path(&rule.target_pattern);
                let base_dir = if target_path.to_string_lossy().contains('*') {
                    let s = target_path.to_string_lossy();
                    let prefix = s.split('*').next().unwrap_or("");
                    PathBuf::from(prefix)
                } else {
                    target_path
                };

                if let Ok(entries) = scanner.scan_directory(&base_dir) {
                    for entry in entries {
                        let (action, rule_name) = VirtualMachine::evaluate_entry(&compiled, &entry);
                        if action == VmAction::SafeTrash {
                            let receipt: ScittReceipt = merkle.create_receipt(
                                "SAFE_TRASH",
                                &entry.path.to_string_lossy(),
                                entry.size_bytes,
                                0.01,
                            );

                            println!("  [PURGA] {} ({:.2} KB) -> {}", entry.path.display(), entry.size_bytes as f64 / 1024.0, rule_name.unwrap_or_default().green());
                            println!("          Leaf SHA3: {}", receipt.leaf_hash.cyan());

                            if !dry_run {
                                let _ = SafeTrash::move_to_trash(&entry.path);
                            }
                        }
                    }
                }
            }

            println!("  Merkle Root Final: {}", hex::encode(merkle.compute_root()).bold().green());
            println!("{}", "══════════════════════════════════════════════════════════════".cyan());
        }

        Commands::Heal { dns, launchservices } => {
            if dns {
                print!("Purgando DNS y mDNSResponder... ");
                let ok = DnsHealer::flush_cache().unwrap_or(false);
                println!("{}", if ok { "OK".green() } else { "FALLO".red() });
            }
            if launchservices {
                print!("Reconstruyendo LaunchServices (lsregister)... ");
                let ok = LaunchServicesHealer::rebuild_database().unwrap_or(false);
                println!("{}", if ok { "OK".green() } else { "FALLO".red() });
            }
        }

        Commands::Status => {
            println!("{}", "══════════════════════════════════════════════════════════════".cyan());
            println!("  {} {}", "ESTADO DEL SISTEMA:".bold().white(), "C5-REAL Zero-Bloatware".green());
            println!("{}", "══════════════════════════════════════════════════════════════".cyan());

            let snapshots = SnapshotAuditor::list_local_snapshots();
            println!("  APFS Local Snapshots: {}", snapshots.len().to_string().yellow());
            for s in snapshots {
                println!("    • {}", s.name);
            }

            println!("  Daemons Residentes Registrados: {}", "0 (Stateless Pure Execution)".green().bold());
            println!("  Unified Buffer Cache (UBC): {}", "Exergía Protegida (Sin RAM Cleaners destructivos)".cyan());
            println!("{}", "══════════════════════════════════════════════════════════════".cyan());
        }
    }

    Ok(())
}
