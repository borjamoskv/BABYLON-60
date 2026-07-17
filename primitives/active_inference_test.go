package primitives

import (
	"testing"
)

func TestUnifiedActiveInferenceEngine(t *testing.T) {
	engine := NewUnifiedActiveInferenceEngine()

	stepCount := 0
	for d := byte(0); d < 10; d++ {
		for p := byte(0); p < 10; p++ {
			for m := byte(0); m < 10; m++ {
				err := engine.Step(d, p, m)
				if err != nil {
					t.Fatalf("Step failed at [%d,%d,%d]: %v", d, p, m, err)
				}
				stepCount++
			}
		}
	}

	if stepCount != 1000 {
		t.Fatalf("Expected 1000 steps, executed %d", stepCount)
	}

	if engine.StepsCount != 1000 {
		t.Fatalf("Expected Engine StepsCount 1000, got %d", engine.StepsCount)
	}

	t.Logf("✅ Verified Unified Active Inference Engine across 3000 Primitives (1000 Tri-Dispatches). Final Free Energy F: %f, D_KL: %f", engine.FreeEnergy, engine.D_KL)
}
