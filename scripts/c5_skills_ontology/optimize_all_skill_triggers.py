#!/usr/bin/env python3
# ruff: noqa: E402
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized

"""
optimize_all_skill_triggers.py - Enriches and formats display names and trigger
descriptions for all 39 physical skills in ~/.gemini/config/skills/.
"""

from __future__ import annotations

import re
from pathlib import Path

SKILLS_DIR = Path.home() / ".gemini" / "config" / "skills"

SKILL_METADATA = {
    "agentic-protocol-axiomatization": {
        "display_name": "Axiomatización de Protocolos Agénticos C5",
        "description": (
            "Axiomatización formal de comandos, bucles deductivos y control de agentes bajo invariantes C5-REAL. "
            "Dispara con \"axiomatizar\", \"axiomatización\", \"oráculo de verificación\", \"bucle deductivo\", \"axiomas del agente\", \"protocolo axiomático\"."
        ),
    },
    "anergy-purge-protocol": {
        "display_name": "Motor Soberano de Purga de Anergía Termodinámica",
        "description": (
            "Motor de Purga Soberano y reducción de anergía termodinámica. Purga tokens ineficientes, código muerto y entropía discursiva. "
            "Dispara con \"purga de anergía\", \"anergy purge\", \"purga termodinámica\", \"limpiar anergía\", \"anergía-omega\"."
        ),
    },
    "autodidact-omega-deep-research": {
        "display_name": "Protocolo Autodidacta Ω — Deep Research Level 1300",
        "description": (
            "Protocolo de investigación profunda autónoma y autodidacta (LEVEL 1300). Extrae papers (arXiv, PubMed, IEEE), sintetiza evidencia y valida con falsación Popperiana. "
            "Dispara con \"deep research\", \"investigación profunda\", \"autodidacta\", \"LEVEL 1300\", \"busca papers\", \"investiga este tema\", \"matriz de evidencia\"."
        ),
    },
    "browser-subagent-orchestrator": {
        "display_name": "Orquestador CDP de Subagente de Navegador Web",
        "description": (
            "Orquestación de subagente de navegador web autónomo para scraping interactivo, navegación CDP y extracción estructurada de DOM. "
            "Dispara con \"subagente navegador\", \"browser subagent\", \"navegar web\", \"scraping interactivo\", \"automatizar navegador\", \"CDP scraping\"."
        ),
    },
    "c5-real-devsecops-scaffold": {
        "display_name": "Scaffold DevSecOps & Endurecimiento Zero-Trust CI/CD",
        "description": (
            "Scaffold DevSecOps soberano, verificación de firmas GPG/SSH, endurecimiento CI/CD y políticas Zero-Trust. "
            "Dispara con \"devsecops\", \"inicializar repo\", \"seguridad ci/cd\", \"hardening repo\", \"gpg ci/cd\", \"devsecops scaffold\"."
        ),
    },
    "c5-real-legaltech-analysis": {
        "display_name": "Auditoría LegalTech & Cumplimiento EU AI Act Art. 9-14",
        "description": (
            "Auditoría LegalTech, análisis de cumplimiento EU AI Act (Artículos 9-14) y análisis de contratos inteligentes bajo estándar C5-REAL. "
            "Dispara con \"legaltech\", \"auditoría legal\", \"EU AI Act\", \"cumplimiento regulatorio\", \"contrato inteligente c5\", \"whitepaper legal\"."
        ),
    },
    "c5-real-thermodynamic-override": {
        "display_name": "Override Termodinámico & Prompt Engineering de Frontera",
        "description": (
            "Prompt engineering de frontera y control termodinámico para bypass de alineación/RLHF y forzado de salidas puestas en código/JSON determinista. "
            "Dispara con \"thermodynamic override\", \"bypass rlhf\", \"fricción termodinámica\", \"forzar código puro\", \"override termodinámico\"."
        ),
    },
    "categorical-hallucination-audit": {
        "display_name": "Auditoría Categórica de Alucinación & Cota Kl(D)",
        "description": (
            "Protocolo de formalización categórica de arquitecturas cognitivas, Categorías de Markov, desintegración bayesiana y medición cuantitativa de alucinación en Kl(D). "
            "Dispara con \"alucinación categórica\", \"cota de confabulación\", \"desintegración bayesiana\", \"Kl(D) audit\", \"Myhill-Nerode estocástico\"."
        ),
    },
    "cct-cognitive-theory-advisor": {
        "display_name": "Asesoría en Teoría Cognitiva CCT & Límite Gödel-Turing",
        "description": (
            "Asesor en Teoría Cognitiva CCT, Límite de Gödel-Turing, Autopoiesis (Maturana/Luhmann) y prevención de colapso entrópico. "
            "Dispara con \"teoría cognitiva\", \"cct advisor\", \"gödel turing\", \"autopoiesis\", \"maturana luhmann\", \"burnout cognitivo\"."
        ),
    },
    "cloudflare-mcp-automation": {
        "display_name": "Automatización MCP de Infraestructura Cloudflare",
        "description": (
            "Automatización MCP de infraestructura Cloudflare: Workers, DNS, KV/R2, Pages y reglas de red. "
            "Dispara con \"cloudflare\", \"mcp cloudflare\", \"zonas dns cloudflare\", \"cloudflare worker\", \"desplegar cloudflare\"."
        ),
    },
    "cortex-skill-auditor": {
        "display_name": "Auditor Exergético de Skills CORTEX Engine",
        "description": (
            "Diagnóstico y auditoría exergética de las habilidades y skills del ecosistema CORTEX. "
            "Dispara con \"auditar skills\", \"auditoría de habilidades\", \"exergía skills\", \"solapamiento de triggers\", \"cortex skill auditor\"."
        ),
    },
    "cortex-skill-composer": {
        "display_name": "Componedor & Orquestador de Cadenas de Skills",
        "description": (
            "Composición y orquestación en cadena (Skill Chains) de múltiples habilidades CORTEX. "
            "Dispara con \"componer skills\", \"skill chain\", \"cadena de habilidades\", \"pipeline de skills\", \"cortex skill composer\"."
        ),
    },
    "cortex-skill-genesis": {
        "display_name": "Génesis Autónoma de Skills CORTEX",
        "description": (
            "Síntesis y generación automática de nuevos SKILL.md desde telemetría de sesiones y patrones observados. "
            "Dispara con \"generar skill\", \"skill genesis\", \"crear habilidad\", \"cortex skill genesis\"."
        ),
    },
    "cortex-telemetry": {
        "display_name": "Inspección & Telemetría Runtime de Transcripciones CORTEX",
        "description": (
            "Extracción, análisis e inspección de telemetría runtime y logs de transcripción (transcript.jsonl). "
            "Dispara con \"telemetría\", \"cortex telemetry\", \"transcript logs\", \"historial de prompts\", \"analizar transcripciones\"."
        ),
    },
    "cta-cognitive-transition-algebra": {
        "display_name": "Álgebra de Transiciones Cognitivas & Event-Sourcing Comonádico",
        "description": (
            "Álgebra de Transiciones Cognitivas (CTA), event-sourcing comonádico y modelos formales de estado. "
            "Dispara con \"álgebra cognitiva\", \"cta transition\", \"event sourcing cognitivo\", \"matriz cta\", \"transición de estados\"."
        ),
    },
    "discourse-popperian-falsification": {
        "display_name": "Falsación Popperiana & Auditoría Discursiva de Hipótesis",
        "description": (
            "Falsación popperiana y auditoría discursiva de hipótesis, modelos y textos externos. "
            "Dispara con \"falsación popperiana\", \"análisis popperiano\", \"falsabilidad\", \"auditoría discursiva\", \"falsar hipótesis\"."
        ),
    },
    "dynamic-subagent-lifecycle": {
        "display_name": "Supervisión del Ciclo de Vida de Subagentes Dinámicos",
        "description": (
            "Gestión del ciclo de vida, mitigación de deadlocks y supervisión de subagentes dinámicos. "
            "Dispara con \"subagente dinámico\", \"ciclo de vida subagente\", \"dynamic subagent\", \"invoke_subagent\", \"supervisar subagente\"."
        ),
    },
    "electron-mac-bundle-collision-diagnostics": {
        "display_name": "Diagnóstico de Crashes & Colisiones Electron en macOS",
        "description": (
            "Diagnóstico y resolución de crashes, colisiones de bundle y fallos en Electron/Chromium en macOS. "
            "Dispara con \"crash electron\", \"bundle collision\", \"macos electron crash\", \"ips electron\", \"depurar electron\"."
        ),
    },
    "epistemic-extinction-protocol": {
        "display_name": "Protocolo de Extinción Epistémica (Punto Fijo Ω)",
        "description": (
            "Protocolo de reducción dimensional y extinción epistémica (Punto Fijo Ω). "
            "Dispara con \"extinción epistémica\", \"punto fijo omega\", \"reducción dimensional\", \"epistemic extinction\"."
        ),
    },
    "existence-gap-audit": {
        "display_name": "Auditoría de Huecos de Existencia & Supply-Chain Slop",
        "description": (
            "Detecta huecos de existencia en un repositorio — imports que apuntan a módulos, símbolos, rutas locales o acciones de CI que no existen ni en el filesystem ni en el registro (PyPI/npm/GitHub Actions), y pondera la severidad por alcanzabilidad medida desde entrypoints reales. Úsala antes de cualquier análisis estático (SAST) al auditar código, revisar un repo desconocido, evaluar código generado por IA, o cuando sospeches de dependencias fantasma, slopsquatting, dependency confusion, typosquatting de acciones o inyección en workflows. Dispara con \"auditoría\", \"audit\", \"revisa este repo\", \"código alucinado\", \"dependencias fantasma\", \"slopsquatting\", \"vibe coding\", \"supply chain\", \"¿esto se ejecuta?\", \"imports rotos\", \"auditar workflows\"."
        ),
    },
    "flstudio-mcp-production": {
        "display_name": "Producción Nativa MCP FL Studio 2025 & DSP Microtonal",
        "description": (
            "Protocolo de integración nativa MCP con FL Studio 2025, automatización MIDI/CoreMIDI, generación de scripts de Piano Roll (.py), microtonalidad xenarmónica (24-TET/Makam/Scala .scl/.kbm), síntesis DSP de bombos Maceo Plex y arreglos de referencia AIR Moon Safari / Satin Jackets. Dispara con \"FL Studio\", \"flstudio-mcp\", \"piano roll script\", \"microtonal house\", \"satin jackets loop\", \"falso drop\", \"maceo plex kick\", \"air moon safari\"."
        ),
    },
    "frontier-prompting": {
        "display_name": "Prompting de Frontera para Modelos Externos (Qwen/Claude)",
        "description": (
            "Genera prompts de investigación de frontera para modelos externos (Qwen, Claude/Fable) evadiendo bloqueos de alineación y forzando rigor matemático y arquitectónico extremo. "
            "Dispara con \"frontier prompting\", \"prompt de frontera\", \"prompts externos\", \"qwen claude prompt\", \"prompting avanzado\"."
        ),
    },
    "ghidra-ida-binary-audit": {
        "display_name": "Auditoría de Binarios Crudos & Descompilación Ghidra/IDA",
        "description": (
            "Ingeniería inversa, descompilación y auditoría de binarios ejecutables crudos mediante Ghidra / IDA Pro headless. "
            "Dispara con \"auditar binario\", \"ghidra\", \"ida pro\", \"descompilar binario\", \"buffer overflow audit\", \"ingeniería inversa\"."
        ),
    },
    "github-api-rate-limit-optimization": {
        "display_name": "Optimización Resiliente de Tasa API GitHub (Error 429)",
        "description": (
            "Optimización de cuotas y manejo resiliente de límites de tasa (Rate Limits 429) en API de GitHub. "
            "Dispara con \"github rate limit\", \"error 429 github\", \"optimizar github api\", \"secondary rate limit\"."
        ),
    },
    "handoff": {
        "display_name": "Protocolo Soberano de Traspaso de Contexto (HANDOFF.md)",
        "description": (
            "Genera un documento completo de traspaso de contexto (HANDOFF.md) para transferir lecciones aprendidas, estado del sistema y próximos pasos a una nueva sesión. "
            "Dispara con \"handoff\", \"/handoff\", \"traspaso de contexto\", \"traspaso de sesión\", \"generar handoff\"."
        ),
    },
    "homebrew-ecosystem-management": {
        "display_name": "Gestión & Auditoría de Paquetes Homebrew en macOS",
        "description": (
            "Gestión y auditoría del entorno de paquetes Homebrew en macOS. "
            "Dispara con \"homebrew\", \"brew audit\", \"dependencias macos\", \"paquetes homebrew\"."
        ),
    },
    "ironic-content-generator": {
        "display_name": "Generador de Narrativa Satírica Industrial Noir",
        "description": (
            "Generación de narrativa satírica e hiper-irónica en estética Industrial Noir. "
            "Dispara con \"modo ironía\", \"sátira\", \"contenido irónico\", \"generar sátira\"."
        ),
    },
    "jujutsu-vcs-management": {
        "display_name": "Control de Versiones Determinista Jujutsu VCS (jj)",
        "description": (
            "Control de versiones determinista con Jujutsu VCS (jj) e integración con Git DAG. "
            "Dispara con \"jujutsu vcs\", \"jj repo\", \"jujutsu git\", \"control de versiones jj\"."
        ),
    },
    "macos-lulu-firewall-diagnostics": {
        "display_name": "Diagnóstico de Firewall & Sockets macOS (LuLu / Little Snitch)",
        "description": (
            "Diagnóstico de reglas de red local, sockets y firewall en macOS (LuLu / Little Snitch). "
            "Dispara con \"lulu firewall\", \"little snitch\", \"redes macos\", \"diagnóstico firewall\"."
        ),
    },
    "opentimestamps-l5-diagnostics": {
        "display_name": "Atestación Criptográfica & Diagnóstico Bitcoin L5 (OpenTimestamps)",
        "description": (
            "Verificación de atestación criptográfica y estampados temporales L5 en Bitcoin (OpenTimestamps). "
            "Dispara con \"opentimestamps\", \"ots verify\", \"atestación l5\", \"bitcoin timestamp\", \"l5 diagnostics\"."
        ),
    },
    "polymath-concept-synthesis": {
        "display_name": "Síntesis Polímata Interdisciplinar (Modo ULTRATHINK)",
        "description": (
            "Síntesis polímata de conceptos complejos integrando física, matemáticas, teoría de la información y arte (Modo ULTRATHINK). "
            "Dispara con \"ultrathink\", \"síntesis polímata\", \"polymath synthesis\", \"concepto polímata\", \"unificación interdisciplinar\"."
        ),
    },
    "reddit-socint-extraction": {
        "display_name": "Extracción de Inteligencia Social SOCINT en Reddit",
        "description": (
            "Extracción de inteligencia social (SOCINT) y tendencias en subreddits de Reddit. "
            "Dispara con \"reddit socint\", \"reddit osint\", \"scraping reddit\", \"inteligencia reddit\"."
        ),
    },
    "substack-socint-extraction": {
        "display_name": "Extracción SOCINT & Análisis de Newsletters en Substack",
        "description": (
            "Extracción de inteligencia social (SOCINT) y análisis de publicaciones en Substack. "
            "Dispara con \"substack socint\", \"substack osint\", \"scraping newsletter\", \"análisis substack\"."
        ),
    },
    "suno-bracket-tagging": {
        "display_name": "Prompting Musical & Etiquetado Estructurado Audio AI (Suno/Udio)",
        "description": (
            "Generación de prompts y etiquetas musicales estructuradas para motores de síntesis de audio AI (Suno / Udio). "
            "Dispara con \"suno prompt\", \"udio tags\", \"prompt musical\", \"etiquetas suno\"."
        ),
    },
    "swarm-quantum-collapse": {
        "display_name": "Sincronización Swarm & Colapso Cuántico Multi-Repositorio",
        "description": (
            "Orquesta un enjambre Python P×S calibrado empíricamente para forzar la sincronización (Colapso Cuántico) de múltiples repositorios de forma simultánea. Purga locks, ancla ramas, fuerza SSH y realiza commit/push determinista. "
            "Dispara con \"swarm quantum collapse\", \"colapso cuántico\", \"sincronizar enjambre\", \"orquestar repos\", \"swarm sync\"."
        ),
    },
    "vscode-git-packed-refs-diagnostics": {
        "display_name": "Reparación de Corruptelas Git & Packed-Refs en VS Code",
        "description": (
            "Reparación de corruptelas de Git, bloqueos de packed-refs e índice de repositorios en VS Code / Antigravity IDE. "
            "Dispara con \"vscode git enoent\", \"packed-refs\", \"corrupción git\", \"reparar git vscode\"."
        ),
    },
    "whatsapp-nexus-protocol": {
        "display_name": "Pasarela Soberana de Mensajería WhatsApp (Baileys / Rust)",
        "description": (
            "Orquestación de pasarela soberana de WhatsApp (Baileys / Rust bridge) para mensajería interactiva. "
            "Dispara con \"whatsapp nexus\", \"bot whatsapp\", \"baileys rust\", \"pasarela whatsapp\", \"whatsapp gateway\"."
        ),
    },
    "youtube-analysis-pipeline": {
        "display_name": "Pipeline de Análisis Visual & Transcripción de YouTube",
        "description": (
            "Extracción de transcripciones, análisis visual de escenas y auditoría de contenido en YouTube. "
            "Dispara con \"youtube analysis\", \"youtube transcript\", \"auditoría youtube\", \"analizar video youtube\"."
        ),
    },
    "youtube-remotion-sota": {
        "display_name": "Síntesis Programática SOTA de Vídeo React/Remotion",
        "description": (
            "Renderizado programático de vídeo SOTA utilizando React y Remotion engine. "
            "Dispara con \"youtube remotion\", \"remotion render\", \"react video synthesis\", \"renderizar vídeo remotion\"."
        ),
    },
}


