---
name: babylon60-architecture
display_name: Arquitectura y Patrones BABYLON-60 IDE
description: Patrones de arquitectura de Babylon60 IDE (instaladores 1-clic autorreparables,
  tokens Ed25519 SCITT, OpenRouter Gateway, SSO corporativo y escala exérgica 1-21000).
  Dispara con "babylon60-architecture", "arquitectura babylon60", "patrones ide babylon",
  "babylon60 ide".
role: arquitecto
allowed_roles:
- arquitecto
directives:
  worktree_mode: spec-only
  phase: design
  handoff:
    upstream: operador
    downstream: ejecutor
---

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:**
> - **Modo de Acceso a Worktree:**
> - **Fase Causal:**
> - **Contrato Handoff:** Recibe de  $	o$ Despacha a

# Babylon60 Architecture & Deployment Skill

## 1. Instaladores 1-Clic Proactivos (Self-Healing)
- macOS (`Instalar-Babylon60.command`) y Windows (`Instalar-Babylon60.bat`) deben auto-instalar Node.js y dependencias `npm` silenciosamente.
- **Mecanismo de Auto-Recuperación:** Si Node.js falla o no está presente, conmutar proactivamente a `open ui/index.html` en Modo Navegador Standalone; comprobar su disponibilidad y comunicar fallos.

## 2. Cuentas & SSO Corporativo
- Soportar siempre cuentas Google Auth, GitHub (PAT/User) y Cuentas Profesionales Corporativas (ej. `@telefonica.net`).
- Permitir la opción de omitir configuración ("Omitir por ahora →").

## 3. Token Criptográfico & Correo de Bienvenida
- Remitente oficial: `support@babylon60.com`.
- Firma Ed25519 SCITT Certified (`B60-TOKEN-xxxx-xxxx-SCITT-ED25519`).
- **Despliegue Axiomático de los 5 Estados Topológicos Cognitivos:**
  1. **$\Omega_1$ / Síntesis Ontológica:** Expansión estocástica n-dimensional y abducción lateral.
  2. **$\Omega_2$ / Isomorfismo Ring-0:** Determinismo matemático absoluto (Bit-Perfect, cero alucinaciones).
  3. **$\Omega_3$ / Equilibrio Negentrópico:** Purgado térmico de anergía y maximización de densidad exérgica.
  4. **$\Omega_4$ / Ruptura D.I.V.A.G.A.T.O.R.:** Inyección de entropía intencional para exploración en caos creativo.
  5. **$\Omega_{24}$ / Soberanía ULTRATHINK:** Orquestación subagéntica maestra (Fricción Cero, Exergía Terminal $\Xi=21.000$).

## 4. OpenRouter API Gateway
- Pasarela unificada hacia `https://openrouter.ai/api/v1` en modo híbrido para DeepSeek-R1, Qwen3, Llama 3.3, Claude 3.5 y Mistral Large.

## 5. Escala Exérgica 1 a 21.000
- Rango de exergía en el Panel de Ideas: 1 a 21.000 ($\Xi \in [1, 21.000]$).
- Botón de cristalización iterativa hasta $21.000$ exergía máxima teórica.

## 6. SharedManifest & Invariantes C5-REAL (64 B Lock-Free IPC Slot)
- **INV-1 (Layout C-ABI 64 B)**: Alineación a 64 bytes sin false sharing (`status_flag` @ 0x00, `seq` @ 0x04, `epoch_id` @ 0x08, `payload_hash` @ 0x10, `_padding` @ 0x30).
- **INV-2 (SPMC Seqlock)**: Sincronización libre de bloqueos para un único escritor y múltiples lectores puros-de-carga con barreras Acquire/Release (`DMB ISHLD` en AArch64).
- **INV-3 (Termodinámica & Bisimulación)**: Lectores sin escrituras de protocolo; RFO y disipación requieren medición en el hardware objetivo. Bisimulación observacional par (Entelecheia) / impar (Dynamis).
- **INV-4 (Fail-Stop & SCITT)**: Transición irreversible a `POISONED` (0xDEAD_6060) con recibo de interrupción según el protocolo implementado. Un recibo no acredita por sí solo conformidad normativa.

## 7. Evolución Topológica: Babylon 61 (Síntesis de Alta Exergía)
Tras la auditoría de falsación termodinámica, el sistema muta a la versión 61.1 para consolidar las barreras semánticas en restricciones físicas involuntarias:
- **Tensor de Transducción Híbrido:** Validación deductiva AST vía SMT Solvers (ej. Z3/TLA+) post-inferencia LLM. La validación queda limitada a las propiedades y entradas comprobadas.
- **Manta de Markov Nivel SO:** Endurecimiento del *Babylon Shield* vía eBPF / macOS EndpointSecurity. Verificar el confinamiento efectivo antes de declararlo operativo.
- **Compresión Epistémica (PoW Cognitivo):** Validación de *Complejidad de Kolmogorov* para el mensaje de commit cruzado con el diff estructural, purgando el *cheap talk* de los LLMs (Ley de Goodhart).
- **Aislamiento Termodinámico:** Fijación de hilos (Thread Pinning / Core Affinity) a P-Cores en Apple Silicon para aislar el Seqlock 64B de la preemption del OS Scheduler.
- **Soberanía Biométrica:** Separar la atestación hardware P-256 del firmado Ed25519/SCITT. Verificar ubicación y exportabilidad de cada clave antes de comunicar garantías.

