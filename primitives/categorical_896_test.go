package primitives

import (
	"math"
	"testing"
)

func TestCategorical896Processor(t *testing.T) {
	proc := NewCategorical896Processor()

	if len(proc.primitives) != 896 {
		t.Fatalf("Expected 896 primitives, got %d", len(proc.primitives))
	}

	cost := proc.CalculateMorphismCost([]int{1, 2, 3}, 0.5)
	if cost != 3.5 {
		t.Fatalf("Expected cost 3.5, got %f", cost)
	}

	emptyCost := proc.CalculateMorphismCost([]int{}, 0.0)
	if !math.IsInf(emptyCost, 1) {
		t.Fatalf("Expected Inf cost for empty sequence, got %f", emptyCost)
	}

	collisions := proc.DetectCollisionsConcurrent([]int{561, 562, 673})
	if collisions != 2 {
		t.Fatalf("Expected 2 collisions, got %d", collisions)
	}
}
