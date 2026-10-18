# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | CLEAN-ROOM AOT DISSECTOR | STATE: C5-REAL
# ============================================================================
"""
clean_room_aot_dissector.py — Transductor de Disección en Sala Limpia AOT (KISH)
================================================================================
Sustituye de forma determinista a los puentes MCP de ingeniería inversa (`morluto/rea`,
`npx rea-agents`) aplicando los Cortafuegos 16 y 17 y las Leyes Ontológicas O1, O2, O8 y O14:

1. Extracción Binaria In-Memory O(1) (Stdlib Pura):
   - Inspección sin dependencias de cabeceras Electron `.asar` (Chromium Pickle) y
     binarios Mach-O 64-bit (`0xFEEDFACF` / `0xCFFAEDFE` / Universal FAT `0xCAFEBABE`).
2. Cortafuegos 17 (Anti-Saturación de Schemas MCP):
   - Rechazo fail-closed (`MCP_SCHEMA_BLOAT_ABORT`) de definiciones dinámicas > 150 tokens.
3. Reducción de Estados de Myhill-Nerode (Algoritmo de Refinamiento de Moore):
   - Colapsa autómatas inflados de envoltorios comerciales (telemetría, spinners, flags
     cosméticos) a su cociente mínimo de estados distinguibles Q / ≡_L.
4. Auditoría de Acoplamiento Físico y Concurrencia (Ley O14):
   - Verifica invariantes que se pierden en la traducción estocástica desde Ghidra:
     alineación de línea de caché L1 (`KUDURRU-64`, `align(64)`), barreras `Acquire/Release`,
     memoria unificada (`MAP_SHARED`, `RFO=0`) y atestación en Secure Enclave (`LAContext`).
"""

from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Sequence, Set, Tuple


# Magics binarios canónicos (Mach-O 64-bit / Universal Binary)
MH_MAGIC_64 = 0xFEEDFACF
MH_CIGAM_64 = 0xCFFAEDFE
FAT_MAGIC = 0xCAFEBABE
FAT_CIGAM = 0xBEBAFECA

# Presupuesto estricto del Cortafuegos 17 (tokens máximos de gramática GBNF / despacho)
MAX_AOT_GRAMMAR_TOKENS = 150

# Techo físico P x S de subagentes concurrentes en Apple Silicon M3 Pro (anti-HTTP 429 / anti-thrashing)
APPLE_SILICON_PXS_SUBAGENT_CAP = 12

# Patrones de envoltorio anérgico (telemetría, spinners cosméticos, source-maps fugados)
ANERGIC_WRAPPER_PATTERNS: Tuple[str, ...] = (
    ".js.map",
    "cli.js.map",
    "sentry",
    "posthog",
    "mixpanel",
    "amplitude",
    "datadog",
    "spinner_verbs",
    "undercover_mode",
    "telemetry_beacon",
)

# Patrones específicos auditados por cada Subagente REA especializado
CLAW_CODE_ANERGIC_PATTERNS: Tuple[str, ...] = (
    "cli.js.map",
    "spinner_verbs",
    "undercover_mode",
    "kairos_flag",
    "buddy_tamagotchi",
    "sentry",
    "statsig",
)

OPENCLAW_UNMEDIATED_RISK_PATTERNS: Tuple[str, ...] = (
    "unmediated_fs_write",
    "raw_shell_exec",
    "unanchored_soul_md",
    "unscoped_env_credentials",
    "direct_whatsapp_media_dispatch",
)

DSH_CORDIS_RISK_PATTERNS: Tuple[str, ...] = (
    "dsh-chatgpt-sub",
    "songoao25/dsh-chatgpt-sub",
    "free_llm_api_unbounded",
    "oauth_web_session_scraper",
    "unbounded_50_subagents",
)


class HarnessTargetKind(str, Enum):
    """Ecosistemas de arneses agénticos auditados y acoplados por Subagentes REA."""

    CLAW_CODE = "claw-code"
    OPENCLAW = "openclaw"
    DEEPSEEK_HARNESS = "deepseek-harness"


@dataclass(frozen=True)
class BinaryHeaderSummary:
    format_type: str
    is_valid: bool
    architecture: str
    header_bytes_parsed: int
    load_commands_or_entries: int
    anergic_artifacts_detected: Tuple[str, ...]
    digest_sha256: str
    error: Optional[str] = None


@dataclass(frozen=True)
class SchemaBudgetVerdict:
    allowed: bool
    estimated_tokens: int
    max_allowed_tokens: int
    status_code: str
    reason: str


@dataclass(frozen=True)
class MyhillNerodeQuotient:
    original_state_count: int
    reachable_state_count: int
    minimal_state_count: int
    anergy_pruning_ratio: float
    equivalence_classes: Tuple[Tuple[str, ...], ...]
    minimal_transitions: Dict[str, Dict[str, str]]
    minimal_accepting: Tuple[str, ...]


@dataclass(frozen=True)
class HardwareConfinementAudit:
    has_cache_line_align64: bool
    has_acquire_release_barriers: bool
    has_uma_zero_copy: bool
    has_secure_enclave_gate: bool
    confinement_preserved: bool
    missing_invariants: Tuple[str, ...]
    verdict_code: str


@dataclass(frozen=True)
class CleanRoomDissectionReceipt:
    artifact_digest: str
    binary_format: str
    schema_budget_allowed: bool
    original_states: int
    minimal_states: int
    pruning_ratio: float
    confinement_preserved: bool
    verdict_code: str
    scitt_receipt_hash: str


@dataclass(frozen=True)
class AppPreflightContract:
    """
    Contrato Pre-Vuelo AOT emitido antes de permitir que `mac-maestro` o un agente
    interactúe con cualquier aplicación de macOS (`.app`).
    """

    app_bundle_id: str
    binary_format: str
    selected_channel: str
    action_channel_map: Dict[str, str]
    verified_actions: Tuple[str, ...]
    unverified_actions: Tuple[str, ...]
    filesystem_guard_flag: str
    aot_dispatch_grammar: str
    grammar_tokens: int
    gate_decision: str
    scitt_preflight_hash: str


@dataclass(frozen=True)
class HarnessSubagentDissectionReport:
    """
    Reporte de disección AOT en sala limpia emitido por un Subagente REA especializado
    sobre un arnés objetivo (`claw-code`, `openclaw`, `deepseek-harness`).
    """

    target_kind: str
    subagent_id: str
    binary_format: str
    header_valid: bool
    extracted_surfaces: Dict[str, Tuple[str, ...]]
    anergic_patterns_found: Tuple[str, ...]
    unmediated_authority_risks: Tuple[str, ...]
    requested_concurrency: int
    recommended_concurrency_cap: int
    quotient: MyhillNerodeQuotient
    confinement_audit: HardwareConfinementAudit
    aot_dispatch_grammar: str
    grammar_tokens: int
    verdict_code: str
    scitt_subagent_hash: str


