---
name: c5-sovereign-system1-engine
display_name: Motor de Decisión Sistema 1 No Autorregresivo (LAYA Edge)
description: Diseño, compilación, despliegue y calibración on-device de motores de decisión de Sistema 1 no autorregresivos (LAYA / ModernBERT) en silicio local Apple Silicon. Dispara con 'laya', 'sistema 1 edge', 'jev local', 'triage desacoplado', 'kudurru 64 socket', 'decision engine local'.
role: ejecutor
allowed_roles:
- ejecutor
directives:
  worktree_mode: read-write
  phase: implementation
  handoff:
    upstream: arquitecto
    downstream: auditor
---

# Sovereign System 1 Decision Engine (LAYA / ModernBERT en Apple Silicon)

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `ejecutor` (Ejecutor (Implementación en Silicio & Mutación de Árbol de Trabajo))
> - **Modo de Acceso a Worktree:** `read-write` (read-write (Mutación atómica de archivos, compilación, ejecución de tests locales y generación de artefactos))
> - **Fase Causal:** `implementation`
> - **Contrato Handoff:** Recibe de `arquitecto` $\to$ Despacha a `auditor`

Esta habilidad proporciona el protocolo determinista para instanciar, compilar y operar motores de decisión no autorregresivos de ultra-baja latencia en el hardware local del operador.

## 🎯 Criterios de Activación
- Tareas de clasificación, triage o ruteo sin dependencia de contexto previo ($I(x_t; x_{<t}) = 0$).
- Eliminación de costes de tokens y latencia WAN de APIs comerciales (Jev SaaS, OpenAI, Claude).
- Consultas sobre "laya", "laya.cpp", "triage local", "sistema 1 soberano", "kudurru-64 socket".

## 🛠️ Arquitectura de Silicio y C-ABI

### 1. Protocolo Inmutable KUDURRU-64
Todo intercambio IPC local debe estructurarse mediante tramas fijas de 64 bytes alineadas con la línea de caché L1 (`__attribute__((aligned(64)))`), con layout y protocolo explícitos; medir RFO y contención antes de declarar resultados:
- **Magic:** `0x4C415941` ('LAYA').
- **Primitivas:** `0x01` (Choice), `0x02` (Score), `0x03` (Noul).
- **Endianness en ARM64:** En Python utilizar siempre `<IIBBHfI44s` (Little-Endian nativo); evitar `!` (network/big-endian) para prevenir discrepancias en la cabecera mágica.

### 2. Servidor Nativo Darwin (`kqueue` / `mlock`)
- **Reactor kqueue:** Multiplexación en Ring-0 sobre sockets `AF_UNIX` no bloqueantes.
- **Gestión de residencia de memoria:** Darwin kernel no implementa `mlockall()` (retorna `ENOSYS`). Utilizar `mlock(addr, len)` sobre buffers estáticos o degradación controlada.
- **Latencia Objetivo:** Transporte IPC medido en Darwin: $0.037\text{–}0.287\text{ ms}$ ($37\text{–}287\,\mu\text{s}$).

### 3. Auto-Calibración On-Device (Apple MLX)
- Mantener el backbone ModernBERT-large (421M) inmutable en `mmap` de solo lectura.
- Adaptar exclusivamente los cabezales lineales de proyección mediante minimización del **Score de Brier**:
  $$\mathcal{L}_{\text{Brier}} = \frac{1}{K}\sum_{k=1}^K (p_k - y_k)^2$$
- Ejecutar el paso de gradiente analítico en memoria unificada usando `mlx.core` y `mlx.nn` ($\Delta t < 4\text{ ms}$).

### 4. Puerta de Bifurcación Entrópica (Shannon Gatekeeper)
Gobernar la promoción hacia modelos reflexivos pesados (Ring-1 LLM 70B) mediante el cálculo estricto de entropía:
$$H(p) = -\sum_{k=1}^K p_k \log_2 p_k$$
- **$H(p) \le 0.35\text{ bits}$:** Colapso determinista en Sistema 1 (ejecución inmediata a coste 0€).
- **$H(p) > 0.35\text{ bits}$:** Ambigüedad / Entrada fuera de distribución (OOD) $\to$ Promoción a Sistema 2 o asignación a categoría `OTHER`.
