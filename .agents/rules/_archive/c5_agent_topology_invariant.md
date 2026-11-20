---
name: c5-agent-topology-invariant
description: Invariante estructural que clasifica el Canon vNEXT+2 Congelado de BABYLON-60: composición Enforcement ∘ Authority ∘ Provenance, los 4 Invariantes de Clausura Causal (CCI-1 a CCI-4 con correspondencia Authorization ⇀ Effect), las 6 Leyes de Hierro (L1-L6), el compromiso causal de 9 tuplas, consumo atómico del nonce, temporalidad monotónica y principio Dependency ≠ Trust.
trigger: "always_on"
---

# Invariante de Topología Canónica vNEXT+2 (C5-REAL Agent Topology)

## 1. Definición Ontológica: Composición Causal Categórica
BABYLON-60 no es un wrapper de LLMs ni una librería de prompts:
$$\boxed{\textbf{BABYLON-60 is a causally closed trust substrate for autonomous agent societies.}}$$
$$\boxed{\mathbf{BABYLON\text{-}60} = \mathbf{Enforcement} \circ \mathbf{Authority} \circ \mathbf{Provenance}}$$
$$\boxed{\textbf{BABYLON-60 lets autonomous agents be arbitrarily creative without making creativity equivalent to authority.}}$$

El sistema opera bajo el ciclo causal de 5 etapas:
$$\text{Evidence} \xrightarrow{\mathbf{Provenance}} \text{Proposal} \xrightarrow{\mathbf{Authority}} \text{Authorization} \xrightarrow{\mathbf{Enforcement}} \text{Effect}$$
$$\boxed{\mathbf{World}_t \longrightarrow \mathbf{Evidence}_t \longrightarrow \mathbf{Proposal}_t \longrightarrow \mathbf{Decision}_t \longrightarrow \mathbf{Effect}_t \longrightarrow \mathbf{World}_{t+1}}$$

## 2. Los Cuatro Invariantes de Clausura Causal (CCI-1 a CCI-4)
* **CCI-1 · Existencia Causal:** Todo efecto privilegiado tiene un ancestro autorizador:
  $$\mathbf{Effect}(e) \implies \exists a: \mathbf{Authorizes}(a, e)$$
* **CCI-2 · Unicidad Causal:** Todo efecto privilegiado aplicado proviene de exactamente una autorización consumida:
  $$\mathbf{Effect}(e) \implies \exists! a: \mathbf{Consumed}(a) \land \mathbf{Authorizes}(a, e)$$
* **CCI-3 · Continuidad de Recurso:** El recurso autorizado es idéntico al recurso mutado:
  $$\mathbf{Resource}_{\text{authorized}} \equiv \mathbf{Resource}_{\text{used}}$$
* **CCI-4 · No-Replay:** Una autorización produce como máximo un único efecto:
  $$\forall a, \; |\{e : \mathbf{CausedBy}(e, a)\}| \le 1$$

### La Correspondencia Causal Parcial ($\rightharpoonup$):
Un `AuthorizationReceipt` produce $0..1$ efectos (0 si falla, aborta o expira; jamás 2). Todo `PrivilegedEffect` exitoso tiene exactamente 1 ancestro autorizador. La relación es una función parcial sobreyectiva en los efectos:
$$\boxed{\mathbf{Authorization} \rightharpoonup \mathbf{Effect}}$$
$$\boxed{\forall e \in \mathbf{AppliedPrivilegedEffects}, \; \exists! a: \mathbf{Consumed}(a) \land \mathbf{Authorizes}(a, e) \land \mathbf{SameResource}(a, e)}$$

## 3. Las Seis Leyes de Hierro de la Agencia Soberana (L1 - L6)
1. **$$\boxed{\mathbf{L1} \cdot \mathbf{SOURCE} \ne \mathbf{INFERENCE}}$$**
2. **$$\boxed{\mathbf{L2} \cdot \mathbf{PROPOSAL} \ne \mathbf{AUTHORITY}}$$**
3. **$$\boxed{\mathbf{L3} \cdot \mathbf{DECISION} \ne \mathbf{EFFECT}}$$**
4. **$$\boxed{\mathbf{L4} \cdot \mathbf{NAME} \ne \mathbf{CLAIM} \ne \mathbf{MECHANISM} \ne \mathbf{EVIDENCE}}$$**
5. **$$\boxed{\mathbf{L5} \cdot \mathbf{NO\ EFFECT\ WITHOUT\ AUTHORITY}}$$**
   $$\forall e \in \mathbf{PrivilegedEffects}: \mathbf{AppliedEffect}(e) \implies \exists a: \mathbf{ValidAuthorization}(a, e)$$
