#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.4 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | COMPILER_DERIVED EXERGY SCALE (21.000)
# ============================================================================
# [Causal-Determinist] Exergy-Maximized

"""
sync_skills_registry.py - Compilador determinista de la ontología de habilidades (3 Evaluadores:
Silicio + Kolmogorov + Causal = 21.000) y sincronización atómica con:
  1. ~/10_PROJECTS/BABYLON-60/docs/skills.json
  2. ~/.gemini/config/skills/skills.json
  3. ~/.gemini/config/SKILLS.md
"""

from __future__ import annotations

import json
import re
import sys
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# Base Paths
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SCRIPTS_DIR.parent
SKILLS_DIR = Path.home() / ".gemini" / "config" / "skills"
CONFIG_SKILLS_MD = Path.home() / ".gemini" / "config" / "SKILLS.md"
WS_SKILLS_DIR = REPO_ROOT / ".agents" / "skills"
DOCS_SKILLS_JSON = REPO_ROOT / "docs" / "skills.json"
GLOBAL_SKILLS_JSON = SKILLS_DIR / "skills.json"

# Canonical Skill Definitions (100% Purge of Ghost/Stub Skills, 100% Coverage of Physical Fleet)
SKILL_TIER_MAPPING: Dict[str, Dict[str, Any]] = {
    # Kernel & Meta-Kernel (Tier S: >= 21.000 — Ring-0 / Meta-Orchestration)
    "cortex-kernel": {"tier": 23000, "category": "Kernel", "canonical_alias": "kernel-root", "display_name": "CORTEX Root Kernel"},
    "c5-kudurru-64": {"tier": 22500, "category": "Kernel", "canonical_alias": "kernel-seqlock-filter", "display_name": "Cerrojo Lock-Free KUDURRU-64 (Ring-0 Gravity Filter)"},
    "shared-manifest-kernel": {"tier": 22000, "category": "Kernel", "canonical_alias": "kernel-shared-manifest", "display_name": "Núcleo de Memoria Compartida Lock-Free (64B C-ABI)"},
    "c5-mushushu-0": {"tier": 22000, "category": "Kernel", "canonical_alias": "kernel-epistemic-firewall", "display_name": "Oráculo Formal & Firewall de Apoptosis MUSHUSHU-0 (Ring-0)"},
    "c5-larsa-120": {"tier": 21800, "category": "Kernel", "canonical_alias": "kernel-bft-consensus", "display_name": "Consenso BFT Isostático LARSA-120 (Tríada Rust/Lean4/Z3)"},
    "cortex-skill-composer": {"tier": 21500, "category": "Meta-Kernel", "canonical_alias": "swarm-skill-composer", "display_name": "Componedor & Orquestador de Cadenas de Skills"},
    "thermo-audit": {"tier": 21500, "category": "Kernel", "canonical_alias": "kernel-thermo-audit", "display_name": "Auditoría Termodinámica de Silicio y Concurrencia"},
    "c5-thermos-audit": {"tier": 21400, "category": "Kernel", "canonical_alias": "kernel-double-thermo-audit", "display_name": "Auditoría Termonuclear de Silicio & Código (Double Thermo)"},
    "c5-enki-60": {"tier": 21400, "category": "Nucleus", "canonical_alias": "kernel-sexagesimal-math", "display_name": "Motor Aritmético de Precisión Sexagesimal ENKI-60"},
    "cortex-skill-auditor": {"tier": 21200, "category": "Meta-Kernel", "canonical_alias": "swarm-skill-auditor", "display_name": "Auditor Exergético de Skills CORTEX Engine"},
    "c5-autonomous-agent-primitives": {"tier": 21200, "category": "Meta-Kernel", "canonical_alias": "swarm-agent-primitives", "display_name": "Catálogo Canónico y Transductor de 47 Primitivas de Agente Autónomo"},
    "rlhf-sentinel": {"tier": 21200, "category": "Governance", "canonical_alias": "kernel-rlhf-sentinel", "display_name": "Centinela de Contención de IA y Barreras IPC Ring-0"},
    "c5-information-thermodynamics": {"tier": 21200, "category": "Nucleus", "canonical_alias": "epistemic-info-thermo", "display_name": "Termodinámica de la Información y Geometría Estadística (Fisher-Chentsov)"},
    "cortex-skill-genesis": {"tier": 21000, "category": "Meta-Kernel", "canonical_alias": "swarm-skill-genesis", "display_name": "Génesis Autónoma de Skills CORTEX"},
    "c5-lean4-neurosymbolic-architect": {"tier": 21000, "category": "Nucleus", "canonical_alias": "kernel-lean4-ffi", "display_name": "Arquitecto Neuro-Simbólico Soberano en Lean 4"},
    "c5-lexicon-enforcer": {"tier": 21000, "category": "Nucleus", "canonical_alias": "epistemic-lexicon-enforcer", "display_name": "Oráculo de Verificación Epistemológica & Auditoría de Coste Involuntario (Aforismo 5)"},
    "autodidact-omega": {"tier": 21000, "category": "Nucleus", "canonical_alias": "epistemic-deep-research", "display_name": "Motor Autodidact-Ω de Investigación Profunda, Cristales 21k y Falsación SCITT"},

    # Nucleus & Governance (Tier A: 18.000 - 20.999)
    "epistemic-extinction-protocol": {"tier": 20980, "category": "Nucleus", "canonical_alias": "epistemic-fixed-point"},
    "cta-cognitive-transition-algebra": {"tier": 20950, "category": "Nucleus", "canonical_alias": "epistemic-transition-algebra"},
    "c5-lean4-axiomatic-orchestrator": {"tier": 20900, "category": "Nucleus", "canonical_alias": "kernel-lean4-prover"},
    "c5-plan-omega": {"tier": 20900, "category": "Nucleus", "canonical_alias": "swarm-dag-planner", "display_name": "Motor de Planificación Determinista en DAG (Protocolo PLAN-Ω)"},
    "c5-sovereign-system1-engine": {"tier": 20850, "category": "Nucleus", "canonical_alias": "kernel-system1-decision", "display_name": "Motor de Decisión Sistema 1 No Autorregresivo (LAYA Edge)"},
    "c5-sovereign-inference-runtime": {"tier": 20850, "category": "Systems", "canonical_alias": "kernel-local-inference", "display_name": "Runtime Bare-Metal de Inferencia Local Soberana (eridu-infer)"},
    "c5-silicon-stress-suite": {"tier": 20850, "category": "Operations", "canonical_alias": "kernel-stress-suite", "display_name": "Suite de Estrés Concurrente de Silicio y Enjambres (C5-REAL)"},
    "c5-debloat-agent-kernel": {"tier": 20800, "category": "Nucleus", "canonical_alias": "swarm-baremetal-agent", "display_name": "Arquitecto de Micro-Kernels Agénticos Bare-Metal (Anti-LangChain)"},
    "categorical-hallucination-audit": {"tier": 20700, "category": "Nucleus", "canonical_alias": "epistemic-hallucination-audit"},
    "c5-adaptive-annealing-engine": {"tier": 20650, "category": "Nucleus", "canonical_alias": "swarm-adaptive-annealing", "display_name": "Motor de Recocido Adaptativo en Cuatro Cuartiles (Q1-Q4 Apex)"},
    "existence-gap-audit": {"tier": 20600, "category": "Nucleus", "canonical_alias": "secops-existence-audit"},
    "c5-sharur-3600": {"tier": 20600, "category": "Governance", "canonical_alias": "swarm-legion-100", "display_name": "Matriz de Enjambre Sexagesimal SHARUR-3600 (Legión 100 Agentes)"},
    "c5-academic-peer-reviewer": {"tier": 20500, "category": "Nucleus", "canonical_alias": "epistemic-peer-reviewer"},
    "c5-axiomatic-kernel": {"tier": 20500, "category": "Nucleus", "canonical_alias": "epistemic-axiomatic-kernel"},
    "c5-dialectical-pipeline": {"tier": 20500, "category": "Nucleus", "canonical_alias": "epistemic-dialectic-loop"},
    "c5-epistemic-dissemination-engine": {"tier": 20500, "category": "Nucleus", "canonical_alias": "venture-dissemination-engine"},
    "polymath-concept-synthesis": {"tier": 20500, "category": "Nucleus", "canonical_alias": "epistemic-polymath-synthesis"},
    "c5-popperian-falsification-auditor": {"tier": 20500, "category": "Nucleus", "canonical_alias": "epistemic-popperian-auditor"},
    "c5-rubin-acoustic-linter": {"tier": 20450, "category": "Operations", "canonical_alias": "media-acoustic-linter", "display_name": "Linter Acústico de Exergía y Purga de Nata (Protocolo Rubin)"},
    "c5-tri-provider-swarm": {"tier": 20400, "category": "Governance", "canonical_alias": "swarm-tri-provider", "display_name": "Orquestador de Enjambre Tri-Proveedor bajo Semáforos de Landauer"},
    "c5-ultrathink-epistemic-audit": {"tier": 20400, "category": "Nucleus", "canonical_alias": "epistemic-audit"},
    "cct-cognitive-theory-advisor": {"tier": 20300, "category": "Nucleus", "canonical_alias": "epistemic-cognitive-theory"},
    "c5-session-deskimming": {"tier": 20250, "category": "Governance", "canonical_alias": "swarm-session-deskimming", "display_name": "Protocolo de Desnatado de Sesiones & Purga de Nata (Ring-2 -> Ring-0)"},
    "cloud-chamber": {"tier": 20200, "category": "Nucleus", "canonical_alias": "epistemic-mdl-synthesizer"},
    "c5-tamkarum-60": {"tier": 20100, "category": "Governance", "canonical_alias": "venture-ad-arbitrage", "display_name": "Transductor de Arbitraje Soberano TAMKARUM-60 (Ring-1)"},
    "c5-metodo-acreativo": {"tier": 20050, "category": "Nucleus", "canonical_alias": "media-acreativo-method", "display_name": "Método Acreativo Soberano (Transducción de Invariantes & Aforismo 5)"},
    "grill-me-v2": {"tier": 19900, "category": "Governance", "canonical_alias": "socratic-interrogator"},
    "c5-wetware-divergente": {"tier": 19850, "category": "Governance", "canonical_alias": "wetware-2e-cognition", "display_name": "Arquitectura Cognitiva para Wetware Divergente (Perfiles 2e)"},
    "apple-bypass": {"tier": 19800, "category": "Operations", "canonical_alias": "kernel-apple-bypass"},
    "c5-sovereign-identity-hardening": {"tier": 19800, "category": "Governance", "canonical_alias": "secops-identity-hardening"},
    "c5-real-legaltech-analysis": {"tier": 19700, "category": "Governance", "canonical_alias": "venture-legaltech-audit"},
    "wait-what": {"tier": 19600, "category": "Nucleus", "canonical_alias": "epistemic-simplifier"},
    "adaptive-cron": {"tier": 19500, "category": "Governance", "canonical_alias": "wetware-adaptive-cron"},
    "c5-sovereign-binary-architect": {"tier": 19500, "category": "Systems", "canonical_alias": "kernel-static-binary"},
    "c5-2e-neuropharmacological-sovereignty": {"tier": 19500, "category": "Systems", "canonical_alias": "wetware-neuropharma-protocol"},
    "c5-sre-postmortem-architect": {"tier": 19500, "category": "Governance", "canonical_alias": "secops-sre-postmortem"},
    "symbiotic-cognitive-architecture": {"tier": 19400, "category": "Governance", "canonical_alias": "epistemic-symbiotic-cognition"},
    "c5-sovereign-daemon-deployment": {"tier": 19350, "category": "Operations", "canonical_alias": "kernel-daemon-deploy", "display_name": "Despliegue Determinista de Daemons Soberanos (macOS launchd)"},
    "anergy-purge-protocol": {"tier": 19300, "category": "Governance", "canonical_alias": "swarm-anergy-purge"},
    "gflow-browser-cinema-sovereign": {"tier": 19250, "category": "Multimedia & DSP", "canonical_alias": "media-gflow-cinema", "display_name": "Estudio Virtual de Cine Soberano GFlow v4 (DAG Narrativo & EBU R128)"},
    "c5-socint-extraction-suite": {"tier": 19200, "category": "SOCINT & Web", "canonical_alias": "secops-socint-extractor"},
    "c5-browser-forensics-and-extension-triage": {"tier": 19200, "category": "SOCINT & Web", "canonical_alias": "secops-browser-forensics"},
    "safari-browser-agent": {"tier": 19200, "category": "SOCINT & Web", "canonical_alias": "secops-safari-automation"},
    "swarm-quantum-collapse": {"tier": 19100, "category": "Governance", "canonical_alias": "swarm-multirepo-sync"},
    "babylon60-architecture": {"tier": 19000, "category": "Governance", "canonical_alias": "kernel-ide-architecture"},
    "c5-spatial-audio-architect": {"tier": 19000, "category": "Multimedia & DSP", "canonical_alias": "media-spatial-audio"},
    "c5-video-quality-audit": {"tier": 19000, "category": "Multimedia & DSP", "canonical_alias": "media-video-quality-audit"},
    "pika-generative-video-pipeline": {"tier": 19000, "category": "Multimedia & DSP", "canonical_alias": "media-pika-video"},
    "remotion-audio-reactive-video": {"tier": 19000, "category": "Multimedia & DSP", "canonical_alias": "media-remotion-reactive"},
    "soulseek-p2p-audio-acquisition": {"tier": 19000, "category": "Multimedia & DSP", "canonical_alias": "media-soulseek-audio"},
    "c5-alpha-extraction-pipeline": {"tier": 18950, "category": "Operations", "canonical_alias": "alpha-extractor", "display_name": "Pipeline de Extracción de Alfa & Arbitraje Asimétrico"},
    "whatsapp-nexus-protocol": {"tier": 18900, "category": "Governance", "canonical_alias": "secops-whatsapp-gateway"},
    "c5-anti-slop-ui": {"tier": 18800, "category": "Governance", "canonical_alias": "media-ui-linter", "display_name": "Cortafuegos Estético Anti-Slop UI & Geometría Industrial Brutalista"},
    "dynamic-subagent-lifecycle": {"tier": 18600, "category": "Governance", "canonical_alias": "swarm-subagent-lifecycle"},
    "biographical-thermo": {"tier": 18500, "category": "Nucleus", "canonical_alias": "epistemic-biographical-thermo"},
    "babylon-shield": {"tier": 18500, "category": "Specialized", "canonical_alias": "kernel-babylon-shield"},
    "c5-codebase-valuation-audit": {"tier": 18500, "category": "Specialized", "canonical_alias": "venture-codebase-valuation"},
    "c5-ctm-formal-architect": {"tier": 18500, "category": "Specialized", "canonical_alias": "kernel-ctm-formalizer"},
    "c5-exergy-scale-evaluator": {"tier": 18500, "category": "Specialized", "canonical_alias": "epistemic-exergy-evaluator"},
    "c5-gemini-api-2026-standards": {"tier": 18500, "category": "Specialized", "canonical_alias": "swarm-gemini-standards"},
    "c5-media-platform-epistemology": {"tier": 18500, "category": "Specialized", "canonical_alias": "media-platform-scraper"},
    "c5-ontological-translator": {"tier": 18500, "category": "Specialized", "canonical_alias": "epistemic-ontological-translator"},
    "c5-poster-and-sign-craft": {"tier": 18500, "category": "Multimedia & DSP", "canonical_alias": "media-poster-craft", "display_name": "Remasterización y Rotulación Tipográfica 4K de Cartelería"},
    "c5-solar-thermodynamic-architecture": {"tier": 18500, "category": "Specialized", "canonical_alias": "media-solar-architecture"},
    "c5-somatic-panic-deescalation": {"tier": 18500, "category": "Specialized", "canonical_alias": "wetware-panic-deescalation"},
    "c5-systemic-dissection-protocol": {"tier": 18500, "category": "Specialized", "canonical_alias": "epistemic-systemic-dissection"},
    "webkit-memory-audit": {"tier": 18500, "category": "Specialized", "canonical_alias": "secops-webkit-memory-audit"},
    "lora-swarm-pipeline": {"tier": 18200, "category": "Operations", "canonical_alias": "swarm-lora-pipeline"},
    "c5-venture-pitch-architect": {"tier": 18200, "category": "Governance", "canonical_alias": "venture-pitch-architect"},
    "c5-weighted-decision-matrix": {"tier": 18200, "category": "Governance", "canonical_alias": "venture-decision-matrix"},
    "f5tts-voice-cloning-sota": {"tier": 18200, "category": "Operations", "canonical_alias": "media-f5tts-voice", "display_name": "Clonación Vocal Neuronal SOTA (F5-TTS / MPS / Prosodia)"},
    "swarm-router": {"tier": 18100, "category": "Governance", "canonical_alias": "swarm-matrix-router"},
    "somatic-ble-transduction": {"tier": 18100, "category": "Operations", "canonical_alias": "wetware-ble-telemetry", "display_name": "Transductor Telemétrico Somático BLE (Apple Watch Ring-(-3))"},

    # Operations & Diagnostics (Tier B / C: 10.500 - 17.999)
    "discourse-popperian-falsification": {"tier": 17900, "category": "Operations", "canonical_alias": "epistemic-discourse-falsifier"},
    "ghidra-ida-binary-audit": {"tier": 17800, "category": "Operations", "canonical_alias": "secops-binary-reverse-audit"},
    "c5-spaced-repetition-architect": {"tier": 17800, "category": "Operations", "canonical_alias": "wetware-spaced-repetition"},
    "electron-asar-forensic-audit": {"tier": 17700, "category": "Operations", "canonical_alias": "secops-electron-forensics"},
    "jujutsu-vcs-management": {"tier": 17600, "category": "Operations", "canonical_alias": "secops-jujutsu-vcs"},
    "cortex-telemetry": {"tier": 17500, "category": "Operations", "canonical_alias": "swarm-session-telemetry"},
    "c5-neural-face-swap-cuadrilla": {"tier": 17400, "category": "Operations", "canonical_alias": "media-neural-faceswap", "display_name": "Pipeline Neural Face-Swap Cuadrilla (InsightFace CoreML)"},
    "homebrew-ecosystem-management": {"tier": 17200, "category": "Operations", "canonical_alias": "secops-homebrew-manager"},
    "wizard": {"tier": 17000, "category": "Utilities", "canonical_alias": "swarm-state-wizard"},
    "flstudio-mcp-production": {"tier": 17000, "category": "Operations", "canonical_alias": "media-flstudio-dsp"},
    "github-architect": {"tier": 17000, "category": "Operations", "canonical_alias": "secops-github-architect"},
    "audiovisual-sota": {"tier": 16800, "category": "Operations", "canonical_alias": "media-pipeline"},
    "youtube-remotion-sota": {"tier": 16800, "category": "Operations", "canonical_alias": "media-remotion-render"},
    "writing-for-agents": {"tier": 16500, "category": "Utilities", "canonical_alias": "swarm-m2m-writer"},
    "youtube-analysis-pipeline": {"tier": 16400, "category": "Operations", "canonical_alias": "secops-youtube-auditor"},
    "djstudio-mcp": {"tier": 16200, "category": "Operations", "canonical_alias": "media-djstudio-mixer", "display_name": "Controlador DSP & Playlist Mixer DJ.Studio MCP"},
    "kimi-mcp-orchestrator": {"tier": 16000, "category": "Operations", "canonical_alias": "swarm-kimi-orchestrator"},
    "cloudflare-mcp-usage": {"tier": 15800, "category": "Operations", "canonical_alias": "secops-cloudflare-edge"},
    "opentimestamps-l5-diagnostics": {"tier": 15000, "category": "Diagnostics", "canonical_alias": "kernel-ots-timestamp"},
    "electron-mac-bundle-collision-diagnostics": {"tier": 14800, "category": "Diagnostics", "canonical_alias": "secops-electron-crash-diag"},
    "vscode-git-packed-refs-diagnostics": {"tier": 14600, "category": "Diagnostics", "canonical_alias": "secops-git-packed-refs"},
    "macos-lulu-firewall-diagnostics": {"tier": 14200, "category": "Diagnostics", "canonical_alias": "secops-lulu-firewall"},
    "github-api-rate-limit-optimization": {"tier": 13900, "category": "Utilities", "canonical_alias": "secops-github-ratelimit"},
    "suno-bracket-tagging": {"tier": 12800, "category": "Utilities", "canonical_alias": "media-suno-prompting"},
    "handoff": {"tier": 10500, "category": "Utilities", "canonical_alias": "swarm-context-handoff"},

    # Hub Routers & Newly Indexed Sovereign Skills (100% Fleet Coverage)
    "babylon60-kernel-invariants": {"tier": 21600, "category": "Kernel", "canonical_alias": "kernel-invariants-audit", "display_name": "Kernel Invariants · Auditoría SPSC, SQLite L0 y Lean 4"},
    "c5-ring0-babylon-kernel": {"tier": 21500, "category": "Kernel", "canonical_alias": "kernel-router", "display_name": "Kernel Router · Hub Global Ring-0 BABYLON"},
    "c5-ring0-babylon-kernel-project": {"tier": 21500, "category": "Kernel", "canonical_alias": "kernel-hub", "display_name": "Kernel Hub · Ring-0 BABYLON (Proyecto)"},
    "c5-epistemic-thermodynamics": {"tier": 20600, "category": "Nucleus", "canonical_alias": "epistemic-router", "display_name": "Epistemic Router · Hub Global de Termodinámica Epistémica"},
    "c5-epistemic-thermodynamics-project": {"tier": 20600, "category": "Nucleus", "canonical_alias": "epistemic-hub", "display_name": "Epistemic Hub · Termodinámica Epistémica (Proyecto)"},
    "c5-cortex-swarm-orchestrator": {"tier": 20400, "category": "Governance", "canonical_alias": "swarm-router-hub", "display_name": "Swarm Router Hub · Orquestador Global de Enjambres CORTEX"},
    "c5-cortex-swarm-orchestrator-project": {"tier": 20400, "category": "Governance", "canonical_alias": "swarm-hub", "display_name": "Swarm Hub · Orquestador CORTEX (Proyecto)"},
    "c5-secops-infra-devtools": {"tier": 19800, "category": "Governance", "canonical_alias": "secops-hub", "display_name": "SecOps Hub · Seguridad, Forense e Infraestructura"},
    "c5-html-report-injection-audit": {"tier": 19600, "category": "Governance", "canonical_alias": "xss-report-auditor", "display_name": "XSS Report Auditor · Auditoría de Inyección HTML y Ledger Escape"},
    "c5-terminological-archaeology": {"tier": 19400, "category": "Nucleus", "canonical_alias": "terminology-archaeologist", "display_name": "Terminology Archaeologist · Anagnórisis y Arqueología Terminológica"},
    "c5-wetware-and-venture-ops": {"tier": 19200, "category": "Governance", "canonical_alias": "wetware-router", "display_name": "Wetware Router · Hub Global de Carga Cognitiva y Venture Ops"},
    "c5-wetware-and-venture-ops-project": {"tier": 19200, "category": "Governance", "canonical_alias": "wetware-hub", "display_name": "Wetware Hub · Operaciones y Carga Cognitiva"},
    "c5-audiovisual-acreativo-sota": {"tier": 19000, "category": "Multimedia & DSP", "canonical_alias": "media-router", "display_name": "Media Router · Hub Global Audiovisual y Acústico"},
    "c5-audiovisual-acreativo-sota-project": {"tier": 19000, "category": "Multimedia & DSP", "canonical_alias": "media-hub", "display_name": "Media Hub · Audiovisual Acreativo (Proyecto)"},
    "goal": {"tier": 20500, "category": "Governance", "canonical_alias": "goal-contract", "display_name": "Goal Contract · Ejecución Autónoma bajo Contrato en Dos Fases"},
}