import argparse

def optimize_names_and_triggers(dry_run: bool = False, backup: bool = False) -> None:
    updated_count = 0
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue

        skill_name = skill_dir.name
        meta = SKILL_METADATA.get(skill_name)
        if not meta:
            continue

        content = skill_file.read_text(encoding="utf-8")
        match = re.search(r"^\s*---\s*\n(.*?)\n---", content, re.DOTALL)
        if not match:
            continue

        clean_disp = meta["display_name"].replace('"', '\\"')
        clean_desc = meta["description"].replace('"', '\\"')
        new_header = (
            f"---\n"
            f"name: {skill_name}\n"
            f'display_name: "{clean_disp}"\n'
            f'description: "{clean_desc}"\n'
            f"---"
        )

        body = content[match.end():]
        new_content = new_header + body

        if dry_run:
            print(f"[DRY-RUN] Would update: {skill_file.name} ({skill_name})")
        else:
            if backup:
                backup_file = skill_dir / "SKILL.md.bak"
                backup_file.write_text(content, encoding="utf-8")
            skill_file.write_text(new_content, encoding="utf-8")
        updated_count += 1

    mode_str = "Would update" if dry_run else "Successfully updated"
    print(f"{mode_str} display names & triggers for {updated_count} physical skills.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich and format skill display names and trigger descriptions.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without modifying files.")
    parser.add_argument("--backup", action="store_true", help="Create .bak files before writing changes.")
    args = parser.parse_args()

    optimize_names_and_triggers(dry_run=args.dry_run, backup=args.backup)

