---
title: Modelo de seguridad del ledger Python BABYLON-60
status: Implementation-Reference
version: 5.0.0
---

# Modelo de seguridad del ledger Python

Este documento delimita `CortexPersistLedger` en la base pública `00f20e7`.
Su cadena usa **SHA3-256 sobre JSON canónico UTF-8**, según el
[perfil criptográfico](spec_cryptographic_profile.md). El ledger Rust SHA-256 y el
árbol BLAKE3 son implementaciones distintas.

Fuentes: [persistencia y verificación](../../01_KISH_ENGINE/babylon60/bft/cortex_persist_ledger.py)
y [funciones criptográficas](../../01_KISH_ENGINE/babylon60/bft/cortex_crypto_kernel.py).
Esta descripción del código no certifica una instalación, un hardware ni el
estado actual de una base de datos.

## 1. Propiedades y condiciones

| Propiedad | Mecanismo observado en el código | Alcance |
| --- | --- | --- |
| Comprobación de cadena | `verify_integrity` recalcula SHA3-256 y comprueba secuencia, hash previo y reloj de Lamport | Detecta discrepancias respecto a las reglas de la cadena almacenada; una historia reescrita necesita una referencia externa confiable para ser contrastada |
| Atribución declarada | `cortex_taint`, `agent_id` y `domain` dentro del sobre hasheado | Vincula esos valores al contenido; no autentica a quien los declara |
| Serialización de escrituras | Transacciones SQLite con `BEGIN IMMEDIATE` | Acota la actualización de esta base local; no demuestra consenso distribuido |
| Idempotencia | Identificadores de evento y restricciones `UNIQUE` | Rechaza identificadores duplicados según el contrato; no demuestra equivalencia semántica de payloads distintos |
| Restricción de modificaciones | Triggers que rechazan `UPDATE` y `DELETE` de entradas | Protege operaciones SQL mientras el esquema permanece intacto; el propietario puede eliminar los triggers |
| Persistencia local | SQLite WAL y `PRAGMA synchronous = FULL` en las conexiones | Solicita sincronización; la durabilidad ante un fallo físico depende también del almacenamiento y requiere una prueba específica |

Una cadena consistente no prueba que se hayan registrado todos los efectos del
agente. El hash no es una firma: quien tiene escritura y conoce el formato puede
recalcularlo. Contrastar una historia con un compromiso previo exige una raíz o
recibo conservado fuera del dominio modificable por el atacante, con clave, fecha
y confianza verificadas cuando se aleguen esas propiedades.

## 2. Fronteras que requieren controles adicionales

| Propiedad | Control que no aporta la cadena por sí sola |
| --- | --- |
| Corrección del contenido | Validación de datos, semántica y origen de las observaciones |
| Autorización de efectos | Política y executor que medien todas las rutas al recurso protegido |
| Identidad y no repudio | Firma válida y atribución confiable de su clave; `agent_id` no es una credencial |
| Almacenamiento WORM físico | Medio o servicio con retención y resistencia a modificaciones fuera del proceso |
| Tiempo externo acreditado | Testigo independiente; un timestamp declarado de evento o commit no es por sí solo una autoridad temporal |
| Tolerancia bizantina distribuida | Protocolo, identidad de validadores, configuración y pruebas de red del despliegue |
| Cumplimiento regulatorio | Evaluación del sistema y procedimiento aplicable; registrar hashes no sustituye gestión de riesgos, gobernanza de datos ni supervisión humana |

Los recibos Ed25519 o P-256 y la mediación del kernel tienen sus propios contratos.
Una firma válida no acredita automáticamente origen hardware ni correspondencia
entre efecto y autorización. Véase el
[perfil COSE de autorización](../security/cose-authorization-profile.md).

## 3. Amenazas y límites

### Alteraciones comprobables con la cadena y su contexto

- Una modificación de campos conservando el hash almacenado se detecta al
  recalcular el sobre, salvo compromiso de la primitiva criptográfica.
- Una secuencia no contigua o un encadenado incoherente se rechaza en
  `verify_integrity`.
- Las colisiones de identificadores y modificaciones SQL están sujetas a las
  restricciones y triggers del esquema instalado.
- La recuperación transaccional corresponde a SQLite. Una comprobación posterior
  de integridad no sustituye un ensayo de pérdida de energía del almacenamiento.

### Amenazas fuera de esta frontera

- Un proceso con permisos sobre el archivo puede borrarlo, sustituirlo o alterar
  esquema e historia. Sin compromiso externo, una historia recalculada o una cadena
  vacía no autentica la historia anterior.
- Las credenciales, sistema operativo, bibliotecas y proceso escritor pertenecen
  al modelo de confianza del despliegue.
- La protección frente a rutas alternativas requiere aislamiento y mediación de
  recursos; no se deduce de usar SQLite, Rust o un árbol Merkle.
- La separación entre inquilinos debe imponerse con rutas, permisos e identidades.
  El constructor recibe una ruta; no establece aislamiento multiinquilino.

## 4. Comprobar una copia del ledger

La API existente devuelve un booleano, no el objeto con `broken_at` que describía
una versión anterior de esta guía. Con el paquete instalado, este ejemplo trabaja
sobre una copia elegida por el operador:

```python
from pathlib import Path
from babylon60.bft.cortex_persist_ledger import CortexPersistLedger

copy_path = Path("copia/master_ledger.db")
if not copy_path.is_file():
    raise FileNotFoundError(copy_path)
ledger = CortexPersistLedger(copy_path)
print({"chain_consistent": ledger.verify_integrity()})
```

El constructor inicializa el esquema y configura conexiones; el ejemplo no es una
apertura forense de solo lectura. Preparar una copia consistente de SQLite mediante
el procedimiento de backup pertinente, incluyendo su estado WAL; no copiar solo
el `.db` de un escritor activo. `True` también es posible para una cadena vacía:
revisar por separado el número de eventos, el intervalo y la raíz externa esperados
antes de aceptar una historia.

Una campaña concreta registra revisión, configuración y artefactos. Los resultados
históricos de [la auditoría del kernel](../security/kernel-audit-2026-10-15.md)
describen sus propios casos y límites; no certifican esta copia ni una revisión
posterior.