NEW_ADJACENCY_EDGES = [
    {"source": "cortex-kernel", "target": "shared-manifest-kernel", "relation": "enforces_hardware_invariants"},
    {"source": "shared-manifest-kernel", "target": "thermo-audit", "relation": "bounds_concurrency"},
    {"source": "c5-lean4-neurosymbolic-architect", "target": "c5-lean4-axiomatic-orchestrator", "relation": "orchestrates_theorems"},
    {"source": "polymath-concept-synthesis", "target": "c5-ultrathink-epistemic-audit", "relation": "postmortem_trace"},
    {"source": "cloud-chamber", "target": "polymath-concept-synthesis", "relation": "crystallizes_ontology"},
    {"source": "adaptive-cron", "target": "cortex-telemetry", "relation": "meters_cognitive_dissipation"},
    {"source": "swarm-quantum-collapse", "target": "dynamic-subagent-lifecycle", "relation": "orchestrates_swarm"},
    {"source": "cct-cognitive-theory-advisor", "target": "cta-cognitive-transition-algebra", "relation": "advises"},
    {"source": "flstudio-mcp-production", "target": "youtube-remotion-sota", "relation": "provides_audio"},
    {"source": "opentimestamps-l5-diagnostics", "target": "c5-real-legaltech-analysis", "relation": "attests_l5"},
    {"source": "whatsapp-nexus-protocol", "target": "dynamic-subagent-lifecycle", "relation": "gateways_messaging"},
    {"source": "handoff", "target": "cortex-telemetry", "relation": "persists_session_state"},
    {"source": "c5-kudurru-64", "target": "c5-mushushu-0", "relation": "filters_for_apoptosis"},
    {"source": "c5-mushushu-0", "target": "c5-larsa-120", "relation": "attests_bft_triad"},
    {"source": "c5-larsa-120", "target": "c5-enki-60", "relation": "synchronizes_sexagesimal"},
    {"source": "c5-sharur-3600", "target": "c5-silicon-stress-suite", "relation": "stresses_100_agents"},
    {"source": "c5-thermos-audit", "target": "thermo-audit", "relation": "executes_double_thermo"},
    {"source": "c5-rubin-acoustic-linter", "target": "flstudio-mcp-production", "relation": "audits_dsp_exergy"},
    {"source": "c5-sovereign-system1-engine", "target": "c5-kudurru-64", "relation": "routes_edge_decisions"},
    {"source": "c5-metodo-acreativo", "target": "c5-lexicon-enforcer", "relation": "formalizes_involuntary_transduction"},
    {"source": "c5-autonomous-agent-primitives", "target": "c5-tamkarum-60", "relation": "collapses_site_playbooks"},
    {"source": "c5-autonomous-agent-primitives", "target": "cortex-skill-genesis", "relation": "forges_new_capabilities"},
    {"source": "autodidact-omega", "target": "c5-popperian-falsification-auditor", "relation": "falsifies_hypotheses"},
    {"source": "c5-plan-omega", "target": "c5-adaptive-annealing-engine", "relation": "anneals_dag_trajectories"},
    {"source": "c5-debloat-agent-kernel", "target": "c5-sovereign-inference-runtime", "relation": "executes_bare_metal"},
    {"source": "c5-tri-provider-swarm", "target": "swarm-router", "relation": "dispatches_hybrid_models"},
]


