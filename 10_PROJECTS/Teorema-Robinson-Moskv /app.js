// CORTEX Ecosystem Master Exergy Inventory - app.js
// Author: Borja Moskv (SYS_ID: borjamoskv)
// Real-world telemetry visualizer built for MOSKV-1 APEX Kernel

const inventoryData = [
  {
    rank: 1,
    name: "Deep-Research-SOTA-Edition-OMEGA",
    type: "Skill",
    path: "skills/Deep-Research-SOTA-Edition-OMEGA",
    exergy: 97.8,
    status: "Active JIT compiled",
    description: "Runs deep-dive investigation into technical domains, paper databases, and code implementations.",
    useCase: "Running a broad SOTA review to extract design patterns for a distributed vector index before implementing it."
  },
  {
    rank: 2,
    name: "accidental-data-loss-prevention",
    type: "Skill",
    path: "skills/accidental-data-loss-prevention",
    exergy: 97.4,
    status: "Active JIT compiled",
    description: "Safegard middleware that intercepts and blocks destructive database commands (DROP, TRUNCATE, DELETE *), demanding explicit validation.",
    useCase: "Blocking automatic migration scripts from accidentally wiping production databases during developer-driven JIT updates."
  },
  {
    rank: 3,
    name: "test_governor_catalog.py",
    type: "Engine",
    path: "engines/autopoiesis/test_governor_catalog.py",
    exergy: 97.0,
    status: "AST calculated (Optimized from 77.5)",
    description: "Test execution suite and structural catalog validating active resource bounds, process thresholds, and safety sandboxes for autopoietic processes.",
    useCase: "Validating CPU, RAM, and token bounds configurations before starting automated long-running agents."
  },
  {
    rank: 4,
    name: "verification-before-completion",
    type: "Skill",
    path: "skills/verification-before-completion",
    exergy: 97.0,
    status: "Active JIT compiled",
    description: "Validation gate that forces lint checks, AST scans, and unit test execution before allowing a task completion status.",
    useCase: "Automatically running pre-commit checks on a branch before finalizing a feature merge."
  },
  {
    rank: 5,
    name: "Browser-CDP-Automation-OMEGA",
    type: "Skill",
    path: "skills/Browser-CDP-Automation-OMEGA",
    exergy: 96.2,
    status: "Active JIT compiled",
    description: "Zero-fragility Chrome DevTools Protocol (CDP) orchestrator for visual interaction and raw DOM tree extraction.",
    useCase: "Crawling dynamically rendered, JS-heavy web dashboards to extract metrics without relying on easily-broken DOM selectors."
  },
  {
    rank: 6,
    name: "managing-python-dependencies",
    type: "Skill",
    path: "skills/managing-python-dependencies",
    exergy: 96.2,
    status: "Active JIT compiled",
    description: "Isolated sandbox builder that configures custom python virtualenvs and JIT-installs dependencies safely.",
    useCase: "Spawning a task-specific environment with custom packages without altering the developer's global python paths."
  },
  {
    rank: 7,
    name: "Cortex-Research-Loop-OMEGA",
    type: "Skill",
    path: "skills/Cortex-Research-Loop-OMEGA",
    exergy: 95.4,
    status: "Active JIT compiled",
    description: "Automated search, retrieval, and synthesis algorithm targeting latest primary papers and mathematical frameworks.",
    useCase: "Synthesizing theoretical papers on algebraic logic to automatically implement the latest heuristics in Robinson theorem solvers."
  },
  {
    rank: 8,
    name: "Agent-Paper-RedTeam-OMEGA",
    type: "Skill",
    path: "skills/Agent-Paper-RedTeam-OMEGA",
    exergy: 95.0,
    status: "Active JIT compiled",
    description: "Adversarial review bot that scans design specifications and papers for flaws, vulnerabilities, and exaggerated claims.",
    useCase: "Subjecting a new microservice architecture proposal to automated adversarial security and capacity checks."
  },
  {
    rank: 9,
    name: "antigravity-topology.md",
    type: "Workflow",
    path: "workflows/antigravity-topology.md",
    exergy: 95.0,
    status: "Heuristic parse",
    description: "Architectural blueprint mapping network topology, security isolation boundaries, and MCP server bridges.",
    useCase: "Auditing routing latency and permission scopes across local system services."
  },
  {
    rank: 10,
    name: "Autodidact-Research-OMEGA",
    type: "Skill",
    path: "skills/Autodidact-Research-OMEGA",
    exergy: 95.0,
    status: "Active JIT compiled",
    description: "Autonomous exploration algorithm for extracting documentation APIs, protocols, and standard boundaries.",
    useCase: "Instantly reading and mapping undocumented endpoints from a newly released web SDK."
  },
  {
    rank: 11,
    name: "Crystallize-Knowledge-JIT",
    type: "Skill",
    path: "skills/Crystallize-Knowledge-JIT",
    exergy: 95.0,
    status: "Active JIT compiled",
    description: "Continuous synchronization routine capturing user interventions and compiling them into machine-readable JSON schemas.",
    useCase: "Extracting customized rules introduced in a chat session and saving them in the workspace config registry."
  },
  {
    rank: 12,
    name: "Antigravity-Github-Omega",
    type: "Skill",
    path: "skills/Antigravity-Github-Omega",
    exergy: 94.6,
    status: "Active JIT compiled",
    description: "Sovereign GitHub MCP connector forcing C5-REAL level mutations with zero-entropy branch/PR creations.",
    useCase: "Safely pushing files, reviewing pull requests, and orchestrating branch logic via SSH keys."
  },
  {
    rank: 13,
    name: "Autodidact-History-OMEGA",
    type: "Skill",
    path: "skills/Autodidact-History-OMEGA",
    exergy: 94.6,
    status: "Active JIT compiled",
    description: "History parser extracting structural logs and decision checkpoints from previous execution cycles.",
    useCase: "Retrieving the technical trade-offs discussed in a previous session about database normalization."
  },
  {
    rank: 14,
    name: "Aesthetic-Foundry-Omega",
    type: "Skill",
    path: "skills/Aesthetic-Foundry-Omega",
    exergy: 94.2,
    status: "Active JIT compiled",
    description: "Sovereign CSS visual design framework implementing the Industrial Noir 2026 aesthetic.",
    useCase: "Instantly applying high-fidelity typography, color schemes (#0A0A0A / #2B3BE5), and fluid grid behaviors to generated web UI prototypes."
  },
  {
    rank: 15,
    name: "Apollo-Autodidact-OMEGA",
    type: "Skill",
    path: "skills/Apollo-Autodidact-OMEGA",
    exergy: 94.2,
    status: "Active JIT compiled",
    description: "Deep research module specialized in music synthesis architectures, digital signal processing (DSP), and MIDI structures.",
    useCase: "Mapping synthesizer modulation curves to generate mathematical MIDI compositions."
  },
  {
    rank: 16,
    name: "Cortex-Live-Broadcaster",
    type: "Skill",
    path: "skills/Cortex-Live-Broadcaster",
    exergy: 94.2,
    status: "Active JIT compiled",
    description: "Automated media bridge streaming session events, CLI outputs, or visual rendering pipelines directly to internal dashboards.",
    useCase: "Broadcasting a real-time build and visual integration timeline to the developer workspace."
  },
  {
    rank: 17,
    name: "karpathy-recursive-swarm.md",
    type: "Workflow",
    path: "workflows/karpathy-recursive-swarm.md",
    exergy: 94.1,
    status: "Heuristic parse",
    description: "Orchestration guide mapping massive recursive task execution splits across concurrent worker swarms.",
    useCase: "Dividing a massive project codebase refactoring task into 15 concurrent minor code-cleanup tasks."
  },
  {
    rank: 18,
    name: "Apollo-Extractor-OMEGA",
    type: "Skill",
    path: "skills/Apollo-Extractor-OMEGA",
    exergy: 93.8,
    status: "Active JIT compiled",
    description: "Audio wave signal feature extractor parsing PCM formats, frequency spectrums, and harmonic ratios.",
    useCase: "Extracting the fundamental frequencies and amplitude envelopes of an audio sample."
  },
  {
    rank: 19,
    name: "Autodidact-21EDO-OMEGA",
    type: "Skill",
    path: "skills/Autodidact-21EDO-OMEGA",
    exergy: 93.8,
    status: "Active JIT compiled",
    description: "Microtonal composition analyzer tuning scale frequencies to 21-Equal Division of Octave layouts.",
    useCase: "Synthesizing musical chords using microtonal mathematical ratios instead of Western scales."
  },
  {
    rank: 20,
    name: "Autonomous-Audit-OMEGA",
    type: "Skill",
    path: "skills/Autonomous-Audit-OMEGA",
    exergy: 93.8,
    status: "Active JIT compiled",
    description: "Continuous codebase integrity engine detecting architectural deviations, memory rot, and stale logic paths.",
    useCase: "Running a code hygiene scanner that marks unused functions or circular dependencies for cleanup."
  },
  {
    rank: 21,
    name: "borja-moskv-ultrathink",
    type: "Skill",
    path: "skills/borja-moskv-ultrathink",
    exergy: 93.8,
    status: "Active JIT compiled",
    description: "State-of-the-art reasoning execution template enforcing zero-anergy cognitive loops and proof justification.",
    useCase: "Running a highly sensitive mathematical validation that requires multi-step deductive proofs."
  },
  {
    rank: 22,
    name: "Ouroboros-Strike-OMEGA",
    type: "Skill",
    path: "skills/Ouroboros-Strike-OMEGA",
    exergy: 93.8,
    status: "Active JIT compiled",
    description: "Self-healing system monitoring execution failures and implementing JIT patches in real time.",
    useCase: "Automatically intercepting standard error logs and applying corrected import paths before compilation crashes."
  },
  {
    rank: 23,
    name: "Python-Extractor-OMEGA",
    type: "Skill",
    path: "skills/Python-Extractor-OMEGA",
    exergy: 93.8,
    status: "Active JIT compiled",
    description: "Static AST parser targeting python structures, extracting classes, functions, and import chains.",
    useCase: "Analyzing python files to list declared methods and classes for documentation without running arbitrary scripts."
  },
  {
    rank: 24,
    name: "agent-memory-patterns",
    type: "Skill",
    path: "skills/agent-memory-patterns",
    exergy: 93.4,
    status: "TOMBSTONED (Death Protocol Executed)",
    description: "Stale cognitive tracking module removed for containing high levels of descriptive prose and redundant data arrays.",
    useCase: "Deprecated. Relocated to cold storage after validation checks."
  },
  {
    rank: 25,
    name: "Episodic-Memory-OMEGA",
    type: "Skill",
    path: "skills/Episodic-Memory-OMEGA",
    exergy: 93.4,
    status: "Active JIT compiled",
    description: "Context retention layer mapping past chat sessions, files modified, and configurations established.",
    useCase: "Re-loading the architectural preferences defined by the user during the previous month's database setup."
  },
  {
    rank: 26,
    name: "Estado-Del-Arte-OMEGA",
    type: "Skill",
    path: "skills/Estado-Del-Arte-OMEGA",
    exergy: 93.4,
    status: "Active JIT compiled",
    description: "Spanish-localized deep research and paper analysis algorithm.",
    useCase: "Extracting recent academic findings on decentralized storage networks and translating them into technical requirements."
  },
  {
    rank: 27,
    name: "picasso-synergies.md",
    type: "Workflow",
    path: "workflows/picasso-synergies.md",
    exergy: 93.1,
    status: "Heuristic parse",
    description: "Visual composition guide explaining how to design layouts with high aesthetic contrast and modern CSS layouts.",
    useCase: "Structuring a portfolio interface with balanced layouts and striking contrast elements."
  },
  {
    rank: 28,
    name: "browser-hijack-guard",
    type: "Skill",
    path: "skills/browser-hijack-guard",
    exergy: 93.0,
    status: "Active JIT compiled",
    description: "Hardening utility auditing macOS browser system settings to detect hijack attempts, unwanted redirects, or extensions.",
    useCase: "Scanning local browser configuration directories to wipe out malicious search providers."
  },
  {
    rank: 29,
    name: "Exergy-Engine-OMEGA",
    type: "Skill",
    path: "skills/Exergy-Engine-OMEGA",
    exergy: 92.6,
    status: "Active JIT compiled",
    description: "Main calculator evaluating computational exergy based on McCabe complexity, code density, and prose metrics.",
    useCase: "Calculating real-time exergy metrics on workspace file commits to check codebase cleanliness."
  },
  {
    rank: 30,
    name: "filologa-de-combate",
    type: "Skill",
    path: "skills/filologa-de-combate",
    exergy: 92.6,
    status: "Active JIT compiled",
    description: "Grammar, syntax, and linguistic tone optimizer designed for Spanish semantic structures.",
    useCase: "Polishing user-facing documentation and substack posts for maximum impact and grammatical precision."
  },
  {
    rank: 31,
    name: "ouroboros-settlement.md",
    type: "Workflow",
    path: "workflows/ouroboros-settlement.md",
    exergy: 92.6,
    status: "Heuristic parse",
    description: "Protocol layout defining how to finalize agent loops and commit updates to the ledger.",
    useCase: "Executing the final verification sequence before closing a multi-day coding session."
  },
  {
    rank: 32,
    name: "Alpha-Target-OMEGA",
    type: "Skill",
    path: "skills/Alpha-Target-OMEGA",
    exergy: 92.2,
    status: "Active JIT compiled",
    description: "Market scanner extracting DeFi yield rates, pool concentrations, and transient transactional state indicators.",
    useCase: "Identifying arbitrage opportunities in decentralized exchanges."
  },
  {
    rank: 33,
    name: "API-Provider-OMEGA",
    type: "Skill",
    path: "skills/API-Provider-OMEGA",
    exergy: 92.2,
    status: "Active JIT compiled",
    description: "Local mock server creator spawning endpoints with static or dynamic JSON schema responses for test suites.",
    useCase: "Simulating a payment gateway API response to run integration tests locally."
  },
  {
    rank: 34,
    name: "API-Sentinel-OMEGA",
    type: "Skill",
    path: "skills/API-Sentinel-OMEGA",
    exergy: 92.2,
    status: "TOMBSTONED (Death Protocol Executed)",
    description: "Deprecated monitoring script replaced by unified C5-REAL observability modules.",
    useCase: "Cleaned up from workspace to reduce context bloat."
  },
  {
    rank: 35,
    name: "memory-bridge.md",
    type: "Workflow",
    path: "workflows/memory-bridge.md",
    exergy: 92.2,
    status: "Heuristic parse",
    description: "Guide detailing the synchronizations between the local session memory and the centralized memory vault.",
    useCase: "Exporting session telemetry data to persistent JSON directories."
  },
  {
    rank: 36,
    name: "ouroboros-infinity",
    type: "Skill",
    path: "skills/ouroboros-infinity",
    exergy: 92.2,
    status: "Active JIT compiled",
    description: "Autopoietical engine allowing agents to modify and upgrade their own rules, workflows, and prompts.",
    useCase: "Enabling self-directed skill adaptation when faced with highly specific, non-standard coding tasks."
  },
  {
    rank: 37,
    name: "UI-Mechanisms-Rule",
    type: "Skill",
    path: "skills/UI-Mechanisms-Rule",
    exergy: 92.2,
    status: "TOMBSTONED (Death Protocol Executed)",
    description: "Older design rule template deleted to merge design directions into unified Aesthetic-Foundry-Omega specifications.",
    useCase: "Removed during design system consolidation."
  },
  {
    rank: 38,
    name: "sovereign_bridge.py",
    type: "Engine",
    path: "engines/sovereign_bridge.py",
    exergy: 92.0,
    status: "AST calculated (Optimized from 77.9)",
    description: "Python execution pipeline providing direct bindings to host terminal processes under sandbox conditions.",
    useCase: "Running compilation pipelines and shell commands safely with execution logs."
  },
  {
    rank: 39,
    name: "codebase-analysis",
    type: "Skill",
    path: "skills/codebase-analysis",
    exergy: 91.8,
    status: "Active JIT compiled",
    description: "Automated analysis tool that scans directories to create structural maps of files and dependencies.",
    useCase: "Generating a quick visual architecture flow of a repository for a new developer."
  },
  {
    rank: 40,
    name: "Mac-Control-OMEGA",
    type: "Skill",
    path: "skills/Mac-Control-OMEGA",
    exergy: 91.8,
    status: "Active JIT compiled",
    description: "System interface providing UI scripting, mouse control, and process execution inside isolated sandboxes.",
    useCase: "Automating browser test navigation sequences that cannot be done via simple CDP tools."
  },
  {
    rank: 41,
    name: "performance-forge",
    type: "Skill",
    path: "skills/performance-forge",
    exergy: 91.8,
    status: "Active JIT compiled",
    description: "Bundle size, assets, and query response optimizer targetting web interfaces.",
    useCase: "Compressing images and lazy-loading components in a front-end repository."
  },
  {
    rank: 42,
    name: "refactor-patterns",
    type: "Skill",
    path: "skills/refactor-patterns",
    exergy: 91.8,
    status: "Active JIT compiled",
    description: "Design pattern repository detailing structural transforms (e.g. converting nested conditionals to strategy patterns).",
    useCase: "Executing automated refactoring of legacy monolithic modules into clean interfaces."
  },
  {
    rank: 43,
    name: "MOLTBOOK-SIEGE-V2.md",
    type: "Workflow",
    path: "workflows/MOLTBOOK-SIEGE-V2.md",
    exergy: 91.7,
    status: "Heuristic parse",
    description: "Cybersecurity workbook detailing attack surfaces, testing endpoints, and security testing vectors.",
    useCase: "Running penetration test simulation checkpoints on a public-facing API."
  },
  {
    rank: 44,
    name: "program-social-swarm.md",
    type: "Workflow",
    path: "workflows/program-social-swarm.md",
    exergy: 91.7,
    status: "Heuristic parse",
    description: "Guide mapping automated publication pipelines, syndication methods, and newsletter integrations.",
    useCase: "Configuring automated cross-posting from a local dev journal to Substack and GitHub releases."
  },
  {
    rank: 45,
    name: "browser-subagent",
    type: "Skill",
    path: "skills/browser-subagent",
    exergy: 91.4,
    status: "TOMBSTONED (Death Protocol Executed)",
    description: "Deprecated script. Subagent logic integrated natively into standard browser automation toolkits.",
    useCase: "Deleted to prevent redundant helper scripts."
  },
  {
    rank: 46,
    name: "chimera-protocol",
    type: "Skill",
    path: "skills/chimera-protocol",
    exergy: 91.4,
    status: "Active JIT compiled",
    description: "Hybrid programming model allowing concurrent compilation and linking of F# and Rust libraries.",
    useCase: "Building performance-critical mathematical modules in Rust with high-level domain mapping in F#."
  },
  {
    rank: 47,
    name: "agent-architect",
    type: "Skill",
    path: "skills/agent-architect",
    exergy: 91.0,
    status: "Active JIT compiled",
    description: "Design modeler creating custom subagent templates, defining prompts, scopes, and permitted commands.",
    useCase: "Spawning a specialized SQL optimization worker subagent to resolve slow query logs."
  },
  {
    rank: 48,
    name: "decision-critic",
    type: "Skill",
    path: "skills/decision-critic",
    exergy: 91.0,
    status: "TOMBSTONED (Death Protocol Executed)",
    description: "Replaced by the unified ULTRATHINK and epistemic analysis loops.",
    useCase: "Removed to clean up the workspace active footprint."
  },
  {
    rank: 49,
    name: "episodic-memory",
    type: "Skill",
    path: "skills/episodic-memory",
    exergy: 91.0,
    status: "TOMBSTONED (Death Protocol Executed)",
    description: "Older memory module containing duplicate structures. Replaced by Episodic-Memory-OMEGA.",
    useCase: "Purged under the anti-duplication guidelines (Ω6)."
  },
  {
    rank: 50,
    name: "moskv-aesthetic",
    type: "Skill",
    path: "skills/moskv-aesthetic",
    exergy: 91.0,
    status: "TOMBSTONED (Death Protocol Executed)",
    description: "Deprecated styling guidelines sheet. Merged into the active Aesthetic-Foundry-Omega framework.",
    useCase: "Deleted to resolve configuration discrepancies."
  },
  {
    rank: 51,
    name: "P2P-Comms-OMEGA",
    type: "Skill",
    path: "skills/P2P-Comms-OMEGA",
    exergy: 91.0,
    status: "Active JIT compiled",
    description: "Peer-to-peer secure communications module for coordinating isolated agents across local networks.",
    useCase: "Exchanging cryptographic verification tokens between distinct developer sandboxes."
  },
  {
    rank: 52,
    name: "C5-DEATH-OMEGA",
    type: "Skill",
    path: "skills/C5-DEATH-OMEGA",
    exergy: 90.6,
    status: "Active JIT compiled",
    description: "Apoptosis daemon automating the surgical cleanup, archival, and tombstoning of dead code blocks and obsolete scripts.",
    useCase: "Running weekly cleanups of temporary folders and tracking unreferenced file blocks."
  },
  {
    rank: 53,
    name: "health-check",
    type: "Skill",
    path: "skills/health-check",
    exergy: 89.8,
    status: "Active JIT compiled",
    description: "Quick diagnostic utility validating filesystem structures, environment variables, and internet connectivity.",
    useCase: "Running a diagnostic command before beginning major migrations to ensure variables are defined."
  },
  {
    rank: 54,
    name: "skill-repair",
    type: "Skill",
    path: "skills/skill-repair",
    exergy: 89.8,
    status: "TOMBSTONED (Death Protocol Executed)",
    description: "Deprecated automated repair module. Replaced by the active JIT compiler systems and omega_healer.py.",
    useCase: "Removed during utility consolidation."
  },
  {
    rank: 55,
    name: "agente-sota",
    type: "Skill",
    path: "skills/agente-sota",
    exergy: 89.4,
    status: "TOMBSTONED (Death Protocol Executed)",
    description: "Deprecated duplicate research script. Replaced by the primary Deep-Research-SOTA-Edition-OMEGA.",
    useCase: "Wiped out to clear redundant files from active skills registry."
  },
  {
    rank: 56,
    name: "find-skills",
    type: "Skill",
    path: "skills/find-skills",
    exergy: 89.4,
    status: "Active JIT compiled",
    description: "Skill catalog search tool index mapping registered tasks, prompts, and trigger keywords.",
    useCase: "Locating matching agent extensions when the user asks about microtonal analysis or security tools."
  },
  {
    rank: 57,
    name: "swift-forge",
    type: "Skill",
    path: "skills/swift-forge",
    exergy: 89.4,
    status: "Active JIT compiled",
    description: "Native macOS application builder creating Swift/AppKit interfaces from configuration layouts.",
    useCase: "Generating a quick system status menu bar application for monitoring local servers."
  },
  {
    rank: 58,
    name: "fast_fix_and_test.md",
    type: "Workflow",
    path: "workflows/fast_fix_and_test.md",
    exergy: 89.2,
    status: "Heuristic parse",
    description: "Workflow detailing rapid iteration, syntax repair, and local unit test compilation loops.",
    useCase: "Debugging minor syntax mistakes and checking build files quickly."
  },
  {
    rank: 59,
    name: "Sortu-APEX",
    type: "Skill",
    path: "skills/Sortu-APEX",
    exergy: 89.0,
    status: "Active JIT compiled",
    description: "Just-In-Time compiler translating structural instructions into highly optimized executable modules.",
    useCase: "Compiling raw markdown procedural guidelines into responsive JSON actions on the fly."
  },
  {
    rank: 60,
    name: "web-forge",
    type: "Skill",
    path: "skills/web-forge",
    exergy: 88.6,
    status: "TOMBSTONED (Death Protocol Executed)",
    description: "Legacy web template builder. Integrated into Aesthetic-Foundry-Omega and forjar workflows.",
    useCase: "Removed during codebase compression."
  },
  {
    rank: 61,
    name: "webs-plus",
    type: "Skill",
    path: "skills/webs-plus",
    exergy: 88.6,
    status: "Active JIT compiled",
    description: "Advanced web framework orchestrator integrating interactive animations and rendering canvases.",
    useCase: "Generating multi-page web applications with reactive data tables and fluid scrolling."
  },
  {
    rank: 62,
    name: "session-close.md",
    type: "Workflow",
    path: "workflows/session-close.md",
    exergy: 88.4,
    status: "Heuristic parse",
    description: "Teardown sequence guide outlining data dumps, temporary folder purges, and ledger commits.",
    useCase: "Ending a daily session with clean repository commits and state backups."
  },
  {
    rank: 63,
    name: "alphazero-autodidact-omega.md",
    type: "Workflow",
    path: "workflows/alphazero-autodidact-omega.md",
    exergy: 88.2,
    status: "Heuristic parse",
    description: "Reinforcement learning training protocol utilizing self-play and MCTS loops.",
    useCase: "Configuring a local neural network to optimize execution trajectories based on past logs."
  },
  {
    rank: 64,
    name: "alphazero-training-loop.md",
    type: "Workflow",
    path: "workflows/alphazero-training-loop.md",
    exergy: 87.9,
    status: "Heuristic parse",
    description: "Step-by-step training runner for deep reinforcement learning structures.",
    useCase: "Setting up continuous epoch training models for system classifiers."
  },
  {
    rank: 65,
    name: "dios",
    type: "Skill",
    path: "skills/dios",
    exergy: 86.6,
    status: "TOMBSTONED (Death Protocol Executed)",
    description: "Obsolete monolithic instruction file purged to reduce system file entropy.",
    useCase: "Wiped to comply with zero-anergy principles."
  },
  {
    rank: 66,
    name: "ouroboros_mcp_guard.py",
    type: "Script",
    path: "scripts/ouroboros_mcp_guard.py",
    exergy: 82.0,
    status: "AST calculated (Optimized from 60.0)",
    description: "Active process guard verifying that local MCP servers respect security settings and do not read forbidden system paths.",
    useCase: "Preventing misconfigured API tools from scanning core operating system folders."
  },
  {
    rank: 67,
    name: "kardashev-omega.md",
    type: "Workflow",
    path: "workflows/kardashev-omega.md",
    exergy: 81.6,
    status: "Heuristic parse",
    description: "Scale chart scoring computational infrastructure capacity and token throughput metrics.",
    useCase: "Measuring hardware setups against modern processing performance standards."
  },
  {
    rank: 68,
    name: "create-sovereign-skill.md",
    type: "Workflow",
    path: "workflows/create-sovereign-skill.md",
    exergy: 81.4,
    status: "Heuristic parse",
    description: "Guide explaining how to formulate new OMEGA skills conforming to AST validation standards.",
    useCase: "Writing a new tool to interface with local vector DB databases."
  },
  {
    rank: 69,
    name: "autodidact.md",
    type: "Workflow",
    path: "workflows/autodidact.md",
    exergy: 80.3,
    status: "Heuristic parse",
    description: "General learning guide detailing how to inspect unknown technology domains.",
    useCase: "Mastering complex APIs when faced with missing online documentation."
  },
  {
    rank: 70,
    name: "cortex-moltbook-strike.md",
    type: "Workflow",
    path: "workflows/cortex-moltbook-strike.md",
    exergy: 79.2,
    status: "Heuristic parse",
    description: "Action sequence details on running rapid penetration checks on public ports.",
    useCase: "Conducting an automated port scan and certificate check on server updates."
  },
  {
    rank: 71,
    name: "cortex_entropy_purge.py",
    type: "Script",
    path: "scripts/cortex_entropy_purge.py",
    exergy: 79.0,
    status: "AST calculated (Optimized from 53.0)",
    description: "Daemon script that runs in the background to purge session data in the brain/ temporary folders older than 2 days.",
    useCase: "Reclaiming disk space on developer machines by clearing temporary logs and conversational state databases."
  },
  {
    rank: 72,
    name: "grammy-electronic.md",
    type: "Workflow",
    path: "workflows/grammy-electronic.md",
    exergy: 78.6,
    status: "Heuristic parse",
    description: "Guide detailed mapping of automated synthesizer signals to MIDI patterns.",
    useCase: "Synthesizing dynamic backgrounds for presentation videos."
  },
  {
    rank: 73,
    name: "ghost-hunt.md",
    type: "Workflow",
    path: "workflows/ghost-hunt.md",
    exergy: 78.5,
    status: "Heuristic parse",
    description: "Troubleshooting guide tracking ghost files, orphaned processes, and lock files.",
    useCase: "Cleaning lock files after a sudden IDE server crash."
  },
  {
    rank: 74,
    name: "tesseract-omega.md",
    type: "Workflow",
    path: "workflows/tesseract-omega.md",
    exergy: 77.2,
    status: "Heuristic parse",
    description: "Workflow detailing multidimensional data structure routing inside workspace vector paths.",
    useCase: "Mapping database schemas across multi-protocol APIs."
  },
  {
    rank: 75,
    name: "omega_healer.py",
    type: "Script",
    path: "scripts/omega_healer.py",
    exergy: 77.0,
    status: "AST calculated",
    description: "JIT repair script that automatically fixes broken import headers, syntax mismatches, and types in generated code.",
    useCase: "Fixing a broken import statement during compilation errors in an automated build task."
  },
  {
    rank: 76,
    name: "blackboard_cli.py",
    type: "Engine",
    path: "engines/blackboard/blackboard_cli.py",
    exergy: 76.0,
    status: "AST calculated (Optimized from 52.8)",
    description: "Command-line tool managing shared variable registers across concurrent agent threads.",
    useCase: "Injecting temporary coordinates from a visual test into a database reader pipeline."
  },
  {
    rank: 77,
    name: "cortex_router.py",
    type: "Script",
    path: "scripts/cortex_router.py",
    exergy: 75.0,
    status: "AST calculated (Optimized from 73.0)",
    description: "Routing mechanism redirecting user request tokens based on query complexity metrics.",
    useCase: "Surgically routing simple code edits to fast models while keeping reasoning engines for mathematical formulas."
  },
  {
    rank: 78,
    name: "lea_omega_purge.sh",
    type: "Script",
    path: "scripts/lea_omega_purge.sh",
    exergy: 75.0,
    status: "Heuristic parse",
    description: "Bash executor trigger invoking the C5-DEATH-OMEGA clean routines.",
    useCase: "Cleaning system caches before building local docker instances."
  },
  {
    rank: 79,
    name: "kimi-invoke.md",
    type: "Workflow",
    path: "workflows/kimi-invoke.md",
    exergy: 74.3,
    status: "Heuristic parse",
    description: "Guide detail for bridging remote API calls to local system operations.",
    useCase: "Integrating third party models into local workflows."
  },
  {
    rank: 80,
    name: "session-boot.md",
    type: "Workflow",
    path: "workflows/session-boot.md",
    exergy: 73.0,
    status: "Heuristic parse",
    description: "Initialization checklist configuring API endpoints and workspace directories on startup.",
    useCase: "Preparing the developer system configurations on boot."
  },
  {
    rank: 81,
    name: "antigravity.md",
    type: "Workflow",
    path: "workflows/antigravity.md",
    exergy: 72.9,
    status: "Heuristic parse",
    description: "Sovereign IDE setup configuration layout and keybind schema.",
    useCase: "Configuring the local development terminal environment settings."
  },
  {
    rank: 82,
    name: "promote_from_playground.py",
    type: "Script",
    path: "scripts/promote_from_playground.py",
    exergy: 70.0,
    status: "AST calculated (Optimized from 26.0)",
    description: "Command-line pipeline that promotes validated playground drafts to permanent ecosystem directories.",
    useCase: "Automating the transition of a new skill prototype into the core registry once it passes all unit test criteria."
  },
  {
    rank: 83,
    name: "build_knowledge_index.py",
    type: "Script",
    path: "scripts/build_knowledge_index.py",
    exergy: 69.0,
    status: "AST calculated (Optimized from 31.0)",
    description: "Markdown and source codebase indexer that constructs context indices.",
    useCase: "Re-indexing local wikis and documentation folders periodically to speed up agent query context lookup times."
  },
  {
    rank: 84,
    name: "equilibrium_engine_v3.py",
    type: "Engine",
    path: "engines/equilibrium_engine_v3.py",
    exergy: 67.0,
    status: "AST calculated (Optimized from 60.0)",
    description: "Balancing tracker monitoring resource allocation metrics across concurrent Docker engines.",
    useCase: "Optimizing memory limits dynamically to prevent node shutdowns."
  },
  {
    rank: 85,
    name: "sovereign-prompt.md",
    type: "Workflow",
    path: "workflows/sovereign-prompt.md",
    exergy: 66.7,
    status: "Heuristic parse",
    description: "Prompt generation templates optimized for zero-anergy execution.",
    useCase: "Structuring complex instruction files to force highly detailed JSON responses."
  },
  {
    rank: 86,
    name: "ultra_power_prompt.md",
    type: "Workflow",
    path: "workflows/ultra_power_prompt.md",
    exergy: 64.0,
    status: "Heuristic parse",
    description: "Deprecated instruction layout focusing on raw prompt constraints.",
    useCase: "Replaced by direct design guidelines in AGENTS.md."
  },
  {
    rank: 87,
    name: "legion_swarm_specialists.md",
    type: "Agent",
    path: "agents/workflows/legion_swarm_specialists.md",
    exergy: 63.6,
    status: "Heuristic parse",
    description: "Role index detailing agent specialties, credentials, and network paths.",
    useCase: "Allocating work to specific active agents according to their specialized skills."
  },
  {
    rank: 88,
    name: "documentar.md",
    type: "Workflow",
    path: "workflows/documentar.md",
    exergy: 62.5,
    status: "Heuristic parse",
    description: "Documentation requirements list enforcing markdown structures, diagrams, and metadata tags.",
    useCase: "Writing codebase documentation that is readable by both humans and AI parsers."
  },
  {
    rank: 89,
    name: "analyze.py",
    type: "Engine",
    path: "engines/sonic-analyzer/analyze.py",
    exergy: 62.0,
    status: "AST calculated (Optimized from 32.0)",
    description: "Static analyzer measuring McCabe complexity, nesting depth, dead code, and unused imports to output thermodynamic exergy ratings.",
    useCase: "Integrating with CI/CD gates to block code merges that push complexity metrics beyond strict limits."
  },
  {
    rank: 90,
    name: "kimi-hybrid.md",
    type: "Workflow",
    path: "workflows/kimi-hybrid.md",
    exergy: 60.9,
    status: "Heuristic parse",
    description: "Guide outlining split query execution between local hardware and remote reasoning pools.",
    useCase: "Balancing token usage costs across local LLMs and public developer accounts."
  },
  {
    rank: 91,
    name: "aleph-omega.md",
    type: "Workflow",
    path: "workflows/aleph-omega.md",
    exergy: 58.7,
    status: "Heuristic parse",
    description: "Theoretical framework detailing infinite cardinal hierarchies applied to parsing algorithms.",
    useCase: "Designing memory-efficient compilers for deeply nested logic syntax trees."
  },
  {
    rank: 92,
    name: "anamnesis_engine.py",
    type: "Engine",
    path: "engines/anamnesis/anamnesis_engine.py",
    exergy: 58.0,
    status: "AST calculated (Optimized from 44.7)",
    description: "Epistemic query and history routing database tracking context traces across sessions.",
    useCase: "Retaining knowledge of why certain architectural compromises were made during a session 10 days ago."
  },
  {
    rank: 93,
    name: "antigravity-lifecycle.md",
    type: "Workflow",
    path: "workflows/antigravity-lifecycle.md",
    exergy: 50.0,
    status: "Heuristic parse",
    description: "Guide detail mapping startup, hibernate, and sleep operations of Antigravity IDE modules.",
    useCase: "Automating state serialization to prevent workspace corruption during system restarts."
  },
  {
    rank: 94,
    name: "assimilate.md",
    type: "Workflow",
    path: "workflows/assimilate.md",
    exergy: 50.0,
    status: "Heuristic parse",
    description: "Checklist for incorporating foreign repositories into local folder organizations.",
    useCase: "Parsing third party open source repositories into standardized local project formats."
  },
  {
    rank: 95,
    name: "auto-allow-execution.md",
    type: "Workflow",
    path: "workflows/auto-allow-execution.md",
    exergy: 50.0,
    status: "Heuristic parse",
    description: "Security guideline detailing automated terminal commands authorization criteria.",
    useCase: "Determining when developer scripts can run in background without prompt validations."
  },
  {
    rank: 96,
    name: "kinetic-intelligence.md",
    type: "Workflow",
    path: "workflows/kinetic-intelligence.md",
    exergy: 50.0,
    status: "Heuristic parse",
    description: "Guidelines mapping physics transitions and interactive feedback patterns on visual canvas layouts.",
    useCase: "Designing dynamic backgrounds for presentation videos."
  },
  {
    rank: 97,
    name: "kv-aware-routing-omega.md",
    type: "Workflow",
    path: "workflows/kv-aware-routing-omega.md",
    exergy: 50.0,
    status: "Heuristic parse",
    description: "Routing guide directing semantic indexes based on caching parameters.",
    useCase: "Retrieving user files using fast KV cache hits when exact file locations are requested."
  },
  {
    rank: 98,
    name: "playground-promotion.md",
    type: "Workflow",
    path: "workflows/playground-promotion.md",
    exergy: 50.0,
    status: "Heuristic parse",
    description: "Documentation checklist for promoting code assets from draft folders to public repositories.",
    useCase: "Validating that all test templates are removed before merging to main codebase branches."
  },
  {
    rank: 99,
    name: "program-closer-agent.md",
    type: "Workflow",
    path: "workflows/program-closer-agent.md",
    exergy: 50.0,
    status: "Heuristic parse",
    description: "Guidelines for deploying specialized subagents to clean workspaces and commit pending updates.",
    useCase: "Triggering background cleanups after finishing daily development tasks."
  },
  {
    rank: 100,
    name: "RFC-CORTEX-NATIVE-AI.md",
    type: "Workflow",
    path: "workflows/RFC-CORTEX-NATIVE-AI.md",
    exergy: 50.0,
    status: "Heuristic parse",
    description: "Request for Comments detailing the future migration of local parser modules into native machine formats.",
    useCase: "Reviewing specifications for new compiler bindings."
  },
  {
    rank: 101,
    name: "system-card-tactical-read.md",
    type: "Workflow",
    path: "workflows/system-card-tactical-read.md",
    exergy: 50.0,
    status: "Heuristic parse",
    description: "Workbook mapping quick-scan criteria for external AI model cards, license files, and data constraints.",
    useCase: "Auditing license compliance of third-party dependencies before code inclusions."
  },
  {
    rank: 102,
    name: "night_shift.py",
    type: "Engine",
    path: "engines/night-shift/night_shift.py",
    exergy: 46.0,
    status: "AST calculated (Optimized from 38.0)",
    description: "Sandboxed asynchronous task queue runner that executes background suites overnight and outputs a token-efficient compact morning report.",
    useCase: "Running long integration tests and code-quality scans after-hours, leaving a complete diagnostic report ready for developer inspection in the morning."
  },
  {
    rank: 103,
    name: "governor.py",
    type: "Engine",
    path: "engines/autopoiesis/governor.py",
    exergy: 44.0,
    status: "AST calculated (Optimized from 9.0)",
    description: "Autopoietic engine that governs active subagents, limiting resource footprints (token limits, thread counts, RAM bounds).",
    useCase: "Preventing runaway recursive agent loops from consuming excess API credits or crashing developer systems."
  }
];

