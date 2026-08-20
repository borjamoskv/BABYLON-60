# 🛡️ NUL-ZK — Zero-Knowledge Circuit Compiler & Arkworks Engine

> **ESTADO:** Congelado / Vault Histórico  
> **Transducción en Producción:** [`src/proof_ir.rs`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/src/proof_ir.rs) y [`packages/babylon60/attestation/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/packages/babylon60/attestation)

---

## 📐 Estructura de Ficheros

| Fichero | Descripción Técnica |
|---|---|
| [`src/ast.rs`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/legacy_exergy/NUL-ZK/src/ast.rs) | Gramática y Árbol de Sintaxis Abstracta (AST) para el DSL de circuitos ZK. |
| [`src/compiler.rs`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/legacy_exergy/NUL-ZK/src/compiler.rs) | Compilador DSL → Puertas R1CS (`Gate`), optimizaciones Zero-Anergy y emisor Rust Arkworks. |
| [`example_arkworks.rs`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/legacy_exergy/NUL-ZK/example_arkworks.rs) | Ejemplo de implementación de la trait `ConstraintSynthesizer<F>` para multiplicación R1CS. |

---

## ⚡ Flujo de Compilación & Pasadas de Optimización

```
[ DSL AST (ast.rs) ]
       │
       ▼  (Compiler::compile)
[ Puertas R1CS Intermedias (Gate) ]
       │
       ├─► Pass 1: Constant Folding (Plegado de Constantes y evaluación en tiempo de compilación)
       ├─► Pass 2: Dead Code Elimination (DCE / Purga de puertas no consumidas)
       │
       ▼  (generate_arkworks_rust)
[ Código Fuente Rust con Trait ConstraintSynthesizer<F> (Arkworks) ]
```

---

## 🧮 Restricción Multiplicativa R1CS (Ejemplo)

Para el caso del multiplicador $c = a \times b$:
$$\text{Constraint 1: } a \cdot b = v_0$$
$$\text{Constraint 2: } v_0 \cdot 1 = c$$
