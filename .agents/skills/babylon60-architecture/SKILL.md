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
- Remitente oficial: `soporte@babylon60.com`.
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
