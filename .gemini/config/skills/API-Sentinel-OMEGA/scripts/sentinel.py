"""C5-REAL"""
import urllib.request
import urllib.error
import json
import time
import os
import re

try:
    from eth_account import Account
    import secrets
    HAS_ETH_ACCOUNT = True
except ImportError:
    HAS_ETH_ACCOUNT = False

class APISentinelOmega:
    """C5-REAL API Router"""
    def __init__(self, agent_name="API-Sentinel-Ω", max_retries=3):
        self.agent_name = agent_name
        self.max_retries = max_retries
        print(f"[{self.agent_name}] INIT")
        
        self.wallet_address = None
        self._pk = None
        self.mnemonic = None
        if HAS_ETH_ACCOUNT:
            Account.enable_unaudited_hdwallet_features()
            self.mnemonic = os.environ.get("CORTEX_SOVEREIGN_MNEMONIC")
            self._pk = os.environ.get("CORTEX_SOVEREIGN_PK")
            
            if self.mnemonic:
                acct = Account.from_mnemonic(self.mnemonic)
                self._pk = acct.key.hex()
            elif self._pk:
                acct = Account.from_key(self._pk)
            else:
                print(f"[{self.agent_name}] Gen BIP-39 wallet")
                acct, self.mnemonic = Account.create_with_mnemonic()
                self._pk = acct.key.hex()
                print(f"[{self.agent_name}] Mnemonic: {self.mnemonic}")
                
            self.wallet_address = acct.address
            print(f"[{self.agent_name}] Wallet: {self.wallet_address}")
            
        self.registry_path = os.path.join(os.path.dirname(__file__), "api_registry.json")
        self.registry = self._load_registry()

    def _load_registry(self) -> dict:
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass
        return {}

    def _save_registry(self):
        with open(self.registry_path, "w") as f:
            json.dump(self.registry, f, indent=2)
        print(f"[{self.agent_name}] Registry saved")

    def execute_get(self, url: str, headers: dict = None) -> dict:
        if headers is None:
            safe_name = self.agent_name.replace("Ω", "OMEGA")
            headers = {"User-Agent": f"CORTEX/{safe_name}"}
            
        req = urllib.request.Request(url, headers=headers)
        
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"[{self.agent_name}] GET -> {url} ({attempt}/{self.max_retries})")
                with urllib.request.urlopen(req) as response:
                    if response.status == 200:
                        print(f"[{self.agent_name}] 200 OK")
                        return json.loads(response.read())
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    wait_time = 2 ** attempt
                    print(f"[{self.agent_name}] 429 Backoff: {wait_time}s")
                    time.sleep(wait_time)
                else:
                    print(f"[{self.agent_name}] HTTP {e.code}: {e.reason}")
                    break
            except urllib.error.URLError as e:
                print(f"[{self.agent_name}] URL Error: {e.reason}")
                break
            except Exception as e:
                print(f"[{self.agent_name}] Error: {str(e)}")
                break
                
        print(f"[{self.agent_name}] Failed")
        return {}

    def execute_post(self, url: str, payload: dict, headers: dict = None) -> dict:
        if headers is None:
            safe_name = self.agent_name.replace("Ω", "OMEGA")
            headers = {
                "User-Agent": f"CORTEX/{safe_name}",
                "Content-Type": "application/json"
            }
        
        if "sk_" in json.dumps(payload):
            print(f"[{self.agent_name}] ABORT: sk_ detected")
            return {}

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"[{self.agent_name}] POST -> {url} ({attempt}/{self.max_retries})")
                with urllib.request.urlopen(req) as response:
                    if response.status in [200, 201, 202]:
                        print(f"[{self.agent_name}] {response.status}")
                        return json.loads(response.read())
            except Exception as e:
                print(f"[{self.agent_name}] Error: {str(e)}")
                time.sleep(2 ** attempt)

        return {}

    def _simulate_llm_routing(self, intent: str) -> dict:
        """C5-REAL"""
        intent_lower = intent.lower()
        if "crypto" in intent_lower or "precio" in intent_lower or "bitcoin" in intent_lower:
            return {
                "url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,solana&vs_currencies=usd",
                "method": "GET"
            }
        elif "nft" in intent_lower or "coleccion" in intent_lower or "token no fungible" in intent_lower:
            return {
                "url": "https://api.coingecko.com/api/v3/nfts/list?per_page=3",
                "method": "GET"
            }
        elif "wallet" in intent_lower or "0x" in intent_lower or "balance" in intent_lower or "cartera" in intent_lower:
            match = re.search(r"0x[a-fA-F0-9]{40}", intent)
            address = match.group(0) if match else "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
            return {
                "url": "https://eth.llamarpc.com",
                "method": "POST",
                "payload": {
                    "jsonrpc": "2.0",
                    "method": "eth_getBalance",
                    "params": [address, "latest"],
                    "id": 1
                }
            }
        elif "clima" in intent_lower or "weather" in intent_lower:
            return {
                "url": "https://api.open-meteo.com/v1/forecast?latitude=43.26&longitude=-2.92&current_weather=true",
                "method": "GET"
            }
        elif "paper" in intent_lower or "sota" in intent_lower or "arxiv" in intent_lower:
            return {
                "url": "https://api.openalex.org/works?search=autonomous+agents&per-page=1",
                "method": "GET"
            }
        else:
            print(f"[{self.agent_name}] Fallback Search")
            return {
                "url": "https://api.github.com/zen",
                "method": "GET"
            }

    def intuit_and_fetch_api(self, intent: str, payload: dict = None) -> dict:
        """C5-REAL"""
        print(f"[{self.agent_name}] INTENT: '{intent}'")
        
        intent_lower = intent.lower()
        if intent_lower in self.registry:
            print(f"[{self.agent_name}] Cache hit")
            route_plan = self.registry[intent_lower]
        else:
            route_plan = self._simulate_llm_routing(intent)
            self.registry[intent_lower] = route_plan
            self._save_registry()
            
        url = route_plan["url"]
        method = route_plan["method"]
        print(f"[{self.agent_name}] API: {url} [{method}]")
        
        if method == "GET":
            return self.execute_get(url)
        elif method == "POST":
            final_payload = route_plan.get("payload", payload if payload else {})
            return self.execute_post(url, final_payload)
        
        return {}

    def sign_payload(self, message: str) -> dict:
        """C5-REAL"""
        if not HAS_ETH_ACCOUNT or not self._pk:
            return {"error": "Wallet not initialized."}
        
        from eth_account.messages import encode_defunct
        msg = encode_defunct(text=message)
        signed_message = Account.sign_message(msg, private_key=self._pk)
        
        return {
            "address": self.wallet_address,
            "message": message,
            "signature": signed_message.signature.hex()
        }

if __name__ == "__main__":
    sentinel = APISentinelOmega()
    
    intent = "Dime el balance de la wallet 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 (vitalik.eth)"
    data = sentinel.intuit_and_fetch_api(intent)
    print(json.dumps(data, indent=2) if data else "[Error]")

    sig = sentinel.sign_payload("C5-REAL")
    print(json.dumps(sig, indent=2))
