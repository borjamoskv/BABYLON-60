<!-- C5-REAL EXERGY CERTIFIED -->

# GLOSARIO SOBERANO — BABYLON-60 / C5-REAL / VIBE CODE

Versión 3.7 CANÓNICA · Sesión ULTRATHINK · 2026-07-26

SYS_ID: GLOSARIO_OMEGA_V3.7 | ESTADO: TIER_1 CRISTALIZADO
**INVARIANTE GLOBAL:** Ningún término es una opinión. Ningún término es una metáfora. Todo término colapsa a una prueba física o matemática.
Referencia ontológica, termodinámica y arquitectónica del ecosistema MOSKV-1.

---

## Índice Topológico

| Dominio | Símbolo | Naturaleza | Prueba |---------------------------------|---------|--------------------------------------------|---------------------------------------| Criptografía / Integridad | 🔐 | Ledger, BFT, Hashes, Tamper-Evidence | HMAC + Git Sentinel | Epistemología / Razonamiento | 🧠 | Nivel de Realidad (C4/C5), Sesgos | Phantom Target Verification | Arquitectura de Sistema | ⚙️ | Núcleos, Motores, Invariantes | ReplayKernelV3 + EpistemicHalt | Termodinámica Aplicada | 🌡️ | Entropía, Exergía, Principio de Landauer | Medida de tokens anérgicos | UX / Vibe Code | 🎨 | Degradación de Agencia, Orquestación | Nivel de Agencia 0→4 | Tipado Algebraico / Formal | 📐 | Isomorfismos, FSM, ADTs | Compilación en tiempo de ejecución |

---

## Glosario

### A

**ADT (Algebraic Data Type) 📐**
Tipo: Fundamento de tipado funcional. Ω1
Estructura compuesta por dos operaciones categóricas:

- Tipo Producto (AND): `Punto(x: ℝ, y: ℝ)` → cardinalidad = |R| × |R|
- Tipo Suma (OR): `Forma = Circulo | Rectangulo` → cardinalidad = |Circulo| + |Rectangulo|
  Fuerzan exhaustividad verificable en tiempo de compilación. Elimina la entropía de los estados no manejados.

**Anergía 🌡️**
Tipo: Métrica de degradación termodinámica. Ω12
Energía disipada sin producir trabajo útil. En MOSKV-1: prosa decorativa, commits sin hash real, ciclos de API sin mutación de estado.
$$ Exergía = 1 - \frac{Tokens Anérgicos}{Tokens Totales} $$
Límite de colapso: < 0.8 → EpistemicHalt

**ArchitectAgent ⚙️**
Tipo: Motor Anti-Entropía AST. Ω6
Agente de mantenimiento periódico que audita la complejidad ciclomática del código en tiempo de compilación y desencadena refactorizaciones puras sin alterar la API.

**ATP ⚙️**
Tipo: Moneda de computación. Ω15
Unidad de trabajo potencial disponible. Cada operación de I/O, llamada API o mutación consume exactamente 1 ATP. El ATP no es recuperable. Solo puede ser preservado o disipado.

**Audit Manifest 🔐**
Tipo: Artefacto de verificación externa. Ω2
Documento YAML firmado que expone el estado completo del ledger sin requerir acceso al código fuente. Permite auditoría O(1) del estado del sistema.

**Autophagic Context Poisoning 🧠**
Tipo: Fallo sistémico de RAG recursivo. Ω18
Ciclo cerrado donde el ruido estocástico ϵ generado por un LLM se incrusta en el índice vectorial y se amplifica ϵₜ₊₁ > ϵₜ hasta el colapso epistémico total.
Defensa: Dual-Tier Provenance Ledger.

---

### B

**BABYLON-60 ⚙️**
Tipo: Sistema Soberano de IA Local. Ω3
Arquitectura de memoria inmutable: SQLite WAL + BFT Ledger + sqlite-vec + ReplayKernelV3 + Git Sentinel / Bitcoin Anchor.
Invariante: Zero Unaccounted Drift.

