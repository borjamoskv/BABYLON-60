---
name: c5_sovereign_antigravity_invariant
description: Preferencia local-first para orquestación continua; aplicar decisiones arquitectónicas al componente y verificar persistencia y rendimiento.
trigger: "model_decision"
---

# Invariante de Antigravedad Soberana y Persistencia 24/7 (INV_C5_SOVEREIGN_ANTIGRAVITY)

- **Ámbito:** diseño o evaluación de orquestación persistente. Local-first es una preferencia del proyecto, no una prohibición general de cloud ni evidencia de ausencia de telemetría. Elegir según requisitos, datos, coste y autorización de la tarea.
- **Arquitectura:** conservar Rust en los componentes del kernel y daemons que tengan esa decisión arquitectónica. No imponerlo a cualquier automatización; el lenguaje y las colas lock-free no prueban latencia ni consumo.
- **Persistencia macOS:** preferir `launchd` para servicios locales que deban integrarse con macOS. Comprobar inicio, reinicio, sesión y permisos en el entorno objetivo; un `.plist` por sí solo no demuestra continuidad 24/7 ni acceso a Touch ID. Configurar o instalar un servicio requiere alcance autorizado y los controles aplicables.
- **Aceptación:** para rendimiento, registrar hardware, carga, configuración, muestra y percentiles p50/p99/p99.9; distinguir memoria de persistencia síncrona. Para disponibilidad, probar recuperación y documentar dependencias de alimentación y sesión. Declarar desconocidos los datos no expuestos.
- **Efectos protegidos:** aplicar el [contrato de atestación](../../docs/03_guides/agent_contracts.md#atestacion-biometrica); este perfil no autoriza despliegues.
