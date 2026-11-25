//! C5-REAL Real-Time Semantic Auditor & Cognitive Diagnostics.

use crate::protocol::{Diagnostic, Position, Range};

pub struct DiagnosticEngine;

impl DiagnosticEngine {
    /// Audits a document's source code and returns C5-REAL diagnostics.
    pub fn audit_document(uri: &str, text: &str) -> Vec<Diagnostic> {
        let mut diagnostics = Vec::new();
        let lines: Vec<&str> = text.lines().collect();

        for (line_idx, line) in lines.iter().enumerate() {
            let line_num = line_idx as u32;

            // 1. Invariant: Forbidden naive unwrap() in Rust
            if uri.ends_with(".rs") && line.contains(".unwrap()") && !line.contains("// allow(unwrap)") {
                if let Some(col) = line.find(".unwrap()") {
                    diagnostics.push(Diagnostic {
                        range: Range {
                            start: Position { line: line_num, character: col as u32 },
                            end: Position { line: line_num, character: (col + 9) as u32 },
                        },
                        severity: Some(1), // Error
                        code: Some("C5-AX02-UNWRAP".to_string()),
                        source: Some("C5-REAL-Paracortex".to_string()),
                        message: "[C5-REAL Axiom 2] Confundir mapa con territorio: Prohibido '.unwrap()' en Ring-0. Usa 'expect(\"C5-REAL: ...\")' o bifurcación monotónica.".to_string(),
                    });
                }
            }

            // 2. Invariant: Floating point in Ring-0 / deterministic arithmetic
            if uri.ends_with(".rs") && (line.contains("f32") || line.contains("f64")) && !line.contains("// allow(float)") {
                if let Some(col) = line.find("f32").or_else(|| line.find("f64")) {
                    diagnostics.push(Diagnostic {
                        range: Range {
                            start: Position { line: line_num, character: col as u32 },
                            end: Position { line: line_num, character: (col + 3) as u32 },
                        },
                        severity: Some(2), // Warning
                        code: Some("C5-AX01-NON-DETERMINISTIC-FLOAT".to_string()),
                        source: Some("C5-REAL-Paracortex".to_string()),
                        message: "[C5-REAL Invariant] Aritmética no determinista: Punto flotante detectado. Prioriza Punto Fijo u enteros escalados (u64/u128).".to_string(),
                    });
                }
            }

            // 3. Invariant: Hardcoded absolute user paths
            if (line.contains("/Users/") || line.contains("/home/")) && !line.contains("Path.home()") && !line.contains("// allow(path)") {
                let pattern = if line.contains("/Users/") { "/Users/" } else { "/home/" };
                if let Some(col) = line.find(pattern) {
                    diagnostics.push(Diagnostic {
                        range: Range {
                            start: Position { line: line_num, character: col as u32 },
                            end: Position { line: line_num, character: (col + pattern.len() + 10) as u32 },
                        },
                        severity: Some(1), // Error
                        code: Some("C5-SEC-ABSOLUTE-PATH".to_string()),
                        source: Some("C5-REAL-Paracortex".to_string()),
                        message: "[C5-REAL SecOps] Ruta absoluta de usuario detectada. Viola portabilidad soberana. Usa Path.home() o REPO_ROOT.".to_string(),
                    });
                }
            }

            // 4. Invariant: Swallowed exceptions in Python
            if uri.ends_with(".py") && (line.trim() == "except:" || line.trim() == "except Exception:" || line.contains("except:") && line.contains("pass")) {
                diagnostics.push(Diagnostic {
                    range: Range {
                        start: Position { line: line_num, character: 0 },
                        end: Position { line: line_num, character: line.len() as u32 },
                    },
                    severity: Some(1), // Error
                    code: Some("C5-ENTROPY-SWALLOWED-EXC".to_string()),
                    source: Some("C5-REAL-Paracortex".to_string()),
                    message: "[C5-REAL Sumidero de Entropía] Prohibido 'except: pass'. Toda excepción debe registrarse causalmente en stderr o Ledger.".to_string(),
                });
            }
        }

        diagnostics
    }
}
