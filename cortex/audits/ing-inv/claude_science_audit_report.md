# Audit Report: Claude Science (com.anthropic.operon)

## Executive Summary
```yaml
Audit_Target: Claude Science.app (mac-arm64.dmg)
Audit_Date: 2026-07-17T20:04:19+02:00
Bundle_Identifier: com.anthropic.operon
Internal_Codename: Operon
Version: 0.1.18-dev.20260709.t211149.shab3f5130
Minimum_OS: macOS 13.0 (Ventura)
Status: Verified (Clean App Bundle Structure)
```

---

## 1. Property List (`Info.plist`) Analysis

The extracted properties from `/Contents/Info.plist` are as follows:

| Key | Value | Description |
| :--- | :--- | :--- |
| `CFBundleDisplayName` | `Claude Science` | Display name of the application in Finder and UI. |
| `CFBundleName` | `Claude Science` | Internal short name of the bundle. |
| `CFBundleExecutable` | `ClaudeScience` | Name of the main executable binary under `Contents/MacOS/`. |
| `CFBundleIdentifier` | `com.anthropic.operon` | Unique bundle identifier (uses codename `operon`). |
| `CFBundleIconFile` | `operon` | Name of the icon file in the resources folder (maps to `operon.icns`). |
| `CFBundleShortVersionString` | `0.1.18-dev.20260709.t211149.shab3f5130` | User-visible release version. |
| `CFBundleVersion` | `0.1.18-dev.20260709.t211149.shab3f5130` | Build version number. |
| `CFBundlePackageType` | `APPL` | Identifies the bundle type as a standard macOS Application. |
| `LSMinimumSystemVersion` | `13.0` | Requires Apple Silicon running macOS Ventura or newer. |
| `NSHighResolutionCapable` | `true` | Supports Retina and high-DPI displays. |

---

## 2. Resource Directory & Bundle File Structure

The `.app` bundle maintains a compact footprint with the following hierarchy:

```
Claude Science.app/
└── Contents/
    ├── Info.plist
    ├── _CodeSignature/
    │   └── CodeResources
    ├── MacOS/
    │   └── ClaudeScience
    └── Resources/
        ├── operon.icns
        └── bin/
            └── claude-science
```

### Components Walkthrough:
1. **`Contents/_CodeSignature/CodeResources`**: Contains hashes and metadata for validation of the application's digital signature.
2. **`Contents/MacOS/ClaudeScience`**: The primary Mach-O executable launched when starting the `.app` bundle.
3. **`Contents/Resources/operon.icns`**: Contains multi-resolution icon assets using the internal codename `operon`.
4. **`Contents/Resources/bin/claude-science`**: A CLI entrypoint or helper binary bundled within resources.

---

## 3. Conclusions & Recommendations
- **Platform Conformity**: The bundle strictly targets `mac-arm64` systems (macOS 13.0+ minimum).
- **Naming Invariant**: The codebase identifier (`com.anthropic.operon`), executable icon file name, and helper path points to the codename **Operon**, indicating this app package corresponds to Anthropic's Operon research/science runtime suite.
- **Resource Footprint**: Minimalist bundle structure without bulky media assets or embedded frameworks, indicating a slim native runner wrapper around core logic.
