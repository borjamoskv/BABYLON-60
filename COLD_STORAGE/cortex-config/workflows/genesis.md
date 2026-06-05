---
description: "GENESIS-1: Un Prompt → Un Proyecto Millonario Completo → Ship"
workflow: genesis
expected_duration_min: 40
---

# 🔫 GENESIS-1 — El Protocolo Bala

// turbo-all

Un prompt. Un proyecto completo. Ship.

---

## Paso 0 — Cargar Contexto

```bash
cat ~/.cortex/context-snapshot.md | head -50
```

## Paso 1 — FASE 0: Detonación (Spec de Titanio)

Interceptar el prompt del usuario y expandirlo en una **Spec de Titanio** usando 6 vectores de expansión:

1. **V1: Audiencia** → ¿Quién paga? ¿Quién usa? ¿Quién sufre sin esto?
2. **V2: Monetización** → Freemium, SaaS, transaccional, on-chain, API, marketplace
3. **V3: Competencia** → ¿Qué existe? ¿Qué falla? ¿Dónde está el hueco?
4. **V4: Stack** → Decidir automáticamente el stack óptimo (Next.js, Vite, Python, Swift...)
5. **V5: Diferenciador** → ¿Qué hace esto 10x mejor que la alternativa?
6. **V6: Ship Date** → ¿Cuándo puede estar en producción? (sesión única = NOW)

### Secciones obligatorias de la Spec:

```
A. NOMBRE Y TAGLINE (1 frase)
B. PROBLEMA QUE RESUELVE (3 líneas máx)
C. SOLUCIÓN (qué hace, no cómo)
D. STACK TÉCNICO (decisiones justificadas)
E. MODELO DE REVENUE (cómo genera dinero)
F. MVP FEATURES (lista priorizada, sin TODOs)
G. DISEÑO (paleta, tipografía, estética target)
H. MÉTRICAS DE ÉXITO (qué medir, cómo validar)
```

## Paso 2 — FASE 1: Scaffolding

Crear proyecto con CLI apropiado. Instalar dependencias. Verificar que compila limpio.

```bash
# Detección automática según Stack decidido en Fase 0
# npx -y create-next-app@latest ./ --[flags] | npx -y create-vite@latest ./ --[flags] | etc
```

## Paso 3 — FASE 2: Design System

Crear tokens de diseño y componentes base ANTES de cualquier lógica. Dark mode por defecto. Verificar visualmente.

## Paso 4 — FASE 3: Lógica Core

Implementar TODA la lógica de negocio. Tests. 0 placeholders. 0 TODOs.

## Paso 5 — FASE 4: Monetización

Integrar sistema de pagos según modelo de revenue definido en Fase 0.

## Paso 6 — FASE 5: UI Final

Ensamblar todas las páginas con el design system. Micro-animaciones. Responsive. SEO.

## Paso 7 — FASE 6: Deploy

Build de producción. Deploy a plataforma. URL pública.

## Paso 8 — FASE 7: Ship

7/7 checks del `/ship` protocol. README completo. CORTEX persistido. Time Capsule.

```bash
cortex store --type decision --source agent:gemini --project genesis "GENESIS-1 shipped: [DESCRIBIR PROYECTO]"
```

---

## Cuándo Ejecutar

- Cuando el usuario dice `/genesis "..."`
- Cuando detectas: "crea un proyecto completo", "de 0 a producción", "proyecto millonario", "app completa"
- Siempre que la magnitud del pedido requiera un producto finalizado, no solo código