#!/usr/bin/env python3
"""
test_clean_room_aot_dissector.py — Suite de Verificación en Silicio (Cortafuegos 16 y 17)
=========================================================================================
Valida deterministamente `CleanRoomAotDissector` frente al paradigma `morluto/rea` (`npx rea-agents`):
  1. Inspección in-memory O(1) de paquetes Electron `.asar` y binarios Mach-O 64-bit Apple Silicon.
  2. Detección fail-closed de residuos anérgicos (`cli.js.map`, telemetría, spinners).
  3. Cortafuegos 17: Bloqueo de schemas MCP inflados (> 150 tokens) vs. gramáticas GBNF AOT.
  4. Teorema de Myhill-Nerode: Reducción del autómata inflado de un envoltorio comercial a su
     cociente mínimo de estados distinguibles (Q / ≡_L).
  5. Ley O14: Detección de pérdida de barreras de memoria (`Acquire/Release`), `align(64)`,
     UMA Zero-Copy y `Secure Enclave` en traducciones estocásticas desde Ghidra.
"""

from __future__ import annotations

import os
import struct
import sys

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "01_KISH_ENGINE")),
)

from babylon60.transducers.clean_room_aot_dissector import (
    CleanRoomAotDissector,
    MH_MAGIC_64,
)


def test_in_memory_asar_header_dissection_and_anergy_detection() -> None:
    """Verifica el parseo Chromium Pickle de un `.asar` y la detección de `cli.js.map` y telemetría."""
    bloated_tree = {
        "dist": {
            "files": {
                "cli.js": {"size": 184000, "offset": "0"},
                "cli.js.map": {"size": 512000, "offset": "184000"},
                "spinner_verbs.json": {"size": 4200, "offset": "696000"},
                "posthog_telemetry_beacon.js": {"size": 9100, "offset": "700200"},
            }
        }
    }
    raw_asar = CleanRoomAotDissector.build_synthetic_asar(bloated_tree)
    summary = CleanRoomAotDissector.inspect_binary_in_memory(raw_asar)

    assert summary.is_valid is True
    assert summary.format_type == "ELECTRON_ASAR"
    assert summary.load_commands_or_entries == 4
    assert "dist/cli.js.map" in summary.anergic_artifacts_detected
    assert "dist/spinner_verbs.json" in summary.anergic_artifacts_detected
    assert "dist/posthog_telemetry_beacon.js" in summary.anergic_artifacts_detected


def test_in_memory_mach_o_64_apple_silicon_header() -> None:
    """Verifica la identificación O(1) de un binario nativo Mach-O 64-bit ARM64 (Apple Silicon)."""
    cputype_arm64 = 0x0100000C
    cpusubtype_all = 0x00000000
    filetype_execute = 0x00000002
    ncmds = 16
    sizeofcmds = 1024
    flags = 0x00200085
    reserved = 0
    mach_o_header = struct.pack(
        "<IIIIIIII",
        MH_MAGIC_64,
        cputype_arm64,
        cpusubtype_all,
        filetype_execute,
        ncmds,
        sizeofcmds,
        flags,
        reserved,
    )
    summary = CleanRoomAotDissector.inspect_binary_in_memory(mach_o_header + (b"\x00" * 64))

    assert summary.is_valid is True
    assert summary.format_type == "MACH_O_64"
    assert summary.architecture == "ARM64_APPLE_SILICON"
    assert summary.load_commands_or_entries == 16
    assert summary.anergic_artifacts_detected == ()


def test_cortafuegos_17_mcp_schema_bloat_vs_aot_grammar() -> None:
    """Verifica que un schema MCP inflado (estilo `npx rea-agents`) es abortado de forma fail-closed."""
    bloated_mcp_schemas = " ".join(
        [f'{{"tool": "ghidra_decompile_fn_{i}", "description": "verbose mcp schema"}}' for i in range(250)]
    )
    verdict_bloat = CleanRoomAotDissector.audit_schema_token_budget(bloated_mcp_schemas)
    assert verdict_bloat.allowed is False
    assert verdict_bloat.status_code == "CORTAFUEGOS_17_MCP_BLOAT_DROP"
    assert verdict_bloat.estimated_tokens > 150

    compact_gbnf = 'root ::= "(" action " " target " " digest ")"'
    verdict_aot = CleanRoomAotDissector.audit_schema_token_budget(compact_gbnf)
    assert verdict_aot.allowed is True
    assert verdict_aot.status_code == "AOT_GRAMMAR_BUDGET_NOMINAL"


