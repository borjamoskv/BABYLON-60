# BABYLON-60 — Cadena de Título de Propiedad Intelectual (IP_PROVENANCE)

**Documento:** `contracts/IP_PROVENANCE.md`  
**Revisión original:** v1.0.0 · 2026-11-07\
**Autor de Registro:** Borja Fernández Angulo (`borjamoskv@gmail.com`)  
**Rol:** Creador Único, Investigador Principal, Operador Raíz Sovereign  
**Repositorio Canónico:** `borjamoskv/BABYLON-60-VAULT` (privado) · espejo: `borjamoskv/BABYLON-60`  
**Registro de la revisión original:** `[AX-41] GOVERNANCE: add IP_PROVENANCE.md and reseal release manifest`

---

## 1. Certificación de Autoría en Sala Limpia

Borja Fernández Angulo declara y certifica que **la totalidad del código fuente**, las demostraciones formales en Lean 4, los esquemas Z3, los manifiestos de gobernanza y la documentación técnica contenidos en el repositorio `BABYLON-60` han sido producidos íntegramente por el autor mediante trabajo original en sala limpia ("clean-room authorship"), sin transferencia de código fuente de empleadores previos, sin código procedente de proyectos bajo acuerdo de no divulgación de terceros, y sin dependencias de Cargo o PyPI con licencias copyleft incompatibles con la licencia soberana del proyecto.

La arquitectura conceptual, la terminología sumeria (`ABZU`, `KISH`, `EDIN`, `KUDURRU`, `LARSA`), el protocolo AX-0, el diseño del Seqlock SPMC y el motor BFT heterogéneo son obras intelectuales originales del autor, desarrolladas en el período 2024–2026.

---

## 2. Módulos Nativos Internalizados — Linaje Ancestral

El autor identifica los siguientes proyectos propios como referencias para componentes de BABYLON-60. La tabla distingue el vínculo técnico de cada componente. El autor declara que conserva la titularidad de todos ellos.

