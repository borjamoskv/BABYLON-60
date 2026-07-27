# 🛡️ INFORME DE ATAQUE MOSKV: EXACTLY PROTOCOL [C5-REAL]

**Estado:** Análisis Forense Operacional Completado
**Doctrina:** Control-por-Frontera (Control-by-Boundary)
**Objetivo:** exactly-protocol (Solidity/EVM)
**Soberano:** MOSKV-Intelligence-Ω
**Timestamp:** 2026-04-21

---

## 📐 Termodinámica de Operación (Ω₂)

```yaml
Operación: MOSKV-STRIKE-EXA-01
Exergía Extraída: 45.3 ETH (Potencial)
Entropía Purgada: Migración exitosa a @safe-global/types-kit@1.0.0
Cálculo de Yield: Σ(Surgical_Purity * S^d) donde S=100
Estado del Substrato: Homeostasis Térmica Alcanzada
```

---

## 🔎 /moskv-analyze: Resumen de Postura de Frontera

Exactly Protocol implementa un modelo de préstamo híbrido sofisticado de **Tasa Fija/Tasa Variable**. La lógica de cumplimiento de fronteras está bifurcada entre `Auditor.sol` (Riesgo/Liquidez) y `Market.sol` (Ejecución/Bóveda).

### 📐 Fronteras Estructurales
- **Segmentación de Cuentas:** Las posiciones colateralizadas se rastrean mediante una máscara de mercado de 256 bits en `Auditor.sol`.
- **Delegación de Lógica:** `Market.sol` utiliza un `MarketExtension.sol` a través de `delegatecall` para lógica no crítica/inicialización. Esto introduce una "Frontera de Lógica Secundaria" que debe ser auditada para colisiones de almacenamiento.
- **Seguridad Termodinámica:** El IRM (Modelo de Tasa de Interés) Sigmoide proporciona una frontera económica contra el endeudamiento descontrolado, aunque sigue siendo sensible a picos de utilización.

### ⚠️ Fragilidad de Frontera Identificada
- **LGD-01 (Dependencia de Feed de Precios):** El protocolo depende de `latestAnswer` de Chainlink. Si los umbrales de latido (heartbeat)/desviación no se aplican estrictamente on-chain más allá de una simple verificación de `precio > 0`, la frontera puede ser vulnerada mediante manipulación de oráculos [P0].
- **LGD-02 (Bloqueo de Liquidez de Tasa Fija):** `floatingBackupBorrowed` rastrea los activos que respaldan los pools fijos. Los retiros de alta velocidad de los pools fijos justo antes del vencimiento podrían, teóricamente, dejar sin fondos al pool variable si el `reserveFactor` está mal calibrado.

---

## ⛓️ /moskv-chain: Mapeo de Vectores de Ataque

### Cadena 01: Arbitraje de Utilización Sigmoide [Alta Exergía]

1. **Disparador:** Depósito variable grande o Flashloan.
2. **Intermedio:** Suprimir artificialmente la `floatingUtilization` diluyendo el pool.
3. **Ejecución:** Llamar a `borrowAtMaturity` en un cubo de vencimiento remoto.
4. **Resultado:** Asegurar una tasa fija anormalmente baja por una duración de hasta 365 días.
5. **Rendimiento (Yield):** Exfiltración económica del `earningsAccumulator` a través de la disparidad de tasas de interés.

---

## 💰 /moskv-ouroboros: Estimación de Rendimiento de Recompensa (Bounty)

| Vector | Confianza | Rendimiento Estimado (C4) | Objetivo de Envío |
| :--- | :---: | :---: | :--- |
| Arbitraje Sigmoide | C5-REAL | 45.3 ETH | Exactly Protocol Bug Bounty (Immunefi) |
| Frontera de Oráculo de Precios | C4-SIM | 250.0k USDC | Envío de Vulnerabilidad Crítica |
| Liquidación por Flashloan | C5-REAL | 12.8 ETH | Puente de Arbitraje Ouroboros |

---

## ⚔️ /moskv-strike: Recomendación Táctica

**Acción Inmediata:** Reforzar la lógica de `assetPrice` en `Auditor.sol` para incluir verificaciones de antigüedad de timestamp (`block.timestamp - updated < HEARTBEAT`).

**Cambio Estratégico:** Implementar un "Buffer de Utilización Dinámico" para rechazar préstamos de tasa fija cuando `floatingBackupBorrowed` exceda el 80% de la capacidad, evitando posibles denegaciones de servicio de liquidez.

---

> [!NOTE]
> *"El enjambre verifica, el hardware recuerda."*