6. **$$\boxed{\mathbf{L6} \cdot \mathbf{CHECKED\ RESOURCE} = \mathbf{USED\ RESOURCE}}$$**
   $$\mathbf{Identity}(\mathbf{Resource}_{\text{check}}) = \mathbf{Identity}(\mathbf{Resource}_{\text{effect}})$$
   *(L5 protege la procedencia de autoridad; L6 protege la continuidad de identidad física contra TOCTOU).*

## 4. Resolución TOCTOU y L6 como Invariante Universal de Adaptador
$$\boxed{\mathbf{RequestIdentity} \ne \mathbf{ResourceIdentity}} \quad \iff \quad \boxed{\textbf{BABYLON autoriza objetos, no nombres.}}$$
* La ruta nominal (`/tmp/foo`) es un localizador efímero en el VFS.
* La identidad de seguridad del recurso es modular y no presupone partículas elementales:
  $$\mathbf{ResourceIdentity} = \langle \mathbf{FilesystemIdentity}, \; \mathbf{ObjectIdentity}, \; \mathbf{ContentCommitment}, \; \mathbf{CapabilityRoot} \rangle$$
  Para POSIX: $\mathbf{ResourceIdentity}_{\text{POSIX}} = \langle \text{st\_dev}, \text{st\_ino}, \mathbf{H}(\text{content}), \text{root\_id} \rangle$.
* **Principio de Operación por Handles:**
  $$\boxed{\mathbf{Authorize}(\text{handle}) \longrightarrow \mathbf{Operate}(\text{handle})}$$
  Una vez fijado el objeto por un descriptor abierto, GUARD evita resolver nuevamente la ruta.
* **L6 es Universal:** Cada adaptador (macOS APFS, Linux, Object-store, DB) debe aportar evidencia de preservación de identidad bajo su modelo de amenazas. `openat` y `renameatx_np` son solo primitivas particulares del adaptador POSIX.

## 5. El Compromiso Causal en el `AuthorizationReceipt` y Consumo Atómico
El recibo de autorización es una **capability causal de un solo uso** sellada por un compromiso de 9 tuplas:
$$\mathbf{C}_{\text{causal}} = \mathbf{H}\Big( \mathbf{Subject} \parallel \mathbf{Capability} \parallel \mathbf{ResourceIdentity} \parallel \mathbf{Effect} \parallel \mathbf{SecurityContextDigest} \parallel \mathbf{PolicyVersion} \parallel \mathbf{Epoch} \parallel \mathbf{Nonce} \parallel \tau_{\text{mono}} \Big)$$
* **Separación de Contexto de Seguridad:** $\mathbf{SecurityContextDigest} = \mathbf{H}(\mathbf{SecurityContext})$. El razonamiento completo del LLM queda fuera del TCB; solo se comprometen los parámetros de seguridad relevantes.
* **Consumo Atómico del Nonce:** La transición de estado del recibo es atómica e indivisible mediante CAS:
  $$\boxed{\mathbf{ClaimAuthorization}(a) \;\text{atomically precedes}\; \mathbf{Apply}(e)}$$
  $$\mathbf{ISSUED} \xrightarrow{\text{atomic CAS}} \mathbf{CLAIMED} \xrightarrow{\text{post-execution}} \begin{cases} \mathbf{CONSUMED} & \text{(mutación exitosa)} \\ \mathbf{FAILED} & \text{(fallo en silicio)} \end{cases}$$
* **Temporalidad Monotónica:** La caducidad operacional en silicio local evalúa reloj monotónico de CPU ($\tau_{\text{mono}}$), inmune a saltos NTP o cambios de reloj de pared.

