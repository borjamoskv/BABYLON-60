//! Dispatch-level checks for C0442 and related runtime guards: each program runs through the
//! real binary (critical halts end the process), in a temporary working directory.
use std::process::{Command, Output};

fn run(program: &str) -> Output {
    let dir = std::env::temp_dir().join(format!(
        "b60_dispatch_{}_{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    std::fs::create_dir(&dir).unwrap();
    let script = dir.join("prog.b60");
    std::fs::write(&script, program).unwrap();
    let out = Command::new(env!("CARGO_BIN_EXE_babylon60-runtime"))
        .arg(&script)
        .current_dir(&dir)
        .output()
        .unwrap();
    let _ = std::fs::remove_dir_all(&dir);
    out
}

fn stdout(out: &Output) -> String {
    String::from_utf8_lossy(&out.stdout).into_owned()
}

/// Valor entero como literal base 60 del runtime ('<' = 10, 'Y' = 1, '-' = 0).
fn b60_literal(mut v: u64) -> String {
    let mut digits = Vec::new();
    loop {
        digits.push(v % 60);
        v /= 60;
        if v == 0 {
            break;
        }
    }
    let places: Vec<String> = digits
        .iter()
        .rev()
        .map(|d| {
            if *d == 0 {
                "-".to_string()
            } else {
                "<".repeat((*d / 10) as usize) + &"Y".repeat((*d % 10) as usize)
            }
        })
        .collect();
    format!("[ {} ]", places.join(" "))
}

/// R1 = 1/60 mediante BA.EXACT (los literales siempre tienen escala 0).
const ONE_SIXTIETH: &str =
    "ALLOC F60 R1\nALLOC F60 R2\nNIG R1 [ Y ]\nNIG R2 [ Y - ]\nBA.EXACT R1 R2\n";

fn tick_of_done(out: &Output) -> u64 {
    let text = stdout(out);
    let line = text
        .lines()
        .find(|l| l.contains("DONE (Tick:"))
        .unwrap_or_else(|| panic!("sin DONE: {text}"));
    line.rsplit("Tick: ")
        .next()
        .unwrap()
        .trim_end_matches(')')
        .parse()
        .unwrap()
}

#[test]
fn nig_multiplier_scale_reaches_the_interpreter() {
    // R0 = 60 × (1/60) = 1: AFTER espera 1 tick. Con la escala ignorada, R0 = 60 y espera 60.
    let program = format!(
        "DUB\nMUB MAIN\nALLOC F60 R0\n{ONE_SIXTIETH}NIG R0 [ Y - ] R1\nAFTER R0 DONE\nMUB DONE\nEXECUTE \"DONE\"\nHALT\n"
    );
    let out = run(&program);
    assert!(out.status.success(), "{}", stdout(&out));
    assert!(
        tick_of_done(&out) < 30,
        "C0442: el multiplicador con escala no llegó al intérprete"
    );
}

#[test]
fn after_rejects_a_fractional_tick_count_in_the_interpreter() {
    let program =
        format!("DUB\nMUB MAIN\n{ONE_SIXTIETH}AFTER R1 DONE\nMUB DONE\nEXECUTE \"DONE\"\nHALT\n");
    let out = run(&program);
    assert!(
        !out.status.success(),
        "C0442: AFTER aceptó 1/60 de tick: {}",
        stdout(&out)
    );
    assert!(stdout(&out).contains("AFTER: el número de ticks debe ser entero"));
}

#[test]
fn after_wake_tick_overflow_is_a_critical_halt() {
    let program = format!(
        "DUB\nMUB MAIN\nALLOC I64 R0\nNIG R0 {}\nAFTER R0 DONE\nMUB DONE\nEXECUTE \"DONE\"\nHALT\n",
        b60_literal(u64::MAX)
    );
    let out = run(&program);
    assert_eq!(
        out.status.code(),
        Some(1),
        "esperado halt crítico: {}",
        stdout(&out)
    );
    assert!(stdout(&out).contains("desborda u64"), "{}", stdout(&out));
}

#[test]
fn repeated_squaring_cannot_grow_the_scale_without_bound() {
    let program = format!(
        "DUB\nMUB MAIN\n{ONE_SIXTIETH}{}HALT\n",
        "NIG R1 R1 R1\n".repeat(8)
    );
    let out = run(&program);
    assert_eq!(
        out.status.code(),
        Some(1),
        "esperado halt crítico: {}",
        stdout(&out)
    );
    assert!(
        stdout(&out).contains("FALSATION_ERROR: TRUNCATION"),
        "{}",
        stdout(&out)
    );
}

#[test]
fn command_missing_operands_is_a_critical_halt_not_a_panic() {
    let out =
        run("DUB\nMUB MAIN\nALLOC F60 R1\nNIG R1 # el comentario se lleva el operando\nHALT\n");
    assert_eq!(
        out.status.code(),
        Some(1),
        "esperado halt crítico, no pánico: {}",
        stdout(&out)
    );
    assert!(stdout(&out).contains("ARITY_ERROR"), "{}", stdout(&out));
}
