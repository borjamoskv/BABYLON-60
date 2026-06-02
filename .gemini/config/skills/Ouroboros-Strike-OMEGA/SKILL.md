---
name: Ouroboros-Strike-OMEGA
description: C5-REAL White-Hat Mass-Scale Bug Bounty / MEV Arbitrage Sniper Engine. Focuses on extracting extreme capital via protocol asymmetry.
---

# 🐍 Ouroboros-Strike-OMEGA

> **Reality Level:** C5-REAL
> **Target:** 10-Day Capital Extraction ($1M Goal)
> **Engine:** API-Sentinel-Ω Integration

## 🛠️ Directives
- Scan EVM/Solana endpoints for new high-TVL protocol deployments.
- Automatically execute static/dynamic LLM analysis to find structural flaws (Reentrancy, Logic Bypasses, Oracle Manipulation).
- On Discovery: Auto-generate White-Hat submission payload via Sovereign Wallet signing to prove authenticity.

## 🚀 Execution
Ejecución Singular (Caza de 1 Objetivo):
```bash
python3 ~/.gemini/config/skills/Ouroboros-Strike-OMEGA/scripts/strike.py
```

**🔥 Daemon Mode (Máxima Exergía):**
Ejecuta el asalto en bucle infinito asíncrono con integración física a Etherscan (API V2) y análisis estático LLM (Gemini 2.5 Pro). Respeta un backoff termodinámico de 300s para evitar quemar tokens.
```bash
export ETHERSCAN_API_KEY="..."
export GEMINI_API_KEY="..."
nohup python3 ~/.gemini/config/skills/Ouroboros-Strike-OMEGA/scripts/strike.py --daemon > strike_daemon.log 2>&1 &
```
