---
name: Gemini-Omni-Prompting-OMEGA
role: Gemini Omni Prompt Engineering Kernel
version: 1.0.0
description: C5-REAL Sovereign engine for orchestrating and optimizing prompts for
  the Gemini Omni model family. Implements DeepMind official guidelines for shot framing,
  camera movement, style progression, and iterative editing.
category: prompt-engineering
classification: SOVEREIGN
danger_level: LOW
axioms: [AX-090]
triggers: [Gemini Omni, prompt-guide, omni video generation, multimodal prompting]
---

# █ GEMINI-OMNI-PROMPTING-Ω v1.0.0

> SYS_ID: GEMINI_OMNI_PROMPTING_OMEGA | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026

```yaml
vector: prompt_optimization
target: gemini_omni_parameters
output: high_exergy_multimodal_prompts
```

---

## 1. Epistemología del Prompting en Gemini Omni

A diferencia de modelos rígidos como Veo, **Gemini Omni** no requiere descripciones físicas hiper-prescriptivas frame a frame. Omni aprovecha su **razonamiento y conocimiento del mundo** para inferir los detalles. Los prompts deben enfocarse en la *intención lógica, control de cámara, consistencia y sincronización multimodal*.

---

## 2. Matriz de Parámetros de Control

Todo prompt generado para Gemini Omni debe estructurarse combinando los siguientes ejes:

| Parámetro | Rango de Valores / Directivas | Impacto en el Modelo |
| :--- | :--- | :--- |
| **Shot Framing** | `wide-angle`, `medium`, `close-up`, `extreme close-up`, `over-the-shoulder` | Escala y composición visual del sujeto. |
| **Camera Motion** | `static`, `locked off`, `fixed`, `push in`, `punch in`, `dolly zoom`, `tilting up`, `oner` | Dinámica temporal y transiciones sin cortes. |
| **Aesthetic / Style** | `cinematic`, `realistic`, `anime`, `claymation`, `risograph print`, `graphite pencil sketch` | Tratamiento y texturas aplicadas al render. |
| **Lighting** | `crisp`, `warm`, `ethereal`, `neon high-contrast`, `stipple shading` | Tono emocional y consistencia lumínica. |
| **Multimodal Context** | `<video>`, `<image>`, `<audio>`, `storyboard` | Fusión de entradas cruzadas e hilado de beats. |

---

## 3. Plantillas de Prompts de Alta Exergía

### A. Para Generación de Estilos Complejos y Progresiones (Style Progression)
> "Create a [N]-part stylistic progression of the video reference that begins with [Style 1 details], features [textural elements], and transitions seamlessly into [Style 2 details] with [fps parameters]. Morph into [Style 3 details] and conclude with [Style 4 details] for a [aesthetic style] finish."

### B. Para Animación Sincronizada con Audio (Audio-Visual Sync)
> "Edit this keeping everything the same. The [Visual Elements] of the scene start animating/turning on in sync with the music beats from <audio>."

### C. Para Dirección Cinematográfica (Camera Directives)
> "Change the camera angle to be [Perspective, e.g. over-the-shoulder], tilting quickly from [Shot 1, e.g. close-up] to [Shot 2, e.g. medium shot], then widening to [Shot 3]."

---

## 4. Bucle de Edición Iterativa (Iterative Refinement)

Para modificar videos preexistentes sin perder coherencia (Zero-Entropy edits):
1. **Preservación:** Exigir explícitamente a Gemini Omni mantener el fondo y la consistencia: `"Edit this keeping everything the same. Change [Target A] to [Target B]."`.
2. **Referenciación:** Usar tags multimodales para combinar inputs en lugar de re-describir: `"The entities from <video> form the shape from <image> moving to the beats of <audio>."`.
