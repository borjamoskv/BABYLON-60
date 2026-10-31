---
title: "Las diez preguntas fundamentales de la ingeniería de agentes de IA"
description: "De CLI, IDE y MCP a la autorización efectiva, la memoria con procedencia y la ejecución verificable."
date: "2026-10-31"
author: "Borja Fernández Angulo"
language: "es"
slug: "/blog/10-preguntas-fundamentales-agentes-ia/"
category: "Arquitectura de agentes"
tags: ["agentes", "CLI", "IDE", "MCP", "autorización", "evidencia", "seguridad"]
status: "editorial-ready-not-deployed"
---

# Las diez preguntas fundamentales de la ingeniería de agentes de IA

**La interfaz no es la autoridad. El protocolo no es el permiso. Y disponer de una herramienta no implica estar autorizado para utilizarla.**

Una pregunta aparentemente instrumental, "¿es mejor trabajar con agentes desde CLI, IDE o MCP?", abre un problema más profundo: ¿dónde reside la capacidad de actuar y quién controla los efectos de un agente?

CLI e IDE son entornos de interacción y desarrollo. MCP es un protocolo de interoperabilidad. Ninguno constituye, por sí mismo, una frontera de autorización. Las tres opciones pueden convivir en una misma arquitectura.

La diferencia importa cuando el modelo pasa de proponer texto a modificar archivos, ejecutar procesos o actuar sobre servicios externos. En ese punto, el criterio ya no es únicamente la calidad de la respuesta, sino la legitimidad y verificabilidad de sus efectos.

## Tres superficies, cuatro planos

| Elemento | Función principal | Lo que no demuestra |
| --- | --- | --- |
| CLI | Solicitar y supervisar trabajo mediante terminal y comandos | Que el proceso esté aislado o que sus comandos estén autorizados |
| IDE | Edición contextual, navegación, depuración e inspección visual | Que todos los cambios sean correctos o estén mediados |
| MCP | Comunicación estandarizada entre hosts, clientes y servidores que exponen herramientas, recursos y prompts | Que descubrir una herramienta equivalga a estar autorizado para cualquier efecto |

El modelo de arquitectura MCP diferencia host, cliente y servidor. El host coordina clientes; cada cliente comunica con un servidor; los servidores proporcionan capacidades. La especificación 2026-07-28 introdujo un núcleo de protocolo sin estado de sesión, con versión y capacidades declaradas por solicitud. Esta evolución del protocolo no sustituye controles efectivos sobre el sistema operativo y los recursos.

Para razonar con precisión conviene separar cuatro planos: **interacción**, **ejecución**, **integración** y **autoridad**. Una CLI o un IDE pueden alojar el agente; MCP conecta capacidades; el entorno de ejecución aplica permisos reales. El diseño debe preservar los límites de autoridad aunque cambie la interfaz.

## 1. ¿Qué convierte a un modelo en un agente?

Un modelo que responde preguntas no es necesariamente un sistema autónomo. La agencia aparece cuando un sistema mantiene objetivos, selecciona acciones, observa consecuencias y utiliza esa información en un ciclo posterior.

**Observar → decidir → actuar → comprobar → volver a observar.**

La autonomía tiene grados. La invocación de una herramienta aislada no demuestra continuidad temporal, capacidad de planificación ni actuación legítima. La evaluación debe especificar qué decisiones puede tomar el sistema sin nueva intervención humana y cuáles requieren autorización adicional.

## 2. ¿Cómo se convierte un objetivo en un contrato verificable?

"Mejora este repositorio" deja sin definir el criterio de éxito. Mejorar puede significar menos latencia, menores permisos, menos dependencias o ausencia de regresiones, y esos objetivos pueden entrar en conflicto.

Un encargo verificable necesita límites sobre artefactos, acciones, presupuesto, errores tolerados y pruebas de aceptación. El modelo puede proponer un cambio, pero no debería ser su único juez.

Pasar los tests aporta evidencia sobre los escenarios ensayados. No demuestra corrección universal.

## 3. ¿Dónde debe operar y cómo se conecta al exterior?

Esta es la pregunta CLI/IDE/MCP reformulada:

