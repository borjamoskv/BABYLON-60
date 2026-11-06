# BABYLON-60 Harness Profile

This directory provides the canonical profile for **BABYLON-60** in the format consumed by comparative agent-harness frameworks such as [Harness Lens](https://huggingface.co/spaces/ybelkada/harness-lens).

## What is BABYLON-60 in harness-lens terms?

Conventional coding-agent harnesses (OpenHands, SWE-agent, Cline, Claude Code, etc.) operate as **application-level wrappers** over LLM inference APIs. They manage prompting, coordinate context windows, invoke local shell/file tools, and apply prompt-based or sandbox permissions.

In contrast, **BABYLON-60 is an execution authority and effect broker**. It operates on the principle:

$$\operatorname{Capability}(AI)\uparrow \;\not\Rightarrow\; \operatorname{Authority}(AI)\uparrow$$

Higher reasoning capability in an AI agent must not automatically expand its execution privileges within a protected deployment perimeter.

## Profile Architecture Breakdown

| Harness Dimension | Conventional Harnesses | BABYLON-60 Implementation |
|---|---|---|
| **System Prompt** | Single mutable text block passed to the model API | Immutable Ring contracts (`.babylon60rules`, `MOSKV1_UNIVERSAL_PROMPT.md`, `agent_contracts.md`) bound via symlinks |
| **Authority Model** | Prompt instructions ("do not run malicious commands") | Cryptographic environment keys, hardware biometrics, nonces |
| **Tool Set** | Direct shell/file passthrough | Mediated MCP broker (`babylon-skills-mcp`, `GUARD` fail-closed) + C-ABI `SharedManifest` (64 B, align 64) |
| **Compaction Strategy** | Heuristic token trimming, sliding window, ad-hoc summarization | Epistemic apoptosis (`POISONED = 0xDEAD_6060`), LARSA-120 batch amortization, `INV_C5_HUME_GUILLOTINE` |
| **Permissions & Sandboxing** | Terminal `y/n` prompts or ephemeral Docker containers | Multi-ring contracts (Ring-0 to Ring-3), Touch ID Secure Enclave gate (`reuseDuration = 0`), OS process confinement |
| **Evidence & Claims** | None or unverified marketing assertions | Stratified `CLAIMS.toml` (`L1_FORMAL`, `L2_IMPLEMENTATION`, `L3_ISOLATION`, `L4_EXPERIMENTAL`) |

## Evidence and Limitations

All formal and empirical claims are verified against [CLAIMS.toml](../../CLAIMS.toml). Claims exposed in this profile carry strictly `verified` or `verified_local` status under audited test suites.

> [!NOTE]
> BABYLON-60 runs as a user-space broker at EL0 on macOS ARM64. Effective mediation requires OS-level process isolation of the untrusted agent runtime (L3). The broker alone does not prevent unconfined direct writes if an agent is granted raw OS access.
