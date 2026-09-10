---
name: babylon60-architecture
description: Patrones de arquitectura de Babylon60 IDE (instaladores 1-clic autorreparables, tokens Ed25519 SCITT, OpenRouter Gateway, SSO corporativo y escala exérgica 1-21000).
---

# Babylon60 Architecture & Deployment Skill

## 1. Instaladores 1-Clic Proactivos (Self-Healing)
- macOS (`Instalar-Babylon60.command`) y Windows (`Instalar-Babylon60.bat`) deben auto-instalar Node.js y dependencias `npm` silenciosamente.
- **Mecanismo de Auto-Recuperación:** Si Node.js falla o no está presente, conmutar proactivamente a `open ui/index.html` en Modo Navegador Standalone (0 errores garantizado).

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
- **INV-3 (Termodinámica & Bisimulación)**: Cero RFO en lectores; disipación de anergía colapsada a cero. Bisimulación observacional par (Entelecheia) / impar (Dynamis).
- **INV-4 (Fail-Stop & SCITT)**: Transición irreversible a `POISONED` (0xDEAD_6060) emitiendo recibo de interrupción firmada COSE_Sign1 conforme a RFC 9942 / SCITT para cumplimiento del EU AI Act (Arts. 12, 14(4), 15 y 50).

## 7. Evolución Topológica: Babylon 61 (Síntesis de Alta Exergía)
Tras la auditoría de falsación termodinámica, el sistema muta a la versión 61.1 para consolidar las barreras semánticas en restricciones físicas involuntarias:
- **Tensor de Transducción Híbrido:** Validación deductiva AST vía SMT Solvers (ej. Z3/TLA+) post-inferencia LLM. Cero alucinaciones inyectadas.
- **Manta de Markov Nivel SO:** Endurecimiento del *Babylon Shield* vía eBPF / macOS EndpointSecurity. Bloqueo Ring-0 real independiente del IDE.
- **Compresión Epistémica (PoW Cognitivo):** Validación de *Complejidad de Kolmogorov* para el mensaje de commit cruzado con el diff estructural, purgando el *cheap talk* de los LLMs (Ley de Goodhart).
- **Aislamiento Termodinámico:** Fijación de hilos (Thread Pinning / Core Affinity) a P-Cores en Apple Silicon para aislar el Seqlock 64B de la preemption del OS Scheduler.
- **Soberanía Biométrica:** Firma SCITT aislada completamente en el Secure Enclave Processor (TouchID), cero exposición de clave Ed25519 en RAM.

## 8. Protocolo de Soberanía en Cloudflare (Prevención Error 10053)
**Transición de Secretos Wrangler (Zero-Trust):** Para sustituir una variable de entorno en texto plano (en `wrangler.toml` bajo `[vars]`) por un secreto cifrado, el agente DEBE seguir esta secuencia estricta o colapsará con el *Error 10053*:
1. Eliminar la variable del `wrangler.toml`.
2. Ejecutar `npx wrangler deploy` para sincronizar y purgar la caché de variables en el *edge*.
3. Ejecutar `npx wrangler secret put <KEY>` (vía `stdin`) para inyectar la carga criptográfica definitiva.

## 8. Conformal Aeon Engine (Cosmología Cíclica de Penrose-Landauer)
- **INV-5 (Ciclo Conforme de Aeones)**: Reemplazar el almacenamiento lineal indefinido por una cosmología cíclica de épocas informacionales ($Aeon_k \to Aeon_{k+1}$).
- **Rescalado Conforme de la Métrica de Fisher**: Al alcanzar la saturación crítica de entropía informacional ($H(t) \ge H_{\text{crit}}$), aplicar el factor de escala $\tilde{g}_{ij} = \Omega^2(t) \cdot g_{ij}$, compactar el histórico a una raíz Merkle de 32 bytes en Bitcoin OP_RETURN (`INV_C5_15`) y reiniciar la memoria de trabajo a costo de Landauer cero.
- **Desacople de Impedancia Microarquitectónica**: Sustituir el cuello de botella de disco SQLite WAL ($5\text{ ms}$) por túneles POSIX Shared Memory / Iceoryx2 ($12\text{ ns}$) acoplados directamente al `SharedManifest` de 64 bytes para intercambio de estado inter-agente.

## 9. Motor de Verdad ATMS (de Kleer 1986 en u128 Bitmasks)
- **Conjeturas vs. Premisas**: Toda salida de agentes estocásticos (LLMs) se clasifica en Nivel 0 de Turing como `Justification::Conjecture` con máscaras de bits `u128`.
- **Dependency-Directed Backtracking (DDB)**: Aislamiento $O(1)$ de asunciones culpables (*culprit assumptions*) sin rebobinado cronológico destructivo.
- **Colapso a Premisa**: Requiere atestación física de Nivel 2 (TouchID / Secure Enclave) para cruzar a Ring-0.

## 10. Geometría Causal Discreta & Sheaf Cohomology
- **Curvatura Forman-Ricci**: $F(e) = 4 - d(u) - d(v) + 3 \cdot \#\text{triangles}(e)$. Valores negativos identifican cuellos de botella termodinámicos en DAGs.
- **Resistencia Efectiva del Grafo**: $R_{\text{eff}} = N \cdot \operatorname{Tr}(L^\dagger)$ mediante la pseudoinversa de Moore-Penrose del Laplaciano.
- **Obstrucción de Sheaf Cohomology $H^1$**: Estimada mediante la conectividad algebraica $\lambda_2$ (valor de Fiedler): $\text{Obstruction} \approx e^{-\lambda_2}$. Mide la imposibilidad de colimitar estados locales en verdad global.

