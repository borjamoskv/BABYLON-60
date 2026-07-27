# BABYLON-60: Graph Canonical Specification (C5-REAL)

> **Régimen C5-REAL | Invariante Asociado: `INV_C5_28`**
> Especificación formal de la serialización canónica de grafos (`graph.canonical`), ordenamiento lexicográfico, refinamiento de color 1-WL (Weisfeiler-Lehman) y cálculo determinista de firmas.

---

## 1. Objetivo y Principio de Canonicidad

Definir las reglas estructurales absolutas del archivo `graph.canonical` emitido por el motor BABYLON-60. El cumplimiento de esta especificación garantiza que dos grafos causales o árboles AST ejecuten un isomorfismo determinista de manera idéntica en cualquier plataforma, preservando la cadena de custodia criptográfica para la verificación formal en Lean 4 / Coq.

---

## 2. Formato de Serialización Pipe-Delimited

El archivo `graph.canonical` debe contener exactamente una línea por cada evento o nodo del grafo causal (`DAGLedger`), utilizando el delimitador pipe (`|`):

$$\text{LineaFormat} := \text{ID} \mid \text{PARENTS} \mid \text{TICK} \mid \text{PAYLOAD} \mid \text{SIGNATURE}$$

```
EV_0||0|R0=60|SIG_OK
EV_1|EV_0|1|R1+=120|SIG_OK
EV_2|EV_0,EV_1|2|AWAIT(SIG_SYNC)|SIG_OK
```

### 2.1 Campos Estrictos
1. **ID**: Identificador causal único (ej. `EV_0`, `EV_102`).
2. **PARENTS**: Lista de IDs de nodos ancestros inmediatos, separados por comas.
   - Si el nodo es raíz, el campo DEBE estar **vacío**.
   - Los IDs de padres DEBEN estar ordenados **lexicográficamente** (ej. `EV_1,EV_2`, nunca `EV_2,EV_1`).
3. **TICK**: Valor escalar entero del reloj lógico monotónico $C$ (ej. `0`, `5`).
4. **PAYLOAD**: Representación determinista del opcode o mutación del estado.
5. **SIGNATURE**: Digest criptográfico de firma de procedencia (ej. `SIG_OK` o HMAC-SHA256).

### 2.2 Invariante de Ordenamiento Lexicográfico
Antes de escribir el archivo a disco o calcular el hash del grafo:
- El vector completo de líneas serializadas DEBE ser **ordenado lexicográficamente según el estándar ASCII** (`canonical_lines.sort()`).
- Cada línea DEBE finalizar obligatoriamente con el salto de línea `\n` (incluida la última línea).
- Codificación de caracteres: **UTF-8 estricto sin BOM**.

---

## 3. Algoritmo 1-WL (Weisfeiler-Lehman 1-D Color Refinement)

Para dar cumplimiento a **`INV_C5_28`**, todo grafo serializado debe someterse al refinamiento de color 1-WL en $O(|V|+|E|)$ para generar la firma de color pre-filtro:

### 3.1 Formulación Matemática de Actualización de Color

Sea $c^{(0)}(v)$ el color inicial del vértice $v \in V$, determinado por el hash SHA-256 de su `PAYLOAD`. En el paso de refinamiento $k + 1$:

$$c^{(k+1)}(v) = \text{SHA256}\left( c^{(k)}(v) \;\parallel\; \text{Sort}\Big(\big\{\!\!\{ c^{(k)}(u) : u \in \mathcal{N}(v) \}\!\!\}\Big) \right)$$

donde $\mathcal{N}(v)$ es el vecindario inmediato del vértice $v$, y $\{\!\{\dots\}\!\}$ denota un multiconjunto.

### 3.2 Pseudocódigo Formal del Pre-Filtro 1-WL

```python
def compute_1wl_hash(graph: Graph, max_iterations: int = 10) -> str:
    # 1. Colores iniciales c^(0)(v)
    colors = {v: sha256(graph.nodes[v].payload.encode()).hexdigest() for v in graph.nodes}
    
    for iteration in range(max_iterations):
        new_colors = {}
        for v in graph.nodes:
            neighbor_colors = sorted([colors[u] for u in graph.neighbors(v)])
            multiset_str = colors[v] + "|" + ",".join(neighbor_colors)
            new_colors[v] = sha256(multiset_str.encode()).hexdigest()
        
        # Si la partición de colores no cambia, alcanzamos la canonicidad 1-WL
        if set(new_colors.values()) == set(colors.values()):
            break
        colors = new_colors

    # Color global del grafo (multiconjunto de colores de vértices ordenados)
    graph_color = sha256(",".join(sorted(colors.values())).encode()).hexdigest()
    return graph_color
```

### 3.3 Política de Activación de VF2 (Exact Isomorphism)
$$\text{VF2\_Trigger}(\mathcal{G}, \mathcal{H}) = \begin{cases}
\mathbf{Execute\_VF2} & \text{si } \text{WLHash}(\mathcal{G}) == \text{WLHash}(\mathcal{H}) \\
\mathbf{Instant\_Reject}(O(1)) & \text{si } \text{WLHash}(\mathcal{G}) \neq \text{WLHash}(\mathcal{H})
\end{cases}$$

---

## 4. Estructura de Raíz Merkle (`graph_hash`)

El hash final del artefacto canónico (`graph_hash`) se calcula inyectando el buffer UTF-8 completo en una función de hash SHA-256:

$$\text{graph\_hash} = \text{SHA256}\Big( \text{line}_1 \parallel \text{line}_2 \parallel \dots \parallel \text{line}_N \Big) \in \{0, 1\}^{256}$$

Este `graph_hash` de 32 bytes binarios es exactamente el valor utilizado por el sink Bitcoin L1 para el cumplimiento de **`INV_C5_15`**.
