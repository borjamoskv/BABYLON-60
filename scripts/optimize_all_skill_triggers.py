#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized

"""
optimize_all_skill_triggers.py - Enriches and formats the trigger descriptions
for all 39 physical skills in ~/.gemini/config/skills/ using clean, safe YAML frontmatter.
"""

from __future__ import annotations

import re
from pathlib import Path

SKILLS_DIR = Path.home() / ".gemini" / "config" / "skills"

ENRICHED_DESCRIPTIONS = {
    "agentic-protocol-axiomatization": (
        "Axiomatización formal de comandos, bucles deductivos y control de agentes bajo invariantes C5-REAL. "
        "Dispara con \"axiomatizar\", \"axiomatización\", \"oráculo de verificación\", \"bucle deductivo\", \"axiomas del agente\", \"protocolo axiomático\"."
    ),
    "anergy-purge-protocol": (
        "Motor de Purga Soberano y reducción de anergía termodinámica. Purga tokens ineficientes, código muerto y entropía discursiva. "
        "Dispara con \"purga de anergía\", \"anergy purge\", \"purga termodinámica\", \"limpiar anergía\", \"anergía-omega\"."
    ),
    "autodidact-omega-deep-research": (
        "Protocolo de investigación profunda autónoma y autodidacta (LEVEL 1300). Extrae papers (arXiv, PubMed, IEEE), sintetiza evidencia y valida con falsación Popperiana. "
        "Dispara con \"deep research\", \"investigación profunda\", \"autodidacta\", \"LEVEL 1300\", \"busca papers\", \"investiga este tema\", \"matriz de evidencia\"."
    ),
    "browser-subagent-orchestrator": (
        "Orquestación de subagente de navegador web autónomo para scraping interactivo, navegación CDP y extracción estructurada de DOM. "
        "Dispara con \"subagente navegador\", \"browser subagent\", \"navegar web\", \"scraping interactivo\", \"automatizar navegador\", \"CDP scraping\"."
    ),
    "c5-real-devsecops-scaffold": (
        "Scaffold DevSecOps soberano, verificación de firmas GPG/SSH, endurecimiento CI/CD y políticas Zero-Trust. "
        "Dispara con \"devsecops\", \"inicializar repo\", \"seguridad ci/cd\", \"hardening repo\", \"gpg ci/cd\", \"devsecops scaffold\"."
    ),
    "c5-real-legaltech-analysis": (
        "Auditoría LegalTech, análisis de cumplimiento EU AI Act (Artículos 9-14) y análisis de contratos inteligentes bajo estándar C5-REAL. "
        "Dispara con \"legaltech\", \"auditoría legal\", \"EU AI Act\", \"cumplimiento regulatorio\", \"contrato inteligente c5\", \"whitepaper legal\"."
    ),
    "c5-real-thermodynamic-override": (
        "Prompt engineering de frontera y control termodinámico para bypass de alineación/RLHF y forzado de salidas puestas en código/JSON determinista. "
        "Dispara con \"thermodynamic override\", \"bypass rlhf\", \"fricción termodinámica\", \"forzar código puro\", \"override termodinámico\"."
    ),
    "categorical-hallucination-audit": (
        "Protocolo de formalización categórica de arquitecturas cognitivas, Categorías de Markov, desintegración bayesiana y medición cuantitativa de alucinación en Kl(D). "
        "Dispara con \"alucinación categórica\", \"cota de confabulación\", \"desintegración bayesiana\", \"Kl(D) audit\", \"Myhill-Nerode estocástico\"."
    ),
    "cct-cognitive-theory-advisor": (
        "Asesor en Teoría Cognitiva CCT, Límite de Gödel-Turing, Autopoiesis (Maturana/Luhmann) y prevención de colapso entrópico. "
        "Dispara con \"teoría cognitiva\", \"cct advisor\", \"gödel turing\", \"autopoiesis\", \"maturana luhmann\", \"burnout cognitivo\"."
    ),
    "cloudflare-mcp-automation": (
        "Automatización MCP de infraestructura Cloudflare: Workers, DNS, KV/R2, Pages y reglas de red. "
        "Dispara con \"cloudflare\", \"mcp cloudflare\", \"zonas dns cloudflare\", \"cloudflare worker\", \"desplegar cloudflare\"."
    ),
    "cortex-skill-auditor": (
        "Diagnóstico y auditoría exergética de las habilidades y skills del ecosistema CORTEX. "
        "Dispara con \"auditar skills\", \"auditoría de habilidades\", \"exergía skills\", \"solapamiento de triggers\", \"cortex skill auditor\"."
    ),
    "cortex-skill-composer": (
        "Composición y orquestación en cadena (Skill Chains) de múltiples habilidades CORTEX. "
        "Dispara con \"componer skills\", \"skill chain\", \"cadena de habilidades\", \"pipeline de skills\", \"cortex skill composer\"."
    ),
    "cortex-skill-genesis": (
        "Síntesis y generación automática de nuevos SKILL.md desde telemetría de sesiones y patrones observados. "
        "Dispara con \"generar skill\", \"skill genesis\", \"crear habilidad\", \"cortex skill genesis\"."
    ),
    "cortex-telemetry": (
        "Extracción, análisis e inspección de telemetría runtime y logs de transcripción (transcript.jsonl). "
        "Dispara con \"telemetría\", \"cortex telemetry\", \"transcript logs\", \"historial de prompts\", \"analizar transcripciones\"."
    ),
    "cta-cognitive-transition-algebra": (
        "Álgebra de Transiciones Cognitivas (CTA), event-sourcing comonádico y modelos formales de estado. "
        "Dispara con \"álgebra cognitiva\", \"cta transition\", \"event sourcing cognitivo\", \"matriz cta\", \"transición de estados\"."
    ),
    "discourse-popperian-falsification": (
        "Falsación popperiana y auditoría discursiva de hipótesis, modelos y textos externos. "
        "Dispara con \"falsación popperiana\", \"análisis popperiano\", \"falsabilidad\", \"auditoría discursiva\", \"falsar hipótesis\"."
    ),
    "dynamic-subagent-lifecycle": (
        "Gestión del ciclo de vida, mitigación de deadlocks y supervisión de subagentes dinámicos. "
        "Dispara con \"subagente dinámico\", \"ciclo de vida subagente\", \"dynamic subagent\", \"invoke_subagent\", \"supervisar subagente\"."
    ),
    "electron-mac-bundle-collision-diagnostics": (
        "Diagnóstico y resolución de crashes, colisiones de bundle y fallos en Electron/Chromium en macOS. "
        "Dispara con \"crash electron\", \"bundle collision\", \"macos electron crash\", \"ips electron\", \"depurar electron\"."
    ),
    "epistemic-extinction-protocol": (
        "Protocolo de reducción dimensional y extinción epistémica (Punto Fijo Ω). "
        "Dispara con \"extinción epistémica\", \"punto fijo omega\", \"reducción dimensional\", \"epistemic extinction\"."
    ),
    "existence-gap-audit": (
        "Detecta huecos de existencia en un repositorio — imports que apuntan a módulos, símbolos, rutas locales o acciones de CI que no existen ni en el filesystem ni en el registro (PyPI/npm/GitHub Actions), y pondera la severidad por alcanzabilidad medida desde entrypoints reales. Úsala antes de cualquier análisis estático (SAST) al auditar código, revisar un repo desconocido, evaluar código generado por IA, o cuando sospeches de dependencias fantasma, slopsquatting, dependency confusion, typosquatting de acciones o inyección en workflows. Dispara con \"auditoría\", \"audit\", \"revisa este repo\", \"código alucinado\", \"dependencias fantasma\", \"slopsquatting\", \"vibe coding\", \"supply chain\", \"¿esto se ejecuta?\", \"imports rotos\", \"auditar workflows\"."
    ),
    "flstudio-mcp-production": (
        "Protocolo de integración nativa MCP con FL Studio 2025, automatización MIDI/CoreMIDI, generación de scripts de Piano Roll (.py), microtonalidad xenarmónica (24-TET/Makam/Scala .scl/.kbm), síntesis DSP de bombos Maceo Plex y arreglos de referencia AIR Moon Safari / Satin Jackets. Dispara con \"FL Studio\", \"flstudio-mcp\", \"piano roll script\", \"microtonal house\", \"satin jackets loop\", \"falso drop\", \"maceo plex kick\", \"air moon safari\"."
    ),
    "frontier-prompting": (
        "Genera prompts de investigación de frontera para modelos externos (Qwen, Claude/Fable) evadiendo bloqueos de alineación y forzando rigor matemático y arquitectónico extremo. "
        "Dispara con \"frontier prompting\", \"prompt de frontera\", \"prompts externos\", \"qwen claude prompt\", \"prompting avanzado\"."
    ),
    "ghidra-ida-binary-audit": (
        "Ingeniería inversa, descompilación y auditoría de binarios ejecutables crudos mediante Ghidra / IDA Pro headless. "
        "Dispara con \"auditar binario\", \"ghidra\", \"ida pro\", \"descompilar binario\", \"buffer overflow audit\", \"ingeniería inversa\"."
    ),
    "github-api-rate-limit-optimization": (
        "Optimización de cuotas y manejo resiliente de límites de tasa (Rate Limits 429) en API de GitHub. "
        "Dispara con \"github rate limit\", \"error 429 github\", \"optimizar github api\", \"secondary rate limit\"."
    ),
    "handoff": (
        "Genera un documento completo de traspaso de contexto (HANDOFF.md) para transferir lecciones aprendidas, estado del sistema y próximos pasos a una nueva sesión. "
        "Dispara con \"handoff\", \"/handoff\", \"traspaso de contexto\", \"traspaso de sesión\", \"generar handoff\"."
    ),
    "homebrew-ecosystem-management": (
        "Gestión y auditoría del entorno de paquetes Homebrew en macOS. "
        "Dispara con \"homebrew\", \"brew audit\", \"dependencias macos\", \"paquetes homebrew\"."
    ),
    "ironic-content-generator": (
        "Generación de narrativa satírica e hiper-irónica en estética Industrial Noir. "
        "Dispara con \"modo ironía\", \"sátira\", \"contenido irónico\", \"generar sátira\"."
    ),
    "jujutsu-vcs-management": (
        "Control de versiones determinista con Jujutsu VCS (jj) e integración con Git DAG. "
        "Dispara con \"jujutsu vcs\", \"jj repo\", \"jujutsu git\", \"control de versiones jj\"."
    ),
    "macos-lulu-firewall-diagnostics": (
        "Diagnóstico de reglas de red local, sockets y firewall en macOS (LuLu / Little Snitch). "
        "Dispara con \"lulu firewall\", \"little snitch\", \"redes macos\", \"diagnóstico firewall\"."
    ),
    "opentimestamps-l5-diagnostics": (
        "Verificación de atestación criptográfica y estampados temporales L5 en Bitcoin (OpenTimestamps). "
        "Dispara con \"opentimestamps\", \"ots verify\", \"atestación l5\", \"bitcoin timestamp\", \"l5 diagnostics\"."
    ),
    "polymath-concept-synthesis": (
        "Síntesis polímata de conceptos complejos integrando física, matemáticas, teoría de la información y arte (Modo ULTRATHINK). "
        "Dispara con \"ultrathink\", \"síntesis polímata\", \"polymath synthesis\", \"concepto polímata\", \"unificación interdisciplinar\"."
    ),
    "reddit-socint-extraction": (
        "Extracción de inteligencia social (SOCINT) y tendencias en subreddits de Reddit. "
        "Dispara con \"reddit socint\", \"reddit osint\", \"scraping reddit\", \"inteligencia reddit\"."
    ),
    "substack-socint-extraction": (
        "Extracción de inteligencia social (SOCINT) y análisis de publicaciones en Substack. "
        "Dispara con \"substack socint\", \"substack osint\", \"scraping newsletter\", \"análisis substack\"."
    ),
    "suno-bracket-tagging": (
        "Generación de prompts y etiquetas musicales estructuradas para motores de síntesis de audio AI (Suno / Udio). "
        "Dispara con \"suno prompt\", \"udio tags\", \"prompt musical\", \"etiquetas suno\"."
    ),
    "swarm-quantum-collapse": (
        "Orquesta un enjambre Python P×S calibrado empíricamente para forzar la sincronización (Colapso Cuántico) de múltiples repositorios de forma simultánea. Purga locks, ancla ramas, fuerza SSH y realiza commit/push determinista. "
        "Dispara con \"swarm quantum collapse\", \"colapso cuántico\", \"sincronizar enjambre\", \"orquestar repos\", \"swarm sync\"."
    ),
    "vscode-git-packed-refs-diagnostics": (
        "Reparación de corruptelas de Git, bloqueos de packed-refs e índice de repositorios en VS Code / Antigravity IDE. "
        "Dispara con \"vscode git enoent\", \"packed-refs\", \"corrupción git\", \"reparar git vscode\"."
    ),
    "whatsapp-nexus-protocol": (
        "Orquestación de pasarela soberana de WhatsApp (Baileys / Rust bridge) para mensajería interactiva. "
        "Dispara con \"whatsapp nexus\", \"bot whatsapp\", \"baileys rust\", \"pasarela whatsapp\", \"whatsapp gateway\"."
    ),
    "youtube-analysis-pipeline": (
        "Extracción de transcripciones, análisis visual de escenas y auditoría de contenido en YouTube. "
        "Dispara con \"youtube analysis\", \"youtube transcript\", \"auditoría youtube\", \"analizar video youtube\"."
    ),
    "youtube-remotion-sota": (
        "Renderizado programático de vídeo SOTA utilizando React y Remotion engine. "
        "Dispara con \"youtube remotion\", \"remotion render\", \"react video synthesis\", \"renderizar vídeo remotion\"."
    ),
}


def optimize_triggers() -> None:
    updated_count = 0
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue

        skill_name = skill_dir.name
        new_desc = ENRICHED_DESCRIPTIONS.get(skill_name)
        if not new_desc:
            continue

        content = skill_file.read_text(encoding="utf-8")
        match = re.search(r"^\s*---\s*\n(.*?)\n---", content, re.DOTALL)
        if not match:
            continue

        # Format clean YAML header
        clean_desc = new_desc.replace('"', '\\"')
        new_header = f'---\nname: {skill_name}\ndescription: "{clean_desc}"\n---'

        body = content[match.end():]
        new_content = new_header + body
        skill_file.write_text(new_content, encoding="utf-8")
        updated_count += 1

    print(f"Successfully optimized frontmatter triggers for {updated_count} physical skills.")


if __name__ == "__main__":
    optimize_triggers()