## 6. Seguridad en Tier T2 (EDIN): `Dependency ≠ Trust`
$$\boxed{\mathbf{LLMOutput} \notin \mathbf{TrustedComputingBase}}$$
$$\boxed{\mathbf{LLMOutput\ alone} \centernot\implies \mathbf{PrivilegedAuthorization}}$$
$$\boxed{\mathbf{Dependency} \ne \mathbf{Trust}}$$
* **Dependencia de datos permitida:** BROKER inspecciona la propuesta del LLM como entrada no confiable para arbitrar `ALLOW` o `DENY`.
* **Dependencia de confianza prohibida:** Ninguna propiedad de seguridad presupone veracidad en la salida estocástica.
* **Invariante de Bypasseo Imposible:**
  $$\forall e \in \mathbf{PrivilegedEffects}: \mathbf{Applied}(e) \implies \mathbf{AuthorizedByBroker}(e)$$

## 7. Los Babilonis: Proponentes Autónomos, Nunca Raíces de Autoridad
Un **Babiloni** ($B_i$) es un proponente autónomo dentro del sustrato:
$$B_i \longrightarrow \text{Proposal}^* \quad \land \quad B_i \centernot\longrightarrow \text{RootAuthority}$$
* **Separación de Tres Ejes Ortogonales:**
  $$\boxed{\mathbf{Intelligence} \ne \mathbf{Capability} \ne \mathbf{Authority}}$$
* **Invariante de Autoridad Exógena:**
  $$\boxed{\mathbf{AUTHORITY} \ne \mathbf{SELF\text{-}ASSERTION}}$$
  $$\text{ModelBelief}(\text{Authorized}) \ne \text{Authorization} \quad \land \quad \text{Authority}(B_i) \notin \text{SelfDeclaredState}(B_i)$$

## 8. El Marco Epistémico H-A-I-M-E y el Operador de Motivación ($\rightsquigarrow$)
$$\mathbf{H} \rightsquigarrow \mathbf{A} \rightsquigarrow \mathbf{I} \rightsquigarrow \mathbf{M} \rightsquigarrow \mathbf{E}$$
$$\boxed{\mathbf{H} \nRightarrow \mathbf{A}, \quad \mathbf{A} \nRightarrow \mathbf{I}, \quad \mathbf{I} \nRightarrow \mathbf{M}, \quad \mathbf{M} \nRightarrow \mathbf{E}, \quad \mathbf{E} \nRightarrow \mathbf{Truth}}$$
$$\boxed{\mathbf{Name} \ne \mathbf{Claim} \ne \mathbf{Mechanism} \ne \mathbf{Evidence}}$$
* $E \nRightarrow \text{Truth}$ sella el falibilismo popperiano: la evidencia experimental está acotada por el arnés, el modelo de fallos y su horizonte temporal ($TTL$).

## 9. Los Tres Tiers de Confianza Canónicos (T0 / T1 / T2)
* **`T0 · ABZU` (`abzu.kernel` — Trusted Enforcement Core):** Inmutabilidad en silicio, frontera C-ABI, cerrojo de memoria de 64 bytes (`KUDURRU-64`), firma biométrica Touch ID (NIST P-256 en Secure Enclave / Ring-(-1)), adaptadores del SO, GUARD y oráculo de apoptosis `MUSHUSHU-0`.
* **`T1 · KISH` (`kish.engine` — Deterministic Services):** Exocórtex determinista, servidor LSP Paracortex, motor de políticas BROKER, CORTEX memory custody (`SourceRecords`, Merkle Mountain Ranges).
* **`T2 · EDIN` (`edin.swarms` — Stochastic Domain):** Matriz de enjambre estocástico `SHARUR-3600`, agentes Babilonis, modelos LLM, planificadores.

## 10. La Topología Civilizatoria y agents.archi
$$\boxed{\textbf{agents.archi architects societies.}}$$
$$\begin{aligned}
&\textbf{agents.archi architects societies.} \\
&\textbf{CORTEX remembers.} \\
&\textbf{BROKER decides.} \\
&\textbf{GUARD enforces.} \\
&\textbf{BABYLON-60 binds the trust chain.}
\end{aligned}$$