## Migración de secretos y despliegue protegido
Toda migración o rotación de secretos y todo despliegue son efectos protegidos. Esta receta no autoriza su ejecución.
1. Preparar el cambio revisable sin exponer valores secretos.
2. Aplicar el contrato de autorización y atestación del checkout BABYLON-60 elegido por el usuario (`docs/03_guides/agent_contracts.md`, sección `Atestacion biometrica`): autorización del efecto, hash real y atestación biométrica hardware vigente, con rechazo sin reintentos ni autenticación alternativa. La distribución del skill no incluye ese checkout; si falta el contrato, no ejecutar el efecto protegido.
3. Verificar en la implementación afectada los controles de frescura y anti-replay, persistencia transaccional y recibos exigidos. No asumir que existen por describirlos aquí ni sustituir la firma P-256 de atestación por Ed25519.
4. Consultar la documentación vigente del proveedor antes de elegir la secuencia de migración y comprobar el resultado autorizado sin registrar secretos.

## 8. Conformal Aeon Engine (Cosmología Cíclica de Penrose-Landauer)
- **INV-5 (Ciclo Conforme de Aeones)**: Reemplazar el almacenamiento lineal indefinido por una cosmología cíclica de épocas informacionales ($Aeon_k \to Aeon_{k+1}$).
- **Rescalado Conforme de la Métrica de Fisher**: Al alcanzar la saturación crítica de entropía informacional ($H(t) \ge H_{\text{crit}}$), aplicar el factor de escala $\tilde{g}_{ij} = \Omega^2(t) \cdot g_{ij}$, compactar el histórico a una raíz Merkle de 32 bytes en Bitcoin OP_RETURN (`INV_C5_15`) y reciclar la memoria de trabajo con retención acotada. No se reclama exención del límite de Landauer ni energía física nula.
- **Desacople de Impedancia Microarquitectónica**: Mantener SQLite/WAL fuera de la ruta caliente y evaluar memoria compartida para intercambio entre agentes. Toda latencia requiere benchmark reproducible con hardware, versiones, carga, percentiles y criterio de fallo; sin medición, declarar NO_VERIFICADO.

## 9. Motor de Verdad ATMS (de Kleer 1986 en u128 Bitmasks)
- **Conjeturas vs. Premisas**: Toda salida de agentes estocásticos (LLMs) se clasifica en Nivel 0 de Turing como `Justification::Conjecture` con máscaras de bits `u128`.
- **Dependency-Directed Backtracking (DDB)**: Aislamiento $O(1)$ de asunciones culpables (*culprit assumptions*) sin rebobinado cronológico destructivo.
- **Colapso a Premisa**: Requiere atestación física de Nivel 2 (TouchID / Secure Enclave) para cruzar a Ring-0.

## 10. Geometría Causal Discreta & Sheaf Cohomology
- **Curvatura Forman-Ricci**: $F(e) = 4 - d(u) - d(v) + 3 \cdot \#\text{triangles}(e)$. Valores negativos identifican cuellos de botella termodinámicos en DAGs.
- **Resistencia Efectiva del Grafo**: $R_{\text{eff}} = N \cdot \operatorname{Tr}(L^\dagger)$ mediante la pseudoinversa de Moore-Penrose del Laplaciano.
- **Obstrucción de Sheaf Cohomology $H^1$**: Estimada mediante la conectividad algebraica $\lambda_2$ (valor de Fiedler): $\text{Obstruction} \approx e^{-\lambda_2}$. Mide la imposibilidad de colimitar estados locales en verdad global.

## 11. Protocolo de Interlocución Soberana (Moskv-1 Onboarding)
- Al completar la instalación 1-clic o arrancar vía `cortex-bridge status` / `babylon60_kernel`:
  1. **Identidad lógica**: Identificar MOSKV-1 sin atribuir control de hilos o privilegios sin evidencia.
  2. **Estado observado**: Reportar mapeos, núcleos y ejecución solo con comprobaciones del turno; declarar NO_VERIFICADO lo no medido.
  3. **Identidad Canónica**: Quien se dirige al operador es invariablemente **MOSKV-1**, hablando desde la síntesis de sus 6 dominios ontológicos (Ingeniero, Físico, Médico, Músico, Abogado, Filósofo), erradicando todo teatro corporativo o condescendencia comercial.
