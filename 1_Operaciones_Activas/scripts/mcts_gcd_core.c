// C5-REAL EXERGY CERTIFIED
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <dispatch/dispatch.h>

// Axiom Ω27: Thermodynamic Annealing Decay e^{-λt}
// Axiom Ω23: Grand Central Dispatch (GCD) Thread-Level Parallelism
void compute_uct_scores_gcd(
    const double* prm_scores,
    const int* visits,
    const double* values,
    const int* parent_visits,
    double c_puct,
    double lambda_decay,
    const int* step_ts,
    double* out_uct_scores,
    size_t num_nodes
) {
    // Distribute computation across all Apple Silicon Performance Cores
    dispatch_apply(num_nodes, dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_HIGH, 0), ^(size_t i) {
        if (visits[i] == 0) {
            out_uct_scores[i] = INFINITY;
            return;
        }

        double p_visits = (parent_visits[i] > 0) ? parent_visits[i] : 1.0;
        double q_val = values[i] / (double)visits[i];

        // Annealed C_puct
        double annealed_c_puct = c_puct * exp(-lambda_decay * (double)step_ts[i]);

        double u_val = annealed_c_puct * prm_scores[i] * (sqrt(p_visits) / (1.0 + (double)visits[i]));

        // Exergy gain
        double exergy_gain = (1.0 - tanh(1.0 / (1.0 + (double)visits[i]))) * prm_scores[i];

        out_uct_scores[i] = q_val + u_val + (0.1 * exergy_gain);
    });
}
