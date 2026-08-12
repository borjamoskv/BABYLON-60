---
title: Perfil Criptográfico BABYLON-60
status: Causal-Determinist
version: 1.0.0
---

# Perfil Criptográfico BABYLON-60 (Causal-Determinist)
> **Régimen Causal-Determinist**
> Esta especificación define las primitivas criptográficas, la separación de dominios y las reglas de serialización.

---

## 1. Algoritmos Oficiales

| Componente | Algoritmo | Entrada | Codificación | Versión |
| :--- | :--- | :--- | :--- | :--- |
| **ID de Objeto** | SHA3-256 | `type_prefix` + CBOR | CBOR Determinista | v1 |
| **ID de Evento** | SHA3-256 | Evento canónico | CBOR Determinista | v1 |
| **Raíz de Cadena** | SHA3-256 | `previous_root` + `event_ID` | Bytes con prefijo de longitud | v1 |
| **Padre Merkle** | SHA3-256 | `domain_tag` + `left` + `right` | Binario fijo | v1 |
| **Marca de Tiempo** | Entero (ms) | UTC | Entero sin signo | v1 |

## 2. Etiquetas de Separación de Dominio

Para prevenir ataques de segunda preimagen entre diferentes contextos, todos los nodos del árbol de Merkle utilizan una etiqueta de dominio (`domain tag`):
- **Etiqueta de Nodo Hoja (Leaf):** `0x00`
- **Etiqueta de Nodo Interno:** `0x01`

## 3. Reglas de Serialización

Los eventos DEBEN serializarse utilizando CBOR Determinista antes de ser procesados por la función hash:
- Las claves de los mapas deben ordenarse estrictamente por su valor en bytes.
- Los enteros deben codificarse en la representación más pequeña posible.
- Las cadenas de texto deben ser UTF-8.

## 4. Cadena de Hash vs Árbol de Merkle

- **Cadena de Hash (Hash Chain):** Utilizada para el registro secuencial lineal dentro de un único flujo de inquilino/agente. Esto produce la `Raíz de Cadena`.
- **Árbol de Merkle (Merkle Tree):** Utilizado para crear raíces de snapshots globales que abarcan múltiples flujos/inquilinos en checkpoints específicos. Esto utiliza el `Padre Merkle`.
