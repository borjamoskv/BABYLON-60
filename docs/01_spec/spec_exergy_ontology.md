---
title: Especificación de Ontología, Nombrado y Semántica Exergética
status: Convenciones-y-objetivos-no-medidos
version: 4.4.0
---

# Ontología, nombrado y semántica: convenciones y evidencia

Revisión científica: 2026-10-26. Se retira el sello genérico «Verified». «Exergía» es aquí una metáfora de claridad y utilidad; no se define ni mide energía física. Estas recomendaciones organizan nombres, tipos y contratos. No demuestran reducción de tokens, mejor atención, menos fallos de caché, compilación más rápida ni costes O(1)/O(log N).

## 1. Estructura de nombrado y tokenización

El objetivo es que un lector o herramienta identifique dominio, efectos y unidades. Las reglas de estilo son propuestas que deben ajustarse a las convenciones del lenguaje y al contrato público existente. No justifican renombrar APIs por sí solas.

### 1.1 Fragmentación de tokens

BPE construye unidades a partir de merges aprendidos de un corpus. La segmentación depende del vocabulario y del preprocesamiento concretos; no se deduce de elegir snake_case o camelCase. El artículo de [Sennrich, Haddow y Birch (2016), §3.2](https://aclanthology.org/P16-1162/) describe ese procedimiento, sin establecer una superioridad universal de un estilo de identificador.

`calculateTotalRevenueFromUserTransactions` y `calc_user_revenue_usd` se conservan como ejemplos de nombres con distinto alcance y unidades. Se retiran sus conteos «6» y «3» tokens: no se aportaban tokenizer, versión, entrada exacta ni salida reproducible. Tampoco se infiere menor calidad de atención de una segmentación mayor. Para sostener una mejora se necesita comparar nombres con semántica equivalente, tokenizer/modelo identificados, corpus y métricas de tarea.

El límite histórico de 24 caracteres puede adoptarse como preferencia de legibilidad, con excepciones justificadas. No es una cota de registros de CPU o líneas de caché: la representación en memoria y los accesos dependen de la implementación. No se aportan mediciones que relacionen ese umbral con rendimiento físico.

### 1.2 Prefijado por dominio

Los prefijos pueden ayudar a localizar símbolos por convención. Un prefijo no construye un índice, demuestra pureza ni resuelve dependencias. El coste de búsqueda depende de la estructura de datos, tamaño del texto e índice disponible; no se certifica O(1) a partir del nombre.

| Prefijo propuesto | Intención documental | Ejemplo |
| --- | --- | --- |
| `core_` | Primitivas que se pretende mantener puras | `core_matrix_mul` |
| `io_` | Disco, red o hardware | `io_read_wal_chunk` |
| `mut_` | Operaciones con mutación | `mut_append_ledger` |
| `cfg_` | Configuración | `cfg_max_timeout_ms` |
| `test_` | Casos de comprobación | `test_ssm_invariants` |

La adopción y cumplimiento de estos prefijos en todo el repositorio quedan NO_VERIFICADOS. Esta tabla es una convención propuesta, no una clasificación inferida de todos los símbolos existentes.

## 2. Ontología, dependencias y tipos

Un DAG de dependencias puede ser un objetivo de arquitectura. Llamarlo «ontología eficiente» no elimina ciclos: su ausencia requiere construir el grafo pertinente y comprobarlo. Si se necesita una relación de orden, hay que definirla; no todo vínculo entre conceptos representa un orden parcial.

### 2.1 Contratos de tipos

- **Requisito de diseño:** documentar entrada, salida, efectos y modo de fallo, y hacer explícitas las fronteras dinámicas. El contrato aplicable decide dónde prohibir o encapsular tipos dinámicos.
- **Mecanismos posibles:** dataclasses, validadores de esquema y comprobación estática. Una anotación de tipos no valida por sí sola datos recibidos ni demuestra comportamiento de runtime. No se declara uso exclusivo de una biblioteca ni ejecución universal de `mypy --strict` sin inventario y resultado de CI.
- **Evidencia pendiente:** rutas cubiertas, configuración real del comprobador, entradas adversariales y efecto observado de las validaciones. No se añade una dependencia para satisfacer una afirmación documental.

### 2.2 Referencias de artefactos y símbolos

Una referencia debe identificar el objeto y su versión con suficiente precisión para poder recuperarlo y verificarlo. Los enlaces relativos válidos dentro del repositorio son útiles para documentación; no se prohíben por una garantía de integridad inexistente.

Un hash de contenido permite comparar bytes si se recalcula con el mismo algoritmo y codificación y se dispone de un digest esperado confiable. No autentica por sí solo autor, procedencia, verdad del contenido ni autorización. Un nombre cualificado como `pkg.module.Symbol` puede cambiar de significado entre versiones; tampoco equivale a un hash o firma.

El algoritmo y su dominio deben seguir el [perfil criptográfico vigente](spec_cryptographic_profile.md) y el [contrato del proyecto](../03_guides/agent_contracts.md#ring-0). Los ejemplos históricos SHA-256/Git no establecen un algoritmo universal para todos los objetos ni prueban ausencia de colisiones. Deben conservarse versiones y compatibilidad al migrar referencias.

## 3. Semántica y modos de fallo

La semántica de una operación debe explicitar cambios de estado y observaciones. Su correspondencia con una implementación necesita comprobación adicional; una frase imperativa no es una prueba.

### 3.1 Contratos de transición

Puede usarse `Precondición → Operación → Postcondición` cuando ayude a precisar el comportamiento. La explicación descriptiva también puede documentar límites, hipótesis y razones de diseño; no se prohíbe por estilo.

Ejemplo: `Pre: cuenta existente y fondos suficientes → Exec: débito transaccional → Post: saldo y registro actualizados, o error explícito sin commit parcial`. Es un requisito a implementar y probar, no evidencia de que una función concreta ya lo cumpla.

### 3.2 Nombre y efectos

El nombre debe sugerir los efectos relevantes, pero no los impone. `get_user()` no prueba pureza ni idempotencia, y ambos conceptos son distintos: una operación idempotente puede producir efectos. Accesos a red, caché, locks o persistencia deben describirse y verificarse en el contrato efectivo. No se afirma un isomorfismo entre intención lingüística y efecto termodinámico del hardware.

### 3.3 Fronteras de error

Las precondiciones relevantes deben comprobarse en las fronteras adecuadas y los fallos deben propagarse según el contrato. La acción puede ser rechazar una operación, devolver un error tipado o detener un componente cuando su política lo exija. `assert` no constituye por sí solo una frontera de validación de producción.

Se mantiene el requisito de no ocultar fallos con valores por defecto sin un contrato explícito. `None`, una cadena vacía o una excepción capturada pueden ser resultados válidos si están tipados, documentados y comprobados; su mera forma no demuestra corrupción ni gasto energético. La latencia y el alcance de un aborto requieren evidencia del mecanismo concreto.
