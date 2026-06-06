# C5-REAL
import os, json, logging, requests
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("apollo-autodidact")

APOLLO_API_URL = "https://api.apollo.io/v1/"
APOLLO_LLMS_TXT = "https://docs.apollo.io/llms.txt"

class ApolloAutodidact:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("APOLLO_API_KEY")
        if not self.api_key: logger.warning("APOLLO_API_KEY unset. C5-REAL fails.")
        self.headers = {"Content-Type": "application/json", "Cache-Control": "no-cache", "x-api-key": self.api_key}
        self.knowledge_base = {}

    def fetch_llm_docs(self) -> str:
        try:
            resp = requests.get(APOLLO_LLMS_TXT, timeout=10)
            resp.raise_for_status()
            self.knowledge_base['llms_txt'] = resp.text
            return resp.text
        except requests.RequestException as e:
            logger.error(f"llms.txt fetch failed: {e}")
            return ""

    def parse_endpoints(self):
        docs = self.knowledge_base.get('llms_txt', '')
        return [line.strip() for line in docs.split("\n") if "https://docs.apollo.io/reference/" in line]

    def execute_dynamic_intent(self, intent: str, dry_run: bool = False):
        intent_lower = intent.lower()
        if "enrich" in intent_lower and "organization" in intent_lower: endpoint = "organizations/enrich"
        elif "enrich" in intent_lower: endpoint = "people/match"
        elif "search" in intent_lower and "organization" in intent_lower: endpoint = "mixed_companies/search"
        else: endpoint = "mixed_people/search"
            
        payload = {}
        if "web3" in intent_lower or "ai" in intent_lower: payload["q_organization_keyword_tags"] = ["web3", "ai"]

        url = urljoin(APOLLO_API_URL, endpoint)
        if dry_run:
            logger.info(f"[C4-SIM] POST {url} keys:{payload.keys()}")
            return {"status": "simulated", "endpoint": endpoint}

        logger.info(f"[C5-REAL] POST {url}")
        if not self.api_key: raise ValueError("C5-REAL requires APOLLO_API_KEY")
            
        resp = requests.post(url, headers=self.headers, json=payload)
        return resp.json() if resp.status_code == 200 else {"error": resp.text, "status_code": resp.status_code}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--intent", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    engine = ApolloAutodidact()
    engine.fetch_llm_docs()
    engine.parse_endpoints()
    print(json.dumps({"result": engine.execute_dynamic_intent(args.intent, args.dry_run)}, indent=2))
