// C5-REAL EXERGY CERTIFIED
// Suite de Falsación Popperiana para Legión Exergética
use std::mem::{size_of, align_of};
use std::path::PathBuf;

use legion_core::{SharedManifest, MerkleTree};
use legion_exergy::{ExergyEvaluator, RiskLevel};
use legion_apfs::FileMetadataEntry;
use legion_lang::{Lexer, Parser, Compiler, VirtualMachine, VmAction};

#[test]
fn test_silicon_alignment_manifest_64b() {
    assert_eq!(size_of::<SharedManifest>(), 64, "SharedManifest DEBE ser exactamente de 64 bytes");
    assert_eq!(align_of::<SharedManifest>(), 64, "SharedManifest DEBE estar alineado a 64 bytes para evitar false sharing");
}

#[test]
fn test_scitt_merkle_tree_reproducibility() {
    let mut tree = MerkleTree::new();
    let r1 = tree.create_receipt("SAFE_TRASH", "/Library/Caches/com.adobe.PS/temp.bin", 1048576, 0.01);
    let r2 = tree.create_receipt("SAFE_TRASH", "/Library/Caches/Slack/GPUCache/data_0", 2097152, 0.02);

    let root = tree.compute_root();
    assert_eq!(root.len(), 32);
    assert!(r1.leaf_hash.len() > 0);
    assert!(r2.leaf_hash.len() > 0);
}

#[test]
fn test_immunity_shield_rejection_of_critical_paths() {
    let immune_paths = [
        "/Users/user/.ssh/id_rsa",
        "/Users/user/.ssh/known_hosts",
        "/Users/user/.gnupg/secring.gpg",
        "/Users/user/Library/Keychains/login.keychain-db",
        "/Users/user/Documents/Thesis.docx",
        "/Users/user/Desktop/Notes.txt",
        "/Applications/Xcode.app/Contents/_CodeSignature/CodeResources",
    ];

    for path_str in &immune_paths {
        let path = PathBuf::from(path_str);
        assert!(ExergyEvaluator::is_strictly_immune(&path), "Ruta {} DEBE ser inmune", path_str);

        let score = ExergyEvaluator::evaluate_file(&path, 1024, 0, 0, true);
        assert_eq!(score.risk, RiskLevel::Red, "Ruta {} DEBE tener RiskLevel::Red", path_str);
        assert!(!score.is_100pct_anergy, "Ruta {} NUNCA debe considerarse anergía", path_str);
    }
}

#[test]
fn test_exergyscript_compiler_rejects_immunity_violations() {
    let malicious_script = r#"
        rule MaliciousDropSSH {
            target = "~/.ssh/*"
            guard  = (age > 1d)
            action = SafeTrash
            attest = SCITT
        }
    "#;

    let mut lexer = Lexer::new(malicious_script);
    let tokens = lexer.tokenize().expect("Lexer failed");
    let mut parser = Parser::new(tokens);
    let program = parser.parse_program().expect("Parser failed");

    let compile_result = Compiler::compile(&program);
    assert!(compile_result.is_err(), "El compilador DEBE rechazar la regla maliciosa contra .ssh");
}

#[test]
fn test_exergyscript_end_to_end_vm_execution() {
    let safe_script = r#"
        rule CleanAdobeCache {
            target = "Library/Caches/com.adobe.*"
            guard  = (age > 14d) && (!is_locked)
            action = SafeTrash
            attest = SCITT
        }
    "#;

    let mut lexer = Lexer::new(safe_script);
    let tokens = lexer.tokenize().expect("Lexer failed");
    let mut parser = Parser::new(tokens);
    let program = parser.parse_program().expect("Parser failed");
    let compiled = Compiler::compile(&program).expect("Compilación falló");

    // Inodo antiguo -> Debería purgar
    let old_entry = FileMetadataEntry {
        path: PathBuf::from("/Users/user/Library/Caches/com.adobe.PS/old.tmp"),
        size_bytes: 50 * 1024 * 1024,
        is_dir: false,
        access_time_epoch: 1000,
        modify_time_epoch: 1000,
        inode: 99991,
    };

    let (action, rule) = VirtualMachine::evaluate_entry(&compiled, &old_entry);
    assert_eq!(action, VmAction::SafeTrash);
    assert_eq!(rule, Some("CleanAdobeCache".to_string()));

    // Inodo reciente -> Debería ignorar
    let recent_entry = FileMetadataEntry {
        path: PathBuf::from("/Users/user/Library/Caches/com.adobe.PS/hot.tmp"),
        size_bytes: 50 * 1024 * 1024,
        is_dir: false,
        access_time_epoch: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs(),
        modify_time_epoch: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs(),
        inode: 99992,
    };

    let (action_recent, _) = VirtualMachine::evaluate_entry(&compiled, &recent_entry);
    assert_eq!(action_recent, VmAction::Ignore, "Archivos recientes no deben ser purgados");
}
