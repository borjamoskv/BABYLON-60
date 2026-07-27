# AUTOPSIA C5-RECON: Spark ALM Controller — Deep Forensic Audit

> *CORTEX Forensics · Target: Spark/MakerDAO · Bounty: $5M (Immunefi) · Zero-Rhetoric Mandate*

## 1. METADATA
- **Protocolo:** Spark ALM Controller (Solidity ^0.8.21 / Foundry)
- **Ecosistema:** MakerDAO/Sky — Spark Liquidity Layer
- **TVL Estimado:** Alto (custodia directa de USDC, USDS, DAI, wstETH, weETH, sUSDe, USTB)
- **Bounty Program:** Immunefi — Hasta **$5,000,000** por vulnerabilidad crítica en Smart Contracts
- **Auditorías Previas:** 21 reportes (Cantina, ChainSecurity, Certora) desde v1.0.0 hasta v1.9.0
- **Contratos Core:** `ALMProxy`, `MainnetController`, `ForeignController`, `RateLimits`, `OTCBuffer`
- **Librerías:** `ERC4626Lib`, `CurveLib`, `UniswapV4Lib`, `PSMLib`, `CCTPLib`, `AaveLib`, `WEETHLib`, `LayerZeroLib`, `ApproveLib`

## 2. ARQUITECTURA (Superficie de Ataque)

```
   Relayer (UNTRUSTED)
       │
       ▼
  MainnetController / ForeignController
       │                    │
       ▼                    ▼
   RateLimits           ALMProxy ──────▶ External Protocols
   (State Store)    (Funds Custody)       (Sky, PSM, Aave,
                                           Curve, UniV4,
                                           Ethena, EtherFi,
                                           Maple, Superstate,
                                           LayerZero, CCTP)
```

**Modelo de Confianza:**
- `DEFAULT_ADMIN_ROLE` (Governance): **Totalmente confiable**
- `RELAYER`: **ASUMIDO COMPROMETIDO** — Todo el diseño gira en torno a que un Relayer puede ser malicioso
- `FREEZER`: Puede revocar Relayers comprometidos

**Invariantes de Seguridad Declarados:**
1. Los fondos NUNCA salen del sistema (solo a direcciones whitelisted)
2. Las pérdidas están acotadas por los Rate Limits
3. El Freezer SIEMPRE puede detener ataques
4. Solo integraciones configuradas por Governance funcionan (Rate Limit Keys = Whitelist)

## 3. VECTORES ANALIZADOS — HALLAZGOS

### Vector A: OTC Swap — Recharge Rate Timing Attack ⚠️ (MEDIUM-HIGH)

**Ubicación:** `MainnetController.sol:1094-1167`

**Observación Crítica:** La función `isOtcSwapReady()` (L1161-1167) determina si un OTC swap anterior ha sido "completado" usando una fórmula basada en tiempo:

```solidity
function getOtcClaimWithRecharge(address exchange) public view returns (uint256) {
    OTC memory otc = otcs[exchange];
    if (otc.sentTimestamp == 0) return 0;
    return otc.claimed18 + (block.timestamp - otc.sentTimestamp) * otc.rechargeRate18;
}

function isOtcSwapReady(address exchange) public view returns (bool) {
    if (maxSlippages[exchange] == 0) return false;
    return getOtcClaimWithRecharge(exchange)
        >= otcs[exchange].sent18 * maxSlippages[exchange] / 1e18;
}
```

**Problema Potencial:** El `rechargeRate18` permite que un swap se considere "completado" sin que el exchange haya devuelto los fondos realmente. Si `rechargeRate18` es demasiado alto, un Relayer comprometido puede:
1. Ejecutar `otcSend()` enviando fondos al exchange
2. Esperar que el tiempo de recarga transcurra (sin que el exchange devuelva nada)
3. Ejecutar otro `otcSend()` porque `isOtcSwapReady()` retorna `true`
4. Repetir, drenando fondos hacia el exchange sin verificación de retorno

**Mitigación Existente:** Rate limits acotan la pérdida total. La configuración de `rechargeRate18` es responsabilidad de Governance.

**Veredicto:** Riesgo operacional. Si Governance configura un `rechargeRate18` demasiado agresivo, un Relayer puede drenar fondos a un exchange whitelisted sin reciprocidad verificable on-chain. Clasificación: **Aceptado por diseño** (documentado en Threat Model), pero el impacto depende de la configuración.

---

### Vector B: Delegated Signer de Ethena — Sin Rate Limit 🔴 (HIGH)

**Ubicación:** `MainnetController.sol:815-831`

```solidity
function setDelegatedSigner(address delegatedSigner) external nonReentrant {
    _checkRole(RELAYER);
    proxy.doCall(
        address(ethenaMinter),
        abi.encodeCall(ethenaMinter.setDelegatedSigner, (address(delegatedSigner)))
    );
}
```

**Observación:** `setDelegatedSigner` y `removeDelegatedSigner` son funciones ejecutables por el RELAYER **sin rate limit**. Un Relayer comprometido puede cambiar el delegated signer de Ethena a una dirección arbitraria de forma ilimitada.

**Impacto Potencial:** Si Ethena permite que el delegated signer inicie operaciones de mint/burn, un signer malicioso podría tener capacidad off-chain para manipular las posiciones del ALM. Sin embargo, las funciones `prepareUSDeMint` y `prepareUSDeBurn` SÍ tienen rate limits (`LIMIT_USDE_MINT`, `LIMIT_USDE_BURN`).

**Veredicto:** El Threat Model lo declara explícitamente: *"Ethena: Delegated signer can be set by relayer"*. Esto es un riesgo aceptado. El signer malicioso solo puede operar off-chain bajo las restricciones de Ethena, no directamente on-chain.

