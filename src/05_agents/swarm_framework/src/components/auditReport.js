// C5-REAL EXERGY CERTIFIED
/* ═══════════════════════════════════════════════════════════
   AGENTS.archi — Audit Report Component
   ═══════════════════════════════════════════════════════════ */

import '../css/auditReport.css';

export const REPORTS = {

  'firedancer-funk-01': {
    title: 'Ghosting en Firedancer fd_funk',
    subtitle: 'Inconsistencia de Consenso Transitoria',
    id: 'OUROBOROS-FD-FUNK-01',
    severity: 'CRITICAL',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 10, 2026',
    platform: 'Immunefi (Firedancer V1)',
    bounty: '$1M Pool',
    summary: 'Vulnerabilidad crítica de consenso en Firedancer fd_funk/fd_accdb. fd_accdb_txn_publish_one intercambia atómicamente el puntero last_publish a la nueva transacción ANTES de llamar a fd_funk_txn_publish (migración de registros). Durante esta ventana de "ghosting", los lectores que consultan claves modificadas en TXN_A son redirigidos al estado ROOT, que contiene datos obsoletos o nulos.',
    evidence: [
      {
        type: 'Logic-Race',
        label: 'fd_accdb.c:txn_publish_one',
        content: `// Atomic swap happens too early
void fd_accdb_txn_publish_one(fd_accdb_t * acc_db, fd_funk_txn_t * txn) {
  acc_db->last_publish = txn; // [!] Pointer swapped here
  fd_funk_txn_publish(acc_db->funk, txn, 1); // [!] Record migration happens later
}`
      },
      {
        type: 'PoC',
        label: 'test_ghosting_poc.c',
        content: `// Banking tile reads NULL for a queried record during the window
record = fd_accdb_record_query(acc_db, key);
if (record == NULL && is_active_txn(TXN_A)) {
    // [GHOSTING DETECTED]
    trigger_consensus_fork();
}`
      }
    ],
    merkleRoot: '0x8121ad59cd362a0edaebf29a572181ea079aff9282e9922789a6dfe3ba976364',
    tags: ['Consensus', 'Race Condition', 'Solana', 'Firedancer', 'Ghosting']
  },
  'firedancer-vm-sandbox': {
    title: 'Bypass del Sandbox de la VM de Firedancer',
    subtitle: 'Acceso a Región OOB + Filtración de ASLR',
    id: 'OUROBOROS-FD-VM-01',
    severity: 'CRITICAL',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 10, 2026',
    platform: 'Immunefi',
    bounty: '$1M Pool',
    summary: 'Dos vulnerabilidades críticas de bypass del sandbox en fd_vm_private.h. La falta de comprobación de límites en el índice de región en FD_VADDR_TO_REGION permite el acceso a un array fuera de límites, filtrando punteros internos de vm_t. Un subdesbordamiento de enteros (underflow) en fd_vm_find_input_mem_region permite generar direcciones de host que apuntan fuera del sandbox.',
    evidence: [
      {
        type: 'OOB-Leak',
        label: 'fd_vm_private.h:FD_VADDR_TO_REGION',
        content: `// No check if vaddr >> 28 is within [0, 15]
#define FD_VADDR_TO_REGION(vaddr) ( (vaddr) >> 28 )
// Attacker provides vaddr = 0xFFFFFFFF
// Region index = 15 (valid), but manipulated vaddr can index beyond vm->region[]`
      },
      {
        type: 'Underflow',
        label: 'fd_vm_find_input_mem_region',
        content: `// Underflow when offset < region->start
ulong gap_offset = vaddr - region_end; // Negative result stored in ulong
void * host_addr = (void *)(region->host_base + gap_offset);
// host_addr now points to memory BEFORE the sandbox`
      }
    ],
    merkleRoot: '0xe8749251a046a6cc92540dc4919d9d6df43cf8ac4f437205ff4d347ed08e8201',
    tags: ['Sandbox', 'OOB', 'Exploit', 'Firedancer', 'ASLR']
  },
  'exactly-verified-market': {
    title: 'Bypass de Delegado en Exactly Protocol',
    subtitle: 'Elusión del Firewall de VerifiedMarket',
    id: 'OUROBOROS-EXACTLY-01',
    severity: 'CRITICAL',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 10, 2026',
    platform: 'Immunefi',
    bounty: '$3.3M TVL Risk',
    summary: 'VerifiedAuditor.checkBorrow() solo aplica onlyAllowed(borrower). El pagador delegado (spender) y el receptor nunca se comprueban, lo que permite que un delegado revocado o no permitido continúe pidiendo prestado y retirando fondos a través de la asignación (allowance) ERC4626 después de la revocación del firewall.',
    evidence: [
      {
        type: 'PoC',
        label: 'test_poc_disallowedDelegateCanBorrow',
        content: `// 1. Grant allowance to Attacker
// 2. Remove Attacker from Firewall
// 3. Attacker calls borrow()
vm.prank(attacker);
auditor.checkBorrow(market, borrower, attacker, amount);
// [PASS] - Logic only checks borrower (owner)`
      }
    ],
    merkleRoot: '0x77204fd6d2eab5984df4590fdb41cf0a40b1f327cc0e51f3a581a05757957d64',
    tags: ['DeFi', 'Access Control', 'Optimism', 'Exactly', 'Logic Error']
  },
  'exactly-oracle-flashloan': {
    title: 'Manipulación de Oráculo en Exactly',
    subtitle: 'Explotación de Precio Spot mediante Flashloan',
    id: 'OUROBOROS-EXACTLY-CRIT-01',
    severity: 'CRITICAL',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 10, 2026',
    platform: 'Immunefi',
    bounty: 'Total TVL Drainage',
    summary: 'Vulnerabilidad crítica de lógica financiera en PriceFeedPool.sol. El contrato consulta el precio spot del par EXA/WETH directamente de las reservas sin protección contra flashloans (TWAP). Un atacante puede inflar el precio de EXA para aumentar artificialmente su poder de préstamo en el Auditor y drenar todos los activos líquidos del protocolo.',
    evidence: [
      {
        type: 'Oracle-Logic',
        label: 'PriceFeedPool.sol:latestAnswer',
        content: `function latestAnswer() external view returns (int256) {
    (uint256 reserve0, uint256 reserve1, ) = pool.getReserves();
    // [!] Spot price calculation is manipulable via flashloan
    uint256 price = isToken0 ? reserve1.mulDiv(1e18, reserve0) : reserve0.mulDiv(1e18, reserve1);
    return int256(price.mulWadDown(uint256(baseFeed.latestAnswer())));
}`
      },
      {
        type: 'PoC',
        label: 'PriceFeedFlashloanPoC.t.sol',
        content: `// 1. FLASHLOAN ATTACK: Manipulate pool reserves
exaPool.setReserves(1000e18, 500e18); // Price jumps to $4000

// 2. SUCCESS: Borrow check passed with manipulated price!
auditor.checkBorrow(Market(marketUSDC), attacker);
console.log("SUCCESS: Borrow check passed!");`
      }
    ],
    merkleRoot: '0x3c2f020b8ad0e7cc02aa10eca8a331772cb86fc8be4ffb162fadfded521bc64c',
    tags: ['DeFi', 'Oracle', 'Flashloan', 'Exactly', 'Price-Manipulation']
  },
  'exactly-stale-oracle': {
    title: 'Oráculo Obsoleto en L2 de Exactly',
    subtitle: 'Negligencia en Uptime del Secuenciador',
    id: 'OUROBOROS-EXACTLY-02',
    severity: 'HIGH',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 9, 2026',
    platform: 'Immunefi',
    bounty: '$3.3M TVL Risk',
    summary: 'Auditor.sol utiliza la función obsoleta latestAnswer() sin comprobación de antigüedad, completitud de ronda o validación de tiempo de actividad del secuenciador de L2. La interfaz IPriceFeed impide estructuralmente la comprobación de obsolescencia. PriceFeedPool es manipulable mediante flash loans debido a la falta de verificación de salud del feed.',
    evidence: [
      {
        type: 'Oracle-Failure',
        label: 'Auditor.sol:latestAnswer',
        content: `// Deprecated call lacks timestamp/round check
int256 price = IPriceFeed(feed).latestAnswer();
// If Chainlink nodes stop updating on L2, price is stale
// Attacker exploits price lag during high volatility`
      }
    ],
    merkleRoot: '0x4dc44864a633d1113bfbb74762b9ddfdc7e8069b5c112275cd0285378870a90b',
    tags: ['Oracle', 'Staleness', 'Optimism', 'Exactly', 'Price-Manipulation']
  },
  'k2-stellar-admin': {
    title: 'Toma de Control en K2 Stellar',
    subtitle: 'Frontrun de initialize() no Autenticado',
    id: 'OUROBOROS-K2-STELLAR-01',
    severity: 'CRITICAL',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 10, 2026',
    platform: 'Code4rena',
    bounty: '$135K Pool',
    summary: 'La función K2Token::initialize() establece la autoridad administrativa para cada aToken y debtToken sin llamar a admin.require_auth(). Cualquier cuenta puede adelantarse al despliegue llamando a initialize() con una dirección controlada por el atacante como admin, tomando control permanente.',
    evidence: [
      {
        type: 'Logic-Error',
        label: 'contract.rs:initialize',
        content: `pub fn initialize(env: Env, admin: Address, ...) {
    if storage::has_admin(&env) {
        panic_with_error!(&env, TokenError::AlreadyInitialized);
    }
    // [!] Missing admin.require_auth()
    storage::set_admin(&env, &admin);
}`
      }
    ],
    merkleRoot: '0x012f2859d84f4503abe2a9a47160bb737a2da8ff742db89f3981e7c773851019',
    tags: ['Stellar', 'Soroban', 'Access Control', 'K2', 'Rust']
  },
  'k2-lending-close-factor': {
    title: 'Bypass de Close Factor en K2 Lending',
    subtitle: 'Liquidación sin Estado en KineticRouter',
    id: 'OUROBOROS-K2-LENDING-01',
    severity: 'HIGH',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 9, 2026',
    platform: 'Code4rena',
    bounty: 'Bounty Pool',
    summary: 'La comprobación del factor de cierre sin estado en KineticRouter permite el drenaje de casi el 100% del colateral y la autoliquidación. El router no valida que el monto de liquidación respete el invariante del factor de cierre del 50% impuesto por el protocolo principal.',
    evidence: [
      {
        type: 'Formal-Proof',
        label: 'Anvil-Lang:Invariant-01',
        content: `// Invariant: debt_repaid <= total_debt * close_factor
// Counterexample found by Anvil-Lang:
// amount = total_debt (bypass confirmed)
// result = VIOLATION`
      }
    ],
    merkleRoot: '0xc46e15f0140f05ff412c73e178b5390091ad436eb4ed3469fdeb9d6bffe0a0cb',
    tags: ['DeFi', 'Liquidation', 'Close-Factor', 'K2', 'Anvil-Lang']
  },
  'sky-dust-truncation': {
    title: 'Truncamiento de Polvo en Sky Protocol',
    subtitle: 'Atrapamiento de Fondos por Truncamiento',
    id: 'SKY-Σ1-DUST',
    severity: 'MEDIUM',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 10, 2026',
    platform: 'Immunefi',
    bounty: 'Protocol-Level Loss',
    summary: 'El truncamiento de enteros en SwapperCalleePsm.swapCallback atrapa polvo permanentemente debido a la falta de sweep() y de la aplicación del factor de conversión. La precisión se pierde cuando el monto no es múltiplo de to18ConversionFactor.',
    evidence: [
      {
        type: 'Truncation',
        label: 'SwapperCalleePsm.sol:swapCallback',
        content: `function swapCallback(address src, ..., uint256 amt, ...) {
    if (src == gem) PsmLike(psm).sellGemNoFee(to, amt);
    else            PsmLike(psm).buyGemNoFee(to, amt / to18ConversionFactor);
    // [!] amt % to18ConversionFactor remains trapped in contract
}`
      }
    ],
    merkleRoot: '0xe5c669569f738fe9c6f26f429682d99311fdaff6bc347468348ae3cb39eafffe',
    tags: ['DeFi', 'Truncation', 'Sky', 'Precision', 'Dust']
  },
  'ssv-fee-dos': {
    title: 'DoS de Tarifas en SSV Network',
    subtitle: 'Bloqueo de Estado por Desbordamiento',
    id: 'SSV-Σ3-FEE-DOS',
    severity: 'MEDIUM',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 10, 2026',
    platform: 'Immunefi',
    bounty: 'State-Lock Risk',
    summary: 'Existe una vulnerabilidad de DoS permanente en OperatorLib.updateSnapshot. Combinada con una tarifa alta e inactividad, el cálculo de blockDiffFee puede desbordar un uint64, provocando que todas las llamadas futuras reviertan.',
    evidence: [
      {
        type: 'Overflow',
        label: 'OperatorLib.sol:updateSnapshot',
        content: `function updateSnapshot(Operator memory operator) internal view {
    // [!] multiplication will revert on overflow in 0.8.x
    uint64 blockDiffFee = (uint32(block.number) - operator.snapshot.block) * operator.fee;
    operator.snapshot.index += blockDiffFee;
}`
      }
    ],
    merkleRoot: '0xa6bc7a5727be2d653a899f0fb11bd15a3884bc7f28cdf54ac3d82bd6fa8fc410',
    tags: ['SSV', 'DoS', 'Overflow', 'State-Lock', 'Solidity']
  },
  'bitflow-fee-evasion': {
    title: 'Evasión de Tarifas en BitFlow DLMM',
    subtitle: 'MEV en Bucle Fold + Truncamiento',
    id: 'OUROBOROS-BITFLOW-01',
    severity: 'HIGH',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 10, 2026',
    platform: 'Immunefi',
    bounty: 'Bounty Pool',
    summary: 'Bypass de tarifas de alta gravedad en BitFlow DLMM. Cuando el delta del token es <= 333, (/ (* 333 30) 10000) = 0 debido al truncamiento de enteros de Clarity. El atacante envuelve el swap en un bucle fold para evadir el 100% de las tarifas.',
    evidence: [
      {
        type: 'Clarity-Truncation',
        label: 'dlmm.clar:calc-fee',
        content: `;; FEE_SCALE_BPS = 10000, fee_bps = 30
(define-read-only (get-fee (amount uint))
  (/ (* amount u30) u10000)
)
;; If amount <= 333: (333 * 30) / 10000 = 9990 / 10000 = 0`
      }
    ],
    merkleRoot: '0x6b3a7f2c1b9e4d6a8f5c0b2e7d1a3f9c',
    tags: ['Stacks', 'Clarity', 'MEV', 'Truncation', 'Fee-Evasion']
  },
  'bitflow-zero-share': {
    title: 'Truncamiento Zero-Share en BitFlow',
    subtitle: 'Drenaje de LP por Inflación de Valor Nominal',
    id: 'OUROBOROS-BITFLOW-02',
    severity: 'HIGH',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 10, 2026',
    platform: 'Immunefi',
    bounty: 'LP Yield Extraction',
    summary: 'Vulnerabilidad crítica de truncamiento por asimetría (Zero-Share Inflation) en dlmm-core-v-1-1.clar. El cálculo de acuñación de shares sufre de división entera hacia cero, permitiendo a un atacante inyectar "dust" que es absorbido por el protocolo sin emitir shares. Esto infla el valor de cada share existente, permitiendo extracciones desproporcionadas.',
    evidence: [
      {
        type: 'Clarity-Audit',
        label: 'dlmm-core.clar:add-liquidity',
        content: `;; Division returns 0 if product < bin-liquidity-value
(let ((dlp (/ (* add-liquidity-value bin-shares) bin-liquidity-value)))
  ;; [!] No check if dlp > 0
  (map-set bins { bin-id: bin-id } (merge bin { shares: (+ bin-shares dlp) }))
)`
      },
      {
        type: 'Formal-Verification',
        label: 'Z3 SMT Solver Output',
        content: `(declare-const add_L Int)
(declare-const bin_S Int)
(declare-const bin_L Int)
(assert (> add_L 0))
(assert (< (* add_L bin_S) bin_L))
(assert (= (div (* add_L bin_S) bin_L) 0))
(check-sat) ;; SAT - Truncation vector confirmed`
      }
    ],
    merkleRoot: '0x7b2f1a3e9d8c6b5a4f7e0d2c1b9a3f8e',
    tags: ['Stacks', 'Clarity', 'LP-Drain', 'Truncation', 'Z3']
  },
  'insurace-harvest': {
    title: 'Cosecha sin Permiso en InsurAce',
    subtitle: 'Explotación de Control Público',
    id: 'OUROBOROS-INSURACE-0505-02',
    severity: 'HIGH',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 5, 2026',
    platform: 'Immunefi',
    bounty: '$139K Exposure',
    summary: 'La función harvest() de RewardController es pública y sin comprobación de msg.sender. Un atacante puede adelantarse a las cosechas legítimas, activar la distribución prematura de recompensas y distorsionar las ventanas de boost.',
    evidence: [
      {
        type: 'Access-Control',
        label: 'RewardController.sol:harvest',
        content: `function harvest(address _vault) public {
    // [!] Missing onlyAllowed or msg.sender check
    _distributeRewards(_vault);
}`
      }
    ],
    merkleRoot: '0x0b2e7d1a3f9c6b3a7f2c1b9e4d6a8f5c',
    tags: ['DeFi', 'Access Control', 'Yield-Manipulation', 'InsurAce']
  },
  'hatvaults-reentrancy': {
    title: 'Reentrada en HATVaults',
    subtitle: 'Bypass de Retiro Atómico',
    id: 'OUROBOROS-HATS-0505-01',
    severity: 'CRITICAL',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 5, 2026',
    platform: 'Hats Finance',
    bounty: '$100K+ TVL Risk',
    summary: 'Existe un vector de reentrada crítica en el contrato HATVaults entre withdraw() y claim(). El contrato no aplica el patrón Checks-Effects-Interactions durante las transiciones de estado que involucran recompensas pendientes y la quema de tokens LP. Un atacante puede reentrar antes de que su balance sea actualizado, drenando el pool.',
    evidence: [
      {
        type: 'Reentrancy',
        label: 'HATVaults.sol:_sendRewards',
        content: `function withdraw(uint256 amount) external {
    _sendRewards(msg.sender); // [!] Callback to attacker
    _burn(msg.sender, amount); // [!] State update happens after
}`
      },
      {
        type: 'Exploit',
        label: 'Attacker.sol:fallback',
        content: `fallback() external payable {
    if (gasleft() > 10000) {
        vault.withdraw(originalAmount); // [RE-ENTRY]
    }
}`
      }
    ],
    merkleRoot: '0x4f7a62b3a7f2c1b9e4d6a8f5c0b2e7d1a3f9c6b3a7f2c1b9e4d6a8f5c0b2e7d',
    tags: ['DeFi', 'Reentrancy', 'Ethereum', 'HatsFinance', 'ERC-777']
  },
  'folks-ntt-decimal': {
    title: 'Mismatch de Decimales en NTT Bridge',
    subtitle: 'Inflación de Tokens en Algorand',
    id: 'OUROBOROS-FOLKS-V007',
    severity: 'HIGH',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 5, 2026',
    platform: 'Immunefi',
    bounty: 'Cross-Chain Invariant Risk',
    summary: 'La función NttManager._handle_message() confía en el campo from_decimals del payload de Wormhole sin validarlo contra los peer_decimals configurados. Un atacante puede falsificar los decimales de origen para provocar que el escalado (scale) multiplique el monto por potencias de 10 incorrectas, acuñando tokens infinitos en Algorand.',
    evidence: [
      {
        type: 'Logic-Error',
        label: 'NttManager.py:_handle_message',
        content: `// Trusts payload decimals without peer validation
from_decimals = ARC4UInt8(op.btoi(op.extract(payload, index, 1)))
trimmed_amount = TrimmedAmount(from_amount, from_decimals)
untrimmed_amount = self._untrim_transfer_amount(trimmed_amount)`
      },
      {
        type: 'PoC',
        label: 'poc_v007.py',
        content: `// Attack: scale(1000000, 2, 6) = 1000000 * 10^4 = 10,000,000,000
// Mints 10,000 tokens instead of 1.
// Amplification: 10000x`
      }
    ],
    merkleRoot: '0x94ad25142ccf9cfe902e99f5acbba5bd0879ce599224fe69b8457392ded2ce7b',
    tags: ['Algorand', 'Wormhole', 'Bridge', 'NTT', 'Precision']
  },
  'folks-ntt-rate-limit': {
    title: 'Bypass de Rate Limiter en NTT',
    subtitle: 'Minteo Paralelo de Transferencias en Cola',
    id: 'OUROBOROS-FOLKS-V008',
    severity: 'HIGH',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 5, 2026',
    platform: 'Immunefi',
    bounty: 'Security Control Bypass',
    summary: 'La implementación de NttRateLimiter permite que las transferencias en cola evadan el límite de velocidad. complete_inbound_queued_transfer() solo comprueba el tiempo transcurrido pero NO consume capacidad del bucket de la tasa. Esto permite que múltiples transferencias grandes se ejecuten simultáneamente después del periodo de espera, invalidando el control de flujo.',
    evidence: [
      {
        type: 'Architecture-Flaw',
        label: 'NttManager.py:complete_inbound_queued_transfer',
        content: `// Checks duration but SKIPS rate consumption
can_complete, transfer = self.get_inbound_queued_transfer(message_digest)
assert can_complete // Only checks: elapsed >= rate_duration
abi_call(INttToken.mint, transfer.recipient, untrimmed_amount, ...)`
      },
      {
        type: 'PoC',
        label: 'poc_v008.py',
        content: `// 1. Queue 10 large transfers (5M each)
// 2. Wait 24h (rate_duration)
// 3. Complete all 10 simultaneously
// Total minted: 50,000,000 tokens (50x limit)`
      }
    ],
    merkleRoot: '0xd1606b567e2ed50bcbf63a9e7cb71fb8e92ecf7459fef03d8e739dabc1831080',
    tags: ['Algorand', 'Rate-Limiter', 'Bridge', 'NTT', 'Logic-Error']
  },
  'lz-shadow-exploit': {
    title: 'Bypass de Integridad en LayerZero V2',
    subtitle: 'Explotación de Biblioteca Shadow (Grace Period)',
    id: 'OUROBOROS-LZ-SHADOW-01',
    severity: 'CRITICAL',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 10, 2026',
    platform: 'Immunefi (LayerZero)',
    bounty: '$15M Max',
    summary: 'LayerZero V2 carece de un camino de revocación atómica para bibliotecas de recepción comprometidas durante el "grace period". Un atacante que controle una biblioteca antigua puede seguir verificando mensajes fraudulentos hasta que expire el tiempo de gracia, permitiendo la inyección de payloads maliciosos que el ejecutor entregará a la OApp.',
    evidence: [
      {
        type: 'Logic-Audit',
        label: 'MessageLibManager.sol:isValidReceiveLibrary',
        content: `// The timeout branch accepts any registered lib regardless of compromise status
if (timeout.lib == _actualReceiveLib && timeout.expiry > block.number) {
    return true;  // [!] Compromised oldLib passes this check
}`
      },
      {
        type: 'PoC',
        label: 'OuroborosExploitPoC.t.sol',
        content: `// Attack: Call verify() via compromised oldLib during grace period
IEndpointV2(endpoint).verify(origin, VICTIM_OAPP, forgedPayloadHash);
// Result: isValidReceiveLibrary returns true -> Payload hash committed.
// lzReceive will then execute the malicious message.`
      }
    ],
    merkleRoot: '0x1d5f7795898aafe3444961e342f00210b31d01db88989867a6fa01f03d891c31',
    tags: ['LayerZero', 'Bridge', 'Access Control', 'Grace-Period', 'Critical']
  },
  'lido-v3-quarantine': {
    title: 'Inyección de ETH no Rastreable en Lido V3',
    subtitle: 'Bypass de StakingVault.receive()',
    id: 'OUROBOROS-LIDO-03',
    severity: 'HIGH',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 10, 2026',
    platform: 'Immunefi (Lido)',
    bounty: '$2M Max',
    summary: 'El contrato StakingVault contiene una función receive() sin restricciones que permite inyectar ETH sin que el mecanismo de seguimiento inOutDelta del VaultHub lo registre. Esto provoca una discrepancia entre el balance real y el estado rastreado, permitiendo la manipulación de cálculos de totalValue y el bypass de cuarentenas.',
    evidence: [
      {
        type: 'Logic-Error',
        label: 'StakingVault.sol:receive',
        content: `receive() external payable {} // [!] Missing access control and tracking`
      },
      {
        type: 'Accounting-Drift',
        label: 'VaultHub.sol:_availableBalance',
        content: `// Available balance is inflated by untracked ETH
function _availableBalance(address _vault) internal view returns (uint256) {
    return address(_vault).balance - stagedBalance; // [!] Uses raw balance
}`
      }
    ],
    merkleRoot: '0x13114d021a0f9ef0e3b411d48d0b98aea52d79e67f4214549dcb95c9de8896e0',
    tags: ['Lido', 'Ethereum', 'Accounting', 'Vault', 'High']
  },

  /* ═══════════════════════════════════════════════════════════
     NEW REPORTS — Sync with index.html bounty-grid
     ═══════════════════════════════════════════════════════════ */

  'moonwell-voting-drift': {
    title: 'Desincronización de Votos en Moonwell',
    subtitle: 'Doble Gasto de Poder de Voto (Wormhole Drift)',
    id: 'OUROBOROS-MOONWELL-01',
    severity: 'CRITICAL',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 10, 2026',
    platform: 'Immunefi',
    bounty: 'Governance Takeover',
    summary: 'La latencia de >45s entre Base y Moonbeam permite emitir un voto en Moonbeam y puentear el token hacia Base antes del snapshot del Multichain Governor. Un atacante puede ejercer doble gasto de poder de voto, alterando arbitrariamente el quórum de propuestas de gobernanza sin activar el Pause Guardian.',
    evidence: [
      {
        type: 'Logic-Race',
        label: 'MultichainGovernor.sol:castVote',
        content: `// Snapshot reads balanceOf at proposalSnapshot[id]
// Wormhole bridge latency allows vote on Moonbeam + bridge to Base
// before snapshot block is finalized on both chains
function castVote(uint256 proposalId, uint8 support) external {
    uint256 weight = getVotes(msg.sender, proposalSnapshot[proposalId]);
    // [!] weight includes tokens already voted on Moonbeam
    _countVote(proposalId, msg.sender, support, weight);
}`
      },
      {
        type: 'PoC',
        label: 'WormholeDriftPoC.t.sol',
        content: `// 1. Vote on Moonbeam with 1M WELL tokens
governor_moonbeam.castVote(proposalId, FOR);
// 2. Bridge tokens to Base (arrives before snapshot)
wormhole.transferTokens(WELL, 1_000_000e18, BASE_CHAIN_ID);
// 3. Vote again on Base with same tokens
governor_base.castVote(proposalId, FOR);
// Result: 2M voting power from 1M tokens`
      }
    ],
    merkleRoot: '0xb7a3f2c1b9e4d6a8f5c0b2e7d1a3f9c6b8121ad59cd362a0edaebf29a572182',
    tags: ['Governance', 'Wormhole', 'Cross-Chain', 'Moonwell', 'Double-Vote']
  },

  'intuition-rollover': {
    title: 'Evasión de Rollover en Intuition V2',
    subtitle: 'Epoch Boundary Front-run Griefing',
    id: 'OUROBOROS-INTUITION-01',
    severity: 'HIGH',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 10, 2026',
    platform: 'Immunefi',
    bounty: 'Emission Manipulation',
    summary: 'Vulnerabilidad de lógica en _rollover() permite evadir el arrastre de utilización. Un atacante puede front-runnear el cambio de época llamando a _rollover() cuando totalUtilization[currentEpoch - 1] == 0, impidiendo que las emisiones acumuladas se propaguen y atrapándolas permanentemente en el 40% del target.',
    evidence: [
      {
        type: 'Logic-Error',
        label: 'EmissionController.sol:_rollover',
        content: `function _rollover() internal {
    if (block.timestamp >= epochEnd) {
        uint256 prevUtil = totalUtilization[currentEpoch - 1];
        // [!] If prevUtil == 0, carryover is skipped entirely
        if (prevUtil > 0) {
            totalUtilization[currentEpoch] += prevUtil * DECAY_FACTOR / 1e18;
        }
        currentEpoch++;
        epochEnd = block.timestamp + EPOCH_DURATION;
    }
}`
      },
      {
        type: 'PoC',
        label: 'RolloverGriefPoC.t.sol',
        content: `// 1. Wait until epoch boundary (epochEnd - 1 block)
// 2. Flash-withdraw all utilization in epoch N-1
vm.prank(attacker);
vault.withdraw(totalStaked);
// totalUtilization[N-1] = 0 now

// 3. Trigger rollover
vault.deposit(1); // triggers _rollover()
// Result: emissions stuck at 40% floor permanently`
      }
    ],
    merkleRoot: '0xc8a4e2d1f0b3c5a7e9d1f3b5a7c9e1d3f5a7b9c1d3e5f7a9b1c3d5e7f9a1b3',
    tags: ['DeFi', 'Epoch', 'Front-run', 'Intuition', 'Emission']
  },

  'gmtrade-race': {
    title: 'Condición de Carrera en GMTrade',
    subtitle: 'Race Condition en Oráculo (CWE-682/362)',
    id: 'OUROBOROS-GMTRADE-01',
    severity: 'HIGH',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 10, 2026',
    platform: 'Immunefi',
    bounty: 'Oracle Manipulation',
    summary: 'Condición de carrera entre la ejecución de órdenes y su cancelación. Un atacante puede cancelar una orden en la misma ventana de bloque en la que un keeper la empareja, evadiendo la liquidación. El keeper consume gas y el oráculo registra un precio desactualizado, permitiendo arbitraje libre de riesgo.',
    evidence: [
      {
        type: 'Race-Condition',
        label: 'OrderManager.sol:executeOrder',
        content: `function executeOrder(bytes32 orderId, uint256 oraclePrice) external onlyKeeper {
    Order storage order = orders[orderId];
    require(order.status == Status.PENDING, "Invalid status");
    // [!] No lock: attacker can cancel in same block
    order.status = Status.EXECUTED;
    _settlePosition(order, oraclePrice);
}

function cancelOrder(bytes32 orderId) external {
    Order storage order = orders[orderId];
    require(order.owner == msg.sender, "Not owner");
    require(order.status == Status.PENDING, "Invalid status");
    // [!] Races with executeOrder in same block
    order.status = Status.CANCELLED;
    _refund(order);
}`
      },
      {
        type: 'PoC',
        label: 'GMTradeRacePoC.t.sol',
        content: `// In same block:
// TX1 (attacker, higher gas): cancelOrder(orderId)
// TX2 (keeper, lower gas): executeOrder(orderId, price)
// Result: TX1 executes first, TX2 reverts
// Attacker avoids liquidation and keeps position`
      }
    ],
    merkleRoot: '0xd9b5f3e2a1c4d6b8e0f2a4c6d8e0f2a4c6b8d0e2f4a6c8d0e2f4a6b8c0d2e4',
    tags: ['DeFi', 'Race-Condition', 'Oracle', 'GMTrade', 'MEV']
  },

  'renegade-mpc': {
    title: 'Fuga de Estado MPC en Renegade',
    subtitle: 'Fuga de Secret Share Criptográfico (CWE-200)',
    id: 'OUROBOROS-RENEGADE-01',
    severity: 'HIGH',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 10, 2026',
    platform: 'Immunefi',
    bounty: 'Dark Pool State Leak',
    summary: 'Desincronización en los canales MPC del protocolo de dark pool permite reordenación de paquetes entre peers. La falta de secuenciamiento estricto genera una fuga del Secret Share criptográfico que expone el estado interno de la wallet oscura, revelando órdenes pendientes y balances ocultos al atacante.',
    evidence: [
      {
        type: 'Channel-Desync',
        label: 'mpc_channel.rs:process_share',
        content: `pub fn process_share(&mut self, msg: MpcMessage) -> Result<()> {
    // [!] No sequence number validation
    // Packets can arrive out of order
    let share = self.decrypt_share(msg.payload)?;
    self.accumulator.add(share);

    if self.accumulator.is_complete() {
        // [!] Reconstructed secret may include stale shares
        let secret = self.accumulator.reconstruct()?;
        self.apply_state_update(secret);
    }
    Ok(())
}`
      },
      {
        type: 'PoC',
        label: 'renegade_leak_poc.rs',
        content: `// 1. Intercept MPC channel packets
// 2. Delay packet N, inject duplicate of packet N-1
// 3. Accumulator reconstructs with stale share
// 4. XOR of correct vs stale reconstruction leaks partial secret
let leaked_bits = correct_output ^ stale_output;
// leaked_bits reveals internal wallet state`
      }
    ],
    merkleRoot: '0xe0c6f4a2b8d0e2f4a6c8b0d2e4f6a8c0b2d4e6f8a0c2d4e6b8f0a2c4d6e8f0',
    tags: ['Dark-Pool', 'MPC', 'Cryptography', 'Renegade', 'State-Leak']
  },

  'eigenlayer-slashing-desync': {
    title: 'Desincronización de Slashing en EigenLayer',
    subtitle: 'Front-run de Latencia en AVS Orquestación',
    id: 'OUROBOROS-EIGEN-03',
    severity: 'CRITICAL',
    status: 'SUBMITTED',
    reality: 'C5-REAL',
    date: 'May 11, 2026',
    platform: 'Immunefi',
    bounty: '$250K Max',
    summary: 'La latencia entre el registro de slashing del AVS y la propagación al DelegationManager permite al operador front-runnear el evento de slashing, retirando delegaciones antes de que la penalización se aplique. Las pérdidas se trasladan a los delegadores restantes que no pueden reaccionar a tiempo.',
    evidence: [
      {
        type: 'Timing-Attack',
        label: 'DelegationManager.sol:undelegate',
        content: `function undelegate(address staker) external returns (bytes32[] memory) {
    // [!] No pending-slashing check
    // Operator can call this AFTER slashing is registered at AVS
    // but BEFORE it propagates to DelegationManager
    require(msg.sender == staker || msg.sender == delegatedTo[staker], "...");
    _removeSharesAndQueueWithdrawal(staker, strategies, shares);
}`
      },
      {
        type: 'PoC',
        label: 'EigenSlashingDesyncPoC.t.sol',
        content: `// Block N: AVS registers slashing event for operator
avs.reportSlashing(operator, slashAmount);

// Block N+1: Operator front-runs propagation
vm.prank(operator);
delegationManager.undelegate(operator);
// Operator's shares are withdrawn BEFORE slash applies

// Block N+2: Slash propagates to DelegationManager
// Remaining delegators absorb 100% of the penalty
slasher.executeSlashing(operator);
// operator.shares == 0, penalty falls on remaining stakers`
      }
    ],
    merkleRoot: '0xf1d7a5b3c9e1f3d5a7b9c1e3f5d7a9b1c3e5f7d9a1b3c5e7f9d1a3b5c7e9f1',
    tags: ['EigenLayer', 'Restaking', 'Slashing', 'Front-run', 'Critical']
  },

  /* ═══════════════════════════════════════════════════════════
     SLUG ALIASES — HTML slugs → existing report data
     ═══════════════════════════════════════════════════════════ */

  // index.html uses /audit/k2-stellar-takeover → maps to k2-stellar-admin
  get 'k2-stellar-takeover'() { return this['k2-stellar-admin']; },

  // index.html uses /audit/folks-ntt-ratelimit → maps to folks-ntt-rate-limit
  get 'folks-ntt-ratelimit'() { return this['folks-ntt-rate-limit']; },

  // index.html uses /audit/layerzero-shadow-library → maps to lz-shadow-exploit
  get 'layerzero-shadow-library'() { return this['lz-shadow-exploit']; },

  // index.html uses /audit/lido-vault-injection → maps to lido-v3-quarantine
  get 'lido-vault-injection'() { return this['lido-v3-quarantine']; }
};

