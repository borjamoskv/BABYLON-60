# Statistics and Classification Engine for LUNA_SOL_GAP_BENCHMARK
from typing import Dict, Any
from benchmark.metrics import BenchmarkMetrics


class StatisticsEngine:
    def classify_domain_matrix(self, domain_scores: Dict[str, Dict[str, float]]) -> Dict[str, str]:
        """
        Classifies each domain into one of 4 quadrants:
        - ORCHESTRATION_LIMITED: CTM improves performance significantly, closing > 70% of gap.
        - HYBRID: Both Think and CTM contribute significantly.
        - MODEL_LIMITED: Neither Think nor CTM closes the gap; Luna weights lack representational capacity.
        - SOL_DOMINANT: Sol performance is far superior and unapproachable.
        """
        classifications = {}
        for dom, b_scores in domain_scores.items():
            A = b_scores.get("A", 0.0)
            B = b_scores.get("B", 0.0)
            C = b_scores.get("C", 0.0)
            D = b_scores.get("D", 0.0)
            E = b_scores.get("E", 0.0)

            rec = b_scores.get("Recovery", -1.0)

            if rec >= 0.70:
                classifications[dom] = "ORCHESTRATION_LIMITED (CTM recovers majority of value)"
            elif C > A and (C - A) >= (B - A):
                classifications[dom] = "HYBRID (CTM + Think synergy)"
            elif D - C > 0.40:
                classifications[dom] = "SOL_DOMINANT (Representational capacity bottleneck)"
            else:
                classifications[dom] = "MODEL_LIMITED (Intrinsic capacity cap)"

        return classifications

    def generate_markdown_report(
        self,
        metrics: BenchmarkMetrics,
        experiment_name: str = "luna_sol_gap_benchmark_v0.1"
    ) -> str:
        classifications = self.classify_domain_matrix(metrics.domain_breakdown)

        md = f"""# Benchmark Report: {experiment_name}

## 1. Executive Summary Metrics

| Metric | Value | Notes |
| :--- | :--- | :--- |
| **Branch A (Luna Single-Pass)** | `{metrics.mean_scores['A']:.4f}` | Baseline Luna performance |
| **Branch B (Luna Think)** | `{metrics.mean_scores['B']:.4f}` | Luna native reasoning |
| **Branch C (Luna CTM)** | `{metrics.mean_scores['C']:.4f}` | Luna + CTM Orchestration |
| **Branch D (Sol Baseline)** | `{metrics.mean_scores['D']:.4f}` | Flagship Sol baseline |
| **Branch E (Luna CTM No Think)** | `{metrics.mean_scores['E']:.4f}` | CTM topology without native think |
| **Absolute Gain ($G_{{CTM}}$)** | `+{metrics.absolute_gain_g_ctm:.4f}` | $C - A$ |
| **Remaining Gap ($G_{{remaining}}$)** | `{metrics.gap_remaining:.4f}` | $D - C$ |
| **Recovery Ratio ($R_E / R_{{gap}}$)** | `{metrics.recovery_ratio_re if metrics.recovery_ratio_re is not None else 'N/A'}` | Status: `{metrics.recovery_ratio_status}` |
| **Verification Value ($VV$)** | `{metrics.verification_value_vv if metrics.verification_value_vv is not None else 'N/A'}` | $P(\\text{{correct}}_{{\\text{{final}}}} \\mid \\text{{incorrect}}_{{\\text{{initial}}}})$ |

---

## 2. Domain Breakdown Matrix

| Domain | A (Luna) | B (Think) | C (CTM) | D (Sol) | E (CTM-NoThink) | Recovery ($R_E$) | Classification |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
"""
        for dom, b_scores in metrics.domain_breakdown.items():
            rec_str = f"{b_scores['Recovery']:.2%}" if b_scores['Recovery'] >= 0 else "N/A"
            cls_str = classifications.get(dom, "N/A")
            md += f"| **{dom.capitalize()}** | {b_scores['A']:.2f} | {b_scores['B']:.2f} | {b_scores['C']:.2f} | {b_scores['D']:.2f} | {b_scores['E']:.2f} | {rec_str} | {cls_str} |\n"

        md += """
---

## 3. Causal Disentanglement: CTM Topology vs Native Reasoning

"""
        c_score = metrics.mean_scores['C']
        e_score = metrics.mean_scores['E']
        b_score = metrics.mean_scores['B']

        if abs(c_score - e_score) < 0.05:
            md += "> **Finding:** Branch C (Luna+CTM) ≈ Branch E (Luna+CTM-NoThink). Structural CTM orchestration is the primary driver of gain.\n"
        elif c_score > e_score and c_score > b_score:
            md += "> **Finding:** Branch C > Branch E & Branch C > Branch B. Native `Think` and CTM Orchestration act synergistically.\n"
        else:
            md += "> **Finding:** Native `Think` (Branch B) provides the bulk of reasoning improvement.\n"

        md += """
---

## 4. Total Token Consumption

| Branch | Total Tokens | Cost Efficiency Ratio |
| :--- | :--- | :--- |
"""
        for b, tok in metrics.token_usage_totals.items():
            md += f"| Branch {b} | {tok:,} | `{tok / max(1, metrics.token_usage_totals['D']):.2f}x Sol tokens` |\n"

        return md
