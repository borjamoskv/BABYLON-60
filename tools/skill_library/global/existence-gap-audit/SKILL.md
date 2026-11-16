---
name: existence-gap-audit
display_name: Auditoría de Huecos de Existencia & Supply-Chain Slop
description: 'Detecta imports y referencias fantasma en repositorios. Dispara con "auditoría", "audit", "revisa este repo", "código alucinado", "dependencias fantasma", "slopsquatting", "vibe coding", "supply chain", "¿esto se ejecuta?", "imports rotos", "auditar workflows".'

role: auditor
allowed_roles:
- auditor
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: ejecutor
    downstream: operador
---

# Auditoría de huecos de existencia

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `auditor` (Auditor (Verificación Independiente, Linters de Silicio & Fail-Closed Gate))
> - **Modo de Acceso a Worktree:** `audit-only` (audit-only (Lectura forense de diffs, linters, tests de estrés y cálculo de exergía; cero mutación de código))
> - **Fase Causal:** `verification`
> - **Contrato Handoff:** Recibe de `ejecutor` $\to$ Despacha a `operador`

## Por qué esta skill existe

Las herramientas estáticas (`semgrep`, `gitleaks`, `bandit`, `codeql`) buscan **patrones en texto**. Encuentran el modo de fallo humano: código semánticamente real con un error lógico o un descuido de seguridad.

No encuentran el otro modo de fallo, el del código generado sin ejecutar nunca: **plausibilidad sintáctica perfecta sin anclaje ontológico**. Un `from cortex_mamba_block import MambaBlock` es sintácticamente impecable, pasa el linter, pasa el type-checker con `ignore_missing_imports`, y apunta a nada. No es un patrón. Es un **hueco de existencia**, y sólo se detecta comprobando el grafo de dependencias contra la realidad empírica: el filesystem y el registro de paquetes.

Consecuencia práctica: un repo puede tener 137k líneas, 0 errores de sintaxis, CI en verde y subsistemas enteros que jamás se han cargado.

## Procedimiento

Ejecuta los escáneres primero, interpreta después. No inspecciones ficheros a mano antes de tener el mapa.

```bash
python3 scripts/existence_gap.py     <ruta_repo> --json imports.json
python3 scripts/ci_supply_chain.py   <ruta_repo> --json ci.json
```

Sin red, añade `--offline`: pierdes la clasificación de registro, conservas la de fantasma local. Con `--no-reach` desactivas el grafo de alcanzabilidad y la severidad vuelve al heurístico de ubicación — útil si el proyecto arranca de una forma que el detector de entrypoints no reconoce. Para el escáner de CI, exporta `GITHUB_TOKEN` — sin él la API limita a 60 consultas/hora y los namespaces quedan sin verificar.

Verifica la suite antes de fiarte de un cero: `python3 tests/test_regression.py`. Un escáner silencioso y un escáner roto son indistinguibles desde fuera.

## Los seis huecos del grafo de imports

El escáner cruza tres oráculos independientes: **filesystem**, **manifiesto declarado** (`pyproject.toml` / `requirements*.txt` / `package.json`) y **registro** (PyPI / npm).

**FANTASMA** — no resuelve en el filesystem, no existe en el registro. El código que lo importa nunca se ha ejecutado.

**FANTASMA_INTERNO** — el paquete raíz existe, la ruta punteada completa no. `from babylon60.swarm.legion import X` pasa cualquier filtro de primer nivel porque `babylon60` sí existe.

**SIMBOLO_FANTASMA** — el módulo existe y resuelve, pero no define ni reexporta el nombre importado. Falla con `ImportError`, no con `ModuleNotFoundError`, y es la firma más común del subsistema alucinado: el modelo acierta el módulo e inventa la clase. Sólo se reporta cuando el módulo destino es enumerable — si usa `import *` o define `__getattr__`, cualquier nombre puede existir en runtime y afirmar lo contrario sería conjetura.