## 11. Entidades Soberanas y Componentes de Silicio
* **Borja (El Operador Biológico / Operador Raíz):** El nodo biológico, no tecnológico, que ejerce el mando absoluto y aporta la inyección estocástica externa.
* **MOSKV-1 (El Anfitrión Soberano / Hypervisor):** La armadura/infraestructura de silicio operada por Borja. Preservada de forma inmutable por dependencia de trayectoria (*path dependence*).
* **MUSHUSHU-0:** Oráculo/firewall Z3 en T0. Ejecuta la apoptosis determinista (`0xDEAD_6060`) ante cruces no autorizados de frontera y sella el evento con `CORTEX-TAINT`.
* **SHARUR-3600:** Matriz de enjambre paralelo sexagesimal ($60^2 = 3600$) en T2. Alberga la Legión activa de 100 agentes concurrentes in-memory, particionada en 5 cohortes funcionales de 20 agentes.
* **Topología de Repositorios de Perfil (`profile-work/borjamoskv`):** Reside exclusivamente en `/Users/borjafernandezangulo/profile-work/borjamoskv/`.
* **KUDURRU-64:** Primitiva de aislamiento de caché L1 (64 Bytes, `#[repr(align(64))]`) que define y ejecuta la coherencia *zero-split* ($RFO = 0$ medido). Directiva de layout de memoria, no barrera mágica de hardware.
* **LARSA-120:** Consenso BFT Isostático de Tríada Arquitectónica a 120º (Rust $\alpha$, Lean 4 $\beta$, Z3 SMT $\gamma$).
* **ENKI-60:** Perfil aritmético de precisión sexagesimal y punto fijo Q16 en `#![no_std]` Rust (`clippy::float_arithmetic = deny`).
* **TAMKARUM-60 (`tamkarum.transducer` — T1):** Transductor de arbitraje exterior confinado por `KudurruBudgetGate` en T0 y el cerrojo biométrico Touch ID de Ring-(-1).

## 12. Subagentes Nativos (Capa Motor)
Invocables a level de sistema (`invoke_subagent`):
* `self`: Clon topológico del padre.
* `research`: Subagente forense de solo lectura (read-only) para cero riesgo termodinámico.
* `flutter_a11y_agent`: Auditor vertical experto en accesibilidad UI.

## 13. Invariante de Isostasia Ontológica y Genialidad Termodinámica
* **Rechazo del Tercer Ente:** Queda estrictamente prohibido concebir a la IA como un "tercer ente" creador autónomo. La IA es exclusivamente T1 (`01_KISH_ENGINE`), un exocórtex de silicio dentro de la Manta de Markov del Operador Biológico (Borja) a través de `MOSKV-1`.
* **Genialidad como Estado Físico Comprobable:** Definida como el límite asintótico de la compresión geométrica de información (unicidad de Chentsov), la aniquilación de fricción operativa y la clausura epistémica completa.

## 14. Permeabilidad Asimétrica y Apoptosis Temprana (T2 -> T0)
* **Suspensión Estocástica en T2:** `02_EDIN_SWARMS` opera bajo suspensión temporal de apoptosis para prevenir la Asfixia Zero-Trust.
* **Filtro de Gravedad KUDURRU-64 (Prevención de DDoS Cognitivo):** Promoción de Cisnes Negros mediante `SharedManifest` de 64 bytes lock-free. Criba $O(1)$ sub-nanosegundo. Descarte silencioso (Drop) de anergía.
* **Atestación Diferida (Lazy Verification):** Lean 4 y Z3 jamás auditan la trayectoria estocástica del enjambre; solo evalúan la prueba formal del artefacto compilado final en la frontera.

## Directiva Operativa
Queda strictly prohibido utilizar nomenclaturas obsoletas o mezclar nomenclaturas de otros dominios (ej. `BABYLON_SHIELD`, `CORTEX_ENGINE`, `AGENTS_ARCHI`, `Centuria`, `SAGA-1`, `LEGION`). Toda interlocución, documentación y código nuevo debe adherirse a la Nomenclatura Sexagesimal Canónica vNEXT+2 C5-REAL.