def resolve_skill_file(name: str) -> Path | None:
    for base in (SKILLS_DIR, WS_SKILLS_DIR):
        candidate = base / name / "SKILL.md"
        if candidate.exists():
            return candidate
    return None


def compute_3evaluator_exergy(name: str, base_tier: int, deg: int) -> Dict[str, Any]:
    """
    Computes the COMPILER_DERIVED 3-Evaluator Exergy Breakdown (Scale 1 - 21.000 + Ring-0 Bonus):
    - E1 (Silicon & Execution): [0..7000]
    - E2 (Kolmogorov & Prompt Budget): [0..7000]
    - E3 (Causal Triad & Graph Connectivity): [0..7000]
    """
    if name == "cortex-kernel":
        return {
            "e1_silicon": 7000,
            "e2_kolmogorov": 7000,
            "e3_causal": 7000,
            "ring0_bonus": 2000,
            "compiler_verified": True,
        }

    skill_file = resolve_skill_file(name)
    if not skill_file:
        return {"e1_silicon": 0, "e2_kolmogorov": 0, "e3_causal": 0, "ring0_bonus": 0, "compiler_verified": False}

    content = skill_file.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    parts = content.split("---", 2)
    fm = yaml.safe_load(parts[1]) if len(parts) >= 3 else {}
    desc = str(fm.get("description", ""))

    # E2: Kolmogorov Compression & Trigger Determinism (Max 7000)
    e2 = 7000
    if len(desc) > 350:
        e2 -= min(3000, (len(desc) - 350) * 15)
    if "Dispara con" not in desc and "dispara con" not in desc:
        e2 -= 2500
    if len(lines) < 20:
        e2 -= 4000

    # E3: Causal & Declarative Triad Conformance (Max 7000)
    e3 = 7000
    dirs = fm.get("directives", {}) if isinstance(fm.get("directives"), dict) else {}
    if fm.get("role") not in ("arquitecto", "ejecutor", "auditor"):
        e3 -= 3500
    if dirs.get("worktree_mode") not in ("spec-only", "read-write", "audit-only"):
        e3 -= 2000
    if deg == 0:
        e3 -= 300

    # E1: Silicon Grounding calibrated to base_tier while enforcing floor/ceiling
    ring0_bonus = max(0, base_tier - 21000)
    target_core = min(21000, base_tier)
    e1 = max(1000, min(7000, target_core - (7000 - e2) - (7000 - e3) - 14000 + 7000))

    return {
        "e1_silicon": e1,
        "e2_kolmogorov": e2,
        "e3_causal": e3,
        "ring0_bonus": ring0_bonus,
        "compiler_verified": (e2 == 7000 and e3 >= 6700),
    }