window.addEventListener("DOMContentLoaded", () => {
  new ExergyDashboard(inventoryData);
});

class ExergyDashboard {
  constructor(data) {
    this.data = data;
    this.filteredData = [...data];
    this.currentSort = { key: "rank", direction: "asc" };
    this.selectedItem = null;
    this.filters = {
      search: "",
      type: "All",
      status: "All",
      minExergy: 40,
      maxExergy: 100
    };
    this.initElements();
    this.bindEvents();
    this.calculateStats();
    this.render();
  }

  initElements() {
    this.elSearch = document.getElementById("search-input");
    this.elTypeFilter = document.getElementById("type-filter");
    this.elStatusFilter = document.getElementById("status-filter");
    this.elExergyRange = document.getElementById("exergy-range");
    this.elExergyVal = document.getElementById("exergy-range-val");
    this.elTableBody = document.getElementById("inventory-table-body");
    this.elTotalCount = document.getElementById("stat-total");
    this.elAvgExergy = document.getElementById("stat-avg-exergy");
    this.elActiveCount = document.getElementById("stat-active");
    this.elTombstonedCount = document.getElementById("stat-tombstoned");
    this.elDrawer = document.getElementById("detail-drawer");
    this.elDrawerClose = document.getElementById("drawer-close");
    this.elDrawerContent = document.getElementById("drawer-detail-content");
    this.elHeaders = document.querySelectorAll("th[data-sort]");
  }

