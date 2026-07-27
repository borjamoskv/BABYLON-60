from cortex import CortexClient
client = CortexClient()
client.add("u1", "agent1", "user likes distributed systems")
print(client.query("u1", "what does user like?"))
