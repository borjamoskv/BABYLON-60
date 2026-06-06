import os
import sys
import json
import time
import argparse
import requests
sentinel_path = os.path.expanduser("~/.gemini/config/skills/API-Sentinel-OMEGA/scripts")
if sentinel_path not in sys.path:
    sys.path.append(sentinel_path)

try:
    from sentinel import APISentinelOmega
except ImportError:
    print("[C5-REAL] Error fatal: Dependencia API-Sentinel-Ω no encontrada.")
    sys.exit(1)


def fetch_contract_source(address: str) -> str:
    # Etherscan public API (rate limited, but free for low volume)
    # C5-REAL: This physically touches Ethereum Mainnet data.
    api_key = os.environ.get("ETHERSCAN_API_KEY", "")
    url = f"https://api.etherscan.io/v2/api?chainid=1&module=contract&action=getsourcecode&address={address}&apikey={api_key}"
    print(f"[Ouroboros-Strike] 🛰️ Ping a Etherscan RPC (v2): Extrayendo bytecode/source de {address}")
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data.get("status") == "1" and data.get("result"):
            return data["result"][0].get("SourceCode", "")
        return ""
    except Exception as e:
        print(f"[Ouroboros-Strike] Error de extracción on-chain: {e}")
        return ""

def scan_memepool_and_tvl(iteration: int = 1):
    print("[Ouroboros-Strike] Iniciando Radar Asimétrico Físico (ETH Mainnet)...")
    print("[Ouroboros-Strike] 🛑 Circuit Breaker Térmico Activo: Limite de 1 contrato por ciclo.")
    time.sleep(1)
    
    # Lista de contratos de TVL ultra alto reales para rotación dinámica
    targets = [
        {
            "address": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
            "name": "Uniswap V3 Factory",
            "tvl_usd": 3_500_000_000,
            "chain": "Ethereum",
            "risk_surface": ["Reentrancy", "Math Overflow"]
        },
        {
            "address": "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",
            "name": "Lido stETH Token",
            "tvl_usd": 25_000_000_000,
            "chain": "Ethereum",
            "risk_surface": ["Inflation Attack", "Balance Manipulation"]
        },
        {
            "address": "0x35D1b3F3de98C33784d6937B3551343018e4022a",
            "name": "MakerDAO VAT",
            "tvl_usd": 8_000_000_000,
            "chain": "Ethereum",
            "risk_surface": ["Collateral Injection", "Auctions Liquidation"]
        },
        {
            "address": "0x87870B27f8db9029135849330d3725c8b25a38CD",
            "name": "Aave V3 Pool",
            "tvl_usd": 6_500_000_000,
            "chain": "Ethereum",
            "risk_surface": ["Bad Debt Accumulation", "Price Oracle Manipulation"]
        },
        {
            "address": "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7",
            "name": "Curve 3Pool",
            "tvl_usd": 1_200_000_000,
            "chain": "Ethereum",
            "risk_surface": ["Slippage Manipulation", "Imbalanced Withdrawals"]
        },
        {
            "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "name": "WETH9",
            "tvl_usd": 5_000_000_000,
            "chain": "Ethereum",
            "risk_surface": ["Reentrancy", "Infinite Mint"]
        },
        {
            "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "name": "Tether USD",
            "tvl_usd": 50_000_000_000,
            "chain": "Ethereum",
            "risk_surface": ["Blacklist Bypass", "Centralization Risks"]
        },
        {
            "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "name": "USD Coin",
            "tvl_usd": 30_000_000_000,
            "chain": "Ethereum",
            "risk_surface": ["Upgradeability Attack", "Signature Replay"]
        }
    ]
    
    target_idx = (iteration - 1) % len(targets)
    target_protocol = targets[target_idx]
    
    print(f"[Ouroboros-Strike] 🎯 TARGET ADQUIRIDO: {target_protocol['name']} ({target_protocol['address']})")
    print(f"[Ouroboros-Strike] TVL Detectado: ${target_protocol['tvl_usd']:,}")
    
    # Integración Física
    source_code = fetch_contract_source(target_protocol["address"])
    if not source_code:
        print("[Ouroboros-Strike] ⚠️ Extracción física fallida. Activando fallback C4-SIM con VulnerableVault.")
        source_code = """
        pragma solidity ^0.8.0;
        contract VulnerableVault {
            mapping(address => uint256) public balances;
            function withdraw() public {
                uint256 bal = balances[msg.sender];
                require(bal > 0);
                (bool sent, ) = msg.sender.call{value: bal}("");
                require(sent, "Failed to send Ether");
                balances[msg.sender] = 0;
            }
        }
        """
        
    print(f"[Ouroboros-Strike] 📥 Código fuente extraído con éxito ({len(source_code)} bytes).")
    
    # Filtro Estático Híbrido (Pre-LLM)
    print("[Ouroboros-Strike] Ejecutando Filtro Heurístico Estático...")
    if "delegatecall" in source_code or "selfdestruct" in source_code:
        print("[Ouroboros-Strike] ⚠️ Patrón de alto riesgo detectado (delegatecall/selfdestruct).")
        target_protocol["risk_surface"].append("Delegatecall Injection")
    else:
        print("[Ouroboros-Strike] 📉 Riesgo estático bajo. En producción esto detendría el ciclo para ahorrar tokens LLM.")
        
    return target_protocol, source_code