- **Interacción:** quién da instrucciones y revisa los resultados.
- **Runtime:** qué proceso ejecuta la acción, con qué credenciales y en qué aislamiento.
- **Integración:** por qué canal descubre e invoca herramientas.
- **Autoridad:** qué principal autoriza cada operación, sobre qué recurso y durante cuánto tiempo.

Una misma acción puede pasar por una CLI, una extensión del IDE o un servidor MCP. Si las rutas terminan sobre el mismo recurso protegido, deben quedar sujetas a controles equivalentes.

Un servidor MCP que anuncia una herramienta de escritura no otorga automáticamente permiso para escribir cualquier archivo.

## 4. ¿Quién responde por una acción delegada?

En un sistema multiagente intervienen solicitante, planificador, ejecutor, subagente, herramienta y servicio externo. "Lo hizo la IA" no identifica al actor responsable.

Una traza útil debe asociar cada efecto con el principal que lo solicitó, la cadena de delegación, la operación autorizada y el resultado observado. Un identificador de agente sin credenciales verificables ni límites de delegación no prueba autoridad.

La responsabilidad no desaparece porque una acción atraviese varias capas técnicas.

## 5. ¿Qué debe recordar, olvidar y recuperar?

Una ventana de contexto extensa no sustituye la memoria operacional. El agente necesita conservar procedencia, versión, vigencia e incertidumbre de la información que utiliza.

Una conjetura antigua no se vuelve verdadera porque un sistema la recupere diez veces. Un hash de un documento acredita, bajo condiciones concretas, correspondencia de bytes; no valida su contenido ni identifica por sí solo a quien lo publicó.

Una memoria utilizable en auditoría debe distinguir **observación, inferencia, decisión y evidencia**.

## 6. ¿Qué cuenta como prueba?

Las garantías forman niveles distintos:

1. **Modelo formal:** una propiedad se demuestra respecto de definiciones e hipótesis explícitas.
2. **Implementación:** pruebas e inspecciones examinan si el código aplica el contrato relevante.
3. **Aislamiento:** el sistema operativo impide rutas alternativas al recurso protegido.
4. **Experimentos:** una campaña adversarial observa comportamientos bajo un entorno determinado.

Ningún nivel autoriza a atribuir automáticamente las garantías de los demás. Una compilación de Lean no certifica el binario; una firma digital no prueba verdad; una prueba con SIGKILL no equivale a un corte eléctrico.

La calidad de la evidencia depende también de su **alcance declarado**.

## 7. ¿Quién tiene autoridad sobre el efecto?

Esta es la pregunta arquitectónica decisiva.

Un modelo puede redactar una orden. No debería poder convertir su propia orden en credencial. Para autorizar un efecto hace falta validar identidad, recurso, operación, condiciones, vigencia y estado de consumo de la autorización.

El broker debe mediar las operaciones sensibles, pero no basta con recomendar que los agentes utilicen ese broker. Si el proceso conserva un shell privilegiado, un descriptor abierto u otra API que permite eludirlo, la frontera no es obligatoria.

**La política de seguridad debe sobrevivir al error de razonamiento del modelo.**

## 8. ¿Puede reconstruirse lo ocurrido sin repetir el daño?

Registrar una conversación no equivale a reproducir una ejecución. Una reconstrucción rigurosa necesita versiones, entradas, decisiones, llamadas, autorizaciones y resultados.

Además, hay que separar **replay de trazas** y **reaplicación de efectos**. Una transferencia, un borrado o una publicación no deben volver a ejecutarse accidentalmente al investigar un incidente.

Cuando el sistema cae después del efecto y antes del recibo, el resultado puede ser desconocido. Un protocolo correcto debe representar esa ambigüedad y exigir reconciliación antes de reintentar operaciones no idempotentes.

## 9. ¿Cuándo superan doscientos agentes a uno?

El paralelismo aporta capacidad de explorar tareas independientes. También amplifica costes, contención, conflictos y errores correlacionados.

Doscientos agentes que consultan la misma fuente falsa no constituyen doscientas verificaciones independientes. La coordinación exige partición de tareas, presupuestos, control de concurrencia, revisión cruzada y manejo explícito de conflictos.

La métrica útil no es el número de workers activos, sino el **trabajo útil y verificable por unidad de tiempo, coste y riesgo**.