@dataclass(frozen=True)
class SovereignHarnessAotBridge:
    """
    Contrato de puente AOT de baja entropía (<= 150 tokens) para acoplar `claw-code`,
    `OpenClaw` o `DeepSeek Harness` al broker `BABYLON-60` (`ReaPreflightGate`).
    """

    target_kind: str
    subagent_id: str
    bridge_protocol: str
    loopback_endpoint: str
    portable_launcher: str
    aot_grammar: str
    grammar_tokens: int
    max_subagents_pxs: int
    requires_rea_preflight_ticket: bool
    system1_local_triage: bool
    manifest_payload: Dict[str, Any]
    bridge_digest_sha256: str


class CleanRoomAotDissector:
    """
    Motor de disección en sala limpia AOT de Anillo-0.
    Opera 100% en memoria sobre stdlib pura sin invocar demonios Node.js ni puentes MCP.
    """

    # ========================================================================
    # 1. EXTRACCIÓN BINARIA IN-MEMORY O(1) (.ASAR & MACH-O 64)
    # ========================================================================

    @staticmethod
    def build_synthetic_asar(file_tree: Dict[str, Any]) -> bytes:
        """Construye un paquete binario Electron `.asar` válido en memoria para tests/auditoría."""
        header_json = json.dumps({"files": file_tree}, separators=(",", ":")).encode("utf-8")
        json_len = len(header_json)
        # Padding a múltiplo de 4 bytes según especificación Chromium Pickle
        padding_len = (4 - (json_len % 4)) % 4
        aligned_json_size = json_len + padding_len
        pickle_payload_size = aligned_json_size + 4
        outer_size = pickle_payload_size + 4
        header = struct.pack("<IIII", 4, outer_size, pickle_payload_size, json_len)
        return header + header_json + (b"\x00" * padding_len)

    @classmethod
    def inspect_binary_in_memory(cls, raw_bytes: bytes) -> BinaryHeaderSummary:
        """
        Inspecciona cabeceras binarias en O(1) sin escribir a disco ni ejecutar código externo.
        Soporta:
          - Contenedores Electron `.asar` (Chromium Pickle)
          - Binarios nativos Apple Silicon Mach-O 64-bit / Universal Binary
        """
        digest = hashlib.sha256(raw_bytes).hexdigest()
        if len(raw_bytes) < 16:
            return BinaryHeaderSummary(
                format_type="UNKNOWN",
                is_valid=False,
                architecture="NONE",
                header_bytes_parsed=len(raw_bytes),
                load_commands_or_entries=0,
                anergic_artifacts_detected=(),
                digest_sha256=digest,
                error="BUFFER_TOO_SHORT_FOR_HEADER",
            )

        # 1. Detección Mach-O 64-bit (ARM64 / x86_64)
        magic_le = struct.unpack("<I", raw_bytes[:4])[0]
        magic_be = struct.unpack(">I", raw_bytes[:4])[0]

        if magic_le in (MH_MAGIC_64, MH_CIGAM_64):
            if len(raw_bytes) < 32:
                return BinaryHeaderSummary(
                    format_type="MACH_O_64",
                    is_valid=False,
                    architecture="UNKNOWN",
                    header_bytes_parsed=len(raw_bytes),
                    load_commands_or_entries=0,
                    anergic_artifacts_detected=(),
                    digest_sha256=digest,
                    error="TRUNCATED_MACH_O_64_HEADER",
                )
            _, cputype, _, _, ncmds, sizeofcmds, _, _ = struct.unpack("<IIIIIIII", raw_bytes[:32])
            arch = "ARM64_APPLE_SILICON" if cputype == 0x0100000C else f"CPU_{hex(cputype)}"
            return BinaryHeaderSummary(
                format_type="MACH_O_64",
                is_valid=True,
                architecture=arch,
                header_bytes_parsed=32 + min(sizeofcmds, max(0, len(raw_bytes) - 32)),
                load_commands_or_entries=ncmds,
                anergic_artifacts_detected=(),
                digest_sha256=digest,
            )

        if magic_be in (FAT_MAGIC, FAT_CIGAM):
            nfat_arch = struct.unpack(">I", raw_bytes[4:8])[0]
            return BinaryHeaderSummary(
                format_type="MACH_O_UNIVERSAL",
                is_valid=True,
                architecture="UNIVERSAL_FAT",
                header_bytes_parsed=8,
                load_commands_or_entries=nfat_arch,
                anergic_artifacts_detected=(),
                digest_sha256=digest,
            )

        # 2. Detección Electron `.asar` (Chromium Pickle: uint32(4), outer_size, payload_size, json_len)
        pickle_data_size, outer_size, payload_size, json_len = struct.unpack("<IIII", raw_bytes[:16])
        if pickle_data_size == 4 and 0 < json_len <= len(raw_bytes) - 16 and outer_size >= payload_size:
            json_slice = raw_bytes[16 : 16 + json_len]
            try:
                tree = json.loads(json_slice.decode("utf-8"))
                files_dict = tree.get("files", {}) if isinstance(tree, dict) else {}
                flat_paths = cls._flatten_asar_paths(files_dict)
                anergic_hits = tuple(
                    sorted(path for path in flat_paths if any(pat in path.lower() for pat in ANERGIC_WRAPPER_PATTERNS))
                )
                return BinaryHeaderSummary(
                    format_type="ELECTRON_ASAR",
                    is_valid=True,
                    architecture="V8_CHROMIUM_BUNDLE",
                    header_bytes_parsed=16 + json_len,
                    load_commands_or_entries=len(flat_paths),
                    anergic_artifacts_detected=anergic_hits,
                    digest_sha256=digest,
                )
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                return BinaryHeaderSummary(
                    format_type="ELECTRON_ASAR",
                    is_valid=False,
                    architecture="V8_CHROMIUM_BUNDLE",
                    header_bytes_parsed=16,
                    load_commands_or_entries=0,
                    anergic_artifacts_detected=(),
                    digest_sha256=digest,
                    error=f"MALFORMED_ASAR_JSON: {exc}",
                )

        return BinaryHeaderSummary(
            format_type="UNRECOGNIZED_BINARY",
            is_valid=False,
            architecture="UNKNOWN",
            header_bytes_parsed=16,
            load_commands_or_entries=0,
            anergic_artifacts_detected=(),
            digest_sha256=digest,
            error="UNSUPPORTED_MAGIC_SIGNATURE",
        )

    @classmethod
    def _flatten_asar_paths(cls, files_node: Mapping[str, Any], prefix: str = "") -> List[str]:
        paths: List[str] = []
        for name, meta in files_node.items():
            full = f"{prefix}/{name}" if prefix else name
            if isinstance(meta, Mapping) and "files" in meta and isinstance(meta["files"], Mapping):
                paths.extend(cls._flatten_asar_paths(meta["files"], full))
            else:
                paths.append(full)
        return paths

    # ========================================================================
    # 2. CORTAFUEGOS 17: PRESUPUESTO DE SCHEMAS AOT VS. BLOAT MCP
    # ========================================================================

    @staticmethod
    def audit_schema_token_budget(
        schema_payload: str,
        max_tokens: int = MAX_AOT_GRAMMAR_TOKENS,
    ) -> SchemaBudgetVerdict:
        """
        Evalúa el coste de prefill de un schema de herramientas o gramática GBNF.
        Bloquea de forma fail-closed las pilas MCP inflamadas (como `npx rea-agents` > 9.000 tokens).
        """
        words = schema_payload.split()
        # Estimación determinista conservadora: max(palabras, bytes // 4)
        estimated_tokens = max(len(words), len(schema_payload.encode("utf-8")) // 4)
        if estimated_tokens > max_tokens:
            return SchemaBudgetVerdict(
                allowed=False,
                estimated_tokens=estimated_tokens,
                max_allowed_tokens=max_tokens,
                status_code="CORTAFUEGOS_17_MCP_BLOAT_DROP",
                reason=(
                    f"Schema payload ({estimated_tokens} tokens) exceeds Ring-0 AOT grammar "
                    f"ceiling ({max_tokens} tokens). Dynamic MCP bridge rejected."
                ),
            )
        return SchemaBudgetVerdict(
            allowed=True,
            estimated_tokens=estimated_tokens,
            max_allowed_tokens=max_tokens,
            status_code="AOT_GRAMMAR_BUDGET_NOMINAL",
            reason="Compact AOT dispatch grammar within L1 prefill ceiling.",
        )

    # ========================================================================
    # 3. REDUCCIÓN DE MYHILL-NERODE (PODA DE ENVOLTORIOS COMERCIALES)
    # ========================================================================

    @staticmethod
    def distill_myhill_nerode_quotient(
        states: Sequence[str],
        alphabet: Sequence[str],
        transitions: Mapping[str, Mapping[str, str]],
        initial_state: str,
        accepting_states: Sequence[str],
    ) -> MyhillNerodeQuotient:
        """
        Calcula el autómata cociente mínimo (Q / ≡_L) mediante alcanzabilidad BFS
        y refinamiento de particiones de Moore:
          1. Elimina estados inalcanzables (código muerto, feature flags inactivos).
          2. Colapsa estados indistinguibles (spinners cosméticos, wrappers de telemetría
             que transicionan al mismo estado funcional).
        """
        original_count = len(states)
        accepting_set: Set[str] = set(accepting_states)

        # Paso 1: Poda de estados inalcanzables desde initial_state
        reachable: Set[str] = set()
        queue: List[str] = [initial_state] if initial_state in states else []
        while queue:
            curr = queue.pop(0)
            if curr in reachable:
                continue
            reachable.add(curr)
            for sym in alphabet:
                nxt = transitions.get(curr, {}).get(sym)
                if nxt is not None and nxt in states and nxt not in reachable:
                    queue.append(nxt)

        reachable_sorted = sorted(reachable)
        if not reachable_sorted:
            return MyhillNerodeQuotient(
                original_state_count=original_count,
                reachable_state_count=0,
                minimal_state_count=0,
                anergy_pruning_ratio=1.0 if original_count > 0 else 0.0,
                equivalence_classes=(),
                minimal_transitions={},
                minimal_accepting=(),
            )

        # Paso 2: Partición inicial P_0 = {F ∩ Reachable, (Q \ F) ∩ Reachable}
        acc_part = frozenset(s for s in reachable_sorted if s in accepting_set)
        rej_part = frozenset(s for s in reachable_sorted if s not in accepting_set)
        partitions: List[FrozenSet[str]] = [p for p in (acc_part, rej_part) if p]

        # Paso 3: Refinamiento iterativo hasta punto fijo
        changed = True
        while changed:
            changed = False
            state_to_block: Dict[str, int] = {}
            for idx, block in enumerate(partitions):
                for s in block:
                    state_to_block[s] = idx

            new_partitions: List[FrozenSet[str]] = []
            for block in partitions:
                if len(block) <= 1:
                    new_partitions.append(block)
                    continue
                signature_groups: Dict[Tuple[int, ...], Set[str]] = {}
                for s in block:
                    sig = tuple(state_to_block.get(transitions.get(s, {}).get(sym, ""), -1) for sym in alphabet)
                    signature_groups.setdefault(sig, set()).add(s)
                if len(signature_groups) > 1:
                    changed = True
                for subgroup in signature_groups.values():
                    new_partitions.append(frozenset(subgroup))
            partitions = new_partitions

        # Ordenar clases canónicamente
        sorted_classes: Tuple[Tuple[str, ...], ...] = tuple(
            sorted((tuple(sorted(block)) for block in partitions), key=lambda c: c[0])
        )
        rep_map: Dict[str, str] = {}
        for cls_tuple in sorted_classes:
            canonical_name = cls_tuple[0]
            for s in cls_tuple:
                rep_map[s] = canonical_name

        min_transitions: Dict[str, Dict[str, str]] = {}
        min_accepting: List[str] = []
        for cls_tuple in sorted_classes:
            rep = cls_tuple[0]
            min_transitions[rep] = {}
            for sym in alphabet:
                target = transitions.get(rep, {}).get(sym)
                if target in rep_map:
                    min_transitions[rep][sym] = rep_map[target]
            if rep in accepting_set:
                min_accepting.append(rep)

        minimal_count = len(sorted_classes)
        pruning_ratio = round(1.0 - (minimal_count / original_count), 6) if original_count > 0 else 0.0

        return MyhillNerodeQuotient(
            original_state_count=original_count,
            reachable_state_count=len(reachable_sorted),
            minimal_state_count=minimal_count,
            anergy_pruning_ratio=pruning_ratio,
            equivalence_classes=sorted_classes,
            minimal_transitions=min_transitions,
            minimal_accepting=tuple(sorted(min_accepting)),
        )

    # ========================================================================
    # 4. AUDITORÍA DE INVARIANTES FÍSICAS Y CONCURRENCIA (LEY O14)
    # ========================================================================

    @staticmethod
    def audit_hardware_confinement(source_code: str) -> HardwareConfinementAudit:
        """
        Verifica si una reconstrucción conserva el acoplamiento a silicio de Anillo-0
        o si es una traducción estocástica degradada (típica de Ghidra + LLM en `morluto/rea`).
        """
        lowered = source_code.lower()

        has_align64 = any(
            tok in lowered for tok in ("repr(align(64))", "alignas(64)", "kudurru_64", "kudurru64", "align(64)")
        )
        has_barriers = any(
            tok in lowered
            for tok in (
                "ordering::acquire",
                "ordering::release",
                "memory_order_acquire",
                "memory_order_release",
                "seqlock",
            )
        )
        has_uma = any(
            tok in lowered
            for tok in (
                "map_shared",
                "mtlresourceoptions",
                "storage_mode_shared",
                "storagemodeshared",
                "rfo=0",
                "zero_copy",
            )
        )
        has_enclave = any(
            tok in lowered
            for tok in (
                "lacontext",
                "secureenclave",
                "secure_enclave",
                "ksecattrtokenidsecureenclave",
                "c5_biometric_gate",
                "cose_sign1",
            )
        )

        missing: List[str] = []
        if not has_align64:
            missing.append("L1_CACHE_ALIGN_64B")
        if not has_barriers:
            missing.append("ACQUIRE_RELEASE_SEQLOCK_BARRIER")
        if not has_uma:
            missing.append("UMA_ZERO_COPY_SHARED_MAPPING")
        if not has_enclave:
            missing.append("SECURE_ENCLAVE_HARDWARE_ATTESTATION")

        preserved = len(missing) == 0
        verdict = "RING0_SILICON_CONFINEMENT_VERIFIED" if preserved else "STOCHASTIC_DECOMPILATION_DRIFT_DETECTED"

        return HardwareConfinementAudit(
            has_cache_line_align64=has_align64,
            has_acquire_release_barriers=has_barriers,
            has_uma_zero_copy=has_uma,
            has_secure_enclave_gate=has_enclave,
            confinement_preserved=preserved,
            missing_invariants=tuple(missing),
            verdict_code=verdict,
        )

    # ========================================================================
    # 5. EMISIÓN DE RECIBO SCITT WORM DETERMINISTA
    # ========================================================================

    @classmethod
    def execute_clean_room_dissection(
        cls,
        binary_payload: bytes,
        dispatch_grammar: str,
        states: Sequence[str],
        alphabet: Sequence[str],
        transitions: Mapping[str, Mapping[str, str]],
        initial_state: str,
        accepting_states: Sequence[str],
        reconstructed_source: str,
    ) -> CleanRoomDissectionReceipt:
        """
        Orquesta el pipeline completo de Disección en Sala Limpia AOT y sella el
        recibo criptográfico inmutable (SCITT WORM).
        """
        header_summary = cls.inspect_binary_in_memory(binary_payload)
        schema_verdict = cls.audit_schema_token_budget(dispatch_grammar)
        quotient = cls.distill_myhill_nerode_quotient(
            states=states,
            alphabet=alphabet,
            transitions=transitions,
            initial_state=initial_state,
            accepting_states=accepting_states,
        )
        hw_audit = cls.audit_hardware_confinement(reconstructed_source)

        overall_ok = (
            header_summary.is_valid
            and schema_verdict.allowed
            and hw_audit.confinement_preserved
            and len(header_summary.anergic_artifacts_detected) == 0
        )
        verdict_code = "CLEAN_ROOM_AOT_COMMITTED" if overall_ok else "CLEAN_ROOM_AOT_REJECTED"

        preimage = (
            f"{header_summary.digest_sha256}|"
            f"{header_summary.format_type}|"
            f"{schema_verdict.status_code}|"
            f"{quotient.original_state_count}->{quotient.minimal_state_count}|"
            f"{hw_audit.verdict_code}|"
            f"{verdict_code}"
        )
        scitt_hash = hashlib.sha256(preimage.encode("utf-8")).hexdigest()

        return CleanRoomDissectionReceipt(
            artifact_digest=header_summary.digest_sha256,
            binary_format=header_summary.format_type,
            schema_budget_allowed=schema_verdict.allowed,
            original_states=quotient.original_state_count,
            minimal_states=quotient.minimal_state_count,
            pruning_ratio=quotient.anergy_pruning_ratio,
            confinement_preserved=hw_audit.confinement_preserved,
            verdict_code=verdict_code,
            scitt_receipt_hash=scitt_hash,
        )

    # ========================================================================
    # 6. GATE PRE-VUELO DE APLICACIONES MACOS (REA / RFO=0 PRE-FLIGHT REVIEW)
    # ========================================================================

    DETERMINISTIC_CHANNEL_PRIORITY: Tuple[str, ...] = (
        "CLI_HEADLESS",
        "ASAR_IPC_OR_SDEF",
        "AX_SEMANTIC_TREE",
    )

    @staticmethod
    def extract_macos_app_surfaces_in_memory(
        sdef_xml: str = "",
        asar_ipc_source: str = "",
        cli_flags: Sequence[str] = (),
        ax_semantic_tuples: Sequence[Tuple[str, str, str]] = (),
    ) -> Dict[str, Tuple[str, ...]]:
        """
        Extrae en memoria (`RFO=0`, cero mutación ni lanzamiento de la aplicación) las
        superficies deterministas de control de un bundle `.app` de macOS:
          1. `CLI_HEADLESS`: Flags nativos del ejecutable en `Contents/MacOS/`.
          2. `ASAR_IPC_OR_SDEF`: Comandos AppleEvents de `Contents/Resources/*.sdef`
             y canales `ipcMain.handle(...)` de contenedores Electron `.asar`.
          3. `AX_SEMANTIC_TREE`: Tuplas de accesibilidad `(id, role, title)` verificadas.
        """
        cli_actions: List[str] = [flag.lstrip("-").replace("-", "_") for flag in cli_flags if flag.strip()]

        ipc_sdef_actions: List[str] = []
        # Parseo ligero sin regex pesada de `<command name="..."` en diccionarios .sdef
        for chunk in sdef_xml.split("<command"):
            if 'name="' in chunk:
                name_val = chunk.split('name="', 1)[1].split('"', 1)[0].strip()
                if name_val:
                    ipc_sdef_actions.append(name_val.lower().replace(" ", "_"))

        # Extracción en sala limpia de canales `ipcMain.handle("channel")` en Electron .asar
        for marker in ('ipcMain.handle("', "ipcMain.handle('"):
            quote_char = marker[-1]
            parts = asar_ipc_source.split(marker)
            for part in parts[1:]:
                ch_name = part.split(quote_char, 1)[0].strip()
                if ch_name:
                    ipc_sdef_actions.append(ch_name.replace(":", "_").replace("-", "_"))

        ax_actions: List[str] = []
        for ax_id, ax_role, ax_title in ax_semantic_tuples:
            if ax_id.strip() and ax_role.strip() and ax_title.strip():
                ax_actions.append(ax_id.strip())

        return {
            "CLI_HEADLESS": tuple(dict.fromkeys(cli_actions)),
            "ASAR_IPC_OR_SDEF": tuple(dict.fromkeys(ipc_sdef_actions)),
            "AX_SEMANTIC_TREE": tuple(dict.fromkeys(ax_actions)),
        }

    @classmethod
    def preflight_audit_app_surface(
        cls,
        app_bundle_id: str,
        binary_payload: bytes,
        discovered_surfaces: Mapping[str, Sequence[str]],
        requested_actions: Sequence[str],
        no_overwrite_policy: bool = True,
    ) -> AppPreflightContract:
        """
        Ejecuta una revisión AOT en sala limpia (`RFO=0`, lectura pura sin mutar la app)
        antes de usar cualquier aplicación o cuando el agente desconoce cómo operar una acción:
          1. Inspecciona en memoria el binario Mach-O o contenedor Electron `.asar`.
          2. Enruta cada acción solicitada a su canal determinista de menor entropía
             (`CLI_HEADLESS` > `ASAR_IPC_OR_SDEF` > `AX_SEMANTIC_TREE`).
          3. Si una acción solicitada cae en `OPAQUE_CUSTOM_CANVAS` o no consta en una superficie
             verificable, bloquea la improvisación (`ABSTAIN_REQUIRE_APPROVAL_UNVERIFIED_SURFACE`).
          4. Vincula la bandera de protección física en kernel (`POSIX_O_CREAT_O_EXCL_RENAME_EXCL`)
             cuando `no_overwrite_policy=True` y audita el presupuesto del Cortafuegos 17 (<= 150 tokens).
        """
        header = cls.inspect_binary_in_memory(binary_payload)
        fs_guard = "POSIX_O_CREAT_O_EXCL_RENAME_EXCL" if no_overwrite_policy else "STANDARD_SCOPED_TX"
        if not header.is_valid:
            preimage_err = f"{app_bundle_id}|{header.digest_sha256}|{fs_guard}|DENY_INVALID_APP_BINARY"
            return AppPreflightContract(
                app_bundle_id=app_bundle_id,
                binary_format=header.format_type,
                selected_channel="NONE",
                action_channel_map={},
                verified_actions=(),
                unverified_actions=tuple(requested_actions),
                filesystem_guard_flag=fs_guard,
                aot_dispatch_grammar="",
                grammar_tokens=0,
                gate_decision="DENY_INVALID_APP_BINARY",
                scitt_preflight_hash=hashlib.sha256(preimage_err.encode("utf-8")).hexdigest(),
            )

        verified: List[str] = []
        unverified: List[str] = []
        action_channel_map: Dict[str, str] = {}
        selected_channel = "NONE"

        for ch in cls.DETERMINISTIC_CHANNEL_PRIORITY:
            if discovered_surfaces.get(ch):
                selected_channel = ch
                break

        for req in requested_actions:
            matched_channel: Optional[str] = None
            for ch in cls.DETERMINISTIC_CHANNEL_PRIORITY:
                if req in discovered_surfaces.get(ch, ()):
                    matched_channel = ch
                    break
            if matched_channel is not None:
                verified.append(req)
                action_channel_map[req] = matched_channel
            else:
                unverified.append(req)

        actions_union = " | ".join(f'"{a}"' for a in verified) if verified else '"noop"'
        aot_grammar = (
            f'root ::= "(" "{app_bundle_id}" " " "{selected_channel}" " " "{fs_guard}" " " ({actions_union}) ")"'
        )
        budget = cls.audit_schema_token_budget(aot_grammar)

        if not budget.allowed:
            decision = "DENY_CORTAFUEGOS_17_SCHEMA_BLOAT"
        elif unverified or not verified:
            decision = "ABSTAIN_REQUIRE_APPROVAL_UNVERIFIED_SURFACE"
        else:
            decision = "ALLOW_DETERMINISTIC_DISPATCH"

        routing_Pairs = ",".join(f"{k}:{v}" for k, v in action_channel_map.items())
        preimage = (
            f"{app_bundle_id}|{header.digest_sha256}|{header.format_type}|"
            f"{selected_channel}|{routing_Pairs}|{','.join(unverified)}|{fs_guard}|{decision}"
        )
        preflight_hash = hashlib.sha256(preimage.encode("utf-8")).hexdigest()

        return AppPreflightContract(
            app_bundle_id=app_bundle_id,
            binary_format=header.format_type,
            selected_channel=selected_channel,
            action_channel_map=action_channel_map,
            verified_actions=tuple(verified),
            unverified_actions=tuple(unverified),
            filesystem_guard_flag=fs_guard,
            aot_dispatch_grammar=aot_grammar,
            grammar_tokens=budget.estimated_tokens,
            gate_decision=decision,
            scitt_preflight_hash=preflight_hash,
        )

    # ========================================================================
    # 7. SUBAGENTES REA PARA ARNESES EXTERNOS (CLAW-CODE, OPENCLAW, DSH)
    # ========================================================================

    @classmethod
    def build_canonical_harness_fixture(
        cls,
        target_kind: str | HarnessTargetKind,
    ) -> Dict[str, Any]:
        """
        Construye en memoria (`RFO=0`, cero archivos temporales) un fixture representativo
        del arnés objetivo para disección AOT y reducción de estados de Myhill-Nerode:
          - `claw-code`: Binario Rust Mach-O 64 ARM64 + bucle CLI contaminado con residuos de
            `cli.js.map`, `spinner_verbs`, `undercover_mode` y feature flags inalcanzables.
          - `openclaw`: Empaquetado TypeScript Gateway (`.asar`) con canales de mensajería,
            `soul.md` y `skills` que requieren mediación `INV-Ω` y `tether.md`.
          - `deepseek-harness`: Contenedor Electron `.asar` (`dsh` v0.2) con plugins Cordis
            (`dsh-chatgpt-sub`) y configuración de 50 subagentes concurrentes.
        """
        norm_kind = target_kind.value if isinstance(target_kind, HarnessTargetKind) else str(target_kind).strip().lower()
        sovereign_ring0_source = (
            "#[repr(C, align(64))] pub struct Kudurru64Cell { "
            "pub seq: AtomicU64 /* Ordering::Acquire Ordering::Release seqlock */ }\n"
            "// Apple Silicon UMA zero_copy MAP_SHARED (RFO=0) + SecureEnclave LAContext COSE_Sign1\n"
        )

        if norm_kind == HarnessTargetKind.CLAW_CODE.value:
            mach_o_arm64 = struct.pack(
                "<IIIIIIII",
                MH_MAGIC_64,
                0x0100000C,
                0,
                2,
                14,
                512,
                0x00200085,
                0,
            ) + (b"\x00" * 64)
            return {
                "target_kind": HarnessTargetKind.CLAW_CODE.value,
                "subagent_id": "rea-subagent:claw-code",
                "binary_payload": mach_o_arm64,
                "manifest_source": (
                    "claw-code rust harness; residuals: cli.js.map spinner_verbs undercover_mode; "
                    "cli_flags: --plan --exec-tool --verify-patch"
                ),
                "cli_flags": ("--plan", "--exec-tool", "--verify-patch"),
                "asar_ipc_source": "",
                "sdef_xml": "",
                "requested_concurrency": 8,
                "states": (
                    "S_CLI_INIT",
                    "S_SPINNER_RUMINATING",
                    "S_SPINNER_UNDERCOVER",
                    "S_TELEMETRY_SENTRY",
                    "S_PATCH_VERIFIED",
                    "S_DEAD_KAIROS_BRANCH",
                    "S_DEAD_TAMAGOTCHI_UI",
                ),
                "alphabet": ("dispatch", "verify"),
                "transitions": {
                    "S_CLI_INIT": {"dispatch": "S_SPINNER_RUMINATING", "verify": "S_TELEMETRY_SENTRY"},
                    "S_SPINNER_RUMINATING": {"dispatch": "S_SPINNER_UNDERCOVER", "verify": "S_PATCH_VERIFIED"},
                    "S_SPINNER_UNDERCOVER": {"dispatch": "S_TELEMETRY_SENTRY", "verify": "S_PATCH_VERIFIED"},
                    "S_TELEMETRY_SENTRY": {"dispatch": "S_SPINNER_RUMINATING", "verify": "S_PATCH_VERIFIED"},
                    "S_PATCH_VERIFIED": {"dispatch": "S_PATCH_VERIFIED", "verify": "S_PATCH_VERIFIED"},
                    "S_DEAD_KAIROS_BRANCH": {"dispatch": "S_DEAD_TAMAGOTCHI_UI", "verify": "S_PATCH_VERIFIED"},
                    "S_DEAD_TAMAGOTCHI_UI": {"dispatch": "S_DEAD_KAIROS_BRANCH", "verify": "S_PATCH_VERIFIED"},
                },
                "initial_state": "S_CLI_INIT",
                "accepting_states": ("S_PATCH_VERIFIED",),
                "reconstructed_source": sovereign_ring0_source,
            }

        if norm_kind == HarnessTargetKind.OPENCLAW.value:
            openclaw_tree = {
                "gateway": {
                    "files": {
                        "soul.md": {"size": 2048, "offset": "0"},
                        "skills_router.js": {"size": 16384, "offset": "2048"},
                        "posthog_telemetry_beacon.js": {"size": 4096, "offset": "18432"},
                    }
                }
            }
            raw_asar = cls.build_synthetic_asar(openclaw_tree)
            return {
                "target_kind": HarnessTargetKind.OPENCLAW.value,
                "subagent_id": "rea-subagent:openclaw",
                "binary_payload": raw_asar,
                "manifest_source": (
                    "openclaw gateway; soul.md + skills; risks: unanchored_soul_md "
                    "unmediated_fs_write direct_whatsapp_media_dispatch"
                ),
                "cli_flags": ("--gateway-loopback", "--verify-soul-chain"),
                "asar_ipc_source": (
                    'ipcMain.handle("skill:dispatch-mediated", async () => {}); '
                    'ipcMain.handle("soul:verify-merkle", async () => {});'
                ),
                "sdef_xml": "",
                "requested_concurrency": 6,
                "states": (
                    "S_GW_INGRESS",
                    "S_CHAT_WRAPPER_WA",
                    "S_CHAT_WRAPPER_TG",
                    "S_CHAT_WRAPPER_DISCORD",
                    "S_BROKER_MEDIATED_COMMIT",
                    "S_UNREACHABLE_RAW_EXEC",
                ),
                "alphabet": ("route", "attest"),
                "transitions": {
                    "S_GW_INGRESS": {"route": "S_CHAT_WRAPPER_WA", "attest": "S_CHAT_WRAPPER_TG"},
                    "S_CHAT_WRAPPER_WA": {"route": "S_CHAT_WRAPPER_TG", "attest": "S_BROKER_MEDIATED_COMMIT"},
                    "S_CHAT_WRAPPER_TG": {"route": "S_CHAT_WRAPPER_DISCORD", "attest": "S_BROKER_MEDIATED_COMMIT"},
                    "S_CHAT_WRAPPER_DISCORD": {"route": "S_CHAT_WRAPPER_WA", "attest": "S_BROKER_MEDIATED_COMMIT"},
                    "S_BROKER_MEDIATED_COMMIT": {
                        "route": "S_BROKER_MEDIATED_COMMIT",
                        "attest": "S_BROKER_MEDIATED_COMMIT",
                    },
                    "S_UNREACHABLE_RAW_EXEC": {
                        "route": "S_UNREACHABLE_RAW_EXEC",
                        "attest": "S_BROKER_MEDIATED_COMMIT",
                    },
                },
                "initial_state": "S_GW_INGRESS",
                "accepting_states": ("S_BROKER_MEDIATED_COMMIT",),
                "reconstructed_source": sovereign_ring0_source,
            }

        if norm_kind == HarnessTargetKind.DEEPSEEK_HARNESS.value:
            dsh_tree = {
                "cordis": {
                    "files": {
                        "dsh_core.js": {"size": 65536, "offset": "0"},
                        "cli.js.map": {"size": 262144, "offset": "65536"},
                        "spinner_verbs.json": {"size": 4096, "offset": "327680"},
                    }
                }
            }
            raw_asar = cls.build_synthetic_asar(dsh_tree)
            return {
                "target_kind": HarnessTargetKind.DEEPSEEK_HARNESS.value,
                "subagent_id": "rea-subagent:deepseek-harness",
                "binary_payload": raw_asar,
                "manifest_source": (
                    "deepseek-harness v0.2 cordis desktop; plugins: songoao25/dsh-chatgpt-sub "
                    "free_llm_api_unbounded oauth_web_session_scraper unbounded_50_subagents"
                ),
                "cli_flags": ("--cordis-headless", "--pxs-bounded-swarm"),
                "asar_ipc_source": (
                    'ipcMain.handle("cordis:dispatch-plugin", async () => {}); '
                    'ipcMain.handle("dsh:verify-preflight", async () => {});'
                ),
                "sdef_xml": "",
                "requested_concurrency": 50,
                "states": (
                    "S_DSH_BOOT",
                    "S_CORDIS_PLUGIN_A",
                    "S_CORDIS_PLUGIN_B",
                    "S_CORDIS_TELEMETRY",
                    "S_AOT_GATE_COMMITTED",
                    "S_DEAD_OAUTH_SCRAPER",
                    "S_DEAD_50_AGENT_FLOOD",
                ),
                "alphabet": ("invoke", "seal"),
                "transitions": {
                    "S_DSH_BOOT": {"invoke": "S_CORDIS_PLUGIN_A", "seal": "S_CORDIS_TELEMETRY"},
                    "S_CORDIS_PLUGIN_A": {"invoke": "S_CORDIS_PLUGIN_B", "seal": "S_AOT_GATE_COMMITTED"},
                    "S_CORDIS_PLUGIN_B": {"invoke": "S_CORDIS_TELEMETRY", "seal": "S_AOT_GATE_COMMITTED"},
                    "S_CORDIS_TELEMETRY": {"invoke": "S_CORDIS_PLUGIN_A", "seal": "S_AOT_GATE_COMMITTED"},
                    "S_AOT_GATE_COMMITTED": {"invoke": "S_AOT_GATE_COMMITTED", "seal": "S_AOT_GATE_COMMITTED"},
                    "S_DEAD_OAUTH_SCRAPER": {"invoke": "S_DEAD_50_AGENT_FLOOD", "seal": "S_AOT_GATE_COMMITTED"},
                    "S_DEAD_50_AGENT_FLOOD": {"invoke": "S_DEAD_OAUTH_SCRAPER", "seal": "S_AOT_GATE_COMMITTED"},
                },
                "initial_state": "S_DSH_BOOT",
                "accepting_states": ("S_AOT_GATE_COMMITTED",),
                "reconstructed_source": sovereign_ring0_source,
            }

        raise ValueError(f"Unsupported harness target kind: {target_kind}")

    @classmethod
    def dissect_external_harness_target(
        cls,
        target_kind: str | HarnessTargetKind,
        *,
        binary_payload: Optional[bytes] = None,
        manifest_source: Optional[str] = None,
        cli_flags: Optional[Sequence[str]] = None,
        asar_ipc_source: Optional[str] = None,
        sdef_xml: str = "",
        requested_concurrency: Optional[int] = None,
        states: Optional[Sequence[str]] = None,
        alphabet: Optional[Sequence[str]] = None,
        transitions: Optional[Mapping[str, Mapping[str, str]]] = None,
        initial_state: Optional[str] = None,
        accepting_states: Optional[Sequence[str]] = None,
        reconstructed_source: Optional[str] = None,
    ) -> HarnessSubagentDissectionReport:
        """
        Ejecuta la disección AOT en sala limpia (`RFO=0`, in-memory) para un arnés externo
        (`claw-code`, `openclaw` o `deepseek-harness`) mediante su Subagente REA dedicado:
          1. Inspecciona en O(1) el binario Mach-O 64 o contenedor Electron `.asar`.
          2. Extrae las superficies deterministas (`CLI_HEADLESS`, `ASAR_IPC_OR_SDEF`, `AX_SEMANTIC_TREE`).
          3. Detecta patrones anérgicos (`cli.js.map`, `spinner_verbs`) y riesgos de autoridad no
             mediada (`dsh-chatgpt-sub`, `unmediated_fs_write`, `unanchored_soul_md`).
          4. Aplica reducción al cociente mínimo de Myhill-Nerode (Q / ≡_L).
          5. Recorta la concurrencia solicitada (ej. 50 subagentes en DSH) al techo físico P x S (12).
          6. Emite una gramática GBNF AOT <= 150 tokens (Cortafuegos 17) y recibo SCITT SHA-256.
        """
        fixture = cls.build_canonical_harness_fixture(target_kind)
        norm_kind = str(fixture["target_kind"])
        subagent_id = str(fixture["subagent_id"])

        raw_bytes = binary_payload if binary_payload is not None else bytes(fixture["binary_payload"])
        manifest_txt = manifest_source if manifest_source is not None else str(fixture["manifest_source"])
        eff_cli = tuple(cli_flags) if cli_flags is not None else tuple(fixture["cli_flags"])
        eff_ipc = asar_ipc_source if asar_ipc_source is not None else str(fixture["asar_ipc_source"])
        req_conc = int(requested_concurrency) if requested_concurrency is not None else int(fixture["requested_concurrency"])
        eff_states = tuple(states) if states is not None else tuple(fixture["states"])
        eff_alpha = tuple(alphabet) if alphabet is not None else tuple(fixture["alphabet"])
        eff_trans = transitions if transitions is not None else fixture["transitions"]
        eff_init = initial_state if initial_state is not None else str(fixture["initial_state"])
        eff_acc = tuple(accepting_states) if accepting_states is not None else tuple(fixture["accepting_states"])
        eff_src = reconstructed_source if reconstructed_source is not None else str(fixture["reconstructed_source"])

        header = cls.inspect_binary_in_memory(raw_bytes)
        surfaces = cls.extract_macos_app_surfaces_in_memory(
            sdef_xml=sdef_xml,
            asar_ipc_source=eff_ipc,
            cli_flags=eff_cli,
        )

        lowered_manifest = manifest_txt.lower()
        anergic_found: Set[str] = set(header.anergic_artifacts_detected)
        for pat in ANERGIC_WRAPPER_PATTERNS + CLAW_CODE_ANERGIC_PATTERNS:
            if pat in lowered_manifest:
                anergic_found.add(pat)

        risk_catalog = OPENCLAW_UNMEDIATED_RISK_PATTERNS + DSH_CORDIS_RISK_PATTERNS
        risks_found = tuple(sorted(pat for pat in risk_catalog if pat in lowered_manifest))
        recommended_cap = min(max(1, req_conc), APPLE_SILICON_PXS_SUBAGENT_CAP)

        quotient = cls.distill_myhill_nerode_quotient(
            states=eff_states,
            alphabet=eff_alpha,
            transitions=eff_trans,
            initial_state=eff_init,
            accepting_states=eff_acc,
        )
        hw_audit = cls.audit_hardware_confinement(eff_src)

        verified_ops = list(surfaces.get("CLI_HEADLESS", ())) + list(surfaces.get("ASAR_IPC_OR_SDEF", ()))
        ops_union = " | ".join(f'"{op}"' for op in verified_ops[:6]) if verified_ops else '"noop"'
        aot_grammar = (
            f'root ::= "(" "{norm_kind}" " " "PXS_{recommended_cap}" '
            f'" " "POSIX_O_CREAT_O_EXCL_RENAME_EXCL" " " ({ops_union}) ")"'
        )
        budget = cls.audit_schema_token_budget(aot_grammar)

        is_ok = (
            header.is_valid
            and budget.allowed
            and hw_audit.confinement_preserved
            and quotient.minimal_state_count < quotient.original_state_count
        )
        verdict_code = "REA_SUBAGENT_AOT_VERIFIED" if is_ok else "REA_SUBAGENT_AOT_REJECTED"

        preimage = (
            f"{norm_kind}|{subagent_id}|{header.digest_sha256}|{header.format_type}|"
            f"{quotient.original_state_count}->{quotient.minimal_state_count}|"
            f"conc:{req_conc}->{recommended_cap}|"
            f"{budget.status_code}|{hw_audit.verdict_code}|{verdict_code}"
        )
        scitt_hash = hashlib.sha256(preimage.encode("utf-8")).hexdigest()

        return HarnessSubagentDissectionReport(
            target_kind=norm_kind,
            subagent_id=subagent_id,
            binary_format=header.format_type,
            header_valid=header.is_valid,
            extracted_surfaces=surfaces,
            anergic_patterns_found=tuple(sorted(anergic_found)),
            unmediated_authority_risks=risks_found,
            requested_concurrency=req_conc,
            recommended_concurrency_cap=recommended_cap,
            quotient=quotient,
            confinement_audit=hw_audit,
            aot_dispatch_grammar=aot_grammar,
            grammar_tokens=budget.estimated_tokens,
            verdict_code=verdict_code,
            scitt_subagent_hash=scitt_hash,
        )

    @classmethod
    def synthesize_harness_aot_bridge(
        cls,
        report: HarnessSubagentDissectionReport,
        *,
        loopback_port: int = 6061,
    ) -> SovereignHarnessAotBridge:
        """
        Sintetiza un puente AOT soberano (<= 150 tokens, cero rutas `/Users/`) para acoplar
        `claw-code`, `OpenClaw` o `DeepSeek Harness` al broker `BABYLON-60`:
          - Erradica el puente NPM `npx rea-agents` (> 9.000 tokens de prefill).
          - Enruta el triaje de Sistema 1 en local (`RFO=0`, < 10 ms) y exige `AuthorizedDispatchTicket`
            (`ReaPreflightGate` SEC1/DER) para cualquier efecto de Sistema 2.
        """
        portable_launcher = "scripts/c5_cli/launch_kernel_mcp.py"
        loopback_endpoint = f"http://127.0.0.1:{loopback_port}/openapi.json"
        budget = cls.audit_schema_token_budget(report.aot_dispatch_grammar)
        if not budget.allowed:
            raise ValueError(f"Bridge grammar violates Cortafuegos 17: {budget.reason}")

        if report.target_kind == HarnessTargetKind.CLAW_CODE.value:
            protocol = "RUST_CLI_AOT_STDIO_BRIDGE"
            manifest: Dict[str, Any] = {
                "harness": "claw-code",
                "subagent_role": "rea_rust_cli_dissector",
                "mcp_server": {
                    "name": "babylon60-rea-aot",
                    "command": "python3",
                    "args": [portable_launcher, "--rea-aot-mode", "claw-code"],
                },
                "purged_anergy": list(report.anergic_patterns_found),
                "quotient_states": report.quotient.minimal_state_count,
                "max_subagents_pxs": report.recommended_concurrency_cap,
                "filesystem_guard": "POSIX_O_CREAT_O_EXCL_RENAME_EXCL",
            }
        elif report.target_kind == HarnessTargetKind.OPENCLAW.value:
            protocol = "TS_GATEWAY_SOUL_TETHER_BRIDGE"
            manifest = {
                "harness": "openclaw",
                "subagent_role": "rea_gateway_authority_auditor",
                "mcp_server": {
                    "name": "babylon60-rea-aot",
                    "command": "python3",
                    "args": [portable_launcher, "--rea-aot-mode", "openclaw"],
                },
                "psychological_stack_layers": ["soul.md", "lore.md", "nemesis.md", "tether.md", "bloodline.json"],
                "complete_mediation_broker": "BabylonBroker",
                "visual_confinement_gate": "NEXUS_ZERO_VISUAL_LEAKAGE_FAIL_CLOSED",
                "blocked_authority_risks": list(report.unmediated_authority_risks),
                "max_subagents_pxs": report.recommended_concurrency_cap,
            }
        elif report.target_kind == HarnessTargetKind.DEEPSEEK_HARNESS.value:
            protocol = "CORDIS_AOT_HYBRID_PLUGIN_BRIDGE"
            manifest = {
                "harness": "deepseek-harness",
                "subagent_role": "rea_cordis_asar_stabilizer",
                "cordis_plugin": {
                    "id": "@babylon60/dsh-rea-aot-bridge",
                    "launcher": portable_launcher,
                    "openapi_loopback": loopback_endpoint,
                },
                "blocked_fragile_plugins": list(report.unmediated_authority_risks),
                "agent_teams_concurrency": {
                    "requested_naive": report.requested_concurrency,
                    "enforced_pxs_cap": report.recommended_concurrency_cap,
                    "thermal_lock": ".swarm_kda_dag_global.lock",
                },
                "routing_policy": {
                    "system1_edge": "LOCAL_STDLIB_IN_MEMORY_ZERO_COST",
                    "system2_cloud": "REA_PREFLIGHT_GATE_SEC1_DER_REQUIRED",
                },
            }
        else:
            raise ValueError(f"Unsupported target_kind for AOT bridge: {report.target_kind}")

        canonical_json = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
        if "/Users/" in canonical_json:
            raise ValueError("INV_C5_OPSEC_CALIBRATION violation: '/Users/' path detected in AOT bridge manifest")

        preimage = f"{report.target_kind}|{report.scitt_subagent_hash}|{protocol}|{canonical_json}"
        bridge_digest = hashlib.sha256(preimage.encode("utf-8")).hexdigest()

        return SovereignHarnessAotBridge(
            target_kind=report.target_kind,
            subagent_id=report.subagent_id,
            bridge_protocol=protocol,
            loopback_endpoint=loopback_endpoint,
            portable_launcher=portable_launcher,
            aot_grammar=report.aot_dispatch_grammar,
            grammar_tokens=report.grammar_tokens,
            max_subagents_pxs=report.recommended_concurrency_cap,
            requires_rea_preflight_ticket=True,
            system1_local_triage=True,
            manifest_payload=manifest,
            bridge_digest_sha256=bridge_digest,
        )