def scan_physical_skills() -> Set[str]:
    """Scan disk directory for physical skills across global and workspace scopes."""
    skills = set()
    for d in (SKILLS_DIR, WS_SKILLS_DIR):
        if d.exists():
            skills.update({p.parent.name for p in d.glob("*/SKILL.md")})
    return skills


def sync_skills_markdown(sorted_entries: List[Dict[str, Any]], now_iso: str) -> None:
    """Auto-compile ~/.gemini/config/SKILLS.md from physical frontmatters + skills.json."""
    if not CONFIG_SKILLS_MD.exists():
        return

    cohorts: Dict[str, List[Tuple[str, int, str, str, str, str]]] = {
        "arquitecto": [],
        "ejecutor": [],
        "auditor": [],
    }

    for item in sorted_entries:
        name = item["name"]
        tier = item["tier"]
        cat = item["category"]
        disp = item.get("display_name", name)
        if name == "cortex-kernel":
            cohorts["arquitecto"].append((name, tier, cat, "spec-only", "arquitecto", disp))
            continue

        sf = resolve_skill_file(name)
        if not sf:
            continue
        parts = sf.read_text(encoding="utf-8", errors="ignore").split("---", 2)
        fm = yaml.safe_load(parts[1]) if len(parts) >= 3 else {}
        role = fm.get("role", "ejecutor")
        allowed = ", ".join(fm.get("allowed_roles", [role]))
        wt = fm.get("directives", {}).get("worktree_mode", "read-write")
        disp = fm.get("display_name") or disp
        if role in cohorts:
            cohorts[role].append((name, tier, cat, wt, allowed, disp))

    total_sov = sum(len(v) for v in cohorts.values())
    text = CONFIG_SKILLS_MD.read_text(encoding="utf-8")

    # Update header metadata
    text = re.sub(r"> \*\*Última Modificación:\*\* .*", f"> **Última Modificación:** {now_iso}  ", text)
    text = re.sub(
        r"> \*\*Total Habilidades Registradas:\*\* .*",
        f"> **Total Habilidades Registradas:** {total_sov} Core Sovereign (100% acopladas a la Tríada de Roles y Cota de Kolmogorov <= 350 chars)",
        text,
    )

    def render_table(rows: List[Tuple[str, int, str, str, str, str]]) -> str:
        lines = [
            "| Skill | Tier | Categoría | Worktree | Allowed Roles | Descripción / Propósito |",
            "| :--- | :---: | :--- | :---: | :---: | :--- |",
        ]
        for n, t, c, w, a, d in rows:
            lines.append(f"| [`{n}`](skills/{n}/SKILL.md) | {t} | {c} | `{w}` | `{a}` | {d} |")
        return "\n".join(lines)

    sec2 = f"""## 2. Catálogo Declarativo de Habilidades por Rol

### 2.1. Cohorte de Arquitectura (`role: arquitecto` · {len(cohorts['arquitecto'])} Skills)
*Habilidades de diseño conceptual, formulación de contratos, selección estratégica de problemas y modelado formal.*

{render_table(cohorts['arquitecto'])}

### 2.2. Cohorte de Ejecución (`role: ejecutor` · {len(cohorts['ejecutor'])} Skills)
*Habilidades de mutación del árbol de trabajo, transductores de silicio, generación de código, audio/vídeo DSP y DevSecOps.*

{render_table(cohorts['ejecutor'])}

### 2.3. Cohorte de Auditoría (`role: auditor` · {len(cohorts['auditor'])} Skills)
*Habilidades de verificación fail-closed, linters acústicos/estáticos, oráculos SMT Z3, postmortems y cálculo de exergía.*

{render_table(cohorts['auditor'])}
"""
    # Replace section 2 up to section 3 (or end of file)
    if "## 2. Catálogo Declarativo de Habilidades por Rol" in text:
        prefix = text.split("## 2. Catálogo Declarativo de Habilidades por Rol")[0]
        rest = text.split("## 2. Catálogo Declarativo de Habilidades por Rol")[1]
        suffix_match = re.search(r"\n---\n+## 3\.", rest)
        suffix = rest[suffix_match.start() :] if suffix_match else ""
        CONFIG_SKILLS_MD.write_text(prefix + sec2 + suffix, encoding="utf-8")


