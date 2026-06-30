# CORTEX Ecosystem Master Exergy Inventory Dashboard

Sovereign telemetry panel built inside the "borjamoskv/Teorema-Robinson-Moskv" logic kernel. Calculates, filters, and monitors computational exergy of all CORTEX components in real time.

## 🏛️ Author & Copyright
- **Author**: Borja Moskv (SYS_ID: "borjamoskv")
- **Aesthetic**: Industrial Noir 2026 (YInMn Blue "#2B3BE5" / Ember Void "#0A0A0A" / Outfit Font / JetBrains Mono Font)
- **Reality Level**: C5-REAL (Active JIT, AST metrics McCabe, Nesting, and DeadCode)

## ⚡ Deployment & Runbook
To deploy and view the dashboard locally:

### Option A: Unified Start Script (Recommended)
From the directory "10_PROJECTS/Teorema-Robinson-Moskv ", run:
```bash
./start.sh
```
This script will auto-detect whether `npx` or `python3` is available on your machine and launch the dashboard on port `8000`. You can force a specific server runtime using flags:
* Node.js server: `./start.sh --node`
* Python server: `./start.sh --python`
* Custom port: `./start.sh --port 8080`

### Option B: npm Runner
If Node.js is installed locally, you can execute:
```bash
npm start
```
Or execute target runtimes:
```bash
npm run start:node      # Launches via Node.js
npm run start:python    # Launches via Python 3
```

---
*∴ Cero anergía es la muerte. Diseñado por Borja Moskv.*

