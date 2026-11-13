# Alertas Dependabot de main — 6 de noviembre de 2026

> **Registro histórico recuperado el 13 de noviembre de 2026.** Este documento conserva la evidencia y los dictámenes de la iteración del 5–6 de noviembre, tomada de `bc563d6cd4d6e021ca73ec035a75588774a4f511`. No valida el árbol recuperado sobre `daa0a848e5dce9d79446fe47dc4c3083061346a5` ni sustituye su nueva aceptación. H08 y la ejecución remota de H09 permanecen pendientes; los resultados locales de Docker, dependencias y pruebas requieren repetición sobre ese árbol.

## Resultado estático

La API de GitHub devolvió 40 alertas abiertas: 35 pip y cinco npm, correspondientes a 38 GHSA y 12 paquetes normalizados. Severidad informada: dos críticas, 11 altas, 21 medias y seis bajas. No hay alertas Cargo entre estas 40.

La comparación utiliza `main` en `930981ea47a5a4524e9c841338f1fd1a1caceb68` y el head previo de la PR #48 en `fa2be511c15def6327f31628fb04c95353110823`. Las 35 alertas Python ya estaban corregidas en ese head; las cinco npm seguían presentes. Las versiones del árbol corregido quedan fuera de los rangos afectados de las 40 alertas capturadas. Esto es una comparación de versiones y rutas del lock, no una demostración universal de ausencia de vulnerabilidades ni de explotación de todas las dependencias.

La respuesta paginada original tiene SHA-256 `640795b8fe7deb8ed2e8205f8772538b0fb93123e566a8d080a962a5189fa6dd`; el arreglo normalizado de 40 registros, `1fcc6239971c8e4745f7a5fac3f83156ffe3ad6704b2c0ce8f24a90961a0eac8`. Se consultó el endpoint de alertas en modo lectura, sin descartar ni cerrar alertas manualmente.

## Cambios

- `uv.lock`: las 35 alertas Python se comprueban individualmente con PEP 440, incluyendo el límite prerelease `4.0.0a1`. Diez paquetes, 33 GHSA distintos, cero versiones del PR en esos rangos vulnerables. `fastmcp-slim` sigue presente en 4.1.6; no se atribuye su corrección a una eliminación.
- `01_KISH_ENGINE/services/email_inbound`: `postal-mime` 3.0.0 → 4.0.8, con suelo declarado `^4.0.8`. Se contrasta la API del constructor, `parse(ArrayBuffer)` y adjuntos con el tag oficial. La corrección atiende el coste de decodificar palabras RFC 2047 y los presupuestos de cabeceras/partes de mensajes anidados.
- `01_KISH_ENGINE/cortex/transducers/video_remotion`: `fast-uri` 3.1.8 → 3.1.9. Es una dependencia de desarrollo transitiva de Ajv, a través del bundler/webpack/schema-utils. Se conserva su alcance de desarrollo al evaluar exposición; instalar herramientas de desarrollo sí la incorpora al árbol.
- La auditoría npm completa detectó además [GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5), relativo al consumo de memoria de Zod al validar colecciones grandes. No pertenece a las 40 alertas iniciales. El grupo Remotion 4.0.526 se actualiza coordinadamente a 4.0.540, con sus dos suelos directos en `^4.0.540`; esa versión publicada ya fija Zod 4.6.7, posterior al primer parche 4.6.6. No se afirma que Remotion 4.0.540 sea el primer release histórico seguro. El paquete distribuido `@remotion/studio-protocol` incorpora también una copia de Zod en `dist/index.cjs`: se verifican marcadores 4.5.4 en 4.0.526 y 4.6.7 en 4.0.540, con integridad del archivo publicado. Por eso la corrección usa el grupo publicado por su mantenedor; cambiar únicamente la dependencia Zod externa dejaría esa copia anterior. Los siete avisos altos del primer `npm audit` representan paquetes/metavisos derivados de un mismo GHSA, no siete vulnerabilidades independientes.

