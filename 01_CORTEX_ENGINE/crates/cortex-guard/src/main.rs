//! cortex-guard: Deterministic Architectural Verification Engine & SARIF Generator
//! C5-REAL Compliant: Zero-Alucination, Physical Constraint Solver for IFC BIM models vs. PGOU/CTE

use clap::{Parser, Subcommand, ValueEnum};
use cortex_guard::dsl::Rulebook;
use cortex_guard::eval::evaluate;
use cortex_guard::ifc::IfcModel;
use cortex_guard::sarif::generate_sarif;
use sha2::{Digest, Sha256};
use std::fs;
use std::path::PathBuf;
use std::process::exit;
use std::time::Instant;

#[derive(Parser)]
#[command(name = "cortex-guard")]
#[command(version = "1.0.0")]
#[command(
    about = "CORTEX Deterministic Verification CLI for Architecture & AEC Compliance",
    long_about = "C5-REAL Architectural Solver: Evaluates ISO 10303-21 IFC BIM models against PGOU/CTE DSL rulebooks with exact line attribution and SARIF v2.1.0 output."
)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Verify an IFC file against a PGOU/CTE Constraint DSL rulebook
    Verify {
        /// Path to the IFC BIM file
        #[arg(short, long)]
        ifc: PathBuf,

        /// Path to the PGOU/CTE DSL rulebook file
        #[arg(short, long)]
        pgou: PathBuf,

        /// Output format
        #[arg(short, long, value_enum, default_value_t = OutputFormat::Human)]
        format: OutputFormat,

        /// Exit with code 1 on any UNSAT violation
        #[arg(long, default_value = "true", num_args = 0..=1, default_missing_value = "true")]
        strict: bool,

        /// Emit GitHub Actions workflow error annotations (::error file=...::)
        #[arg(long, default_value_t = false)]
        annotate_gh: bool,
    },
}

#[derive(Copy, Clone, PartialEq, Eq, PartialOrd, Ord, ValueEnum, serde::Serialize, serde::Deserialize)]
enum OutputFormat {
    Human,
    Json,
    Sarif,
}

fn compute_file_hash(content: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(content);
    hex::encode(hasher.finalize())
}

fn main() {
    let start_time = Instant::now();
    let cli = Cli::parse();

    match cli.command {
        Commands::Verify {
            ifc,
            pgou,
            format,
            strict,
            annotate_gh,
        } => {
            // 1. Read IFC file
            let ifc_bytes = match fs::read(&ifc) {
                Ok(bytes) => bytes,
                Err(e) => {
                    eprintln!("CRASH [ERR_301]: Failed to read IFC file '{}': {}", ifc.display(), e);
                    exit(3);
                }
            };
            let ifc_hash = compute_file_hash(&ifc_bytes);
            let ifc_content = match String::from_utf8(ifc_bytes) {
                Ok(s) => s,
                Err(e) => {
                    eprintln!("CRASH [ERR_303]: IFC file '{}' is not valid UTF-8: {}", ifc.display(), e);
                    exit(3);
                }
            };

            // 2. Read PGOU Rulebook
            let pgou_bytes = match fs::read(&pgou) {
                Ok(bytes) => bytes,
                Err(e) => {
                    eprintln!("CRASH [ERR_302]: Failed to read PGOU DSL file '{}': {}", pgou.display(), e);
                    exit(3);
                }
            };
            let pgou_hash = compute_file_hash(&pgou_bytes);
            let pgou_content = match String::from_utf8(pgou_bytes) {
                Ok(s) => s,
                Err(e) => {
                    eprintln!("CRASH [ERR_304]: PGOU DSL file '{}' is not valid UTF-8: {}", pgou.display(), e);
                    exit(3);
                }
            };

            // 3. Parse IFC STEP Model
            let model = match IfcModel::parse(&ifc_content, ifc.clone()) {
                Ok(m) => m,
                Err(e) => {
                    eprintln!("CRASH [ERR_305]: Failed to parse STEP ISO 10303-21 in '{}': {}", ifc.display(), e);
                    exit(3);
                }
            };

            // 4. Parse PGOU / CTE Rulebook
            let rulebook = match Rulebook::parse(&pgou_content, &pgou) {
                Ok(r) => r,
                Err(e) => {
                    eprintln!("CRASH [ERR_306]: Failed to parse PGOU / CTE Rulebook in '{}': {}", pgou.display(), e);
                    exit(3);
                }
            };

            // 5. Run Deterministic Constraint Solver
            let result = evaluate(&model, &rulebook, ifc_hash, pgou_hash, start_time);
            let has_violations = !result.violations.is_empty();

            // 6. Emit GitHub Actions Annotations if requested
            if annotate_gh {
                for v in &result.violations {
                    println!(
                        "::error file={},line={}::[{}] {} — Medido: {}, Límite: {}. Cita: {}",
                        v.file_path, v.line, v.code, v.title, v.measured, v.limit, v.legal_citation
                    );
                }
            }

            // 7. Output according to selected format
            match format {
                OutputFormat::Human => {
                    println!("================================================================================");
                    println!("                       CORTEX-GUARD DETERMINISTIC AUDIT REPORT                  ");
                    println!("================================================================================");
                    println!("STATUS      : {}", result.status);
                    println!("IFC HASH    : {}", result.ifc_hash);
                    println!("PGOU HASH   : {}", result.pgou_hash);
                    println!("EXEC TIME   : {} ms", result.execution_time_ms);
                    println!("VIOLATIONS  : {}", result.violations.len());
                    println!("--------------------------------------------------------------------------------");

                    if result.violations.is_empty() {
                        println!("✅ [CONFORME] Todos los elementos del modelo IFC satisfacen las restricciones normativas.");
                    } else {
                        for v in &result.violations {
                            println!("[{}] {}", v.code, v.title);
                            println!("── {}", v.description);
                            println!("│");
                            println!("├─ Archivo & Línea: {}:{}", v.file_path, v.line);
                            println!("├─ Plano aportado:  Distancia/Valor medido = {}", v.measured);
                            println!("├─ Norma aplicable: Valor límite exigido  = {}", v.limit);
                            println!("│");
                            println!("└─ Evidencia Legal: {}\n", v.legal_citation);
                        }
                    }
                }
                OutputFormat::Json => {
                    let json_out = serde_json::to_string_pretty(&result).expect("BFT Fallback");
                    println!("{}", json_out);
                }
                OutputFormat::Sarif => {
                    let sarif_report = generate_sarif(&result);
                    let sarif_out = serde_json::to_string_pretty(&sarif_report).expect("BFT Fallback");
                    println!("{}", sarif_out);
                }
            }

            // Contractual Exit Codes
            if has_violations && strict {
                exit(1);
            } else {
                exit(0);
            }
        }
    }
}