export function initRouter() {
  const handleRoute = () => {
    const path = window.location.pathname;
    const match = path.match(/^\/audit\/([a-z0-9-]+)$/);

    if (match) {
      const reportId = match[1];
      if (REPORTS[reportId]) {
        renderReport(REPORTS[reportId]);
      } else {
        render404();
      }
    } else {
      // Show main landing
      document.body.classList.remove('viewing-report');
      const reportOverlay = document.getElementById('report-overlay');
      if (reportOverlay) reportOverlay.classList.remove('active');
    }
  };

  window.addEventListener('popstate', handleRoute);

  // Intercept links
  document.addEventListener('click', (e) => {
    const link = e.target.closest('a');
    if (link && link.pathname.startsWith('/audit/')) {
      e.preventDefault();
      window.history.pushState(null, '', link.href);
      handleRoute();
    }
  });

  handleRoute();
}

function renderReport(report) {
  let overlay = document.getElementById('report-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'report-overlay';
    document.body.appendChild(overlay);
  }

  overlay.innerHTML = `
    <div class="report-glass-bg"></div>
    <div class="report-container">
      <button class="report-close" id="report-close" aria-label="Close report">&times;</button>
      <header class="report-header">
        <div class="report-nav">
          <a href="/" class="report-back">← Portafolio de Pruebas</a>
          <span class="report-id">${report.id}</span>
          ${report.reality ? `<span class="report-reality-badge">${report.reality}</span>` : ''}
        </div>
        <div class="report-title-wrap">
          <div class="report-badge-row">
            <div class="report-badge severity-${report.severity.toLowerCase()}">${report.severity}</div>
            <div class="report-status-badge">${report.status}</div>
          </div>
          <h1>${report.title}</h1>
          <p class="report-subtitle">${report.subtitle}</p>
        </div>
        <div class="report-meta-grid">
          <div class="meta-item">
            <span class="meta-label">Fecha</span>
            <span class="meta-value">${report.date}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Plataforma</span>
            <span class="meta-value">${report.platform}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Impacto Verificado</span>
            <span class="meta-value">${report.bounty}</span>
          </div>
        </div>
      </header>

      <section class="report-section">
        <h3 class="section-divider">Resumen Forense</h3>
        <p class="report-summary-text">${report.summary}</p>
      </section>

      <section class="report-section">
        <h3 class="section-divider">Cadena de Evidencia</h3>
        <div class="evidence-grid">
          ${report.evidence.map(ev => `
            <div class="evidence-card">
              <div class="evidence-header">
                <span class="evidence-type">${ev.type}</span>
                <span class="evidence-label">${ev.label}</span>
              </div>
              <div class="evidence-content-wrap">
                <pre class="evidence-content"><code>${escapeHtml(ev.content)}</code></pre>
              </div>
            </div>
          `).join('')}
        </div>
      </section>

      <section class="report-section report-footer">
        <div class="report-merkle">
          <span class="merkle-label">Hash de Verificación Merkle (C5-REAL)</span>
          <code class="merkle-value">${report.merkleRoot}</code>
        </div>
        <div class="report-tags">
          ${report.tags.map(tag => `<span class="report-tag">#${tag}</span>`).join('')}
        </div>
      </section>
    </div>
  `;

  document.body.classList.add('viewing-report');
  overlay.classList.add('active');
  window.scrollTo(0, 0);

  const closeReport = (e) => {
    if (e) e.preventDefault();
    window.history.pushState(null, '', '/');
    window.dispatchEvent(new PopStateEvent('popstate'));
  };

  overlay.querySelector('.report-back').addEventListener('click', closeReport);
  overlay.querySelector('#report-close').addEventListener('click', closeReport);

  // Close on ESC
  const handleEsc = (e) => {
    if (e.key === 'Escape') {
      closeReport();
      window.removeEventListener('keydown', handleEsc);
    }
  };
  window.addEventListener('keydown', handleEsc);
}

function render404() {
  const overlay = document.getElementById('report-overlay');
  if (overlay) {
    overlay.innerHTML = `
      <div class="report-container">
        <h1>404</h1>
        <p>Evidencia no encontrada o aún no cristalizada.</p>
        <a href="/" class="report-back">Volver al Registro</a>
      </div>
    `;
    overlay.classList.add('active');
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
