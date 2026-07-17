package primitives

import (
	"errors"
	"math"
)

type UnifiedActiveInferenceEngine struct {
	StateVector          *StateVector
	CognitiveChainVector *CognitiveChainVector
	TTSHarnessState      *TTSHarnessState
	FreeEnergy           float64
	D_KL                 float64
	ExpectedLogLikelihood float64
	StepsCount           uint64
}

func NewUnifiedActiveInferenceEngine() *UnifiedActiveInferenceEngine {
	InitStateObserverKernel()
	InitNeuroChainKernel()
	InitTTSHarnessKernel()

	return &UnifiedActiveInferenceEngine{
		StateVector:          &StateVector{},
		CognitiveChainVector: &CognitiveChainVector{},
		TTSHarnessState:      &TTSHarnessState{},
		FreeEnergy:           0.0,
		D_KL:                 0.0,
		ExpectedLogLikelihood: 0.0,
		StepsCount:           0,
	}
}

func (e *UnifiedActiveInferenceEngine) Step(d, p, m byte) error {
	if d > 9 || p > 9 || m > 9 {
		return errors.New("indices out of bounds [0-9]")
	}

	err := DispatchStateObserver(d, p, m, e.StateVector)
	if err != nil {
		return err
	}

	err = DispatchNeuroChain(d, p, m, e.CognitiveChainVector)
	if err != nil {
		return err
	}

	err = DispatchTTSHarness(d, p, m, e.TTSHarnessState)
	if err != nil {
		return err
	}

	e.StepsCount++

	// Compute Variational Free Energy F = D_KL - E[ln p(O|S)]
	obsNorm := e.StateVector.NormError
	neuroNorm := e.CognitiveChainVector.PredictionError
	ttsEfficiency := e.TTSHarnessState.KVCacheEfficiency

	// Divergence D_KL
	e.D_KL = math.Abs(obsNorm - neuroNorm)
	// Expected Log Likelihood
	e.ExpectedLogLikelihood = math.Log(math.Max(0.001, ttsEfficiency))
	// Free Energy F
	e.FreeEnergy = e.D_KL - e.ExpectedLogLikelihood

	return nil
}
