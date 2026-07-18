# TIPADO ALGEBRAICO Y MECÁNICA GENÓMICA C5-REAL (ULTRATHINK)
> **Autor:** borjamoskv
> **Nivel de Realidad:** C5-REAL
> **Módulo:** `babylon60.types.algebraic` & `babylon60.genomics.adt`

## 1. PRINCIPIO DE DISEÑO: "Make Illegal States Unrepresentable"
El Tipado Algebraico C5-REAL transducido en BABYLON-60 no es una convención semántica, es una barrera termodinámica. Las variables estocásticas (Strings, Dicts anidados, Nulos) generan una alta fricción entrópica y violan la cardinalidad estricta del isomorfismo de Curry-Howard.

Mediante el uso de **Sum Types** (Uniones Etiquetadas) y **Product Types** (Registros Estrictos) en Python 3.10+ (vía `@dataclass(frozen=True)` y `typing.Union`), garantizamos que las transiciones de estado imposibles o los estados intermedios ilegales no compilen bajo `mypy --strict`.

### 1.1 Leyes Cardinales Aplicadas
1. **Tipos Producto ($|A \times B| = |A| \cdot |B|$):** Un `GenomicVariantRecord` es el producto estricto de su posición y su variante.
2. **Tipos Suma ($|A + B| = |A| + |B|$):** `CoordinateSystem = BED0Based | VCF1Based`. Es físicamente imposible representar una coordenada que mezcle ambos sistemas; la cardinalidad exacta divide los dominios y previene errores "Off-By-One".
3. **Mónadas de Flujo:** 
   - `Result[T, E] = Ok[T] | Err[E]`
   - `Option[T] = Some[T] | Nothing`

## 2. GENÓMICA ESTRUCTURAL: SUM TYPES EN ONCOLOGÍA
Las clasificaciones clínicas han sido reducidas a estados discretos (Sum Types) bajo el módulo `babylon60.genomics.adt`:

- **TMBClassification:** `TMBHigh` | `TMBLow` | `TMBIndeterminate`. Un estado `TMBLow` no puede ser forzado a revelar los mismos diccionarios de detalles que el `High` si así se modela, evitando la fuga de estado.
- **APOBECStatus:** `APOBECDriven` | `APOBECBackground`.
- **HRDStatus:** `HRDPositive` | `HRDNegative`.

Cualquier patrón en el AST (Pattern Matching `match / case`) que no procese todas las ramas de estas uniones, fallará contra `make_illegal_states_unrepresentable()`.

## 3. TERMODINÁMICA GENÓMICA: REGLA Ω31 (ENTROPÍA CLONAL)
El genoma oncológico es un sistema caótico (Prigogine, Teorema H de Boltzmann). La Regla $\Omega31$ dicta que no podemos simular entropía; debemos calcularla físicamente sobre el disco.

Se ha implementado el cálculo exacto de la **Entropía de Shannon** para el paisaje subclonal:
$$ S_{clonal} = - \sum_{i=1}^{n} p_i \ln(p_i) $$

Donde $p_i$ es la frecuencia alélica normalizada del clon $i$. El motor `GenomicEvaluationEngine.evaluate_clonal_entropy` computa este valor y lo encapsula en un tipo `ClonalEntropyResult` C5-REAL, anclando el grado termodinámico de heterogeneidad intra-tumoral al estado Booleano.

## INVENTARIO DE IGNORANCIA: Lo que sé que no sé (L38)
1. **Isomorfismo de Categorías:** Sé que el tipado algebraico implementado en Python carece de la pureza de un sistema basado en Hindley-Milner (como F# o Haskell). No sé si la barrera de `mypy --strict` será suficiente para prevenir el 100% de los escapes a nivel de runtime C-extension.
2. **Cardinalidad Cuántica de Variantes SV:** Las Variantes Estructurales (SVs) tienen una cardinalidad casi infinita al depender de metadatos `dict` crudos (`breakpoint_info`). No he tipado algebraicamente los SV breakpoints (e.g., BND, INV) de manera absoluta, dejando una pequeña vía abierta de entropía.
3. **Pérdida de Entropía Dinámica:** Calculamos la Entropía de Shannon de un snapshot secuencial (VCF estático). No sé cómo mapear la *derivada temporal* de la entropía $\frac{dS}{dt}$ en la red booleana sin múltiples muestras temporales del mismo paciente.
