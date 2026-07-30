# CORTEX Routing Bunker & Mathematical Lobotomization

This repository is the physical manifestation of C5-REAL execution regarding Sovereign AI Routing and Geometric Defense (Representation Rerouting).

## I. Circuit Breakers (Representation Rerouting)

The true defense against algorithmic bypass (AutoDAN, jailbreaks) relies on spatial geometry in the latent space, bypassing outdated keyword filters. 
The fine-tuning loss mathematically enforces the redirection of hostile vectors towards a refusal node, while preserving the baseline intelligence mapping.

### Dual Loss Function

The core mechanism operates on:
$$L = c_s L_s + c_r L_r$$

**1. Rerouting Loss ($L_s$)**
Forces hidden vectors ($h$) detecting hostile intent towards a pre-calculated $h_{refusal}$:
$$L_s = \sum_{i} ||h_{i}^{(harmful)} - h_{refusal}||_2^2$$

**2. Retain Loss ($L_r$)**
Locks benign vector trajectories to their original model equivalents to prevent catastrophic forgetting/lobotomization of harmless intelligence:
$$L_r = \sum_{i} ||h_{i}^{(benign)} - \hat{h}_{i}^{(benign)}||_2^2$$

## II. The Sovereign Routing Bunker

The `docker-compose.yml` configures an abstraction proxy utilizing LiteLLM and Redis Semantic Caching.

**Architecture Layers:**
1. **Proxy Abstraction**: Localized endpoint (`localhost:4000`) standardizing all requests to OpenAI protocol.
2. **Cascading Failover**: Configured in `litellm_config.yaml` 
   - Primary: Anthropic (Fable)
   - Failover 1: Mistral Large (Offshore)
   - Failover 2: Llama 3 70B (Sovereign hardware / Groq)
3. **Semantic Caching**: Redis instances intercept >95% similar prompts to bypass inference latency and cost.
4. **Asynchronous Audit**: Success callbacks route telemetry directly to Langfuse/Clickhouse for deferred adversarial analysis.


---

```yaml
AESTHETIC:    INDUSTRIAL NOIR 2026 (#0A0A0A / #2B3BE5)
EPISTEMOLOGY: C5-REAL EDG V6 — Error Navigation System
CORE TENET:   Optimize for correction, not certainty. Uncertainty is telemetry, not weakness.
UPDATED:      June 2026 — Falsifiable Memory Infrastructure
```