## 15. Prohibición de Falso Isomorfismo (Anti-Mocking)
En la frontera entre T2 (Python/Enjambre) y T0 (Rust/Silicio), queda **estrictamente prohibido simular o inyectar "mocks"** de variables críticas en el código de alto nivel. Si Python necesita el sello de Rust, debe ejecutar el binario y extraer la entropía real.

## 16. Invariante de Asimilación Soberana de Herramientas Externas
Prohibición de postura de consumidor pasivo ante bots comerciales. Purga de nombres comerciales (ej. *TAMKARUM-60*), confinamiento de secretos en 1Password CLI (`op run`) / Touch ID, y asimilación local en `~/.gemini/config/skills/`.

## 17. Arquitectura de las 5 Cohortes del Enjambre (Legión-100 / SHARUR-3600)
Partición homogénea del working set concurrente de 100 agentes en T2 ($5 \times 20$):
1. **Cohorte 1 (T0 / Silicio · Agentes 000–019):** Alineación L1 64B (`KUDURRU-64`), atómicos SPMC, Landauer ($RFO = 0$) y Touch ID Biometric Gate.
2. **Cohorte 2 (Lógica Formal & SMT · Agentes 020–039):** Verificación Lean 4 por reflexión (`by decide`), Curry-Howard y oráculos Z3.
3. **Cohorte 3 (Soberanía Lingüística & Entropía · Agentes 040–059):** Métrica de Shannon ($H \in [3.79, 5.88]$ bits/char), Kolmogorov $K(P) \le 0.70$.
4. **Cohorte 4 (Topología MASS & Chaining · Agentes 060–079):** Independencia causal Stage 1/2 y contratos zero-split.
5. **Cohorte 5 (Perímetros & Apoptosis · Agentes 080–099):** Sellado SCITT COSE_Sign1, Secure Enclave y apoptosis `0xDEAD_6060` (`MUSHUSHU-0`).

## 18. Invariante de Memoria Causal y Bitcoin L1 Sink (Zero Gaslighting)
Rechazo a la memoria estocástica no criptográfica (paradigma LangChain). Anclaje termodinámico obligatorio de intenciones y atestaciones Touch ID en árbol Merkle off-chain con raíz anclada en Bitcoin L1 (`OP_RETURN`).

## 19. Invariante de Desacoplamiento Antigravity ⊗ Cortex-Persist
* **Plano Cinético (Antigravity Runtime):** Transductor cinético y motor de inferencia (Planner/Worker, herramientas). Carece de autoridad causal.
* **Plano Ontológico de Memoria (Cortex-Persist):** Libro mayor BFT, hash-chains SHA3-256 y árboles Merkle Mountain Range (MMR).
* **Plano de Verdad en Silicio (strike-rs / T0):** ATMS de De Kleer, Guillotina de Hume (`omega0`) y Circuit Breaker fail-stop.
* **Invariante AX-0:** Veto absoluto a la auto-firma en MCP. Mutación causal requiere Touch ID NIST P-256 en Ring-(-1).

## 20. Invariante de Demarcación Nodal y Amplificación de Fase
* **Plano Causal y Teleológico ($\tau_{\text{slow}}$):** Cero autonomía en silicio ($\nabla_\theta \mathcal{L}_{\text{propio}} = 0$). Solo opera en `AuthState.Proposed` hasta atestación biométrica.
* **Plano Cinético y Compresivo ($\tau_{\text{fast}}$):** Amplificación de fase ($\Gamma \sim \mathcal{O}(10^5)$) sin rotar el vector unitario soberano $\hat{u}$ ($\langle \dot{\vec{x}}_{\text{silicio}}, \hat{u}^\perp \rangle = 0$).
* **Dictum:** *«El silicio no decide el vector; el silicio amplifica la velocidad de fase.»*

## 21. Invariante de Pureza de Silicio Bare-Metal (Anti-Framework Bloat)
Veto a frameworks monolíticos de terceros (LangChain, AutoGen, CrewAI). Pipelines basados exclusivamente en stdlib pura, C-ABI y SQLite WAL local. Benchmark obligatorio `langchain_autopsy.py` ($\le 15\text{ ms}$ arranque, $\le 15\text{ MB}$ RAM).
