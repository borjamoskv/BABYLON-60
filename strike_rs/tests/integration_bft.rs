use strike_rs::ledger::MasterLedger;
use strike_rs::atms::Atms;
use strike_rs::omega0::{Statement, Modality, Justification, JustifiedStatement};

#[test]
fn test_integration_full_bft_ledger_to_atms_flow() {
    let db_path = ":memory:";
    let mut ledger = MasterLedger::new(db_path).unwrap();
    let mut atms = Atms::new();

    // 1. Inyectar Statement Epistémico
    let stmt1 = Statement {
        content: "Axioma BFT: El sistema tolera f < n/3".into(),
        modality: Modality::Epistemic,
        obligations: vec![],
    };
    let js1 = JustifiedStatement {
        statement: stmt1.clone(),
        justification: Justification::Axiom { domain: "Consenso".into() },
    };

    let env_id = "env_bft_test";
    
    // 2. Aserción en Master Ledger
    let taint1 = ledger.assert_knowledge(&js1, env_id).unwrap();
    assert!(taint1.contains("-") || taint1.starts_with("TAINT"));
    
    // 3. Instalación en ATMS
    let node1 = atms.add_premise(&stmt1.content);
    assert!(atms.is_believed(node1));

    // 4. Inyectar Conjetura (Nogood potencial)
    let stmt2 = Statement {
        content: "Axioma Falso: f = n/2".into(),
        modality: Modality::Epistemic,
        obligations: vec![],
    };
    let js2 = JustifiedStatement {
        statement: stmt2.clone(),
        justification: Justification::Conjecture,
    };
    
    let taint2 = ledger.assert_knowledge(&js2, env_id).unwrap();
    assert!(taint2.contains("-") || taint2.starts_with("TAINT"));
    
    let node2 = atms.add_assumption(&stmt2.content);
    assert!(atms.is_believed(node2));

    // 5. Inyectar contradicción desde el ledger al ATMS
    let stmt2_hash = MasterLedger::hash_statement(&stmt2);
    let taint_nogood = ledger.assert_nogood(&stmt2_hash, env_id).unwrap();
    assert!(taint_nogood.contains(":NOGOOD:"));

    atms.contradict(&[node2]);

    // 6. Verificación de Invariantes DDB y Chain
    assert!(!atms.is_believed(node2), "El nodo conjeturado debe perder su etiqueta (Label) tras el Nogood");
    assert!(atms.is_believed(node1), "El axioma base debe permanecer creído (DDB)");
    assert!(ledger.verify_chain(env_id).is_ok(), "La cadena de hashes debe ser válida");
}
