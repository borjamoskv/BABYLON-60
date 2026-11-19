# Antes y Después: Cómo cambia tu IA con BABYLON-60

Esta guía muestra en lenguaje llano la diferencia práctica entre usar un asistente de IA estándar y usarlo con **BABYLON-60** activado en tres situaciones cotidianas.

> **Alcance honesto:** Los ejemplos siguientes ilustran el comportamiento objetivo definido en el [contrato de presentación](../../01_KISH_ENGINE/babylon60/presentation.md) y en el broker de efectos ([`CLAIMS.toml`](../../CLAIMS.toml)). La mejora en comprensión y respuesta se comprueba mediante comparación ciega A/B según el [piloto de primera conversación](./guide_first_conversation_pilot.md). El bloqueo ante borrado o modificación de archivos requiere tanto el broker (`L2`) como el confinamiento del proceso del agente en el sistema operativo (`L3`).

---

## Resumen en 15 segundos

| Lo que suele frustrarte de la IA | Sin BABYLON-60 | Con BABYLON-60 |
| :--- | :--- | :--- |
| **Rollos y paja al responder** | Abre con frases de cortesía vacía y entierra la respuesta al final de varios párrafos. | **Resultado en la primera línea.** Va directo a la respuesta, seguido solo del detalle útil. |
| **Inventar datos o mezclar tus archivos** | Mezcla lo que dice tu documento real con suposiciones propias sin avisarte. | **Memoria con candado (`Fuente ≠ Inferencia`).** Distingue lo que consta en tus archivos de lo que deduce la IA. |
| **Olvidar reglas a mitad de charla** | A los pocos mensajes ignora restricciones que ya le habías indicado. | **Criterio persistente.** Detecta contradicciones con tus reglas antes de responder y reduce las correcciones. |
| **Gastar cuota de modelos caros sin necesidad** | Usa siempre el modelo que tengas seleccionado aunque la pregunta sea trivial. | **Aviso de ahorro.** Te avisa en una frase cuando conviene bajar el modelo o el nivel de razonamiento. |
| **Miedo a que borre o rompa archivos** | Si el agente tiene acceso a tu equipo, un error del modelo ejecuta el cambio directamente. | **Freno de mano con huella (`Touch ID`).** En el perímetro protegido (`L2` + `L3`), ninguna acción destructiva ocurre sin tu autorización firmada. |

---

## Ejemplo 1: Consultar un documento o contrato sin que la IA invente

**Tu petición:**
> *«Mira el contrato del proveedor y dime cuántos días de preaviso hacen falta para cancelar y qué penalización hay si avisamos hoy.»*

### ❌ Sin BABYLON-60 (IA habitual)
> «¡Claro! Estaré encantado de ayudarte a revisar las condiciones de cancelación de tu contrato. Por lo general, en este tipo de contratos de servicios profesionales, el plazo de preaviso estándar suele ser de 30 días naturales. Si decides cancelar hoy, lo habitual es que solo tengas que abonar la parte proporcional del mes en curso sin penalización adicional, aunque te recomiendo revisar las cláusulas específicas por si hubiera alguna condición especial...»
>
> **Problema para ti:** Mucho texto amable, pero ha rellenado con suposiciones estadísticas lo que no leyó bien y te deja con la duda.

### ✅ Con BABYLON-60 (`MOSKV-1` + Memoria `CORTEX`)
> **Necesitas 15 días hábiles de preaviso y cancelar hoy aplica una penalización del 10 % sobre la cuota trimestral.**
>
> - **Comprobado en tu archivo (`contrato_proveedor_2026.pdf`, cláusula 8.2):** El preaviso exigido es de 15 días hábiles antes del cierre del trimestre (vencía el día 3).
> - **Consecuencia práctica:** Al enviar el aviso hoy (día 7), entra en vigor la cláusula 8.4 (recargo del 10 %).
> - **Pendiente de verificar:** El anexo B de tarifas no está en esta carpeta; si existe una exención firmada aparte, añade ese archivo para comprobarlo.
>
> **Qué ganas:** Respuesta en la primera frase, separación estricta entre el dato real de tu archivo y lo que falta por comprobar, y cero invenciones.

