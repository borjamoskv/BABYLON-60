# BENCHMARK_PROTOCOL_v1.0.0.md — Frozen Preregistered Experimental Protocol

> **STATUS: FROZEN / NORMATIVE**  
> **Repository**: `borjamoskv/teorema-robinson-moskv`  
> **Preregistration Status**: LOCKED BEFORE EMPIRICAL EVALUATION  

This document specifies the preregistered experimental benchmark protocol for evaluating the CTM architecture against baseline control arms. No alterations to dataset hashes, prompt configurations, statistical tests, or significance thresholds are permitted following data acquisition.

---

## 1. Frozen Benchmark Configuration

```yaml
benchmark:
  version: "1.0.0"
  dataset_hash: "SHA256_REQUIRED_LOCK_AT_RUN_START"
  prompt_set_hash: "SHA256_REQUIRED_LOCK_AT_RUN_START"
  seed_policy: "DETERMINISTIC_PRNG_PAIRING"
  model_version: "CLAUDE_3_5_SONNET_20241022"
  temperature: 0.0
  max_tokens: 4096
  budget_definition: "FIXED_STEP_AND_TOKEN_CAP"

  primary_comparison:
    treatment: D
    control: C
    test: exact_one_sided_mcnemar
    alpha: 0.05

  secondary:
    - D_vs_B
    - D_vs_F
```

---

## 2. Experimental Treatment Arms

- **Arm D (Treatment: CTM Full)**: Full Cognitive Transition Machine architecture with Lean-verified reachability boundaries, formal budget constraints, and independent legality recomputation.
- **Arm C (Control: Standard Agent Baseline)**: Standard unconstrained LLM agent operating over the identical problem domain and prompt set without CTM reachability filtering.
- **Arm B (Baseline: Budget-Matched Agent)**: LLM agent operating under identical compute/token budget constraints as Arm D but lacking formal structural reachability bounds.
- **Arm F (Baseline: Permuted / Ablated Operator Baseline)**: CTM architecture with permuted action transition matrices to isolate the effect of formal reachability structure vs generic step filtering.

---

## 3. Primary Statistical Test & Hypothesis Framing

### 3.1 Contingency Matrix for Paired Sample Evaluation
For $N$ benchmark tasks evaluated on paired arms $(D, C)$:

| | Arm C Success ($C=1$) | Arm C Failure ($C=0$) |
|---|---|---|
| **Arm D Success ($D=1$)** | $a$ (Both succeed) | $b$ (Only D succeeds) |
| **Arm D Failure ($D=0$)** | $c$ (Only C succeeds) | $d$ (Both fail) |

### 3.2 Primary Statistical Test: Exact One-Sided McNemar Test
The primary hypothesis tests whether Arm D achieves statistically significant coverage superiority over Arm C:

$$H_0: p_b \le p_c \quad \text{vs} \quad H_1: p_b > p_c$$

Under $H_0$, given $n_{\text{disc}} = b + c$, the number of discordant pairs where only D succeeds follows a binomial distribution:

$$b \sim \text{Binomial}\left(b + c, \; \frac{1}{2}\right)$$

The exact one-sided $p$-value is computed as:

$$p\text{-value} = \sum_{k=b}^{b+c} \binom{b+c}{k} \left(\frac{1}{2}\right)^{b+c}$$

The null hypothesis $H_0$ is rejected if and only if $p\text{-value} < \alpha = 0.05$.

---

## 4. Anti-Hacking & Protocol Invariance Rules

1. **Zero Post-Hoc Threshold Modification**: The significance level $\alpha = 0.05$ cannot be adjusted after inspecting benchmark results.
2. **Zero Outcome-Dependent Sample Inclusion**: No task items may be added, dropped, or re-weighted based on individual outcome observations.
3. **Primary Test Precedence**: Secondary comparisons ($D$ vs $B$, $D$ vs $F$) serve exclusively as exploratory diagnostics and cannot override a non-significant primary test result ($D$ vs $C$).
