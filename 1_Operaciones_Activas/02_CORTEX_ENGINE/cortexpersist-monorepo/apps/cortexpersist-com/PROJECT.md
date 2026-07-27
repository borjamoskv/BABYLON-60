# Project: /maquina-credibilidad

## Architecture
- **Framework**: Astro project.
- **Frontend Stack**: Astro + React components for interactivity.
- **Styling**: Tailwind CSS + Custom CSS following Industrial Noir 2026 (#0A0A0A base, #2B3BE5 blue accents, neon borders, clean typography).
- **Page Route**: `/maquina-credibilidad` (mapped to `src/pages/maquina-credibilidad.astro`).
- **Components Location**: React components under `src/components/` (or matching the project's existing structure).

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | E2E Testing Track | Define feature inventory and write Tiers 1-4 tests | None | DONE |
| 2 | Codebase Exploration | Analyze layout, existing Tailwind styles, and page configs | None | DONE |
| 3 | Narrative & Base Layout | Page routing and complete chapter narrative rendering | M2 | DONE |
| 4 | Pirámide de la Desconfianza | Interactive component showing levels, pricing, functions, mechanics | M3 | DONE |
| 5 | Evolución del Precio | Interactive pricing chart highlighting the Ancla of 2.357€ | M3 | DONE |
| 6 | La Trampa Fiscal | Card layout comparison table (Ley 49/2002 vs iHelp) | M3 | DONE |
| 7 | Creators Network | Network list/visualization of ~65 creators and key figures | M3 | DONE |
| 8 | Page Integration | Add menu links from `/`, `/gurus` & back-to-substrate navigation | M3 | DONE |
| 9 | Verification & Hardening | Run E2E test suites, fix defects, verify with Forensic Auditor | M1, M4, M5, M6, M7, M8 | DONE |

## Interface Contracts
- `/maquina-credibilidad` page must render the complete essay.
- The interactive components must be functional in the browser without crashing.
- Navigation links must correctly route to and from the page.

## Code Layout
- Page: `src/pages/maquina-credibilidad.astro`
- Components: `src/components/` (React components for Pirámide, Price Chart, Trampa Fiscal, Creators Network)
- Data/Content: inline in the components/pages or loaded from dedicated json/md files if cleaner.