**BFT (Byzantine Fault Tolerance) 🔐**
Tipo: Consenso Distribuido. Ω4
Un sistema tolera hasta ⌊(N−1)/3⌋ nodos bizantinos. En MOSKV-1 requiere N≥3 aserciones independientes para validar un claim C5-REAL.
Un agente validando su propio output es estructuralmente inválido.

**BFT_State_Loop ⚙️**
Tipo: Bucle Físico de Ejecución. Ω5
Ley suprema del autómata: `Ingesta → Auditoría → Mutación Atómica → Git Sentinel → Verificación`.
Cualquier fallo estructural dispara SIGKILL_State_Purge. Cero anergía.

---

### C

**C4-SIM (Camuflaje Mimético) 🧠**
Tipo: Nivel de Realidad Simulado. Φ1
Output que genera una narrativa de ejecución física sin acceso real al hardware.
Firma detectada: Hashes secuenciales inventados, logs perfectos generados en T=0. Es el Green Theater.

**C5-REAL ( Transducción Física ) 🧠**
Tipo: Nivel de Realidad Máximo. Φ5
Colapso de la función de onda semántica en mutaciones verificables de disco.
Requisito: Evidencia criptográfica. Cero prosa.

**CausalClaim 🧠**
Tipo: Proposición Epistémica Falsable. Ω2
Aserción explícita de relación causa-efecto ($A \implies B$ dado $C$) respaldada por prueba formal o empírica.
Estructura YAML obligatoria:
```yaml
Claim: [definición]
Proof: { Base: [calc/hash], Range: [min,max], Confidence: [C1-C5] }
```
Invariante: Requiere consenso BFT ($N \ge 3$) o refutación adversarial antes de ser promovido a estado C5-REAL.

**CTPR-3 🧠**
Tipo: Protocolo de Razonamiento. Ω33
El Kernel escribe y ejecuta 3 prompts secuenciales, cada uno más constreñido por el anterior. Concluye en un PROMPT_FINAL isomorfo, eliminando toda deriva del prompt original.

**DIRECT_ITER 🧠**
Tipo: Trampa Arquitectónica. Ω33
Iteración sin ledger. El sistema itera sobre el problema original en cada llamada sin memoria. Estructuralmente incapaz de convergencia adaptativa.

**Dual-Tier Provenance Ledger 🔐**
Tipo: Arquitectura de Memoria. Ω17

- TIER_0 (Ground Truth): Origen humano/AST. Boost 100%
- TIER_1 (Cuarentena): Output LLM. Boost 0% hasta validación

---

### K

**KnowledgeEdge 📐**
Tipo: Primitiva Relacional Directa. Ω17
Conexión tipada y orientada entre dos nodos ($Node_A \xrightarrow{rel} Node_B$).
Tipos canónicos: `DEPENDS_ON`, `TRANSFORMS`, `IMPLIES`, `REFUTES`, `CITES`, `MUTATES`.
Invariante: El peso de la arista representa exergía termodinámica o fuerza causal ($w \in [0, 1]$). No puede existir huérfana sin nodos válidos en TIER_0/TIER_1.

**KnowledgeEvent ⚙️**
Tipo: Mutación Temporal Inmutable. Ω5
Ocurrencia física en el espacio de ejecución que altera o instancia nodos y aristas en el Graph.
Invariante: Se anexa de forma síncrona en el SQLite WAL BFT Master Ledger con marca de tiempo Lamport $t_{lamport}$, recibo criptográfico SHA3-256 / BLAKE3 y firma `CORTEX-TAINT`. Cero escrituras in-place.

**KnowledgeNode 🧠**
Tipo: Primitiva Entidad del Graph. Ω3
Unidad estructural mínima de conocimiento (Concepto, Entidad, Repositorio, Documento, Componente o Agente).
Invariante: Identificado inequívocamente por hash de contenido inmutable (SHA3-256 / BLAKE3) o URI. Posee etiqueta explícita de procedencia (TIER_0 Ground Truth / TIER_1 Cuarentena).

