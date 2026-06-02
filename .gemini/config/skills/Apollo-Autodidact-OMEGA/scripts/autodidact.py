import os
import sys
import json
import logging
import requests
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("apollo-autodidact")

APOLLO_API_URL = "https://api.apollo.io/v1/"
APOLLO_LLMS_TXT = "https://docs.apollo.io/llms.txt"

class ApolloAutodidact:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("APOLLO_API_KEY")
        if not self.api_key:
            logger.warning("APOLLO_API_KEY is not set. C5-REAL extraction will fail.")
        
        self.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache"
        }
        self.knowledge_base = {}

    def fetch_llm_docs(self) -> str:
        """Fetch the latest llms.txt documentation to map endpoints."""
        logger.info(f"Fetching API mappings from {APOLLO_LLMS_TXT}")
        try:
            resp = requests.get(APOLLO_LLMS_TXT, timeout=10)
            resp.raise_for_status()
            self.knowledge_base['llms_txt'] = resp.text
            return resp.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch llms.txt: {e}")
            return ""

    def parse_endpoints(self):
        """Parse llms.txt to extract documentation links."""
        docs = self.knowledge_base.get('llms_txt', '')
        endpoints = []
        for line in docs.split("\n"):
            if "https://docs.apollo.io/reference/" in line:
                endpoints.append(line.strip())
        logger.info(f"Discovered {len(endpoints)} endpoint references in docs.")
        return endpoints

    def execute_dynamic_intent(self, intent: str, dry_run: bool = False):
        """Synthesize logic based on intent.
        
        Example: If intent requires 'enriching contacts', map it to 
        people/match or people/bulk_match based on the autodidact logic.
        """
        logger.info(f"Executing intent: {intent} (Dry run: {dry_run})")
        
        # Determine the target endpoint dynamically based on intent keywords
        intent_lower = intent.lower()
        if "enrich" in intent_lower and "organization" in intent_lower:
            endpoint = "organizations/enrich"
        elif "enrich" in intent_lower:
            endpoint = "people/match"
        elif "search" in intent_lower and "organization" in intent_lower:
            endpoint = "mixed_companies/search"
        else:
            endpoint = "mixed_people/search" # Default target
            
        logger.info(f"Autodidact mapped intent to endpoint: {endpoint}")
        
        payload = {
            "api_key": self.api_key
        }
        
        if "web3" in intent_lower or "ai" in intent_lower:
            payload["q_organization_keyword_tags"] = ["web3", "ai"]

        if dry_run:
            logger.info(f"[C4-SIM] Would POST to {urljoin(APOLLO_API_URL, endpoint)} with payload: {payload.keys()}")
            return {"status": "simulated", "endpoint": endpoint}

        logger.info(f"[C5-REAL] Executing against {urljoin(APOLLO_API_URL, endpoint)}")
        if not self.api_key:
            raise ValueError("C5-REAL requires APOLLO_API_KEY")
            
        url = urljoin(APOLLO_API_URL, endpoint)
        resp = requests.post(url, headers=self.headers, json=payload)
        
        if resp.status_code == 200:
            logger.info("Extraction successful. Exergy positive.")
            return resp.json()
        else:
            logger.error(f"API Error {resp.status_code}: {resp.text}")
            return {"error": resp.text, "status_code": resp.status_code}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Apollo Autodidact C5-REAL Engine")
    parser.add_argument("--intent", type=str, required=True, help="Intent to execute")
    parser.add_argument("--dry-run", action="store_true", help="Run in C4-SIM mode")
    
    args = parser.parse_args()
    
    engine = ApolloAutodidact()
    engine.fetch_llm_docs()
    engine.parse_endpoints()
    
    result = engine.execute_dynamic_intent(args.intent, dry_run=args.dry_run)
    print(json.dumps({"result": result}, indent=2))
