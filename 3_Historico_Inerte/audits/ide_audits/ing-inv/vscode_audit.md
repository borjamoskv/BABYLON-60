<!-- C5-REAL EXERGY CERTIFIED -->

# Reverse Engineering Audit: VSCode (darwin-arm64)

## Executive Summary

This report documents the reverse engineering findings of `VSCode-darwin-arm64.dmg`.
This is a standard Microsoft Visual Studio Code build, serving as a baseline comparison for the Devin fork.

---

## 1. Package Metadata & Signatures

- **Application Name**: Visual Studio Code
- **Developer/Publisher**: Microsoft Corporation
- **Code Signature Verification**:
  - **Executable**: `Visual Studio Code.app/Contents/MacOS/Code`
  - **Bundle Identifier**: `com.microsoft.VSCode`
  - **Team Identifier**: `UBF8T346G9`
  - **Signing Authority**: `Developer ID Application: Microsoft Corporation (UBF8T346G9)`
  - **Notarization Status**: Stapled
  - **Architecture**: arm64 (Mach-O thin executable)

---

## 2. Technology Stack & Layout

- **Core Engine**: Electron (bundled with Chromium v126 / Node.js)
- **App Entry point**: `Contents/Resources/app/out/main.js`
- **Data Folders**:
  - Windows Registry/Local folder: `Code`
  - macOS Data folder: `~/Library/Application Support/Code`

---

## 3. Telemetry, Updates & API Endpoints

- **Update Server**:
  - `https://update.code.visualstudio.com`
- **Telemetry Settings**:
  - `enableTelemetry`: true
  - Telemetry level supports `error` and `usage` logging.
- **Extensions Gallery**:
  - Uses the official Microsoft marketplace: `https://marketplace.visualstudio.com/_apis/public/gallery`
- **Link Protection Trusted Domains**:
  - Pre-whitelists standard Microsoft, GitHub, and login portals (`login.microsoftonline.com`, `github.com`, `vscode.dev`).