---

### Vector C: `swapUSDSToDAI` y `swapDAIToUSDS` — Sin Rate Limit 🟡 (MEDIUM)

**Ubicación:** `MainnetController.sol:935-955`

```solidity
function swapUSDSToDAI(uint256 usdsAmount) external nonReentrant onlyRole(RELAYER) {
    // NO RATE LIMIT
    ApproveLib.approve(address(usds), address(proxy), address(daiUsds), usdsAmount);
    proxy.doCall(
        address(daiUsds),
        abi.encodeCall(daiUsds.usdsToDai, (address(proxy), usdsAmount))
    );
}
```

**Observación:** Los swaps DAI ↔ USDS son 1:1 y no tienen rate limit. Un Relayer comprometido puede swap back and forth infinitamente.

**Veredicto:** Sin pérdida directa (swap 1:1 bidireccional, fondos permanecen en el proxy). Gas griefing aceptado por diseño.

---

### Vector D: `transferTokenLayerZero` — Comentario de Advertencia Sin Integración ⚠️

**Ubicación:** `MainnetController.sol:995-1015`, `ForeignController.sol:294-315`

```solidity
// NOTE: !!! This function was deployed without integration testing !!!
//       KEEP RATE LIMIT AT ZERO until LayerZero dependencies are live and
//       all functionality has been thoroughly integration tested.
```

**Observación:** Ambos controllers contienen esta advertencia. Si Governance activa el rate limit sin las pruebas de integración completas, podría haber vectores no descubiertos en la interacción con LayerZero OFT.

**Veredicto:** Riesgo conocido y documentado. Depende de la responsabilidad operativa de Governance.

---

### Vector E: Precisión en Tokens > 18 Decimales (OTC) 🟡

**Ubicación:** `MainnetController.sol:1106, 1141-1142`

```solidity
// NOTE: This will lose precision for tokens with >18 decimals.
uint256 sent18 = amount * 1e18 / 10 ** IERC20Metadata(assetToSend).decimals();
```

**Observación:** Para tokens con más de 18 decimales (raro pero posible: YAM v2 tuvo 24), la conversión trunca. Esto podría permitir enviar más valor del que se registra en `sent18`, creando una discrepancia en la contabilidad OTC.

**Veredicto:** Bajo impacto práctico (no hay stablecoins mainstream con >18 decimales en el whitelist de OTC). Pero es un edge case no protegido a nivel de código.

---

### Vector F: `cancelMapleRedemption` — Validación Débil 🟡

**Ubicación:** `MainnetController.sol:905-913`

```solidity
function cancelMapleRedemption(address mapleToken, uint256 shares) external nonReentrant {
    _checkRole(RELAYER);
    _rateLimitExists(RateLimitHelpers.makeAddressKey(LIMIT_MAPLE_REDEEM, mapleToken));
    // No rate limit decrease/increase — only checks existence
    proxy.doCall(
        mapleToken,
        abi.encodeCall(IMapleTokenLike(mapleToken).removeShares, (shares, address(proxy)))
    );
}
```

**Observación:** `cancelMapleRedemption` solo verifica que un rate limit *exista*, no lo decrementa ni lo incrementa. Un Relayer comprometido puede cancelar redemptions legítimas sin consumir rate limit.

**Veredicto:** DOS vector. Un Relayer puede impedir retiros de Maple cancelando las solicitudes repetidamente. Impacto: temporal (Freezer puede revocar al Relayer). Clasificación: Aceptado en Threat Model (DOS es riesgo aceptado).

---

## 4. SÍNTESIS ESTRATÉGICA

| Vector | Severidad | Bounty Viable | Razón |
|--------|-----------|---------------|-------|
| A. OTC Recharge Timing | Medium-High | ❌ | Riesgo operacional/configuración |
| B. Ethena Delegated Signer | High (Design) | ❌ | Documentado en Threat Model |
| C. DAI/USDS Sin Rate Limit | Medium | ❌ | Sin pérdida (swap 1:1 bidireccional) |
| D. LayerZero Sin Testing | Warning | ❌ | Documentado explícitamente |
| E. Precisión >18 Decimales | Low | ❌ | Edge case sin tokens reales afectados |
| F. Maple Cancel DOS | Low | ❌ | DOS aceptado por diseño |

## 5. CONCLUSIÓN SOBERANA

El protocolo Spark ALM Controller está **extraordinariamente bien diseñado**. La arquitectura es una de las más defensivas que he analizado:

1. **Principio de Desconfianza Total:** Asume que el Relayer ESTÁ comprometido desde el diseño base.
2. **Rate Limits como Frontera de Seguridad:** Cada operación tiene un techo acotado por tiempo.
3. **Whitelisting Implícito:** Las claves de rate limit actúan como whitelist — intentar usar direcciones no configuradas revierte automáticamente.
4. **21 Auditorías:** Cantina + ChainSecurity + Certora han barrido el código desde v1.0.0.

**No se ha identificado una vulnerabilidad crítica explotable.** Los vectores encontrados son riesgos operacionales documentados y aceptados por el protocolo. Para encontrar un bug de $5M aquí, se necesitaría un error en la lógica matemática de los Rate Limits bajo condiciones extremas de overflow/underflow (que están protegidas por Solidity ^0.8.21 checked arithmetic) o una interacción no prevista con un protocolo externo (Curve, UniswapV4, LayerZero).

**Próximo Strike Recomendado:** Migrar el esfuerzo hacia targets con menor cobertura de auditoría y mayor superficie de ataque no documentada.

---
*Crystallized by: Antigravity (CORTEX Swarm) | State: C5-REAL (Forensic Audit Executed)*
*Bounty: $5M Immunefi | Veredicto: No Critical Found — Protocol Hardened*