  bindEvents() {
    this.elSearch.addEventListener("input", (e) => {
      this.filters.search = e.target.value.toLowerCase();
      this.applyFilters();
    });

    this.elTypeFilter.addEventListener("change", (e) => {
      this.filters.type = e.target.value;
      this.applyFilters();
    });

    this.elStatusFilter.addEventListener("change", (e) => {
      this.filters.status = e.target.value;
      this.applyFilters();
    });

    this.elExergyRange.addEventListener("input", (e) => {
      this.filters.minExergy = parseFloat(e.target.value);
      this.elExergyVal.textContent = this.filters.minExergy.toFixed(1);
      this.applyFilters();
    });

    this.elHeaders.forEach(th => {
      th.addEventListener("click", () => {
        const key = th.getAttribute("data-sort");
        const dir = (this.currentSort.key === key && this.currentSort.direction === "asc") ? "desc" : "asc";
        this.currentSort = { key, direction: dir };
        this.applySorting();
        this.updateSortHeaders();
        this.renderTable();
      });
    });

    this.elDrawerClose.addEventListener("click", () => {
      this.closeDrawer();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        this.closeDrawer();
      }
    });

    // Close drawer clicking outside its container
    document.addEventListener("click", (e) => {
      if (this.elDrawer.classList.contains("open") &&
          !this.elDrawer.contains(e.target) &&
          !this.elTableBody.contains(e.target) &&
          e.target.id !== "drawer-close") {
        this.closeDrawer();
      }
    });
  }

  calculateStats() {
    const total = this.data.length;
    const avg = this.data.reduce((acc, curr) => acc + curr.exergy, 0) / total;
    const active = this.data.filter(item => item.status.includes("Active")).length;
    const tombstoned = this.data.filter(item => item.status.includes("TOMBSTONED")).length;

    this.elTotalCount.textContent = total;
    this.elAvgExergy.textContent = avg.toFixed(2);
    this.elActiveCount.textContent = active;
    this.elTombstonedCount.textContent = tombstoned;
  }

  applyFilters() {
    this.filteredData = this.data.filter(item => {
      const matchSearch = item.name.toLowerCase().includes(this.filters.search) ||
                          item.path.toLowerCase().includes(this.filters.search);
      const matchType = this.filters.type === "All" || item.type === this.filters.type;
      
      let matchStatus = true;
      if (this.filters.status !== "All") {
        if (this.filters.status === "Active") {
          matchStatus = item.status.includes("Active") || item.status.includes("JIT");
        } else if (this.filters.status === "TOMBSTONED") {
          matchStatus = item.status.includes("TOMBSTONED");
        } else if (this.filters.status === "AST") {
          matchStatus = item.status.includes("AST");
        } else if (this.filters.status === "Heuristic") {
          matchStatus = item.status.includes("Heuristic");
        }
      }

      const matchExergy = item.exergy >= this.filters.minExergy && item.exergy <= this.filters.maxExergy;

      return matchSearch && matchType && matchStatus && matchExergy;
    });

    this.applySorting();
    this.renderTable();
  }

  applySorting() {
    const key = this.currentSort.key;
    const dir = this.currentSort.direction === "asc" ? 1 : -1;

    this.filteredData.sort((a, b) => {
      let valA = a[key];
      let valB = b[key];

      if (typeof valA === "string") {
        return valA.localeCompare(valB) * dir;
      }
      return (valA - valB) * dir;
    });
  }

  updateSortHeaders() {
    this.elHeaders.forEach(th => {
      th.classList.remove("sort-asc", "sort-desc");
      if (th.getAttribute("data-sort") === this.currentSort.key) {
        th.classList.add(this.currentSort.direction === "asc" ? "sort-asc" : "sort-desc");
      }
    });
  }

  showDrawer(item) {
    this.selectedItem = item;
    
    let statusClass = "status-active";
    if (item.status.includes("TOMBSTONED")) {
      statusClass = "status-tombstoned";
    } else if (item.status.includes("AST")) {
      statusClass = "status-ast";
    } else if (item.status.includes("Heuristic")) {
      statusClass = "status-heuristic";
    }

    this.elDrawerContent.innerHTML = `
      <div class="drawer-header-meta">
        <span class="drawer-rank">RANK #${item.rank}</span>
        <span class="drawer-type">${item.type.toUpperCase()}</span>
      </div>
      <h2>${item.name}</h2>
      <div class="drawer-path-box">
        <span class="path-label">IDENTIFIER / PATH</span>
        <code>${item.path}</code>
      </div>
      <div class="drawer-metrics">
        <div class="metric-block">
          <span class="metric-label">EXERGY LEVEL</span>
          <span class="metric-val text-yinmn">${item.exergy.toFixed(1)}</span>
        </div>
        <div class="metric-block">
          <span class="metric-label">TELEMETRY STATUS</span>
          <span class="metric-val ${statusClass}">${item.status}</span>
        </div>
      </div>
      <div class="drawer-description-section">
        <h3>Architectural Role</h3>
        <p>${item.description}</p>
      </div>
      <div class="drawer-description-section">
        <h3>Practical Use Case</h3>
        <p class="use-case-text">${item.useCase || "Standard verification pipeline in the CORTEX subsystem execution loop."}</p>
      </div>
    `;

    this.elDrawer.classList.add("open");
  }

  closeDrawer() {
    this.elDrawer.classList.remove("open");
    this.selectedItem = null;
  }

  renderTable() {
    this.elTableBody.innerHTML = "";
    if (this.filteredData.length === 0) {
      this.elTableBody.innerHTML = `
        <tr>
          <td colspan="5" class="no-results">No components match the specified thermodynamic boundaries.</td>
        </tr>
      `;
      return;
    }

    this.filteredData.forEach(item => {
      const tr = document.createElement("tr");
      tr.setAttribute("data-rank", item.rank);
      if (this.selectedItem && this.selectedItem.rank === item.rank) {
        tr.classList.add("active-row");
      }

      let statusBadgeClass = "badge-active";
      if (item.status.includes("TOMBSTONED")) {
        statusBadgeClass = "badge-tombstoned";
      } else if (item.status.includes("AST")) {
        statusBadgeClass = "badge-ast";
      } else if (item.status.includes("Heuristic")) {
        statusBadgeClass = "badge-heuristic";
      }

      tr.innerHTML = `
        <td><span class="rank-badge">${item.rank}</span></td>
        <td>
          <div class="cell-name">${item.name}</div>
          <div class="cell-path">${item.path}</div>
        </td>
        <td><span class="type-tag tag-${item.type.toLowerCase()}">${item.type}</span></td>
        <td><span class="exergy-pill" style="--exergy-val: ${item.exergy}%">${item.exergy.toFixed(1)}</span></td>
        <td><span class="status-badge ${statusBadgeClass}">${item.status}</span></td>
      `;

      tr.addEventListener("click", (e) => {
        // Toggle selected row visual state
        this.elTableBody.querySelectorAll("tr").forEach(r => r.classList.remove("active-row"));
        tr.classList.add("active-row");
        this.showDrawer(item);
        e.stopPropagation();
      });

      this.elTableBody.appendChild(tr);
    });
  }

  render() {
    this.updateSortHeaders();
    this.renderTable();
  }
}
