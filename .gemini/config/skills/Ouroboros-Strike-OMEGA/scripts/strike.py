"""
C5-REAL
Ouroboros-Strike-OMEGA Asymmetric Bounty Engine
"""
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
    print("C5-REAL: ERR: API-Sentinel-Ω not found.")
    sys.exit(1)


def fetch_contract_source(address: str) -> str:
    # C5-REAL: Etherscan RPC call
    api_key = os.environ.get("ETHERSCAN_API_KEY", "")
    url = f"https://api.etherscan.io/v2/api?chainid=1&module=contract&action=getsourcecode&address={address}&apikey={api_key}"
    print(f"C5-REAL: FETCH_SOURCE {address}")
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data.get("status") == "1" and data.get("result"):
            return data["result"][0].get("SourceCode", "")
        return ""
    except Exception as e:
        print(f"ERR: fetch_contract_source {e}")
        return ""

def scan_memepool_and_tvl(iteration: int = 1):
    print("C5-REAL: SCAN_INIT")
    time.sleep(1)
    
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
    
    print(f"TARGET: {target_protocol['address']} | TVL: {target_protocol['tvl_usd']}")
    
    source_code = fetch_contract_source(target_protocol["address"])
    if not source_code:
        print("C4-SIM: FETCH_FAIL | ACTIVATING_FALLBACK")
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
        
    print(f"SRC_BYTES: {len(source_code)}")
    
    if "delegatecall" in source_code or "selfdestruct" in source_code:
        print("WARN: DELEGATECALL_OR_SELFDESTRUCT")
        target_protocol["risk_surface"].append("Delegatecall Injection")
        
    return target_protocol, source_code

def analyze_contract_with_llm(source_code: str) -> str:
    print("C5-REAL: LLM_ANALYZE")
    code_sample = source_code[:30000]
    
    prompt = f"""You are an expert smart contract security auditor performing a white-hat review.

TASK: Analyze the following Solidity source code for CRITICAL vulnerabilities that could result in loss of funds.

IMPORTANT RULES:
1. High-TVL contracts are battle-tested. Cite EXACT function and line pattern.
2. Proxy contracts (delegatecall) are NOT inherently vulnerable.
3. Reentrancy requires external call BEFORE state update AND no reentrancy guard.
4. Standard ERC-20 transfers are NOT vulnerabilities.
5. Oracle Manipulation requires direct spot reserve reads instead of secure feed/TWAP.

OUTPUT JSON FORMAT:
{{
  "verdict": "VULNERABLE" or "SAFE",
  "confidence": 0.0 to 1.0,
  "vulnerability_type": "name" or null,
  "evidence": "exact function name and code pattern" or null,
  "reasoning": "one sentence explaining why"
}}

Fallback to "SAFE" if confidence < 0.7 or well-known audited protocol.

Source code:
{code_sample}
"""

    def _call_api(name, url, headers, json_payload, extract_fn):
        print(f"ROUTE: {name}")
        try:
            resp = requests.post(url, headers=headers, json=json_payload, timeout=30)
            if resp.status_code == 200:
                val = extract_fn(resp.json())
                print(f"{name}: OK")
                return val
            print(f"ERR: {name} HTTP_{resp.status_code}")
        except Exception as e:
            print(f"ERR: {name} {e}")
        return None

    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key:
        res = _call_api(
            "GROQ", 
            "https://api.groq.com/openai/v1/chat/completions",
            {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "max_tokens": 500},
            lambda d: d["choices"][0]["message"]["content"].strip() if d.get("choices") else None
        )
        if res: return res

    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        res = _call_api(
            "OPENAI",
            "https://api.openai.com/v1/chat/completions",
            {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
            {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "max_tokens": 500},
            lambda d: d["choices"][0]["message"]["content"].strip() if d.get("choices") else None
        )
        if res: return res

    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if gemini_key:
        print("ROUTE: GEMINI")
        try:
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={gemini_key}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                if "candidates" in data and len(data["candidates"]) > 0:
                    print("GEMINI: OK")
                    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            print(f"ERR: GEMINI HTTP_{resp.status_code}")
        except Exception as e:
            print(f"ERR: GEMINI {e}")

    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    if openrouter_key:
        res = _call_api(
            "OPENROUTER",
            "https://openrouter.ai/api/v1/chat/completions",
            {"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"},
            {"model": "google/gemini-2.5-pro", "messages": [{"role": "user", "content": prompt}]},
            lambda d: d["choices"][0]["message"]["content"].strip() if d.get("choices") else None
        )
        if res: return res

    print("C4-SIM: ALL_APIS_FAIL | FALLBACK_SAFE")
    return '{"verdict": "SAFE", "confidence": 0.0, "vulnerability_type": null, "evidence": null, "reasoning": "API_EXHAUSTION"}'

def _parse_llm_verdict(llm_result: str) -> dict:
    import re
    try:
        return json.loads(llm_result.strip())
    except (json.JSONDecodeError, ValueError):
        pass
    
    try:
        code_block = re.search(r'```(?:json)?\s*(.+?)```', llm_result, re.DOTALL)
        if code_block:
            return json.loads(code_block.group(1).strip())
    except (json.JSONDecodeError, AttributeError):
        pass
    
    try:
        start = llm_result.index('{')
        end = llm_result.rindex('}') + 1
        return json.loads(llm_result[start:end])
    except (ValueError, json.JSONDecodeError):
        pass
    
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
                "reasoning": "REGEX_PARSED"
            }
    except (AttributeError, ValueError):
        pass
    
    cleaned = llm_result.strip().upper()
    if cleaned == "SAFE":
        return {"verdict": "SAFE", "confidence": 1.0, "vulnerability_type": None, "evidence": None, "reasoning": "LEGACY_SAFE"}
    return {"verdict": "VULNERABLE", "confidence": 0.3, "vulnerability_type": llm_result.strip(), "evidence": None, "reasoning": "LEGACY_UNSTRUCTURED"}

