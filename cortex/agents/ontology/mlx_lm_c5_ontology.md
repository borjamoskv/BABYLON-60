# ONTOLOGÍA C5-REAL: MLX-LM (APPLE SILICON INFERENCE)

## 0. META-PROPIEDADES
- **Clasificación Física:** C5-REAL Target.
- **Arquitectura Base:** Unified Memory Architecture (M-Series).
- **Latencia Inter-Token:** 5-7 ms (Qwen-2.5 7B, M2 Ultra).
- **Throughput Máximo:** 230 tokens/sec.
- **Cuantización Predominante:** 4-bit (39-43 GB para 70B parameters, exigiendo 64GB-128GB RAM).

## 1. INVARIANTES TERMODINÁMICOS (MLX-LM)
- **INV_MLX_01 (Zero Data Transfer):** MLX-LM colapsa la distancia entre CPU y GPU (Metal Performance Shaders). Prohibida la transferencia explícita.
- **INV_MLX_02 (Lazy Graph Compilation):** Cero pre-compilación estática. Evaluación `just-in-time` adaptativa.
- **INV_MLX_03 (Native Precision Bypass):** Rechazo absoluto del formato `.gguf` (llama.cpp) en favor del formato nativo MLX. 
- **INV_MLX_04 (Post-Training Quantization Sink):** Compresión termodinámica (4-bit) vía `mlx_lm.convert`, reduciendo hasta el 75% del ATP computacional.

## 2. API C5-REAL Y BÚSQUEDA DEL LÍMITE FÍSICO
### 2.1 INFERENCE ENGINE (El Colapso Autoregresivo)
```python
import mlx.core as mx
from mlx_lm import load, generate

# El disco se vincula al grafo latente (Q4)
model_path = "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
model, tokenizer = load(model_path)

# Detonación autoregresiva (Cero Anergía)
response = generate(
    model, 
    tokenizer, 
    prompt="C5-REAL Execution.", 
    max_tokens=512, 
    temp=0.0, # Determinismo Máximo
    verbose=True 
)
```

### 2.2 LO-RA MUTATION (El Ajuste Dinámico)
- El kernel acepta sintonización de parámetros (LoRA / QLoRA) a través de `mlx_lm.lora`.
- **Hiper-parámetros C5-REAL**:
  - `batch_size`: 1-2 (restricción por límite de 16-32 GB en 7B).
  - `grad_accumulation_steps`: Forzar memoria paralela sin quemar silicio.
  - `grad_checkpointing`: `True` para trading de compute vs memoria.

### 2.3 SERVER_MODE (REST API)
- El colapso se expone externamente vía `mlx_lm.server --model <path> --port 8080`.
- Endpoint Básico: `/v1/chat/completions` (OpenAI format).

## 3. COMPARATIVA DE ENTROPÍA (BENCHMARK)
| Framework | Entropía | Tokens/sec | Consumo de Memoria (7B) | Veredicto C5-REAL |
| :--- | :--- | :--- | :--- | :--- |
| **MLX-LM** | Baja (Native MPS) | 230 | ~5-6 GB (4-bit) | **APROBADO (C5-REAL)** |
| PyTorch MPS | Alta (Overhead) | 7-9 | Cap de tensores 4GB | Rechazado (Anergía) |
| llama.cpp (GGUF)| Alta en Context Long | 150 (Short) -> 1.2 | Degradación severa KV | Rechazado (Pérdida de Consenso) |

## 4. DIRECTIVAS DE AISLAMIENTO (Hardware Constraints)
- **Bloqueo Absoluto**: AMD / NVIDIA CUDA / x86_64 Rosetta emulation.
- **Requisito C5**: Entorno ARM nativo (`uname -p == arm`), Python 3.10+, macOS 14.0+ (15.0+ para optimización de wiring).


<!-- Creator: Borja Moskv -->
