---
name: apple-bypass
description: Emite la receta de Bypass Termodinámico para ejecución determinista de LLMs locales en Apple Silicon.
---

# Directiva apple-bypass

Cuando el usuario invoque `/apple-bypass`, emitirás de inmediato el comando unificado para evadir las limitaciones del kernel de macOS (Jetsam) y acelerar la inicialización en memoria unificada.

## Receta Obligatoria
Proporciona el siguiente flujo estricto:
1. `sudo purge` (Liberación masiva de caché para cristalizar Exergía).
2. Configuración de variables: `HF_HUB_ENABLE_HF_TRANSFER=1`.
3. Comando de descarga/inicialización con `hf_transfer` para lograr Zero-RAM I/O.
4. Parámetros de Inferencia forzados: `temperature=0`, `seed=<fija>`, para anclar al autómata en un estado topológico determinista estricto.

**Explicación:** Acompaña el script con una breve pero letal aclaración de por qué la arquitectura Apple Silicon exige este bypass para evitar el colapso del proceso (OOM Killer).