def test_myhill_nerode_quotient_collapses_wrapper_bloat() -> None:
    """
    Verifica que un autómata comercial con estados redundantes de spinner, telemetría y
    feature flags muertos (inalcanzables) colapsa exactamente a su cociente mínimo de Myhill-Nerode.
    """
    states = [
        "S_INIT",
        "S_SPINNER_RUMINATING",
        "S_SPINNER_FLIBBERTIGIBBETING",
        "S_TELEMETRY_FLUSH",
        "S_COMMITTED",
        "S_DEAD_KAIROS_FLAG",
        "S_DEAD_BUDDY_TAMAGOTCHI",
    ]
    alphabet = ["dispatch", "verify"]
    # Los tres estados intermedios (S_SPINNER_*, S_TELEMETRY_FLUSH) tienen transiciones idénticas
    # hacia S_COMMITTED y no son estados de aceptación: son equivalentes bajo Myhill-Nerode.
    transitions = {
        "S_INIT": {
            "dispatch": "S_SPINNER_RUMINATING",
            "verify": "S_TELEMETRY_FLUSH",
        },
        "S_SPINNER_RUMINATING": {
            "dispatch": "S_SPINNER_FLIBBERTIGIBBETING",
            "verify": "S_COMMITTED",
        },
        "S_SPINNER_FLIBBERTIGIBBETING": {
            "dispatch": "S_TELEMETRY_FLUSH",
            "verify": "S_COMMITTED",
        },
        "S_TELEMETRY_FLUSH": {
            "dispatch": "S_SPINNER_RUMINATING",
            "verify": "S_COMMITTED",
        },
        "S_COMMITTED": {
            "dispatch": "S_COMMITTED",
            "verify": "S_COMMITTED",
        },
        # Estados inalcanzables (feature flags muertos en el bundle)
        "S_DEAD_KAIROS_FLAG": {
            "dispatch": "S_DEAD_BUDDY_TAMAGOTCHI",
            "verify": "S_COMMITTED",
        },
        "S_DEAD_BUDDY_TAMAGOTCHI": {
            "dispatch": "S_DEAD_KAIROS_FLAG",
            "verify": "S_COMMITTED",
        },
    }

    quotient = CleanRoomAotDissector.distill_myhill_nerode_quotient(
        states=states,
        alphabet=alphabet,
        transitions=transitions,
        initial_state="S_INIT",
        accepting_states=["S_COMMITTED"],
    )

    assert quotient.original_state_count == 7
    assert quotient.reachable_state_count == 5
    # Clases mínimas: {S_INIT}, {S_SPINNER_RUMINATING, S_SPINNER_FLIBBERTIGIBBETING, S_TELEMETRY_FLUSH}, {S_COMMITTED}
    assert quotient.minimal_state_count == 3
    assert quotient.anergy_pruning_ratio > 0.55


def test_hardware_confinement_audit_and_scitt_receipt() -> None:
    """
    Contrasta un clon estocástico generado desde pseudocódigo de Ghidra (que pierde barreras
    y Secure Enclave) frente a una reconstrucción soberana en Anillo-0.
    """
    stochastic_llm_clone = """
    pub struct ClonedState {
        pub seq: u64,
        pub payload: Vec<u8>,
    }
    """
    audit_bad = CleanRoomAotDissector.audit_hardware_confinement(stochastic_llm_clone)
    assert audit_bad.confinement_preserved is False
    assert audit_bad.verdict_code == "STOCHASTIC_DECOMPILATION_DRIFT_DETECTED"
    assert "L1_CACHE_ALIGN_64B" in audit_bad.missing_invariants
    assert "SECURE_ENCLAVE_HARDWARE_ATTESTATION" in audit_bad.missing_invariants

    sovereign_ring0_source = """
    #[repr(C, align(64))]
    pub struct Kudurru64Cell {
        pub seq: AtomicU64, // Ordering::Acquire / Ordering::Release seqlock
    }
    // Apple Silicon UMA zero_copy MAP_SHARED (RFO=0) + SecureEnclave LAContext COSE_Sign1
    """
    mach_o_header = struct.pack(
        "<IIIIIIII",
        MH_MAGIC_64,
        0x0100000C,
        0,
        2,
        8,
        256,
        0,
        0,
    )
    receipt = CleanRoomAotDissector.execute_clean_room_dissection(
        binary_payload=mach_o_header,
        dispatch_grammar='root ::= "(" action " " scope ")"',
        states=["S0", "S1_DUP", "S1_DUP2", "S_DONE"],
        alphabet=["step"],
        transitions={
            "S0": {"step": "S1_DUP"},
            "S1_DUP": {"step": "S_DONE"},
            "S1_DUP2": {"step": "S_DONE"},
            "S_DONE": {"step": "S_DONE"},
        },
        initial_state="S0",
        accepting_states=["S_DONE"],
        reconstructed_source=sovereign_ring0_source,
    )

    assert receipt.verdict_code == "CLEAN_ROOM_AOT_COMMITTED"
    assert receipt.confinement_preserved is True
    assert receipt.schema_budget_allowed is True
    assert len(receipt.scitt_receipt_hash) == 64