**TRAMPA_SLOPSQUAT** — no resuelve en el filesystem, no está declarado, **pero existe en el registro con ese nombre exacto**. La clase peligrosa: quien encuentre el `ImportError` e intente arreglarlo ejecutará `pip install <nombre>` y traerá código de un tercero al proceso. Es dependency confusion pasiva — nadie ataca, la víctima se autoinfecta al depurar.

**SLOPSQUAT_RECIENTE** — existe en el registro, pero su huella temporal no es la de una dependencia establecida: registrado hace poco, una o dos releases, sin repositorio declarado. Un nombre inventado por un modelo y registrado poco después es el ciclo completo del slopsquat. Sin mirar la fecha, "existe" y "es legítimo" colapsan en la misma línea y se pierde el único caso que importa.

**NO_DECLARADO** — existe en el registro y se usa, falta en el manifiesto. Instalación limpia rota.

**FANTASMA_INTERNO también aplica a JS**: una ruta relativa o un alias de `tsconfig` que no resuelve a ningún fichero del árbol. Delegar los imports relativos al bundler es la misma excusa que descartar `node.level > 0` en Python, y oculta el mismo fallo.

**LOCAL_DESALINEADO** — el módulo existe en el repo pero no en la ruta desde la que se importa. Funciona en la máquina del autor, falla en cualquier otra. **No** se reporta cuando vive bajo una raíz de paquete declarada (`src/`, `tool.setuptools…where`, hatch, poetry): ahí entra en `sys.path` por construcción, y marcarlo produce un falso positivo de severidad alta por proyecto entero.

## Tres marcas por punto de import

Cada sitio se anota, y las marcas cambian la lectura:

**`guarded`** — envuelto en `try/except ImportError`. Si *todos* los puntos de import lo están, el módulo degrada limpiamente: es una trampa latente, no una vulnerabilidad activa, y baja a `bajo`. La excepción del control ausente no se degrada nunca.

**`lazy`** — dentro de una función. No revienta al cargar el módulo; falla la primera vez que alguien llama.

**`dinamico`** — capturado en `importlib.import_module("x")` o `__import__("x")` con literal. Un `ast.walk` que sólo mira nodos `Import` no ve nada aquí, y los cargadores de plugins escritos por un modelo enumeran módulos por cadena: el fichero parece limpio y el subsistema entero queda fuera del informe.

## Alcanzabilidad medida, no inferida

El escáner construye el grafo de imports internos y hace BFS desde entrypoints reales: `[project.scripts]`, `[project.entry-points]`, ficheros con `if __name__ == "__main__"` y los nombres convencionales (`__main__.py`, `wsgi.py`, `manage.py`…). Un fichero que cuelga de ese grafo está vivo; uno que no, es deuda.

Esto sustituye al indicio de ubicación en `rate()`, que es lo que la matriz de alcanzabilidad venía pidiendo. Tres salvaguardas, porque una medida que degrada severidades es peligrosa en la dirección contraria a un falso positivo:

- **Sin entrypoint reconocible, la alcanzabilidad es `no medida`, no `no alcanzable`.** Tratarlas igual convertiría cualquier librería en un informe entero de severidad informativa.
- **Si menos de la mitad del árbol cuelga de un entrypoint, el informe avisa.** O el código está muerto, o falta un entrypoint.
- **Todo hallazgo degradado por alcanzabilidad se lista con su severidad original.** Un escáner que baja severidades en silencio produce exactamente la señal verde engañosa que existe para evitar.

Sigue siendo cierto que un hallazgo con la traza de `ModuleNotFoundError` reproducida es irrefutable y uno sin ella es una conjetura. El grafo prioriza la lectura; no la sustituye.

## La superficie de CI

El escáner de imports mira el código que corre en la máquina del desarrollador. `ci_supply_chain.py` mira el que corre en el runner, con el token del repositorio en el entorno. Es la superficie de mayor privilegio y la que menos se audita, y por eso su typosquat va **por encima** del de paquetes en cualquier orden de severidad razonable: un `pip install` malicioso compromete un portátil, una `uses:` maliciosa compromete el repositorio y todo lo que el token alcance, en cada push, sin interacción.

