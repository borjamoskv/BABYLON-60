// C5-REAL EXERGY CERTIFIED
// INV-3 POPPER: All theoretical invariants must be empirically falsifiable.
package primitives

import (
	"sync"
	"testing"
)

func TestEntelecheiaTransition(t *testing.T) {
	proc := NewCategoricalProcessor()

	// Force transition from Dynamis -> Entelecheia
	err := proc.ExecuteEntelecheia([]byte("semantic_payload"))
	if err != nil {
		t.Fatalf("Failed Entelecheia CAS transition: %v", err)
	}

	epoch, status := proc.ReadState()
	if epoch != 1 || status != StatusActive {
		t.Fatalf("Expected Epoch 1 and StatusActive (4), got Epoch %d, Status %d", epoch, status)
	}
}

func TestPrimumMovensFailStop(t *testing.T) {
	proc := NewCategoricalProcessor()

	// Initial Entelecheia
	proc.ExecuteEntelecheia([]byte("valid_payload"))

	activeManifest := proc.ActiveEpochPtr.Load()

	// Trigger the Limit / Adjunction (Primum Movens)
	proc.TriggerPrimumMovens()

	if activeManifest.StatusFlag.Load() != StatusQuarantine {
		t.Fatalf("Expected old manifest to be in Quarantine (6), got %d", activeManifest.StatusFlag.Load())
	}

	// Active epoch should now be the fallback (Idle state, Epoch 0)
	epoch, status := proc.ReadState()
	if epoch != 0 || status != StatusIdle {
		t.Fatalf("Expected rollback to Idle Fallback, got Epoch %d, Status %d", epoch, status)
	}
}

func TestConcurrentLockFreeEBR(t *testing.T) {
	proc := NewCategoricalProcessor()

	var wg sync.WaitGroup
	const readers = 100
	wg.Add(readers + 1)

	// Single writer pushing Entelecheia and triggering Primum Movens randomly
	go func() {
		defer wg.Done()
		for i := 0; i < 50; i++ {
			_ = proc.ExecuteEntelecheia([]byte("payload"))
			if i%10 == 0 {
				proc.TriggerPrimumMovens()
			}
			// Reset for next test loop
			proc.ActiveEpochPtr.Load().StatusFlag.Store(StatusIdle)
		}
	}()

	// Multiple readers reading state concurrently (lock-free)
	for i := 0; i < readers; i++ {
		go func() {
			defer wg.Done()
			for j := 0; j < 50; j++ {
				_, _ = proc.ReadState()
			}
		}()
	}

	wg.Wait()
}
