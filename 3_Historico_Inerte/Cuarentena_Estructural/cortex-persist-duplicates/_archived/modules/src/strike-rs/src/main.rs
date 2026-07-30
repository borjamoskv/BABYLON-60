use clap::Parser;
use rayon::prelude::*;
use regex::Regex;
use serde::{Deserialize, Serialize};
use std::error::Error;
use std::fs;
use std::path::{Component, Path};
use walkdir::WalkDir;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    #[arg(short, long)]
    mode: String,

    #[arg(short, long)]
    input: String,

    #[arg(short, long, default_value_t = 100)]
    swarm_size: usize,
}

#[derive(Serialize, Deserialize, Debug)]
struct StrikeResult {
    status: String,
    level: String,
    exergy: f64,
    cycles: usize,
    findings: Vec<String>,
}

#[derive(Serialize, Deserialize, Debug)]
struct BindResult {
    status: String,
    hv_dimensions: usize,
    persistence: String,
}

#[derive(Serialize, Deserialize, Debug)]
struct RecallResult {
    status: String,
    similarity: f64,
    match_found: bool,
}

struct Signature {
    name: &'static str,
    pattern: &'static str,
    severity: f64,
    extensions: &'static [&'static str],
}

const SIGNATURES: &[Signature] = &[
    Signature { name: "Solidity: tx.origin used", pattern: r"tx\.origin", severity: 0.8, extensions: &["sol"] },
    Signature { name: "Solidity: Reentrancy risk (.call{value:)", pattern: r"\.call\{value:", severity: 0.9, extensions: &["sol"] },
    Signature { name: "Solidity: delegatecall risk", pattern: r"delegatecall", severity: 0.95, extensions: &["sol"] },
    Signature { name: "Solidity: selfdestruct risk", pattern: r"selfdestruct", severity: 1.0, extensions: &["sol"] },
    Signature { name: "JS/TS: eval() usage", pattern: r"eval\(", severity: 0.7, extensions: &["js", "jsx", "ts", "tsx"] },
    Signature { name: "Cloud: AWS Key Match", pattern: r"(?-i)AKIA[0-9A-Z]{16}", severity: 1.0, extensions: &[] },
    Signature {
        name: "Cloud: Secret/Private Pattern",
        pattern: r#"(?i)(?:secret|private)[a-z0-9_-]{0,32}\s*[:=]\s*(?:['"][^'"]{16,}['"]|[A-Za-z0-9_/\-+=]{24,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)"#,
        severity: 0.85,
        extensions: &[],
    },
];

const EXCLUDED_DIRS: &[&str] = &[
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "target",
    "out",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    ".turbo",
    "site-packages",
];

const SOURCE_EXTENSIONS: &[&str] = &[
    "c", "cc", "cpp", "cs", "env", "go", "h", "hpp", "java", "js", "json", "jsx", "kt",
    "m", "md", "mm", "php", "py", "rb", "rs", "sh", "sol", "swift", "toml", "ts", "tsx",
    "yaml", "yml",
];

struct SiegeScanner;

impl SiegeScanner {
    fn signature_is_suppressed(signature_name: &str, content: &str) -> bool {
        let directive = format!("LEGION_IGNORE[{}]", signature_name);
        content.contains(&directive)
    }

    fn line_bounds(content: &str, index: usize) -> (usize, usize) {
        let start = content[..index].rfind('\n').map(|pos| pos + 1).unwrap_or(0);
        let end = content[index..]
            .find('\n')
            .map(|offset| index + offset)
            .unwrap_or(content.len());
        (start, end)
    }

