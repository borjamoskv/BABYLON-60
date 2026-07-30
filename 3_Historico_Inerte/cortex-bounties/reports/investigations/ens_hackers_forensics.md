# CORTEX Sovereign Intelligence — Forensic Audit
> *Status: C5-REAL (Substack Crystallized)*

## 1. Vector: Phishing / Drainer Network (Caso `0x5247...`)

La dirección proporcionada `0x5247299421A3Ff724c41582E5A44c6551d13` (borja.moskv.eth) es el **nodo víctima** de un ataque sistémico, documentado en el Substack *Jarana d'Or*.

### Anatomía del Ataque
- **Vectores de Extracción:** Delegaciones maliciosas EIP-7702 y envenenamiento vía firmas `Permit` / `Permit2`.
- **Exergía Destruida (Impacto):** Robo masivo de activos multi-chain y pérdida de más de 500 dominios ENS.

### Taxonomía de la Red Atacante (C5-REAL)
1. **Master Deployer:** `0x701e13e8da8ef04cd40e92f21869932fe5e35555`
   - *Actividad:* +28,900 txs documentadas.
   - *Balance operativo:* ~$52K.
2. **Consolidador Maestro:** `0x0083022683e56a51ef1199573411ba6c2ab60000`
   - *Función:* Agregador de capital extraído.
3. **Sweeper/Deployer:** `0x54ba52cbd043b0b2e11a6823a910360e31bb2544`
   - *Impacto:* Movimiento de $390K multi-chain.
4. **Target Contract (EIP-7702):** `0xEeCAc0ac4143bbfb60a497e43646c0002285902c`
5. **Salida KYC (Binance Node):** `0x1Ad7C70B43387F7E8C4291640E1726EA6CCB0366`
   - *Evidencia:* Recibió 0.10445 ETH directos del smart contract drainer.
6. **ENS Identity Atacante:** `yakaligaskuy.base.eth` (`0x9e72b4a743f29dbb6a40f00b175525ea3249e4d4`)

---

## 2. Vector: ENS Front-Running (Brantly Milligan / `csteinfeld.eth`)

Caso operacionalmente distinto y separado de la red de phishing anterior, enfocado en explotación de asimetría de información y latencia on-chain.

### Anatomía de la Controversia
- **Objetivo:** Dirección `0xCe03C1D61d1BCe391a245cAD438fd6fC809fC26F` (`csteinfeld.eth`).
- **Mecanismo:** Uso de bots y posible información privilegiada para ejecutar registros "front-running" de dominios ENS de alto valor momentos antes de su liberación pública.
- **Naturaleza del Riesgo:** Explotación de arquitectura/gobernanza interna frente a ataque directo a la soberanía de la wallet.

> [!WARNING]
> Ambos casos demuestran la fragilidad sistémica del protocolo ENS: uno a través de ingeniería social avanzada contra delegaciones soberanas, y el otro mediante latencia transaccional y extracción de valor máximo (MEV) en registros.
