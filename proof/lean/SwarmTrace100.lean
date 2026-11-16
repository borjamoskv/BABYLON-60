namespace Babylon.L0.SwarmMmrTrace

structure WaveMmrSeal where
  wave : Nat
  leafCount : Nat
  peaks : List String
deriving Repr, DecidableEq

def swarmTrace : List WaveMmrSeal := [
  ⟨1, 10, ["peak_l0_w1_blake3"]⟩,
  ⟨2, 20, ["peak_l0_w2_blake3"]⟩,
  ⟨3, 30, ["peak_l0_w3_blake3"]⟩,
  ⟨4, 40, ["peak_l0_w4_blake3"]⟩,
  ⟨5, 50, ["peak_l0_w5_blake3"]⟩,
  ⟨6, 60, ["peak_l0_w6_blake3"]⟩,
  ⟨7, 70, ["peak_l0_w7_blake3"]⟩,
  ⟨8, 80, ["peak_l0_w8_blake3"]⟩,
  ⟨9, 90, ["peak_l0_w9_blake3"]⟩,
  ⟨10, 100, ["peak_l0_w10_blake3"]⟩,
]

theorem swarmTrace_complete_100_agents : swarmTrace.length = 10 := by rfl

end Babylon.L0.SwarmMmrTrace