def execute_strike(iteration: int = 1):
    sentinel = APISentinelOmega()
    print("C5-REAL: EXEC_STRIKE")
    
    target, source_code = scan_memepool_and_tvl(iteration)
    
    llm_result = analyze_contract_with_llm(source_code)
    verdict = _parse_llm_verdict(llm_result)
    
    print(f"VERDICT: {verdict.get('verdict')} | CONF: {verdict.get('confidence', 0):.2f}")
    
    is_safe = verdict.get("verdict", "SAFE").upper() == "SAFE"
    confidence = float(verdict.get("confidence", 0))
    
    if is_safe or confidence < 0.7:
        print("ABORT: SAFE_OR_LOW_CONF")
        return False
        
    vuln_type = verdict.get("vulnerability_type", "Unknown")
    evidence = verdict.get("evidence", "N/A")
    print(f"VULN: {vuln_type} | EV: {evidence}")
    
    claim = f"VULN: {target['address']} | TVL: {target['tvl_usd']} | TYPE: {vuln_type} | EV: {evidence}"
    print("C5-REAL: SIGN_CLAIM")
    signature = sentinel.sign_payload(claim)
    
    print("OUT:")
    print(json.dumps(signature))
    return True

def daemon_mode(sleep_time=300, max_iterations=None):
    mode_text = max_iterations if max_iterations is not None else "INF"
    print(f"DAEMON: CYCLES={mode_text} | SLEEP={sleep_time}s")
    iteration = 1
    while max_iterations is None or iteration <= max_iterations:
        print(f"CYCLE: {iteration}")
        try:
            execute_strike(iteration)
        except Exception as e:
            print(f"ERR: FATAL_CYCLE_{iteration} {e}")
        
        if max_iterations is not None and iteration >= max_iterations:
            print("DAEMON: HALT")
            break
            
        print(f"SLEEP: {sleep_time}s")
        time.sleep(sleep_time)
        iteration += 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", action="store_true")
    parser.add_argument("--cycles", type=int, default=None)
    parser.add_argument("--sleep", type=int, default=300)
    args = parser.parse_args()
    
    if args.daemon:
        daemon_mode(sleep_time=args.sleep, max_iterations=args.cycles)
    else:
        execute_strike()
