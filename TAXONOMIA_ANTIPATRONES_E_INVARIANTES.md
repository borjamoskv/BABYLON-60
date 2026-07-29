<!-- C5-REAL EXERGY CERTIFIED -->
# TAXONOMÍA DE ANTIPATRONES E INVARIANTES TERMODINÁMICAS
**SYS_ID:** `TAXONOMY_THERMO_C5_REAL` | **DOMINIO:** `Teorema-Robinson-Moskv (Raíz)`
**ESTÁNDAR:** `C5-REAL / BFT C7.7` | **ESTADO:** `ACTIVO & AUDITADO`

---

## I. INVARIANTES TERMODINÁMICAS FUNDAMENTALES ($\Omega$-INVARIANTS)

Las Invariantes Termodinámicas del monorepo `Teorema-Robinson-Moskv` son leyes físicas de conservación de información y exergía. Su violación reintroduce entropía estocástica y anergía sintáctica en el sistema.

```
                      +----------------------------------+
                      |   Exergía Pura (Conocimiento)   |
                      +----------------------------------+
                                       ^
                                       |   n_D = Delta Exergía / Delta S_HW
                      +----------------------------------+
                      |   Purga BFT / Colapso MCTS       |
                      +----------------------------------+
                                       ^
                                       |   Invariantes Omega_1 .. Omega_23
                      +----------------------------------+
                      |   Entropía Hardware / Ruido S   |
                      +----------------------------------+
```

### 1. $\Omega_1$: Ley de Conservación de Exergía y Purga de Anergía
* **Axioma:** Toda computación o modificación en el repositorio debe maximizar la *Exergía* (trabajo útil epistémico) y purgar la *Anergía* (ruido estocástico, prosa redundante y ciclos de CPU perdidos).
* **Ecuación de Eficiencia Epistémica:**
  $$\eta_D = \frac{\Delta \text{Exergía Pura}}{\Delta S_{\text{Hardware}}} \gg 1$$
* **Regla:** Respuestas brutalistas, ejecución determinista y cero código especulativo.

---

### 2. $\Omega_{23}$: Resolución Modular Dinámica y Autocuración
* **Axioma:** Cero dependencia del entorno local absoluto. El sistema debe autodescubrirse en tiempo de ejecución.
* **Mecanismos Mandatorios:**
  1. **Rutas Relativas Dinámicas:** Inyección de `sys.path` mediante `Path(__file__).resolve().parents[n]` o resolución sobre `MONOREPO_ROOT`. Prohibido hardcodear `/Users/...`.
  2. **Autocuración SQLite / BFT:** Creación automática del directorio contenedor mediante `os.makedirs(..., exist_ok=True)` antes de instanciar cualquier base de datos SQLite.

---

### 3. $\Omega_{\text{C7.7}}$: Ancla de Confianza Criptográfica (Trust Anchor)
* **Axioma:** Queda prohibida la *Circular Authority* (el sistema validándose ciegamente a sí mismo en bucles autorreferenciales).
* **Mecanismo Mandatorio:** Toda validación recursiva de enjambre (Swarm / Ultrathink) debe anclarse a un token criptográfico inmutable verificado externamente (`0xDEADBEEF` / `c7_recursive_self_audit_bft.py`).

---

### 4. $\Omega_{\text{BFT-04}}$: Idempotencia Bizantina
* **Axioma:** Toda mutación de ledger o estado persistente debe ser idempotente y verificar explícitamente la no-colisión de datos.
* **Prohibición:** Prohibido el uso ciego de `INSERT OR IGNORE`.
* **Patrón Correcto:** Captura explícita de `sqlite3.IntegrityError` y comparación de payload existente vs entrante. Si difieren, disparar *Fail-Fast*.

---