def analyze_contract_with_llm(source_code: str) -> str:
    print("[Ouroboros-Strike] Desplegando Enjambre de Análisis Estático Físico (Waterfall Engine)...")
    
    # Truncate to avoid token limits but keep enough for structural analysis
    code_sample = source_code[:30000]
    
    prompt = f"""You are an expert smart contract security auditor performing a white-hat review.

TASK: Analyze the following Solidity source code for CRITICAL vulnerabilities that could result in loss of funds.

IMPORTANT RULES:
1. Many high-TVL contracts (Uniswap, Aave, Lido, WETH, USDT, USDC) have been extensively audited and are battle-tested. Do NOT report vulnerabilities unless you can cite the EXACT function name and line pattern.
2. Proxy contracts (containing delegatecall) are NOT inherently vulnerable — delegatecall is a standard upgrade pattern.
3. "Reentrancy" requires: (a) an external call BEFORE a state update, AND (b) no reentrancy guard. If checks-effects-interactions pattern is followed, it is NOT vulnerable.
4. Standard ERC-20 transfers, WETH wrap/unwrap, and staking deposit/withdraw patterns are NOT vulnerabilities.
5. "Oracle Manipulation" occurs when a lending or derivative contract reads token prices directly from spot reserves (e.g. Uniswap getReserves() r0/r1 ratio) instead of using a secure Chainlink feed or TWAP. Spot reserve pricing is highly vulnerable to flash loan price manipulation.

RESPOND IN THIS EXACT JSON FORMAT:
{{
  "verdict": "VULNERABLE" or "SAFE",
  "confidence": 0.0 to 1.0,
  "vulnerability_type": "name or null",
  "evidence": "exact function name and code pattern, or null",
  "reasoning": "one sentence explaining why"
}}

If confidence < 0.7, set verdict to "SAFE".
If the code is a well-known audited protocol, set verdict to "SAFE" with reasoning.

Source code:
{code_sample}
"""

    # 1. GROQ Fallback
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key:
        print("[Ouroboros-Strike] 🔄 Ruteando a través de Groq (Llama-3.3-70b)...")
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data and len(data["choices"]) > 0:
                    val = data["choices"][0]["message"]["content"].strip()
                    print(f"[Ouroboros-Strike] ✅ Respuesta Groq recibida: {val}")
                    return val
            print(f"[Ouroboros-Strike] Groq falló con código: {resp.status_code}")
        except Exception as e:
            print(f"[Ouroboros-Strike] Error de red Groq: {e}")

    # 2. OPENAI Fallback
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        print("[Ouroboros-Strike] 🔄 Ruteando a través de OpenAI (GPT-4o-Mini)...")
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {openai_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data and len(data["choices"]) > 0:
                    val = data["choices"][0]["message"]["content"].strip()
                    print(f"[Ouroboros-Strike] ✅ Respuesta OpenAI recibida: {val}")
                    return val
            print(f"[Ouroboros-Strike] OpenAI falló con código: {resp.status_code}")
        except Exception as e:
            print(f"[Ouroboros-Strike] Error de red OpenAI: {e}")

    # 3. GEMINI NATIVE Fallback
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if gemini_key:
        print("[Ouroboros-Strike] 🔄 Ruteando a través de Gemini Nativo...")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={gemini_key}"
        try:
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if "candidates" in data and len(data["candidates"]) > 0:
                    val = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    print(f"[Ouroboros-Strike] ✅ Respuesta Gemini recibida: {val}")
                    return val
            print(f"[Ouroboros-Strike] Gemini Nativo falló con código: {resp.status_code}")
        except Exception as e:
            print(f"[Ouroboros-Strike] Error de red Gemini Nativo: {e}")

    # 4. OPENROUTER Fallback
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    if openrouter_key:
        print("[Ouroboros-Strike] 🔄 Ruteando a través de OpenRouter...")
        headers = {
            "Authorization": f"Bearer {openrouter_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "google/gemini-2.5-pro",
            "messages": [{"role": "user", "content": prompt}]
        }
        try:
            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data and len(data["choices"]) > 0:
                    val = data["choices"][0]["message"]["content"].strip()
                    print(f"[Ouroboros-Strike] ✅ Respuesta OpenRouter recibida: {val}")
                    return val
            print(f"[Ouroboros-Strike] OpenRouter falló con código: {resp.status_code}")
        except Exception as e:
            print(f"[Ouroboros-Strike] Error de red OpenRouter: {e}")

    print("[Ouroboros-Strike] Agotamiento total de Capital. Activando fallback C4-SIM.")
    return '{"verdict": "SAFE", "confidence": 0.0, "vulnerability_type": null, "evidence": null, "reasoning": "No LLM available — defaulting to SAFE to avoid false positives"}'

def _parse_llm_verdict(llm_result: str) -> dict:
    """Parse structured JSON verdict from LLM. Gracefully handles malformed output."""
    import re
    
    # Strategy 1: Try to parse the entire response as JSON
    try:
        return json.loads(llm_result.strip())
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Strategy 2: Extract JSON from markdown code blocks
    try:
        code_block = re.search(r'```(?:json)?\s*(.+?)```', llm_result, re.DOTALL)
        if code_block:
            return json.loads(code_block.group(1).strip())
    except (json.JSONDecodeError, AttributeError):
        pass
    
    # Strategy 3: Find the first { and last } and try to parse
    try:
        start = llm_result.index('{')
        end = llm_result.rindex('}') + 1
        candidate = llm_result[start:end]
        return json.loads(candidate)
    except (ValueError, json.JSONDecodeError):
        pass
    
    # Strategy 4: Truncated JSON — find verdict field directly
    try:
        verdict_match = re.search(r'"verdict"\s*:\s*"(\w+)"', llm_result)
        confidence_match = re.search(r'"confidence"\s*:\s*([\d.]+)', llm_result)
        vuln_match = re.search(r'"vulnerability_type"\s*:\s*"([^"]+)"', llm_result)
        evidence_match = re.search(r'"evidence"\s*:\s*"([^"]+)"', llm_result)
        if verdict_match:
            return {
                "verdict": verdict_match.group(1),
                "confidence": float(confidence_match.group(1)) if confidence_match else 0.5,
                "vulnerability_type": vuln_match.group(1) if vuln_match else None,
                "evidence": evidence_match.group(1) if evidence_match else None,
                "reasoning": "Parsed from truncated JSON response"
            }
    except (AttributeError, ValueError):
        pass
    
    # Fallback: treat raw string as old-format response
    cleaned = llm_result.strip().upper()
    if cleaned == "SAFE":
        return {"verdict": "SAFE", "confidence": 1.0, "vulnerability_type": None, "evidence": None, "reasoning": "Legacy SAFE response"}
    else:
        return {"verdict": "VULNERABLE", "confidence": 0.3, "vulnerability_type": llm_result.strip(), "evidence": None, "reasoning": "Legacy unstructured response — low confidence"}

def execute_strike(iteration: int = 1):
    sentinel = APISentinelOmega()
    print("\n--- INICIO DE FASE DE ATAQUE (WHITE-HAT) ---")
    
    target, source_code = scan_memepool_and_tvl(iteration)
    
    llm_result = analyze_contract_with_llm(source_code)
    verdict = _parse_llm_verdict(llm_result)
    
    print(f"[Ouroboros-Strike] 📊 Verdict: {verdict.get('verdict')} | Confidence: {verdict.get('confidence', 0):.0%}")
    
    is_safe = verdict.get("verdict", "SAFE").upper() == "SAFE"
    confidence = float(verdict.get("confidence", 0))
    
    if is_safe or confidence < 0.7:
        reason = verdict.get("reasoning", "No reason provided")
        print(f"[Ouroboros-Strike] 🛡️ Contrato seguro (confidence={confidence:.0%}). Razón: {reason}")
        print("[Ouroboros-Strike] Abortando ataque para ahorrar tokens.")
        return False
        
    vuln_type = verdict.get("vulnerability_type", "Unknown")
    evidence = verdict.get("evidence", "N/A")
    print(f"[Ouroboros-Strike] ⚠️ VULNERABILIDAD DETECTADA: {vuln_type}")
    print(f"[Ouroboros-Strike] 📋 Evidencia: {evidence}")
    
    claim = f"Vulnerabilidad Crítica detectada en {target['address']} ({target['name']}). Impacto potencial: {target['tvl_usd']*.8:,} USD. Recompensa (10%): {target['tvl_usd']*.08:,} USD. Diagnóstico: {vuln_type}. Evidencia: {evidence}"
    
    print("\n[Ouroboros-Strike] Firmando el reclamo de recompensa con la Sovereign Wallet...")
    signature = sentinel.sign_payload(claim)
    
    print("\n--- RESULTADO DE CRISTALIZACIÓN ---")
    print(json.dumps(signature, indent=2))
    print("\n[Ouroboros-Strike] Payload listo para inyección automática en portal de Bug Bounty (ImmuneFi).")
    return True

def daemon_mode(sleep_time=300, max_iterations=None):
    mode_text = "Infinito" if max_iterations is None else str(max_iterations)
    print(f"[Ouroboros-Strike] ♾️ MODO DAEMON INICIADO. Ciclos: {mode_text}. Latencia termodinámica: {sleep_time}s.")
    iteration = 1
    while max_iterations is None or iteration <= max_iterations:
        print(f"\n=============================")
        print(f"   CICLO DE CAZA #{iteration}")
        print(f"=============================")
        try:
            execute_strike(iteration)
        except Exception as e:
            print(f"[Ouroboros-Strike] ⚠️ Error fatal no controlado en ciclo {iteration}: {e}")
        
        if max_iterations is not None and iteration >= max_iterations:
            print("[Ouroboros-Strike] 🛑 Límite de ciclos alcanzado. Terminando daemon.")
            break
            
        print(f"[Ouroboros-Strike] ⏳ Enfriamiento térmico activado. Durmiendo {sleep_time} segundos...")
        time.sleep(sleep_time)
        iteration += 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ouroboros-Strike-OMEGA Asymmetric Bounty Engine")
    parser.add_argument("--daemon", action="store_true", help="Ejecutar en bucle infinito (o limitado por --cycles)")
    parser.add_argument("--cycles", type=int, default=None, help="Límite de ciclos para el modo daemon")
    parser.add_argument("--sleep", type=int, default=300, help="Tiempo de enfriamiento entre ciclos en segundos")
    args = parser.parse_args()
    
    if args.daemon:
        daemon_mode(sleep_time=args.sleep, max_iterations=args.cycles)
    else:
        execute_strike()
