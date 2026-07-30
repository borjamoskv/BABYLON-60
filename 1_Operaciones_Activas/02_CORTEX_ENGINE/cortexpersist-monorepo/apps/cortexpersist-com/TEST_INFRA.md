# CORTEX-Persist Test Infrastructure Specification

**Reality Level**: C5-REAL (verifiable configuration and run instructions)

---

## 1. Test Philosophy: Opaque-Box & Requirement-Driven

The E2E testing framework for the CORTEX-Persist substrate follows a strict **Opaque-Box** philosophy:
- We test static build outputs compiled via `npm run build` into `dist/`.
- We make zero assumptions about React's internal state variables or custom rendering life cycles. Instead, we inspect the produced DOM structures, attribute nodes, styling declarations, and semantic markup to confirm compliance with system requirements.
- Tests are **Requirement-Driven**: every test case directly addresses a feature requirement (such as pricing anchors, table headers, SEO metadata, reading times, or Spanish text validity).

---

## 2. Feature Inventory

The substrate implements six core features, mapped to specific requirements and validation targets:

| Feature ID | Feature Name | Description / Requirement | Target / Elements |
|:---|:---|:---|:---|
| **F1** | Essay Narrative & Chapters | Spanish essay content detailing the Substack Mafia mechanics. Structurally divided into chapters with unique anchor IDs. | Title containing "La Máquina de la Credibilidad", `h1` header, >= 5 sections/headings, >= 15,000 text characters, Spanish accent validity (no encoding bugs), reading time calculations. |
| **F2** | La Pirámide de la Desconfianza | Segmented interactive pyramid showcasing four tiers of aggressive extraction. | `#piramide-desconfianza` container, 4 distinct tiers (Cebo, Membresía, Bootcamp, Círculo Interno), active tier detail displays (`#piramide-details`), price tags (0€, 10€, 300€, 3.000€), aria accessibility parameters. |
| **F3** | Price Evolution Chart | Line/scatter chart depicting price inflation timeline from July '25 to March '26. | `#precio-evolution-chart` SVG elements, "2.357€" VIP price anchor highlighted, 9 coordinate data points, timeline labels, interactive tooltip container. |
| **F4** | La Trampa Fiscal | Card-grid or table comparing standard subscriptions vs. iHelp campaigns under Ley 49/2002. | `#trampa-fiscal-table`, column headers for "Ley 49/2002" and "iHelp", variables for Deductions (80%), VAT (21% vs 0%), and net cost (50€ vs 250€), warning styling classes, missing value fallbacks. |
| **F5** | Creators Network | Ecosistema count showing mutual recommendation loop. | `#creators-network`, badge with count "65" or "65+", names "Samuel" and "Jorge Bosch", search inputs, filter controls, zero-results templates. |
| **F6** | Substrate Integration & Navigation | Bidirectional cross-links and relative routing layouts. | Relative anchor tag linking to `/` and `/gurus`, index.html linking to `/maquina-credibilidad`, gurus/index.html linking to `/maquina-credibilidad`, page header active styled elements, target security controls. |

---

## 3. Test Architecture

The E2E test suite executes using a custom, process-less static runner:

```
+------------------+     npm run build      +---------------------+
|  Astro Pages /   | =====================> |   Static Build in   |
| React Components |                        |       dist/         |
+------------------+                        +---------------------+
                                                       ||
                                                       || Read files
                                                       \/
+------------------+     Run assertions     +---------------------+
| Test Report &    | <===================== |  JSDOM DOM Parser   |
| non-zero Exit    |                        |  (tests/run-e2e.js) |
+------------------+                        +---------------------+
```

### Dependencies
- **Node.js**: Native filesystem module (`node:fs`) and path resolver (`node:path`).
- **JSDOM**: Simulates a full, headless browser environment by parsing raw HTML strings into standard document objects.

### Commands to Execute
- **Run the E2E suite directly**:
  ```bash
  node tests/run-e2e.js
  ```
- **Run via npm wrapper**:
  ```bash
  npm run test:e2e
  ```

---

## 4. Real-World Application Scenarios (Tier 4)

We validate user journeys using five scenario chains simulating target browser execution:

1. **The Investigator Journey**: Simulates a user landing on the home page (`/`), navigating via menu links to `/maquina-credibilidad`, scrolling down, and inspecting the pyramid's base level. Verified by asserting that home routing tags exist, the page title resolves, and the default active detail panel contains the free tier specifications.
2. **The Auditor Journey**: Simulates a regulatory agent auditing fiscal statements. Accesses the page directly and scrolls to the "La Trampa Fiscal" comparison. Verified by asserting that Ley 49/2002 calculations (such as "80%" tax deductions and "+21.0% exención") are explicitly present in the comparison text.
3. **The Researcher Journey**: Simulates a journalist researching creator affiliations. Focuses search inputs on the network container and filters by name. Verified by asserting that input tags are present and the dataset correctly exposes key coordinators like "Samuel" and "Jorge Bosch".
4. **The Financial Forensics Journey**: Simulates an analyst auditing price progression timelines. Hovers over the price nodes. Verified by asserting that the SVG coordinate layout highlights the 2.357€ VIP membership marker and details pricing deviation.
5. **The Telemetry Audit Trace**: Simulates verifying cryptographic persistence. Interacts with the components and checks the ledger log. Verified by asserting that telemetry container widgets exist and are bound to log interactive UI states.

---

## 5. Coverage Thresholds

To seal build quality, tests are categorized into 4 tiers with the following compliance targets:

- **Tier 1: Feature Coverage**
  - Minimum 5 test cases per feature (across 6 features) = **30 test cases**
- **Tier 2: Boundary & Corner Cases**
  - Minimum 5 test cases per feature (across 6 features) = **30 test cases**
- **Tier 3: Cross-Feature Combinations**
  - Minimum **6 test cases** checking pairwise module interactions.
- **Tier 4: Real-World Scenarios**
  - Minimum **5 test cases** verifying real-world client journeys.

**Grand Total Coverage Target**: **71 test cases** (All 71 implemented in `tests/run-e2e.js`).