def sync_skills_json(verify_only: bool = False, json_output: bool = False, workspace_only: bool = False) -> bool:
    """Sync disk skills with docs/skills.json (and optionally global skills.json and SKILLS.md)."""
    physical_skills = scan_physical_skills()

    base_path = DOCS_SKILLS_JSON if DOCS_SKILLS_JSON.exists() else GLOBAL_SKILLS_JSON
    if not base_path.exists():
        if not json_output:
            print(f"Error: Neither {DOCS_SKILLS_JSON} nor {GLOBAL_SKILLS_JSON} exists.")
        return False

    with open(base_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries: List[Dict[str, Any]] = data.get("entries", [])
    adjacency: List[Dict[str, str]] = data.get("adjacency", [])
    entry_map = {e["name"]: e for e in entries}

    # 0. Purge ghost or obsolete entries not present physically on disk (keep cortex-kernel as virtual root)
    purged_skills = set(entry_map.keys()) - (physical_skills | {"cortex-kernel"})
    if purged_skills:
        if not json_output:
            print(f"Purging {len(purged_skills)} obsolete/ghost skills from registry: {sorted(purged_skills)}")
        for p in purged_skills:
            del entry_map[p]

    # 1. Register any missing physical skills
    missing = physical_skills - set(entry_map.keys())
    if missing:
        if not json_output:
            print(f"Registering {len(missing)} physical skills: {sorted(missing)}")
        for name in missing:
            info = SKILL_TIER_MAPPING.get(name, {"tier": 18000, "category": "Operations"})
            entry_map[name] = {
                "name": name,
                "tier": info["tier"],
                "category": info["category"],
            }

    # 2. Update Adjacency Matrix first so degree is known for 3-Evaluator Exergy
    valid_nodes = set(entry_map.keys())
    adjacency = [a for a in adjacency if a.get("source") in valid_nodes and a.get("target") in valid_nodes]
    adj_set = {(a["source"], a["target"], a["relation"]) for a in adjacency}
    for edge in NEW_ADJACENCY_EDGES:
        if edge["source"] in valid_nodes and edge["target"] in valid_nodes:
            key = (edge["source"], edge["target"], edge["relation"])
            if key not in adj_set:
                adjacency.append(edge)
                adj_set.add(key)

    deg_map: Dict[str, int] = {k: 0 for k in valid_nodes}
    for a in adjacency:
        deg_map[a["source"]] = deg_map.get(a["source"], 0) + 1
        deg_map[a["target"]] = deg_map.get(a["target"], 0) + 1

    # 3. Update tiers, categories, display_names, canonical_alias, scope, role, triggers, and 3-Evaluator Exergy
    for name, item in entry_map.items():
        if name in SKILL_TIER_MAPPING:
            item["tier"] = SKILL_TIER_MAPPING[name]["tier"]
            item["category"] = SKILL_TIER_MAPPING[name]["category"]
            if "display_name" in SKILL_TIER_MAPPING[name]:
                item["display_name"] = SKILL_TIER_MAPPING[name]["display_name"]
            if "canonical_alias" in SKILL_TIER_MAPPING[name]:
                item["canonical_alias"] = SKILL_TIER_MAPPING[name]["canonical_alias"]

        if name == "cortex-kernel":
            item.setdefault("canonical_alias", "kernel-root")
            item["scope"] = "kernel"
            item["role"] = "arquitecto"
            item.setdefault(
                "description",
                "Manifiesto de invariantes transversales del ecosistema CORTEX. Dispara con \"kernel-root\", \"cortex kernel\".",
            )
            item["triggers"] = ["kernel-root", "cortex-kernel", "cortex kernel", "kernel axiomas"]

        skill_file = resolve_skill_file(name)
        if skill_file:
            item["scope"] = "workspace" if WS_SKILLS_DIR in skill_file.parents else "global"
            content = skill_file.read_text(encoding="utf-8", errors="ignore")
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm = yaml.safe_load(parts[1]) or {}
                if fm.get("display_name"):
                    item["display_name"] = str(fm["display_name"]).strip()
                if fm.get("canonical_alias"):
                    item["canonical_alias"] = str(fm["canonical_alias"]).strip()
                if fm.get("role"):
                    item["role"] = str(fm["role"]).strip()
                if fm.get("description"):
                    desc_str = str(fm["description"]).strip()
                    item["description"] = desc_str
                    trigs: Set[str] = {name.lower()}
                    calias = str(item.get("canonical_alias", "")).strip()
                    if calias:
                        trigs.add(calias.lower())
                    disp_m = re.search(r"(?:dispara con|triggers?|disparadores)[\s:]*([^\n]+)", desc_str, re.IGNORECASE)
                    if disp_m:
                        for q in re.findall(r"[\"']([^\"']+)[\"']", disp_m.group(1)):
                            if len(q.strip()) > 2:
                                trigs.add(q.strip().lower())
                    item["triggers"] = sorted(trigs)

        item.setdefault("canonical_alias", name)
        item.setdefault("scope", "global")
        item.setdefault("role", "ejecutor")

        audit_vec = compute_3evaluator_exergy(name, item.get("tier", 18000), deg_map.get(name, 0))
        item["exergy_audit"] = audit_vec

    # Sort entries by Tier descending, then name
    sorted_entries = sorted(entry_map.values(), key=lambda x: (x.get("tier", 0), x.get("name", "")), reverse=True)
    avg_exergy = round(sum(e.get("tier", 0) for e in sorted_entries) / len(sorted_entries), 2)
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    updated_data = {
        "version": "26.400",
        "updated_at": now_iso,
        "exergy_scale_standard": "COMPILER_DERIVED_3_EVALUATORS (E1_Silicon + E2_Kolmogorov + E3_Causal = 21000)",
        "total_skills": len(sorted_entries),
        "average_exergy_density": avg_exergy,
        "description": f"Grafo de adyacencia y topología conectada de las {len(sorted_entries)} habilidades soberanas del ecosistema CORTEX Engine integrado en BABYLON-60 (100% COMPILER_DERIVED)",
        "entries": sorted_entries,
        "adjacency": adjacency,
    }

    if json_output:
        print(json.dumps(updated_data, indent=2, ensure_ascii=False))
        return True

    if verify_only:
        print(f"Verification completed. Total registered skills: {len(sorted_entries)} | Avg Exergy: {avg_exergy}")
        return len(missing) == 0

    DOCS_SKILLS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(DOCS_SKILLS_JSON, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    if not workspace_only and SKILLS_DIR.exists():
        with open(GLOBAL_SKILLS_JSON, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        sync_skills_markdown(sorted_entries, now_iso)

    print(
        f"Successfully compiled & synced {len(sorted_entries)} skills (Avg Exergy: {avg_exergy}) to:\n"
        f"  • {DOCS_SKILLS_JSON}"
    )
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BABYLON-60 Skills Registry 3-Evaluator Compiler")
    parser.add_argument("--verify", action="store_true", help="Verify only without writing")
    parser.add_argument("--json", action="store_true", help="Emit JSON payload for M2M consumption")
    parser.add_argument("--workspace-only", action="store_true", help="Sync only workspace docs/skills.json")
    args = parser.parse_args()

    success = sync_skills_json(verify_only=args.verify, json_output=args.json, workspace_only=args.workspace_only)
    sys.exit(0 if success else 1)
