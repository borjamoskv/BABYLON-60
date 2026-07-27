import requests
class CortexClient:
    def __init__(self, base_url="http://localhost:8009"):
        self.base_url = base_url
    def add(self, user_id, agent_id, content):
        return requests.post(
            f"{self.base_url}/memory/add",
            json={
                "user_id": user_id,
                "agent_id": agent_id,
                "content": content
            }
        ).json()
    def query(self, user_id, query):
        return requests.post(
            f"{self.base_url}/memory/query",
            json={
                "user_id": user_id,
                "query": query
            }
        ).json()
