# EXECUTION: C5-REAL / C4-SIM
import os, json, logging, requests
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("apollo")

APOLLO_API_URL = "https://api.apollo.io/v1/"
APOLLO_LLMS_TXT = "https://docs.apollo.io/llms.txt"

class ApolloAutodidact:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("APOLLO_API_KEY")
        if not self.api_key: logger.warning("C5-REAL fails: APOLLO_API_KEY unset")
        self.headers = {"Content-Type": "application/json", "x-api-key": self.api_key}
        self.knowledge_base = {}

    def fetch_llm_docs(self) -> str:
        try:
            resp = requests.get(APOLLO_LLMS_TXT, timeout=10)
            resp.raise_for_status()
            self.knowledge_base['llms_txt'] = resp.text
            return resp.text
        except requests.RequestException as e:
            logger.error(f"FAIL: {e}")
            return ""

    def parse_endpoints(self):
        docs = self.knowledge_base.get('llms_txt', '')
        return [line.strip() for line in docs.split("\n") if "https://docs.apollo.io/reference/" in line]

    def execute_dynamic_intent(self, intent: str, dry_run: bool = False):
        i = intent.lower()
        endpoint = "organizations/enrich" if "enrich" in i and "organization" in i else \
                   "people/match" if "enrich" in i else \
                   "mixed_companies/search" if "search" in i and "organization" in i else \
                   "mixed_people/search"
        
        payload = {"q_organization_keyword_tags": ["web3", "ai"]} if "web3" in i or "ai" in i else {}
        url = urljoin(APOLLO_API_URL, endpoint)
        
        if dry_run:
            logger.info(f"[C4-SIM] POST {url} keys:{list(payload.keys())}")
            return {"status": "C4-SIM", "endpoint": endpoint}

        logger.info(f"[C5-REAL] POST {url}")
        if not self.api_key: raise ValueError("C5-REAL: APOLLO_API_KEY req")
            
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
    print(json.dumps({"result": engine.execute_dynamic_intent(args.intent, args.dry_run)}))
