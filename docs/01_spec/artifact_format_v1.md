---
title: Formato de Artefacto BABYLON-60 v1
status: Causal-Determinist
version: 1.0.0
---

# Formato de Artefacto BABYLON-60 v1

<div align="center">

[![C5-REAL Verified](https://img.shields.io/badge/C5--REAL-Verified-00F0FF?style=for-the-badge&logo=shield)](https://github.com/borjamoskv/BABYLON-60)
[![Régimen](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)

</div>

## 1. Introducción
Esta es la especificación normativa para el *Artifact Bundle* (Paquete de Artefacto) de BABYLON-60. Cualquier implementación conforme de la Fase 0 (Runtime Bootstrap) debe emitir esta estructura canónica exacta. El propósito de este formato es garantizar que estados lógicos idénticos produzcan hashes idénticos, permitiendo la verificación reproducible vía Lean 4 y Coq.

## 2. Disposición del Paquete de Artefacto

El *Artifact Bundle* DEBE ser un directorio (o archivo comprimido) estructurado exactamente de la siguiente manera:

```text
Artifact Bundle
├── manifest.json
├── graph.canonical
├── trace.bin
├── proof.ir
├── metadata.json
├── hashes/
│   ├── graph.sha256
│   ├── trace.sha256
│   └── bundle.sha256
└── signature
```

### 2.1. manifest.json
Un objeto JSON que indica la versión y los hashes estructurales. Debe contener exactamente las siguientes claves:
- `"version"`: DEBE ser `"1.0"`.
- `"components"`: Array de rutas incluidas en el bundle.
- `"global_hash"`: El hash global del bundle, calculado como el SHA-256 de los contenidos concatenados de `hashes/bundle.sha256`.

### 2.2. Serialización Canónica (`graph.canonical`)
El DAG del Ledger DEBE ser serializado de forma canónica antes de aplicar el hash, siguiendo estrictamente las reglas de ordenamiento topológico y el formato delimitado por pipes detallados en la [Especificación de Serialización Canónica de Grafos](spec_graph_canonical.md).

### 2.3. Representación Intermedia (`proof.ir`)
Este archivo contiene la Representación Intermedia (Proof IR) de la traza de ejecución y sus invariantes, limpia de cualquier sintaxis específica de Lean o Coq. Los traductores backend parsearán este IR para generar pruebas nativas.

### 2.4. Hashes
Todos los hashes DEBEN ser codificados en SHA-256 en formato hexadecimal en minúsculas.
- `graph.sha256`: Hash de `graph.canonical`.
- `trace.sha256`: Hash de `trace.bin`.
- `bundle.sha256`: Manifiesto de los hashes de todos los componentes.

## 3. Conformidad
Una implementación solo se considera conforme si el `graph.sha256` producido para un script dado coincide bit-a-bit con el intérprete de referencia.