# Reverse Engineering Audit: Devin (darwin-arm64-3.4.27)

## Executive Summary
This report documents the reverse engineering findings of `Devin-darwin-arm64-3.4.27.dmg`.
Our static analysis reveals that this distribution of Devin is built on top of **Codeium Windsurf** (version 3.4.27 / VS Code base version 1.110.1), rather than being a fully custom standalone native IDE. It integrates custom extensions, custom schema definitions, and packages a native CLI helper.

---

## 1. Package Metadata & Signatures
- **Application Name**: Devin (represented internally in `product.json` as `devin-desktop`)
- **Developer/Publisher**: Exafunction, Inc.
- **Code Signature Verification**:
  - **Executable**: `Devin.app/Contents/MacOS/Devin`
  - **Bundle Identifier**: `com.exafunction.windsurf` (Note: Inherits Windsurf's original Bundle ID)
  - **Team Identifier**: `83Z2LHX6XW`
  - **Signing Authority**: `Developer ID Application: EXAFUNCTION, INC. (83Z2LHX6XW)`
  - **Notarization Status**: Stapled
  - **Architecture**: arm64 (Mach-O thin executable)

---

## 2. Technology Stack & Core Layout
The application is packaged as an Electron bundle following the typical VS Code distribution layout:
- **Core Engine**: Electron/NodeJS (bundled with Chromium v126)
- **App Entry point**: `Contents/Resources/app/out/main.js`
- **Dependency base**: Copied directly from the Windsurf repository with custom overrides in `product.json` and `package.json`.
- **System Folders**:
  - Data Directory: `~/.devin`
  - Server Data Directory: `~/.devin-server`
  - Tunnel Application: `devin-tunnel`

---

## 3. Bundled Extensions and Custom Features
Within `Contents/Resources/app/extensions`, standard VS Code extensions are present, along with customized elements:
- **`windsurf/` Extension**: Handles the primary connection to Codeium/Exafunction services, triggering the Cascade agent panel, microphone dictation, and local workspaces.
- **`prompt-basics/` Extension**:
  - Registers custom editor files: `.prompt.md`, `copilot-instructions.md`, `.instructions.md`, `.agent.md`, `.chatmode.md`, and `SKILL.md`.
  - Configures default editor rules for these extensions to suppress quick suggestions and handle word-wrap for prompt engineering workflows.
- **`mermaid-chat-features/` Extension**:
  - Contains tool registration `renderMermaidDiagram` to render diagrams from AI chat output.
  - Contains Azure Application Insights telemetry instrumentation key: `0c6ae279ed8443289764825290e4f9e2-1a736e7c-1324-4338-be46-fc2a58ae4d14-7255`.
- **`theme-2026/`**: Modern neutral minimal light and dark themes.

---

## 4. Bundled Daemons and Native Binaries
Under `Contents/Resources/app/extensions/windsurf/devin/bin`, the package includes a compiled native executable:
- **Path**: `extensions/windsurf/devin/bin/devin`
- **File Type**: Mach-O 64-bit executable arm64
- **Purpose**: Serves as the Devin local Agent CLI, allowing external processes to interface with local system APIs and relay workspace state back to the agent coordinator.

---

## 5. Telemetry, Analytics, and API Endpoints
During binary and JS bundle analysis, the following hostnames and API endpoints were identified:
- **Devin Backend/Portal**:
  - `https://app.devin.ai`
  - `https://app.beta.devin.ai`
  - `https://staging.itsdev.in`
  - `https://*.devinenterprise.com`
  - `https://beta.devinenterprise.com`
- **Agent/Cascade Debugging**:
  - `https://cascadeplayground.watchdevinwork.com/cascade_query/...`
  - `https://exafunction.retool.com/apps/b9412a18-63c8-11ef-8e93-573ca9cceee4/Supercomplete%20Inspect` (Internal tool for debugging/auditing completion logs)
- **Codeium Services**:
  - `https://server.codeium.com`
  - `https://server-staging.codeium.com`
  - `https://inference.codeium.com`
  - `https://unleash.codeium.com/api/` (Feature flags manager)
  - `https://marketplace.windsurf.com` (Extension gallery)
  - `https://update.windsurf.com` & `https://windsurf-stable.codeium.com`
  - `https://eu.windsurf.com` & `https://windsurf.fedstart.com`
