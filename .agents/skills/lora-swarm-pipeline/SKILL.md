---
name: lora-swarm-pipeline
description: "Pipeline de minería paralelizada con enjambre de agentes calibrado empíricamente, extracción por N-Zonas sin redundancia (SHA-256), formato ShareGPT/ChatML y clustering semántico de datasets multi-dominio. Dispara con \"lora swarm\", \"enjambre lora\", \"minería enjambre\", \"n-zonas enjambre\", \"dataset swarm\", \"enjambre ShareGPT\", \"minar datasets enjambre\", \"swarm pipeline\"."
---

# 🐝 LoRA Swarm Pipeline & Multi-Domain Clustering

## Cuándo usar esta Skill
- Cuando se requiera personalizar un LLM local con el conocimiento completo de un workspace masivo.
- Cuando se busque entrenar adaptadores LoRA/DoRA especializados por áreas de conocimiento interdisciplinares (Médico, Abogado, Físico, Músico, Ingeniero).

## Flujo de Trabajo
1. **Minería Swarm de Cero Anergía**: Ejecutar script Python multi-hilo/multi-proceso con concurrencia calibrada empíricamente ($P \times S$) mediante un *sweep* de cambios de contexto (`ru_nivcsw`), con lectura en memoria única (`f.readlines()`) para disipación de I/O = 0.
2. **Segmentación por Zonas Proporcionales (N-Zonas)**: Dividir los archivos en N franjas proporcionales adaptadas a la topología de hardware del clúster, garantizando cobertura del 100% sin truncamiento.
3. **Deduplicación SHA-256**: Generar hashes únicos por bloque `filename_zone_chunk` para garantizar cero redundancia entre iteraciones.
4. **Esquema Nativo ShareGPT / ChatML**: Formatear salidas en `messages` `[system, user, assistant]` consumibles por Unsloth, Llama-Factory y Axolotl.
5. **Clustering Multi-Etiqueta por Dominios**: Clasificar en sub-datasets por palabra clave (`moskv1_[dominio]_sharegpt.jsonl`): Físico, Médico, Abogado, Músico e Ingeniero.
6. **Entrenamiento PEFT/Unsloth**: Configurar adaptadores DoRA (rank=16, alpha=32) optimizados para VRAM reducida.
