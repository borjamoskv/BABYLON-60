---
title: Perfiles criptográficos por implementación BABYLON-60
status: Implementation-Reference
version: 5.0.0
---

# Perfiles criptográficos por implementación

Esta referencia describe los bytes de las implementaciones presentes en la base
pública `00f20e7`. El ledger Python, el ledger Rust y el árbol BLAKE3 son formatos
distintos. Un verificador debe elegir el perfil del productor; cambiar de algoritmo
o serialización cambia el digest. Esta descripción no certifica una ejecución ni
la conformidad de todos los subsistemas con un único formato on-wire.

## 1. Matriz de perfiles

| Productor y función | Digest o firma | Bytes de entrada y formato | Fuente |
| --- | --- | --- | --- |
| `CortexPersistLedger` Python: `compute_cortex_hash` | SHA3-256, hexadecimal de 64 caracteres | Sobre JSON canónico UTF-8 de la sección 2 | [Kernel criptográfico Python](../../01_KISH_ENGINE/babylon60/bft/cortex_crypto_kernel.py) y [ledger](../../01_KISH_ENGINE/babylon60/bft/cortex_persist_ledger.py) |
| Merkle del ledger Python: `build_merkle_tree` | SHA3-256 | Hashes de entrada binarios, prefijos por nivel y cardinalidad de la sección 3 | [Kernel criptográfico Python](../../01_KISH_ENGINE/babylon60/bft/cortex_crypto_kernel.py) |
| `WormLedger` Rust: `append` | SHA-256 | `prev_hash || payload || signature`; firma comprobada con el `Signer` suministrado | [Ledger Rust](../../src/worm.rs) |
| Merkle BLAKE3: `build_root` en Rust y Python | BLAKE3, raíz `b3:<hex>` | Dominios `B60-LEAF-v1\0`, `B60-NODE-v1\0`, `B60-ROOT-v1\0`; cardinalidad `u64` little-endian | [Rust](../../crates/babylon-attest/src/merkle_b3.rs) y [Python](../../01_KISH_ENGINE/babylon60/attestation/merkle_b3.py) |
| Recibos Rust: `emit_worm_anchor_receipt`, `emit_halt_receipt_with_timestamp` | Algoritmo del `Signer`; implementaciones Ed25519 y P-256 | Payload CBOR dentro de COSE_Sign1 | [Recibos y firmantes](../../src/receipt.rs) |

Un firmante P-256 o un recibo válido no demuestra por sí solo que la clave proceda
del Secure Enclave ni que se haya mostrado Touch ID. `WormLedger` conserva entradas
en memoria y ofrece persistencia opcional; su nombre no acredita almacenamiento
físicamente inmutable.

## 2. Sobre del ledger Python

`compute_cortex_hash` construye un objeto con estos campos:

```text
seq, event_id, event_type, payload_json, cortex_taint, agent_id,
domain, lamport_t, prev_hash, timestamp
```

`payload_json` es una **cadena** que contiene el JSON del payload, no un objeto
anidado. `prev_hash` es la representación hexadecimal que conserva la entrada.
`timestamp` también forma parte del hash: reproducir el digest exige conservar su
valor exacto, además del reloj lógico y los demás campos. El timestamp declarado
no es por sí solo un sello de tiempo externo.

`_canonical_json` aplica exactamente:

```python
json.dumps(envelope, sort_keys=True, separators=(",", ":"),
           ensure_ascii=False, allow_nan=False).encode("utf-8")
```

`compute_envelope_hash` calcula SHA3-256 de esos bytes. Este perfil **no usa CBOR**
para la cadena del ledger Python. No añade normalización Unicode ni reordena el
contenido de una cadena `payload_json` recibida: conservar la representación del
productor es necesario para reproducir el digest.

### Vector mínimo de serialización y hash

El sobre genérico `{"b": "á", "a": 1}` produce:

```text
JSON:   {"a":1,"b":"á"}
Bytes:  7b2261223a312c2262223a22c3a1227d
SHA3:   932a26668b27658b9d8eb455cfc878a7fa452def06c026f0735bb350330b5d2b
```

Desde la raíz, esta comprobación ejecuta solo funciones puras; no abre un ledger
ni genera certificados:

```sh
python3 - <<'PY'
import runpy

kernel = runpy.run_path("01_KISH_ENGINE/babylon60/bft/cortex_crypto_kernel.py")
envelope = {"b": "á", "a": 1}
expected = "932a26668b27658b9d8eb455cfc878a7fa452def06c026f0735bb350330b5d2b"
assert kernel["_canonical_json"](envelope).encode("utf-8").hex() == "7b2261223a312c2262223a22c3a1227d"
assert kernel["compute_envelope_hash"](envelope) == expected
print("PASS: vector JSON UTF-8 / SHA3-256")
PY
```

El vector comprueba el sobre genérico. Una entrada completa aporta los once campos
anteriores; el vector no acredita durabilidad ni autorización.

## 3. Merkle del ledger Python

`build_merkle_tree` recibe en orden los hashes SHA3-256 de las entradas y los
convierte de hexadecimal a bytes. No añade un hash de hoja individual. Cada par
se combina con `SHA3-256(tag || left || right)`:

- El primer nivel de combinación usa `tag = 0x00`.
- Los niveles siguientes usan `tag = 0x01`.
- Un nivel impar duplica el último nodo para completar el par.
- La raíz final es `SHA3-256(0x02 || top || count_u64_LE)`.
- La lista vacía devuelve 64 caracteres `0`; una sola entrada también pasa por
  el sellado de raíz con cardinalidad.

El árbol BLAKE3 de la matriz usa otros dominios y un hash explícito de hoja; sus
pruebas no son intercambiables. La raíz compromete la secuencia suministrada,
no la veracidad de los eventos ni la existencia de entradas omitidas.

## 4. Selección y cambios de perfil

El formato del artefacto debe identificar productor, versión y perfil. Un digest
hexadecimal sin contexto no distingue SHA-256 de SHA3-256. No reinterpretar datos
existentes bajo otro algoritmo: una migración conserva el perfil original y
publica sus reglas y vectores nuevos.

El [modelo de seguridad](spec_security_model.md) delimita integridad, confianza en
claves, autorización, aislamiento y referencias externas.
