package primitives

import (
	"testing"
)

func TestInitAndResolveAll10000(t *testing.T) {
	InitKernel()

	for d := byte(0); d < 10; d++ {
		for p := byte(0); p < 10; p++ {
			for m := byte(0); m < 10; m++ {
				for tgt := byte(0); tgt < 10; tgt++ {
					identity, err := ResolveIdentity(d, p, m, tgt)
					if err != nil {
						t.Fatalf("Failed to resolve identity for %d %d %d %d: %v", d, p, m, tgt, err)
					}

					code := uint16(d)*1000 + uint16(p)*100 + uint16(m)*10 + uint16(tgt)
					if identity.Code != code {
						t.Errorf("Expected code %d, got %d", code, identity.Code)
					}

					// Test dispatch
					err = Dispatch(d, p, m, tgt)
					if err != nil {
						t.Errorf("Failed to dispatch %d %d %d %d: %v", d, p, m, tgt, err)
					}
				}
			}
		}
	}
}

func TestResolveOutOfRange(t *testing.T) {
	_, err := ResolveIdentity(10, 0, 0, 0)
	if err == nil {
		t.Error("Expected error for out-of-range domain")
	}
	
	_, err = ResolveIdentity(0, 10, 0, 0)
	if err == nil {
		t.Error("Expected error for out-of-range primitive")
	}
	
	_, err = ResolveIdentity(0, 0, 10, 0)
	if err == nil {
		t.Error("Expected error for out-of-range modifier")
	}
	
	_, err = ResolveIdentity(0, 0, 0, 10)
	if err == nil {
		t.Error("Expected error for out-of-range target")
	}
}
