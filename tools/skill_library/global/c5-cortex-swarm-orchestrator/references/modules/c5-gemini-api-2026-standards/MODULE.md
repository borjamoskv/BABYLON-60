---
name: c5-gemini-api-2026-standards
display_name: Estándares Gemini API 2026 & Tensor de Transducción
description: 'Estándares Gemini API 2026: modelos y cuotas verificables, diagnóstico HTTP, credenciales autorizadas y salidas estructuradas. Dispara con "gemini api 2026", "renovar gemini", "gemini api key", "tensor de transducción", "structured outputs", "gemini json schema", "cuotas gemini api".'
role: ejecutor
allowed_roles:
- ejecutor
directives:
  worktree_mode: read-write
  phase: implementation
  handoff:
    upstream: arquitecto
    downstream: auditor
---

# Gemini API: configuración verificable y credenciales

> **Directiva Declarativa:** Implementación dentro del alcance autorizado; los cambios de infraestructura y credenciales requieren autorización de la operación concreta.

## Modelos, cuotas y costes
- Mantener el modelo pedido por el usuario cuando esté disponible. Verificar identificador, capacidades y disponibilidad en la [documentación oficial de modelos](https://ai.google.dev/gemini-api/docs/models) y en el proyecto autorizado antes de configurar una integración. No cambiar de modelo por una preferencia fija del skill.
- Las [cuotas](https://ai.google.dev/gemini-api/docs/rate-limits) se aplican por proyecto, dependen de modelo y nivel, y no garantizan capacidad efectiva. Registrar límites observados y manejar errores con reintentos acotados cuando corresponda; no prometer ausencia de 429.
- Consultar precios y esquema vigente del SDK antes de recomendar presupuesto o parámetros de razonamiento. No fijar aquí tarifas, fechas de retirada, descuentos, límites de salida ni flags universales.

## Diagnóstico de errores
Registrar el código HTTP y mensaje redactado, servicio, modelo, fecha y configuración no sensible. Un código aislado o el prefijo de una clave no demuestran su causa. Contrastar credenciales, restricciones, habilitación de API y cuotas sin desactivar controles ni regenerar claves como primera respuesta automática.

## 3. Gestión y Diagnóstico de Credenciales API
1. **Diagnóstico pasivo:** Verificar presencia de variables de entorno y metadatos de configuración sin imprimir valores de claves. No buscar secretos en transcripciones, historiales ni archivos de conversación. Una variable presente no demuestra que la credencial sea válida.
2. **Comprobación de servicio:** Usar respuestas HTTP ya disponibles o preparar una prueba mínima. Una petición autenticada solo se ejecuta dentro del alcance autorizado para ese servicio; no confundir inspección local con permiso para llamadas externas o consumo de cuota. Redactar secretos en errores y logs.
3. **Preparación:** Registrar código de error, fecha y causa comprobada; si falta evidencia, declarar NO_VERIFICADO. Preparar pasos de remediación sin ejecutarlos. No equiparar cuota agotada con clave expirada.
4. **Mutación expresamente autorizada:** Crear proyectos, emitir, rotar o revocar claves requiere autorización explícita del operador para la operación concreta. Una sesión abierta de Safari o una clave existente no concede ese permiso. Si la autorización ya cubre exactamente la acción, conservarla sin pedir confirmación duplicada.
5. **Ejecución y custodia:** Aplicar las compuertas de autorización y atestación del proyecto. Elegir el almacén de secretos autorizado, preservar configuración existente y no exponer claves en consola, chat o control de versiones. Borrar una clave expuesta requiere plan de revocación y actualización de consumidores; ocultar una alerta no acredita remediación.

## Salidas estructuradas y pruebas
Usar un esquema compatible con el modelo y la versión instalada del SDK. Validar tipos y restricciones de dominio antes de consumir la respuesta. JSON válido, una semilla o temperatura fija no demuestran verdad ni determinismo entre ejecuciones o plataformas.

Antes de llamadas nuevas, acotar contexto, concurrencia, reintentos, salida y gasto al presupuesto autorizado. Preparar un ejemplo compatible con el SDK observado y verificarlo en el entorno permitido; no ejecutar llamadas ni consumir cuota solo para cargar el skill.

## Evidencia de cierre
Informar modelo y versión usados, fuentes consultadas, parámetros comprobados y resultado observado. Separar pruebas locales de llamadas reales; declarar NO_VERIFICADO lo que no se ejecutó. No registrar secretos ni deliberaciones internas del modelo.