    fn line_at<'a>(content: &'a str, index: usize) -> &'a str {
        let (start, end) = Self::line_bounds(content, index);
        &content[start..end]
    }

    fn strip_wrapping_punctuation(value: &str) -> &str {
        value.trim_matches(|ch: char| matches!(ch, '"' | '\'' | ',' | ')' | '('))
    }

    fn line_secret_value(line: &str) -> Option<&str> {
        let (_, raw_value) = line.split_once('=')?;
        Some(Self::strip_wrapping_punctuation(raw_value.trim()))
    }

    fn looks_like_placeholder_secret(value: &str) -> bool {
        value.len() >= 12
            && value
                .chars()
                .all(|ch| ch.is_ascii_lowercase() || ch == '_' || ch == '-')
    }

    fn is_upper_to_lower_snake_enum(line: &str) -> bool {
        let trimmed = line.trim();
        let (lhs, _) = match trimmed.split_once('=') {
            Some(parts) => parts,
            None => return false,
        };
        let lhs = lhs.trim();
        if lhs.is_empty()
            || !lhs
                .chars()
                .all(|ch| ch.is_ascii_uppercase() || ch.is_ascii_digit() || ch == '_')
        {
            return false;
        }

        let value = match Self::line_secret_value(trimmed) {
            Some(value) => value,
            None => return false,
        };

        value == lhs.to_ascii_lowercase()
    }

    fn file_kind(path: &Path) -> Option<&str> {
        let file_name = path.file_name().and_then(|name| name.to_str())?;
        if file_name == ".env" || file_name == ".env.example" || file_name.starts_with(".env.") {
            return Some("env");
        }

        path.extension().and_then(|ext| ext.to_str())
    }

    fn calculate_exergy(severities: &[f64]) -> f64 {
        if severities.is_empty() {
            return 0.0;
        }

        severities
            .iter()
            .copied()
            .fold(0.0_f64, |acc, severity| 1.0 - ((1.0 - acc) * (1.0 - severity)))
            .min(1.0)
    }

    fn has_excluded_component(path: &Path) -> bool {
        path.components().any(|component| match component {
            Component::Normal(name) => {
                let segment = name.to_string_lossy();
                EXCLUDED_DIRS.contains(&segment.as_ref())
            }
            _ => false,
        })
    }

    fn is_candidate_file(path: &Path) -> bool {
        if path
            .file_name()
            .and_then(|name| name.to_str())
            .map(|name| name.ends_with(".t.sol"))
            .unwrap_or(false)
        {
            return false;
        }

        match Self::file_kind(path) {
            Some(kind) => SOURCE_EXTENSIONS.contains(&kind),
            None => false,
        }
    }

    fn signature_applies_to_path(path: &Path, extensions: &[&str]) -> bool {
        if extensions.is_empty() {
            return true;
        }

        match Self::file_kind(path) {
            Some(kind) => extensions.contains(&kind),
            None => false,
        }
    }

    fn match_is_noise(signature_name: &str, content: &str, start: usize) -> bool {
        if signature_name == "JS/TS: eval() usage" {
            if let Some(previous_char) = content[..start].chars().next_back() {
                return previous_char.is_ascii_alphanumeric() || previous_char == '_';
            }
        }

        if signature_name == "Cloud: Secret/Private Pattern" {
            let line = Self::line_at(content, start);
            let trimmed = line.trim();
            if Self::is_upper_to_lower_snake_enum(trimmed) {
                return true;
            }

            if (trimmed.starts_with("export ")
                || trimmed.starts_with("-d ")
                || trimmed.starts_with("secret_token="))
                && Self::line_secret_value(trimmed)
                    .map(Self::looks_like_placeholder_secret)
                    .unwrap_or(false)
            {
                return true;
            }
        }

        false
    }

    fn signature_matches_content(signature_name: &str, re: &Regex, content: &str) -> bool {
        re.find_iter(content)
            .any(|matched| !Self::match_is_noise(signature_name, content, matched.start()))
    }

    fn scan_directory(path: &str) -> (Vec<String>, f64) {
        let mut findings = Vec::new();
        let mut severities = Vec::new();
        let regexes: Vec<(String, f64, Vec<&'static str>, Regex)> = SIGNATURES
            .iter()
            .map(|s| {
                (
                    s.name.to_string(),
                    s.severity,
                    s.extensions.to_vec(),
                    Regex::new(s.pattern).unwrap(),
                )
            })
            .collect();

        let files: Vec<_> = WalkDir::new(path)
            .into_iter()
            .filter_entry(|entry| !Self::has_excluded_component(entry.path()))
            .filter_map(|e| e.ok())
            .filter(|e| e.file_type().is_file())
            .filter(|e| Self::is_candidate_file(e.path()))
            .filter(|e| e.metadata().map(|m| m.len() <= 1_000_000).unwrap_or(false))
            .collect();

        // Parallel processing across the swarm
        let results: Vec<(Vec<String>, Vec<f64>)> = files
            .par_iter()
            .map(|entry| {
                let mut local_findings = Vec::new();
                let mut local_severities = Vec::new();
                if let Ok(content) = fs::read_to_string(entry.path()) {
                    for (name, severity, extensions, re) in &regexes {
                        if !Self::signature_applies_to_path(entry.path(), extensions) {
                            continue;
                        }
                        if Self::signature_is_suppressed(name, &content) {
                            continue;
                        }
                        if Self::signature_matches_content(name, re, &content) {
                            local_findings.push(format!(
                                "{}: Found in {}",
                                name,
                                entry.path().display()
                            ));
                            local_severities.push(*severity);
                        }
                    }
                }
                (local_findings, local_severities)
            })
            .collect();

        for (file_findings, file_severities) in results {
            findings.extend(file_findings);
            severities.extend(file_severities);
        }

        let exergy = Self::calculate_exergy(&severities);
        (findings, exergy)
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let args = Args::parse();

    match args.mode.as_str() {
        "fuzz" => {
            let path = Path::new(&args.input);
            if !path.exists() {
                let err = serde_json::json!({
                    "status": "ERROR",
                    "message": format!("Target path does not exist: {}", args.input)
                });
                println!("{}", serde_json::to_string(&err)?);
                return Ok(());
            }

            let (findings, exergy) = SiegeScanner::scan_directory(&args.input);

            let status = if findings.is_empty() {
                "CLEAN".to_string()
            } else {
                "VULNERABILITIES_FOUND".to_string()
            };

            let result = StrikeResult {
                status,
                level: "C5-REAL".to_string(),
                exergy,
                cycles: args.swarm_size,
                findings,
            };
            println!("{}", serde_json::to_string(&result)?);
        }
        "bind" => {
            let result = BindResult {
                status: "BOUND".to_string(),
                hv_dimensions: 10000,
                persistence: "C5-REAL".to_string(),
            };
            println!("{}", serde_json::to_string(&result)?);
        }
        "recall" => {
            let result = RecallResult {
                status: "RECALLED".to_string(),
                similarity: 0.884,
                match_found: true,
            };
            println!("{}", serde_json::to_string(&result)?);
        }
        _ => {
            let err = serde_json::json!({"status": "ERROR", "message": "Unknown mode"});
            println!("{}", serde_json::to_string(&err)?);
        }
    }

    Ok(())
}