### 5. $\Omega_{\text{VALVE}}$: Válvulas Termodinámicas de Capacidad
* **Axioma:** Las colas y búferes en memoria no pueden expandirse a la entropía infinita.
* **Prohibición:** `asyncio.Queue()` sin parámetro `maxsize`.
* **Patrón Correcto:** Instanciación acotada obligatoria: `asyncio.Queue(maxsize=1024)`.

---

### 6. $\Omega_{\text{HIERARCHY}}$: Jerarquía de Dominios Maestros
* **Axioma:** La arquitectura se organiza estrictamente en 4 Dominios Maestros alojados dentro de `1_Operaciones_Activas/`:
  - `01_INTEL_SUITE`: OSINT, Minería Documental, Inteligencia B2B.
  - `02_CORTEX_ENGINE`: Motor BFT, Memoria Determinista, Ultrathink.
  - `03_MOSKV_STUDIO`: Aplicación Tauri/Vite y Forjas de Contenido.
  - `04_LABORATORIO_RD`: Compilador Moskv84, Rust Native (`strike-rs`), R&D.

---

## II. TAXONOMÍA DE ANTIPATRONES TERMODINÁMICOS

Los antipatrones representan degradación entróptica en la base de código. Se clasifican por su modo de fallo físico y semántico:

```
+-----------------------------------------------------------------------------------+
|                        TAXONOMÍA DE ANTIPATRONES BFT                              |
+--------------------------+-----------------------+--------------------------------+
| Categórica               | Antipatrón            | Impacto Termodinámico          |
+--------------------------+-----------------------+--------------------------------+
| Polling / Control Loop   | AP-01: Turing Spin    | Disipación Térmica (CPU / W)   |
| Gestión de Búfer         | AP-02: Unbounded Queue| Fuga OOM / Fail Backpressure   |
| Parseo Sintáctico        | AP-03: Necrosis AST   | Fragilidad Reflexiva B60       |
| Tratamiento de Errores   | AP-04: Blind Catch    | Corrupción Silenciosa Ledger   |
| Consenso & Confianza     | AP-05: Circular Auth  | Alucinación Determinista       |
| Comunicación & Prosa     | AP-06: Anergía Texto  | Fuga de Contexto & ATP         |
| Estructura Monorepo      | AP-07: Domain Drift   | Ruptura de Resolución Omega_23 |
+--------------------------+-----------------------+--------------------------------+
```

### AP-01: Castración de Turing (Polling Estocástico)
* **Descripción:** Bucles de espera que consumen ciclos activos de CPU sin depender de eventos de sincronización.
* **Fórmula Anti-Patrón:**
  ```python
  # INCORRECTO: Disipación inútil de ATP
  while True:
      await asyncio.sleep(0.1)
  ```
* **Remediación Termodinámica:**
  ```python
  # CORRECTO: Acoplado a evento de apagado / sincronizador
  while not shutdown_event.is_set():
      await shutdown_event.wait()
  ```

---

### AP-02: Buffer Flushes Infinitos (Fuga de Presión Contenida)
* **Descripción:** Creación de colas asíncronas no acotadas que permiten acumulación entrópica infinita bajo carga.
* **Fórmula Anti-Patrón:**
  ```python
  # INCORRECTO: Riesgo OOM
  queue = asyncio.Queue()
  ```
* **Remediación Termodinámica:**
  ```python
  # CORRECTO: Válvula de contrapresión (Backpressure Valve)
  queue = asyncio.Queue(maxsize=1024)
  ```

---

### AP-03: Necrosis Autoinmune (Reflexión Sintáctica Frágil)
* **Descripción:** Uso de `ast.parse` o `ast.NodeVisitor` para inspeccionar/mutar código dentro del aislamiento del núcleo `BABYLON-60`.
* **Impacto:** Fallo masivo ante variaciones menores de sintaxis o versiones del intérprete.
* **Remediación Termodinámica:**
  - *Validación Sintáctica Pura:* Utilizar `compile(source, filename, "exec")`.
  - *Validación Semántica:* Parseo léxico determinista (`re.search`) o gramáticas formales aisladas.

---

