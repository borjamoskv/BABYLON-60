"""
INV_BFT_04 / Thermodynamic Valve Extension
Bayesian Swarm module with Logarithmic Opinion Pooling (LogOP).
Faithful to Gelfand & Dey.
"""

from typing import List, Dict
import math

class BayesianSwarm:
    def __init__(self, agents: List[str]):
        """
        agents: List of BFT agent identifiers.
        """
        self.agents = agents

    def logarithmic_opinion_pool(
        self,
        opinions: Dict[str, Dict[str, float]],
        weights: Dict[str, float] = None
    ) -> Dict[str, float]:
        """
        Computes the Logarithmic Opinion Pool (LogOP) of multiple categorical distributions.
        
        opinions: Dict mapping agent_id -> Dict[hypothesis -> probability]
        weights: Optional dict mapping agent_id -> weight. Defaults to uniform weights.
        
        Returns a normalized categorical distribution Dict[hypothesis -> probability].
        """
        if not opinions:
            return {}

        # Default to uniform weights if none provided
        if weights is None:
            w = 1.0 / len(opinions)
            weights = {agent: w for agent in opinions.keys()}

        # Collect all hypotheses
        hypotheses = set()
        for dist in opinions.values():
            hypotheses.update(dist.keys())

        aggregated_unnormalized = {}
        
        for hyp in hypotheses:
            log_sum = 0.0
            vetoed = False
            for agent, dist in opinions.items():
                p = dist.get(hyp, 0.0)
                w = weights.get(agent, 0.0)
                
                if p <= 0.0:
                    vetoed = True
                    break # Veto absolute (LogOP property)
                
                # Geometric weighted component in logarithmic domain to prevent underflow
                p_clamped = max(p, 1e-300)
                try:
                    val = math.log(p_clamped)
                    if math.isinf(val):
                        vetoed = True
                        break
                    log_sum += w * val
                except ValueError:
                    vetoed = True
                    break
            
            if vetoed:
                aggregated_unnormalized[hyp] = 0.0
            else:
                aggregated_unnormalized[hyp] = math.exp(log_sum)

        # Normalize
        total_mass = sum(aggregated_unnormalized.values())
        if total_mass == 0.0:
            # If all hypotheses were vetoed or total mass is 0
            return {hyp: 0.0 for hyp in hypotheses}

        return {hyp: val / total_mass for hyp, val in aggregated_unnormalized.items()}
