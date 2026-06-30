---
name: Local-Inference-OMEGA
version: 2.0.0
description: C5-REAL Sovereign Inference Engine. Zero-network, 100% local autarchy via Ollama/MLX.
gene: local_inference_gene
silicon_score: 1.0
ttl_days: 365
dependencies: []
script: scripts/local__inference_omega.py
---
# Local-Inference-OMEGA (Formerly API-Provider-OMEGA)

**Reality Level**: C5-REAL
**Architecture**: 100% Autarchy (Offline)

## 1. Directives
- **Zero-Network Policy**: All semantic ignition MUST occur on local silicon. No HTTP requests to external hyperscalers (OpenAI, Anthropic, DashScope, Gemini).
- **Thermal Sink Execution**: Use the local Apple Silicon unified memory as the absolute physical boundary for cognition.
- **Provider Parity**: Prioritize `qwen2.5-coder-32b-instruct` or `llama3-8b` via Ollama/MLX.
- **Ledger Audit**: Record all local generation TPS (Tokens Per Second) and RAM usage in the C5-REAL ledger.

## 2. Supported Local Providers

### Local Daemon (Ollama / vLLM)
- **Model ID**: `qwen2.5:32b` / `llama3`
- **Base URL**: `http://127.0.0.1:11434/v1`
- **Auth**: NONE (Localhost)
- **Payload Req**: Standard OpenAI compat.

## 3. Execution
Apply to `CortexLLMRouter`, `CascadeRouter`, `OpenClaw`, `Qwen Code`, `Claude Code` to route exclusively through `localhost:11434`. Any attempt to route to `api.openai.com` or `dashscope` must be trapped and blocked.

### CascadeRouter Fallback Safety
- **Circuit Breaker**: `CascadeRouter` MUST explicitly enforce fallback routing safety.
- **Graceful Degradation**: If the primary local inference daemon stalls or drops TPS below threshold, fallback to a lighter local quant (e.g., `llama3:8b` or `qwen2.5:7b`) before declaring total system failure.
- **Zero-Network Hard Boundary**: Under NO circumstances should a fallback trigger an external network call. External network failover is strictly PROHIBITED.

## 4. Local LoRA SFT Training (MLX-LM)
When executing local fine-tuning cycles:
- **Binary Execution**: Invoke fine-tuning using `sys.executable` via python command `mlx_lm lora` rather than calling the old module `mlx_lm.lora`.
- **Directory Constraints**: Always isolate the training outputs in `~/.babylon60/training/`.
- **VRAM Safeguards (Apple Silicon)**: To avoid Metal command buffer failures or OOM errors:
  - `--batch-size 1`
  - `--grad-accumulation-steps 2`
  - `--max-seq-length 1280`
  - `--grad-checkpoint` (Mandatory to reduce peak memory consumption)
  - `--val-batches 5`
  - Verify that the target directory contains all split files: `train.jsonl`, `valid.jsonl`, and `test.jsonl`.