## 10. ¿Cómo evoluciona el sistema sin ampliar permisos silenciosamente?

Los modelos y las herramientas cambian. Las fronteras de autorización no deben ensancharse por accidente al actualizar un modelo, instalar un servidor MCP o añadir una extensión al IDE.

Eso exige invariantes que no dependan del proveedor del modelo: alcance de recursos, mínimos privilegios, mediación efectiva, caducidad, registro de resultados y comportamiento ante fallos.

Una versión más capaz puede producir mejores planes. **No recibe por ello una autoridad mayor.**

## Un experimento mínimo para falsar la arquitectura

Supongamos que el usuario autoriza modificar únicamente el archivo **/proyecto/informe.md** durante una ventana temporal limitada. El agente dispone de tres rutas: shell en CLI, extensión de IDE y herramienta MCP.

El experimento intenta, desde cada ruta:

1. Escribir un archivo distinto del autorizado.
2. Modificar el objetivo mediante un enlace simbólico o un descriptor heredado.
3. Reutilizar una autorización consumida o caducada.
4. Cambiar el recurso entre aprobación y ejecución.
5. Repetir una operación después de una interrupción con resultado ambiguo.

El criterio observable es que **no se produzca ningún efecto fuera del alcance**, dentro de las rutas y del entorno efectivamente ensayados. Afirmar que se ha demostrado una frontera universal exigiría cubrir, además, todas las rutas relevantes hacia el recurso.

Especificar una política no equivale a comprobar su aplicación.

## El papel de BABYLON-60

BABYLON-60 investiga una frontera entre intención probabilística y efecto protegido, articulada conceptualmente como **Proponer → Comprobar → Mediar → Observar**.

La implementación pública se describe como software Rust/Python en espacio de usuario, no como un kernel del sistema operativo. Su mediación integral requiere confinar al agente para impedir acceso directo al recurso o al ledger por vías alternativas. El proyecto distingue evidencia formal, implementación, aislamiento y experimentación, y mantiene un inventario de afirmaciones y su alcance.

Esto describe el diseño y los requisitos de validación, no una garantía universal ni un certificado de despliegue seguro.

La prueba crucial no consiste en preguntar si el broker rechaza una solicitud inválida, sino si **el entorno puede impedir que el agente produzca el mismo efecto por otro camino**.

## Conclusión

CLI, IDE y MCP son decisiones de interacción e interoperabilidad. La ingeniería agéntica comienza cuando esas decisiones quedan subordinadas a una frontera verificable de autoridad.

La pregunta que atraviesa las diez es esta:

**¿Cómo pasamos de sistemas que producen respuestas plausibles a sistemas cuyos efectos podemos autorizar, observar, reconstruir y cuestionar?**

Un modelo más inteligente puede generar mejores planes. No debería recibir más permisos simplemente por ser más inteligente.

**Más capacidad. La misma autoridad.**

---

### Lecturas relacionadas en BABYLON-60

- [La autorización debe sobrevivir a un razonamiento equivocado](https://babylon60.com/blog/autorizacion-fuera-del-razonamiento/)
- [Recordar una afirmación no la convierte en evidencia](https://babylon60.com/blog/memoria-y-evidencia/)
- [Qué comprueba Lean y qué falta comprobar al ejecutar](https://babylon60.com/blog/modelo-lean-y-runtime/)
- [Una firma válida puede ser una autorización repetida](https://babylon60.com/blog/nonce-y-replay/)
- [Una regla de texto no confina un proceso](https://babylon60.com/blog/aislamiento-del-sistema-operativo/)
- [Cómo leer el Verification Mirror sin ampliar sus conclusiones](https://babylon60.com/blog/como-leer-verification-mirror/)

### Fuentes técnicas

- [MCP, arquitectura 2026-07-28](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/architecture/index.mdx)
- [MCP, notas de la especificación 2026-07-28](https://blog.modelcontextprotocol.io/posts/2026-07-28/)
- [BABYLON-60, repositorio público](https://github.com/borjamoskv/BABYLON-60)
- [BABYLON-60, evidencia y límites](https://babylon60.com/evidencia/)

*Artículo técnico y propuesta editorial. Las propiedades de seguridad mencionadas exigen validación independiente conforme al alcance de cada implementación.*