| Componente en BABYLON-60 | Proyecto relacionado | Repositorio | Naturaleza del vínculo | SPDX Header |
|:---|:---|:---|:---|:---:|
| [`src/seqlock.rs`](../src/seqlock.rs) | `axiom-0` | [`borjamoskv/axiom-0`](https://github.com/borjamoskv/axiom-0) | El autor atribuye el patrón de lectura coherente a `SeqlockCell`. BABYLON-60 implementa el protocolo en `SharedManifest`. | ✓ |
| `src/larsa_bft.rs` | `teorema-robinson-moskv` | `borjamoskv/teorema-robinson-moskv` (privado, archivado) | Formalización del consenso BFT heterogéneo (Rust + Lean 4 + Z3) absorbida al motor KISH | ✓ |
| `01_KISH_ENGINE/cortex/` (subsistema) | `cortex-persist` standalone | `borjamoskv/cortex-persist` (público) | Núcleo SQLite WAL + linaje SHA-256 + filtrado epistémico integrado como submódulo funcional en Ring-1 | — |

> **Nota sobre `teorema-robinson-moskv`:** El registro de 2026-11-07 sitúa sus artefactos compilados, tests y commits históricos en `BABYLON-60-VAULT`.

> **Nota sobre `cortex-persist`:** El repositorio público `borjamoskv/cortex-persist` contiene la versión standalone del motor de persistencia. La versión integrada dentro de `BABYLON-60` ha sido refactorizada y extendida; cualquier fork del repo standalone posterior a 2025-01-01 no afecta a los derechos del núcleo integrado en este monorepo.

### Seqlock y axiom-0

**Atribución e implementación.** El autor vincula el protocolo de BABYLON-60 con su trabajo sobre `SeqlockCell<T, N>` en `axiom-0`. Ambos lectores aceptan los datos cuando la secuencia permanece estable y par durante la lectura. En BABYLON-60, `SharedManifest` publica una época y un hash de 32 bytes. Las funciones de compatibilidad `publish` y `read` delegan en `SharedManifest::publish` y `SharedManifest::read_snapshot`. La emisión de recibos de parada usa esa lectura para obtener la época y el hash de una misma publicación. [SeqlockCell en la revisión examinada](https://github.com/borjamoskv/axiom-0/blob/5cfffafd590f2be901c2403322882241f6d9e861/src/seqlock.rs#L152-L184) · [Implementación de SharedManifest](../src/shared_manifest_core.rs) · [Adaptador](../src/seqlock.rs) · [Recibos](../src/receipt.rs).

| Fecha (2026) | Repositorio y commit | Evidencia en Git |
| --- | --- | --- |
| 9 de agosto | BABYLON-60 `9431aba1` | `src/seqlock.rs` ya contiene las operaciones de publicación y lectura sobre `SharedManifest`. |
| 14 de septiembre | axiom-0 `1f5236b` | El primer commit conservado en el historial examinado contiene el seqlock de Axiom y el motor de tipos QTT. |
| 23 de octubre | BABYLON-60 `6ac9b8bd` | El protocolo se concentra en `src/shared_manifest_core.rs` y `src/seqlock.rs` pasa a delegar en él. |
| 7 de noviembre | BABYLON-60 `e6491252` | El cambio en `src/seqlock.rs` añade diez líneas de cabecera con la atribución. Las funciones ya existían. |

**Alcance de la comprobación del 18 de noviembre de 2026.** La resolución de Cargo con el lockfile de BABYLON-60 (`d59d391c`) carece de dependencia de `micro-axiom-0`. La comparación de los identificadores de contenido de Git (`git ls-tree -r`) entre esa revisión y `axiom-0` (`5cfffafd`) dio cero archivos completos idénticos. La atribución se limita al patrón seqlock. En BABYLON-60 no se encontró uso del motor QTT, del generador de C ni de `TurbineEngine` de Axiom. Una transferencia directa de código, incluida una posible adaptación de fragmentos, queda sin acreditar en el historial disponible.

---

## 3. Perímetro Excluido del Perímetro de IP Soberano

Los siguientes artefactos presentes en el árbol de trabajo **no forman parte del perímetro de propiedad intelectual transferible** en operaciones de M&A o licenciamiento:

| Ruta | Motivo de Exclusión |
|:---|:---|
| `experiments/oncology/` | Dataset de investigación biomédica de terceros con restricciones de redistribución. No ejecutable como producto. |
| `deps/` (si existe) | Vendored copies de crates Rust bajo sus licencias originales (MIT / Apache-2.0). Ver SBOM completo. |
| Archivos `.ots` | Atestaciones OpenTimestamps de terceros (Bitcoin blockchain). No son IP, son evidencia criptográfica. |

---

## 4. Auditoría de Cadena de Suministro (SBOM)

### 4.1 Dependencias Rust (Cargo)

- **Total de crates:** ~498 (directas + transitivas, `cargo tree --locked`)
- **Licencias predominantes:** MIT, Apache-2.0, ISC, BSD-2-Clause
- **Licencias copyleft detectadas:** Ninguna (GPL / LGPL / AGPL)
- **Crates con licencia dual MIT/Apache-2.0:** Mayoría del ecosistema `tokio`, `serde`, `rusqlite`
- **Crates con licencia propia:** `rusqlite` (MIT), `loom` (MIT, solo dev-dependency)
- **Verificación:** `cargo deny check licenses` — sin violaciones en HEAD actual

### 4.2 Dependencias Python (PyPI / uv)

- **Total de paquetes:** ~203 (directas + transitivas, `uv pip list --format=json`)
- **Licencias predominantes:** MIT, Apache-2.0, BSD-3-Clause
- **Licencias copyleft detectadas:** Ninguna
- **Paquetes de testing excluibles del perímetro comercial:** `pytest`, `hypothesis`, `mypy`, `ruff`

### 4.3 Dependencias Lean 4 y Censo Formal de Anillo-0

- **Toolchain:** `leanprover/lean4:v4.34.0-rc2` (Apache-2.0)
- **Módulos formales propios (`proof/lean/*.lean`):** **26 archivos propietarios** (**22 módulos con declaraciones de teoremas + 4 módulos auxiliares sin teoremas**; ~20.133 LOC; 36 archivos `.lean` considerando las suites auxiliares del repositorio con ~21.596 LOC) — autoría íntegra en sala limpia de Borja Fernández Angulo.
- **Teoremas y construcciones verificadas (código propio):** **144 declaraciones de teoremas** (`#001–#144`: **105 universales/estructurales y testigos [72,9 %]** + **39 comprobaciones de instancias cerradas [27,1 %: 37 positivas + 2 fixtures negativos]**) más **228 definiciones e inductivos** (**205 `def` + 23 `inductive`**, enumerados 1:1 en `docs/06_theory/evidence/lean-census-372-v511.json`), sumando **372 construcciones formales de Anillo-0** (más **34 `structure` + 13 `abbrev` = 275 construcciones no-teorema / 419 declaraciones totales de nivel superior**). El alcance exacto por módulo y teorema se documenta en `docs/06_theory/AUDIT_LEAN_SCOPE_2026.md`.
- **Dependencias del árbol Lake (`.lake/packages/`):** **611 archivos `.lean`** (~162.867 LOC) correspondientes a librerías certificadas del ecosistema Lean 4 (`batteries` [305], `aesop` [254], `proofwidgets` [37], `alloy` [15]) bajo licencia Apache-2.0.
- **Total del árbol de compilación formal:** **637 archivos `.lean`** (~183.000 LOC totales entre núcleo propio y librerías base de verificación).

---

## 5. Declaración de Ausencia de Cargas Legales

El autor declara que, a la fecha de compilación de este documento:

1. **No existe ninguna reclamación pendiente** de propiedad intelectual por parte de terceros sobre el código fuente de `BABYLON-60`.
2. **No existen acuerdos de confidencialidad** con empleadores o clientes anteriores que afecten al contenido de este repositorio.
3. **No existen licencias de patente** otorgadas a terceros sobre los algoritmos implementados (Seqlock SPMC, LARSA BFT, protocolo AX-0, KUDURRU-64).
4. **La licencia soberana** (`LICENSE` en la raíz del repositorio) es la única licencia aplicable al código propietario. Las dependencias de terceros conservan sus licencias originales tal como se indica en el SBOM.

---

## 6. Registro de Atestación Criptográfica

| Artefacto | SHA-256 | Fecha de Sellado |
|:---|:---|:---|
| `dist/babylon60-v5.1.0-terminal-mcp.tar.gz` | `d57a4275b0a45130c97b16cba9a9fb189a7d41192f5b63a7d60d7596ed927186` | 2026-11-07 |
| `RELEASE_MANIFEST.json` (v5.1.0) | _(actualizar tras AX-41)_ | _(pendiente resello)_ |
| `CLAIMS.toml` HEAD `e6491252` | _(generado por `compile_claims_manifest.py --fresh`)_ | 2026-11-07 |
| `src/seqlock.rs` (con cabecera SPDX) | _(AX-40, commit `e6491252`)_ | 2026-11-07 |
| `src/larsa_bft.rs` (con cabecera SPDX) | _(AX-40, commit `e6491252`)_ | 2026-11-07 |

> Los archivos `.ots` vinculados en `contracts/babylon60.ots` proporcionan atestación de existencia en la blockchain de Bitcoin independiente de GitHub. Para verificar: `ots verify contracts/babylon60.ots`.

---

## 7. Contacto Institucional para Due Diligence

**Canal único de contacto técnico M&A / Licenciamiento:**

```
access@babylon60.com
```

> No utilizar direcciones personales del autor. Ver Invariante de Desacople Inbound (Sovereign Operator Stance).

---

*El registro de firma `[AX-41]` corresponde a la revisión original del 7 de noviembre de 2026 en `borjamoskv/BABYLON-60-VAULT`.*

---
**Borja Fernández Angulo** · *Investigador en Sistemas Complejos*  
`borjamoskv` · BABYLON-60 Sovereign Core · 2026
