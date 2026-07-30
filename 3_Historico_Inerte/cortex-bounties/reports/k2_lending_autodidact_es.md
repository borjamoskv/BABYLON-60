# Módulo de Aprendizaje Autodidacta – K2 Lending Bypass del Factor de Cierre (C4)

## 1️⃣ Visión General
La vulnerabilidad **Bypass del Factor de Cierre** (C4) permite a un atacante abrir un préstamo con colateral insuficiente al explotar una condición de carrera entre la contabilización de salidas pendientes del vault y la verificación del balance al abrir el préstamo. El protocolo sobreestima el colateral del prestatario, habilitando un sobre‑préstamo y la extracción de valor.

## 2️⃣ Modelo de Amenaza
| Actor | Capacidad | Objetivo |
|-------|-----------|----------|
| **Atacante (EOA)** | Puede llamar a `requestExit`, `openLoan` y a cualquier función pública del vault dentro del mismo bloque. | Inflar el colateral efectivo, evadir el factor de cierre y extraer fondos excedentes. |
| **Protocolo** | Rastrea depósitos mediante `vaultAccountedBalance` y `inFlightExitingAmount` en almacenamiento por epoch. | Garantizar solvencia y aplicar el límite del factor de cierre.

## 3️⃣ Fallo Lógico Central
- El vault registra una *salida pendiente* (`inFlightExitingAmount`) que solo se reconcilia al final del epoch.
- `K2Lending.openLoan` verifica una **instantánea** de `vaultAccountedBalance` **antes** de que la salida pendiente sea deducida.
- Cuando `requestExit` y `openLoan` se ejecutan en el mismo bloque, el préstamo pasa la verificación usando el balance obsoleto, mientras que la salida pendiente reduce el colateral real después.

## 4️⃣ Pasos de Explotación (un solo agente)
```solidity
// 1. Depositar colateral
vault.deposit{value: 10 ether}();

// 2. Programar una pequeña salida (p.ej., 0.1 ether)
vault.requestExit(0.1 ether);

// 3. En el mismo bloque, abrir un préstamo usando el balance desactualizado
k2Lending.openLoan({borrowAmount: 5 ether}); // pasa la verificación del factor de cierre

// 4. Tras el bloque, la salida pendiente se reconcilia, reduciendo el colateral a 9.9 ether
//    El préstamo queda sub‑colateralizado (5 ether prestados contra 4.95 ether efectivo).
```
Ejecutar lo anterior en una sola transacción (o usando un wrapper estilo flash‑loan) genera beneficio sin riesgo de liquidación.

## 5️⃣ Amplificación con Múltiples Agentes
Desplegar **N** agentes paralelos (p. ej., 100) que realicen los pasos anteriores en el mismo bloque. La ganancia total escala linealmente:
```
Beneficio_por_agente ≈ 0.05 ether → Beneficio_total = 0.05 ether × N
```
Con **N = 100**, el beneficio ≈ 5 ether (~$8 k).

## 6️⃣ Mitigaciones (Inserción de Guardas Determinísticas)
1. **Sincronizar la Lectura del Balance** – Llamar a `vault.processPendingExits()` **antes** de cualquier instantánea de balance en `openLoan`.
2. **Préstamo Atómico Salida‑Préstamo** – Implementar un wrapper `safeBorrow(uint256 amount)` que realice `requestExit → processPendingExits → openLoan` de forma atómica.
3. **Guardia de Re‑entrada** – Aplicar el modificador `nonReentrant` a todos los puntos de entrada públicos del vault.
4. **Aserción basada en Eventos** – Emitir `VaultSyncViolation(address atacante, uint256 before, uint256 after)` si se detecta una discrepancia de balance.

## 7️⃣ Suite de Pruebas (Foundry)
- **`test/CloseFactorBypass.t.sol`** – Desplegar un fork del mainnet con el contrato exacto (`0xE31b…4817`).
- Usar `vm.prank` para simular 100 agentes en un solo bloque.
- Afirmar que la ganancia antes de la mitigación sea `> 0` y después de aplicar los guardas sea `== 0`.

## 8️⃣ Referencias
- **Auditoría K2 Lending** – Envío a Code4rena (2026‑04‑K2).
- **StakingVaultOperations.sol** – Líneas 120‑149 (lógica de salida pendiente) y 210‑224 (lectura de balance).
- **EIP‑2535 (Diamond) Proxy** – Interacción vía `delegatecall`/`ERC‑7201`.

---
*Este módulo autodidacta está pensado para facilitar la auto‑educación rápida y la replicación del análisis de vulnerabilidad.*