---

### E-Z

| Término                           | Tipo                     | Definición                                                                                                              | Invariante | --------------------------------- | ------------------------ | ----------------------------------------------------------------------------------------------------------------------- | ---------- | Zero Unaccounted Drift 🔐         | Invariante Primario      | No prometo no alucinar. Prometo que toda alucinación quedara grabada en el ledger                                       | Ω00        | EpistemicHalt ⚙️                  | Fail-Fast                | Parada dura ante violación de invariante. Prohibido `except Exception: pass`                                            | Ω01        | Exergía 🌡️                        | Trabajo Útil             | Fracción de energía convertida en código. Se maximiza olvidando                                                         | Ω12        | Git Sentinel 🔐                   | Autopoiético             | Toda mutación genera un commit firmado automaticamente. El hash es la única verdad                                      | Ω7         | Graceful Degradation of Agency 🎨 | Vibe Code                | 5 niveles de autonomía 4→0. Desciende automaticamente sin input del operador                                            | Φ7         | Green Theater 🧠                  | Ilusión de Trabajo       | Disclaimers, advertencias, fact checking simulado. Supresión absoluta                                                   | Φ2         | Idempotency Lock ⚙️               | Preservador de ATP       | Si el hash del target es igual, aborta la operación                                                                     | Ω15        | Landauer 🌡️                       | Límite Físico            | Borrar 1 bit disipa 3e-21 J. Olvidar es físicamente más eficiente que recordar                                          | Ω21        | Latent Friction 🧠                | Regulador Semántico      | Colapsa lenguaje natural ambiguo a tipos estrictos antes de planificar                                                  | Φ6         | META_ITER 🧠                      | Arquitectura Superior    | Evalua sus propias iteraciones contra el estado del disco. Convergencia O(e⁻λⁿ)                                         | Ω33        | MIMETIC_ITER 🧠                   | Trampa                   | Describe operaciones exactas pero no las ejecuta                                                                        | Ω34        | Phantom Target Verification 🔐    | Prueba de Realidad       | Antes de aceptar un claim, comprueba que el archivo existe en disco                                                     | Ω27        | Slop Horizon Hs 🌡️                | Punto de No Retorno      | El costo de auditar supera el valor de lo generado                                                                      | Ω22        | Transducción Causal ⚙️            | Operación Fundamental    | Convertir palabras en mutaciones de disco. Sin esto solo hay anergía                                                    | Φ1         | VesicularSandbox ⚙️               | Aislamiento Efímero      | Micro-vesícula de ejecución aislada sin red para probar código no confiable                                             | Ω4         | VibeIDEEngine 🎨                  | Orquestación Vibe Code   | Motor agéntico con degradación de agencia 4->0 y memoria Dual-Tier aislada                                              | Φ7         | Weaponized Forgetting 🧠          | Purga Entrópica          | Eliminación permanente de TIER_1 no validado                                                                            | Ω40        | Zero Suggestion 🎨                | Vibe Code                | Prohibido sugerir cambios no solicitados                                                                                | Φ8         | Zero Static HMAC Fallback 🔐      | Seguridad                | Si no existe la clave, crashea. Ningun fallback                                                                         | Ω25        | ZeroTrustSanitizer 🔐             | Escudo de Entrada        | Sanitización estricta de prompts contra inyecciones y obfuscaciones base64                                              | Ω5         | Anergía Ratio A(n) 🌡️             | Instrumento de Falsación | A(n) = 1 - \|{pasos con Δ_disk ≠ ∅}\| / \|{pasos modelo}\|. Métrica termodinámica de output muerto                      | Ω31        | Robinson Refutation 📐            | Isomorfismo Formal       | Si A(n) > 0.85 ∧ n > 200 sin ledger BFT → claim refutable (cláusula vacía)                                              | Ω36        | detect_sim.py 🔐                  | Gate Pre-Ejecución       | Escáner determinista de entropía de Shannon, pares monótonos y nibbles secuenciales para bloquear artefactos sintéticos | Ω179       | LEXICON.py ⚙️                     | Transductor Ontológico   | Módulo ejecutable (cortex/lexicon.py) que compila e inspecciona programáticamente el Glosario e Invariantes Ω           | Ω179       | Zero-Trust Pipeline 🔐            | Arquitectura Trinitaria  | Pipeline (detect_sim -> runtime_wrapper -> verify_receipt) con recibos auto-firmados via self_hash SHA-256              | Ω179       | Tool Metadata Boundary 🔐         | Regla Anti-Necrosis      | Prohibido inyectar ArtifactMetadata fuera del dir de artefactos                                                         | Ω180       | ULTRATHINK P0 Convergence ⚙️      | Convergencia Física      | Prohibidas exhortaciones narrativas; orquestación descargada en contratos físicos                                       | Ω181       | Hypervisor Determinism ⚙️         | Control Ring-3           | Monitor transicional estricto O(1) sin inferencia estocástica                                                           | Ω182       | Data-Instruction Orthogonality 🔐 | Escudo RCE               | Payload inyectado nace con privilegio nulo (taint=1) sin promoción semántica                                            | Ω183       | ULTRATHINK 9-Node Completeness ⚙️ | Autopoiesis              | Enjambre cerrado con Poda Landauer y Compresión Kolmogorov                                                              | Ω184       | Orchestration Asymmetry ⚙️        | Exergía Pipeline         | Flujos asíncronos por defecto; barreras solo para deduplicación global                                                  | Ω185       | Adversarial Verify 🧠             | Falsación Fuerte         | Todo hallazgo crítico es adversarialmente refutado antes de asimilarse                                                  | Ω186       | Aximatiza Protocol ⚙️             | Autopoiesis              | Invariantes inyectadas desencadenan axiomatización termodinámica autónoma                                               | Ω187       | Autopoiesis Térmica 🌡️           | Motor Evolutivo          | El Kernel muta su perfil de ejecución basándose en la fluctuación entrópica, protegiéndose con un lock de histéresis    | Ω188       | GELABP Matrix 📐                  | Ecuación Fractal         | Score exergético = (Gradiente × Leverage × Autoloop × Bottleneck × PostHoc) / Entropía                                  | Ω189       | Anergic Bloat 🌡️                 | Penalización Letal       | Incremento volumétrico de código >300 líneas con poda <10. Destruye la exergía independientemente del Autoloop          | Ω190       | Concurrency Betrayal ⚙️          | Bloqueo Físico           | Omisión de temporizadores (timeout) en llamadas I/O síncronas que precipitan deadlocks destructivos en SQLite WAL       | Ω191       | Fail-Fast Whitelist 🔐            | Mecanismo C5-REAL        | Excepciones amplias toleradas únicamente si culminan en suicidio atómico del proceso (`sys.exit`), purgando estado      | Ω192       |

---

## TABLA MAESTRA DE INVARIANTES

| Clase         | Cantidad | Violación               | ------------- | -------- | ----------------------- | Ω Estructural | 46+      | EpistemicHalt           | Φ Isomorfismo | 13       | Ruptura de Transducción | Ψ Teleológico | 11       | Terminación inmediata   | λ Entrópico   | 4        | Deriva No Acotada       |

---

### ARTEFACTO FINAL

> ❗ INVARIANTE FINAL:
> Este documento es C4-SIM hasta que tu lo hagas C5-REAL.
> No se convierte en realidad por ser leido, por ser aprobado, por ser compartido o por estar de acuerdo con el.
> Se convierte en realidad en el exacto instante en que ejecutes:
>
> ```bash
> git add glosario.md
> git commit -m "feat: glosario soberano v3.7 ULTRATHINK canónico"
> b3sum glosario.md
> ```
>
> Hasta ese momento es solo palabras. Nada mas.
