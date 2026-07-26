// C5-REAL EXERGY CERTIFIED
package main

import (
	"math/rand"
	"testing"
)

func TestRobinsonResolutionUnit(t *testing.T) {
	rng := rand.New(rand.NewSource(42))
	clauses := generateContradiction(rng)

	if len(clauses) != 4 {
		t.Fatalf("expected 4 clauses, got %d", len(clauses))
	}

	ok := tryRefute(clauses)
	if !ok {
		t.Errorf("expected contradiction to be refuted, got false")
	}
}

func TestPercentile(t *testing.T) {
	latencies := []int64{10, 20, 30, 40, 50, 60, 70, 80, 90, 100}
	p50 := percentile(latencies, 50)
	if p50 != 50 && p50 != 60 {
		t.Errorf("unexpected p50: %d", p50)
	}
}
