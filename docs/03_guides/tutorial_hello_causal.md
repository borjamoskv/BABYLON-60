---
title: Primer programa B60 local
status: Educational example
version: 5.0.0
---

# Tutorial: primer programa B60 local

Este ejercicio ejecuta una suma y comprueba el artefacto que escribe el
intérprete Rust de [src/babylon60.rs](../../src/babylon60.rs). El target Cargo
se llama `babylon60`; es distinto del CLI Python instalado con el mismo nombre
y del target `babylon60_kernel`. Los comandos siguientes seleccionan el binario
Rust mediante su ruta, sin depender del `PATH`.

## 1. Preparar el intérprete

Desde la raíz del checkout, con Rust 1.89 o posterior y Python 3:

```sh
cargo build --locked -p babylon60_root --bin babylon60
mkdir -p target/docs-hello
```

La primera compilación necesita acceso a las dependencias fijadas en
`Cargo.lock`. Con la caché preparada, se admite añadir `--offline`.
Este target recibe una ruta `.b60`; no implementa una opción `--help`.

## 2. Escribir y ejecutar un programa acotado

Guarda el siguiente texto en `target/docs-hello/hello_causal.b60`:

```text
DUB
ALLOC I64 R0
NIG R0 [ Y ]
DAH R0 [ YY ]
SAR R0
EXECUTE "HELLO_CAUSAL"
HALT
```

`[ Y ]` representa 1 y `[ YY ]` representa 2. `DAH` suma al registro; `SAR`
registra su valor y `EXECUTE` añade una etiqueta al grafo de este intérprete.
Este `EXECUTE` del DSL no despacha una acción externa.

```sh
(cd target/docs-hello && ../debug/babylon60 hello_causal.b60)
```

La ejecución termina y escribe estos tres archivos bajo
`target/docs-hello/artifact_bundle_v3/`:

- `manifest.json`: contiene `global_hash`.
- `graph.canonical`: serializa los eventos del ejercicio.
- `proof.ir`: contiene obligaciones intermedias; su exportación no ejecuta Lean.

El manifiesto enumera además componentes que este emisor no escribe. Este
ejercicio comprueba sólo los tres archivos anteriores.

## 3. Comprobar el resultado y el digest

Desde la raíz del checkout:

```sh
python3 - <<'PY'
from pathlib import Path
import hashlib
import json

bundle = Path("target/docs-hello/artifact_bundle_v3")
graph = (bundle / "graph.canonical").read_bytes()
manifest = json.loads((bundle / "manifest.json").read_text())
events = graph.decode("utf-8").splitlines()
assert any("|R0=3|" in event for event in events)
assert any("|HELLO_CAUSAL|" in event for event in events)
assert hashlib.sha256(graph).hexdigest() == manifest["global_hash"]
assert (bundle / "proof.ir").is_file()
print("PASS: suma 1 + 2 y digest del grafo exportado")
PY
```

Estos controles detectan un resultado distinto de 3 o una discrepancia entre el
grafo y su manifiesto. No demuestran autorización de efectos, identidad del
operador, supervisión humana ni cumplimiento jurídico.

## Límites del ejemplo

El `main` de este intérprete introduce dos cadenas de texto como proposiciones
simuladas en una cola SPSC. Los mensajes que las presentan como verificadas no
son resultados de Lean. El grafo utiliza marcadores de firma del intérprete,
sin atestación de Secure Enclave ni garantía de almacenamiento WORM. Un mensaje
de finalización, un digest consistente o la ausencia de `CRITICAL HALT` no
certifican todas las invariantes del sistema.

Los programas de [tools/examples](../../tools/examples/) son material de
experimentación. Este tutorial no atribuye a sus instrucciones `F60`, `AWAIT`
o `AFTER` exactitud general, ausencia de carreras ni sincronización con tiempo
físico. Consulte la [especificación](../SPECIFICATION.md) y el
[modelo de seguridad](../01_spec/spec_security_model.md) para distinguir el
modelo, la implementación y las propiedades aún pendientes.
