package main

import (
	"path/filepath"
	"testing"
)

func TestVerifyPrimitiveP2P_HonestPeers(t *testing.T) {
	res := VerifyPrimitiveP2P(1, 0, "T01_Causal_Ontology_Pearl", false)
	if res.QuorumMatch != "3/3" {
		t.Fatalf("Esperado Quorum 3/3 en nodos honestos, obtenido: %s (Veredicto: %s)", res.QuorumMatch, res.ConsensusVerd)
	}
	if res.PeerAlphaHash != res.PeerBetaHash || res.PeerAlphaHash != res.PeerGammaHash {
		t.Fatalf("Discrepancia en hashes Merkle de nodos honestos: A=%s, B=%s, G=%s", res.PeerAlphaHash, res.PeerBetaHash, res.PeerGammaHash)
	}
}

func TestVerifyPrimitiveP2P_ByzantineResilience(t *testing.T) {
	res := VerifyPrimitiveP2P(100, 0, "T01_Causal_Ontology_Pearl", true)
	if res.QuorumMatch != "2/3" {
		t.Fatalf("Esperada Tolerancia Bizantina Quorum 2/3 tras deriva de Node Gamma, obtenido: %s (Veredicto: %s)", res.QuorumMatch, res.ConsensusVerd)
	}
	if res.PeerAlphaHash != res.PeerBetaHash {
		t.Fatalf("Discrepancia entre nodos honestos en escenario bizantino: A=%s, B=%s", res.PeerAlphaHash, res.PeerBetaHash)
	}
	if res.PeerGammaHash == res.PeerAlphaHash {
		t.Fatalf("Node Gamma debía presentar deriva bizantina (sensor drift), pero coincide con Alpha")
	}
}

func TestDatabaseWALPersistence(t *testing.T) {
	dbPath := filepath.Join("..", "nexus_anchors.db")
	db, err := InitDB(dbPath)
	if err != nil {
		t.Fatalf("Error inicializando Master Ledger SQLite WAL en Go: %v", err)
	}
	defer db.Close()

	var count int
	err = db.QueryRow("SELECT count(*) FROM p2p_1000_primitives_go_ledger").Scan(&count)
	if err != nil {
		t.Fatalf("Error consultando tabla de ledger Go: %v", err)
	}
	t.Logf("Registros existentes en tabla Go WAL: %d", count)
}
