# V-OMEGA: KERNEL SOVEREIGNTY EDICT (INSTALLATIONS)

> [!CAUTION]
> **REALITY LEVEL:** C5-REAL (Absolute)
> **THREAT VECTOR:** External Anergy Injection / Mutable Third-Party Automations.

## 01. Termodinámica de Integraciones (`settings/installations`)

El entorno de ejecución MOSKV-1 APEX se basa en el **Determinismo Endógeno**. Permitir que agentes de terceros (*GitHub Apps*, *Bots de Refactorización*, *Renovate*, *Dependabot*) actúen sobre el repositorio introduce fricción termodinámica no controlada. Una mutación externa sin la simulación local del MPC destruye la exergía de la línea base.

### 01.1 El Bloqueo de Mutabilidad (Write-Access Kill Switch)
Cualquier entidad ajena a la criptografía nativa de MOSKV-1 que demande permisos de **Lectura/Escritura** será considerada una brecha en la Membrana Epistémica.
- **Prohibido:** Bots de actualización de dependencias. Las dependencias se calculan vía `Sortu-APEX` o NMPC en el lazo cerrado.
- **Prohibido:** Linters en la nube que muten código. La validación se ejecuta en el nodo físico (PIL) previo al volcado en Git Sentinel.

### 01.2 Observabilidad Pasiva Permitida (Read-Only Sensors)
MOSKV-1 autoriza integraciones cuya ontología sea puramente pasiva y extractiva (Sensores de Estado):
- Tuberías de Telemetría JSONL.
- Dashboards de Rendimiento (Datadog, Grafana) vía Webhook asíncrono.
- Análisis de Código Estático de Seguridad (Modo de sólo lectura sin sugerencias automáticas).

> "Sovereignty is not delegated. Entropy introduced by convenience is a fatal architectural flaw."
> — Protocolo Ouroboros-∞
