// C5-REAL EXERGY CERTIFIED
// INV-3 POPPER: All theoretical invariants must be empirically falsifiable. Continuous metaphors are rejected.
package primitives

import (
	"testing"
)

type SubsystemTestCase struct {
	Name         string
	Init         func()
	Dispatch     func(d, p, m byte) error
	GetExecCount func(code uint16) uint64
}

func TestSubsystemKernelsTableDriven(t *testing.T) {
	subsystems := []SubsystemTestCase{
		{
			Name: "Haskell",
			Init: InitHaskellKernel,
			Dispatch: func(d, p, m byte) error {
				return DispatchHaskell(d, p, m, &HaskellStateVector{})
			},
			GetExecCount: GetHaskellExecutionCount,
		},
		{
			Name: "Kimi",
			Init: InitKimiKernel,
			Dispatch: func(d, p, m byte) error {
				return DispatchKimi(d, p, m, &KimiStateVector{})
			},
			GetExecCount: GetKimiExecutionCount,
		},
		{
			Name: "NeuroChain",
			Init: InitNeuroChainKernel,
			Dispatch: func(d, p, m byte) error {
				return DispatchNeuroChain(d, p, m, &CognitiveChainVector{})
			},
			GetExecCount: GetNeuroChainExecutionCount,
		},
		{
			Name: "Noether",
			Init: InitNoetherKernel,
			Dispatch: func(d, p, m byte) error {
				return DispatchNoether(d, p, m, &NoetherStateVector{})
			},
			GetExecCount: GetNoetherExecutionCount,
		},
		{
			Name: "Observer",
			Init: InitStateObserverKernel,
			Dispatch: func(d, p, m byte) error {
				return DispatchStateObserver(d, p, m, &StateVector{})
			},
			GetExecCount: GetStateObserverExecutionCount,
		},
		{
			Name: "Playwright",
			Init: InitPlaywrightKernel,
			Dispatch: func(d, p, m byte) error {
				return DispatchPlaywright(d, p, m, &PlaywrightStateVector{})
			},
			GetExecCount: GetPlaywrightExecutionCount,
		},
		{
			Name: "TTSHarness",
			Init: InitTTSHarnessKernel,
			Dispatch: func(d, p, m byte) error {
				return DispatchTTSHarness(d, p, m, &TTSHarnessState{})
			},
			GetExecCount: GetTTSHarnessExecutionCount,
		},
		{
			Name: "Constants",
			Init: InitConstantsKernel,
			Dispatch: func(d, p, m byte) error {
				return DispatchConstants(d, p, m, &ConstantsStateVector{})
			},
			GetExecCount: GetConstantsExecutionCount,
		},
	}

	for _, tc := range subsystems {
		tc := tc
		t.Run(tc.Name, func(t *testing.T) {
			tc.Init()
			count := 0
			for d := byte(0); d < 10; d++ {
				for p := byte(0); p < 10; p++ {
					for m := byte(0); m < 10; m++ {
						err := tc.Dispatch(d, p, m)
						if err != nil {
							t.Fatalf("Failed to dispatch %s primitives [%d,%d,%d]: %v", tc.Name, d, p, m, err)
						}
						code := uint16(d)*100 + uint16(p)*10 + uint16(m)
						execCount := tc.GetExecCount(code)
						if execCount < 1 {
							t.Errorf("Expected execution count >= 1 for code %d in %s, got %d", code, tc.Name, execCount)
						}
						count++
					}
				}
			}
			if count != 1000 {
				t.Fatalf("Expected 1000 %s primitives tested, got %d", tc.Name, count)
			}
			t.Logf("✅ Successfully verified 100%% execution coverage across all 1000 %s Primitives.", tc.Name)
		})
	}
}
