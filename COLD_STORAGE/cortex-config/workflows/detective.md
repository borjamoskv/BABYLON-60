---
description: "The Detective v2 — Deep Code Analysis and Tech Debt Hunting"
workflow: detective
expected_duration_min: 15
---
# 🕵️ DETECTIVE-Ω (Code Forensics)

## 1. Step 1: Evidence Scan
- **Structure**: `find` recursion (MaxDepth 5).
- **Surface**: `wc -l` (LOC per extension), `sort -rn` (Max size).
- **Alarm**: `grep -rcn` (Cyclomatic Complexity), `TODO/FIXME/HACK`.

## 2. Step 2: Interrogation (8 Dimensions)
| # | Vector | Criticality |
|---|---|---|
| 1 | **God Objects** | 🔴 (>500 LOC/10+ methods) |
| 2 | **Circulars** | 🔴 (A→B→A) |
| 3 | **Dead Code** | 🟡 (Unused imports/funcs) |
| 4 | **Copy-Paste** | 🟡 (Duplicity > 10 lines) |
| 5 | **Security** | 🔴 (Hardcoded secrets/SSRF) |
| 6 | **Error Handling** | 🟡 (Empty `catch/except`) |
| 7 | **Naming** | 🟢 (Confusing symbols) |
| 8 | **Perf** | 🟠 (O(n²) loops/leaks) |

## 3. Step 3: Heatmap & Report
- **Generate**: `FORENSIC_REPORT.md`.
- **Sprint 1**: Quick Wins (1-2h).
- **Sprint 2**: Medium Refactors.
- **Sprint 3**: Deep logic overhaul.

## 4. Step 4: Auto-Fix Express
- **Safe**: Unused imports, `alt` tags, `const/let` conversion.
- **Aggressive**: Empty `except` patching, `console.log` purge.

## 5. Usage
- `/detective [path | ecosystem.active_focus]`