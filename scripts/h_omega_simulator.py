#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
  C5-REAL v2.0 · Regulatory Fragility Simulator (H_Ω Falsification Engine)
═══════════════════════════════════════════════════════════════════════════

  Dynamic System:
    X_t = (S_t, R_t, Ω_t, ℛ_t)

  Equations:
    S_{t+1} = F(S_t, R_t, D_t)
    R_{t+1} = G(R_t, S_{t+1})
    Ω_t     = P_n / (w_I·I_n + w_A·A_d + w_F·F_g)
    ℛ_{t+1} = ℛ_t + G_recovery - G_depletion(L, ||D||, Ω)
    L_t     = L(S_t, S*_t)
    J_t     = α·Ω_t + β·L_t + γ·C_t

  Hypotheses Under Falsification:
    H1: corr(Ω, L) > 0                    (descriptive validity)
    H2: ∂L/∂Ω | {I,A,F,R,V,D} > 0        (causal robustness)
    H3: Ω > Ω* ∧ ℛ < ℛ* ⟹ dℛ/dt < 0     (exhaustion dynamics)

  Author: C5-REAL Epistemic Engine
  Date:   2026-08-17
  Status: FALSIFICATION_READY
═══════════════════════════════════════════════════════════════════════════
"""

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
from scipy import stats

# ─── Output directory ────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR.parent / "results" / "h_omega"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════
# §1  OPERATIONALIZATION: Variable Definitions
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class RegulatorParams:
    """Operationalized regulator variables, all normalized to (0, 1]."""
    P_n: float   # Normalized coercive power  P_c / P_ref
    I_n: float   # Informational resolution   ∈ (0, 1]
    A_d: float   # Adaptive rate              ∈ (0, 1]
    F_g: float   # Feedback fidelity          ∈ (0, 1]
    # Weights (must sum to 1)
    w_I: float = 0.40
    w_A: float = 0.30
    w_F: float = 0.30

    @property
    def omega(self) -> float:
        """Dimensionless Regulatory Fragility Index Ω."""
        denominator = self.w_I * self.I_n + self.w_A * self.A_d + self.w_F * self.F_g
        return self.P_n / max(denominator, 1e-12)

    def __post_init__(self):
        assert 0 < self.I_n <= 1, f"I_n must be in (0,1], got {self.I_n}"
        assert 0 < self.A_d <= 1, f"A_d must be in (0,1], got {self.A_d}"
        assert 0 < self.F_g <= 1, f"F_g must be in (0,1], got {self.F_g}"
        assert self.P_n >= 0,     f"P_n must be >= 0, got {self.P_n}"
        assert abs(self.w_I + self.w_A + self.w_F - 1.0) < 1e-9, "Weights must sum to 1"


@dataclass
class SystemState:
    """Full state vector X_t = (S_t, R_t, Ω_t, ℛ_t)."""
    S: float            # System state (deviation from target S*)
    regulator: RegulatorParams
    resilience: float   # ℛ_t ∈ [0, ∞)
    S_star: float = 0.0 # Target state

    @property
    def loss(self) -> float:
        """Regulatory loss L_t = |S_t - S*_t|²."""
        return (self.S - self.S_star) ** 2

    @property
    def omega(self) -> float:
        return self.regulator.omega

    @property
    def coordination_cost(self) -> float:
        """C_t: coordination cost grows with coercion and inversely with adaptation."""
        return self.regulator.P_n * (1.0 - self.regulator.A_d) * 0.5

    def J(self, alpha: float = 0.3, beta: float = 0.5, gamma: float = 0.2) -> float:
        """Multi-objective cost functional J_t = α·Ω + β·L + γ·C."""
        return alpha * self.omega + beta * self.loss + gamma * self.coordination_cost


# ═══════════════════════════════════════════════════════════════════════════
# §2  DYNAMICS: Transition Functions
# ═══════════════════════════════════════════════════════════════════════════

class C5DynamicalSystem:
    """
    Implements the coupled dynamical system:
      S_{t+1} = F(S_t, R_t, D_t)
      R_{t+1} = G(R_t, S_{t+1})
      ℛ_{t+1} = ℛ_t + G_recovery - G_depletion
    """

    def __init__(
        self,
        perturbation_std: float = 0.15,
        recovery_rate: float = 0.02,
        depletion_sensitivity: float = 0.08,
        regulator_learning_rate: float = 0.01,
        coercion_ratchet: float = 0.005,
        seed: Optional[int] = None,
    ):
        self.perturbation_std = perturbation_std
        self.recovery_rate = recovery_rate
        self.depletion_sensitivity = depletion_sensitivity
        self.regulator_learning_rate = regulator_learning_rate
        self.coercion_ratchet = coercion_ratchet
        self.rng = np.random.default_rng(seed)

    def step(self, state: SystemState) -> SystemState:
        """Advance the system by one timestep."""
        # ── Perturbation ──
        D_t = self.rng.normal(0, self.perturbation_std)

        # ── S_{t+1} = F(S_t, R_t, D_t) ──
        # The regulator applies a corrective force proportional to its
        # informational resolution and feedback fidelity, but the coercive
        # force introduces its own distortion (overshooting).
        correction = (
            state.regulator.I_n
            * state.regulator.F_g
            * (state.S_star - state.S)
            * 0.3
        )
        coercion_distortion = (
            state.regulator.P_n
            * (1.0 - state.regulator.I_n)
            * self.rng.normal(0, 0.1)
        )
        S_new = state.S + correction + coercion_distortion + D_t

        # ── R_{t+1} = G(R_t, S_{t+1}) ──
        # The regulator adapts (slowly) and ratchets up coercion when loss is high.
        loss_new = (S_new - state.S_star) ** 2
        new_P_n = state.regulator.P_n + self.coercion_ratchet * loss_new
        new_I_n = np.clip(
            state.regulator.I_n
            + self.regulator_learning_rate * state.regulator.A_d * (1.0 - state.regulator.I_n)
            - 0.005 * state.regulator.P_n,  # coercion degrades information
            0.01, 1.0
        )
        new_A_d = np.clip(
            state.regulator.A_d - 0.002 * state.regulator.P_n,  # coercion rigidifies
            0.01, 1.0
        )
        new_F_g = np.clip(
            state.regulator.F_g
            - 0.003 * state.regulator.P_n   # coercion degrades feedback
            + 0.005 * state.regulator.A_d,   # adaptation recovers feedback
            0.01, 1.0
        )

        new_regulator = RegulatorParams(
            P_n=new_P_n,
            I_n=new_I_n,
            A_d=new_A_d,
            F_g=new_F_g,
            w_I=state.regulator.w_I,
            w_A=state.regulator.w_A,
            w_F=state.regulator.w_F,
        )

        # ── ℛ_{t+1} = ℛ_t + G_recovery - G_depletion(L, ||D||, Ω) ──
        omega_t = new_regulator.omega
        G_recovery = self.recovery_rate * (1.0 + 0.5 * new_regulator.A_d)
        G_depletion = self.depletion_sensitivity * (
            loss_new + abs(D_t) * 0.3 + omega_t * 0.1
        )
        new_resilience = max(state.resilience + G_recovery - G_depletion, 0.0)

        return SystemState(
            S=S_new,
            regulator=new_regulator,
            resilience=new_resilience,
            S_star=state.S_star,
        )

    def simulate(self, initial_state: SystemState, T: int = 500) -> dict:
        """Run simulation for T timesteps, returning full trajectory."""
        trajectory = {
            "t": [], "S": [], "omega": [], "loss": [], "resilience": [],
            "J": [], "P_n": [], "I_n": [], "A_d": [], "F_g": [], "C": [],
        }
        state = initial_state
        for t in range(T):
            trajectory["t"].append(t)
            trajectory["S"].append(state.S)
            trajectory["omega"].append(state.omega)
            trajectory["loss"].append(state.loss)
            trajectory["resilience"].append(state.resilience)
            trajectory["J"].append(state.J())
            trajectory["P_n"].append(state.regulator.P_n)
            trajectory["I_n"].append(state.regulator.I_n)
            trajectory["A_d"].append(state.regulator.A_d)
            trajectory["F_g"].append(state.regulator.F_g)
            trajectory["C"].append(state.coordination_cost)
            state = self.step(state)

        return {k: np.array(v) for k, v in trajectory.items()}


# ═══════════════════════════════════════════════════════════════════════════
# §3  EXPERIMENTAL DESIGN: Four Regime Quadrants
# ═══════════════════════════════════════════════════════════════════════════

REGIMES = {
    "Q1_Adaptive": {
        "description": "Low Ω, High ℛ → Adaptive regime",
        "P_n": 0.3,  "I_n": 0.85, "A_d": 0.80, "F_g": 0.85,
        "resilience": 5.0,
        "color": "#2ecc71",
    },
    "Q2_Vulnerable": {
        "description": "Low Ω, Low ℛ → Vulnerable regime",
        "P_n": 0.3,  "I_n": 0.80, "A_d": 0.75, "F_g": 0.80,
        "resilience": 0.5,
        "color": "#f39c12",
    },
    "Q3_Authoritarian_Stable": {
        "description": "High Ω, High ℛ → Authoritarian but stable (petro-state)",
        "P_n": 3.0,  "I_n": 0.25, "A_d": 0.15, "F_g": 0.20,
        "resilience": 8.0,
        "color": "#e74c3c",
    },
    "Q4_Fragile_Collapsible": {
        "description": "High Ω, Low ℛ → Fragile / collapsible",
        "P_n": 3.0,  "I_n": 0.20, "A_d": 0.10, "F_g": 0.15,
        "resilience": 0.8,
        "color": "#8e44ad",
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# §4  HYPOTHESIS TESTING ENGINE
# ═══════════════════════════════════════════════════════════════════════════

def test_H1(trajectories: dict) -> dict:
    """
    H1 · Descriptive Validity: corr(Ω, L) > 0
    Pool all timesteps across all regimes and compute Pearson/Spearman.
    """
    all_omega = np.concatenate([t["omega"] for t in trajectories.values()])
    all_loss  = np.concatenate([t["loss"]  for t in trajectories.values()])

    pearson_r, pearson_p = stats.pearsonr(all_omega, all_loss)
    spearman_r, spearman_p = stats.spearmanr(all_omega, all_loss)

    result = {
        "hypothesis": "H1: corr(Ω, L) > 0",
        "pearson_r": float(pearson_r),
        "pearson_p": float(pearson_p),
        "spearman_r": float(spearman_r),
        "spearman_p": float(spearman_p),
        "n_samples": int(len(all_omega)),
        "verdict": "SUPPORTED" if (pearson_r > 0 and pearson_p < 0.01) else "NOT SUPPORTED",
    }
    return result


def test_H2(n_trials: int = 200, T: int = 300) -> dict:
    """
    H2 · Causal Robustness: ∂L/∂P_n | {I,A,F,R,V,D} > 0
    
    Controlled experiment: fix I_n, A_d, F_g, ℛ₀, perturbation_std.
    Vary ONLY P_n across a range. Measure final average L.
    Then regress L on P_n.
    """
    P_n_values = np.linspace(0.1, 5.0, n_trials)
    avg_losses = []

    # Fixed control variables
    fixed_I = 0.50
    fixed_A = 0.40
    fixed_F = 0.50
    fixed_R = 3.0
    fixed_perturbation = 0.15

    for p in P_n_values:
        sys = C5DynamicalSystem(
            perturbation_std=fixed_perturbation,
            seed=42,  # Same seed for reproducibility
        )
        initial = SystemState(
            S=0.0,
            regulator=RegulatorParams(P_n=p, I_n=fixed_I, A_d=fixed_A, F_g=fixed_F),
            resilience=fixed_R,
        )
        traj = sys.simulate(initial, T=T)
        # Use second half to avoid transient
        avg_loss = float(np.mean(traj["loss"][T // 2:]))
        avg_losses.append(avg_loss)

    avg_losses = np.array(avg_losses)

    # Linear regression: L = a + b·P_n
    slope, intercept, r_value, p_value, std_err = stats.linregress(P_n_values, avg_losses)

    result = {
        "hypothesis": "H2: ∂L/∂P_n | {I,A,F,R,V,D} > 0",
        "slope_dL_dPn": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r_value ** 2),
        "p_value": float(p_value),
        "std_err": float(std_err),
        "n_trials": n_trials,
        "controlled_vars": {
            "I_n": fixed_I, "A_d": fixed_A, "F_g": fixed_F,
            "resilience_0": fixed_R, "perturbation_std": fixed_perturbation,
        },
        "verdict": "SUPPORTED" if (slope > 0 and p_value < 0.01) else "NOT SUPPORTED",
        "P_n_values": P_n_values.tolist(),
        "avg_losses": avg_losses.tolist(),
    }
    return result


def test_H3(T: int = 800) -> dict:
    """
    H3 · Exhaustion Dynamics:
    ∃ Ω* , ℛ* such that Ω > Ω* ∧ ℛ < ℛ* ⟹ dℛ/dt < 0 persistently.
    
    Run Q3 (Authoritarian Stable) for long enough to observe ℛ depletion,
    then check if the system transitions to Q4 behavior.
    """
    sys = C5DynamicalSystem(seed=2026)
    initial = SystemState(
        S=0.0,
        regulator=RegulatorParams(P_n=3.5, I_n=0.25, A_d=0.12, F_g=0.18),
        resilience=6.0,
    )
    traj = sys.simulate(initial, T=T)

    resilience = traj["resilience"]
    omega = traj["omega"]
    loss = traj["loss"]

    # Find the point where resilience first drops below threshold
    R_star = 1.0  # threshold
    exhaustion_indices = np.where(resilience < R_star)[0]

    if len(exhaustion_indices) > 0:
        t_exhaustion = int(exhaustion_indices[0])
        # Check if dℛ/dt < 0 persistently after exhaustion
        post_exhaustion_R = resilience[t_exhaustion:]
        dR_dt = np.diff(post_exhaustion_R)
        fraction_negative = float(np.mean(dR_dt < 0))

        # Check if loss increases persistently after exhaustion
        post_exhaustion_L = loss[t_exhaustion:]
        # Use rolling mean to smooth
        window = min(20, len(post_exhaustion_L) // 3)
        if window > 1:
            rolling_L = np.convolve(post_exhaustion_L, np.ones(window)/window, mode='valid')
            dL_dt = np.diff(rolling_L)
            fraction_L_increasing = float(np.mean(dL_dt > 0))
        else:
            fraction_L_increasing = float('nan')

        # Mean Ω in the exhaustion regime
        mean_omega_post = float(np.mean(omega[t_exhaustion:]))
    else:
        t_exhaustion = -1
        fraction_negative = 0.0
        fraction_L_increasing = 0.0
        mean_omega_post = float(np.mean(omega))

    result = {
        "hypothesis": "H3: Ω > Ω* ∧ ℛ < ℛ* ⟹ dℛ/dt < 0 persistently",
        "R_star_threshold": R_star,
        "t_exhaustion": t_exhaustion,
        "fraction_dR_negative_post_exhaustion": fraction_negative,
        "fraction_dL_increasing_post_exhaustion": fraction_L_increasing,
        "mean_omega_post_exhaustion": mean_omega_post,
        "total_timesteps": T,
        "verdict": (
            "SUPPORTED"
            if (t_exhaustion > 0 and fraction_negative > 0.6 and fraction_L_increasing > 0.5)
            else "NOT SUPPORTED"
        ),
        "trajectory": {
            "resilience": resilience.tolist(),
            "omega": omega.tolist(),
            "loss": loss.tolist(),
        },
    }
    return result


# ═══════════════════════════════════════════════════════════════════════════
# §5  VISUALIZATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════

def plot_all(trajectories: dict, h1: dict, h2: dict, h3: dict):
    """Generate publication-quality diagnostic plots."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "figure.facecolor": "#0d1117",
        "axes.facecolor": "#161b22",
        "text.color": "#c9d1d9",
        "axes.labelcolor": "#c9d1d9",
        "xtick.color": "#8b949e",
        "ytick.color": "#8b949e",
        "axes.edgecolor": "#30363d",
        "grid.color": "#21262d",
        "grid.alpha": 0.6,
    })

    # ── Figure 1: Four-Regime Trajectories ──────────────────────────────
    fig1, axes1 = plt.subplots(2, 2, figsize=(16, 10))
    fig1.suptitle(
        "C5-REAL v2.0 · Regulatory Fragility Simulator — Four Regime Quadrants",
        fontsize=14, fontweight="bold", color="#58a6ff",
    )

    metrics = [
        ("omega", "Ω (Fragility Index)"),
        ("loss", "L (Regulatory Loss)"),
        ("resilience", "ℛ (Resilience)"),
        ("J", "J (Total Cost Functional)"),
    ]

    for ax, (key, label) in zip(axes1.flat, metrics):
        for regime_name, traj in trajectories.items():
            color = REGIMES[regime_name]["color"]
            ax.plot(traj["t"], traj[key], color=color, alpha=0.85, linewidth=1.2,
                    label=regime_name.replace("_", " "))
        ax.set_ylabel(label)
        ax.set_xlabel("t")
        ax.legend(fontsize=7, loc="upper left", framealpha=0.3)
        ax.grid(True, alpha=0.3)

    fig1.tight_layout(rect=[0, 0, 1, 0.95])
    fig1.savefig(OUTPUT_DIR / "fig1_four_regimes.png", dpi=200, bbox_inches="tight")
    print(f"  ✓ Saved: {OUTPUT_DIR / 'fig1_four_regimes.png'}")

    # ── Figure 2: H1 — Ω vs L Scatter ──────────────────────────────────
    fig2, ax2 = plt.subplots(figsize=(10, 7))
    for regime_name, traj in trajectories.items():
        color = REGIMES[regime_name]["color"]
        ax2.scatter(traj["omega"], traj["loss"], c=color, alpha=0.3, s=8,
                    label=regime_name.replace("_", " "))
    ax2.set_xlabel("Ω (Fragility Index)")
    ax2.set_ylabel("L (Regulatory Loss)")
    ax2.set_title(
        f"H1: corr(Ω, L) — Pearson r={h1['pearson_r']:.4f}, p={h1['pearson_p']:.2e} "
        f"→ [{h1['verdict']}]",
        color="#58a6ff",
    )
    ax2.legend(fontsize=8, framealpha=0.3)
    ax2.grid(True, alpha=0.3)
    fig2.tight_layout()
    fig2.savefig(OUTPUT_DIR / "fig2_H1_scatter.png", dpi=200, bbox_inches="tight")
    print(f"  ✓ Saved: {OUTPUT_DIR / 'fig2_H1_scatter.png'}")

    # ── Figure 3: H2 — Controlled P_n vs L ─────────────────────────────
    fig3, ax3 = plt.subplots(figsize=(10, 7))
    P_vals = np.array(h2["P_n_values"])
    L_vals = np.array(h2["avg_losses"])
    ax3.scatter(P_vals, L_vals, c="#58a6ff", alpha=0.6, s=15, zorder=3)
    # Regression line
    x_line = np.linspace(P_vals.min(), P_vals.max(), 100)
    y_line = h2["intercept"] + h2["slope_dL_dPn"] * x_line
    ax3.plot(x_line, y_line, color="#f85149", linewidth=2, linestyle="--",
             label=f"slope = {h2['slope_dL_dPn']:.4f}, R² = {h2['r_squared']:.4f}")
    ax3.set_xlabel("P_n (Normalized Coercive Power) — INTERVENTIONAL do(P_n)")
    ax3.set_ylabel("⟨L⟩ (Mean Regulatory Loss, second half)")
    ax3.set_title(
        f"H2: ∂L/∂P_n | {{I,A,F,ℛ,V,D}} > 0 — p={h2['p_value']:.2e} → [{h2['verdict']}]",
        color="#58a6ff",
    )
    ax3.legend(fontsize=9, framealpha=0.3)
    ax3.grid(True, alpha=0.3)
    fig3.tight_layout()
    fig3.savefig(OUTPUT_DIR / "fig3_H2_causal.png", dpi=200, bbox_inches="tight")
    print(f"  ✓ Saved: {OUTPUT_DIR / 'fig3_H2_causal.png'}")

    # ── Figure 4: H3 — Exhaustion Dynamics ──────────────────────────────
    h3_traj = h3["trajectory"]
    fig4, (ax4a, ax4b, ax4c) = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    fig4.suptitle(
        "H3: Exhaustion Dynamics — Authoritarian System Under Sustained Ω",
        fontsize=13, fontweight="bold", color="#58a6ff",
    )

    t_range = np.arange(len(h3_traj["omega"]))
    t_exh = h3["t_exhaustion"]

    ax4a.plot(t_range, h3_traj["omega"], color="#e74c3c", linewidth=1.2)
    ax4a.set_ylabel("Ω (Fragility)")
    ax4a.axhline(y=np.mean(h3_traj["omega"]), color="#f39c12", linestyle=":", alpha=0.5,
                 label=f"⟨Ω⟩ = {np.mean(h3_traj['omega']):.2f}")
    if t_exh > 0:
        ax4a.axvline(x=t_exh, color="#8b949e", linestyle="--", alpha=0.7,
                     label=f"t_exhaustion = {t_exh}")
    ax4a.legend(fontsize=8, framealpha=0.3)
    ax4a.grid(True, alpha=0.3)

    ax4b.plot(t_range, h3_traj["resilience"], color="#2ecc71", linewidth=1.2)
    ax4b.axhline(y=h3["R_star_threshold"], color="#f85149", linestyle="--", alpha=0.7,
                 label=f"ℛ* = {h3['R_star_threshold']}")
    if t_exh > 0:
        ax4b.axvline(x=t_exh, color="#8b949e", linestyle="--", alpha=0.7)
    ax4b.set_ylabel("ℛ (Resilience)")
    ax4b.legend(fontsize=8, framealpha=0.3)
    ax4b.grid(True, alpha=0.3)

    ax4c.plot(t_range, h3_traj["loss"], color="#f39c12", linewidth=0.8, alpha=0.6)
    # Rolling average
    window = 20
    if len(h3_traj["loss"]) > window:
        rolling = np.convolve(h3_traj["loss"], np.ones(window)/window, mode='valid')
        ax4c.plot(np.arange(len(rolling)), rolling, color="#e74c3c", linewidth=1.5,
                  label=f"Rolling mean (w={window})")
    if t_exh > 0:
        ax4c.axvline(x=t_exh, color="#8b949e", linestyle="--", alpha=0.7,
                     label=f"ℛ < ℛ* at t={t_exh}")
    ax4c.set_ylabel("L (Loss)")
    ax4c.set_xlabel("t")
    ax4c.legend(fontsize=8, framealpha=0.3)
    ax4c.grid(True, alpha=0.3)

    fig4.tight_layout(rect=[0, 0, 1, 0.95])
    fig4.savefig(OUTPUT_DIR / "fig4_H3_exhaustion.png", dpi=200, bbox_inches="tight")
    print(f"  ✓ Saved: {OUTPUT_DIR / 'fig4_H3_exhaustion.png'}")

    # ── Figure 5: Phase Portrait (Ω, ℛ) with regime quadrants ──────────
    fig5, ax5 = plt.subplots(figsize=(10, 8))
    for regime_name, traj in trajectories.items():
        color = REGIMES[regime_name]["color"]
        ax5.plot(traj["omega"], traj["resilience"], color=color, alpha=0.5, linewidth=0.8)
        ax5.scatter(traj["omega"][0], traj["resilience"][0], c=color, s=80,
                    edgecolors="white", zorder=5, marker="o")
        ax5.scatter(traj["omega"][-1], traj["resilience"][-1], c=color, s=80,
                    edgecolors="white", zorder=5, marker="X",
                    label=regime_name.replace("_", " "))

    # Quadrant boundaries
    omega_mid = 2.0
    R_mid = 2.0
    ax5.axvline(x=omega_mid, color="#8b949e", linestyle=":", alpha=0.4)
    ax5.axhline(y=R_mid, color="#8b949e", linestyle=":", alpha=0.4)
    ax5.text(0.5, 6.0, "Q1: Adaptive", color="#2ecc71", fontsize=9, ha="center")
    ax5.text(0.5, 0.5, "Q2: Vulnerable", color="#f39c12", fontsize=9, ha="center")
    ax5.text(8.0, 6.0, "Q3: Authoritarian\nStable", color="#e74c3c", fontsize=9, ha="center")
    ax5.text(8.0, 0.5, "Q4: Fragile\nCollapsible", color="#8e44ad", fontsize=9, ha="center")

    ax5.set_xlabel("Ω (Fragility Index)")
    ax5.set_ylabel("ℛ (Resilience)")
    ax5.set_title("Phase Portrait: (Ω, ℛ) Trajectories", color="#58a6ff")
    ax5.legend(fontsize=8, framealpha=0.3, title="● Start   ✕ End", title_fontsize=7)
    ax5.grid(True, alpha=0.3)
    fig5.tight_layout()
    fig5.savefig(OUTPUT_DIR / "fig5_phase_portrait.png", dpi=200, bbox_inches="tight")
    print(f"  ✓ Saved: {OUTPUT_DIR / 'fig5_phase_portrait.png'}")

    # ── Figure 6: Regulator Decomposition ───────────────────────────────
    fig6, axes6 = plt.subplots(2, 2, figsize=(16, 10))
    fig6.suptitle(
        "Regulator Variable Decomposition (P_n, I_n, A_d, F_g)",
        fontsize=13, fontweight="bold", color="#58a6ff",
    )
    reg_vars = [
        ("P_n", "P_n (Coercive Power)"),
        ("I_n", "I_n (Information Resolution)"),
        ("A_d", "A_d (Adaptation Rate)"),
        ("F_g", "F_g (Feedback Fidelity)"),
    ]
    for ax, (key, label) in zip(axes6.flat, reg_vars):
        for regime_name, traj in trajectories.items():
            color = REGIMES[regime_name]["color"]
            ax.plot(traj["t"], traj[key], color=color, alpha=0.85, linewidth=1.2,
                    label=regime_name.replace("_", " "))
        ax.set_ylabel(label)
        ax.set_xlabel("t")
        ax.legend(fontsize=7, loc="best", framealpha=0.3)
        ax.grid(True, alpha=0.3)

    fig6.tight_layout(rect=[0, 0, 1, 0.95])
    fig6.savefig(OUTPUT_DIR / "fig6_regulator_decomposition.png", dpi=200, bbox_inches="tight")
    print(f"  ✓ Saved: {OUTPUT_DIR / 'fig6_regulator_decomposition.png'}")

    plt.close("all")


