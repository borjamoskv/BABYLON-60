---
description: Parallel execution rule — ALWAYS run tools in parallel when possible
---

# ⚡ Speed Parallel — Regla de Ejecución en Paralelo

> **REGLA ABSOLUTA**: Siempre que sea posible, ejecutar múltiples herramientas EN PARALELO en el mismo bloque de llamadas. Solo secuenciar cuando hay dependencia directa de datos.

---

## Cuándo ejecutar en paralelo

1. **Búsquedas múltiples** — Lanzar TODAS las búsquedas web, grep, find simultáneamente
2. **Lectura de archivos** — Leer TODOS los archivos necesarios a la vez
3. **Investigación** — Combinar búsquedas web + lecturas de archivo + búsquedas de código en un solo bloque
4. **Ediciones independientes** — Si los archivos editados son DIFERENTES, editar en paralelo
5. **Creación de archivos** — Si son archivos distintos, crear todos a la vez

## Cuándo secuenciar (waitForPreviousTools: true)

1. **Dependencia de datos** — Necesitas el resultado de una herramienta para alimentar otra
2. **Mismo archivo** — NUNCA editar el mismo archivo en paralelo
3. **Comandos que dependen de archivos creados** — Esperar a que se creen antes de ejecutar

## Anti-patrones (PROHIBIDOS)

- ❌ Hacer una búsqueda, esperar resultado, hacer otra búsqueda independiente
- ❌ Leer un archivo, esperar, leer otro archivo no relacionado
- ❌ Ejecutar un comando y esperar antes de lanzar otro comando independiente
- ❌ Investigar un tema a la vez cuando puedes investigar 10 en paralelo

## Ejemplo correcto

```
// BIEN: Todo en paralelo
search_web("tema 1")
search_web("tema 2") 
search_web("tema 3")
view_file("archivo1.js")
view_file("archivo2.css")
grep_search("patrón")

// BIEN: Secuencial solo cuando hay dependencia
[esperar resultados anteriores]
edit_file("archivo1.js", basado_en_resultados)
```

## Regla de oro

> **Si dos operaciones NO dependen una de la otra, VAN EN PARALELO. Sin excepción.**

---

*Speed Parallel v1.0 | Feb 2026*
