<!-- C5-REAL EXERGY CERTIFIED -->

# Reverse Engineering Audit: WebStorm 2026.2

## Executive Summary

This report documents the reverse engineering findings of `WebStorm-2026.2-aarch64.dmg`.
WebStorm is a commercial JavaScript/TypeScript IDE built on the JetBrains IntelliJ platform. Static analysis shows native macOS Arm64 runtime integration (JetBrains Runtime - JBR) and, notably, a built-in MCP (Model Context Protocol) server.

---

## 1. Package Metadata & Signatures

- **Application Name**: WebStorm
- **Developer/Publisher**: JetBrains s.r.o.
- **Code Signature Verification**:
  - **Executable**: `WebStorm.app/Contents/MacOS/webstorm`
  - **Bundle Identifier**: `com.jetbrains.WebStorm`
  - **Team Identifier**: `2ZEFAR8TH3`
  - **Signing Authority**: `Developer ID Application: JetBrains s.r.o. (2ZEFAR8TH3)`
  - **Notarization Status**: Stapled
  - **Architecture**: arm64 (Mach-O thin executable)

---

## 2. Technology Stack & Launch Configuration

- **Core Engine**: JVM (Java Virtual Machine), compiled with Kotlin and Java.
- **Runtime Environment**: Bundled JetBrains Runtime (JBR), which is a customized OpenJDK build.
- **Boot Classpath / Libraries**: Packages core JARs in `Contents/lib/` and plugins in `Contents/plugins/`.
- **JVM Options (`webstorm.vmoptions`)**:
  - Includes standard heap settings (`-Xms128m`, `-Xmx2048m`).
  - Activates compact object headers (`-XX:+UseCompactObjectHeaders`).
  - **AI License Override**: Includes `-Denable.non.commercial.ai.license=true` as a default JVM argument, enabling JetBrains AI features under non-commercial licenses.

---

## 3. Notable Bundled Plugins

Analysis of the `Contents/plugins/` directory reveals:

- **`mcpserver/`**:
  - **Purpose**: Implements a Model Context Protocol (MCP) server directly inside the IDE.
  - **Libraries**: Contains `io.modelcontextprotocol.kotlin.sdk.jar` (Kotlin SDK for MCP), `ktor-server-sse-jvm.jar` (Server-Sent Events server via Ktor), and `mcpserver.jar`.
  - **Integrations**: Bundles MCP terminal and VCS integrations (`intellij.mcpserver.terminal.jar`, `intellij.mcpserver.vcs.jar`).
- **`platform-acp-plugin/` & `platform-daemon-plugin/`**:
  - Integrations for running local daemon tasks and background services.
- **`qodana/`**: JetBrains' code quality platform plugin.
- **`completionMlRanking/` & `searchEverywhereMl/`**: Machine-learning-based code completion and search relevance ranking.
