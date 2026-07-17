# Reverse Engineering Audit: PyCharm 2026.1.4

## Executive Summary
This report documents the reverse engineering findings of `pycharm-2026.1.4-aarch64.dmg`.
PyCharm Professional is JetBrains' IDE dedicated to Python, Web, and Scientific development. Key findings include a built-in MCP server (similar to WebStorm 2026.2) and a specialized **`code-provenance`** plugin linking LLMs, Claude, and Git logic.

---

## 1. Package Metadata & Signatures
- **Application Name**: PyCharm
- **Developer/Publisher**: JetBrains s.r.o.
- **Code Signature Verification**:
  - **Executable**: `PyCharm.app/Contents/MacOS/pycharm`
  - **Bundle Identifier**: `com.jetbrains.pycharm`
  - **Team Identifier**: `2ZEFAR8TH3`
  - **Signing Authority**: `Developer ID Application: JetBrains s.r.o. (2ZEFAR8TH3)`
  - **Notarization Status**: Stapled
  - **Architecture**: arm64 (Mach-O thin executable)

---

## 2. Technology Stack & Launch Configuration
- **Core Engine**: JVM (Java Virtual Machine), compiled with Kotlin and Java.
- **Runtime Environment**: Bundled JetBrains Runtime (JBR), a customized OpenJDK 21 build.
- **JVM Options (`pycharm.vmoptions`)**:
  - Max heap is set to `-Xmx2048m` with initial heap at `-Xms256m` (larger starting heap than WebStorm's `-Xms128m`).
  - Lacks the `-Denable.non.commercial.ai.license=true` flag by default, meaning AI license options are handled standardly via user accounts.

---

## 3. Notable Bundled Plugins
Analysis of the `Contents/plugins/` directory reveals:
- **`mcpserver/`**:
  - Includes the same Kotlin Model Context Protocol SDK (`io.modelcontextprotocol.kotlin.sdk.jar`) and server infrastructure as found in WebStorm 2026.2.
- **`code-provenance/`**:
  - **Purpose**: Deep integration of code origin tracing, attributing files/functions to authors or generation agents.
  - **Libraries**: Bundles dedicated modules:
    - `intellij.code.provenance.core.claude.jar` (Claude API integration)
    - `intellij.code.provenance.core.llm.jar` (General LLM logic)
    - `intellij.code.provenance.core.mcp.jar` (MCP interface integration)
    - `intellij.code.provenance.core.git.jar` (Git-based code history attribution)
- **`dataWrangler-plugin/`**: Integrated pandas/numpy visual inspector and data cleaning tool.
- **`jupyter-plugin/` & `jupyter-py-colab-plugin/`**: Native support for Jupyter notebooks and Google Colab integration.
