<!-- C5-REAL EXERGY CERTIFIED -->
a--
name: conversation_transcript_epistemic_auditor
description: extracción, clasificación, auditoría epistémica y generación de atlas historiográficos a partir de transcripciones jsonl (<appdatadir>/brain/<id>/.system_generated/logs/transcript.jsonl).
---

# conversation transcript epistemic auditor

este skill define la metodología estándar para escanear, analizar, categorizar y sintetizar el historial de conversaciones pasadas almacenadas en la plataforma (`<appdatadir>/brain/`).

## 1. cuándo invocarse
- cuando el usuario solicite un repaso o auditoría de $n$ conversaciones pasadas (ej. "repasa las ultimas 200 conversaciones", "analiza el historial").
- para rescatar credenciales rotadas, contexto perdido o decisiones de diseño tomadas en sesiones anteriores.
- para generar un atlas cronológico y una matriz de fricción/resolución sobre el desarrollo del proyecto.

## 2. flujo de ejecución (tool chain)

### paso 1: localización y extracción con script automatizado
ejecutar el script asistente incluido en el skill:
```bash
python3 .agents/skills/conversation_transcript_epistemic_auditor/scripts/audit_transcripts.py --limit 200 --output-dir .
```

el script realiza automáticamente:
- limpieza de etiquetas de metadatos (`<additional_metadata>`, `<ephemeral_message>`) y extracción de prompts.
- categorización por áreas del sistema y conteo de pasos.
- ordenación cronológica descendente y escritura del informe markdown `resumen_ultimas_n_conversaciones.md`.

### paso 2: categorización por áreas temáticas
clasificar cada conversación en bloques clave mediante coincidencia de palabras clave y rutas de archivo (ej. *kernel rust*, *filosofía escohotado*, *email delivery*, *wa-nexus*, *web deploy*, *gobernanza*).

### paso 3: identificación de fricciones y soluciones
escanear los mensajes en busca de indicadores de bloqueo/error (`bloqueado`, `error`, `spamhaus`, `working`, `cache`) para generar la matriz de fricción/resolución sistémica.

### paso 4: generación de artefactos muestrales
crear los artefactos finales en el directorio de la conversación actual (`<appdatadir>/brain/<conversation-id>`):
1. `resumen_ultimas_n_conversaciones.md`: resumen ejecutivo, desglose por categorías, matriz de herramientas y traducción a vectores enterprise.
2. `atlas_epistemico_conversaciones.md`: catálogo historiográfico completo (#1 a #n) organizado por fechas y fases de desarrollo.
