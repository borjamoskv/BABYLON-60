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
	// q(S) = N(mu_q, Sigma_q) from StateVector (estimated state)
	// p(S) = N(mu_p, Sigma_p) representing target prior cognitive states
	// mu_q = e.StateVector.States
	// Sigma_q = e.StateVector.Covariance
	// mu_p = [HomeostasisEnergy, AttentionWeight, ActionTorque, LanguageEntropy]
	
	// Rigorous closed-form D_KL for 4D Gaussians assuming Sigma_p = Identity for stabilization
	// D_KL = 0.5 * [ tr(Sigma_q) + mu_diff^T * mu_diff - 4 - ln(det(Sigma_q)) ]
	
	trSigmaQ := 0.0
	for i := 0; i < 4; i++ {
		trSigmaQ += e.StateVector.Covariance[i][i]
	}
	
	muP := [4]float64{
		e.CognitiveChainVector.HomeostasisEnergy,
		e.CognitiveChainVector.AttentionWeight,
		e.CognitiveChainVector.ActionTorque,
		e.CognitiveChainVector.LanguageEntropy,
	}
	
	mahalanobis := 0.0
	for i := 0; i < 4; i++ {
		diff := e.StateVector.States[i] - muP[i]
		mahalanobis += diff * diff // mu_diff^T * Sigma_p^-1 * mu_diff where Sigma_p = I
	}
	
	// Determinant approximation of Sigma_q (diagonal product since it dominates)
	detSigmaQ := 1.0
	for i := 0; i < 4; i++ {
		detSigmaQ *= math.Max(1e-5, e.StateVector.Covariance[i][i])
	}
	
	e.D_KL = 0.5 * (trSigmaQ + mahalanobis - 4.0 - math.Log(detSigmaQ))
	if e.D_KL < 0 {
		e.D_KL = 0.0 // Numerical lower bound
	}

	ttsEfficiency := e.TTSHarnessState.KVCacheEfficiency
	e.ExpectedLogLikelihood = math.Log(math.Max(0.001, ttsEfficiency))
	e.FreeEnergy = e.D_KL - e.ExpectedLogLikelihood

	return nil
}