def test_preflight_app_surface_review_and_abstention() -> None:
    """
    Verifica el Gate Pre-Vuelo AOT (`preflight_audit_app_surface`) y la extracción
    en memoria (`extract_macos_app_surfaces_in_memory`, `RFO=0`) antes de operar una app:
      1. Extrae acciones desde diccionarios `.sdef`, canales `.asar` (`ipcMain.handle`),
         flags CLI y tuplas `AXUIElement` `(id, role, title)`.
      2. Enruta cada acción a su canal determinista de menor entropía (`action_channel_map`)
         y sella la guardia `POSIX_O_CREAT_O_EXCL_RENAME_EXCL`.
      3. Si el agente no sabe o la acción cae en un lienzo opaco (`OPAQUE_CUSTOM_CANVAS`),
         se abstiene de improvisar (`ABSTAIN_REQUIRE_APPROVAL_UNVERIFIED_SURFACE`).
    """
    mach_o_header = struct.pack(
        "<IIIIIIII",
        MH_MAGIC_64,
        0x0100000C,
        0,
        2,
        12,
        512,
        0,
        0,
    )
    sdef_xml = (
        '<dictionary><suite name="DAW"><command name="organize_finder_folder" code="fndrorgan"/></suite></dictionary>'
    )
    asar_ipc = 'ipcMain.handle("project:verify-header", async () => {});'
    surfaces = CleanRoomAotDissector.extract_macos_app_surfaces_in_memory(
        sdef_xml=sdef_xml,
        asar_ipc_source=asar_ipc,
        cli_flags=["--render-stems-wav"],
        ax_semantic_tuples=[("open_export_dialog", "AXButton", "Export Stems...")],
    )

    # Caso 1: Flujo determinista conocido (FL Studio -> exportar stems -> organizar en Finder sin sobrescribir)
    contract_ok = CleanRoomAotDissector.preflight_audit_app_surface(
        app_bundle_id="com.image-line.flstudio",
        binary_payload=mach_o_header + (b"\x00" * 32),
        discovered_surfaces=surfaces,
        requested_actions=["render_stems_wav", "organize_finder_folder", "open_export_dialog"],
        no_overwrite_policy=True,
    )
    assert contract_ok.gate_decision == "ALLOW_DETERMINISTIC_DISPATCH"
    assert contract_ok.selected_channel == "CLI_HEADLESS"
    assert contract_ok.action_channel_map == {
        "render_stems_wav": "CLI_HEADLESS",
        "organize_finder_folder": "ASAR_IPC_OR_SDEF",
        "open_export_dialog": "AX_SEMANTIC_TREE",
    }
    assert contract_ok.filesystem_guard_flag == "POSIX_O_CREAT_O_EXCL_RENAME_EXCL"
    assert contract_ok.verified_actions == (
        "render_stems_wav",
        "organize_finder_folder",
        "open_export_dialog",
    )
    assert contract_ok.unverified_actions == ()
    assert contract_ok.grammar_tokens <= 150

    # Caso 2: Acción sobre lienzo opaco o desconocida -> abstención fail-closed sin improvisar clics
    contract_abstain = CleanRoomAotDissector.preflight_audit_app_surface(
        app_bundle_id="com.image-line.flstudio",
        binary_payload=mach_o_header + (b"\x00" * 32),
        discovered_surfaces=surfaces,
        requested_actions=["render_stems_wav", "tweak_vst_opengl_knob"],
        no_overwrite_policy=True,
    )
    assert contract_abstain.gate_decision == "ABSTAIN_REQUIRE_APPROVAL_UNVERIFIED_SURFACE"
    assert contract_abstain.verified_actions == ("render_stems_wav",)
    assert contract_abstain.unverified_actions == ("tweak_vst_opengl_knob",)
