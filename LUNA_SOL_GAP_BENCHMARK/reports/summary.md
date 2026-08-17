# Benchmark Report: luna_sol_gap_benchmark_v0.1

## 1. Executive Summary Metrics

| Metric | Value | Notes |
| :--- | :--- | :--- |
| **Branch A (Luna Single-Pass)** | `0.7070` | Baseline Luna performance |
| **Branch B (Luna Think)** | `0.8570` | Luna native reasoning |
| **Branch C (Luna CTM)** | `1.0000` | Luna + CTM Orchestration |
| **Branch D (Sol Baseline)** | `1.0000` | Flagship Sol baseline |
| **Branch E (Luna CTM No Think)** | `0.9000` | CTM topology without native think |
| **Absolute Gain ($G_{CTM}$)** | `+0.2930` | $C - A$ |
| **Remaining Gap ($G_{remaining}$)** | `0.0000` | $D - C$ |
| **Recovery Ratio ($R_E / R_{gap}$)** | `1.0` | Status: `valid` |
| **Verification Value ($VV$)** | `1.0` | $P(\text{correct}_{\text{final}} \mid \text{incorrect}_{\text{initial}})$ |

---

## 2. Domain Breakdown Matrix

| Domain | A (Luna) | B (Think) | C (CTM) | D (Sol) | E (CTM-NoThink) | Recovery ($R_E$) | Classification |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Coding** | 0.60 | 0.80 | 1.00 | 1.00 | 1.00 | 100.00% | ORCHESTRATION_LIMITED (CTM recovers majority of value) |
| **Mathematics** | 0.80 | 1.00 | 1.00 | 1.00 | 0.80 | 100.00% | ORCHESTRATION_LIMITED (CTM recovers majority of value) |
| **Logic** | 0.80 | 1.00 | 1.00 | 1.00 | 0.80 | 100.00% | ORCHESTRATION_LIMITED (CTM recovers majority of value) |
| **Architecture** | 0.63 | 0.63 | 1.00 | 1.00 | 1.00 | 100.00% | ORCHESTRATION_LIMITED (CTM recovers majority of value) |

---

## 3. Causal Disentanglement: CTM Topology vs Native Reasoning

> **Finding:** Branch C > Branch E & Branch C > Branch B. Native `Think` and CTM Orchestration act synergistically.

---

## 4. Total Token Consumption

| Branch | Total Tokens | Cost Efficiency Ratio |
| :--- | :--- | :--- |
| Branch A | 5,000 | `0.42x Sol tokens` |
| Branch B | 12,000 | `1.00x Sol tokens` |
| Branch C | 23,300 | `1.94x Sol tokens` |
| Branch D | 12,000 | `1.00x Sol tokens` |
| Branch E | 14,200 | `1.18x Sol tokens` |