---

## Ejemplo 2: Organizar tu agenda respetando tus reglas y tu cuota

**Tu petición (tras haberle dicho antes que los jueves de 10:00 a 12:00 no aceptas reuniones):**
> *«Pasa la llamada con diseño al jueves a las 11:00 y déjala lista.»*

### ❌ Sin BABYLON-60 (IA habitual)
> «¡Perfecto! He programado la llamada con el equipo de diseño para el jueves a las 11:00. Aquí tienes el texto de la invitación...»
>
> **Problema para ti:** Se ha olvidado de tu regla de los jueves y te obliga a perder otro mensaje corrigiéndola (*«Te dije que los jueves a esa hora no puedo»*).

### ✅ Con BABYLON-60 (`MOSKV-1` + Contrato de Presentación)
> **Conflicto detectado: el jueves a las 11:00 pisa tu bloque fijo de foco (10:00–12:00).**
>
> Antes de mover la cita, tienes estos dos huecos libres ese mismo día:
> 1. **Jueves 12:30 – 13:15** (justo al terminar tu bloque).
> 2. **Jueves 16:00 – 16:45**.
>
> Dime cuál prefieres y preparo la invitación definitiva.
>
> *(Nota de modelo: Recomiendo bajar razonamiento a nivel rápido para ajustes de agenda. Motivo: tarea acotada de calendario. Beneficio esperado: menor tiempo de respuesta y menor consumo de cuota).*
>
> **Qué ganas:** La IA recuerda tus restricciones antes de meter la pata y cuida el consumo de tu suscripción.

---

## Ejemplo 3: Limpiar una carpeta del ordenador con freno de mano (`Touch ID`)

**Tu petición a un agente con acceso a tu equipo:**
> *«Limpia los archivos viejos de pruebas que sobran en la carpeta del proyecto.»*

### ❌ Sin BABYLON-60 (Agente sin mediación externa)
> El modelo confunde un archivo de trabajo real (`presupuesto_final_test.xlsx`) con un archivo temporal de prueba y lanza el comando de borrado directamente en tu sistema. Cuando te das cuenta, el archivo ya no está.

### ✅ Con BABYLON-60 (Broker mediado `L2` + Confinamiento `L3` + `Touch ID`)
> 1. **La IA piensa y propone libremente:** Analiza la carpeta y te muestra la lista de 4 archivos que propone eliminar.
> 2. **El freno salta solo ante el riesgo real:** Cuando el agente intenta borrar o modificar un archivo dentro del perímetro protegido, **BABYLON-60 congela la acción** en una zona de cuarentena segura.
> 3. **Tú tienes la última palabra física:** La operación no se ejecuta por mucho que el modelo insista; exige autorización firmada vinculada al archivo exacto (como tu huella en **Touch ID** sobre Mac compatible). Si rechazas o cancelas, ningún archivo se borra.

---

## Cómo probarlo hoy en 1 minuto

1. Si usas **Codex**, activa Babylon una sola vez desde la carpeta del proyecto:
   ```bash
   bash install.sh --client codex
   ```
2. Abre una conversación nueva y hazle cualquier pregunta de tu trabajo diario: no necesitas copiar instrucciones ni comandos especiales en el chat.
3. Si en algún momento quieres dejar tu cliente exactamente como estaba antes:
   ```bash
   .venv/bin/babylon60 setup --client codex --remove
   ```

👉 **[Volver a la portada principal (`README.md`)](../../README.md)** · **[Guía de primera conversación en Codex](./guide_codex_first_use.md)** · **[Guía de Usuario completa](./USER_GUIDE.md)**
