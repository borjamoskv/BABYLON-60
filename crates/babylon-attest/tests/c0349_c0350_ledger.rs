//! C0349 / C0350: ledger exclusion across processes and observable write errors.
//!
//! The parent test spawns this same test binary as child writers, so the exclusion is
//! exercised between real processes sharing one BABYLON_HOME. Temporary fixture only.
use babylon_attest::ledger::{append_event, get_chain_blocks, verify_chain};
use std::process::Command;

const CHILD_ENV: &str = "C0349_CHILD_APPENDS";
const WRITERS: usize = 4;
const APPENDS_PER_WRITER: usize = 25;

/// Child role: when the parent sets CHILD_ENV, append that many events and exit.
#[test]
fn child_append() {
    let Ok(count) = std::env::var(CHILD_ENV) else {
        return;
    };
    let count: usize = count.parse().expect("child append count");
    for n in 0..count {
        append_event(serde_json::json!({"writer": std::process::id(), "n": n}))
            .expect("child append");
    }
}

#[test]
fn ledger_exclusion_and_observable_errors() {
    if std::env::var(CHILD_ENV).is_ok() {
        return; // child processes only run `child_append`
    }
    let home = std::env::temp_dir().join(format!("c0349-ledger-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&home);
    std::env::set_var("BABYLON_HOME", &home);

    // C0349: several processes append concurrently to the same ledger.
    let children: Vec<_> = (0..WRITERS)
        .map(|_| {
            Command::new(std::env::current_exe().unwrap())
                .args(["child_append", "--exact", "--test-threads=1"])
                .env("BABYLON_HOME", &home)
                .env(CHILD_ENV, APPENDS_PER_WRITER.to_string())
                .spawn()
                .expect("spawn child writer")
        })
        .collect();
    for mut child in children {
        assert!(child.wait().unwrap().success(), "child writer failed");
    }

    let blocks = get_chain_blocks().expect("chain readable after concurrent writers");
    let expected = WRITERS * APPENDS_PER_WRITER;
    assert_eq!(
        blocks.len(),
        expected,
        "C0349: bloques perdidos o duplicados"
    );
    for (position, block) in blocks.iter().enumerate() {
        assert_eq!(
            block.index, position as u64,
            "C0349: índice no contiguo (bifurcación)"
        );
        if position > 0 {
            assert_eq!(
                block.prev_hash,
                blocks[position - 1].block_hash,
                "C0349: cadena bifurcada"
            );
        }
    }
    let report = verify_chain().expect("verify_chain");
    assert!(report.valid);
    assert_eq!(report.total_blocks, expected as u64);

    // C0350: a write that cannot happen is an error, never a confirmed block.
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let ledger = babylon_attest::env::ledger_file();
        std::fs::set_permissions(&ledger, std::fs::Permissions::from_mode(0o444)).unwrap();
        let denied = append_event(serde_json::json!({"must": "fail"}));
        std::fs::set_permissions(&ledger, std::fs::Permissions::from_mode(0o644)).unwrap();
        assert!(
            denied.is_err(),
            "C0350: escritura imposible confirmada como éxito"
        );
        assert_eq!(
            get_chain_blocks().unwrap().len(),
            expected,
            "C0350: bloque fantasma"
        );
    }

    let _ = std::fs::remove_dir_all(&home);
}