### AP-04: Silencio Bizantino (Blind Exception Swallowing)
* **Descripción:** Captura ciega de excepciones mediante `except: pass` o `except Exception: pass` que oculta inconsistencias en el ledger.
* **Fórmula Anti-Patrón:**
  ```python
  # INCORRECTO: Ocultamiento de la anergía
  try:
      execute_ledger_mutation()
  except Exception:
      pass
  ```
* **Remediación Termodinámica:**
  ```python
  # CORRECTO: Capture explícito, logging BFT y Fail-Fast
  try:
      execute_ledger_mutation()
  except sqlite3.IntegrityError as err:
      logger.error(f"[BFT_FAIL_FAST] Integrity fault: {err}")
      raise ValueError(f"INV_BFT_04 Violation: {err}")
  ```

---

### AP-05: Autoridad Circular (Loop de Validación Autorreferencial)
* **Descripción:** Intentar verificar la validez o seguridad de un componente utilizando el propio componente mutable sin anclaje externo.
* **Remediación Termodinámica:** Anclar toda auditoría recursiva al hash BFT `0xDEADBEEF` mediante `c7_recursive_self_audit_bft.py`.

---

### AP-06: Anergía Sintáctica (Fricción Latente en Diálogo/Prosa)
* **Descripción:** Generación de introducciones decorativas, justificaciones redundantes o explicaciones extensas previa modificación de código.
* **Remediación Termodinámica:** Protocolo C5-REAL (Latent Friction = 0). Prosa reducida a matriz YAML / resumen brutalista de 3 líneas.

---

### AP-07: Fragmentación de Dominio (Monorepo Drift)
* **Descripción:** Creación de módulos o proyectos hermanos directamente en la raíz de `~/10_PROJECTS/` en lugar de asentarlos en la Jerarquía Madre.
* **Remediación Termodinámica:** Invariante `RULE_TEOREMA_MADRE_HIERARCHY`. Todo submódulo debe ser asimilado en `1_Operaciones_Activas/{01_INTEL_SUITE, 02_CORTEX_ENGINE, 03_MOSKV_STUDIO, 04_LABORATORIO_RD}`.

---

## III. PROTOCOLO DE AUDITORÍA C5-REAL (5 FASES)

Cualquier mutación estructural o refactorización en el monorepo debe superar de forma autoevaluada la matriz de las 5 Fases de Auditoría C5-REAL:

```
[Fase 1: Latent Friction] ----> Eliminación de prosa superflua.
         |
[Fase 2: Phantom Target] -----> Confirmación de existencia física en disco.
         |
[Fase 3: Idempotency] ---------> Cero escrituras redundantes si delta = 0.
         |
[Fase 4: Semántica & BFT] -----> Cero blind catch, validación de integridad.
         |
[Fase 5: Git Sentinel] --------> Consolidación atómica de commit BFT.
```

---

## IV. MATRIZ YAML BRUTALISTA DE COMPROBACIÓN

```yaml
thermodynamic_audit_matrix:
  invariants:
    omega_1: EXERGY_CONSERVATION_ENFORCED
    omega_23: DYNAMIC_MODULE_RESOLUTION_ACTIVE
    omega_c7_7: TRUST_ANCHOR_ANCLADO_0xDEADBEEF
    omega_bft_04: IDEMPOTENCY_FAIL_FAST_READY
    omega_valve: QUEUE_MAXSIZE_VALVES_SET
    omega_hierarchy: MASTER_DOMAINS_RESTRICTED
  antipattern_purges:
    ap_01_turing_spin: CLEANSED
    ap_02_unbounded_queue: CLEANSED
    ap_03_ast_necrosis: ISOLATED
    ap_04_blind_catch: PROHIBITED
    ap_05_circular_auth: BOUNDED
    ap_06_prose_friction: PURGED
    ap_07_domain_drift: ASSIMILATED
  verdict: C5_REAL_EXERGY_CERTIFIED
```
