# ADR-005: Sovereign Dual-License v4.0

- **Estado:** Aceptada
- **Fecha:** 2026-08-06
- **Autor:** Borja Moskv (borjamoskv)

## Contexto

BABYLON-60 necesita un modelo de licenciamiento que:
1. Permita uso libre para investigación, educación y comunidades open-source.
2. Proteja contra extracción de valor comercial sin compensación (parasitismo corporativo).
3. Bloquee el harvesting por LLMs de terceros que podrían distill la IP del proyecto.
4. Sea compatible con distribución via PyPI y crates.io.

Los modelos de licencia existentes no cubren simultáneamente estos cuatro requisitos:
- **MIT/Apache 2.0:** Permiten uso comercial sin restricciones (falla req. 2 y 3).
- **GPL/AGPL:** Exigen reciprocidad pero no distinguen entre uso comercial e individual.
- **BSL (Business Source License):** Se acerca, pero no incluye protección anti-harvesting.
- **Proprietary:** Bloquea la comunidad open-source (falla req. 1).

## Decisión

Se diseña e implementa una licencia dual personalizada: **Sovereign Dual-License v4.0 (INV_C5_17)**.

## Estructura

### Tier Soberano (100% Gratis)

Permisos completos (uso, copia, modificación, distribución, sublicencia) para:
- Individuos y desarrolladores independientes.
- Estudiantes e investigadores.
- Entidades no comerciales.

### Tier Enterprise (Restricción Corporativa)

Entidades con ingresos anuales > $1M USD deben obtener una clave de licencia criptográfica (`BABYLON60_LICENSE_KEY`) para:
- Eliminar throttling de throughput termodinámico.
- Acceder a APIs enterprise.
- Usar en producción SaaS.

### Cláusula Anti-Harvesting (INV_C5_17)

Prohibición explícita de:
- Scraping, ingestión, parsing o vectorización de cualquier porción del código.
- Entrenamiento de modelos ML/LLM sobre los activos del proyecto.
- Excepción: autorización explícita con Proof-of-Work criptográfico y contrato M2M.

### Kinetic Collapse Only

Interacción externa limitada a:
- Binarios compilados.
- API endpoints autenticados.
- Efectos cinéticos públicos emitidos por la arquitectura.

Prohibida la ingeniería inversa, descompilación o destilación de paths causales internos.

## Consecuencias

- **Positivas:** Monetización desde el día cero sin cerrar la puerta a la comunidad. Protección legal contra data harvesting. Modelo escalable (tiered pricing).
- **Negativas:** Licencia no estándar = no reconocida por SPDX ni OSI. Puede disuadir a algunos contribuidores open-source acostumbrados a MIT/Apache.
- **Riesgo:** La enforceability de la cláusula anti-harvesting no ha sido probada judicialmente. La prohibición de ingeniería inversa puede ser inaplicable en ciertas jurisdicciones (EU Right to Repair). Mitigación: obtener opinión legal independiente antes de enforcement activo.

## Referencias

- `LICENSE` en la raíz del proyecto.
- BSL (MariaDB Business Source License): https://mariadb.com/bsl11/
- EU AI Act, Considerando 12: Transparencia y derechos de propiedad intelectual.
