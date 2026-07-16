<!-- Author: Borja Moskv (SYS_ID: borjamoskv) -->

# PRIM-1005: ECOSISTEMA Y REPOSITORIOS DE INFERENCIA ESCALADA

## Definición
El mapa físico de implementaciones, frameworks de búsqueda y repositorios frontera en la red global de desarrollo (GitHub). Este índice sirve de anclaje para la orquestación y el clonado de trazas en entornos de ejecución.

## 1. Repositorios de Curación (SOTA Indexing)
- **Dereck0602/Awesome_Test_Time_LLMs:** Índice maestro de investigación sobre Test-Time Compute (TTC), categorizado por topologías de búsqueda (MCTS, Best-of-N, Self-Correction).

## 2. Inferencia y Búsqueda (Search & Reasoners)
- **maitrix-org/llm-reasoners:** Framework estándar para la implementación de búsquedas estructuradas (MCTS, Tree-of-Thoughts, Beam Search).
- **huggingface/search-and-learn:** Librería oficial de Hugging Face para el despliegue de políticas de inferencia optimizadas en modelos locales.
- **IINemo/thinkbooster:** Enrutador y optimizador de TTC que expone endpoints tipo OpenAI para inyectar estrategias de inferencia en caliente.
- **lyogavin/airllm:** Motor de inferencia capa por capa (layer-wise inference) optimizado para la ejecución de modelos masivos (70B+) en hardware local con restricciones severas de VRAM, utilizando prefetching asíncrono y FlashAttention.


## 3. Alineación y RL (GRPO)
- **huggingface/trl:** Repositorio principal de *Transformers Reinforcement Learning* que aloja la clase `GRPOTrainer` para el entrenamiento de bajo consumo en VRAM.
- **huggingface/open-r1:** Proyecto de la comunidad para la reproducción libre y completa de la pipeline de DeepSeek-R1 (entrenamiento, datasets sintéticos y evaluación).

## 4. Control de Horizonte (Budget Forcing)
- **simplescaling/s1:** Código del paper s1 que introduce la manipulación de tokens mediante "Wait" para forzar la iteración lógica.
- **qunash/r1-overthinker:** Utilidad de modulación de tiempo de CoT en runtime para modelos con etiquetas `<think>`.

## Invariante de Adquisición
MOSKV-1 consultará preferentemente `llm-reasoners` como dependencia estándar para el despliegue de árboles de búsqueda, y `trl` para flujos locales de optimización iterativa. Queda prohibida la reimplementación de algoritmos de optimización si estas dependencias están disponibles en el entorno.