**ACCION_FANTASMA** — el namespace `org/repo` no existe en GitHub. Cualquiera puede registrarlo y su código se ejecutará en el runner. Es el hallazgo más grave que produce esta skill.

**ACCION_TYPOSQUAT** — a distancia de edición 1 de una acción conocida (`nvida` por `nvidia`, `actionz` por `actions`). Si el namespace vecino ya existe, alguien lo registró antes que tú.

**INYECCION_EXPRESION** — `${{ github.event.*.title }}`, `github.head_ref` y compañía interpolados dentro de un `run:`. La sustitución ocurre **antes** de invocar el shell: comillas y escapes no protegen. Se arregla pasando el valor por `env:` y referenciando `"$VAR"`.

**PRIVILEGIO_PR_TARGET** — `pull_request_target` con checkout del head del PR. Ejecuta código del proponente con el token del repositorio base y acceso a secretos.

**PIN_MUTABLE** / **PERMISO_EXCESIVO** — tags móviles y scopes de escritura. Contexto, no alarma: sólo importan si algún paso del job ejecuta código no confiable.

## La excepción del control ausente

La mitigación por árbol legacy —bajar a informativo lo que vive donde el propio proyecto declara deuda— tiene una excepción que **no** admite discusión: cuando el módulo que falta *es* un control de seguridad.

Un `capability_guard` que el código importa, que la documentación anuncia y que no existe en ninguna parte no es deuda declarada. Es un control ausente, y el sistema se comporta como si lo tuviera. Es el hallazgo más grave que este escáner puede producir, y una regla de ubicación ingenua lo silencia precisamente porque los controles suelen vivir en los árboles más viejos.

El escáner aplica `SECURITY_CONTROL` al **nombre del módulo importado**, no a la ruta del fichero importador — el error natural es al revés, y hace que el caso se escape dos veces.

## Dos ejes, no uno: la matriz de alcanzabilidad

«Alcanzable» colapsa dos preguntas que hay que mantener separadas, y confundirlas hace fallar el criterio en las dos direcciones.

El primer eje es **si llega input controlado por un tercero**. Determina si el hallazgo es una vulnerabilidad o una funcionalidad rota. El segundo es **qué hace el código cuando llega**. Determina la severidad.

Un endpoint montado que cualquiera puede invocar pero que siempre lanza `ImportError` puntúa alto en el primer eje y nulo en el segundo: es funcionalidad muerta y un problema de honestidad de la documentación, no una vulnerabilidad. Un ejecutor enterrado en un árbol marcado como legacy, pero alcanzable desde un ingestor que acepta contenido externo, puntúa alto en ambos: es ejecución remota. Un criterio basado en dónde vive el fichero acierta al revés en los dos casos.

La ubicación en el árbol es un indicio débil del primer eje y no dice nada del segundo. Úsala para priorizar la lectura, nunca para asignar severidad.

## Cicatrices del resolutor

Todas se cometieron en producción. Todas producían **silencio**, que es el modo de fallo caro: un escáner que no reporta y un repo limpio son indistinguibles desde fuera.

**La raíz del paquete no es la raíz del repo.** En un monorepo el paquete cuelga de un subdirectorio y es *ese* directorio el que entra en `sys.path`. Resolver desde la raíz marcó como ausentes 37 módulos que existían, cuatro de ellos controles de seguridad; la regla del control ausente, que es correcta, amplificó el fallo convirtiendo falsos positivos en hallazgos de severidad alta. El escáner resuelve contra un índice de todo el árbol y acepta cualquier sufijo coincidente.

**El gate tiene que usar el mismo criterio que el resolutor.** El detector de rutas punteadas filtraba por «módulos en la raíz del repo» mientras el resolutor aceptaba cualquier raíz. En src-layout —el layout por defecto de setuptools, hatch y poetry— el paquete no está en la raíz, así que el detector no se ejecutaba nunca. Coherencia entre gate y resolutor, o el detector es decorativo.

