// C5-REAL EXERGY CERTIFIED
// xrgc: Compilador Formal de ExergyScript (XRG)
use clap::{Parser, Subcommand};
use colored::*;
use std::path::PathBuf;
use std::fs;

use legion_lang::{Lexer, Parser as XrgParser, Compiler, CompiledProgram};

#[derive(Parser)]
#[command(name = "xrgc")]
#[command(author = "Borja & Exergy Swarm Team")]
#[command(version = "1.0.0")]
#[command(about = "Compilador Formal y Tribunal de Inmunidad para ExergyScript (C5-REAL Certified)")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Verifica formalmente un archivo .xrg contra el Tribunal de Inmunidad
    Check {
        file: PathBuf,
    },
    /// Compila un script .xrg a Bytecode binario serializado (.xrgb)
    Build {
        file: PathBuf,
        #[arg(short, long)]
        output: Option<PathBuf>,
    },
    /// Desensambla y muestra los OpCodes IR de un archivo de Bytecode
    Disasm {
        file: PathBuf,
    },
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Check { file } => {
            let code = fs::read_to_string(&file)?;
            println!("Verificando política formal: {}", file.display().to_string().cyan());

            let mut lexer = Lexer::new(&code);
            let tokens = lexer.tokenize().map_err(|e| format!("Error de Léxico: {}", e))?;
            let mut parser = XrgParser::new(tokens);
            let program = parser.parse_program().map_err(|e| format!("Error de Sintaxis: {}", e))?;

            Compiler::compile(&program).map_err(|e| format!("Fallo del Tribunal de Inmunidad: {}", e))?;
            println!("{} {} [Inmunidad 100% Verificada: 0 violaciones]", "✓".green().bold(), "Compilación Formal Exitosa".green());
        }

        Commands::Build { file, output } => {
            let code = fs::read_to_string(&file)?;
            let mut lexer = Lexer::new(&code);
            let tokens = lexer.tokenize().map_err(|e| format!("Error de Léxico: {}", e))?;
            let mut parser = XrgParser::new(tokens);
            let program = parser.parse_program().map_err(|e| format!("Error de Sintaxis: {}", e))?;

            let compiled = Compiler::compile(&program).map_err(|e| format!("Fallo del Tribunal de Inmunidad: {}", e))?;
            let serialized = serde_json::to_vec_pretty(&compiled)?;

            let out_path = output.unwrap_or_else(|| file.with_extension("xrgb"));
            fs::write(&out_path, serialized)?;

            println!("{} {} -> {}", "✓".green().bold(), "Bytecode Emitido".green(), out_path.display().to_string().yellow());
        }

        Commands::Disasm { file } => {
            let data = fs::read_to_string(&file)?;
            let compiled: CompiledProgram = serde_json::from_str(&data)?;

            println!("{}", "══════════════════════════════════════════════════════════════".cyan());
            println!("  {} {}", "DESENSAMBLADOR DE BYTECODE:".bold().white(), file.display().to_string().yellow());
            println!("{}", "══════════════════════════════════════════════════════════════".cyan());

            for (idx, rule) in compiled.rules.iter().enumerate() {
                println!("  Regla [{}]: {} (Target: {})", idx.to_string().green(), rule.name.bold(), rule.target_pattern.cyan());
                println!("  Instrucciones OpCode (IR):");
                for (op_idx, op) in rule.instructions.iter().enumerate() {
                    println!("    0x{:04x} │ {:?}", op_idx, op);
                }
                println!();
            }
            println!("{}", "══════════════════════════════════════════════════════════════".cyan());
        }
    }

    Ok(())
}