# ═══════════════════════════════════════════════════════════════════════════
# §6  MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 72)
    print("  C5-REAL v2.0 · H_Ω Falsification Engine")
    print("=" * 72)

    # ── §6.1  Simulate Four Regimes ─────────────────────────────────────
    print("\n[§1] Simulating four regime quadrants...")
    trajectories = {}
    T = 500
    for regime_name, params in REGIMES.items():
        sys = C5DynamicalSystem(seed=2026)
        initial = SystemState(
            S=0.5,  # Initial deviation from target
            regulator=RegulatorParams(
                P_n=params["P_n"],
                I_n=params["I_n"],
                A_d=params["A_d"],
                F_g=params["F_g"],
            ),
            resilience=params["resilience"],
        )
        traj = sys.simulate(initial, T=T)
        trajectories[regime_name] = traj
        print(f"  ✓ {regime_name}: Ω₀={traj['omega'][0]:.2f} → Ω_T={traj['omega'][-1]:.2f}, "
              f"ℛ₀={traj['resilience'][0]:.2f} → ℛ_T={traj['resilience'][-1]:.2f}")

    # ── §6.2  Test H1: Descriptive Validity ─────────────────────────────
    print("\n[§2] Testing H1: corr(Ω, L) > 0...")
    h1_result = test_H1(trajectories)
    print(f"  Pearson  r = {h1_result['pearson_r']:+.4f}  (p = {h1_result['pearson_p']:.2e})")
    print(f"  Spearman ρ = {h1_result['spearman_r']:+.4f}  (p = {h1_result['spearman_p']:.2e})")
    print(f"  ═══ VERDICT: {h1_result['verdict']} ═══")

    # ── §6.3  Test H2: Causal Robustness ────────────────────────────────
    print("\n[§3] Testing H2: ∂L/∂P_n | {I,A,F,ℛ,V,D} > 0...")
    h2_result = test_H2(n_trials=200, T=300)
    print(f"  slope(∂L/∂P_n) = {h2_result['slope_dL_dPn']:+.6f}")
    print(f"  R²             = {h2_result['r_squared']:.4f}")
    print(f"  p-value        = {h2_result['p_value']:.2e}")
    print(f"  ═══ VERDICT: {h2_result['verdict']} ═══")

    # ── §6.4  Test H3: Exhaustion Dynamics ──────────────────────────────
    print("\n[§4] Testing H3: Exhaustion dynamics (ℛ depletion)...")
    h3_result = test_H3(T=800)
    print(f"  t_exhaustion (ℛ < ℛ*) = {h3_result['t_exhaustion']}")
    print(f"  fraction dℛ/dt < 0 post-exhaustion = {h3_result['fraction_dR_negative_post_exhaustion']:.2%}")
    print(f"  fraction dL/dt > 0 post-exhaustion  = {h3_result['fraction_dL_increasing_post_exhaustion']:.2%}")
    print(f"  ⟨Ω⟩ post-exhaustion = {h3_result['mean_omega_post_exhaustion']:.2f}")
    print(f"  ═══ VERDICT: {h3_result['verdict']} ═══")

    # ── §6.5  Generate Plots ────────────────────────────────────────────
    print("\n[§5] Generating diagnostic plots...")
    plot_all(trajectories, h1_result, h2_result, h3_result)

    # ── §6.6  Save Structured Results ───────────────────────────────────
    results = {
        "framework": "C5-REAL v2.0",
        "experiment": "H_Omega Falsification",
        "timestamp": "2026-08-17T18:22:00+02:00",
        "system": {
            "state_vector": "X_t = (S_t, R_t, Ω_t, ℛ_t)",
            "timesteps_per_regime": T,
        },
        "H1": {k: v for k, v in h1_result.items()},
        "H2": {k: v for k, v in h2_result.items() if k not in ("P_n_values", "avg_losses")},
        "H3": {k: v for k, v in h3_result.items() if k != "trajectory"},
        "epistemic_status": {
            "Omega": "dimensionless composite diagnostic index",
            "H_Omega": "falsifiable hypothesis, not theorem",
            "J": "multi-objective cost functional",
            "resilience": "dynamic state variable with hysteresis",
        },
    }

    results_path = OUTPUT_DIR / "h_omega_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  ✓ Results saved: {results_path}")

    # ── §6.7  Summary ───────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  FALSIFICATION SUMMARY")
    print("=" * 72)
    verdicts = {
        "H1 (Descriptive)": h1_result["verdict"],
        "H2 (Causal)":      h2_result["verdict"],
        "H3 (Exhaustion)":  h3_result["verdict"],
    }
    for name, verdict in verdicts.items():
        icon = "✅" if verdict == "SUPPORTED" else "❌"
        print(f"  {icon}  {name}: {verdict}")

    all_supported = all(v == "SUPPORTED" for v in verdicts.values())
    print(f"\n  {'🟢' if all_supported else '🔴'}  Overall: "
          f"{'All hypotheses SUPPORTED by simulation' if all_supported else 'Some hypotheses NOT SUPPORTED'}")
    print(f"\n  ⚠️  EPISTEMIC WARNING: These results demonstrate consistency")
    print(f"     within a SYNTHETIC model. They do NOT constitute empirical")
    print(f"     proof. Real-world validation requires operationalizing")
    print(f"     P_n, I_n, A_d, F_g against measurable observables.")
    print("=" * 72)


if __name__ == "__main__":
    main()
