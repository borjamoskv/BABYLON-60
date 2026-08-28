<!-- C5-REAL EXERGY CERTIFIED -->
# AGENTS.archi — Sovereign Agentic Architecture Registry (C5-REAL APEX)

> **AGENTS.archi is the definitive hub for multi-agent design patterns, CORTEX protocols, and Industrial Noir AI infrastructure.**
> Verifiable agentic safety, formal specification, and cryptographic proof of execution.

> [!WARNING]
> **ENTORNO DE INVESTIGACIÓN & PRUEBA DE CONCEPTO (EXPERIMENTAL STATUS)**
> AGENTS.archi opera actualmente como un **laboratorio experimental activo de investigación**. La pasarela de pago (Stripe PWYW) se encuentra **activa** para la canalización de donaciones y soporte al desarrollo de la investigación C5-REAL, **sin que la plataforma se encuentre en condiciones de ofrecer o prestar servicios comerciales de auditoría en producción**.

---

## ⬡ Arquitectura del Registro Soberano

AGENTS.archi implementa una interfaz web industrial (*Industrial Noir 2026*) alimentada por funciones sin servidor (Cloudflare Pages Functions) y motores de verificación síncronos en local/Edge.

```
                                  ┌─────────────────────────────────────────┐
                                  │      AGENTS.archi Web Interface         │
                                  └────────────────────┬────────────────────┘
                                                       │
                   ┌───────────────────────────────────┼───────────────────────────────────┐
                   │                                   │                                   │
                   ▼                                   ▼                                   ▼
      ┌─────────────────────────┐         ┌─────────────────────────┐         ┌─────────────────────────┐
      │  ASL Formal Sandbox     │         │   Architect's Swarm     │         │  Evidence Ledger        │
      │  (Z3 / CF-GKAT Engine)  │         │   (100 Helper Agents)   │         │  (SHA3-256 Merkle Tree) │
      └────────────┬────────────┘         └────────────┬────────────┘         └────────────┬────────────┘
                   │                                   │                                   │
                   └───────────────────────────────────┼───────────────────────────────────┘
                                                       │
                                                       ▼
                                      ┌─────────────────────────────────┐
                                      │   Stripe PWYW Checkout Session  │
                                      │   (Active Sandbox Contribution) │
                                      └─────────────────────────────────┘
```

### 1. Núcleos de Verificación & Componentes UI
- **ASL Formal Verification Sandbox ([aslSandbox.js](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/src/agents-archi/src/components/aslSandbox.js))**: Entorno de ejecución en navegador para la validación de invariantes agenticas mediante especificaciones en álgebra CF-GKAT y reducción SMT/Z3.
- **Architect's Swarm ([architectSwarm.js](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/src/agents-archi/src/components/architectSwarm.js))**: Orquestación visual de 100 agentes auxiliares autónomos ejecutados en híper-paralelo con telemetría de memoria, estrés y tasa de cristalización.
- **Evidence Ledger ([evidenceLedger.js](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/src/agents-archi/src/components/evidenceLedger.js))**: Registro inmutable de auditorías forenses respaldado por árboles de Merkle SHA3-256 y sellado SCITT.
- **Sovereign Council & Genesis Oscilloscope ([sovereignCouncil.js](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/src/agents-archi/src/components/sovereignCouncil.js))**: Monitorización de estado termodinámico (Entropía, Consonancia Armónica Ω₆₄ y Ruido Térmico en dB).
- **Nexus Graph ([nexusGraph.js](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/src/agents-archi/src/components/nexusGraph.js))**: Visualización topológica de la base de conocimiento unificada submodular.

### 2. Pasarela de Cobros & Intake (Cloudflare Pages Functions)
- **`/api/create-checkout-session` ([create-checkout-session.js](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/src/agents-archi/functions/api/create-checkout-session.js))**: Integración con Stripe Checkout (USD PWYW — *Pay-What-You-Want*). Permite aportaciones desde 1 USD (o donación libre 0 USD vía bypass local).
- **`/api/audit-request` ([audit-request.js](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/src/agents-archi/functions/api/audit-request.js))**: Canalización atómica de briefs forenses con generación local de firmas criptográficas `ARCHI-YYYYMMDD-[HASH]` y fallback automático a mailto diferido.

---

## ⚡ Invariantes Termodinámicos (C5-REAL)

1. **Exergía Máxima (Zero Anergy)**: Cero capas ornamentales ni código reactivo ineficiente. Componentes modulares Vanilla JS/CSS con micro-glassmorphism renderizados a 60 FPS mediante canvas directos de silicio.
2. **Modo Experimento Explícito**: Ninguna transacción o interacción en la plataforma presupone un contrato de prestación de servicio comercial. La pasarela Stripe canaliza fondos de apoyo al laboratorio.
3. **Bisimulación Observacional**: La equivalencia entre especificaciones ASL y la conducta del agente se evalúa mediante trazas de estados discretos sin suposiciones de gradiente continuo (`st: *R → R`, `H(X) < ε`).

---

## 🛠️ Despliegue Local & Desarrollo

### Requisitos Previos
- Node.js ≥ 20.x
- Cloudflare Wrangler CLI (para Functions locales)

### Inicialización Sincrónica
```bash
# Clonar el repositorio
git clone https://github.com/borjamoskv/agents-archi.git
cd agents-archi

# Instalar dependencias
npm ci

# Servidor de desarrollo local (Vite)
npm run dev
```

### Emulación de API Serverless (Stripe & Intake)
```bash
# Ejecutar funciones Cloudflare Pages localmente con variables de entorno
npx wrangler pages dev . --binding STRIPE_SECRET_KEY="sk_test_..."
```

---

## 📜 Licencia & Gobernanza

Desarrollado bajo los estándares de **CORTEX PERSIST FOUNDATION**.

- **Autor / Investigador Principal:** Borja Moskv (`@borjamoskv`)
- **Runtime de Inferencia Protegido:** [BABYLON60](https://babylon60.com)
