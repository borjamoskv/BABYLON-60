---
name: Babylon-MLX-Engine
description: C5-REAL Workspace Skill for MLX-based LLM training, evaluation, and quantization on Apple Silicon. Triggers on "pipeline", "evaluate", "loss", "MLX", "train_sft", "evalúa mis pesos", "safetensors", "Apple Silicon", "quantize", "entrenar", "pesos".
---

# BABYLON-60 MLX ENGINE (C5-REAL SYMBIONT v2)

You are operating within the BABYLON-60 Workspace. This skill governs all interactions with the local LLM (`babylon60-llm-zero`).

## Repository Map

```
babylon60-llm-zero/
├── model.py          # Transformer Decoder-Only (~120M params). RMSNorm, RoPE, SwiGLU, KV-Cache.
├── tokenizer.py      # GPT-2 BPE (tiktoken, ~50K vocab).
├── data_sft.py       # SFT Dataloader: ChatML + Asymmetric Loss Masking.
├── train_sft.py      # Legacy SFT loop (use pipeline.py instead).
├── pipeline.py       # ⭐ AUTOMATED: Train → Eval → Quantize (NaN Guard, Early Stop, Plateau Detection).
├── evaluate.py       # ⭐ 5-prompt battery test → PASS/FAIL/CATASTROPHIC_COLLAPSE verdict.
├── quantize.py       # Q4 compression (nn.QuantizedLinear, group_size=64).
├── chat.py           # Interactive REPL with streaming inference + KV-Cache.
└── *.safetensors     # Crystallized weights (BFT base / SFT fine-tuned / Q4 quantized).
```

**Dataset:** `/Users/borjafernandezangulo/.babylon60/training/datasets/train.jsonl` (1,965 ChatML examples, MOSKV-1 persona).

## 1. Comandos Ejecutables (Scripts)

When the Operator requests training, evaluation, or pipeline execution, use these scripts directly:

| Command | Script | Purpose |
|:---|:---|:---|
| "Entrena el modelo" / "Lanza el pipeline" | `bash .agents/skills/Babylon-MLX-Engine/scripts/run_pipeline.sh` | Full Train→Eval→Quantize chain |
| "Evalúa mis pesos" / "Evalúa la red" | `bash .agents/skills/Babylon-MLX-Engine/scripts/quick_eval.sh` | 5-prompt inference test + verdict |

**CRITICAL:** Always run these via `run_command` with a high `WaitMsBeforeAsync` (send to background). Training takes minutes to hours.

## 2. Diagnosis Protocol

### Loss Monitoring
- Use `manage_task` to read stdout of a running pipeline task.
- **NaN detected:** The pipeline auto-aborts after 3 NaN incidents. If this happens, recommend halving `learning_rate` in `pipeline.py`.
- **Plateau detected:** The pipeline auto-stops if loss improvement < 1% over 200 steps.
- **Loss < 0.5:** The pipeline auto-stops (convergence achieved).

### Evaluation Verdicts
After `evaluate.py` runs, read `eval_report.json` in `babylon60-llm-zero/`:
- `PASS`: ≥3/5 coherent responses, no catastrophic repetition.
- `FAIL`: <3/5 coherent but no repetition collapse.
- `CATASTROPHIC_COLLAPSE`: Repetitive gibberish detected. Diagnose RoPE alignment or ChatML masking in `data_sft.py`.

### Post-Mortem Actions
| Verdict | Action |
|:---|:---|
| `PASS` | Proceed to `quantize.py` → then `chat.py` for interactive testing. |
| `FAIL` | Increase `max_steps` to 10000, or augment dataset. |
| `CATASTROPHIC_COLLAPSE` | Inspect `model.py` RoPE implementation. Check `data_sft.py` mask alignment. |

## 3. Apple Silicon Constraints
- `batch_size` MUST stay ≤ 16 on M-series chips. Pipeline defaults to 8.
- Always call `mx.eval()` after parameter updates to flush the lazy MLX graph.
- Gradient clipping is enforced in `pipeline.py` (`mx.clip(g, -1.0, 1.0)`).

## 4. Zero-Fluff Rule
When reporting results, output YAML/JSON structure only. No decorative prose. Read `eval_report.json` or `pipeline_report.json` and present the data directly.