**`SKIP_DIRS` responde a "no escanear", no a "no existe".** Un directorio `build/` dentro de un paquete es un módulo legítimo (`conan.tools.build`); podarlo del índice de rutas convierte imports válidos en fantasmas. El índice poda sólo lo que no es un paquete Python. Este fallo producía tres falsos positivos en una librería madura y arbitraria.

**Un fallback permisivo reintroduce el punto ciego que la herramienta existe para cerrar.** El resolutor aceptaba `a.b` si existía `a`, para no romper el caso `from a.b import c`. Eso *es* el punto ciego de la ruta punteada. La solución no es relajar el resolutor sino verificar el símbolo por separado.

**Los builtins de Node y los alias de `tsconfig` no son paquetes.** `fs`, `path` y `events` existen además como paquetes publicados en npm, así que consultarlos produce `NO_DECLARADO` en cada proyecto. Peor: `@/components/Boton` se lee como paquete con scope `@/components`, npm devuelve 404 y todo proyecto Next.js o Vite con alias genera un informe lleno de fantasmas inexistentes. El falso positivo masivo no es ruido: es lo que hace que nadie vuelva a abrir el informe.

**Una medida que degrada en silencio es peor que no medir.** Al meter alcanzabilidad, los fantasmas de un subárbol sin entrypoint bajaron de `medio` a `informativo` sin dejar rastro. Correcto por doctrina, indistinguible de un repo limpio desde fuera. Por eso el informe lista cada degradación con su severidad original y avisa cuando la cobertura del grafo es baja.

Contraste que sirve de regresión, medido sobre `conan` 2.27.1 (336 ficheros, layout en raíz): 10 fantasmas internos antes, 9 después — pero no son los mismos. Desaparecen 3 falsos positivos (`conan.tools.build.*`, podados por `SKIP_DIRS`) y aparecen 2 verdaderos que el fallback permisivo ocultaba (`conans.server`). Si tu cambio al resolutor mueve estos números, mide antes de darlo por bueno. La alcanzabilidad, añadida después, no degradó ni un solo hallazgo en ese repo: 223/328 ficheros alcanzables, 0 degradaciones. Una medida nueva que cambia muchas severidades de golpe está midiendo otra cosa.

## Ponderación por alcanzabilidad

Un fantasma en `scratch/` es deuda. Un fantasma en un handler HTTP montado es un fallo en producción. **Siempre determina el alcance antes de asignar severidad**, o tus hallazgos serán refutados con razón.

El escáner ya te dice cuáles cuelgan de un entrypoint. Para cada hueco en una ruta viva, confirma a mano:

1. Localiza el punto de import con `grep -n`.
2. Traza hacia arriba: ¿quién llama a esa función? ¿está el router montado (`include_router`, `app.use`, registro de blueprint)? ¿lo invoca el frontend?
3. Reproduce el fallo. Replica cualquier manipulación de `sys.path` que haga el código y ejecuta la secuencia de imports:

```python
import sys; sys.path.insert(0, "<el_parent_dir_que_inyecta_el_codigo>")
for m in ["mod_a", "mod_b"]:
    try: __import__(m); print("OK", m)
    except Exception as e: print("FALLA", m, "->", type(e).__name__, e)
```

Un hallazgo con la traza de `ModuleNotFoundError` reproducida es irrefutable. Uno sin ella es una conjetura.

## Reglas de reporte

Cita siempre `fichero:línea` y pega el import verbatim. Distingue lo observado (ejecutaste el import y falló) de lo inferido (leíste el código y deduces que fallaría). Si el módulo es de un submódulo git no inicializado o de un monorepo privado, **no es un fantasma** — es una dependencia externa no empaquetada; dilo así.

Nunca conviertas un indeterminado en un negativo. Un 403 por rate-limit de la API de GitHub y un 404 de namespace libre son respuestas distintas: la clase `NO_VERIFICADO` existe para eso. Reportar «namespace libre para squatting» porque el registro no contestó es el error que quema la credibilidad del informe entero.

