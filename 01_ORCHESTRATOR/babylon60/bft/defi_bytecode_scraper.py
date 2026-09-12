# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized DeFi & Hook Bytecode Scraper (Skill 41)
"""defi_bytecode_scraper.py - Análisis cuantitativo de bytecode y hooks Uniswap v4.

Verifica:
1. Máscara de permisos de 14 bits en direcciones de Hook de Uniswap v4.
2. Detección de opcodes de almacenamiento transitorio EIP-1153 (TSTORE 0x5d, TLOAD 0x5e).
3. Auditoría de riesgos de reentrancy transitoria y omisión de limpieza de estado.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import logging
from typing import Dict, List, Optional, Sequence

from babylon60.transducers.bounty_feed_transducer import BountyAdvisory, BountyDomain

logger = logging.getLogger("babylon60.bft.defi_scraper")

# Constantes de Permisos Uniswap v4 (Bits 13..0 en los 14 bits superiores de la dirección)
BEFORE_INITIALIZE_FLAG = 1 << 13
AFTER_INITIALIZE_FLAG = 1 << 12
BEFORE_ADD_LIQUIDITY_FLAG = 1 << 11
AFTER_ADD_LIQUIDITY_FLAG = 1 << 10
BEFORE_REMOVE_LIQUIDITY_FLAG = 1 << 9
AFTER_REMOVE_LIQUIDITY_FLAG = 1 << 8
BEFORE_SWAP_FLAG = 1 << 7
AFTER_SWAP_FLAG = 1 << 6
BEFORE_DONATE_FLAG = 1 << 5
AFTER_DONATE_FLAG = 1 << 4
BEFORE_SWAP_RETURNS_DELTA_FLAG = 1 << 3
AFTER_SWAP_RETURNS_DELTA_FLAG = 1 << 2
AFTER_ADD_LIQUIDITY_RETURNS_DELTA_FLAG = 1 << 1
AFTER_REMOVE_LIQUIDITY_RETURNS_DELTA_FLAG = 1 << 0

# Opcodes EIP-1153 (Cancun / Dencun Hard Fork)
OPCODE_TLOAD = 0x5C + 2  # 0x5e
OPCODE_TSTORE = 0x5C + 1  # 0x5d

# Opcodes Críticos de Riesgo y Control de Flujo
OPCODE_ORIGIN = 0x32
OPCODE_DELEGATECALL = 0xF4
OPCODE_CREATE2 = 0xF5
OPCODE_SELFDESTRUCT = 0xFF


@dataclass(frozen=True)
class HookPermissions:
    """Decodificación de permisos a partir de la máscara de bits de la dirección."""

    raw_bits: int
    before_initialize: bool
    after_initialize: bool
    before_add_liquidity: bool
    after_add_liquidity: bool
    before_remove_liquidity: bool
    after_remove_liquidity: bool
    before_swap: bool
    after_swap: bool
    before_donate: bool
    after_donate: bool
    before_swap_returns_delta: bool
    after_swap_returns_delta: bool
    after_add_liquidity_returns_delta: bool
    after_remove_liquidity_returns_delta: bool

    @classmethod
    def from_address(cls, address: str) -> HookPermissions:
        """Extrae los 14 bits de permisos de una dirección Ethereum (160 bits)."""
        clean_addr = address.lower().replace("0x", "").strip()
        if len(clean_addr) != 40:
            return cls(
                0, False, False, False, False, False, False, False, False, False, False, False, False, False, False
            )

        addr_int = int(clean_addr, 16)
        # Uniswap v4 ubica los flags en los primeros 14 bits más significativos de los 160 bits:
        bits = (addr_int >> (160 - 14)) & 0x3FFF

        return cls(
            raw_bits=bits,
            before_initialize=bool(bits & BEFORE_INITIALIZE_FLAG),
            after_initialize=bool(bits & AFTER_INITIALIZE_FLAG),
            before_add_liquidity=bool(bits & BEFORE_ADD_LIQUIDITY_FLAG),
            after_add_liquidity=bool(bits & AFTER_ADD_LIQUIDITY_FLAG),
            before_remove_liquidity=bool(bits & BEFORE_REMOVE_LIQUIDITY_FLAG),
            after_remove_liquidity=bool(bits & AFTER_REMOVE_LIQUIDITY_FLAG),
            before_swap=bool(bits & BEFORE_SWAP_FLAG),
            after_swap=bool(bits & AFTER_SWAP_FLAG),
            before_donate=bool(bits & BEFORE_DONATE_FLAG),
            after_donate=bool(bits & AFTER_DONATE_FLAG),
            before_swap_returns_delta=bool(bits & BEFORE_SWAP_RETURNS_DELTA_FLAG),
            after_swap_returns_delta=bool(bits & AFTER_SWAP_RETURNS_DELTA_FLAG),
            after_add_liquidity_returns_delta=bool(bits & AFTER_ADD_LIQUIDITY_RETURNS_DELTA_FLAG),
            after_remove_liquidity_returns_delta=bool(bits & AFTER_REMOVE_LIQUIDITY_RETURNS_DELTA_FLAG),
        )


@dataclass
class BytecodeAnalysisResult:
    """Resultado del escaneo cuantitativo de bytecode y hooks."""

    contract_address: Optional[str]
    has_tstore: bool
    has_tload: bool
    tstore_count: int
    tload_count: int
    delegatecall_count: int = 0
    selfdestruct_count: int = 0
    origin_count: int = 0
    create2_count: int = 0
    hook_permissions: Optional[HookPermissions] = None
    findings: List[str] = field(default_factory=list)
    risk_score: float = 0.0

    def to_dict(self) -> Dict[str, object]:
        """Convierte el resultado a formato serializable."""
        d = asdict(self)
        if self.hook_permissions:
            d["hook_permissions"] = asdict(self.hook_permissions)
        return d


class DeFiBytecodeScraper:
    """Motor de inspección de bytecode y verificación de invariantes en Smart Contracts."""

    def disassemble_opcodes(self, raw_bytecode: bytes) -> List[int]:
        """Desensambla una secuencia de bytes EVM saltando los operandos de PUSH1..PUSH32."""
        opcodes: List[int] = []
        idx = 0
        n = len(raw_bytecode)

        while idx < n:
            op = raw_bytecode[idx]
            opcodes.append(op)

            # Opcodes PUSH1 (0x60) hasta PUSH32 (0x7f)
            if 0x60 <= op <= 0x7F:
                push_bytes = op - 0x60 + 1
                idx += push_bytes + 1
            else:
                idx += 1

        return opcodes

    def analyze_bytecode(self, hex_code: str, address: Optional[str] = None) -> BytecodeAnalysisResult:
        """Escanea el bytecode EVM en busca de primitivas de riesgo e invariantes rotas."""
        clean_hex = hex_code.strip()
        if clean_hex.startswith("0x") or clean_hex.startswith("0X"):
            clean_hex = clean_hex[2:]

        try:
            raw_bytes = bytes.fromhex(clean_hex)
        except ValueError:
            return BytecodeAnalysisResult(
                contract_address=address,
                has_tstore=False,
                has_tload=False,
                tstore_count=0,
                tload_count=0,
                delegatecall_count=0,
                selfdestruct_count=0,
                origin_count=0,
                create2_count=0,
                hook_permissions=None,
                findings=["Bytecode hexadecimal corrupto o invalido"],
                risk_score=0.1,
            )

        opcodes = self.disassemble_opcodes(raw_bytes)
        tstore_count = opcodes.count(OPCODE_TSTORE)
        tload_count = opcodes.count(OPCODE_TLOAD)
        delegatecall_count = opcodes.count(OPCODE_DELEGATECALL)
        selfdestruct_count = opcodes.count(OPCODE_SELFDESTRUCT)
        origin_count = opcodes.count(OPCODE_ORIGIN)
        create2_count = opcodes.count(OPCODE_CREATE2)

        findings: List[str] = []
        risk = 0.0

        if tstore_count > 0 or tload_count > 0:
            findings.append(
                f"EIP-1153 Transient Storage activo: {tstore_count} TSTORE (0x5d), {tload_count} TLOAD (0x5e)"
            )
            if tstore_count > 0 and tload_count == 0:
                findings.append("Riesgo Causal: TSTORE sin TLOAD detectado; posible fuga o anergía de almacenamiento")
                risk += 0.3
            elif tstore_count > 0 and tstore_count > tload_count * 3:
                findings.append("Riesgo Causal: Posible reentrancy transitoria sin patrón balanceado de reseteo a cero")
                risk += 0.4

        if delegatecall_count > 0:
            findings.append(
                f"Riesgo de Inyección: {delegatecall_count} DELEGATECALL detectados (Proxy/Storage Collision)"
            )
            risk += min(0.35, delegatecall_count * 0.15)

        if selfdestruct_count > 0:
            findings.append(f"Anergía / EIP-6780: {selfdestruct_count} SELFDESTRUCT detectados (Opcode restringido)")
            risk += 0.2

        if origin_count > 0:
            findings.append(f"Riesgo de Autorización: {origin_count} ORIGIN (tx.origin) detectados")
            risk += 0.25

        if create2_count > 0:
            findings.append(f"Despliegue Dinámico: {create2_count} CREATE2 detectados (Potencial metamorfismo)")

        # Análisis de dirección y permisos si corresponde a un Hook de Uniswap v4
        hook_perms: Optional[HookPermissions] = None
        if address:
            hook_perms = HookPermissions.from_address(address)
            if hook_perms.raw_bits > 0:
                findings.append(f"Hook Uniswap v4 detectado (Máscara de bits: 0x{hook_perms.raw_bits:04x})")
                if hook_perms.before_swap:
                    findings.append("Hook tiene BEFORE_SWAP activo (Vector crítico de manipulación de precio/balance)")
                    risk += 0.3
                if hook_perms.before_swap_returns_delta or hook_perms.after_swap_returns_delta:
                    findings.append("Hook utiliza Delta Returns (Flash Accounting)")
                    risk += 0.2
                if tstore_count > 0 and (hook_perms.before_swap or hook_perms.after_swap):
                    findings.append("Superficie de Alta Exergía: Hook combina Transient Storage y Swaps")
                    risk += 0.4

        return BytecodeAnalysisResult(
            contract_address=address,
            has_tstore=tstore_count > 0,
            has_tload=tload_count > 0,
            tstore_count=tstore_count,
            tload_count=tload_count,
            delegatecall_count=delegatecall_count,
            selfdestruct_count=selfdestruct_count,
            origin_count=origin_count,
            create2_count=create2_count,
            hook_permissions=hook_perms,
            findings=findings,
            risk_score=min(1.0, risk),
        )

    def process_advisories(self, advisories: Sequence[BountyAdvisory]) -> List[BytecodeAnalysisResult]:
        """Procesa un lote de oportunidades del dominio EVM drenadas del despachador."""
        results: List[BytecodeAnalysisResult] = []
        for adv in advisories:
            if adv.domain == BountyDomain.DOMAIN_EVM:
                # Si el payload contiene un fragmento de bytecode o dirección, lo analiza
                analysis = self.analyze_bytecode(adv.payload_summary, address=adv.advisory_id)
                results.append(analysis)
        return results