Los suelos de ejecución de estos módulos npm quedan declarados por sus dependencias: `postal-mime` exige Node >=20 y `@rspack/core` exige `^20.19.0 || >=22.12.0`. Las comprobaciones del candidato se ejecutan con Node 26.13.0 y npm 11.20.0; no acreditan ejecución en Node 18 ni en otros sistemas operativos.

## Matriz de las 40 alertas originales

Las filas npm proceden de los dos `package-lock.json` indicados arriba; todas las filas pip proceden de `uv.lock`. «PR corregida» describe el árbol de esta rama; la rama principal permanece invariable.

| ID | GHSA | Severidad | Paquete | main | PR corregida | Estado en el árbol de la PR |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | [GHSA-xcq7-p3pf-p88h](https://github.com/advisories/GHSA-xcq7-p3pf-p88h) | medium | `opentelemetry-api` | `1.44.0` | `1.45.2` | Ya corregida en la PR anterior |
| 2 | [GHSA-vqqp-x5qm-5qp4](https://github.com/advisories/GHSA-vqqp-x5qm-5qp4) | medium | `fastmcp-slim` | `4.1.0` | `4.1.6` | Ya corregida en la PR anterior |
| 3 | [GHSA-7xgj-8392-5q4r](https://github.com/advisories/GHSA-7xgj-8392-5q4r) | medium | `fastmcp-slim` | `4.1.0` | `4.1.6` | Ya corregida en la PR anterior |
| 4 | [GHSA-vqqp-x5qm-5qp4](https://github.com/advisories/GHSA-vqqp-x5qm-5qp4) | medium | `fastmcp` | `4.1.0` | `4.1.6` | Ya corregida en la PR anterior |
| 5 | [GHSA-7xgj-8392-5q4r](https://github.com/advisories/GHSA-7xgj-8392-5q4r) | medium | `fastmcp` | `4.1.0` | `4.1.6` | Ya corregida en la PR anterior |
| 6 | [GHSA-f2hq-32vh-53cc](https://github.com/advisories/GHSA-f2hq-32vh-53cc) | high | `postal-mime` | `3.0.0` | `4.0.8` | Corregida en esta iteración |
| 9 | [GHSA-333x-w4r6-6crp](https://github.com/advisories/GHSA-333x-w4r6-6crp) | low | `fast-uri` | `3.1.8` | `3.1.9` | Corregida en esta iteración |
| 10 | [GHSA-wjr9-j795-jxcr](https://github.com/advisories/GHSA-wjr9-j795-jxcr) | medium | `fast-uri` | `3.1.8` | `3.1.9` | Corregida en esta iteración |
| 11 | [GHSA-xhq7-xmqj-769h](https://github.com/advisories/GHSA-xhq7-xmqj-769h) | low | `fast-uri` | `3.1.8` | `3.1.9` | Corregida en esta iteración |
| 12 | [GHSA-w74x-v6f9-j3xg](https://github.com/advisories/GHSA-w74x-v6f9-j3xg) | medium | `fast-uri` | `3.1.8` | `3.1.9` | Corregida en esta iteración |
| 13 | [GHSA-xmj3-9gf7-h52w](https://github.com/advisories/GHSA-xmj3-9gf7-h52w) | low | `setuptools` | `83.0.0` | `84.2.1` | Ya corregida en la PR anterior |
| 14 | [GHSA-v4x8-3wr5-3wq8](https://github.com/advisories/GHSA-v4x8-3wr5-3wq8) | high | `filelock` | `3.32.2` | `4.2.9` | Ya corregida en la PR anterior |
| 15 | [GHSA-567q-5qvw-pf92](https://github.com/advisories/GHSA-567q-5qvw-pf92) | low | `filelock` | `3.32.2` | `4.2.9` | Ya corregida en la PR anterior |
| 16 | [GHSA-9vhv-jxww-xfm5](https://github.com/advisories/GHSA-9vhv-jxww-xfm5) | low | `filelock` | `3.32.2` | `4.2.9` | Ya corregida en la PR anterior |
| 17 | [GHSA-6q48-6c7w-9gw2](https://github.com/advisories/GHSA-6q48-6c7w-9gw2) | critical | `certifi` | `2026.7.22` | `2026.10.23` | Ya corregida en la PR anterior |
| 18 | [GHSA-6v38-4h7w-rj9h](https://github.com/advisories/GHSA-6v38-4h7w-rj9h) | critical | `authlib` | `1.7.2` | `1.9.4` | Ya corregida en la PR anterior |
| 19 | [GHSA-45c3-73f7-pv4m](https://github.com/advisories/GHSA-45c3-73f7-pv4m) | high | `dnspython` | `2.8.0` | `2.9.2` | Ya corregida en la PR anterior |
| 20 | [GHSA-jj7h-c3hg-m23x](https://github.com/advisories/GHSA-jj7h-c3hg-m23x) | low | `authlib` | `1.7.2` | `1.9.4` | Ya corregida en la PR anterior |
| 21 | [GHSA-7vr2-2fgp-9w7p](https://github.com/advisories/GHSA-7vr2-2fgp-9w7p) | high | `authlib` | `1.7.2` | `1.9.4` | Ya corregida en la PR anterior |
| 22 | [GHSA-q686-2qmg-hqc7](https://github.com/advisories/GHSA-q686-2qmg-hqc7) | medium | `authlib` | `1.7.2` | `1.9.4` | Ya corregida en la PR anterior |
| 23 | [GHSA-fch4-3c6x-j4gc](https://github.com/advisories/GHSA-fch4-3c6x-j4gc) | medium | `authlib` | `1.7.2` | `1.9.4` | Ya corregida en la PR anterior |
| 24 | [GHSA-c5mf-xmp2-59rc](https://github.com/advisories/GHSA-c5mf-xmp2-59rc) | medium | `authlib` | `1.7.2` | `1.9.4` | Ya corregida en la PR anterior |
| 25 | [GHSA-x4rv-c3wx-4cr8](https://github.com/advisories/GHSA-x4rv-c3wx-4cr8) | medium | `authlib` | `1.7.2` | `1.9.4` | Ya corregida en la PR anterior |
| 26 | [GHSA-8m4g-j4wp-wgcg](https://github.com/advisories/GHSA-8m4g-j4wp-wgcg) | high | `Authlib` | `1.7.2` | `1.9.4` | Ya corregida en la PR anterior |
| 27 | [GHSA-fq56-3cx3-fjxp](https://github.com/advisories/GHSA-fq56-3cx3-fjxp) | medium | `filelock` | `3.32.2` | `4.2.9` | Ya corregida en la PR anterior |
| 28 | [GHSA-m462-7rxw-wvpg](https://github.com/advisories/GHSA-m462-7rxw-wvpg) | medium | `filelock` | `3.32.2` | `4.2.9` | Ya corregida en la PR anterior |
| 29 | [GHSA-j8f7-rjxc-mr56](https://github.com/advisories/GHSA-j8f7-rjxc-mr56) | medium | `filelock` | `3.32.2` | `4.2.9` | Ya corregida en la PR anterior |
| 30 | [GHSA-69hj-f68j-2879](https://github.com/advisories/GHSA-69hj-f68j-2879) | medium | `filelock` | `3.32.2` | `4.2.9` | Ya corregida en la PR anterior |
| 31 | [GHSA-rfpc-qcw5-3pc4](https://github.com/advisories/GHSA-rfpc-qcw5-3pc4) | medium | `filelock` | `3.32.2` | `4.2.9` | Ya corregida en la PR anterior |
| 32 | [GHSA-cwqr-hh33-gh44](https://github.com/advisories/GHSA-cwqr-hh33-gh44) | medium | `filelock` | `3.32.2` | `4.2.9` | Ya corregida en la PR anterior |
| 33 | [GHSA-8mx5-7m5m-r77g](https://github.com/advisories/GHSA-8mx5-7m5m-r77g) | medium | `filelock` | `3.32.2` | `4.2.9` | Ya corregida en la PR anterior |
| 34 | [GHSA-9c4x-gm8v-wgc4](https://github.com/advisories/GHSA-9c4x-gm8v-wgc4) | medium | `filelock` | `3.32.2` | `4.2.9` | Ya corregida en la PR anterior |
| 35 | [GHSA-6627-m3xw-93mp](https://github.com/advisories/GHSA-6627-m3xw-93mp) | medium | `filelock` | `3.32.2` | `4.2.9` | Ya corregida en la PR anterior |
| 36 | [GHSA-jpxq-7h8p-2q76](https://github.com/advisories/GHSA-jpxq-7h8p-2q76) | high | `joserfc` | `1.7.4` | `1.8.0` | Ya corregida en la PR anterior |
| 37 | [GHSA-9pg5-8c7x-5hfx](https://github.com/advisories/GHSA-9pg5-8c7x-5hfx) | medium | `joserfc` | `1.7.4` | `1.8.0` | Ya corregida en la PR anterior |
| 38 | [GHSA-fm9c-5rcf-2q5p](https://github.com/advisories/GHSA-fm9c-5rcf-2q5p) | high | `pyasn1` | `0.6.4` | `0.6.5` | Ya corregida en la PR anterior |
| 39 | [GHSA-9m75-vc3g-4x39](https://github.com/advisories/GHSA-9m75-vc3g-4x39) | high | `pyasn1` | `0.6.4` | `0.6.5` | Ya corregida en la PR anterior |
| 40 | [GHSA-mm57-4v3p-rchx](https://github.com/advisories/GHSA-mm57-4v3p-rchx) | high | `pyasn1` | `0.6.4` | `0.6.5` | Ya corregida en la PR anterior |
| 41 | [GHSA-2qm8-x737-gmw5](https://github.com/advisories/GHSA-2qm8-x737-gmw5) | high | `pyasn1` | `0.6.4` | `0.6.5` | Ya corregida en la PR anterior |
| 42 | [GHSA-c73q-w75p-j82v](https://github.com/advisories/GHSA-c73q-w75p-j82v) | high | `Authlib` | `1.7.2` | `1.9.4` | Ya corregida en la PR anterior |

## Comprobación y alcance

La evidencia externa de esta iteración conserva la matriz JSON/CSV, rutas transitivas, rangos, versiones, integridades y resultados sin reescribir las ejecuciones anteriores. Las comprobaciones npm se realizan con instalación de lock e integridades, auditoría completa con dependencias de desarrollo y pruebas del worker/bundler. Las pruebas de cabeceras y partes anidadas son locales y acotadas; no se envía correo ni se llama al webhook de producción. Una sonda de tiempos describe únicamente los tamaños y hardware observados.

Los tests npm portables quedan en cada proyecto y usan el parser real, crypto real y entradas locales; el webhook se captura dentro del test. Se pueden repetir desde la raíz del repositorio:

```bash
(cd 01_KISH_ENGINE/services/email_inbound && npm ci --ignore-scripts && npm test && npm audit)
(cd 01_KISH_ENGINE/cortex/transducers/video_remotion && npm ci --ignore-scripts && npm run test:security && npm audit)
```

Los resultados de la batería Python/Swift y los cinco gates sobre el commit final firmado se registran después del freeze en la descripción de la PR y sus artefactos de aceptación. Este informe no presenta una ejecución anterior como resultado del nuevo commit. Lean, Miri, reloj lógico, Cargo y firma conservan sus ámbitos ya declarados en la [revisión histórica](PR48_FINAL_REVIEW_2026-11-05.md).

La compatibilidad del ledger V1 y el compromiso V2 no se alteran por estas actualizaciones npm; su [contrato de versiones](../03_guides/guide_ledger_hash_versions.md) sigue vigente. No se cambian las dependencias Python/Rust ni el código productivo del worker, de memoria, autorización o confinamiento.

## Pendientes

H08 permanece aplazado por decisión del operador y H09 remoto sigue pendiente. La PR se mantiene abierta sin merge ni auto-merge. No se cambia facturación ni se relajan protecciones. Mantener `main` sin cambios conserva sus alertas abiertas; la ausencia de cierre automático en `main` no sustituye la comparación explícita con el árbol de la PR.