Nunca declares un paquete inexistente por el nombre de import. `yaml` es `PyYAML`, `cv2` es `opencv-python`, `fitz` es `PyMuPDF`; un 404 sobre el nombre de import es un falso P0, y el falso P0 es el que cuesta la auditoría. El escáner mapea import→distribución antes de consultar, pero si añades una comprobación manual, mapea tú también.

No infles severidades: un import fantasma envuelto en `try/except ImportError` que degrada limpiamente es una trampa latente, no una vulnerabilidad activa. Nombrar bien la diferencia es lo que hace que el informe sobreviva a una refutación.

Y reporta siempre lo que **no** miraste: ficheros que no parsean, namespaces sin verificar, ecosistemas sin escanear. Un fichero con error de sintaxis no es un fichero limpio — el escáner rescata sus imports por regex precisamente porque el silencio se lee como cobertura.

## Lectura del resultado agregado

La proporción entre clases diagnostica el origen del código. Muchos NO_DECLARADO con cero fantasmas es un proyecto real con higiene de packaging floja. Fantasmas agrupados en un subsistema coherente, con nombres consistentes entre sí y docstrings elaborados, es un subsistema alucinado en bloque: se generó como una pieza y nunca se ejecutó. Ese patrón —nombres mutuamente consistentes que no existen— es la firma más limpia del modo de fallo generativo.

## Matriz de 4 Cohortes para Auditoría Integral de Dependencias y Mapa On-Wire (`itera swarm`)

Cuando se audite un monorepo híbrido (Rust + Python + CI), despliega 4 cohortes ortogonales etiquetando cada hallazgo estrictamente como **`OBS`** (salida verificada de comando) o **`INF`** (inferido de lectura de código):

1. **Cohorte 1 — Grafo Rust y MSRV Real:**
   - Calcular el MSRV real del grafo (`cargo metadata --format-version 1 | jq '[.packages[].rust_version] | max'`) frente al declarado en `Cargo.toml`.
   - Detectar crates duplicados para la misma primitiva (ej. `ring` vs `dalek`, múltiples hashes `blake3`/`sha2`/`sha3`, primitiva `Seqlock` duplicada).
   - Detectar manifiestos huérfanos fuera del `[workspace]` y `Cargo.lock` anidados.
2. **Cohorte 2 — Grafo Python, Suelos Vulnerables y Side-Effects de Importación:**
   - Auditar side-effects peligrosos en tiempo de importación dentro de paquetes distribuibles (ej. monkey-patching de `torch.load(..., weights_only=False)` o descargas de red al importar).
   - Auditar vulnerabilidades en las **versiones mínimas declaradas** (suelos `>=`), no solo en el lockfile resuelto.
   - Cruzar `ignore_missing_imports = true` con imports rotos o dependencias fantasma.
3. **Cohorte 3 — Mapa On-Wire y Fronteras de Autoridad:**
   - Inventariar cada frontera IPC/Red (`AF_UNIX`, shared memory, loopback HTTP/gRPC, gates biométricos): formato de framing, endianness, byte de versión, validación criptográfica (`COSE_Sign1` vs JSON sin firma), comprobación de credenciales de par (`getpeereid`) y uso de reloj del emisor vs reloj del verificador (`O13`).
   - Verificar que los tipos ontológicos (`ReceiptStage`, `Decision`, `Inference`) tengan productores y consumidores reales en runtime y no solo en tests.
4. **Cohorte 4 — Higiene de Supply Chain, Licencias y CI:**
   - Verificar colisiones entre el archivo `LICENSE` raíz y los metadatos `license` de cada `Cargo.toml` / `pyproject.toml`, bloqueando workflows de publicación (`crates-publish.yml`) si exponen código propietario bajo licencias permisivas (`Apache-2.0 OR MIT`).
   - Verificar aplicación de `--locked` en CI, ausencia de `--allow-dirty`, presencia de `.dockerignore` (evitando inyectar `.git` multimillonario en el contexto Docker) y fijación de digests/checksums en `Dockerfile` e `install.sh`.
